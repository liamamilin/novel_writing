from typing import Literal

from pydantic import BaseModel

HOOK_TYPES = Literal["mystery", "tension", "promise", "emotional", "power"]
HOOK_URGENCIES = Literal["stable", "rising", "critical"]


class Hook(BaseModel):
    hook_id: str
    content: str = ""
    source_chapter: str = ""
    status: str = "open"
    priority: str = "medium"

    type: str = "mystery"
    reader_patience: int = 8
    urgency: str = "stable"
    urgency_increase_rate: float = 0.5

    payoff_type: str = ""
    planned_payoff_range: str = ""
    actual_payoff_chapter: str = ""

    related_subplots: list[str] = []
    related_characters: list[str] = []
    foreshadow_density: str = "medium"

    notes: str = ""
