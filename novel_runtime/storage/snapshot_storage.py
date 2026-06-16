from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from novel_runtime.exceptions import SnapshotNotFoundError
from novel_runtime.storage import state_storage, subplot_storage


class SnapshotManager:
    def create_snapshot(self, project_path: Path, chapter_number: int) -> Path:
        snapshot_dir = project_path / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        story_state = state_storage.load_story_state(project_path)
        characters = state_storage.load_characters(project_path)
        hooks = state_storage.load_hooks(project_path)
        subplots = subplot_storage.load_subplots(project_path)

        snapshot = {
            "snapshot_chapter": chapter_number,
            "created_at": datetime.now().isoformat(),
            "story_state": story_state,
            "characters": [c.model_dump() for c in characters],
            "hooks": [h.model_dump() for h in hooks],
            "subplots": [s.model_dump() for s in subplots],
        }

        snapshot_path = snapshot_dir / f"state_after_chapter_{chapter_number:03d}.yaml"
        with open(snapshot_path, "w", encoding="utf-8") as f:
            yaml.dump(snapshot, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return snapshot_path

    def restore_snapshot(self, project_path: Path, chapter_number: int) -> None:
        snapshot_path = project_path / "snapshots" / f"state_after_chapter_{chapter_number:03d}.yaml"
        if not snapshot_path.exists():
            raise SnapshotNotFoundError(f"Snapshot for chapter {chapter_number} not found")

        with open(snapshot_path, encoding="utf-8") as f:
            snapshot = yaml.safe_load(f)

        if snapshot is None:
            raise SnapshotNotFoundError(f"Invalid snapshot for chapter {chapter_number}")

        from novel_runtime.models.character import CharacterState
        from novel_runtime.models.hook import Hook
        from novel_runtime.models.subplot import Subplot

        state_storage.save_story_state(project_path, snapshot.get("story_state", {}))
        characters = [CharacterState(**c) for c in snapshot.get("characters", [])]
        state_storage.save_characters(project_path, characters)
        hooks = [Hook(**h) for h in snapshot.get("hooks", [])]
        state_storage.save_hooks(project_path, hooks)
        subplots = [Subplot(**s) for s in snapshot.get("subplots", [])]
        subplot_storage.save_subplots(project_path, subplots)

        project_yaml_path = project_path / "project.yaml"
        if project_yaml_path.exists():
            with open(project_yaml_path, encoding="utf-8") as f:
                project_data = yaml.safe_load(f) or {}
            project_data["current_chapter_id"] = f"chapter_{chapter_number:03d}"
            with open(project_yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(project_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def list_snapshots(self, project_path: Path) -> list[int]:
        snapshot_dir = project_path / "snapshots"
        if not snapshot_dir.exists():
            return []
        chapters = []
        for f in snapshot_dir.glob("state_after_chapter_*.yaml"):
            try:
                ch = int(f.stem.split("_")[-1])
                chapters.append(ch)
            except (ValueError, IndexError):
                pass
        return sorted(chapters)

    def delete_snapshot(self, project_path: Path, chapter_number: int) -> bool:
        snapshot_path = project_path / "snapshots" / f"state_after_chapter_{chapter_number:03d}.yaml"
        if not snapshot_path.exists():
            return False
        snapshot_path.unlink()
        return True
