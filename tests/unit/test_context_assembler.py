from __future__ import annotations

from pathlib import Path

import pytest

from novel_runtime.compiler.context_assembler import ContextAssembler
from novel_runtime.db.database import Database
from novel_runtime.llm.token_counter import TokenBudgetManager
from novel_runtime.models.project import ProjectCreate
from novel_runtime.models.style import ConditionalRule, StyleAsset
from novel_runtime.services.project_service import ProjectService
from novel_runtime.services.style_service import StyleService
from novel_runtime.storage import bible_storage, state_storage, style_storage


@pytest.fixture
def env(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.init_db()
    project_svc = ProjectService(db, tmp_path)
    project = project_svc.create_project(ProjectCreate(project_name="测试", genre="都市", idea="测试创意"))
    project_path = tmp_path / project.project_id
    style = StyleAsset(
        style_id="style_001",
        style_name="测试文风",
        narration="第三人称",
        sentence_rhythm="短句为主",
        dialogue_style="直接冲突型",
        avoid=["大段设定"],
    )
    style_storage.save_style_asset(project_path, style)
    from novel_runtime.models.project import ProjectUpdate
    project_svc.update_project(project.project_id, ProjectUpdate(default_style_id="style_001"))
    return project, project_path, project_svc


class TestContextAssembler:
    def test_assemble_basic(self, env):
        project, project_path, _ = env
        assembler = ContextAssembler(project_path.parent)
        rc = assembler.assemble(project.project_id, 1, "主角首次登场", "style_001")
        assert rc.project_id == project.project_id
        assert rc.chapter_id == "chapter_001"
        assert "第三人称" in rc.style_and_voices_content
        assert "主角首次登场" == rc.chapter_goal_content
        assert rc.total_tokens > 0
        pass

    def test_assemble_with_locale(self, env):
        project, project_path, _ = env
        state_storage.save_story_state(project_path, {
            "current_location": "云海市",
            "current_time": "傍晚",
            "current_conflict": "拍卖会冲突",
            "protagonist_status": "隐藏身份中",
        })
        from novel_runtime.models.character import CharacterState
        char = CharacterState(character_id="char_001", name="林云", role="protagonist")
        state_storage.save_characters(project_path, [char])

        assembler = ContextAssembler(project_path.parent)
        rc = assembler.assemble(project.project_id, 1, "拍卖会", "style_001")
        assert "云海市" in rc.current_state_content
        assert "林云" in rc.character_state_content
        pass

    def test_assemble_no_style(self, env):
        project, project_path, _ = env
        from novel_runtime.exceptions import StyleNotSetError
        assembler = ContextAssembler(project_path.parent)
        try:
            assembler.assemble(project.project_id, 1, "test", "nonexistent")
            assert False, "Expected StyleNotSetError"
        except StyleNotSetError:
            pass

    def test_assemble_project_not_found(self, tmp_path):
        assembler = ContextAssembler(tmp_path)
        from novel_runtime.exceptions import ProjectNotFoundError
        try:
            assembler.assemble("nonexistent", 1, "test", "style_001")
            assert False, "Expected ProjectNotFoundError"
        except ProjectNotFoundError:
            pass

    def test_token_budget_within(self):
        mgr = TokenBudgetManager(total_budget=10000)
        sections = {"a": "hello", "b": "world"}
        result = mgr.allocate(sections)
        assert result["a"] == "hello"
        assert result["b"] == "world"
        pass

    def test_token_budget_over(self):
        mgr = TokenBudgetManager(
            total_budget=20,
            allocation={"a": 100, "b": 10},
            priority_order=["a", "b"],
        )
        sections = {"a": "Short text here", "b": "Very long " * 50 + "end"}
        result = mgr.allocate(sections)
        assert result["a"] == sections["a"]
        assert len(result["b"]) < len(sections["b"])
        pass

    def test_summarize_section(self):
        mgr = TokenBudgetManager()
        text = "第一段内容。\n第二段内容。\n第三段内容。\n第四段内容。\n"
        full = mgr.summarize_section(text, "full")
        assert full == text
        reduced = mgr.summarize_section(text, "reduced")
        assert "第一段" in reduced
        assert "第四段" in reduced
        minimal = mgr.summarize_section(text, "minimal")
        assert len(minimal) <= len(text)
        pass

    def test_assemble_to_markdown(self, env):
        project, project_path, _ = env
        assembler = ContextAssembler(project_path.parent)
        md = assembler.assemble_to_markdown(project.project_id, 1, "测试", "style_001")
        assert "# Context Pack" in md
        assert "项目ID:" in md
        assert "Token 统计:" in md
        pass
