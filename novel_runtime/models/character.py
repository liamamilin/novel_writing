from pydantic import BaseModel


class NarrativeRole(BaseModel):
    current_function: str = ""
    functions: list[str] = []
    arc_stage: str = ""
    arc_stages_available: list[str] = []
    last_significant_moment: str = ""
    chapters_since_development: int = 0
    reader_attachment_level: str = ""
    next_use_suggestion: str = ""


class CharacterState(BaseModel):
    character_id: str
    name: str = ""
    role: str = "supporting"

    current_location: str = ""
    current_goal: str = ""
    current_emotion: str = ""
    known_information: list[str] = []
    unknown_information: list[str] = []
    abilities: list[str] = []
    secrets: list[str] = []
    relationships: list = []
    last_seen_chapter: str = ""

    narrative_role: NarrativeRole = NarrativeRole()

    voice_id: str = ""
