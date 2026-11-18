import json
import logging
import re
from urllib.parse import unquote

import pytest
from fastapi.testclient import TestClient

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
    app = create_app(
        Config("groq", "m", "test-key"),
        default_path=str(fixtures / "small.py"),
        llm_client=llm,
    )
    return TestClient(app)


def generate(client, fixtures):
    return client.post("/generate", data={"path": str(fixtures / "small.py")})


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
    assert "/source?" not in r.text


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
