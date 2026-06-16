from typing import Literal

from pydantic import BaseModel

FIX_ACTIONS = Literal["replace", "insert", "delete", "rewrite"]
FIX_SEVERITIES = Literal["critical", "moderate", "low"]


class FixInstruction(BaseModel):
    fix_id: str = ""
    type: str = ""
    severity: str = "moderate"
    location: str = ""
    problem: str = ""
    action: str = "replace"
    original_text: str = ""
    suggested_fix: str = ""
    constraint: str = ""


class FixInstructionsFile(BaseModel):
    fix_instructions: list[FixInstruction] = []
