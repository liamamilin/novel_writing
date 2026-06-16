from __future__ import annotations

import re

from novel_runtime.agents.base import AgentResult, BaseAgent
from novel_runtime.llm.output_validator import MarkdownValidator


class ContinuityReviewResult:
    def __init__(self, review_content: str, issues: list[dict]):
        self.review_content = review_content
        self.issues = issues


class ContinuityAuditorAgent(BaseAgent):
    def get_prompt_template(self) -> str:
        return "continuity_review"

    def get_validator(self):
        return MarkdownValidator(required_sections=["Summary", "Issues"])

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        issues = []
        issue_pattern = re.compile(
            r"(?:### )?Issue \d+\s*\n.*?(?=### Issue \d+|## |$)",
            re.DOTALL,
        )
        for match in issue_pattern.finditer(raw_output):
            block = match.group(0)
            issue = {
                "type": self._extract_field(block, "问题类型|type"),
                "location": self._extract_field(block, "问题位置|location"),
                "problem": self._extract_field(block, "问题说明|problem"),
                "severity": self._extract_field(block, "严重程度|severity"),
                "suggested_fix": self._extract_field(block, "修改动作|suggested_fix"),
            }
            if any(issue.values()):
                issues.append(issue)

        result = ContinuityReviewResult(raw_output, issues)
        return AgentResult(success=True, data=result, raw_output=raw_output)

    def review(self, styled_draft: str, context_pack: str, character_state: str,
               timeline: str, hooks: str, world_setting: str) -> AgentResult:
        return self.execute(variables={
            "styled_draft": styled_draft,
            "context_pack": context_pack,
            "character_state": character_state,
            "timeline": timeline,
            "hooks": hooks,
            "world_setting": world_setting,
        })

    def _extract_field(self, text: str, field_pattern: str) -> str:
        for line in text.split("\n"):
            stripped = line.strip()
            if re.search(field_pattern, stripped, re.IGNORECASE):
                parts = re.split(r"[：:]\s*", stripped, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return ""
