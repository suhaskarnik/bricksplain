from pathlib import Path

import pytest

from bricksplain import notebook as nb
from bricksplain.audience_doc import AUDIENCE_BY_KEY, Citation, verify
from evals.cases import CASES


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_expected_citation_points_at_real_lines(case):
    notebook = nb.load(case.notebook)
    citation = Citation(
        cell=case.cell, start=case.start, end=case.end, quote=case.quote
    )
    assert verify(citation, notebook) is None
    assert case.audience in AUDIENCE_BY_KEY


def test_cases_are_named_uniquely_and_complete():
    assert len({c.name for c in CASES}) == len(CASES) >= 5
    assert all(c.must_surface and c.why for c in CASES)


def test_generality_fixture_has_no_sample_domain_vocabulary():
    from evals.cases import FORBIDDEN_TERMS, GENERALITY

    text = Path(GENERALITY).read_text(encoding="utf-8").lower()
    assert [t for t in FORBIDDEN_TERMS if t in text] == []
