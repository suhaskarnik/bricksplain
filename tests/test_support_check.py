import json

from support import generate, make_client
from test_audience_docs import by_audience, fact

from bricksplain.llm import LLMError

# small.py: Cell 2 is lines 7-10 ("x = 1" on line 8, "y = 2" on line 9).


def answers(manager, **others):
    return {"manager": manager, "developer": {}, "agent": {}, **others}


def test_claim_whose_quote_does_not_back_it_is_dropped_and_counted(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Good claim."), fact("Check HALTS the run.")]}
    llm = by_audience(answers(out), unsupported={"HALTS": "quote only prints"})
    r = generate(make_client(llm, path), path)
    assert "Good claim." in r.docs["manager"]
    assert "HALTS" not in r.docs["manager"]
    assert "1 claim dropped" in r.docs["manager"]


def test_support_check_is_one_batched_call_with_every_claim_and_quote(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("First."), fact("Second.", quote="x")]}
    llm = by_audience(answers(out))
    generate(make_client(llm, path), path)
    assert len(llm.support_calls) == 1
    sent = json.loads(llm.support_calls[0])["claims"]
    assert [(c["text"], c["quotes"]) for c in sent] == [
        ("First.", ["x = 1"]),
        ("Second.", ["x"]),
    ]


def test_doc_without_claims_makes_no_support_call(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(answers({}))
    generate(make_client(llm, path), path)
    assert llm.support_calls == []


def test_retry_with_reason_recovers_an_unsupported_claim(fixtures):
    path = str(fixtures / "small.py")
    bad, fixed = fact("Check HALTS the run."), fact("Check only prints.")
    gen = iter([{"summary": [bad]}, {"summary": [fixed]}])
    llm = by_audience(
        answers(lambda: next(gen)), unsupported={"HALTS": "quote only prints"}
    )
    r = generate(make_client(llm, path), path)
    assert "Check only prints." in r.docs["manager"]
    assert "HALTS" not in r.docs["manager"]
    assert "dropped" not in r.docs["manager"].lower()
    assert llm.seen.count("manager") == 2


def test_reason_is_fed_back_to_the_retry(fixtures):
    path = str(fixtures / "small.py")
    prompts = []
    out = {"summary": [fact("Check HALTS the run.")]}
    llm = by_audience(answers(out), unsupported={"HALTS": "quote only prints"})
    inner = llm.complete

    def spy(system, user):
        prompts.append(user)
        return inner(system, user)

    llm.complete = spy
    generate(make_client(llm, path), path)
    assert any("quote only prints" in p and "not supported" in p for p in prompts)


def test_support_reasons_logged_only_when_response_logging_is_on(fixtures, caplog):
    import logging

    path = str(fixtures / "small.py")
    out = {"summary": [fact("Check HALTS the run.")]}
    llm = by_audience(answers(out), unsupported={"HALTS": "quote only prints"})
    with caplog.at_level(logging.WARNING, logger="bricksplain"):
        generate(make_client(llm, path), path)
    plain = [r for r in caplog.records if not getattr(r, "llm_response", False)]
    assert any("support check dropped" in r.getMessage() for r in plain)
    assert not any("quote only prints" in r.getMessage() for r in plain)
    assert any(
        "quote only prints" in r.getMessage()
        for r in caplog.records
        if getattr(r, "llm_response", False)
    )


def test_doc_with_support_drops_is_not_cached(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [fact("Check HALTS the run.")]}
    llm = by_audience(answers(out), unsupported={"HALTS": "no"})
    client = make_client(llm, path)
    generate(client, path)
    seen = len(llm.seen)
    generate(client, path)
    assert llm.seen[seen:].count("manager") >= 1


def test_support_call_failure_is_isolated_to_its_audience_doc(fixtures):
    path = str(fixtures / "small.py")

    def boom(user):
        claims = json.loads(user)["claims"]
        if any(c["text"] == "Manager claim." for c in claims):
            raise LLMError("support down")
        return json.dumps(
            {"verdicts": [{"id": c["id"], "supported": True} for c in claims]}
        )

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


def test_unusable_support_answer_fails_the_doc_not_the_run(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(
        answers({"summary": [fact("Manager claim.")]}), support=lambda u: "not json"
    )
    r = generate(make_client(llm, path), path)
    assert 'data-doc-state="failed"' in r.docs["manager"]


def test_claim_missing_from_verdicts_is_treated_as_unsupported(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(
        answers({"summary": [fact("Manager claim.")]}),
        support=lambda u: json.dumps({"verdicts": []}),
    )
    r = generate(make_client(llm, path), path)
    assert "Manager claim." not in r.docs["manager"]
    assert "1 claim dropped" in r.docs["manager"]


def test_verdict_ids_returned_as_strings_still_match(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(
        answers({"summary": [fact("Manager claim.")]}),
        support=lambda u: json.dumps(
            {"verdicts": [{"id": "0", "supported": True, "reason": "ok"}]}
        ),
    )
    r = generate(make_client(llm, path), path)
    assert "Manager claim." in r.docs["manager"]
    assert "dropped" not in r.docs["manager"].lower()
