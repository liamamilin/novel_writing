from typing import Literal, Optional

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

    hook_id: Optional[str] = None
    hook_type: Optional[str] = None
    reader_patience: Optional[int] = None
    subplot_id: Optional[str] = None
    advancement: Optional[str] = None
    next_stage: Optional[str] = None
    arc_progression: Optional[str] = None


class SummaryAnnotation(BaseModel):
    type: str = "new_world_info"
    hook_id: Optional[str] = None
    info: Optional[str] = None
    from_character: Optional[str] = None
    to_character: Optional[str] = None
    change: Optional[str] = None


class StateAnnotationsFile(BaseModel):
    chapter_id: str = ""
    annotations: list[StateAnnotation] = []
    summary_annotations: list[SummaryAnnotation] = []
