from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from novel_runtime.config import Settings
from novel_runtime.db.database import Database
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.models.project import ProjectCreate
from novel_runtime.models.style import StyleAsset, CharacterVoice
from novel_runtime.services.project_service import ProjectService
from novel_runtime.services.style_service import StyleService


@pytest.fixture
def style_env(tmp_path, mock_style_llm_provider):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.init_db()
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "style_analysis.md").write_text("分析以下样本文本：\n{{samples}}\n文风名称：{{style_name}}")
    (prompts_dir / "adversarial_test.md").write_text("文风参数：{style_params}\n偏离文字：{deviation_text}")
    loader = PromptLoader(prompts_dir)
    project_svc = ProjectService(db, tmp_path)
    config = Settings(storage_base_path=str(tmp_path))
    style_svc = StyleService(db, project_svc, mock_style_llm_provider, loader, config)
    project = project_svc.create_project(ProjectCreate(project_name="测试", genre="都市", idea="test"))
    return style_svc, project, mock_style_llm_provider, tmp_path


class TestStyleService:
    def test_upload_sample(self, style_env):
        svc, project, _, _ = style_env
        sample_id = svc.upload_sample(project.project_id, "样本1", "这是一段样本文本内容。")
        assert sample_id.startswith("sample_")

    def test_analyze_style_sync(self, style_env):
        svc, project, mock_provider, _ = style_env
        sample_id = svc.upload_sample(project.project_id, "样本1", "样本文本")
        style = svc.analyze_style_sync(project.project_id, [sample_id], "都市快节奏", run_adversarial=False)
        assert isinstance(style, StyleAsset)
        assert style.style_id.startswith("style_")
        assert len(style.avoid) >= 1

    def test_get_style(self, style_env):
        svc, project, mock_provider, tmp_path = style_env
        sample_id = svc.upload_sample(project.project_id, "样本1", "样本文本")
        style = svc.analyze_style_sync(project.project_id, [sample_id], "都市快节奏", run_adversarial=False)
        loaded = svc.get_style(project.project_id, style.style_id)
        assert loaded.style_id == style.style_id

    def test_list_styles(self, style_env):
        svc, project, mock_provider, _ = style_env
        assert svc.list_styles(project.project_id) == []
        sample_id = svc.upload_sample(project.project_id, "样本1", "样本文本")
        svc.analyze_style_sync(project.project_id, [sample_id], "文风1", run_adversarial=False)
        styles = svc.list_styles(project.project_id)
        assert len(styles) >= 1

    def test_character_voice(self, style_env):
        svc, project, _, _ = style_env
        voice = CharacterVoice(
            character_id="char_001",
            character_name="林雪",
            speech_patterns={"typical_phrases": ["原来如此"], "sentence_length": "中句"},
        )
        saved = svc.save_character_voice(project.project_id, voice)
        assert saved.voice_id.startswith("voice_")
        loaded = svc.get_character_voice(project.project_id, saved.voice_id)
        assert loaded.character_name == "林雪"
