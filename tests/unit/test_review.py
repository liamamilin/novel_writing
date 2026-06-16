from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from novel_runtime.compiler.fix_instruction_merger import merge_reviews
from novel_runtime.llm.prompt_loader import PromptLoader


class TestFixInstructionMerger:
    def test_merge_continuity_issues(self):
        issues = [
            {"type": "人物状态", "location": "scene_2", "problem": "角色位置矛盾",
             "severity": "critical", "suggested_fix": "修改为正确位置"},
            {"type": "时间线", "location": "scene_3", "problem": "时间跳跃",
             "severity": "moderate", "suggested_fix": "调整时间描述"},
        ]
        result = merge_reviews(issues, {}, [], "")
        assert len(result.fix_instructions) == 2
        assert result.fix_instructions[0].severity == "critical"
        assert result.fix_instructions[0].fix_id == "FIX_001"

    def test_merge_quality_scores(self):
        scores = {"开头": 5, "冲突": 7, "节奏": 4}
        result = merge_reviews([], scores, [], "")
        [f.fix_id for f in result.fix_instructions]
        # scores < 6 should generate fix instructions
        assert any(f.severity == "low" and "开头" in f.problem for f in result.fix_instructions)
        assert any(f.severity == "low" and "节奏" in f.problem for f in result.fix_instructions)

    def test_max_instructions(self):
        issues = [
            {"type": "人物", "location": f"s{i}", "problem": f"p{i}",
             "severity": "critical", "suggested_fix": "fix"}
            for i in range(15)
        ]
        result = merge_reviews(issues, {}, [], "")
        assert len(result.fix_instructions) <= 10

    def test_sort_by_severity(self):
        issues = [
            {"type": "a", "location": "1", "problem": "low",
             "severity": "low", "suggested_fix": "fix"},
            {"type": "b", "location": "2", "problem": "critical",
             "severity": "critical", "suggested_fix": "fix"},
            {"type": "c", "location": "3", "problem": "moderate",
             "severity": "moderate", "suggested_fix": "fix"},
        ]
        result = merge_reviews(issues, {}, [], "")
        severities = [f.severity for f in result.fix_instructions]
        assert severities == sorted(severities, key=lambda x: {"critical": 0, "moderate": 1, "low": 2}.get(x, 3))


class TestContinuityAuditorAgent:
    def test_process_output_with_issues(self):
        from novel_runtime.agents.continuity_auditor import ContinuityAuditorAgent
        agent = ContinuityAuditorAgent.__new__(ContinuityAuditorAgent)
        sample = """## Summary
发现2个问题

## Issues

### Issue 1
问题类型：人物状态
问题位置：scene_2
问题说明：角色位置矛盾
严重程度：critical
修改动作：修改位置
"""
        result = agent.process_output(sample, {})
        assert result.success
        assert len(result.data.issues) >= 1

    def test_process_output_no_issues(self):
        from novel_runtime.agents.continuity_auditor import ContinuityAuditorAgent
        agent = ContinuityAuditorAgent.__new__(ContinuityAuditorAgent)
        sample = """## Summary
未发现连续性错误
## Issues
"""
        result = agent.process_output(sample, {})
        assert result.success


class TestQualityAuditorAgent:
    def test_process_output_with_scores(self):
        from novel_runtime.agents.quality_auditor import QualityAuditorAgent
        agent = QualityAuditorAgent.__new__(QualityAuditorAgent)
        sample = """## Score
开头：8
冲突：7
节奏：6
文风：8

## Main Problems
问题1：节奏略慢

## Rewrite Suggestions
建议加速
"""
        result = agent.process_output(sample, {})
        assert result.success
        assert result.data.scores.get("开头") == 8
        assert len(result.data.problems) >= 1

    def test_process_output_empty(self):
        from novel_runtime.agents.quality_auditor import QualityAuditorAgent
        agent = QualityAuditorAgent.__new__(QualityAuditorAgent)
        result = agent.process_output("", {})
        assert result.success
