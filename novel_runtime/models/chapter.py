from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Scene(BaseModel):
    scene_number: int
    location: str = ""
    characters: list[str] = []
    scene_function: str = ""
    conflict: str = ""
    turning_point: str = ""
    output: str = ""
    target_word_count: int = 0


class AgentContract(BaseModel):
    from_agent: str = ""
    to_agent: str = ""
    promises: list[str] = []
    constraints: list[str] = []


class ChapterPlanRhythm(BaseModel):
    rhythm_type: str = ""
    rhythm_role_in_volume: str = ""
    relationship_with_previous: str = ""
    satisfaction_point_timing: str = ""
    pressure_point_timing: str = ""


class SubplotAllocation(BaseModel):
    advanced: list[dict] = []
    idle: list[dict] = []


class ChapterPlanCreate(BaseModel):
    chapter_goal: str = ""
    style_id: str = ""


class Chapter(BaseModel):
    chapter_id: str
    chapter_number: int
    title: str = ""
    status: Literal["planned", "drafted", "reviewed", "approved", "locked"] = "planned"

    plan_path: str = ""
    draft_path: str = ""
    styled_draft_path: str = ""
    final_path: str = ""
    context_pack_path: str = ""
    state_annotations_path: str = ""
    fix_instructions_path: str = ""
    review_continuity_path: str = ""
    review_quality_path: str = ""
    review_cross_chapter_path: str = ""
    review_reader_sim_path: str = ""

    rhythm_type: str = ""
    tension_level: int = 0
    satisfaction_level: int = 0
    reader_hook_strength: int = 0

    subplots_advanced: list[dict] = []
    subplots_idle: list[dict] = []

    active_draft_id: int = 0
    draft_count: int = 0

    summary: str = ""

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
