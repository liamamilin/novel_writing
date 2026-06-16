from __future__ import annotations

from uuid import uuid4

from novel_runtime.models.subplot import Subplot
from novel_runtime.services.project_service import ProjectService
from novel_runtime.storage import subplot_storage, strategy_storage


class SubplotService:
    def __init__(self, project_service: ProjectService):
        self.project_service = project_service

    def _project_path(self, project_id: str):
        return self.project_service.get_project_path(project_id)

    def create_subplot(self, project_id: str, name: str, subplot_type: str, involved_characters: list[str] | None = None) -> Subplot:
        sp = Subplot(
            subplot_id=f"subplot_{uuid4().hex[:4]}",
            name=name,
            type=subplot_type,
            status="setup",
            involved_characters=involved_characters or [],
        )
        sp.arc = {"setup_chapter": "", "current_stage": "setup"}
        existing = self.list_subplots(project_id)
        subplot_storage.save_subplots(self._project_path(project_id), existing + [sp])
        return sp

    def update_subplot(self, project_id: str, subplot_id: str, updates: dict) -> Subplot | None:
        return subplot_storage.update_subplot(self._project_path(project_id), subplot_id, updates)

    def advance_subplot(self, project_id: str, subplot_id: str, advancement: str, chapter_id: str) -> Subplot | None:
        sp = subplot_storage.load_subplot(self._project_path(project_id), subplot_id)
        if sp is None:
            return None
        next_status = {"setup": "escalating", "escalating": "climax", "climax": "resolving", "resolving": "resolved"}
        new_status = next_status.get(sp.status, sp.status)
        return subplot_storage.update_subplot(self._project_path(project_id), subplot_id, {
            "last_advanced": chapter_id,
            "chapters_since_advance": 0,
            "status": new_status,
        })

    def list_subplots(self, project_id: str, status: str | None = None) -> list[Subplot]:
        all_sp = subplot_storage.load_subplots(self._project_path(project_id))
        if status:
            return [s for s in all_sp if s.status == status]
        return all_sp

    def suggest_subplot_allocation(self, project_id: str, chapter_number: int) -> dict:
        project_path = self._project_path(project_id)
        strategy = strategy_storage.load_strategy(project_path)
        all_sp = subplot_storage.load_subplots(project_path)
        should_advance = []
        should_idle = []
        at_risk = []

        for sp in all_sp:
            if sp.status in ("resolved", "abandoned"):
                continue
            idle_time = sp.chapters_since_advance + 1
            if idle_time >= strategy.subplot_policy.min_advance_frequency:
                should_advance.append({
                    "subplot_id": sp.subplot_id,
                    "name": sp.name,
                    "chapters_idle": idle_time,
                })
            else:
                should_idle.append({
                    "subplot_id": sp.subplot_id,
                    "name": sp.name,
                    "chapters_idle": idle_time,
                })
            if idle_time >= strategy.subplot_policy.max_gap_between_advances:
                at_risk.append({
                    "subplot_id": sp.subplot_id,
                    "name": sp.name,
                    "chapters_idle": idle_time,
                })

        return {"should_advance": should_advance, "should_idle": should_idle, "at_risk": at_risk}
