from __future__ import annotations

from uuid import uuid4

from novel_runtime.models.hook import Hook
from novel_runtime.services.project_service import ProjectService
from novel_runtime.storage import state_storage, strategy_storage


class HookService:
    def __init__(self, project_service: ProjectService):
        self.project_service = project_service

    def _project_path(self, project_id: str):
        return self.project_service.get_project_path(project_id)

    def add_hook(self, project_id: str, content: str, source_chapter: str = "", hook_type: str = "mystery",
                 priority: str = "medium", reader_patience: int = 8,
                 related_characters: list[str] | None = None) -> Hook:
        hook = Hook(
            hook_id=f"H_{uuid4().hex[:6].upper()}",
            content=content,
            source_chapter=source_chapter,
            type=hook_type,
            priority=priority,
            reader_patience=reader_patience,
            related_characters=related_characters or [],
        )
        return state_storage.add_hook(self._project_path(project_id), hook)

    def update_hook(self, project_id: str, hook_id: str, updates: dict) -> Hook | None:
        return state_storage.update_hook(self._project_path(project_id), hook_id, updates)

    def trigger_hook(self, project_id: str, hook_id: str) -> Hook | None:
        return state_storage.update_hook(self._project_path(project_id), hook_id, {"status": "triggered"})

    def resolve_hook(self, project_id: str, hook_id: str, resolution: str, chapter: str) -> Hook | None:
        return state_storage.update_hook(self._project_path(project_id), hook_id, {
            "status": "resolved",
            "actual_payoff_chapter": chapter,
            "notes": resolution,
        })

    def get_chapter_hooks(self, project_id: str, chapter_number: int) -> dict:
        return state_storage.get_hooks_for_chapter(self._project_path(project_id), chapter_number)

    def list_hooks(self, project_id: str, status: str | None = None,
                   hook_type: str | None = None, priority: str | None = None) -> list[Hook]:
        hooks = state_storage.load_hooks(self._project_path(project_id))
        if status:
            hooks = [h for h in hooks if h.status == status]
        if hook_type:
            hooks = [h for h in hooks if h.type == hook_type]
        if priority:
            hooks = [h for h in hooks if h.priority == priority]
        return hooks

    def escalate_urgency(self, project_id: str, current_chapter: int) -> list[Hook]:
        project_path = self._project_path(project_id)
        strategy = strategy_storage.load_strategy(project_path)
        if not strategy.hook_policy.urgency_escalation:
            return []

        hooks = state_storage.load_hooks(project_path)
        updated = []
        for h in hooks:
            if h.status not in ("open", "triggered"):
                continue
            try:
                src_ch = int(h.source_chapter.split("_")[-1])
            except (ValueError, IndexError):
                continue
            patience = h.reader_patience
            urgency_threshold = src_ch + patience
            rising_threshold = src_ch + (patience * 7 // 10)
            if current_chapter >= urgency_threshold and h.urgency != "critical":
                state_storage.update_hook(project_path, h.hook_id, {"urgency": "critical"})
                updated.append(h)
            elif current_chapter >= rising_threshold and h.urgency != "rising":
                state_storage.update_hook(project_path, h.hook_id, {"urgency": "rising"})
                updated.append(h)
        return updated
