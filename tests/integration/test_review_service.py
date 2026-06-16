from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from novel_runtime.db.database import Database
from novel_runtime.services.project_service import ProjectService
from novel_runtime.models.project import ProjectCreate
from novel_runtime.llm.prompt_loader import PromptLoader
from pathlib import Path


@pytest.fixture
def review_env(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.init_db()
    project_svc = ProjectService(db, tmp_path)
    project = project_svc.create_project(ProjectCreate(project_name="测试", genre="都市"))

    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    for name in ["continuity_review", "quality_review"]:
        (prompts_dir / f"{name}.md").write_text(f"DRAFT: {{{{styled_draft}}}}")

    mock_provider = MagicMock()
    mock_provider.generate_with_usage.return_value = (
        "## Summary\nok\n## Issues\n### Issue 1\n问题类型：人物\n问题位置：scene_1\n问题说明：矛盾\n严重程度：critical\n修改动作：修改",
        {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    )

    from novel_runtime.services.review_service import ReviewService
    loader = PromptLoader(prompts_dir)
    svc = ReviewService(project_svc, mock_provider, loader)
    return project, svc, project_svc, tmp_path


class TestReviewIntegration:
    def test_fix_instructions_validator(self):
        from novel_runtime.llm.output_validator import FixInstructionsValidator
        validator = FixInstructionsValidator()

        valid = """fix_instructions:
  - fix_id: FIX_001
    type: continuity_violation
    severity: critical
    location: scene_2
    problem: 位置矛盾
    action: replace
    original_text: "..."
    suggested_fix: "修正"
    constraint: "保持逻辑"
"""
        result = validator.validate(valid)
        assert result.is_valid, f"Expected valid: {result.errors}"

        invalid = """fix_instructions:
  - fix_id: FIX_001
    type: a
    severity: invalid_severity
    location: ""
    action: invalid_action
"""
        result = validator.validate(invalid)
        assert not result.is_valid

        empty = "fix_instructions: []"
        result = validator.validate(empty)
        assert result.is_valid

    def test_continuity_review_validator(self):
        from novel_runtime.llm.output_validator import ContinuityReviewValidator
        validator = ContinuityReviewValidator()
        result = validator.validate("## Summary\ntest\n## Issues\n### Issue 1\ntest")
        assert result.is_valid

        result = validator.validate("## Summary\ntest")
        assert not result.is_valid

    def test_quality_review_validator(self):
        from novel_runtime.llm.output_validator import QualityReviewValidator
        validator = QualityReviewValidator()
        result = validator.validate("## Score\n开头：8\n## Main Problems\n问题\n## Rewrite Suggestions\n建议")
        assert result.is_valid

        result = validator.validate("## Score\n开头：8")
        assert not result.is_valid

    def test_review_service_continuity(self, review_env):
        project, svc, project_svc, tmp_path = review_env
        project_path = tmp_path / project.project_id
        chapters_dir = project_path / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)

        from novel_runtime.storage.project_storage import ProjectStorage
        from novel_runtime.models.chapter import Chapter
        chapter = Chapter(
            chapter_id="chapter_001", chapter_number=1, status="drafted",
        )
        chapter_dir = chapters_dir / "chapter_001"
        chapter_dir.mkdir(exist_ok=True)
        chapter_yaml = chapter_dir / "chapter.yaml"
        import yaml
        chapter_yaml.write_text(yaml.dump(chapter.model_dump()))
        (chapter_dir / "styled_draft.md").write_text("## Scene 1\n主角登场")
        (chapter_dir / "context_pack.md").write_text("## Info\ntest")
        (chapter_dir / "plan.md").write_text("## Plan\ntest")

        result = svc.review_chapter(project.project_id, 1, ["continuity"])
        assert "continuity" in result.get("review_paths", {})
