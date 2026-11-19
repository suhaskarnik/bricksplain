import logging
import shutil

from fastapi.testclient import TestClient
from support import generate, make_client
from test_audience_docs import by_audience, fact

from bricksplain.app import create_app
from bricksplain.config import Config

ANSWERS = {"manager": {"summary": [fact("x is one.")]}, "developer": {}, "agent": {}}


def test_second_generate_hits_cache_without_llm_call(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(ANSWERS)
    client = make_client(llm, path)
    generate(client, path)
    calls = len(llm.seen)
    assert calls == 3
    second = generate(client, path)
    assert len(llm.seen) == calls
    assert "x is one." in second.docs["manager"]


def test_cache_survives_a_new_app_instance(fixtures):
    path = str(fixtures / "small.py")
    generate(make_client(by_audience(ANSWERS), path), path)
    llm = by_audience(ANSWERS)
    r = generate(make_client(llm, path), path)
    assert llm.seen == []
    assert "x is one." in r.docs["manager"]


def test_regenerate_bypasses_and_refreshes_cache(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(ANSWERS)
    client = make_client(llm, path)
    generate(client, path)
    docs = generate(client, path, regenerate="1").docs
    assert len(llm.seen) == 6
    assert "x is one." in docs["manager"]
    generate(client, path)
    assert len(llm.seen) == 6  # refreshed entry is still served from cache


def test_changed_notebook_invalidates(fixtures, tmp_path):
    src = tmp_path / "nb.py"
    shutil.copy(fixtures / "small.py", src)
    llm = by_audience(ANSWERS)
    client = make_client(llm, str(src))
    generate(client, str(src))
    src.write_text(src.read_text() + "\ny = 2\n")
    generate(client, str(src))
    assert len(llm.seen) == 6


def test_changed_model_invalidates(fixtures):
    path = str(fixtures / "small.py")
    llm = by_audience(ANSWERS)
    generate(make_client(llm, path), path)
    other = TestClient(
        create_app(
            Config("groq", "other-model", "k"), default_path=path, llm_client=llm
        )
    )
    generate(other, path)
    assert len(llm.seen) == 6


def test_changed_prompt_invalidates_only_that_audience(fixtures, monkeypatch):
    import bricksplain.cache as cache_mod

    path = str(fixtures / "small.py")
    llm = by_audience(ANSWERS)
    client = make_client(llm, path)
    generate(client, path)
    real = cache_mod.load_prompt
    monkeypatch.setattr(
        cache_mod,
        "load_prompt",
        lambda n: real(n) + " edited" if n == "manager" else real(n),
    )
    generate(client, path)
    assert llm.seen[3:] == ["manager"]


def test_cache_hits_and_misses_logged_at_info(fixtures, caplog):
    path = str(fixtures / "small.py")
    client = make_client(by_audience(ANSWERS), path)
    with caplog.at_level(logging.INFO, logger="bricksplain"):
        generate(client, path)
        assert "cache miss: manager" in caplog.text
        generate(client, path)
        assert "cache hit: manager" in caplog.text


def test_doc_with_dropped_claims_is_not_cached(fixtures):
    path = str(fixtures / "small.py")
    bad = {"summary": [fact("x is one.", quote="not in the notebook")]}
    llm = by_audience({"manager": bad, "developer": {}, "agent": {}})
    client = make_client(llm, path)
    generate(client, path)
    seen = len(llm.seen)
    generate(client, path)
    assert llm.seen[seen:].count("manager") >= 1


def test_failing_claim_content_is_logged_for_diagnosis(fixtures, caplog):
    path = str(fixtures / "small.py")
    bad = {"summary": [fact("x is one.", quote="made up quote")]}
    client = make_client(
        by_audience({"manager": bad, "developer": {}, "agent": {}}), path
    )
    with caplog.at_level(logging.WARNING, logger="bricksplain"):
        generate(client, path)
    assert "made up quote" in caplog.text
    assert "x is one." in caplog.text


def test_quote_without_magic_prefix_verifies_against_markdown_cell(fixtures):
    path = str(fixtures / "small.py")
    claim = {
        "type": "fact",
        "text": "The notebook has a title and notes.",
        "citations": [
            {"cell": 1, "start": 3, "end": 4, "quote": "## Title\nsome notes"}
        ],
    }
    llm = by_audience({"manager": {"summary": [claim]}, "developer": {}, "agent": {}})
    r = generate(make_client(llm, path), path)
    assert "The notebook has a title and notes." in r.docs["manager"]
    assert llm.seen.count("manager") == 1  # no retry: nothing failed


def test_changed_support_prompt_invalidates_every_audience(fixtures, monkeypatch):
    import bricksplain.cache as cache_mod

    path = str(fixtures / "small.py")
    llm = by_audience(ANSWERS)
    client = make_client(llm, path)
    generate(client, path)
    real = cache_mod.load_prompt
    monkeypatch.setattr(
        cache_mod,
        "load_prompt",
        lambda n: real(n) + " edited" if n == "support" else real(n),
    )
    generate(client, path)
    assert sorted(llm.seen[3:]) == ["agent", "developer", "manager"]
