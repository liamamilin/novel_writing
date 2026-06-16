from __future__ import annotations

from novel_runtime.agents.base import BaseAgent, AgentResult
from novel_runtime.llm.output_validator import MarkdownValidator


class CrossChapterReviewResult:
    def __init__(self, review_content: str):
        self.review_content = review_content


class CrossChapterAuditorAgent(BaseAgent):
    def get_prompt_template(self) -> str:
        return "cross_chapter_review"

    def get_validator(self):
        return MarkdownValidator(
            required_sections=[
                "Rhythm Analysis", "Subplot Status", "Hook Status",
                "Character Development", "Strategy Compliance",
            ],
        )

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        result = CrossChapterReviewResult(raw_output)
        return AgentResult(success=True, data=result, raw_output=raw_output)

    def review(
        self,
        styled_draft: str,
        recent_plans: str,
        recent_reviews: str,
        story_state: str,
        hooks: str,
        subplots: str,
        strategy_summary: str,
    ) -> AgentResult:
        return self.execute(variables={
            "styled_draft": styled_draft,
            "recent_plans": recent_plans,
            "recent_reviews": recent_reviews,
            "story_state": story_state,
            "hooks": hooks,
            "subplots": subplots,
            "strategy_summary": strategy_summary,
        })
