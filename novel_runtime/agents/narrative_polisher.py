from __future__ import annotations

from novel_runtime.agents.base import AgentResult, BaseAgent
from novel_runtime.llm.output_validator import MarkdownValidator


class NarrativePolisherAgent(BaseAgent):
    def get_prompt_template(self) -> str:
        return "narrative_polish"

    def get_validator(self):
        return MarkdownValidator()

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        return AgentResult(success=True, data=raw_output, raw_output=raw_output)

    def polish(
        self,
        draft: str,
        style_params: str,
        rhythm_type: str,
        voice_params: str,
        annotations_summary: str,
    ) -> AgentResult:
        return self.execute(variables={
            "draft": draft,
            "style_params": style_params,
            "rhythm_type": rhythm_type,
            "voice_params": voice_params,
            "annotations_summary": annotations_summary,
        })
