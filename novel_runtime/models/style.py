from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ConditionalRule(BaseModel):
    condition: Literal["fight_scene", "emotional_scene", "dialogue_scene", "exposition_scene", "climax_scene"]
    adjustments: dict[str, str] = {}


class StyleAssetCreate(BaseModel):
    style_name: str
    sample_ids: list[str] = []


class StyleAsset(BaseModel):
    style_id: str = ""
    style_name: str = ""
    source_text_ids: list[str] = []

    narration: str = ""
    sentence_rhythm: str = ""
    dialogue_style: str = ""
    description_density: str = ""

    emotion_curve: str = ""
    conflict_pattern: str = ""

    chapter_opening: str = ""
    chapter_ending: str = ""

    scene_density: str = ""

    avoid: list[str] = []

    conditional_rules: list[ConditionalRule] = []

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CharacterVoice(BaseModel):
    voice_id: str = ""
    character_id: str = ""
    character_name: str = ""

    speech_patterns: dict = {}
    internal_monologue: dict = {}
    quirks: list[dict] = []
