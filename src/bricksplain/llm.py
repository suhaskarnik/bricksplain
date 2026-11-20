"""LLM client: one OpenAI-compatible chat call, with request metadata logged."""

import logging
import time
from collections.abc import Callable
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
        "reasoning": True,
    },
    "google": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "json_mode": True,
    },
}


MAX_RATE_LIMIT_RETRIES = 3
MAX_RETRY_WAIT = 60.0
DEFAULT_RETRY_WAIT = 5.0


def _retry_wait(resp: httpx.Response) -> float:
    """Seconds to wait before retrying a 429, honouring Retry-After."""
    try:
        wait = float(resp.headers.get("retry-after", ""))
    except ValueError:
        wait = DEFAULT_RETRY_WAIT
    return min(max(wait, 0.0), MAX_RETRY_WAIT)


class LLMError(Exception):
    """The LLM call failed. Never contains the API key."""


def post_with_retry(
    http: httpx.Client,
    url: str,
    body: dict,
    api_key: str,
    sleep: Callable[[float], None],
    label: str,
) -> httpx.Response:
    """POST, waiting and retrying on 429 up to MAX_RATE_LIMIT_RETRIES times.

    Returns the first non-429 response; raises LLMError once retries run out."""
    retries = 0
    while True:
        log.info(f"making call to {label}, URL: {url}")
        resp = http.post(url, json=body, headers={"Authorization": f"Bearer {api_key}"})
        log.info("received response from %s", label)
        if resp.status_code != 429:
            return resp
        if retries >= MAX_RATE_LIMIT_RETRIES:
            log.error("llm rate limited; giving up after %d retries", retries)
            raise LLMError(
                "The LLM provider is rate limiting requests; try again shortly."
            )
        wait = _retry_wait(resp)
        retries += 1
        log.warning(
            "llm rate limited (429); retry %d/%d in %.1fs",
            retries,
            MAX_RATE_LIMIT_RETRIES,
            wait,
        )
        sleep(wait)


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class OpenAICompatClient:
    def __init__(
        self,
        config: Config,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 120.0,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._config = config
        self._sleep = sleep
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
        if provider.get("reasoning") and cfg.reasoning_effort:
            body["reasoning"] = {"effort": cfg.reasoning_effort}
        started = time.monotonic()
        status: int | str = "error"
        usage: dict = {}
        try:
            resp = post_with_retry(
                self._http,
                provider["url"],
                body,
                cfg.api_key,
                self._sleep,
                label=cfg.provider,
            )
            status = resp.status_code
            if status != 200:
                log.error("llm request failed: HTTP %s", status)
                raise LLMError(f"The LLM provider returned HTTP {status}.")
            data = resp.json()
            usage = data.get("usage") or {}
            return data["choices"][0]["message"]["content"] or ""
        except httpx.HTTPError as e:
            log.error("llm request failed: %s", type(e).__name__)
            raise LLMError(f"The LLM request failed: {type(e).__name__}.") from e
        except (KeyError, IndexError, ValueError, TypeError) as e:
            log.error("llm response had an unexpected shape")
            raise LLMError("The LLM response had an unexpected shape.") from e
        finally:
            log.info(
                "llm request provider=%s model=%s status=%s latency=%.2fs "
                "prompt_tokens=%s completion_tokens=%s reasoning_tokens=%s",
                cfg.provider,
                cfg.model,
                status,
                time.monotonic() - started,
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
                (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
            )
