from __future__ import annotations

import re

from novel_runtime.agents.base import AgentResult, BaseAgent
from novel_runtime.llm.output_validator import MarkdownValidator
from novel_runtime.models.chapter import AgentContract, ChapterPlanRhythm, SubplotAllocation


class ChapterPlanResult:
    def __init__(self, plan_content: str, rhythm: ChapterPlanRhythm, subplot_allocation: SubplotAllocation, agent_contract: AgentContract):
        self.plan_content = plan_content
        self.rhythm = rhythm
        self.subplot_allocation = subplot_allocation
        self.agent_contract = agent_contract


class ChapterPlannerAgent(BaseAgent):
    def get_prompt_template(self) -> str:
        return "chapter_plan"

    def get_validator(self):
        return MarkdownValidator(
            required_sections=[
                "Agent Contract", "Chapter Goal", "Reader Promise",
                "Rhythm Plan", "Subplot Allocation", "Conflict",
                "Scene List", "Ending Hook",
            ],
        )

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        rhythm = self._extract_rhythm(raw_output)
        subplot_alloc = self._extract_subplot_allocation(raw_output)
        contract = self._extract_contract(raw_output)
        result = ChapterPlanResult(raw_output, rhythm, subplot_alloc, contract)
        return AgentResult(success=True, data=result, raw_output=raw_output)

    def plan(self, context_pack: str, strategy_summary: str) -> AgentResult:
        return self.execute(variables={
            "context_pack": context_pack,
            "strategy_summary": strategy_summary,
        })

    def _extract_rhythm(self, text: str) -> ChapterPlanRhythm:
        rhythm = ChapterPlanRhythm()
        patterns = {
            "rhythm_type": r"本章节奏类型[：:]\s*(.+)",
            "rhythm_role_in_volume": r"本章在卷中的节奏角色[：:]\s*(.+)",
            "relationship_with_previous": r"与前一章的节奏关系[：:]\s*(.+)",
            "satisfaction_point_timing": r"爽点投放时机[：:]\s*(.+)",
            "pressure_point_timing": r"压力累积时机[：:]\s*(.+)",
        }
        for field, pattern in patterns.items():
            m = re.search(pattern, text)
            if m:
                setattr(rhythm, field, m.group(1).strip())
        return rhythm

    def _extract_subplot_allocation(self, text: str) -> SubplotAllocation:
        sa = SubplotAllocation()
        current_section = None
        for line in text.split("\n"):
            stripped = line.strip()
            if "推进的子线" in stripped:
                current_section = "advance"
                continue
            elif "暂缓的子线" in stripped or "暂缓的" in stripped:
                current_section = "idle"
                continue
            elif stripped.startswith("## "):
                current_section = None
                continue
            if current_section == "advance" and stripped and not stripped.startswith("-"):
                continue
            if current_section == "advance" and stripped.startswith("-"):
                sa.advanced.append({"description": stripped.lstrip("- ")})
            elif current_section == "idle" and stripped.startswith("-"):
                sa.idle.append({"description": stripped.lstrip("- ")})
        return sa

    def _extract_contract(self, text: str) -> AgentContract:
        contract = AgentContract()
        in_contract = False
        for line in text.split("\n"):
            stripped = line.strip()
            if "Agent Contract" in stripped:
                in_contract = True
                continue
            if in_contract and stripped.startswith("## "):
                break
            if in_contract:
                if stripped.startswith("- ") or stripped.startswith("* "):
                    content = stripped.lstrip("- *").strip()
                    if "promise" in content.lower() or "承诺" in content:
                        contract.promises.append(content)
                    elif "constraint" in content.lower() or "约束" in content or "不得" in content:
                        contract.constraints.append(content)
        if not contract.promises:
            for line in text.split("\n"):
                stripped = line.strip()
                if "promises" in stripped.lower() or "承诺" in stripped:
                    m = re.search(r"[：:]\s*(.+)", stripped)
                    if m:
                        contract.promises = [p.strip() for p in m.group(1).split("、")]
        if not contract.constraints:
            for line in text.split("\n"):
                stripped = line.strip()
                if "constraints" in stripped.lower() or "约束" in stripped:
                    m = re.search(r"[：:]\s*(.+)", stripped)
                    if m:
                        contract.constraints = [c.strip() for c in m.group(1).split("、")]
        return contract
