import json
import threading

from support import (
    generate,
    make_client,
    panel,
    panel_ids,
    wait_done,
)

from bricksplain.audience_doc import AUDIENCES, load_prompt
from bricksplain.llm import LLMError

# small.py: Cell 2 is lines 7-10 ("x = 1" on line 8).

DEV = ("notebook_map", "data_flow", "business_rules", "inferred_glossary", "gotchas")
AGENT = ("purpose", "invariants", "risky_areas", "verify")


def fact(text, quote="x = 1"):
    return {
        "type": "fact",
        "text": text,
        "citations": [{"cell": 2, "start": 8, "end": 8, "quote": quote}],
    }


def by_audience(mapping, unsupported=None, support=None):
    """An LLM that answers by which Audience's system prompt it is given.

    It is also the SupportJudge: each (claim, quotes) it is asked about is recorded
    in `support_calls`, not `seen`. The score is `support(claim, quotes)` if given,
    else 0.0 for claims whose text contains a key of `unsupported`, else 1.0."""
    prompts = {load_prompt(a.prompt): a.key for a in AUDIENCES}

    class LLM:
        def __init__(self):
            self.lock = threading.Lock()
            self.seen = []
            self.support_calls = []

        def score(self, claim, quotes):
            with self.lock:
                self.support_calls.append((claim, quotes))
            if support:
                return support(claim, quotes)
            return 0.0 if any(k in claim for k in (unsupported or {})) else 1.0

        def complete(self, system, user):
            key = prompts[system]
            with self.lock:
                self.seen.append(key)
            out = mapping[key]
            if callable(out):
                out = out()
            if isinstance(out, Exception):
                raise out
            return out if isinstance(out, str) else json.dumps(out)

    return LLM()


def test_developer_doc_has_fixed_skeleton_and_cited_glossary(fixtures):
    llm = by_audience(
        {
            "manager": {},
            "agent": {},
            "developer": {"inferred_glossary": [fact("x: a value.")]},
        }
    )
    r = generate(
        make_client(llm, str(fixtures / "small.py")), str(fixtures / "small.py")
    )
    dev = r.docs["developer"]
    for heading in (
        "Notebook map by Cell",
        "Data flow",
        "Business rules",
        "Inferred Glossary",
        "Gotchas and how to run",
    ):
        assert f"<h3>{heading}</h3>" in dev
    assert "x: a value." in dev and "cell=2&amp;start=8&amp;end=8" in dev


def test_agent_doc_has_fixed_skeleton(fixtures):
    llm = by_audience(
        {"manager": {}, "developer": {}, "agent": {"purpose": [fact("Sets x.")]}}
    )
    r = generate(
        make_client(llm, str(fixtures / "small.py")), str(fixtures / "small.py")
    )
    for heading in ("Purpose", "Invariants", "Risky areas", "How to verify changes"):
        assert f"<h3>{heading}</h3>" in r.docs["agent"]
    assert "Sets x." in r.docs["agent"]


def test_glossary_only_in_developer_doc(fixtures):
    llm = by_audience({"manager": {}, "developer": {}, "agent": {}})
    r = generate(
        make_client(llm, str(fixtures / "small.py")), str(fixtures / "small.py")
    )
    assert "Inferred Glossary" in r.docs["developer"]
    assert "Inferred Glossary" not in r.docs["manager"]
    assert "Inferred Glossary" not in r.docs["agent"]


def test_uncited_glossary_entry_is_dropped(fixtures):
    entry = {"type": "fact", "text": "UNCITED TERM", "citations": []}
    llm = by_audience(
        {"manager": {}, "agent": {}, "developer": {"inferred_glossary": [entry]}}
    )
    r = generate(
        make_client(llm, str(fixtures / "small.py")), str(fixtures / "small.py")
    )
    assert "UNCITED TERM" not in r.docs["developer"]
    assert "1 claim dropped" in r.docs["developer"]


def test_three_calls_run_concurrently(fixtures):
    barrier = threading.Barrier(3, timeout=5)

    def wait():
        barrier.wait()  # raises BrokenBarrierError unless all three are in flight
        return {}

    llm = by_audience({"manager": wait, "developer": wait, "agent": wait})
    r = generate(
        make_client(llm, str(fixtures / "small.py")), str(fixtures / "small.py")
    )
    assert sorted(llm.seen) == ["agent", "developer", "manager"]
    assert all('data-doc-state="done"' in h for h in r.docs.values())


def test_each_tab_shows_state_and_fills_in_as_it_finishes(fixtures):
    gate = threading.Event()
    llm = by_audience(
        {
            "manager": {"summary": [fact("Manager text.")]},
            "agent": {},
            "developer": lambda: gate.wait(5) and {},
        }
    )
    path = str(fixtures / "small.py")
    client = make_client(llm, path)
    page = client.post("/generate", data={"path": path}).text
    assert [a for _, a in panel_ids(page)] == ["manager", "developer", "agent"]
    job = panel_ids(page)[0][0]
    try:
        # Manager finishes while the developer call is still blocked.
        done = wait_done(client, page, only=("manager",))
        assert "Manager text." in done["manager"]
        dev = panel(client, job, "developer")
        assert 'data-doc-state="running"' in dev
    finally:
        gate.set()
    assert 'data-doc-state="done"' in wait_done(client, page)["developer"]


def test_one_failing_doc_leaves_the_others_unaffected(fixtures):
    llm = by_audience(
        {
            "manager": {"summary": [fact("Manager text.")]},
            "developer": LLMError("The LLM provider returned HTTP 500."),
            "agent": {"purpose": [fact("Agent text.")]},
        }
    )
    r = generate(
        make_client(llm, str(fixtures / "small.py")), str(fixtures / "small.py")
    )
    assert 'data-doc-state="failed"' in r.docs["developer"]
    assert "Developer doc could not be generated" in r.docs["developer"]
    assert "HTTP 500" in r.docs["developer"]
    assert "Manager text." in r.docs["manager"]
    assert "Agent text." in r.docs["agent"]


def test_unexpected_crash_in_one_doc_is_contained(fixtures):
    llm = by_audience({"manager": {}, "developer": {}, "agent": lambda: 1 / 0})
    r = generate(
        make_client(llm, str(fixtures / "small.py")), str(fixtures / "small.py")
    )
    assert 'data-doc-state="failed"' in r.docs["agent"]
    assert 'data-doc-state="done"' in r.docs["manager"]


def test_unknown_job_is_404(fixtures):
    client = make_client(by_audience({}), str(fixtures / "small.py"))
    assert client.get("/jobs/nope/manager").status_code == 404


def test_every_audience_has_its_own_domain_free_prompt():
    prompts = [load_prompt(a.prompt) for a in AUDIENCES]
    assert len(set(prompts)) == 3
    for p in prompts:
        for word in ("cash", "invoice", "payment", "customer", "bank"):
            assert word not in p.lower()


def test_every_prompt_carries_the_same_generic_checklist():
    checklist = load_prompt("checklist")
    for phrase in (
        "disagree with",
        "never used",
        "reassigned",
        "overwrite",
        "do not stop",
        "outside the notebook",
    ):
        assert phrase in checklist.lower()
    for a in AUDIENCES:
        assert checklist.strip() in load_prompt(a.prompt)


def test_each_prompt_says_how_to_express_findings_for_its_audience():
    by_key = {a.key: load_prompt(a.prompt).lower() for a in AUDIENCES}
    assert "business consequence" in by_key["manager"]
    assert "code reality" in by_key["developer"]
    for word in ("invariant", "risky", "runnable check"):
        assert word in by_key["agent"]


CONCERN = {
    "type": "concern",
    "severity": "high",
    "text": "Check only prints.",
    "citations": [{"cell": 2, "start": 8, "end": 8, "quote": "x = 1"}],
}
NONE = {"type": "no_findings", "text": "The checklist found nothing."}


def test_findings_render_as_concerns_with_citations(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(
        {"manager": {"potential_issues": [CONCERN]}, "developer": {}, "agent": {}}
    )
    html = generate(make_client(llm, path), path).docs["manager"]
    assert "Check only prints." in html
    assert "Concern" in html
    assert "cell=2&amp;start=8&amp;end=8" in html


def test_no_findings_statement_is_accepted_and_shown_without_citation(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(
        {"manager": {"potential_issues": [NONE]}, "developer": {}, "agent": {}}
    )
    html = generate(make_client(llm, path), path).docs["manager"]
    assert "The checklist found nothing." in html
    assert "No findings" in html
    assert "dropped" not in html.lower()
    assert llm.support_calls == []  # nothing to support-check
    assert llm.seen.count("manager") == 1


def test_no_findings_is_in_the_markdown_download(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(
        {"manager": {"potential_issues": [NONE]}, "developer": {}, "agent": {}}
    )
    client = make_client(llm, path)
    r = generate(client, path)
    job = panel_ids(r.page)[0][0]
    md = client.get(f"/jobs/{job}/manager/download.md").text
    assert "No findings" in md and "The checklist found nothing." in md
