from support import generate, make_client, panel_ids
from test_audience_docs import by_audience

# small.py cells: 1 = lines 2-5, 2 = 7-10, 3 = 12-15, 4 = 17-18 (14 lines in all).


def cite(cell, start, end, quote):
    return {"cell": cell, "start": start, "end": end, "quote": quote}


def claim(text, *citations):
    return {"type": "fact", "text": text, "citations": list(citations)}


# Overlapping ranges in Cell 2 (8-9, 8-8, 8-10) must count once: lines 8-10.
OVERLAPPING = {
    "summary": [
        claim("A.", cite(2, 8, 9, "x = 1"), cite(1, 3, 3, "Title")),
        claim("B.", cite(2, 8, 8, "x = 1")),
        claim("C.", cite(2, 8, 10, "y = 2")),
    ]
}


def run(fixtures, manager):
    path = str(fixtures / "small.py")
    llm = by_audience({"manager": manager, "developer": {}, "agent": {}})
    client = make_client(llm, path)
    r = generate(client, path)
    return client, r, llm


def test_page_shows_shares_with_overlaps_counted_once(fixtures):
    _, r, _ = run(fixtures, OVERLAPPING)
    html = r.docs["manager"]
    assert "Coverage" in html
    assert "2 of 4 Cells" in html
    assert "4 of 14 lines" in html


def test_uncited_cells_are_listed_with_source_viewer_links(fixtures):
    _, r, _ = run(fixtures, OVERLAPPING)
    html = r.docs["manager"]
    assert "cell=3" in html and "cell=4" in html
    assert "Cell 3" in html and "Cell 4" in html
    assert "Uncited" in html


def test_doc_with_no_claims_reports_zero_coverage_and_every_cell(fixtures):
    _, r, _ = run(fixtures, {})
    assert "0 of 4 Cells" in r.docs["manager"]
    assert "0 of 14 lines" in r.docs["manager"]


def test_dropped_claims_do_not_count_toward_coverage(fixtures):
    path = str(fixtures / "small.py")
    out = {"summary": [claim("HALTS.", cite(2, 8, 8, "x = 1"))]}
    llm = by_audience(
        {"manager": out, "developer": {}, "agent": {}}, unsupported={"HALTS": "no"}
    )
    r = generate(make_client(llm, path), path)
    assert "0 of 4 Cells" in r.docs["manager"]


def test_markdown_download_includes_the_same_summary(fixtures):
    client, r, _ = run(fixtures, OVERLAPPING)
    job = next(j for j, a in panel_ids(r.page) if a == "manager")
    md = client.get(f"/jobs/{job}/manager/download.md").text
    assert "## Coverage" in md
    assert "2 of 4 Cells" in md and "4 of 14 lines" in md
    assert "/source?path=" in md and "&cell=3" in md and "&cell=4" in md


def test_coverage_is_not_passed_back_to_the_llm(fixtures):
    path = str(fixtures / "small.py")
    prompts = []
    llm = by_audience({"manager": OVERLAPPING, "developer": {}, "agent": {}})
    inner = llm.complete

    def spy(system, user):
        prompts.append(system + user)
        return inner(system, user)

    llm.complete = spy
    generate(make_client(llm, path), path)
    assert not any("Coverage" in p or "of 14 lines" in p for p in prompts)


def test_low_coverage_never_causes_a_rejection_or_retry(fixtures):
    _, r, llm = run(fixtures, {"summary": [claim("A.", cite(2, 8, 8, "x = 1"))]})
    assert "dropped" not in r.docs["manager"].lower()
    assert llm.seen.count("manager") == 1


def test_cached_docs_also_show_coverage(fixtures):
    client, _, _ = run(fixtures, OVERLAPPING)
    r = generate(client, str(fixtures / "small.py"))
    assert "2 of 4 Cells" in r.docs["manager"]
