from __future__ import annotations

import json
from datetime import datetime, timezone

from novel_runtime.db.database import Database
from novel_runtime.models.task import Task


class TaskRepo:
    def __init__(self, db: Database):
        self.db = db

    def create(self, task: Task) -> Task:
        conn = self.db.get_connection()
        conn.execute(
            """INSERT INTO tasks (task_id, project_id, task_type, status,
               input_data, output_data, error, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task.task_id, task.project_id, task.task_type, task.status,
             json.dumps(task.input_data), json.dumps(task.output_data), task.error,
             task.created_at.isoformat(), task.updated_at.isoformat()),
        )
        conn.commit()
        conn.close()
        return task

    def get_by_id(self, task_id: str) -> Task | None:
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        conn.close()
        if row is None:
            return None
        data = dict(row)
        data["input_data"] = json.loads(data["input_data"])
        data["output_data"] = json.loads(data["output_data"])
        return Task(**data)

    def list_by_project(self, project_id: str, status: str | None = None) -> list[Task]:
        conn = self.db.get_connection()
        if status:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE project_id = ? AND status = ?", (project_id, status)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tasks WHERE project_id = ?", (project_id,)).fetchall()
        conn.close()
        result = []
        for r in rows:
            data = dict(r)
            data["input_data"] = json.loads(data["input_data"])
            data["output_data"] = json.loads(data["output_data"])
            result.append(Task(**data))
        return result

    def update_status(self, task_id: str, status: str, output_data: dict | None = None, error: str | None = None) -> Task:
        conn = self.db.get_connection()
        now = datetime.now(timezone.utc).isoformat()
        if output_data is not None:
            conn.execute(
                "UPDATE tasks SET status=?, output_data=?, updated_at=? WHERE task_id=?",
                (status, json.dumps(output_data), now, task_id),
            )
        elif error is not None:
            conn.execute(
                "UPDATE tasks SET status=?, error=?, updated_at=? WHERE task_id=?",
                (status, error, now, task_id),
            )
        else:
            conn.execute(
                "UPDATE tasks SET status=?, updated_at=? WHERE task_id=?",
                (status, now, task_id),
            )
        conn.commit()
        conn.close()
        return self.get_by_id(task_id)

    def list_orphans(self, threshold_seconds: int = 300) -> list[Task]:
        conn = self.db.get_connection()
        rows = conn.execute(
            """SELECT * FROM tasks
               WHERE status='running'
               AND REPLACE(updated_at, 'T', ' ') < datetime('now', ? || ' seconds')""",
            (str(-threshold_seconds),),
        ).fetchall()
        conn.close()
        result = []
        for r in rows:
            data = dict(r)
            data["input_data"] = json.loads(data["input_data"])
            data["output_data"] = json.loads(data["output_data"])
            result.append(Task(**data))
        return result
