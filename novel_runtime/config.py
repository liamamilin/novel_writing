from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    llm_provider: str = "openai_compatible"
    llm_base_url: str = ""
    llm_model: str = ""
    llm_api_key_env: str = "LLM_API_KEY"
    llm_max_retries: int = 1
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    context_token_budget: int = 8000
    context_budget_allocation: dict = {
        "style_and_voices": 800,
        "story_context": 600,
        "recent_chapters": 1500,
        "current_state": 600,
        "character_state": 1200,
        "hooks": 400,
        "subplots": 400,
        "chapter_goal": 300,
        "narrative_diagnosis": 500,
        "generation_constraints": 400,
        "writing_strategy": 300,
        "health_report": 400,
    }
    context_priority_order: list[str] = [
        "style_and_voices",
        "chapter_goal",
        "current_state",
        "character_state",
        "recent_chapters",
        "hooks",
        "subplots",
        "story_context",
        "narrative_diagnosis",
        "writing_strategy",
        "health_report",
        "generation_constraints",
    ]

    storage_base_path: str = "./novel_projects"
    db_path: str = ""

    log_level: str = "INFO"
    log_format: str = "text"
    log_file: str = ""

    max_fix_iterations: int = 1

    llm_cache_enabled: bool = False
    llm_cache_ttl: int = 86400
    llm_cache_path: str = ""

    auth_token: str = ""

    chapter_status_flow: dict = {
        "planned": "drafted",
        "drafted": "reviewed",
        "reviewed": "approved",
        "approved": "locked",
    }

    model_config = SettingsConfigDict(env_prefix="NWR_")
