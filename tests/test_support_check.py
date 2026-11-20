import logging

from support import generate, make_client
from test_audience_docs import by_audience, fact

from bricksplain.decision import SUPPORT_THRESHOLD
from bricksplain.llm import LLMError

# small.py: Cell 2 is lines 7-10 ("x = 1" on line 8, "y = 2" on line 9).


def answers(manager, **others):
    return {"manager": manager, "developer": {}, "agent": {}, **others}


def test_claim_whose_quote_does_not_back_it_is_dropped_and_counted(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Good claim."), fact("Check HALTS the run.")]}
    llm = by_audience(answers(out), unsupported={"HALTS": ""})
    r = generate(make_client(llm, path), path)
    assert "Good claim." in r.docs["manager"]
    assert "HALTS" not in r.docs["manager"]
    assert "1 claim dropped" in r.docs["manager"]


def test_each_claim_is_judged_with_the_full_cited_lines_under_their_cell_label(
    fixtures,
):
    path = str(fixtures / "small.py")
    out = {
        "summary": [
            fact("First."),
            fact("Second.", quote="x"),
            fact("Wide.", start=8, end=9, quote="y = 2"),
        ]
    }
    llm = by_audience(answers(out))
    generate(make_client(llm, path), path)
    assert sorted(llm.support_calls) == [
        ("First.", ["Cell 2, line 8:\nx = 1"]),
        ("Second.", ["Cell 2, line 8:\nx = 1"]),
        ("Wide.", ["Cell 2, lines 8-9:\nx = 1\ny = 2"]),
    ]


def test_every_support_score_is_logged_without_claim_text(fixtures, caplog):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Secret claim text.")]}
    score = SUPPORT_THRESHOLD + 0.123  # supported, so there is no retry to log twice
    llm = by_audience(answers(out), support=lambda c, q: score)
    with caplog.at_level(logging.INFO, logger="bricksplain"):
        generate(make_client(llm, path), path)
    msgs = [r.getMessage() for r in caplog.records if "support score" in r.getMessage()]
    assert msgs == [f"support score manager/summary #0: {score:.3f}"]


def test_score_below_threshold_drops_and_at_threshold_keeps(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Low."), fact("Edge.")]}
    scores = {"Low.": SUPPORT_THRESHOLD - 0.001, "Edge.": SUPPORT_THRESHOLD}
    llm = by_audience(answers(out), support=lambda claim, quotes: scores[claim])
    r = generate(make_client(llm, path), path)
    assert "Edge." in r.docs["manager"]
    assert "Low." not in r.docs["manager"]


def test_doc_without_claims_makes_no_support_call(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(answers({}))
    generate(make_client(llm, path), path)
    assert llm.support_calls == []


def test_unsupported_claim_is_dropped_without_a_retry(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Good claim."), fact("Check HALTS the run.")]}
    llm = by_audience(answers(out), unsupported={"HALTS": ""})
    r = generate(make_client(llm, path), path)
    assert "HALTS" not in r.docs["manager"]
    assert "1 claim dropped" in r.docs["manager"]
    assert llm.seen.count("manager") == 1  # a retry would be a second call


def test_retry_recovers_a_citation_failure_and_is_support_checked(fixtures):
    path = str(fixtures / "small.py")
    bad = fact("Check HALTS the run.", quote="not in the cell")
    fixed = fact("Check only prints.")
    gen = iter([{"summary": [bad]}, {"summary": [fixed]}])
    llm = by_audience(answers(lambda: next(gen)))
    r = generate(make_client(llm, path), path)
    assert "Check only prints." in r.docs["manager"]
    assert "dropped" not in r.docs["manager"].lower()
    assert llm.seen.count("manager") == 2
    assert [c for c, _ in llm.support_calls] == ["Check only prints."]


def test_retry_feedback_names_the_citation_failure_not_support_drops(fixtures):
    path = str(fixtures / "small.py")
    prompts = []
    out = {
        "summary": [
            fact("Bad quote.", quote="not in the cell"),
            fact("Check HALTS the run."),
        ]
    }
    llm = by_audience(answers(out), unsupported={"HALTS": ""})
    inner = llm.complete

    def spy(system, user):
        prompts.append(user)
        return inner(system, user)

    llm.complete = spy
    generate(make_client(llm, path), path)
    feedback = next(p for p in prompts if "failed checks" in p)
    assert "quote not found" in feedback
    assert "HALTS" not in feedback
    assert "is not supported by its quoted text" not in feedback


def test_scores_logged_only_when_response_logging_is_on(fixtures, caplog):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Check HALTS the run.")]}
    llm = by_audience(answers(out), support=lambda c, q: SUPPORT_THRESHOLD / 2)
    with caplog.at_level(logging.WARNING, logger="bricksplain"):
        generate(make_client(llm, path), path)
    plain = [r for r in caplog.records if not getattr(r, "llm_response", False)]
    assert any("support check dropped" in r.getMessage() for r in plain)
    shown = f"{SUPPORT_THRESHOLD / 2:.2f}"
    assert not any(shown in r.getMessage() for r in plain)
    assert any(
        shown in r.getMessage()
        for r in caplog.records
        if getattr(r, "llm_response", False)
    )


def test_cached_draft_is_support_checked_again_without_a_generation_call(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Check HALTS the run.")]}
    llm = by_audience(answers(out), unsupported={"HALTS": ""})
    client = make_client(llm, path)
    generate(client, path)
    seen, judged = len(llm.seen), len(llm.support_calls)
    generate(client, path)
    assert llm.seen[seen:].count("manager") == 0  # generation comes from the cache
    assert len(llm.support_calls) > judged  # Jev is asked again


def test_cached_draft_picks_up_a_changed_support_verdict(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Check HALTS the run.")]}
    unsupported = {"HALTS": ""}
    llm = by_audience(answers(out), unsupported=unsupported)
    client = make_client(llm, path)
    first = generate(client, path)
    assert "HALTS" not in first.docs["manager"]
    unsupported.clear()
    second = generate(client, path)
    assert "HALTS" in second.docs["manager"]


def test_support_failure_is_isolated_to_its_audience_doc(fixtures):
    path = str(fixtures / "small.py")

    def boom(claim, quotes):
        if claim == "Manager claim.":
            raise LLMError("support down")
        return 1.0

    llm = by_audience(
        answers(
            {"summary": [fact("Manager claim.")]},
            developer={"gotchas": [fact("Dev claim.")]},
        ),
        support=boom,
    )
    r = generate(make_client(llm, path), path)
    assert 'data-doc-state="failed"' in r.docs["manager"]
    assert "Manager claim." not in r.docs["manager"]
    assert 'data-doc-state="done"' in r.docs["developer"]
    assert "Dev claim." in r.docs["developer"]


def test_check_is_off_without_a_judge_and_keeps_every_verified_claim(fixtures):
    from fastapi.testclient import TestClient

    from bricksplain.app import create_app
    from bricksplain.config import Config

    path = str(fixtures / "small.py")
    llm = by_audience(answers({"summary": [fact("Check HALTS the run.")]}))
    client = TestClient(
        create_app(Config("groq", "m", "k"), default_path=path, llm_client=llm)
    )
    r = generate(client, path)
    assert "HALTS" in r.docs["manager"]
    assert llm.support_calls == []


def test_retry_that_says_less_does_not_replace_a_fuller_first_pass(fixtures):
    path = str(fixtures / "small.py")
    first = {
        "summary": [
            fact("One."),
            fact("Two.", quote="y = 2", start=9, end=9),
            fact("Bad quote.", quote="not in the cell"),
        ]
    }
    terse = {"summary": [fact("One.")]}
    gen = iter([first, terse])
    llm = by_audience(answers(lambda: next(gen)))
    r = generate(make_client(llm, path), path)
    assert llm.seen.count("manager") == 2
    assert "One." in r.docs["manager"] and "Two." in r.docs["manager"]


def test_instruction_section_items_are_verified_but_not_scored(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(
        {
            "manager": {},
            "developer": {},
            "agent": {
                "invariants": [fact("Invariant HALTS.")],
                "verify": [
                    fact("x must be 1; compare to the last run."),
                    fact("Bad quote.", quote="not in the cell"),
                ],
            },
        },
        unsupported={"HALTS": "", "must be": ""},
    )
    r = generate(make_client(llm, path), path)
    agent = r.docs["agent"]
    assert "Invariant HALTS." not in agent  # scored and dropped
    assert "x must be 1; compare to the last run." in agent  # not scored
    assert "Bad quote." not in agent  # its Citation still fails verification
    # (scored once per generation pass; the bad quote triggers a Citation retry)
    assert {c for c, _ in llm.support_calls} == {"Invariant HALTS."}
