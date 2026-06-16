from __future__ import annotations

from datetime import datetime

from novel_runtime.db.database import Database
from novel_runtime.models.project import Project


class ProjectRepo:
    def __init__(self, db: Database):
        self.db = db

    def create(self, project: Project, storage_path: str) -> Project:
        conn = self.db.get_connection()
        conn.execute(
            """INSERT INTO projects (project_id, project_name, genre, status,
               default_style_id, current_volume_id, current_chapter_id,
               bible_version, writing_strategy_id, storage_path, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (project.project_id, project.project_name, project.genre, project.status,
             project.default_style_id, project.current_volume_id, project.current_chapter_id,
             project.bible_version, project.writing_strategy_id, storage_path,
             project.created_at.isoformat(), project.updated_at.isoformat()),
        )
        conn.commit()
        conn.close()
        return project

    def get_by_id(self, project_id: str) -> Project | None:
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone()
        conn.close()
        if row is None:
            return None
        return Project(**dict(row))

    def list_projects(self, status: str | None = None) -> list[Project]:
        conn = self.db.get_connection()
        if status:
            rows = conn.execute("SELECT * FROM projects WHERE status = ?", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM projects").fetchall()
        conn.close()
        return [Project(**dict(r)) for r in rows]

    def update(self, project: Project) -> Project:
        project.updated_at = datetime.now()
        conn = self.db.get_connection()
        conn.execute(
            """UPDATE projects SET project_name=?, genre=?, status=?,
               default_style_id=?, current_volume_id=?, current_chapter_id=?,
               bible_version=?, writing_strategy_id=?, updated_at=?
               WHERE project_id=?""",
            (project.project_name, project.genre, project.status,
             project.default_style_id, project.current_volume_id, project.current_chapter_id,
             project.bible_version, project.writing_strategy_id,
             project.updated_at.isoformat(), project.project_id),
        )
        conn.commit()
        conn.close()
        return project

    def delete(self, project_id: str) -> bool:
        conn = self.db.get_connection()
        cursor = conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
