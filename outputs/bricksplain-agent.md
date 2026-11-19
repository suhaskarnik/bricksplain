# AI coding agent Audience Doc

Notebook: `examples/cash_application_engine.py`

## Purpose

- **Fact** Executes Cash App v3 to process bank receipts, match them against open items and customer records, allocate payments using reference, exact, and FIFO methods, write off small balances, and write results to delta tables. [Cell 1, lines 3-4](/source?path=examples%2Fcash_application_engine.py&cell=1&start=3&end=4) [Cell 37, lines 458-460](/source?path=examples%2Fcash_application_engine.py&cell=37&start=458&end=460)

## Invariants

- **Fact** Receipt amounts must reconcile with allocated lines per receipt within tolerance. [Cell 34, lines 424-425](/source?path=examples%2Fcash_application_engine.py&cell=34&start=424&end=425)

## Risky areas

- **Concern (high)** External CSV inputs loaded from src path could have schema or formatting changes that break parsing. [Cell 6, line 48](/source?path=examples%2Fcash_application_engine.py&cell=6&start=48&end=48)
- **Concern (medium)** Notebook uses shared utilities from an external run statement whose code is not visible. [Cell 5, line 44](/source?path=examples%2Fcash_application_engine.py&cell=5&start=44&end=44)

## How to verify changes

- **Fact** Reconciliation check prints the count of allocation mismatches and halts or reports breaks if any exist. [Cell 34, line 425](/source?path=examples%2Fcash_application_engine.py&cell=34&start=425&end=425)
- **Fact** Company code recon checks if any difference between bank and lines exceeds 0.01. [Cell 41, line 507](/source?path=examples%2Fcash_application_engine.py&cell=41&start=507&end=507)
