from __future__ import annotations

from novel_runtime.agents.base import BaseAgent, AgentResult
from novel_runtime.llm.output_validator import MarkdownValidator


class ContextCompilerAgent(BaseAgent):
    def get_prompt_template(self) -> str:
        return "context_compile"

    def get_validator(self):
        return MarkdownValidator(
            required_sections=[
                "Project Info", "Style Asset", "Character Voices",
                "Global Story Context", "Narrative Diagnosis",
                "Subplot Status", "Recent Chapters", "Current State",
                "Character State", "Hooks", "Chapter Goal",
                "Generation Constraints", "Writing Strategy",
            ],
        )

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        return AgentResult(success=True, data=raw_output, raw_output=raw_output)

    def compile(self, raw_context: str, health_report: str) -> AgentResult:
        return self.execute(variables={
            "raw_context": raw_context,
            "health_report": health_report,
        })
