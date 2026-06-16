from __future__ import annotations
from pathlib import Path
from uuid import uuid4

import yaml

from novel_runtime.agents.state_updater import StateUpdaterAgent
from novel_runtime.compiler.state_diff import StateDiffer
from novel_runtime.compiler.state_health_checker import StateHealthChecker
from novel_runtime.exceptions import ChapterNotFoundError, InvalidStateTransitionError
from novel_runtime.llm.provider import LLMProvider
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.models.character import CharacterState
from novel_runtime.models.hook import Hook
from novel_runtime.models.subplot import Subplot
from novel_runtime.services.bible_update_service import BibleUpdateService
from novel_runtime.services.project_service import ProjectService
from novel_runtime.services.hook_service import HookService
from novel_runtime.storage import state_storage, strategy_storage, subplot_storage
from novel_runtime.storage.chapter_storage import load_chapter_file, save_chapter_file, chapter_file_exists, freeze_chapter, unfreeze_chapter
from novel_runtime.storage.snapshot_storage import SnapshotManager


class StateService:
    def __init__(
        self,
        project_service: ProjectService,
        provider: LLMProvider,
        prompt_loader: PromptLoader,
    ):
        self.project_service = project_service
        self.differ = StateDiffer()
        self.snapshot_manager = SnapshotManager()
        self.health_checker = StateHealthChecker()
        self.bible_updater = BibleUpdateService()
        self.hook_service = HookService(project_service)
        self._agent = StateUpdaterAgent(provider=provider, prompt_loader=prompt_loader)

    def update_state(self, project_id: str, chapter_number: int) -> dict:
        project = self.project_service.get_project(project_id)
        project_path = self.project_service.get_project_path(project_id)

        chapter = self.project_service.get_chapter(project_id, chapter_number)
        if chapter.status != "approved":
            raise InvalidStateTransitionError(
                f"Chapter {chapter_number} is {chapter.status}, must be 'approved' to update state"
            )

        draft_path = project_path / "chapters" / f"chapter_{chapter_number:03d}" / "draft.md"
        final_path = project_path / "chapters" / f"chapter_{chapter_number:03d}" / "final.md"

        if not final_path.exists():
            raise FileNotFoundError(f"final.md for chapter {chapter_number} not found")

        diff_result = self.differ.diff(draft_path, final_path)

        try:
            final_text = final_path.read_text(encoding="utf-8")
        except Exception:
            final_text = ""

        try:
            annotations_raw = load_chapter_file(project_path, chapter_number, "state_annotations")
        except FileNotFoundError:
            annotations_raw = ""

        current_characters = state_storage.load_characters(project_path)
        current_story_state = state_storage.load_story_state(project_path)
        current_hooks = state_storage.load_hooks(project_path)
        current_subplots = subplot_storage.load_subplots(project_path)

        ag_result = self._agent.update(
            final_text=final_text,
            annotations_text=annotations_raw,
            diff_summary=diff_result.summary,
            current_characters=yaml.dump([c.model_dump() for c in current_characters], allow_unicode=True) if current_characters else "",
            current_story_state=yaml.dump(current_story_state, allow_unicode=True) if current_story_state else "",
            current_hooks=yaml.dump([h.model_dump() for h in current_hooks], allow_unicode=True) if current_hooks else "",
            current_subplots=yaml.dump([s.model_dump() for s in current_subplots], allow_unicode=True) if current_subplots else "",
        )

        if not ag_result.success:
            return {"error": ag_result.validation_errors}

        update_result = ag_result.data

        if update_result.character_updates:
            chars = {c.character_id: c for c in current_characters}
            for cu in update_result.character_updates:
                cid = cu.get("character_id", "")
                if cid in chars:
                    for key, value in cu.items():
                        if key != "character_id" and value is not None:
                            setattr(chars[cid], key, value)
            state_storage.save_characters(project_path, list(chars.values()))

        if update_result.new_hooks:
            for h in update_result.new_hooks:
                hook = Hook(
                    hook_id=h.get("hook_id", f"H_{uuid4().hex[:6].upper()}"),
                    content=h.get("content", ""),
                    source_chapter=f"chapter_{chapter_number:03d}",
                    type=h.get("type", "mystery"),
                    reader_patience=h.get("reader_patience", 8),
                )
                state_storage.add_hook(project_path, hook)

        triggered = update_result.triggered_hooks
        for tid in triggered:
            state_storage.update_hook(project_path, tid, {"status": "triggered"})

        for rh in update_result.resolved_hooks:
            rid = rh.get("hook_id", "")
            if rid:
                state_storage.update_hook(project_path, rid, {
                    "status": "resolved",
                    "actual_payoff_chapter": f"chapter_{chapter_number:03d}",
                })

        if update_result.subplot_advances:
            for sa in update_result.subplot_advances:
                sid = sa.get("subplot_id", "")
                if sid:
                    advancement = sa.get("advancement", "")
                    subplot_storage.update_subplot(project_path, sid, {
                        "last_advanced": f"chapter_{chapter_number:03d}",
                        "chapters_since_advance": 0,
                    })

        chapter.summary = update_result.summary
        from novel_runtime.storage.project_storage import ProjectStorage
        ProjectStorage(self.project_service.storage_base).save_chapter(project, chapter)

        snapshot_path = self.snapshot_manager.create_snapshot(project_path, chapter_number)

        strategy = strategy_storage.load_strategy(project_path)
        health_report = self.health_checker.check(project_path, chapter_number, strategy)
        health_yaml = yaml.dump(health_report.model_dump(), allow_unicode=True, default_flow_style=False)
        save_chapter_file(project_path, chapter_number, "review_continuity", health_yaml)

        bible_proposal = self.bible_updater.detect_update_need(
            project_path,
            update_result.world_updates,
            update_result.character_updates,
        )

        updated_files = [
            "states/story_state.yaml",
            "states/characters.yaml",
            "states/hooks.yaml",
        ]
        if update_result.subplot_advances:
            updated_files.append("subplots/subplot_registry.yaml")

        suggestions_path = project_path / "chapters" / f"chapter_{chapter_number:03d}" / "next_suggestions.yaml"
        if update_result.next_chapter_suggestions:
            suggestions_data = {"suggestions": update_result.next_chapter_suggestions}
            with open(suggestions_path, "w", encoding="utf-8") as f:
                yaml.dump(suggestions_data, f, allow_unicode=True, default_flow_style=False)

        return {
            "snapshot_path": str(snapshot_path),
            "updated_files": updated_files,
            "health_issues": len(health_report.issues),
            "next_suggestions_path": str(suggestions_path) if update_result.next_chapter_suggestions else "",
            "bible_update_proposal": bible_proposal.model_dump() if bible_proposal else None,
        }

    def rollback_state(self, project_id: str, target_chapter: int) -> dict:
        project_path = self.project_service.get_project_path(project_id)
        self.snapshot_manager.restore_snapshot(project_path, target_chapter)
        return {"restored_to_chapter": target_chapter}
