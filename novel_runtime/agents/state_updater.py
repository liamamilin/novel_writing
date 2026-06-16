from __future__ import annotations

import yaml

from novel_runtime.agents.base import AgentResult, BaseAgent


class StateUpdateResult:
    def __init__(self, data: dict):
        self.summary: str = data.get("summary", "")
        self.character_updates: list[dict] = data.get("character_updates", [])
        self.relationship_updates: list[dict] = data.get("relationship_updates", [])
        self.timeline_update: dict = data.get("timeline_update", {})
        self.new_hooks: list[dict] = data.get("new_hooks", [])
        self.triggered_hooks: list[str] = data.get("triggered_hooks", [])
        self.resolved_hooks: list[dict] = data.get("resolved_hooks", [])
        self.world_updates: list[str] = data.get("world_updates", [])
        self.subplot_advances: list[dict] = data.get("subplot_advances", [])
        self.ability_changes: list[dict] = data.get("ability_changes", [])
        self.next_chapter_suggestions: list[str] = data.get("next_chapter_suggestions", [])
        self.bible_update_needed: bool = data.get("bible_update_needed", False)
        self.bible_update_reasons: list[str] = data.get("bible_update_reasons", [])


class StateUpdaterAgent(BaseAgent):
    def get_prompt_template(self) -> str:
        return "state_update"

    def get_validator(self):
        return None

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        try:
            data = yaml.safe_load(raw_output)
        except Exception as e:
            return AgentResult(success=False, raw_output=raw_output, validation_errors=[str(e)])

        if not isinstance(data, dict):
            return AgentResult(success=False, raw_output=raw_output, validation_errors=["Output is not a dictionary"])

        result = StateUpdateResult(data)
        return AgentResult(success=True, data=result, raw_output=raw_output)

    def update(
        self,
        final_text: str,
        annotations_text: str,
        diff_summary: str,
        current_characters: str,
        current_story_state: str,
        current_hooks: str,
        current_subplots: str,
    ) -> AgentResult:
        return self.execute(variables={
            "final_text": final_text,
            "annotations": annotations_text,
            "diff_summary": diff_summary,
            "current_characters": current_characters,
            "current_story_state": current_story_state,
            "current_hooks": current_hooks,
            "current_subplots": current_subplots,
        })
