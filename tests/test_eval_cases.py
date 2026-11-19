from pathlib import Path

import pytest

from bricksplain import notebook as nb
from bricksplain.audience_doc import (
    AUDIENCE_BY_KEY,
    AudienceDoc,
    Citation,
    Item,
    Section,
    verify,
)
from evals.cases import CASES, CLEAN_NOTEBOOK, HALT_CASES, SECTION_CASES
from evals.run import halt_claims, says_it_halts, section_cited, surfaced


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_expected_citation_points_at_real_lines(case):
    notebook = nb.load(case.notebook)
    citation = Citation(
        cell=case.cell, start=case.start, end=case.end, quote=case.quote
    )
    assert verify(citation, notebook) is None
    for cell, start, end, quote in case.also:
        assert (
            verify(Citation(cell=cell, start=start, end=end, quote=quote), notebook)
            is None
        )
    assert case.audience in AUDIENCE_BY_KEY


@pytest.mark.parametrize("case", HALT_CASES, ids=lambda c: c.name)
def test_print_only_check_points_at_real_lines(case):
    citation = Citation(
        cell=case.cell, start=case.start, end=case.end, quote=case.quote
    )
    assert verify(citation, nb.load(case.notebook)) is None
    assert "print" in case.quote.lower()


@pytest.mark.parametrize("case", SECTION_CASES, ids=lambda c: c.name)
def test_section_cases_name_a_real_section(case):
    keys = [k for k, _ in AUDIENCE_BY_KEY[case.audience].sections]
    assert case.section in keys


def doc(section, *items):
    return AudienceDoc([Section(section, section, list(items))], 0)


def fact(text, cell, start, end, kind="fact"):
    return Item(
        type=kind,
        text=text,
        severity="low" if kind == "concern" else None,
        citations=[Citation(cell=cell, start=start, end=end, quote="x")],
    )


def test_concern_only_case_ignores_a_fact_at_the_same_lines():
    case = next(c for c in CASES if c.name == "fifo-mismatch-is-a-concern")
    assert not surfaced(case, doc("gotchas", fact("sorted", 26, 320, 320)))
    assert surfaced(case, doc("gotchas", fact("sorted", 26, 320, 320, "concern")))


def test_alternative_locations_satisfy_a_case():
    case = next(c for c in CASES if c.name == "manager-sees-a-risk")
    assert surfaced(case, doc("s", fact("w", 37, 459, 459)))
    assert surfaced(case, doc("s", fact("w", 4, 34, 34)))
    assert not surfaced(case, doc("s", fact("w", 1, 2, 2)))


def test_halt_judge_flags_a_halting_claim_and_not_a_negated_one():
    assert says_it_halts("Duplicate check halts the run")
    assert not says_it_halts("Duplicate check only prints; does not halt the run")
    case = HALT_CASES[0]
    bad = doc(
        "verify", fact("Halts the run on duplicates", case.cell, case.start, case.end)
    )
    ok = doc(
        "verify",
        fact("Prints a warning, does not stop", case.cell, case.start, case.end),
    )
    assert halt_claims(case, bad) and not halt_claims(case, ok)


def test_section_case_needs_a_cited_item():
    case = SECTION_CASES[0]
    assert section_cited(case, doc(case.section, fact("a", 1, 1, 1)))
    assert not section_cited(case, doc(case.section))


def test_clean_notebook_exists_and_has_no_sample_vocabulary():
    from evals.cases import FORBIDDEN_TERMS

    text = Path(CLEAN_NOTEBOOK).read_text(encoding="utf-8").lower()
    assert [t for t in FORBIDDEN_TERMS if t in text] == []
    assert len(nb.load(CLEAN_NOTEBOOK).cells) >= 2


def test_cases_are_named_uniquely_and_complete():
    assert len({c.name for c in CASES}) == len(CASES) >= 5
    assert all(c.must_surface and c.why for c in CASES)


def test_generality_fixture_has_no_sample_domain_vocabulary():
    from evals.cases import FORBIDDEN_TERMS, GENERALITY

    text = Path(GENERALITY).read_text(encoding="utf-8").lower()
    assert [t for t in FORBIDDEN_TERMS if t in text] == []
