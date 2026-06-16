from __future__ import annotations
from pathlib import Path
import tempfile, shutil

import pytest

from novel_runtime.compiler.state_diff import StateDiffer
from novel_runtime.storage.snapshot_storage import SnapshotManager
from novel_runtime.storage import state_storage, subplot_storage
from novel_runtime.models.character import CharacterState
from novel_runtime.models.hook import Hook
from novel_runtime.models.subplot import Subplot
from novel_runtime.exceptions import SnapshotNotFoundError


class TestStateDiffer:
    def setup_method(self):
        self.differ = StateDiffer()

    def test_no_changes(self, tmp_path):
        draft = tmp_path / "draft.md"
        final = tmp_path / "final.md"
        content = "## Scene 1\n主角登场。"
        draft.write_text(content)
        final.write_text(content)
        result = self.differ.diff(draft, final)
        assert not result.has_changes
        assert result.summary == "无修改"

    def test_user_added_content(self, tmp_path):
        draft = tmp_path / "draft.md"
        final = tmp_path / "final.md"
        draft.write_text("")
        final.write_text("用户从头写的内容。")
        result = self.differ.diff(draft, final)
        assert result.has_changes
        assert "从头写" in result.summary

    def test_draft_not_exists(self, tmp_path):
        draft = tmp_path / "draft.md"
        final = tmp_path / "final.md"
        final.write_text("final content")
        result = self.differ.diff(draft, final)
        assert result.has_changes


class TestSnapshotManager:
    def setup_method(self):
        self.manager = SnapshotManager()

    def test_create_and_restore(self, tmp_path):
        char = CharacterState(character_id="c1", name="林云", role="protagonist")
        state_storage.save_characters(tmp_path, [char])
        hook = Hook(hook_id="H001", content="伏笔1", type="mystery")
        state_storage.add_hook(tmp_path, hook)

        snap_path = self.manager.create_snapshot(tmp_path, 1)
        assert snap_path.exists()

        state_storage.save_characters(tmp_path, [])
        state_storage.save_hooks(tmp_path, [])

        self.manager.restore_snapshot(tmp_path, 1)
        chars = state_storage.load_characters(tmp_path)
        hooks = state_storage.load_hooks(tmp_path)
        assert len(chars) == 1
        assert len(hooks) == 1

    def test_list_snapshots(self, tmp_path):
        assert self.manager.list_snapshots(tmp_path) == []
        self.manager.create_snapshot(tmp_path, 1)
        self.manager.create_snapshot(tmp_path, 3)
        chapters = self.manager.list_snapshots(tmp_path)
        assert chapters == [1, 3]

    def test_delete_snapshot(self, tmp_path):
        self.manager.create_snapshot(tmp_path, 1)
        assert self.manager.delete_snapshot(tmp_path, 1) == True
        assert self.manager.delete_snapshot(tmp_path, 1) == False

    def test_restore_nonexistent(self, tmp_path):
        with pytest.raises(SnapshotNotFoundError):
            self.manager.restore_snapshot(tmp_path, 99)


class TestStateUpdaterAgent:
    def test_process_output(self):
        from novel_runtime.agents.state_updater import StateUpdaterAgent
        agent = StateUpdaterAgent.__new__(StateUpdaterAgent)
        yaml_output = """summary: 主角在拍卖会上展示鉴定能力
character_updates:
  - character_id: c1
    current_goal: 隐藏实力
new_hooks:
  - hook_id: H012
    content: 神秘人关注主角
    type: mystery
triggered_hooks:
  - H007
next_chapter_suggestions:
  - 神秘势力调查主角
  - 赵坤报复
bible_update_needed: false
"""
        result = agent.process_output(yaml_output, {})
        assert result.success
        assert result.data.summary == "主角在拍卖会上展示鉴定能力"
        assert len(result.data.new_hooks) == 1
        assert len(result.data.next_chapter_suggestions) == 2
