import logging

from support import generate, make_client
from test_audience_docs import by_audience, fact

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


def test_each_claim_is_judged_with_its_own_quotes(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("First."), fact("Second.", quote="x")]}
    llm = by_audience(answers(out))
    generate(make_client(llm, path), path)
    assert sorted(llm.support_calls) == [("First.", ["x = 1"]), ("Second.", ["x"])]


def test_score_below_threshold_drops_and_at_threshold_keeps(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Low."), fact("Edge.")]}
    scores = {"Low.": 0.49, "Edge.": 0.5}
    llm = by_audience(answers(out), support=lambda claim, quotes: scores[claim])
    r = generate(make_client(llm, path), path)
    assert "Edge." in r.docs["manager"]
    assert "Low." not in r.docs["manager"]


def test_doc_without_claims_makes_no_support_call(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(answers({}))
    generate(make_client(llm, path), path)
    assert llm.support_calls == []


def test_retry_recovers_an_unsupported_claim(fixtures):
    path = str(fixtures / "small.py")
    bad, fixed = fact("Check HALTS the run."), fact("Check only prints.")
    gen = iter([{"summary": [bad]}, {"summary": [fixed]}])
    llm = by_audience(answers(lambda: next(gen)), unsupported={"HALTS": ""})
    r = generate(make_client(llm, path), path)
    assert "Check only prints." in r.docs["manager"]
    assert "HALTS" not in r.docs["manager"]
    assert "dropped" not in r.docs["manager"].lower()
    assert llm.seen.count("manager") == 2


def test_failing_claim_text_is_fed_back_to_the_retry_without_a_score(fixtures):
    path = str(fixtures / "small.py")
    prompts = []
    out = {"summary": [fact("Check HALTS the run.")]}
    llm = by_audience(answers(out), support=lambda c, q: 0.12 if "HALTS" in c else 1.0)
    inner = llm.complete

    def spy(system, user):
        prompts.append(user)
        return inner(system, user)

    llm.complete = spy
    generate(make_client(llm, path), path)
    feedback = next(p for p in prompts if "Check HALTS the run." in p)
    assert "is not supported by its quoted text" in feedback
    assert "0.12" not in feedback


def test_scores_logged_only_when_response_logging_is_on(fixtures, caplog):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Check HALTS the run.")]}
    llm = by_audience(answers(out), support=lambda c, q: 0.12)
    with caplog.at_level(logging.WARNING, logger="bricksplain"):
        generate(make_client(llm, path), path)
    plain = [r for r in caplog.records if not getattr(r, "llm_response", False)]
    assert any("support check dropped" in r.getMessage() for r in plain)
    assert not any("0.12" in r.getMessage() for r in plain)
    assert any(
        "0.12" in r.getMessage()
        for r in caplog.records
        if getattr(r, "llm_response", False)
    )


def test_doc_with_support_drops_is_cached_to_avoid_repeat_cost(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Check HALTS the run.")]}
    llm = by_audience(answers(out), unsupported={"HALTS": ""})
    client = make_client(llm, path)
    generate(client, path)
    seen = len(llm.seen)
    generate(client, path)
    assert llm.seen[seen:].count("manager") == 0


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
