from __future__ import annotations

import re

from novel_runtime.agents.base import AgentResult, BaseAgent
from novel_runtime.llm.output_validator import MarkdownValidator


class QualityReviewResult:
    def __init__(self, review_content: str, scores: dict, problems: list[dict]):
        self.review_content = review_content
        self.scores = scores
        self.problems = problems


class QualityAuditorAgent(BaseAgent):
    def get_prompt_template(self) -> str:
        return "quality_review"

    def get_validator(self):
        return MarkdownValidator(
            required_sections=["Score", "Main Problems", "Rewrite Suggestions"],
        )

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        scores = {}
        problems = []

        for line in raw_output.split("\n"):
            stripped = line.strip()
            for dim in ["开头", "冲突", "节奏", "爽点", "文风", "结尾", "对白", "信息密度", "场景变化", "人物行为"]:
                pattern = rf"^{dim}[：:]\s*(\d+)"
                m = re.match(pattern, stripped)
                if m:
                    scores[dim] = int(m.group(1))

        if not scores:
            score_match = re.search(r"Score[：:]\s*({.*?})", raw_output, re.DOTALL)
            if score_match:
                for line in score_match.group(1).split("\n"):
                    stripped = line.strip()
                    if ":" in stripped and not stripped.startswith("#"):
                        parts = stripped.split(":", 1)
                        scores[parts[0].strip()] = parts[1].strip()

        problem_pattern = re.compile(r"(?:### )?问题\d*[：:]\s*(.+?)(?=###|$)", re.DOTALL)
        for match in problem_pattern.finditer(raw_output):
            text = match.group(1).strip()
            if text:
                problems.append({"description": text})

        result = QualityReviewResult(raw_output, scores, problems)
        return AgentResult(success=True, data=result, raw_output=raw_output)

    def review(self, styled_draft: str, chapter_plan: str, style_params: str) -> AgentResult:
        return self.execute(variables={
            "styled_draft": styled_draft,
            "chapter_plan": chapter_plan,
            "style_params": style_params,
        })
