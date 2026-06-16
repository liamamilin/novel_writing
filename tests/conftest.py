import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def tmp_project():
    path = Path(tempfile.mkdtemp(prefix="nwr_test_"))
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def mock_llm_provider():
    provider = MagicMock()
    provider.generate.return_value = ""
    provider.generate_with_usage.return_value = ("", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    return provider


@pytest.fixture
def sample_project(tmp_project):
    project_dir = tmp_project / "novel_test_001"
    project_dir.mkdir(parents=True)
    subdirs = ["style_assets", "source_texts", "bible", "strategies", "chapters", "subplots", "states", "snapshots"]
    for d in subdirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)
    from novel_runtime.models.project import Project
    project = Project(project_name="测试项目", genre="都市")
    return project_dir, project


@pytest.fixture
def db_session(tmp_path):
    db_path = tmp_path / "test.db"
    from novel_runtime.db.database import Database
    db = Database(str(db_path))
    db.init_db()
    yield db
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def mock_style_llm_provider():
    provider = MagicMock()
    provider.generate.return_value = """narration: 第三人称贴身视角
sentence_rhythm: 短句为主
dialogue_style: 直接冲突型
description_density: 动作描写40%，环境描写30%，心理描写30%
emotion_curve: 压迫感→反击→爽感释放
conflict_pattern: 外部冲突驱动
chapter_opening: 冲突开场
chapter_ending: 悬念收尾
scene_density: 每300字一次冲突变化
avoid:
  - 大段设定说明
  - 连续心理独白
  - 过度形容
conditional_rules:
  - condition: fight_scene
    adjustments:
      sentence_rhythm: 极短句，断点式推进
      description_density: 动作描写为主，环境描写最小化
  - condition: emotional_scene
    adjustments:
      sentence_rhythm: 中长句，铺垫后短句爆发
      dialogue_style: 对白克制，留白多
"""
    provider.generate_with_usage.return_value = (provider.generate.return_value, {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
    return provider
