from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class HealthIssue(BaseModel):
    type: str = ""
    severity: str = "warning"
    description: str = ""
    suggestion: str = ""
    character_id: str | None = None
    hook_id: str | None = None
    subplot_id: str | None = None


class StateHealthReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"shr_{uuid4().hex[:6]}")
    chapter_id: str = ""
    generated_at: datetime = Field(default_factory=datetime.now)
    issues: list[HealthIssue] = []
