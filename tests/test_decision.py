import json

import httpx
import pytest

from bricksplain.decision import SUPPORT_MODEL, SUPPORT_URL, JevJudge
from bricksplain.llm import LLMError


def judge(handler, sleeps=None):
    return JevJudge(
        "k",
        "Does it hold? Claim: {claim}",
        transport=httpx.MockTransport(handler),
        sleep=(sleeps.append if sleeps is not None else lambda s: None),
    )


def ok(noul):
    return httpx.Response(
        200,
        json={
            "model": "typesafe/jev-1.13-20260917",
            "answers": {"support": {"type": "noul", "noul": noul}},
            "usage": {"input_tokens": 1, "output_tokens": 1, "cost": 0.00003},
        },
    )


def test_request_carries_quotes_as_state_and_claim_as_the_question():
    seen = []

    def handler(request):
        seen.append(request)
        return ok(0.98)

    assert judge(handler).score("It halts.", ["a", "b"]) == 0.98
    req = seen[0]
    assert str(req.url) == SUPPORT_URL
    assert req.headers["authorization"] == "Bearer k"
    body = json.loads(req.content)
    assert body["model"] == SUPPORT_MODEL
    assert body["state"] == "a\nb"
    q = body["questions"]["support"]
    assert q["type"] == "noul"
    assert q["instructions"] == "Does it hold? Claim: It halts."


def test_rate_limit_is_retried_then_succeeds():
    replies = iter([httpx.Response(429, headers={"retry-after": "2"}), ok(0.7)])
    sleeps = []
    assert judge(lambda r: next(replies), sleeps).score("c", ["q"]) == 0.7
    assert sleeps == [2.0]


@pytest.mark.parametrize(
    "reply",
    [
        httpx.Response(500),
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"answers": {}}),
        httpx.Response(200, json={"answers": {"support": {"noul": "high"}}}),
        httpx.Response(200, json={"answers": {"support": {"noul": 1.5}}}),
        httpx.Response(200, json={"answers": {"support": {"noul": True}}}),
    ],
)
def test_unusable_reply_raises_llm_error(reply):
    with pytest.raises(LLMError):
        judge(lambda r: reply).score("c", ["q"])


def test_exhausted_rate_limit_raises_llm_error():
    with pytest.raises(LLMError):
        judge(lambda r: httpx.Response(429)).score("c", ["q"])
