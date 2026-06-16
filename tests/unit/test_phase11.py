from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from novel_runtime.compiler.fix_instruction_merger import merge_all_reviews


class TestCrossChapterAuditor:
    def test_process_output(self):
        from novel_runtime.agents.cross_chapter_auditor import CrossChapterAuditorAgent
        agent = CrossChapterAuditorAgent.__new__(CrossChapterAuditorAgent)
        sample = """## Rhythm Analysis
连续3章递进，节奏重复
## Subplot Status
感情线4章未推进
## Hook Status
开放伏笔6/8
## Character Development
主角有发展
## Strategy Compliance
符合策略
"""
        result = agent.process_output(sample, {})
        assert result.success
        assert "Rhythm Analysis" in result.data.review_content

    def test_validator(self):
        from novel_runtime.agents.cross_chapter_auditor import CrossChapterAuditorAgent
        agent = CrossChapterAuditorAgent.__new__(CrossChapterAuditorAgent)
        validator = agent.get_validator()
        valid = """## Rhythm Analysis
ok
## Subplot Status
ok
## Hook Status
ok
## Character Development
ok
## Strategy Compliance
ok
"""
        result = validator.validate(valid)
        assert result.is_valid


class TestReaderSimulator:
    def test_process_output(self):
        from novel_runtime.agents.reader_simulator import ReaderSimulatorAgent
        agent = ReaderSimulatorAgent.__new__(ReaderSimulatorAgent)
        sample = """## Engagement Prediction
兴奋点: scene_2
## Abandonment Risk
弃书风险评分: 3
## Reader Expectation
下一章: 揭秘
"""
        result = agent.process_output(sample, {})
        assert result.success
        assert "弃书风险" in result.data.review_content


class TestMergeAllReviews:
    def test_merge_with_cross_chapter(self):
        result = merge_all_reviews(
            continuity_issues=[],
            quality_scores={},
            quality_problems=[],
            cross_chapter_text="连续同节奏",
            reader_sim_text="弃书风险评分: 5",
        )
        assert len(result.fix_instructions) >= 1

    def test_merge_with_high_risk(self):
        result = merge_all_reviews(
            continuity_issues=[],
            quality_scores={},
            quality_problems=[],
            cross_chapter_text="",
            reader_sim_text="弃书风险评分: 9",
        )
        assert len(result.fix_instructions) >= 1
        assert result.fix_instructions[0].severity == "critical"

    def test_merge_max_10(self):
        issues = [
            {"type": "人物", "location": f"s{i}", "problem": f"p{i}",
             "severity": "critical", "suggested_fix": "fix"}
            for i in range(8)
        ]
        result = merge_all_reviews(
            continuity_issues=issues,
            quality_scores={"开头": 3, "节奏": 4, "冲突": 5, "对白": 3, "文风": 5},
            quality_problems=[],
            cross_chapter_text="连续同节奏",
            reader_sim_text="弃书风险评分: 7",
        )
        assert len(result.fix_instructions) <= 10
