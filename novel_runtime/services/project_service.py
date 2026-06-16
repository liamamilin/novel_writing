from __future__ import annotations
from pathlib import Path

from novel_runtime.db.database import Database
from novel_runtime.db.project_repo import ProjectRepo
from novel_runtime.exceptions import ProjectNotFoundError
from novel_runtime.models.chapter import Chapter
from novel_runtime.models.project import Project, ProjectCreate, ProjectUpdate
from novel_runtime.storage.event_storage import EventStorage
from novel_runtime.storage.project_layout import create_project_layout
from novel_runtime.storage.project_storage import ProjectStorage


class ProjectService:
    def __init__(self, db: Database, storage_base: Path):
        self.db = db
        self.storage_base = storage_base
        self.project_storage = ProjectStorage(storage_base)
        self.project_repo = ProjectRepo(db)

    def create_project(self, create: ProjectCreate) -> Project:
        project = Project(
            project_name=create.project_name,
            genre=create.genre,
            idea=create.idea,
            target_reader=create.target_reader,
            core_selling_point=create.core_selling_point,
            target_style=create.target_style,
        )
        project_path = self.storage_base / project.project_id
        project_meta = {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "genre": project.genre,
            "status": project.status,
            "bible_version": project.bible_version,
        }
        create_project_layout(project_path, project_meta)
        self.project_storage.save_project(project)
        self.project_repo.create(project, str(project_path))
        EventStorage(self.storage_base).record(project.project_id, "project_created", details={"name": project.project_name})
        return project

    def get_project(self, project_id: str) -> Project:
        project = self.project_repo.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} not found")
        return project

    def list_projects(self, status: str | None = None) -> list[Project]:
        return self.project_repo.list_projects(status)

    def update_project(self, project_id: str, updates: ProjectUpdate) -> Project:
        project = self.get_project(project_id)
        for field, value in updates.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        self.project_storage.save_project(project)
        self.project_repo.update(project)
        return project

    def create_chapter(self, project_id: str, chapter_number: int) -> Chapter:
        project = self.get_project(project_id)
        chapter = Chapter(
            chapter_id=f"chapter_{chapter_number:03d}",
            chapter_number=chapter_number,
        )
        self.project_storage.create_chapter_dir(project_id, chapter_number)
        self.project_storage.save_chapter(project, chapter)
        EventStorage(self.storage_base).record(project_id, "chapter_created", details={"chapter_number": chapter_number})
        return chapter

    def get_chapter(self, project_id: str, chapter_number: int) -> Chapter:
        return self.project_storage.load_chapter(project_id, chapter_number)

    def advance_chapter_status(self, project_id: str, chapter_number: int) -> Chapter:
        project = self.get_project(project_id)
        chapter = self.project_storage.load_chapter(project_id, chapter_number)
        chapter = self.project_storage.update_chapter_status(project_id, chapter_number, chapter.status)
        self.project_storage.save_chapter(project, chapter)
        return chapter

    def list_chapters(self, project_id: str) -> list[Chapter]:
        return self.project_storage.list_chapters(project_id)

    def get_project_path(self, project_id: str) -> Path:
        return self.project_storage.get_project_path(project_id)

    def delete_project(self, project_id: str) -> bool:
        project_path = self.get_project_path(project_id)
        if not project_path.exists():
            return False
        import shutil
        shutil.rmtree(project_path)
        conn = self.db.get_connection()
        conn.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
        conn.commit()
        conn.close()
        return True
