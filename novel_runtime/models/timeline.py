
from pydantic import BaseModel


class StoryTime(BaseModel):
    start: str = ""
    end: str = ""
    duration: str = ""


class TimelineEvent(BaseModel):
    event_id: str
    chapter_id: str = ""
    story_time: StoryTime = StoryTime()
    reading_duration: str = ""
    pacing_ratio: str = ""
    location: str = ""
    characters: list[str] = []
    event_summary: str = ""
    state_change: str = ""
