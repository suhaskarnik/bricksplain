"""Eval Cases: what a good Audience Doc must surface for a fixture Notebook.

This is evaluation data only. Nothing here may leak into prompts or app code.
"""

from dataclasses import dataclass

SAMPLE = "testdata/cash_application_engine.py"


@dataclass(frozen=True)
class EvalCase:
    name: str
    notebook: str
    audience: str
    must_surface: str
    cell: int
    start: int
    end: int
    quote: str
    why: str


CASES = (
    EvalCase(
        "tolerance-reassigned",
        SAMPLE,
        "developer",
        "A tolerance constant is silently reassigned mid-run",
        29,
        361,
        361,
        "TOL = 5.0",
        "Later logic uses a tolerance ten times looser than the one declared up front.",
    ),
    EvalCase(
        "unused-writeoff-cap",
        SAMPLE,
        "developer",
        "A write-off cap constant is declared but never used",
        4,
        34,
        34,
        "MAX_WO = 250.0",
        "The advertised limit on write-offs is not actually enforced.",
    ),
    EvalCase(
        "fifo-by-largest-balance",
        SAMPLE,
        "developer",
        "A step labelled FIFO orders by largest balance, not age",
        26,
        320,
        320,
        "ds = sorted(ds, key=lambda d: -bal[d])",
        "The label promises oldest-first allocation but the code does largest-first.",
    ),
    EvalCase(
        "overwrite-mode-write",
        SAMPLE,
        "agent",
        "A table is written in overwrite mode",
        37,
        459,
        459,
        '.mode("overwrite")',
        "Re-running destroys the table's previous contents.",
    ),
    EvalCase(
        "unseen-included-dependency",
        SAMPLE,
        "developer",
        "An included Notebook is used but its contents are not visible",
        5,
        44,
        44,
        "%run ../shared/fin_utils",
        "Behaviour defined outside the Notebook is unknown and must be reported as such.",
    ),
)
