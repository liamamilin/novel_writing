from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from novel_runtime.compiler.plan_validator import PlanValidator
from novel_runtime.models.chapter import AgentContract, ChapterPlanRhythm
from novel_runtime.models.strategy import WritingStrategy


class TestPlanValidator:
    def setup_method(self):
        self.validator = PlanValidator()
        self.strategy = WritingStrategy()

    def test_valid_plan(self):
        plan = """## Agent Contract
promises:
- 包含主角登场
- 设置冲突
constraints:
- 字数3000

## Chapter Goal
test

## Reader Promise
test

## Rhythm Plan
本章节奏类型：递进型
本章在卷中的节奏角色：铺垫
与前一章的节奏关系：延续加速
爽点投放时机：场景2
压力累积时机：场景1

## Subplot Allocation
test

## Conflict
test

## Scene List

### Scene 1
地点：都市
出场人物：主角
冲突：寻找
预期字数：1500

### Scene 2
地点：郊区
出场人物：反派
冲突：对抗
预期字数：1500

## Ending Hook
悬念
"""
        contract = AgentContract(promises=["包含主角登场", "设置冲突"], constraints=["字数3000"])
        result = self.validator.validate(plan, contract=contract, strategy=self.strategy)
        assert result.is_valid, f"Expected valid but got: {result.errors}"

    def test_missing_contract(self):
        plan = "## Chapter Goal\ntest\n## Rhythm Plan\n## Scene List\n### Scene 1\n地点：x\n人物：x\n冲突：x\n预期字数：100\n### Scene 2\n地点：x\n人物：x\n冲突：x\n预期字数：100\n## Ending Hook\nx"
        contract = AgentContract(promises=[], constraints=[])
        result = self.validator.validate(plan, contract=contract, strategy=self.strategy)
        assert not result.is_valid
        assert any("promises" in e for e in result.errors)

    def test_too_few_scenes(self):
        plan = "## Scene List\n### Scene 1\n地点：x\n人物：x\n冲突：x\n预期字数：100\n## Ending Hook\nx"
        contract = AgentContract(promises=["a", "b"], constraints=["c"])
        result = self.validator.validate(plan, contract=contract, strategy=self.strategy)
        assert not result.is_valid
        assert any("场景" in e for e in result.errors)

    def test_missing_ending_hook(self):
        plan = "## Scene List\n### Scene 1\n地点：x\n人物：x\n冲突：x\n预期字数：100\n### Scene 2\n地点：x\n人物：x\n冲突：x\n预期字数：100"
        contract = AgentContract(promises=["a", "b"], constraints=["c"])
        result = self.validator.validate(plan, contract=contract, strategy=self.strategy)
        assert not result.is_valid
        assert any("Ending Hook" in e for e in result.errors)

    def test_chapter_planner_process_output(self):
        from novel_runtime.agents.chapter_planner import ChapterPlannerAgent
        agent = ChapterPlannerAgent.__new__(ChapterPlannerAgent)
        sample = """## Agent Contract
- 承诺: 主角登场
- 约束: 字数3000以内

## Chapter Goal
test

## Reader Promise
test

## Rhythm Plan
本章节奏类型：递进型
本章在卷中的节奏角色：铺垫
与前一章的节奏关系：延续加速
爽点投放时机：场景2中期
压力累积时机：场景1全段

## Subplot Allocation
本章推进的子线：
- 主线: 推进

## Conflict
test

## Scene List

### Scene 1
地点：都市
出场人物：主角
场景功能：引入
冲突：寻找线索
转折：发现目标
输出结果：获得信息
预期字数：1500

## Ending Hook
悬念"""
        result = agent.process_output(sample, {})
        assert result.success
        plan = result.data
        assert plan.rhythm.rhythm_type == "递进型"
        assert len(plan.agent_contract.promises) >= 1
        assert len([line for line in sample.split("\n") if "### Scene" in line]) >= 1
