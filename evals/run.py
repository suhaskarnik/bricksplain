"""Live evaluation: `just eval`. Calls the real configured provider."""

import os
import sys
from pathlib import Path

from bricksplain import notebook as nb
from bricksplain.audience_doc import AUDIENCE_BY_KEY, AudienceDoc, generate_doc
from bricksplain.config import ConfigError, load_config
from bricksplain.llm import OpenAICompatClient

from .cases import CASES, EvalCase


def surfaced(case: EvalCase, doc: AudienceDoc) -> bool:
    """True when a Claim cites lines overlapping the case's expected Line Range."""
    return any(
        c.cell == case.cell and c.start <= case.end and c.end >= case.start
        for s in doc.sections
        for item in s.items
        for c in item.citations
    )


def main() -> None:
    try:
        client = OpenAICompatClient(load_config(Path.cwd(), os.environ))
    except ConfigError as e:
        sys.exit(f"Configuration error: {e}")
    docs: dict[tuple[str, str], AudienceDoc] = {}
    failed = 0
    for case in CASES:
        key = (case.notebook, case.audience)
        if key not in docs:
            docs[key] = generate_doc(
                client, nb.load(case.notebook), AUDIENCE_BY_KEY[case.audience]
            )
        ok = surfaced(case, docs[key])
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {case.name} [{case.audience}]")
        if not ok:
            print(f"      expected: {case.must_surface}")
            print(f"      cell {case.cell}, lines {case.start}-{case.end}: {case.why}")
    print(f"\n{len(CASES) - failed}/{len(CASES)} cases passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
