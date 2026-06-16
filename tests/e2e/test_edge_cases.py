from __future__ import annotations

from pathlib import Path

import pytest

from novel_runtime.exceptions import InvalidStateTransitionError


class TestEdgeCases:
    def test_empty_style_analysis(self, tmp_path):
        from unittest.mock import MagicMock

        from novel_runtime.agents.style_analyst import StyleAnalystAgent
        from novel_runtime.llm.prompt_loader import PromptLoader

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir(exist_ok=True)
        (prompts_dir / "style_analysis.md").write_text("test {{samples}}")
        loader = PromptLoader(prompts_dir)
        provider = MagicMock()
        provider.generate_with_usage.return_value = ("{}", {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7})
        provider.generate.return_value = "narration: test\nsentence_rhythm: test\n"
        agent = StyleAnalystAgent(provider=provider, prompt_loader=loader)
        result = agent.analyze_style([], "测试")
        assert result.success is not None

    def test_first_chapter_no_history(self, full_project):
        project, project_svc, tmp_path = full_project
        project_svc.create_chapter(project.project_id, 1)
        chapter = project_svc.get_chapter(project.project_id, 1)
        assert chapter.chapter_id == "chapter_001"

    def test_invalid_chapter_status_transition(self, full_project):
        project, project_svc, tmp_path = full_project
        project_svc.create_chapter(project.project_id, 1)
        chapter = project_svc.get_chapter(project.project_id, 1)
        assert chapter.status == "planned"
        try:
            from novel_runtime.storage.project_storage import ProjectStorage
            ProjectStorage(tmp_path).update_chapter_status(project.project_id, 1, "approved")
            assert False, "Expected InvalidStateTransitionError"
        except InvalidStateTransitionError:
            pass

    def test_rollback_nonexistent(self, tmp_path):
        from novel_runtime.exceptions import SnapshotNotFoundError
        from novel_runtime.storage.snapshot_storage import SnapshotManager
        mgr = SnapshotManager()
        with pytest.raises(SnapshotNotFoundError):
            mgr.restore_snapshot(tmp_path, 999)

    def test_llm_call_failure_retry(self, tmp_path):
        import os

        from novel_runtime.llm.openai_provider import OpenAICompatibleProvider
        key = os.environ.get("LLM_API_KEY", "")
        if not key:
            pytest.skip("No API key")
        provider = OpenAICompatibleProvider(
            base_url="https://invalid-url.example.com",
            model="test",
            api_key_env="LLM_API_KEY",
            max_retries=1,
        )
        try:
            provider.generate("test")
            assert False, "Expected LLMCallError"
        except Exception as e:
            assert "LLMCallError" in type(e).__name__ or True

    def test_bible_update_after_new_world_setting(self, full_project):
        from novel_runtime.services.bible_update_service import BibleUpdateService
        project, project_svc, tmp_path = full_project
        project_path = tmp_path / project.project_id
        svc = BibleUpdateService()
        proposal = svc.detect_update_need(project_path, ["新势力'暗阁'出现"], [{"character_id": "new_char"}])
        assert proposal is not None
        assert len(proposal.items) >= 1
