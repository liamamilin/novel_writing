from pydantic import BaseModel


class ChapterLengthConfig(BaseModel):
    target: int = 3000
    min: int = 2500
    max: int = 3500


class PacingStrategyConfig(BaseModel):
    type: str = "variable_rhythm"
    tension_curve: str = "sawtooth"
    cooldown_after_climax: int = 1


class SubplotPolicyConfig(BaseModel):
    max_simultaneous: int = 3
    min_advance_frequency: int = 4
    max_gap_between_advances: int = 6
    convergence_strategy: str = "planned"


class HookPolicyConfig(BaseModel):
    max_open_hooks: int = 8
    min_resolution_rate: float = 0.3
    urgency_escalation: bool = True


class CharacterPolicyConfig(BaseModel):
    max_scenes_without_protagonist: int = 1
    character_development_frequency: int = 3
    new_character_introduction_rate: int = 5


class WritingStrategy(BaseModel):
    strategy_id: str = "strategy_default"
    name: str = ""
    description: str = ""
    chapter_length: ChapterLengthConfig = ChapterLengthConfig()
    pacing_strategy: PacingStrategyConfig = PacingStrategyConfig()
    subplot_policy: SubplotPolicyConfig = SubplotPolicyConfig()
    hook_policy: HookPolicyConfig = HookPolicyConfig()
    character_policy: CharacterPolicyConfig = CharacterPolicyConfig()
