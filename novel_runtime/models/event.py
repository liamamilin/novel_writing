from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel, Field


class ProjectEvent(BaseModel):
    event_id: str
    project_id: str
    action: str
    actor: str = "system"
    details: dict = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
