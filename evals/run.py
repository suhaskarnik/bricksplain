"""Live evaluation: `just eval`. Calls the real configured provider."""

import os
import sys
from pathlib import Path

from bricksplain import notebook as nb
from bricksplain.audience_doc import (
    AUDIENCE_BY_KEY,
    AUDIENCES,
    SUPPORT_PROMPT,
    AudienceDoc,
    generate_doc,
    load_prompt,
    verify,
)
from bricksplain.config import ConfigError, load_config
from bricksplain.decision import JevJudge
from bricksplain.llm import OpenAICompatClient

from .cases import (
    CASES,
    CLEAN_NOTEBOOK,
    FORBIDDEN_TERMS,
    GENERALITY,
    HALT_CASES,
    HALT_WORDS,
    NEGATIONS,
    SECTION_CASES,
    EvalCase,
    HaltCase,
    SectionCase,
)


def surfaced(case: EvalCase, doc: AudienceDoc) -> bool:
    """True when a Claim cites lines overlapping an acceptable Line Range."""
    return any(
        c.cell == cell and c.start <= end and c.end >= start
        for s in doc.sections
        for item in s.items
        if item.type == "concern" or not case.concern_only
        for c in item.citations
        for cell, start, end, _ in case.locations()
    )


def section_cited(case: SectionCase, doc: AudienceDoc) -> bool:
    """True when the case's section holds a cited Fact or Concern."""
    return any(
        item.citations
        for s in doc.sections
        if s.key == case.section
        for item in s.items
    )


def says_it_halts(text: str) -> bool:
    """True when the text claims a check stops the run and does not negate it."""
    t = text.lower()
    return any(w in t for w in HALT_WORDS) and not any(n in t for n in NEGATIONS)


def halt_claims(case: HaltCase, doc: AudienceDoc) -> list[str]:
    """Texts of Claims citing the print-only check that say it halts the run."""
    return [
        item.text
        for s in doc.sections
        for item in s.items
        if says_it_halts(item.text)
        and any(
            c.cell == case.cell and c.start <= case.end and c.end >= case.start
            for c in item.citations
        )
    ]


def invented_concerns(doc: AudienceDoc) -> list[str]:
    """Concerns raised on a Notebook that has no risks."""
    return [
        item.text for s in doc.sections for item in s.items if item.type == "concern"
    ]


def doc_text(doc: AudienceDoc) -> str:
    return " ".join(item.text for s in doc.sections for item in s.items).lower()


def generality_problems(notebook: nb.Notebook, doc: AudienceDoc) -> list[str]:
    """Why a doc for the unrelated-domain Notebook is not domain-agnostic or unverified."""
    problems = []
    text = doc_text(doc)
    problems += [f"mentions {t!r}" for t in FORBIDDEN_TERMS if t in text]
    if doc.dropped:
        problems.append(f"{doc.dropped} claim(s) had citations that failed to verify")
    problems += [
        f"citation does not verify: {why}"
        for s in doc.sections
        for item in s.items
        for c in item.citations
        if (why := verify(c, notebook))
    ]
    return problems


def main() -> None:
    try:
        config = load_config(Path.cwd(), os.environ)
        client = OpenAICompatClient(config)
        judge = JevJudge(config.support_api_key, load_prompt(SUPPORT_PROMPT))
    except ConfigError as e:
        sys.exit(f"Configuration error: {e}")
    docs: dict[tuple[str, str], AudienceDoc] = {}
    failed = 0
    for case in CASES:
        key = (case.notebook, case.audience)
        if key not in docs:
            docs[key] = generate_doc(
                client, judge, nb.load(case.notebook), AUDIENCE_BY_KEY[case.audience]
            )
        ok = surfaced(case, docs[key])
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {case.name} [{case.audience}]")
        if not ok:
            print(f"      expected: {case.must_surface}")
            print(f"      cell {case.cell}, lines {case.start}-{case.end}: {case.why}")
    print(f"\n{len(CASES) - failed}/{len(CASES)} cases passed")

    notebook = nb.load(GENERALITY)
    for a in AUDIENCES:
        doc = docs.get((GENERALITY, a.key)) or generate_doc(client, judge, notebook, a)
        problems = generality_problems(notebook, doc)
        failed += bool(problems)
        print(f"{'FAIL' if problems else 'PASS'}  generality [{a.key}]")
        for p in problems:
            print(f"      {p}")

    def report(ok: bool, label: str, *details: str) -> None:
        nonlocal failed
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
        if not ok:
            for d in details:
                print(f"      {d}")

    def doc_for(path: str, audience: str) -> AudienceDoc:
        if (path, audience) not in docs:
            docs[(path, audience)] = generate_doc(
                client, judge, nb.load(path), AUDIENCE_BY_KEY[audience]
            )
        return docs[(path, audience)]

    for sc in SECTION_CASES:
        ok = section_cited(sc, doc_for(sc.notebook, sc.audience))
        report(ok, f"{sc.name} [{sc.audience}]", f"expected: {sc.must_surface}")
    for hc in HALT_CASES:
        bad = halt_claims(hc, doc_for(hc.notebook, hc.audience))
        report(
            not bad,
            f"{hc.name} [{hc.audience}]",
            hc.why,
            *[f"claimed: {t}" for t in bad],
        )
    for a in AUDIENCES:
        bad = invented_concerns(doc_for(CLEAN_NOTEBOOK, a.key))
        report(not bad, f"clean notebook [{a.key}]", *[f"invented: {t}" for t in bad])
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
