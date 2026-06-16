from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class BibleUpdateItem(BaseModel):
    file: Literal["novel_bible.md", "world_setting.md", "character_profiles.md", "volume_plan.md", "chapter_plan.md"] = "novel_bible.md"
    section: str = ""
    change: str = ""
    reason: str = ""


class BibleUpdateProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: f"bup_{uuid4().hex[:6]}")
    project_id: str = ""
    trigger_chapter: str = ""
    items: list[BibleUpdateItem] = []
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)


class BibleChangelogEntry(BaseModel):
    version: int = 0
    chapter: str = ""
    changes: list[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)


class BibleChangelog(BaseModel):
    entries: list[BibleChangelogEntry] = []
