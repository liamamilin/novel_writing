from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from novel_runtime.db.database import Database
from novel_runtime.models.hook import Hook
from novel_runtime.models.project import ProjectCreate
from novel_runtime.models.strategy import WritingStrategy
from novel_runtime.models.subplot import Subplot
from novel_runtime.services.hook_service import HookService
from novel_runtime.services.project_service import ProjectService
from novel_runtime.services.strategy_service import StrategyService
from novel_runtime.services.subplot_service import SubplotService
from novel_runtime.storage import state_storage, strategy_storage, subplot_storage


@pytest.fixture
def env(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.init_db()
    svc = ProjectService(db, tmp_path)
    project = svc.create_project(ProjectCreate(project_name="测试", genre="都市"))
    hook_svc = HookService(svc)
    subplot_svc = SubplotService(svc)
    strategy_svc = StrategyService(svc)
    return project, hook_svc, subplot_svc, strategy_svc


class TestHook:
    def test_add_and_list(self, env):
        project, svc, _, _ = env
        svc.add_hook(project.project_id, "伏笔内容", "chapter_001", "mystery", "high")
        hooks = svc.list_hooks(project.project_id)
        assert len(hooks) == 1
        assert hooks[0].type == "mystery"

    def test_trigger_and_resolve(self, env):
        project, svc, _, _ = env
        svc.add_hook(project.project_id, "伏笔2", "chapter_001")
        hooks = svc.list_hooks(project.project_id)
        hook_id = hooks[0].hook_id
        svc.trigger_hook(project.project_id, hook_id)
        hooks = svc.list_hooks(project.project_id, status="triggered")
        assert len(hooks) == 1
        svc.resolve_hook(project.project_id, hook_id, "已回收", "chapter_005")
        hooks = svc.list_hooks(project.project_id, status="resolved")
        assert len(hooks) == 1

    def test_chapter_hooks(self, env):
        project, svc, _, _ = env
        project_path = project.project_id
        svc.add_hook(project_path, "内容", "chapter_001", "mystery", "high")
        result = svc.get_chapter_hooks(project_path, 2)
        assert "can_trigger" in result
        assert "must_not_forget" in result


class TestSubplot:
    def test_create_and_list(self, env):
        project, _, svc, _ = env
        svc.create_subplot(project.project_id, "感情线", "romance", ["char_001"])
        all_sp = svc.list_subplots(project.project_id)
        assert len(all_sp) >= 1
        assert all_sp[0].type == "romance"

    def test_suggest_allocation(self, env):
        project, _, svc, _ = env
        svc.create_subplot(project.project_id, "主线", "main_plot")
        suggestion = svc.suggest_subplot_allocation(project.project_id, 3)
        assert "should_advance" in suggestion
        assert "should_idle" in suggestion


class TestStrategy:
    def test_get_default(self, env):
        project, _, _, svc = env
        strategy = svc.get_strategy(project.project_id)
        assert strategy.strategy_id == "strategy_default"

    def test_update(self, env):
        project, _, _, svc = env
        svc.update_strategy(project.project_id, {"name": "新策略"})
        strategy = svc.get_strategy(project.project_id)
        assert strategy.name == "新策略"

    def test_reset(self, env):
        project, _, _, svc = env
        svc.update_strategy(project.project_id, {"name": "新策略"})
        svc.reset_strategy(project.project_id)
        strategy = svc.get_strategy(project.project_id)
        assert strategy.name != "新策略"
