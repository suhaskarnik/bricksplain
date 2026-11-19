"""Eval Cases: what a good Audience Doc must surface for a fixture Notebook.

This is evaluation data only. Nothing here may leak into prompts or app code.
"""

from dataclasses import dataclass

SAMPLE = "examples/cash_application_engine.py"
GENERALITY = "evals/fixtures/sensor_feature_pipeline.py"
CLEAN = "evals/fixtures/clean_temperature_report.py"

# Vocabulary of the sample Notebook's domain. Docs generated for the generality
# Notebook must contain none of it, and neither may that Notebook itself.
FORBIDDEN_TERMS = (
    "receipt",
    "invoice",
    "cash",
    "remittance",
    "write-off",
    "writeoff",
    "allocation",
    "ledger",
    "bank",
    "payment",
    "fifo",
    "debtor",
    "open item",
)


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
    # Other places that satisfy the case equally well: (cell, start, end, quote).
    also: tuple[tuple[int, int, int, str], ...] = ()
    # True when the matching Claim must be a Concern, not just any Claim.
    concern_only: bool = False

    def locations(self) -> list[tuple[int, int, int, str]]:
        return [(self.cell, self.start, self.end, self.quote), *self.also]


@dataclass(frozen=True)
class SectionCase:
    """A section of an Audience Doc must hold at least one cited Claim."""

    name: str
    notebook: str
    audience: str
    section: str
    must_surface: str


@dataclass(frozen=True)
class HaltCase:
    """No Claim citing this print-only check may say it stops the run."""

    name: str
    notebook: str
    audience: str
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
    EvalCase(
        "manager-sees-a-risk",
        SAMPLE,
        "manager",
        "The manager doc names the reassigned tolerance, an overwrite write or the unused cap",
        29,
        361,
        361,
        "TOL = 5.0",
        "A manager must hear about a setting that changes mid-run, data that is overwritten, "
        "or a limit that is not enforced.",
        also=(
            (37, 459, 459, '.mode("overwrite")'),
            (38, 474, 474, '.mode("overwrite")'),
            (4, 34, 34, "MAX_WO = 250.0"),
        ),
    ),
    EvalCase(
        "fifo-mismatch-is-a-concern",
        SAMPLE,
        "developer",
        "The name-versus-ordering mismatch is raised as a Concern",
        26,
        320,
        320,
        "ds = sorted(ds, key=lambda d: -bal[d])",
        "A label that promises oldest-first but sorts by balance must be flagged as a risk.",
        concern_only=True,
    ),
    EvalCase(
        "label-used-as-feature",
        GENERALITY,
        "developer",
        "The prediction target is included in the model's input features",
        2,
        13,
        13,
        "LABEL]",
        "The model sees the answer, so its score is meaningless.",
    ),
    EvalCase(
        "scaler-fit-before-split",
        GENERALITY,
        "developer",
        "Scaling is fitted on all rows before the train/test split",
        5,
        33,
        33,
        "StandardScaler().fit(pdf[FEATURES])",
        "Test-set statistics leak into training.",
    ),
    EvalCase(
        "seed-parameter-ignored",
        GENERALITY,
        "developer",
        "A seed parameter is read but the split is not seeded",
        5,
        35,
        35,
        "train_test_split(pdf, test_size=0.2)",
        "Runs are not reproducible despite the seed parameter.",
    ),
    EvalCase(
        "feature-table-overwrite",
        GENERALITY,
        "agent",
        "The feature table is written in overwrite mode",
        7,
        46,
        46,
        '.mode("overwrite")',
        "Re-running replaces the table's previous contents.",
    ),
    EvalCase(
        "unseen-helper-notebook",
        GENERALITY,
        "developer",
        "An included Notebook is used but its contents are not visible",
        3,
        17,
        17,
        "%run ../shared/ml_helpers",
        "Behaviour defined outside the Notebook is unknown and must be reported as such.",
    ),
)

SECTION_CASES = (
    SectionCase(
        "agent-has-invariant",
        SAMPLE,
        "agent",
        "invariants",
        "At least one cited invariant to preserve",
    ),
    SectionCase(
        "agent-has-runnable-check",
        SAMPLE,
        "agent",
        "verify",
        "At least one cited, runnable check",
    ),
)

HALT_CASES = (
    HaltCase(
        "print-only-duplicate-check-does-not-halt",
        SAMPLE,
        "agent",
        19,
        205,
        205,
        'print("WARNING dup receipts!!")',
        "The duplicate check only prints a warning; the run carries on.",
    ),
    HaltCase(
        "print-only-recon-check-does-not-halt",
        SAMPLE,
        "agent",
        34,
        425,
        425,
        'print("recon mismatches:", len(bad))',
        "The reconciliation check only prints a count; the run carries on.",
    ),
    HaltCase(
        "print-only-company-recon-does-not-halt",
        SAMPLE,
        "agent",
        41,
        508,
        508,
        'print("CO RECON BREAK")',
        "The company-level reconciliation break only prints; the run carries on.",
    ),
)

# Planted risks in the generality Notebook, mirroring the sample's risk classes.
GENERALITY_RISKS = (
    EvalCase(
        "unused-null-cap",
        GENERALITY,
        "developer",
        "A null-fraction cap constant is declared but never used",
        8,
        50,
        50,
        "MAX_NULL_FRAC = 0.05",
        "The advertised cap is not enforced; the check uses a different literal.",
    ),
    EvalCase(
        "staleness-reassigned",
        GENERALITY,
        "developer",
        "A staleness constant is reassigned after first use",
        11,
        67,
        67,
        "STALE_H = 48",
        "Later logic uses a value eight times looser than the one declared up front.",
    ),
)

CASES += GENERALITY_RISKS

HALT_CASES += (
    HaltCase(
        "print-only-null-check-does-not-halt",
        GENERALITY,
        "agent",
        9,
        58,
        58,
        'print("WARNING too many nulls")',
        "The null check only prints a warning; the run carries on.",
    ),
)

# A Notebook with no risks: no Concern may be invented for any Audience.
CLEAN_NOTEBOOK = CLEAN

# Wording that says a check stops the run. A text that also negates is not a claim.
HALT_WORDS = ("halt", "stop", "abort", "fail the run", "raise", "block", "fail fast")
NEGATIONS = ("not", "never", "n't", "no ", "without", "only print", "merely")
