from __future__ import annotations

from novel_runtime.agents.base import BaseAgent, AgentResult
from novel_runtime.llm.output_validator import YAMLValidator


class StoryArchitectAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prompt_template = "bible_direction_variants"

    def get_prompt_template(self) -> str:
        return self._prompt_template

    def get_validator(self):
        if self._prompt_template == "bible_direction_variants":
            return YAMLValidator(
                required_fields=["variants"],
                field_types={"variants": list},
            )
        return None

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        return AgentResult(success=True, data=raw_output, raw_output=raw_output)

    def generate_direction_variants(self, idea: str, genre: str, target_reader: str, core_selling_point: str) -> AgentResult:
        self._prompt_template = "bible_direction_variants"
        return self.execute(variables={
            "idea": idea,
            "genre": genre,
            "target_reader": target_reader,
            "core_selling_point": core_selling_point,
        })

    def generate_character_concepts(self, direction: dict, idea: str) -> AgentResult:
        direction_summary = (
            f"方向名称: {direction.get('name', '')}\n"
            f"卖点: {direction.get('core_selling_point', '')}\n"
            f"节奏风格: {direction.get('pacing_style', '')}\n"
            f"主角类型: {direction.get('character_type', '')}\n"
            f"世界观: {direction.get('world_setting', '')}\n"
            f"摘要: {direction.get('summary', '')}"
        )
        self._prompt_template = "bible_character_concepts"
        return self.execute(variables={
            "direction_name": direction.get("name", ""),
            "direction_summary": direction_summary,
            "idea": idea,
        })

    def generate_full_bible(self, direction: dict, characters: list[dict], idea: str, genre: str) -> AgentResult:
        chars_text = "\n".join(
            f"- {c.get('name', '')} ({c.get('role', '')}): {c.get('personality', '')}"
            for c in characters
        )
        direction_summary = (
            f"方向名称: {direction.get('name', '')}\n"
            f"卖点: {direction.get('core_selling_point', '')}\n"
            f"摘要: {direction.get('summary', '')}"
        )
        self._prompt_template = "bible_full_generation"
        return self.execute(variables={
            "direction_summary": direction_summary,
            "direction_name": direction.get("name", ""),
            "characters": chars_text,
            "idea": idea,
            "genre": genre,
        })
