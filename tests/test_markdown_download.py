import re

import pytest
from support import generate, make_client, panel_ids
from test_audience_docs import by_audience, fact

from bricksplain.audience_doc import AUDIENCES

SECTIONS = {
    "manager": ("Summary", "Potential issues"),
    "developer": ("Notebook map by Cell", "Gotchas and how to run"),
    "agent": ("Purpose", "How to verify changes"),
}
FIRST = {"manager": "summary", "developer": "notebook_map", "agent": "purpose"}


def llm_with(key):
    out = {a.key: {} for a in AUDIENCES}
    out[key] = {
        FIRST[key]: [
            fact("It sets x."),
            {
                "type": "concern",
                "text": "x is hardcoded.",
                "severity": "high",
                "citations": [{"cell": 2, "start": 8, "end": 8, "quote": "x = 1"}],
            },
            {"type": "context", "text": "Hardcoding is generally risky."},
        ]
    }
    return by_audience(out)


@pytest.mark.parametrize("key", [a.key for a in AUDIENCES])
def test_markdown_download_keeps_skeleton_labels_and_citations(fixtures, key):
    path = str(fixtures / "small.py")
    client = make_client(llm_with(key), path)
    r = generate(client, path)
    assert "Download .md" in r.docs[key]
    job_id = next(j for j, a in panel_ids(r.page) if a == key)

    resp = client.get(f"/jobs/{job_id}/{key}/download.md")
    assert resp.status_code == 200
    assert "attachment" in resp.headers["content-disposition"]
    assert ".md" in resp.headers["content-disposition"]
    assert resp.headers["content-type"].startswith("text/markdown")
    md = resp.text
    for heading in SECTIONS[key]:
        assert f"## {heading}" in md
    assert "**Fact**" in md
    assert "**Concern (high)**" in md
    assert "**Context (not from the Notebook)**" in md
    assert re.search(
        r"\[Cell 2, line 8\]\(/source\?path=[^)]+&cell=2&start=8&end=8\)", md
    )
    assert "Hardcoding is generally risky." in md


def test_download_unknown_job_is_404(client):
    assert client.get("/jobs/nope/manager/download.md").status_code == 404
