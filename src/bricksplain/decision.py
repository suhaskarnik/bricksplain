"""Support Check client: a decision model (Jev, on OpenRouter) that scores how
strongly a quoted text establishes a Claim.

It is separate from the model that writes the docs, and OpenRouter-only."""

import logging
import time
from collections.abc import Callable
from typing import Protocol

import httpx

from .llm import LLMError, post_with_retry

log = logging.getLogger("bricksplain")

SUPPORT_URL = "https://openrouter.ai/api/v1/systemone"
# The alias is the pinned input (and part of the cache key); the dated model it
# resolved to comes back in the response and is logged on every request.
SUPPORT_MODEL = "jev-1.13"
# A Claim is supported when its noul score reaches this. Tune against the Eval Cases.
SUPPORT_THRESHOLD = 0.5
QUESTION_ID = "support"


class SupportJudge(Protocol):
    def score(self, claim: str, evidence: list[str]) -> float:
        """Probability in [0, 1] that the evidence texts, together, establish the claim."""
        ...


class JevJudge:
    def __init__(
        self,
        api_key: str,
        question: str,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 60.0,
        sleep: Callable[[float], None] = time.sleep,
    ):
        """`question` is the instruction template; `{claim}` is replaced by the Claim."""
        self._key = api_key
        self._question = question
        self._sleep = sleep
        self._http = httpx.Client(transport=transport, timeout=timeout)

    def score(self, claim: str, evidence: list[str]) -> float:
        body = {
            "model": SUPPORT_MODEL,
            "state": "\n".join(evidence),
            "questions": {
                QUESTION_ID: {
                    "type": "noul",
                    "instructions": self._question.replace("{claim}", claim),
                }
            },
        }
        started = time.monotonic()
        status: int | str = "error"
        data: dict = {}
        try:
            resp = post_with_retry(
                self._http, SUPPORT_URL, body, self._key, self._sleep, "support check"
            )
            status = resp.status_code
            if status != 200:
                log.error("support check request failed: HTTP %s", status)
                raise LLMError(f"The support check returned HTTP {status}.")
            data = resp.json()
            value = data["answers"][QUESTION_ID]["noul"]
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise TypeError("noul is not a number")
            if not 0 <= value <= 1:
                raise ValueError("noul out of range")
            return float(value)
        except httpx.HTTPError as e:
            log.error("support check request failed: %s", type(e).__name__)
            raise LLMError(f"The support check failed: {type(e).__name__}.") from e
        except (KeyError, ValueError, TypeError, AttributeError) as e:
            log.error("support check response had an unexpected shape")
            raise LLMError("The support check response had an unexpected shape.") from e
        finally:
            usage = data.get("usage") if isinstance(data, dict) else None
            usage = usage if isinstance(usage, dict) else {}
            log.info(
                "support check request model=%s resolved_model=%s status=%s "
                "latency=%.2fs input_tokens=%s output_tokens=%s cost=%s",
                SUPPORT_MODEL,
                data.get("model") if isinstance(data, dict) else None,
                status,
                time.monotonic() - started,
                usage.get("input_tokens"),
                usage.get("output_tokens"),
                usage.get("cost"),
            )
