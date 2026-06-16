from typing import Literal

from pydantic import BaseModel

ANNOTATION_TYPES = Literal[
    "character_state_change", "new_hook", "resolved_hook", "subplot_advance",
    "subplot_resolve", "character_development", "new_world_info",
    "relationship_change", "location_change", "ability_change",
]

SUMMARY_ANNOTATION_TYPES = Literal[
    "resolved_hook", "new_hook", "new_world_info", "relationship_change",
    "ability_change", "location_change",
]


class StateAnnotation(BaseModel):
    location: str = ""
    type: str = "character_state_change"
    character: str = ""
    change: str = ""
    trigger: str = ""
    narrative_impact: str = ""

    hook_id: str | None = None
    hook_type: str | None = None
    reader_patience: int | None = None
    subplot_id: str | None = None
    advancement: str | None = None
    next_stage: str | None = None
    arc_progression: str | None = None


class SummaryAnnotation(BaseModel):
    type: str = "new_world_info"
    hook_id: str | None = None
    info: str | None = None
    from_character: str | None = None
    to_character: str | None = None
    change: str | None = None


class StateAnnotationsFile(BaseModel):
    chapter_id: str = ""
    annotations: list[StateAnnotation] = []
    summary_annotations: list[SummaryAnnotation] = []
