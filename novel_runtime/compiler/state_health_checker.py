from __future__ import annotations

from pathlib import Path

from novel_runtime.models.health_report import HealthIssue, StateHealthReport
from novel_runtime.models.strategy import WritingStrategy
from novel_runtime.storage import state_storage, subplot_storage
from novel_runtime.storage.chapter_storage import load_chapter_file
from novel_runtime.storage.project_storage import ProjectStorage


class StateHealthChecker:
    def check(self, project_path: Path, chapter_number: int, strategy: WritingStrategy) -> StateHealthReport:
        report = StateHealthReport(chapter_id=f"chapter_{chapter_number:03d}")
        issues = []

        try:
            issues.extend(self._check_character_idle(project_path, strategy))
        except Exception:
            pass
        try:
            issues.extend(self._check_hook_overdue(project_path, chapter_number))
        except Exception:
            pass
        try:
            issues.extend(self._check_hook_overload(project_path, strategy))
        except Exception:
            pass
        try:
            issues.extend(self._check_subplot_neglect(project_path, strategy))
        except Exception:
            pass
        try:
            issues.extend(self._check_subplot_overload(project_path, strategy))
        except Exception:
            pass
        try:
            issues.extend(self._check_protagonist_absent(project_path, chapter_number, strategy))
        except Exception:
            pass
        try:
            issues.extend(self._check_rhythm_repetition(project_path, chapter_number))
        except Exception:
            pass
        try:
            issues.extend(self._check_new_character_density(project_path, chapter_number, strategy))
        except Exception:
            pass

        issues.sort(key=lambda x: {"critical": 0, "warning": 1, "info": 2}.get(x.severity, 3))
        report.issues = issues
        return report

    def _check_character_idle(self, project_path: Path, strategy: WritingStrategy) -> list[HealthIssue]:
        issues = []
        characters = state_storage.load_characters(project_path)
        freq = strategy.character_policy.character_development_frequency
        for c in characters:
            if c.narrative_role.chapters_since_development > freq and c.role != "minor":
                issues.append(HealthIssue(
                    type="character_idle",
                    severity="warning",
                    description=f"{c.name}已{c.narrative_role.chapters_since_development}章没有实质性发展",
                    suggestion=f"在接下来的2章内给予{c.name}角色发展机会",
                    character_id=c.character_id,
                ))
        return issues

    def _check_hook_overdue(self, project_path: Path, chapter_number: int) -> list[HealthIssue]:
        issues = []
        hooks = state_storage.load_hooks(project_path)
        for h in hooks:
            if h.status not in ("open", "triggered"):
                continue
            try:
                src = int(h.source_chapter.split("_")[-1])
            except (ValueError, IndexError):
                continue
            if src + h.reader_patience < chapter_number:
                issues.append(HealthIssue(
                    type="hook_overdue",
                    severity="critical",
                    description=f"伏笔{h.hook_id}已超出计划回收范围{chapter_number - src - h.reader_patience}章",
                    suggestion="在最近2章内回收或推进此伏笔",
                    hook_id=h.hook_id,
                ))
        return issues

    def _check_hook_overload(self, project_path: Path, strategy: WritingStrategy) -> list[HealthIssue]:
        open_hooks = len(state_storage.get_open_hooks(project_path))
        max_hooks = strategy.hook_policy.max_open_hooks
        if open_hooks > max_hooks:
            return [HealthIssue(
                type="hook_overload",
                severity="warning",
                description=f"开放伏笔{open_hooks}个，超过上限{max_hooks}",
                suggestion=f"考虑在最近几章回收一些伏笔，降低到{max_hooks}以下",
            )]
        return []

    def _check_subplot_neglect(self, project_path: Path, strategy: WritingStrategy) -> list[HealthIssue]:
        issues = []
        subplots = subplot_storage.load_subplots(project_path)
        max_gap = strategy.subplot_policy.max_gap_between_advances
        for s in subplots:
            if s.status == "resolved":
                continue
            idle = s.chapters_since_advance + 1
            if idle > max_gap:
                issues.append(HealthIssue(
                    type="subplot_neglect",
                    severity="warning",
                    description=f"子线'{s.name}'已{idle}章未推进",
                    suggestion="下一章需要推进此子线",
                    subplot_id=s.subplot_id,
                ))
        return issues

    def _check_subplot_overload(self, project_path: Path, strategy: WritingStrategy) -> list[HealthIssue]:
        active = [s for s in subplot_storage.load_subplots(project_path) if s.status != "resolved"]
        max_active = strategy.subplot_policy.max_simultaneous
        if len(active) > max_active:
            return [HealthIssue(
                type="subplot_overload",
                severity="warning",
                description=f"同时活跃子线{len(active)}条，超过上限{max_active}",
                suggestion="考虑推进部分子线到解决状态",
            )]
        return []

    def _check_protagonist_absent(self, project_path: Path, chapter_number: int, strategy: WritingStrategy) -> list[HealthIssue]:
        issues = []
        max_absent = strategy.character_policy.max_scenes_without_protagonist
        absent = 0
        for n in range(max(1, chapter_number - max_absent), chapter_number):
            try:
                draft = load_chapter_file(project_path, n, "draft")
                if draft and "主角" not in draft and "主人公" not in draft:
                    absent += 1
            except FileNotFoundError:
                continue
        if absent > max_absent:
            issues.append(HealthIssue(
                type="protagonist_absent",
                severity="warning",
                description=f"主角已连续{absent}章未出现",
                suggestion="确保下一章主角出场",
            ))
        return issues

    def _check_rhythm_repetition(self, project_path: Path, chapter_number: int) -> list[HealthIssue]:
        rhythm_types = []
        for n in range(max(1, chapter_number - 3), chapter_number):
            try:
                chapter = ProjectStorage(project_path.parent).load_chapter(project_path.name, n)
                if chapter.rhythm_type:
                    rhythm_types.append(chapter.rhythm_type)
            except Exception:
                continue
        if len(rhythm_types) >= 3 and len(set(rhythm_types[-3:])) == 1:
            return [HealthIssue(
                type="rhythm_repetition",
                severity="warning",
                description=f"连续{len(rhythm_types)}章节奏类型相同（{rhythm_types[-1]}）",
                suggestion="下一章建议使用不同的节奏类型",
            )]
        return []

    def _check_new_character_density(self, project_path: Path, chapter_number: int, strategy: WritingStrategy) -> list[HealthIssue]:
        rate = strategy.character_policy.new_character_introduction_rate
        total_chars = len(state_storage.load_characters(project_path))
        expected_max = chapter_number // rate + 1
        if total_chars > expected_max + 1:
            return [HealthIssue(
                type="new_character_density",
                severity="info",
                description=f"已引入{total_chars}个角色（预期最多{expected_max}），建议控制新角色引入节奏",
                suggestion=f"每{rate}章引入1个新角色为宜",
            )]
        return []
