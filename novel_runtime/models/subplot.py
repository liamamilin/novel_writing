from pydantic import BaseModel


class ConvergencePoint(BaseModel):
    with_subplot: str = ""
    planned_chapter_range: str = ""
    convergence_type: str = "causal"


class Subplot(BaseModel):
    subplot_id: str
    name: str = ""
    type: str = "main_plot"
    status: str = "setup"

    arc: dict = {}
    involved_characters: list[str] = []
    related_hooks: list[str] = []
    last_advanced: str = ""
    chapters_since_advance: int = 0

    interleave_plan: dict = {}
    convergence_points: list[ConvergencePoint] = []
