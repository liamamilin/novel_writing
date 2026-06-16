from __future__ import annotations

import logging
import os
import time
from collections.abc import Iterator

import httpx

from novel_runtime.exceptions import LLMCallError
from novel_runtime.llm.provider import LLMProvider
from novel_runtime.metrics import llm_calls_total, llm_latency_seconds, llm_tokens_total

logger = logging.getLogger("novel_runtime.llm.openai_provider")


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key_env: str = "LLM_API_KEY",
        default_temperature: float = 0.7,
        default_max_tokens: int = 4096,
        max_retries: int = 1,
        cache=None,
    ):
        super().__init__(default_temperature, default_max_tokens)
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = os.environ.get(api_key_env, "")
        self.max_retries = max_retries
        self.cache = cache

    def _build_messages(self, prompt: str, system_prompt: str, context: dict | None) -> list[dict]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
            messages.append({"role": "system", "content": f"Additional context:\n{context_str}"})
        messages.append({"role": "user", "content": prompt})
        return messages

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        result, _ = self.generate_with_usage(prompt, system_prompt, context, temperature, max_tokens)
        return result

    def generate_with_usage(
        self,
        prompt: str,
        system_prompt: str = "",
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> tuple[str, dict]:
        if self.cache:
            key = self.cache.make_key(prompt, system_prompt, context, temperature, self.model)
            cached_text = self.cache.get(key)
            if cached_text is not None:
                logger.info("llm_cache_hit", extra={"model": self.model})
                return cached_text, {"cached": True, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        if not self.api_key:
            raise LLMCallError("API key not set. Set the environment variable specified in llm_api_key_env.")

        messages = self._build_messages(prompt, system_prompt, context)
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.default_temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.default_max_tokens,
        }

        last_error = None
        start = time.monotonic()
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=httpx.Timeout(10.0, read=120.0)) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                    )
                    if response.status_code == 401:
                        raise LLMCallError("Authentication failed (401). Check API key.")
                    if response.status_code == 429:
                        raise LLMCallError("Rate limited (429). Retrying...")
                    if response.status_code >= 500:
                        raise LLMCallError(f"Server error ({response.status_code}). Retrying...")
                    response.raise_for_status()
                    data = response.json()
                    text = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    usage_dict = {
                        "prompt_tokens": usage.get("prompt_tokens", -1),
                        "completion_tokens": usage.get("completion_tokens", -1),
                        "total_tokens": usage.get("total_tokens", -1),
                    }
                    latency = (time.monotonic() - start) * 1000
                    if self.cache:
                        self.cache.set(key, text, self.model)
                    llm_calls_total.labels(agent="openai", status="success").inc()
                    llm_tokens_total.labels(agent="openai", type="prompt").inc(usage_dict["prompt_tokens"])
                    llm_tokens_total.labels(agent="openai", type="completion").inc(usage_dict["completion_tokens"])
                    llm_latency_seconds.labels(agent="openai").observe(latency / 1000.0)
                    logger.info("llm_call_success", extra={
                        "model": self.model,
                        "attempt": attempt + 1,
                        "prompt_tokens": usage_dict["prompt_tokens"],
                        "completion_tokens": usage_dict["completion_tokens"],
                        "total_tokens": usage_dict["total_tokens"],
                        "latency_ms": f"{latency:.1f}",
                    })
                    return text, usage_dict
            except httpx.TimeoutException as e:
                last_error = LLMCallError(f"Request timeout: {e}")
                logger.warning("llm_retry", extra={"attempt": attempt + 1, "error": str(e)})
            except httpx.HTTPStatusError as e:
                last_error = LLMCallError(f"HTTP error {e.response.status_code}: {e}")
                logger.warning("llm_retry", extra={"attempt": attempt + 1, "status": e.response.status_code})
            except LLMCallError as e:
                last_error = e
                logger.warning("llm_retry", extra={"attempt": attempt + 1, "error": str(e)})
            except Exception as e:
                last_error = LLMCallError(f"Unexpected error: {e}")
                logger.error("llm_unexpected_error", extra={"error": str(e)})

            if attempt < self.max_retries:
                time.sleep(2 ** attempt)

        latency = (time.monotonic() - start) * 1000
        llm_calls_total.labels(agent="openai", status="error").inc()
        logger.error("llm_call_failed", extra={
            "model": self.model,
            "latency_ms": f"{latency:.1f}",
            "error": str(last_error),
        })
        raise last_error

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        context: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        if not self.api_key:
            raise LLMCallError("API key not set.")

        messages = self._build_messages(prompt, system_prompt, context)
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.default_temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.default_max_tokens,
            "stream": True,
        }

        with httpx.Client(timeout=httpx.Timeout(10.0, read=300.0)) as client:
            with client.stream("POST", f"{self.base_url}/chat/completions",
                               json=payload,
                               headers={"Authorization": f"Bearer {self.api_key}"}) as response:
                if response.status_code != 200:
                    raise LLMCallError(f"Stream error: HTTP {response.status_code}")
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        import json
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    def count_tokens(self, text: str) -> int:
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except ImportError:
            return len(text) // 4
