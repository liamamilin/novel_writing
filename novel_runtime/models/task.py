from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

TASK_TYPES = Literal[
    "style_analysis", "bible_generation", "bible_direction", "bible_character",
    "context_compile", "chapter_plan", "chapter_draft", "narrative_polish",
    "continuity_review", "quality_review", "cross_chapter_review", "reader_simulation",
    "fix_and_repolish", "state_update", "bible_update",
]

TASK_STATUSES = Literal["pending", "running", "success", "failed", "cancelled"]


class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid4().hex}")
    project_id: str
    task_type: str = ""
    status: str = "pending"
    input_data: dict = {}
    output_data: dict = {}
    error: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
