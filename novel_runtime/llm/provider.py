from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterator

from novel_runtime.config import Settings
from novel_runtime.exceptions import LLMCallError


class LLMProvider(ABC):
    def __init__(self, default_temperature: float = 0.7, default_max_tokens: int = 4096):
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        ...

    @abstractmethod
    def generate_with_usage(
        self,
        prompt: str,
        system_prompt: str = "",
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> tuple[str, dict]:
        ...

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        raise NotImplementedError("Streaming not supported by this provider")

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        ...


def create_provider(config: Settings) -> LLMProvider:
    if config.llm_provider == "openai_compatible":
        from novel_runtime.llm.openai_provider import OpenAICompatibleProvider

        cache = None
        if config.llm_cache_enabled:
            from novel_runtime.llm.cache import LLMCache
            cache_path = config.llm_cache_path or str(Path(config.storage_base_path) / "llm_cache.db")
            cache = LLMCache(db_path=cache_path, ttl=config.llm_cache_ttl)

        return OpenAICompatibleProvider(
            base_url=config.llm_base_url,
            model=config.llm_model,
            api_key_env=config.llm_api_key_env,
            default_temperature=config.llm_temperature,
            default_max_tokens=config.llm_max_tokens,
            max_retries=config.llm_max_retries,
            cache=cache,
        )
    raise ValueError(f"Unknown LLM provider: {config.llm_provider}")
