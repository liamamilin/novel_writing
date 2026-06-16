from __future__ import annotations

from datetime import datetime
from pathlib import Path

from novel_runtime.exceptions import (
    ChapterNotFoundError,
    InvalidStateTransitionError,
    ProjectNotFoundError,
)
from novel_runtime.models.chapter import Chapter
from novel_runtime.models.project import Project
from novel_runtime.storage.base import read_yaml_model, write_yaml_model

VALID_TRANSITIONS = {
    "planned": "drafted",
    "drafted": "reviewed",
    "reviewed": "approved",
    "approved": "locked",
}

CHAPTER_FILE_TYPES_MD = [
    "context_pack", "plan", "draft", "styled_draft", "final",
    "review_continuity", "review_quality", "review_cross_chapter", "review_reader_sim",
]

CHAPTER_FILE_TYPES_YAML = [
    "state_annotations", "fix_instructions",
]


class ProjectStorage:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def _project_path(self, project_id: str) -> Path:
        return self.base_path / project_id

    def load_project(self, project_id: str) -> Project:
        path = self._project_path(project_id) / "project.yaml"
        if not path.exists():
            raise ProjectNotFoundError(f"Project {project_id} not found")
        return read_yaml_model(path, Project)

    def save_project(self, project: Project) -> Path:
        project.updated_at = datetime.now()
        path = self._project_path(project.project_id) / "project.yaml"
        return write_yaml_model(path, project, overwrite=True)

    def get_project_path(self, project_id: str) -> Path:
        return self._project_path(project_id)

    def create_chapter_dir(self, project_id: str, chapter_number: int) -> Path:
        chapter_dir = self._project_path(project_id) / "chapters" / f"chapter_{chapter_number:03d}"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        for ft in CHAPTER_FILE_TYPES_MD:
            (chapter_dir / f"{ft}.md").touch(exist_ok=True)
        for ft in CHAPTER_FILE_TYPES_YAML:
            (chapter_dir / f"{ft}.yaml").touch(exist_ok=True)
        return chapter_dir

    def load_chapter(self, project_id: str, chapter_number: int) -> Chapter:
        path = self._chapter_yaml_path(project_id, chapter_number)
        if not path.exists():
            raise ChapterNotFoundError(
                f"Chapter {chapter_number} not found in project {project_id}"
            )
        return read_yaml_model(path, Chapter)

    def _chapter_dir(self, project_id: str, chapter_number: int) -> Path:
        return self._project_path(project_id) / "chapters" / f"chapter_{chapter_number:03d}"

    def _chapter_yaml_path(self, project_id: str, chapter_number: int) -> Path:
        return self._chapter_dir(project_id, chapter_number) / "chapter.yaml"

    def save_chapter(self, project: Project, chapter: Chapter) -> Path:
        chapter.updated_at = datetime.now()
        path = self._chapter_yaml_path(project.project_id, chapter.chapter_number)
        return write_yaml_model(path, chapter, overwrite=True)

    def update_chapter_status(self, project_id: str, chapter_number: int, new_status: str) -> Chapter:
        chapter = self.load_chapter(project_id, chapter_number)
        expected_next = VALID_TRANSITIONS.get(chapter.status)
        if new_status != expected_next:
            raise InvalidStateTransitionError(
                f"Cannot transition from {chapter.status} to {new_status}. "
                f"Expected: {chapter.status} -> {expected_next}"
            )
        chapter.status = new_status
        return chapter

    def list_chapters(self, project_id: str) -> list[Chapter]:
        chapters_dir = self._project_path(project_id) / "chapters"
        if not chapters_dir.exists():
            return []
        result = []
        for d in sorted(chapters_dir.iterdir()):
            if not d.is_dir():
                continue
            yaml_path = d / "chapter.yaml"
            if yaml_path.exists():
                result.append(read_yaml_model(yaml_path, Chapter))
        return result
