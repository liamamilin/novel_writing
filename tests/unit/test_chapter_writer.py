from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from novel_runtime.llm.state_annotations_validator import StateAnnotationsValidator


class TestStateAnnotationsValidator:
    def setup_method(self):
        self.validator = StateAnnotationsValidator()

    def test_valid_annotations(self):
        yaml_input = """annotations:
  - location: scene_1_paragraph_3
    type: character_state_change
    character: 林云
    change: 从隐藏到部分暴露
    trigger: 展示鉴定能力
  - location: scene_2_paragraph_5
    type: new_hook
    character: 神秘人
    change: 关注主角
    trigger: 拍卖会事件
  - location: scene_3_paragraph_1
    type: subplot_advance
    character: 赵坤
    change: 敌意增强
    trigger: 公开质疑
"""
        result = self.validator.validate(yaml_input)
        assert result.is_valid, f"Expected valid: {result.errors}"

    def test_missing_required_type(self):
        yaml_input = """annotations:
  - location: scene_1_1
    type: character_state_change
    character: 林云
    change: test
    trigger: test
"""
        self.validator.required_types = ["new_hook", "character_state_change"]
        result = self.validator.validate(yaml_input)
        assert not result.is_valid
        assert any("new_hook" in e for e in result.errors)

    def test_invalid_yaml(self):
        result = self.validator.validate("not: yaml: [")
        assert not result.is_valid

    def test_missing_location(self):
        yaml_input = """annotations:
  - type: character_state_change
    change: test
"""
        result = self.validator.validate(yaml_input)
        assert not result.is_valid


class TestChapterWriterAgent:
    def test_process_output_with_annotations(self):
        from novel_runtime.agents.chapter_writer import ChapterWriterAgent
        agent = ChapterWriterAgent.__new__(ChapterWriterAgent)
        sample = """### Scene 1
主角走进拍卖会。

### Scene 2
冲突爆发。

---ANNOTATIONS---
annotations:
  - location: scene_1_1
    type: character_state_change
    character: 主角
    change: 进入拍卖会
    trigger: 到达
  - location: scene_2_1
    type: new_hook
    character: 神秘人
    change: 关注主角
    trigger: 拍卖会
  - location: scene_2_2
    type: subplot_advance
    character: 赵坤
    change: 敌意
    trigger: 冲突
"""
        result = agent.process_output(sample, {})
        assert result.success, f"Expected success: {result.validation_errors}"
        data = result.data
        assert "### Scene 1" in data.draft
        assert "Scene 2" in data.draft
        assert data.annotations.get("annotations") is not None

    def test_process_output_no_annotations(self):
        from novel_runtime.agents.chapter_writer import ChapterWriterAgent
        agent = ChapterWriterAgent.__new__(ChapterWriterAgent)
        result = agent.process_output("### Scene 1\nContent\n", {})
        assert result.success
        assert "Scene 1" in result.data.draft

    def test_process_output_with_contract_check(self):
        from novel_runtime.agents.chapter_writer import ChapterWriterAgent
        agent = ChapterWriterAgent.__new__(ChapterWriterAgent)
        draft_text = "主角出场了。冲突爆发了。"
        sample = f"""{draft_text}

---ANNOTATIONS---
annotations:
  - location: scene_1_1
    type: character_state_change
    character: 主角
    change: test
    trigger: test
  - location: scene_2_1
    type: new_hook
    character: 配角
    change: test
    trigger: test
  - location: scene_2_2
    type: subplot_advance
    character: 反派
    change: test
    trigger: test
"""
        result = agent.process_output(sample, {
            "promises": ["主角出场"],
            "constraints": ["字数3000"],
            "contract_text": "test",
        })
        assert result.success
        assert "promises_fulfilled" in result.data.contract_check


class TestNarrativePolisherAgent:
    def test_process_output(self):
        from novel_runtime.agents.narrative_polisher import NarrativePolisherAgent
        agent = NarrativePolisherAgent.__new__(NarrativePolisherAgent)
        result = agent.process_output("润色后的文本", {})
        assert result.success
        assert result.data == "润色后的文本"

    def test_polish_returns_text(self):
        from novel_runtime.agents.narrative_polisher import NarrativePolisherAgent
        from unittest.mock import MagicMock
        mock_provider = MagicMock()
        mock_provider.generate_with_usage.return_value = ("润色结果", {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})
        agent = NarrativePolisherAgent(provider=mock_provider, prompt_loader=MagicMock())
        agent.prompt_loader.load.return_value = "DRAFT: {{draft}}"
        result = agent.polish("草稿", "style", "escalation", "voices", "summary")
        assert result.success
