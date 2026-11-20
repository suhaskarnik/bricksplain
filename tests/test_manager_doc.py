import json
import logging
import re
from urllib.parse import unquote

import pytest
from fastapi.testclient import TestClient
from support import generate as _generate
from support import llm_for

from bricksplain.app import create_app
from bricksplain.config import Config

# small.py: Cell 2 is lines 7-10 ("x = 1" on line 8, "y = 2" on line 9).


class FakeLLM:
    def __init__(self, output):
        self.output = output if isinstance(output, str) else json.dumps(output)
        self.calls = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.output


def fact(text="Sets x.", cell=2, start=8, end=8, quote="x = 1"):
    return {
        "type": "fact",
        "text": text,
        "citations": [{"cell": cell, "start": start, "end": end, "quote": quote}],
    }


def doc(**sections):
    base = {k: [] for k in ("summary", "how_it_works", "outcomes", "potential_issues")}
    base.update(sections)
    return base


def make_client(fixtures, llm):
    routed = llm_for("manager", llm)
    app = create_app(
        Config("groq", "m", "test-key"),
        default_path=str(fixtures / "small.py"),
        llm_client=routed,
        support_judge=routed,
    )
    return TestClient(app)


def generate(client, fixtures):
    return _generate(client, str(fixtures / "small.py"))


def test_valid_doc_has_fixed_skeleton_and_verified_citation_links(fixtures):
    llm = FakeLLM(
        doc(
            summary=[fact("Sets x to one.")],
            potential_issues=[
                {
                    "type": "concern",
                    "severity": "high",
                    "text": "Hidden dependency.",
                    "citations": [
                        {
                            "cell": 4,
                            "start": 18,
                            "end": 18,
                            "quote": "%run ../shared/helper",
                        }
                    ],
                }
            ],
        )
    )
    r = generate(make_client(fixtures, llm), fixtures)
    assert r.status_code == 200
    for heading in (
        "Summary",
        "How it works in business terms",
        "Outcomes and impact",
        "Potential issues",
    ):
        assert heading in r.text
    assert "Sets x to one." in r.text
    href = re.search(r'href="(/source\?[^"]*)"', r.text).group(1)
    href = unquote(href.replace("&amp;", "&"))
    assert "cell=2" in href and "start=8" in href and "end=8" in href
    assert "high" in r.text
    assert "dropped" not in r.text.lower()


def test_citation_link_opens_source_viewer_with_highlight(fixtures):
    client = make_client(fixtures, FakeLLM(doc(summary=[fact()])))
    r = generate(client, fixtures)
    href = re.search(r'href="(/source\?[^"]*)"', r.text).group(1).replace("&amp;", "&")
    viewer = client.get(href)
    assert re.findall(r'class="hl"[^>]*data-line="(\d+)"', viewer.text) == ["8"]


@pytest.mark.parametrize(
    "bad",
    [
        fact(cell=99),
        fact(start=1, end=3),
        fact(quote="z = 3"),
    ],
    ids=["bad-cell", "out-of-range", "quote-mismatch"],
)
def test_failing_claim_is_dropped_and_count_shown_and_logged(fixtures, bad, caplog):
    bad = {**bad, "text": "BAD CLAIM"}
    llm = FakeLLM(doc(summary=[fact("Good claim."), bad]))
    with caplog.at_level(logging.INFO, logger="bricksplain"):
        r = generate(make_client(fixtures, llm), fixtures)
    assert "Good claim." in r.text
    assert "BAD CLAIM" not in r.text
    assert "1 claim dropped" in r.text
    assert any("dropped" in m and "1" in m for m in caplog.messages)


def test_quote_match_is_whitespace_normalised(fixtures):
    llm = FakeLLM(doc(summary=[fact("Spaced.", quote="x   =\t1")]))
    r = generate(make_client(fixtures, llm), fixtures)
    assert "Spaced." in r.text


def test_context_has_no_citation_and_is_marked(fixtures):
    llm = FakeLLM(doc(summary=[{"type": "context", "text": "Generic framing."}]))
    r = generate(make_client(fixtures, llm), fixtures)
    assert "Generic framing." in r.text
    assert "Not from the Notebook" in r.text
    assert "start=" not in r.text  # no Citation link (uncited-Cell links have none)


def test_fact_without_citation_is_dropped(fixtures):
    llm = FakeLLM(doc(summary=[{"type": "fact", "text": "Uncited.", "citations": []}]))
    r = generate(make_client(fixtures, llm), fixtures)
    assert "Uncited." not in r.text
    assert "1 claim dropped" in r.text


def test_prose_is_rendered_escaped_from_structure(fixtures):
    llm = FakeLLM(doc(summary=[fact("<script>alert(1)</script>")]))
    r = generate(make_client(fixtures, llm), fixtures)
    assert "<script>alert(1)</script>" not in r.text


def test_unparseable_llm_output_shows_error(fixtures):
    r = generate(make_client(fixtures, FakeLLM("not json")), fixtures)
    assert r.status_code == 200
    assert "could not be generated" in r.text.lower()


def test_bad_path_shows_error_without_calling_llm(fixtures):
    llm = FakeLLM(doc())
    r = make_client(fixtures, llm).post("/generate", data={"path": "/nope.py"})
    assert "does not exist" in r.text
    assert llm.calls == []


def test_system_prompt_is_domain_free_and_notebook_goes_in_user_message(fixtures):
    llm = FakeLLM(doc())
    generate(make_client(fixtures, llm), fixtures)
    system, user = llm.calls[0]
    assert "x = 1" in user and "x = 1" not in system
    lowered = system.lower()
    for word in ("cash", "invoice", "payment", "customer", "bank"):
        assert word not in lowered
    # The Notebook is numbered so the LLM can cite absolute lines.
    assert re.search(r"^\s*8\b.*x = 1", user, re.MULTILINE)


def test_llm_request_metadata_is_logged_without_secrets(fixtures, caplog):
    import httpx

    from bricksplain.llm import OpenAICompatClient

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(doc())}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 7},
            },
        )

    client = OpenAICompatClient(
        Config("groq", "llama-x", "test-key"),
        transport=httpx.MockTransport(handler),
    )
    with caplog.at_level(logging.INFO, logger="bricksplain"):
        client.complete("sys", "usr")
    text = "\n".join(caplog.messages)
    assert "groq" in text and "llama-x" in text and "200" in text
    assert "11" in text and "7" in text and "latency" in text
    assert "test-key" not in text


def test_non_integer_citation_numbers_are_dropped(fixtures):
    bad = fact("Stringly.")
    bad["citations"][0]["start"] = "8"
    r = generate(make_client(fixtures, FakeLLM(doc(summary=[bad]))), fixtures)
    assert "Stringly." not in r.text
    assert "1 claim dropped" in r.text


def test_viewer_form_uses_the_edited_path(fixtures):
    r = make_client(fixtures, FakeLLM(doc())).get("/")
    assert r.text.count('name="path"') == 1
    assert 'formaction="/generate"' in r.text


def test_google_provider_posts_to_google_url_with_model_verbatim():
    import httpx

    from bricksplain.llm import OpenAICompatClient

    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    client = OpenAICompatClient(
        Config("google", "gemini-2.5-flash", "g-key"),
        transport=httpx.MockTransport(handler),
    )
    assert client.complete("sys", "usr") == "ok"
    assert seen["url"].startswith("https://generativelanguage.googleapis.com/")
    assert seen["body"]["model"] == "gemini-2.5-flash"
    assert seen["body"]["response_format"] == {"type": "json_object"}
    assert seen["auth"] == "Bearer g-key"


class SeqLLM:
    """Returns/raises the queued outputs in order."""

    def __init__(self, *outputs):
        self.outputs = list(outputs)
        self.calls = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        out = self.outputs.pop(0)
        if isinstance(out, Exception):
            raise out
        return out if isinstance(out, str) else json.dumps(out)


def test_retry_succeeds_with_failures_fed_back(fixtures, caplog):
    bad = fact("BAD CLAIM", quote="z = 3")
    llm = SeqLLM(doc(summary=[bad]), doc(summary=[fact("Fixed claim.")]))
    with caplog.at_level(logging.INFO, logger="bricksplain"):
        r = generate(make_client(fixtures, llm), fixtures)
    assert len(llm.calls) == 2
    assert "quote not found" in llm.calls[1][1]
    assert "Fixed claim." in r.text and "BAD CLAIM" not in r.text
    assert "dropped" not in r.text.lower()
    assert any("retry" in m for m in caplog.messages)


def test_claims_still_failing_after_retry_are_dropped_and_counted(fixtures):
    bad = fact("BAD CLAIM", quote="z = 3")
    out = doc(summary=[fact("Good claim."), bad])
    llm = SeqLLM(out, out)
    r = generate(make_client(fixtures, llm), fixtures)
    assert len(llm.calls) == 2
    assert "Good claim." in r.text and "BAD CLAIM" not in r.text
    assert "1 claim dropped" in r.text


def test_failed_retry_keeps_first_result(fixtures):
    from bricksplain.llm import LLMError

    out = doc(summary=[fact("Good claim."), fact("BAD", quote="z = 3")])
    r = generate(make_client(fixtures, SeqLLM(out, LLMError("boom"))), fixtures)
    assert "Good claim." in r.text and "1 claim dropped" in r.text


def _client_with(responses, sleeps, key="test-key"):
    import httpx

    from bricksplain.llm import OpenAICompatClient

    queue = list(responses)
    ok = httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
    return OpenAICompatClient(
        Config("groq", "m", key),
        transport=httpx.MockTransport(lambda req: queue.pop(0) if queue else ok),
        sleep=sleeps.append,
    )


def test_429_honours_retry_after_then_succeeds(caplog):
    import httpx

    sleeps = []
    client = _client_with([httpx.Response(429, headers={"retry-after": "7"})], sleeps)
    with caplog.at_level(logging.INFO, logger="bricksplain"):
        assert client.complete("sys", "SECRET-PROMPT") == "ok"
    assert sleeps == [7.0]
    text = "\n".join(caplog.messages)
    assert "429" in text and "7.0s" in text
    assert "SECRET-PROMPT" not in text and "test-key" not in text


def test_persistent_429_gives_up_with_clear_error_in_ui(fixtures):
    import httpx

    from bricksplain.llm import MAX_RATE_LIMIT_RETRIES

    sleeps = []
    client = _client_with([httpx.Response(429)] * 10, sleeps)
    r = generate(make_client(fixtures, client), fixtures)
    assert len(sleeps) == MAX_RATE_LIMIT_RETRIES
    assert "could not be generated" in r.text and "rate limiting" in r.text
    assert "Traceback" not in r.text


def test_persistent_server_failure_is_logged_and_shown(fixtures, caplog):
    import httpx

    client = _client_with([httpx.Response(500)], [])
    with caplog.at_level(logging.ERROR, logger="bricksplain"):
        r = generate(make_client(fixtures, client), fixtures)
    assert "HTTP 500" in r.text
    assert any("500" in m for m in caplog.messages)


# --- Citation range covers what the Claim asserts -------------------------


def whole_cell(cell=2, start=7, end=10, quote="x = 1", text="Cell sets values."):
    return {**fact(text, cell, start, end, quote), "describes_cell": True}


def test_whole_cell_claim_with_full_range_is_accepted(fixtures):
    llm = FakeLLM(doc(summary=[whole_cell()]))
    r = generate(make_client(fixtures, llm), fixtures)
    assert "Cell sets values." in r.text
    assert "dropped" not in r.text.lower()
    assert "start=7&amp;end=10" in r.text


def test_whole_cell_claim_with_narrow_range_is_rejected_with_reason(fixtures, caplog):
    llm = FakeLLM(doc(summary=[whole_cell(start=8, end=8)]))
    with caplog.at_level(logging.INFO, logger="bricksplain"):
        r = generate(make_client(fixtures, llm), fixtures)
    assert "Cell sets values." not in r.text
    assert "1 claim dropped" in r.text
    retry_prompt = llm.calls[1][1]
    assert "cell 2" in retry_prompt and "7-10" in retry_prompt


def test_retry_recovers_a_narrow_whole_cell_claim(fixtures):
    class Scripted(FakeLLM):
        def complete(self, system, user):
            self.calls.append((system, user))
            narrow = len(self.calls) == 1
            return json.dumps(
                doc(summary=[whole_cell(start=8, end=8) if narrow else whole_cell()])
            )

    llm = Scripted({})
    r = generate(make_client(fixtures, llm), fixtures)
    assert len(llm.calls) == 2
    assert "Cell sets values." in r.text
    assert "dropped" not in r.text.lower()


def test_multi_cell_claim_renders_one_link_per_cell_and_in_markdown(fixtures):
    multi = {
        "type": "fact",
        "text": "Spans two cells.",
        "citations": [
            {"cell": 2, "start": 8, "end": 8, "quote": "x = 1"},
            {"cell": 4, "start": 18, "end": 18, "quote": "%run ../shared/helper"},
        ],
    }
    client = make_client(fixtures, FakeLLM(doc(summary=[multi])))
    r = generate(client, fixtures)
    links = re.findall(r'href="(/source\?[^"]*start=[^"]*)"', r.docs["manager"])
    assert len(links) == 2
    assert "cell=2" in links[0] and "cell=4" in links[1]
    job, _ = re.search(r'data-job="(\w+)" data-audience="(\w+)"', r.page).groups()
    md = client.get(f"/jobs/{job}/manager/download.md").text
    assert md.count("&start=") == 2  # Citation links only, not Coverage links
    assert "Cell 2, line 8" in md and "Cell 4, line 18" in md


def test_narrow_whole_cell_claim_in_a_concern_is_also_rejected(fixtures):
    bad = {
        "type": "concern",
        "severity": "low",
        "text": "NARROW CONCERN",
        "describes_cell": True,
        "citations": [{"cell": 2, "start": 8, "end": 8, "quote": "x = 1"}],
    }
    r = generate(make_client(fixtures, FakeLLM(doc(potential_issues=[bad]))), fixtures)
    assert "NARROW CONCERN" not in r.text
    assert "1 claim dropped" in r.text


def test_unflagged_narrow_claim_still_passes(fixtures):
    r = generate(make_client(fixtures, FakeLLM(doc(summary=[fact()]))), fixtures)
    assert "Sets x." in r.text
    assert "dropped" not in r.text.lower()


def test_reasoning_effort_sent_to_openrouter_only():
    import httpx

    from bricksplain.config import Config
    from bricksplain.llm import OpenAICompatClient

    bodies = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    for provider in ("openrouter", "groq"):
        OpenAICompatClient(
            Config(provider, "m", "k", "low"), transport=httpx.MockTransport(handler)
        ).complete("s", "u")
    assert bodies[0]["reasoning"] == {"effort": "low"}
    assert "reasoning" not in bodies[1]
