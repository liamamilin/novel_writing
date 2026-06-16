from __future__ import annotations

import pytest


class TestMinimalLoop:
    """最小闭环测试 — 使用 Mock LLM，不依赖真实 API"""

    def test_step_1_create_project(self, full_project):
        project, project_svc, tmp_path = full_project
        assert project.project_id.startswith("novel_")
        project_path = tmp_path / project.project_id
        assert project_path.exists()
        assert (project_path / "project.yaml").exists()
        assert (project_path / "states" / "story_state.yaml").exists()

    def test_step_2_style_analysis(self, full_project):
        from novel_runtime.config import Settings
        from novel_runtime.llm.prompt_loader import PromptLoader
        from novel_runtime.services.style_service import StyleService

        project, project_svc, tmp_path = full_project
        from unittest.mock import MagicMock

        from tests.e2e.conftest import mock_e2e_provider
        provider = MagicMock()
        provider.generate_with_usage.return_value = (
            "narration: 第三人称贴身视角\nsentence_rhythm: 短句为主\ndialogue_style: 直接冲突型\n"
            "description_density: 中等\nemotion_curve: 铺垫→爆发\nconflict_pattern: 外部冲突\n"
            "chapter_opening: 冲突开场\nchapter_ending: 悬念收尾\nscene_density: 中等\navoid:\n  - 大段说明\n",
            {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        provider.generate.return_value = provider.generate_with_usage.return_value[0]
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir(exist_ok=True)
        (prompts_dir / "style_analysis.md").write_text("test {{samples}}")
        loader = PromptLoader(prompts_dir)
        style_svc = StyleService(
            project_svc.db, project_svc, provider, loader, Settings(storage_base_path=str(tmp_path)),
        )
        sample_id = style_svc.upload_sample(project.project_id, "测试样本", "样本文本内容")
        style = style_svc.analyze_style_sync(project.project_id, [sample_id], "都市快节奏", run_adversarial=False)
        assert style.style_id is not None
        assert "短句" in style.sentence_rhythm

    def test_step_3_context_compile(self, full_project):
        from unittest.mock import MagicMock

        from novel_runtime.config import Settings
        from novel_runtime.llm.prompt_loader import PromptLoader
        from novel_runtime.llm.provider import create_provider
        from novel_runtime.models.style import StyleAsset
        from novel_runtime.services.context_service import ContextService
        from novel_runtime.storage import style_storage

        project, project_svc, tmp_path = full_project
        project_path = tmp_path / project.project_id
        style = StyleAsset(style_id="style_001", style_name="测试", narration="第三人称")
        style_storage.save_style_asset(project_path, style)
        from novel_runtime.models.project import ProjectUpdate
        project_svc.update_project(project.project_id, ProjectUpdate(default_style_id="style_001"))

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir(exist_ok=True)
        (prompts_dir / "context_compile.md").write_text("{{raw_context}} {{health_report}}")
        loader = PromptLoader(prompts_dir)
        provider = MagicMock()
        provider.generate_with_usage.return_value = (
            "## Project Info\ntest\n## Style Asset\ntest\n## Character Voices\ntest\n"
            "## Global Story Context\ntest\n## Narrative Diagnosis\ntest\n## Subplot Status\ntest\n"
            "## Recent Chapters\ntest\n## Current State\ntest\n## Character State\ntest\n"
            "## Hooks\ntest\n## Chapter Goal\ntest\n## Generation Constraints\ntest\n## Writing Strategy\ntest",
            {"prompt_tokens": 30, "completion_tokens": 20, "total_tokens": 50},
        )
        provider.generate.return_value = provider.generate_with_usage.return_value[0]
        ctx_svc = ContextService(project_svc, provider, loader)
        result = ctx_svc.compile_context(project.project_id, 1, "主角首次登场")
        assert "context_pack_path" in result
        assert "health_issues" in result

    def test_step_4_chapter_plan(self, full_project):
        from unittest.mock import MagicMock

        from novel_runtime.llm.prompt_loader import PromptLoader
        from novel_runtime.models.project import ProjectUpdate
        from novel_runtime.models.style import StyleAsset
        from novel_runtime.services.chapter_service import ChapterService
        from novel_runtime.storage import style_storage

        project, project_svc, tmp_path = full_project
        project_path = tmp_path / project.project_id
        style = StyleAsset(style_id="style_001", style_name="测试", narration="第三人称")
        style_storage.save_style_asset(project_path, style)
        project_svc.update_project(project.project_id, ProjectUpdate(default_style_id="style_001"))
        project_svc.create_chapter(project.project_id, 1)
        project_path = tmp_path / project.project_id
        ch_dir = project_path / "chapters" / "chapter_001"
        ch_dir.mkdir(parents=True, exist_ok=True)
        (ch_dir / "context_pack.md").write_text("## Context\ntest")
        (ch_dir / "chapter.yaml").write_text("chapter_id: chapter_001\nchapter_number: 1\nstatus: planned\n")

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir(exist_ok=True)
        (prompts_dir / "chapter_plan.md").write_text("{{context_pack}} {{strategy_summary}}")
        (prompts_dir / "context_compile.md").write_text("{{raw_context}}")
        loader = PromptLoader(prompts_dir)
        provider = MagicMock()
        provider.generate_with_usage.return_value = (
            "## Agent Contract\npromises:\n- test\nconstraints:\n- test\n"
            "## Chapter Goal\ntest\n## Reader Promise\ntest\n"
            "## Rhythm Plan\n本章节奏类型：递进型\n本章在卷中的节奏角色：铺垫\n与前一章的节奏关系：延续加速\n"
            "爽点投放时机：场景2\n压力累积时机：场景1\n"
            "## Subplot Allocation\ntest\n## Conflict\ntest\n"
            "## Scene List\n### Scene 1\n地点：都市\n出场人物：主角\n冲突：寻找\n预期字数：1500\n"
            "### Scene 2\n地点：郊区\n出场人物：反派\n冲突：对抗\n预期字数：1500\n"
            "## Ending Hook\n悬念\n",
            {"prompt_tokens": 30, "completion_tokens": 40, "total_tokens": 70},
        )
        provider.generate.return_value = provider.generate_with_usage.return_value[0]
        from novel_runtime.services.context_service import ContextService
        ctx_svc = ContextService(project_svc, provider, loader)
        ch_svc = ChapterService(project_svc, ctx_svc, provider, loader)
        result = ch_svc.generate_plan(project.project_id, 1, "测试")
        if result.get("plan_path"):
            assert "chapter_plan.md" in result["plan_path"]

    def test_step_5_state_snapshot(self, full_project):
        from novel_runtime.models.character import CharacterState
        from novel_runtime.storage import state_storage
        from novel_runtime.storage.snapshot_storage import SnapshotManager

        project, project_svc, tmp_path = full_project
        project_path = tmp_path / project.project_id
        char = CharacterState(character_id="c1", name="林云", role="protagonist")
        state_storage.save_characters(project_path, [char])

        mgr = SnapshotManager()
        snap = mgr.create_snapshot(project_path, 1)
        assert snap.exists()

        state_storage.save_characters(project_path, [])
        mgr.restore_snapshot(project_path, 1)
        chars = state_storage.load_characters(project_path)
        assert len(chars) == 1
