"""LLM client: one OpenAI-compatible chat call, with request metadata logged."""

import logging
import time
from typing import Protocol

import httpx

from .config import Config

log = logging.getLogger("bricksplain")

# provider -> chat completions URL, and whether JSON mode is supported.
PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "json_mode": True,
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "json_mode": True,
    },
}


class LLMError(Exception):
    """The LLM call failed. Never contains the API key."""


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class OpenAICompatClient:
    def __init__(
        self,
        config: Config,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 120.0,
    ):
        self._config = config
        self._http = httpx.Client(transport=transport, timeout=timeout)

    def complete(self, system: str, user: str) -> str:
        cfg = self._config
        provider = PROVIDERS[cfg.provider]
        body: dict = {
            "model": cfg.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if provider["json_mode"]:
            body["response_format"] = {"type": "json_object"}
        started = time.monotonic()
        status: int | str = "error"
        usage: dict = {}
        try:
            resp = self._http.post(
                provider["url"],
                json=body,
                headers={"Authorization": f"Bearer {cfg.api_key}"},
            )
            status = resp.status_code
            if status != 200:
                raise LLMError(f"The LLM provider returned HTTP {status}.")
            data = resp.json()
            usage = data.get("usage") or {}
            return data["choices"][0]["message"]["content"] or ""
        except httpx.HTTPError as e:
            raise LLMError(f"The LLM request failed: {type(e).__name__}.") from e
        except (KeyError, IndexError, ValueError, TypeError) as e:
            raise LLMError("The LLM response had an unexpected shape.") from e
        finally:
            log.info(
                "llm request provider=%s model=%s status=%s latency=%.2fs "
                "prompt_tokens=%s completion_tokens=%s",
                cfg.provider,
                cfg.model,
                status,
                time.monotonic() - started,
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
            )
