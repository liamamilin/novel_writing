from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=100)
    genre: str = Field(..., min_length=1)
    idea: str = ""
    target_reader: str = ""
    core_selling_point: str = ""
    target_style: str = ""


class ProjectUpdate(BaseModel):
    project_name: str | None = None
    genre: str | None = None
    idea: str | None = None
    target_reader: str | None = None
    core_selling_point: str | None = None
    target_style: str | None = None
    status: Literal["draft", "active", "paused", "archived"] | None = None
    default_style_id: str | None = None
    current_volume_id: str | None = None
    current_chapter_id: str | None = None
    bible_version: int | None = None
    writing_strategy_id: str | None = None


class Project(BaseModel):
    project_id: str = Field(
        default_factory=lambda: f"novel_{datetime.now().strftime('%Y%m%d')}_{uuid4().hex[:5]}"
    )
    project_name: str
    genre: str
    idea: str = ""
    target_reader: str = ""
    core_selling_point: str = ""
    target_style: str = ""
    status: Literal["draft", "active", "paused", "archived"] = "draft"
    default_style_id: str = ""
    current_volume_id: str = "volume_001"
    current_chapter_id: str = "chapter_001"
    bible_version: int = 0
    writing_strategy_id: str = "strategy_default"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
