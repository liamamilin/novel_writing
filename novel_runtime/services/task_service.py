from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import BackgroundTasks

from novel_runtime.agents.base import AgentResult, BaseAgent
from novel_runtime.db.database import Database
from novel_runtime.db.task_repo import TaskRepo
from novel_runtime.exceptions import InvalidStateTransitionError
from novel_runtime.metrics import task_duration_seconds
from novel_runtime.models.task import Task

logger = logging.getLogger("novel_runtime.services.task_service")


class TaskService:
    def __init__(self, db: Database):
        self.db = db
        self.task_repo = TaskRepo(db)

    def create_task(self, project_id: str, task_type: str, input_data: dict) -> Task:
        task = Task(
            task_id=f"task_{uuid4().hex[:12]}",
            project_id=project_id,
            task_type=task_type,
            status="pending",
            input_data=input_data,
        )
        created = self.task_repo.create(task)
        logger.info("task_created", extra={"task_id": created.task_id, "project_id": project_id, "task_type": task_type})
        return created

    def execute_task(self, task_id: str, agent: BaseAgent, variables: dict, context: dict | None = None) -> Task:
        task = self.task_repo.get_by_id(task_id)
        start = time.monotonic()
        task = self.task_repo.update_status(task_id, "running")
        logger.info("task_running", extra={"task_id": task_id, "task_type": task.task_type, "project_id": task.project_id})

        try:
            result: AgentResult = agent.execute(variables, context)
            if result.success:
                task = self.task_repo.update_status(
                    task_id, "success",
                    output_data={
                        "data": str(result.data) if not isinstance(result.data, dict) else result.data,
                        "retries_used": result.retries_used,
                        "tokens_used": result.tokens_used,
                    },
                )
                duration = (time.monotonic() - start) * 1000
                task_duration_seconds.labels(task_type=task.task_type).observe(duration / 1000.0)
                logger.info("task_success", extra={
                    "task_id": task_id,
                    "task_type": task.task_type,
                    "project_id": task.project_id,
                    "duration_ms": f"{duration:.1f}",
                    "retries": result.retries_used,
                    "tokens": result.tokens_used,
                })
            else:
                task = self.task_repo.update_status(
                    task_id, "failed",
                    error="; ".join(result.validation_errors) if result.validation_errors else "Unknown error",
                )
                logger.warning("task_failed", extra={
                    "task_id": task_id,
                    "task_type": task.task_type,
                    "project_id": task.project_id,
                    "error": task.error,
                })
        except Exception as e:
            task = self.task_repo.update_status(task_id, "failed", error=str(e))
            logger.error("task_crashed", extra={
                "task_id": task_id,
                "task_type": task.task_type,
                "project_id": task.project_id,
                "error": str(e),
            })

        return task

    def execute_task_async(
        self,
        project_id: str,
        task_type: str,
        agent: BaseAgent,
        variables: dict,
        background_tasks: BackgroundTasks,
        context: dict | None = None,
    ) -> Task:
        task = self.create_task(project_id, task_type, variables)

        def _execute():
            self.execute_task(task.task_id, agent, variables, context)

        background_tasks.add_task(_execute)
        return task

    def get_task(self, task_id: str) -> Task:
        return self.task_repo.get_by_id(task_id)

    def list_tasks(self, project_id: str, task_type: str | None = None) -> list[Task]:
        return self.task_repo.list_by_project(project_id, task_type)

    def cancel_task(self, task_id: str) -> Task:
        task = self.task_repo.get_by_id(task_id)
        if task.status == "running":
            raise InvalidStateTransitionError("Cannot cancel a running task")
        cancelled = self.task_repo.update_status(task_id, "cancelled")
        logger.info("task_cancelled", extra={"task_id": task_id, "project_id": task.project_id})
        return cancelled
