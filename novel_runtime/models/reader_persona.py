from __future__ import annotations
from pydantic import BaseModel


class ReaderPersona(BaseModel):
    persona_id: str
    name: str
    age_group: str = ""
    preferences: list[str] = []
    tolerance_thresholds: dict[str, str] = {}
    review_prompt_template: str = ""
