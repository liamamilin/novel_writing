from __future__ import annotations

from novel_runtime.agents.base import BaseAgent, AgentResult
from novel_runtime.llm.output_validator import MarkdownValidator


class ReaderSimResult:
    def __init__(self, review_content: str):
        self.review_content = review_content


class ReaderSimulatorAgent(BaseAgent):
    def get_prompt_template(self) -> str:
        return "reader_simulation"

    def get_validator(self):
        return None

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        result = ReaderSimResult(raw_output)
        return AgentResult(success=True, data=result, raw_output=raw_output)

    def simulate(
        self,
        styled_draft: str,
        style_params: str,
        recent_summary: str,
        target_reader: str,
        strategy_summary: str,
    ) -> AgentResult:
        return self.execute(variables={
            "styled_draft": styled_draft,
            "style_params": style_params,
            "recent_summary": recent_summary,
            "target_reader": target_reader,
            "strategy_summary": strategy_summary,
        })
