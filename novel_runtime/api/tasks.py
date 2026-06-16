from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from novel_runtime.db.database import Database
from novel_runtime.db.task_repo import TaskRepo

router = APIRouter(prefix="/api/projects/{project_id}/tasks", tags=["tasks"])


def get_task_repo(request: Request) -> TaskRepo:
    db: Database = request.app.state.db
    return TaskRepo(db)


@router.get("/{task_id}")
async def get_task(
    project_id: str,
    task_id: str,
    repo: TaskRepo = Depends(get_task_repo),
):
    task = repo.get_by_id(task_id)
    if task is None:
        raise HTTPException(404, f"Task {task_id} not found")
    return task
