from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from novel_runtime.llm.output_validator import (
    BaseValidator,
    validate_with_retry,
)
from novel_runtime.llm.prompt_loader import PromptLoader
from novel_runtime.llm.provider import LLMProvider


@dataclass
class AgentResult:
    success: bool
    data: Any = None
    raw_output: str = ""
    validation_errors: list[str] = field(default_factory=list)
    retries_used: int = 0
    tokens_used: dict = field(default_factory=dict)


class BaseAgent:
    def __init__(
        self,
        provider: LLMProvider,
        prompt_loader: PromptLoader,
        validator: BaseValidator | None = None,
        max_retries: int = 1,
    ):
        self.provider = provider
        self.prompt_loader = prompt_loader
        self.validator = validator
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"novel_runtime.agents.{self.__class__.__name__}")

    def get_prompt_template(self) -> str:
        raise NotImplementedError

    def get_validator(self) -> BaseValidator | None:
        return self.validator

    def process_output(self, raw_output: str, context: dict) -> AgentResult:
        raise NotImplementedError

    def execute(
        self,
        variables: dict,
        context: dict | None = None,
    ) -> AgentResult:
        try:
            prompt = self.prompt_loader.load(self.get_prompt_template(), variables)
        except FileNotFoundError as e:
            self.logger.error("prompt_template_not_found", extra={"template": self.get_prompt_template(), "error": str(e)})
            return AgentResult(success=False, raw_output="", validation_errors=[str(e)])

        total_prompt_tokens = 0
        total_completion_tokens = 0

        try:
            text, usage = self.provider.generate_with_usage(
                prompt, context=context,
            )
            total_prompt_tokens += usage.get("prompt_tokens", 0)
            total_completion_tokens += usage.get("completion_tokens", 0)
        except Exception as e:
            self.logger.error("llm_call_failed", extra={"error": str(e)})
            return AgentResult(
                success=False,
                raw_output="",
                validation_errors=[f"LLM call failed: {e}"],
                tokens_used={"prompt": total_prompt_tokens, "completion": total_completion_tokens},
            )

        validator = self.get_validator()
        retries_used = 0

        if validator is not None:
            result = validate_with_retry(
                validator=validator,
                llm_output=text,
                max_retries=self.max_retries,
                provider=self.provider,
                original_prompt=prompt,
            )
            retries_used = 1 if not validator.validate(text).is_valid else 0
            if not result.is_valid:
                self.logger.warning("validation_failed", extra={
                    "errors": result.errors,
                    "retries_used": retries_used,
                })
                return AgentResult(
                    success=False,
                    raw_output=text,
                    validation_errors=result.errors,
                    retries_used=retries_used,
                    tokens_used={
                        "prompt": total_prompt_tokens,
                        "completion": total_completion_tokens,
                    },
                )

        processed = self.process_output(text, context or {})
        processed.retries_used = retries_used
        processed.tokens_used = {
            "prompt": total_prompt_tokens,
            "completion": total_completion_tokens,
        }
        self.logger.info("agent_executed", extra={
            "template": self.get_prompt_template(),
            "success": processed.success,
            "retries": retries_used,
        })
        return processed
