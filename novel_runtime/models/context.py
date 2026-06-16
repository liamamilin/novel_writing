from pydantic import BaseModel


class RawContext(BaseModel):
    project_id: str = ""
    chapter_id: str = ""

    style_and_voices_content: str = ""
    story_context_content: str = ""
    recent_chapters_content: str = ""
    current_state_content: str = ""
    character_state_content: str = ""
    hooks_content: str = ""
    subplots_content: str = ""
    chapter_goal_content: str = ""
    writing_strategy_content: str = ""
    health_report_content: str = ""

    total_tokens: int = 0
    budget_used: dict[str, int] = {}


class ContextPack(BaseModel):
    project_id: str = ""
    chapter_id: str = ""
    content: str = ""
