from __future__ import annotations
from pathlib import Path

import pytest

from novel_runtime.compiler.state_health_checker import StateHealthChecker
from novel_runtime.models.character import CharacterState, NarrativeRole
from novel_runtime.models.hook import Hook
from novel_runtime.models.subplot import Subplot
from novel_runtime.models.strategy import WritingStrategy
from novel_runtime.storage import state_storage, subplot_storage


@pytest.fixture
def env(tmp_path):
    checker = StateHealthChecker()
    strategy = WritingStrategy()
    return tmp_path, checker, strategy


class TestStateHealthChecker:
    def test_no_issues(self, env):
        path, checker, strategy = env
        report = checker.check(path, 1, strategy)
        assert len(report.issues) == 0

    def test_character_idle(self, env):
        path, checker, strategy = env
        char = CharacterState(
            character_id="c1", name="林云", role="protagonist",
        )
        char.narrative_role.chapters_since_development = 10
        state_storage.save_characters(path, [char])
        report = checker.check(path, 5, strategy)
        idle_issues = [i for i in report.issues if i.type == "character_idle"]
        assert len(idle_issues) >= 1

    def test_hook_overdue(self, env):
        path, checker, strategy = env
        hook = Hook(hook_id="H001", source_chapter="chapter_001", reader_patience=3, status="open")
        state_storage.add_hook(path, hook)
        report = checker.check(path, 10, strategy)
        overdue = [i for i in report.issues if i.type == "hook_overdue"]
        assert len(overdue) >= 1
        assert overdue[0].severity == "critical"

    def test_hook_overload(self, env):
        path, checker, strategy = env
        for i in range(15):
            state_storage.add_hook(path, Hook(
                hook_id=f"H{i:03d}", content=f"hook{i}", status="open"
            ))
        report = checker.check(path, 1, strategy)
        overload = [i for i in report.issues if i.type == "hook_overload"]
        assert len(overload) >= 1

    def test_subplot_neglect(self, env):
        path, checker, strategy = env
        sp = Subplot(subplot_id="sp1", name="感情线", status="escalating", chapters_since_advance=10)
        subplot_storage.save_subplots(path, [sp])
        report = checker.check(path, 5, strategy)
        neglect = [i for i in report.issues if i.type == "subplot_neglect"]
        assert len(neglect) >= 1

    def test_rhythm_repetition(self, env):
        path, checker, strategy = env
        project_name = "project"
        project_path = path / project_name
        from novel_runtime.models.chapter import Chapter
        from novel_runtime.storage.base import write_yaml_model
        chapters_dir = project_path / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)
        for n in range(1, 5):
            ch = Chapter(chapter_id=f"chapter_{n:03d}", chapter_number=n, rhythm_type="escalation")
            ch_dir = chapters_dir / f"chapter_{n:03d}"
            ch_dir.mkdir(exist_ok=True)
            write_yaml_model(ch_dir / "chapter.yaml", ch, overwrite=True)
        report = checker.check(project_path, 5, strategy)
        rhythm = [i for i in report.issues if i.type == "rhythm_repetition"]
        assert len(rhythm) >= 1

    def test_subplot_overload(self, env):
        path, checker, strategy = env
        sps = [Subplot(subplot_id=f"sp{i}", name=f"s{i}", status="escalating") for i in range(5)]
        subplot_storage.save_subplots(path, sps)
        report = checker.check(path, 1, strategy)
        overload = [i for i in report.issues if i.type == "subplot_overload"]
        assert len(overload) >= 1

    def test_issues_sorted_by_severity(self, env):
        path, checker, strategy = env
        hook = Hook(hook_id="H001", source_chapter="chapter_001", reader_patience=1, status="open")
        state_storage.add_hook(path, hook)
        char = CharacterState(character_id="c1", name="林云", role="protagonist")
        char.narrative_role.chapters_since_development = 10
        state_storage.save_characters(path, [char])
        report = checker.check(path, 10, strategy)
        severities = [i.severity for i in report.issues]
        assert severities == sorted(severities, key=lambda x: {"critical": 0, "warning": 1, "info": 2}.get(x, 3))
