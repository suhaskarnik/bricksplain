# Manager Audience Doc

Notebook: `testdata/cash_application_engine.py`

## Summary

- **Fact** This notebook runs the Version 3 cash application process, which replaces the older version 2 notebook for matching cash receipts against open accounts receivable invoices. [Cell 1, lines 3-4](/source?path=testdata%2Fcash_application_engine.py&cell=1&start=3&end=4)

## How it works in business terms

- **Fact** It accepts user inputs for the source file path, run date, company code filter, and whether to perform a dry run. [Cell 3, lines 18-21](/source?path=testdata%2Fcash_application_engine.py&cell=3&start=18&end=21)
- **Fact** It reads raw input files including bank receipts, open items, customers, AR overrides, FX rates, and shared utilities. [Cell 6, line 48](/source?path=testdata%2Fcash_application_engine.py&cell=6&start=48&end=48) [Cell 8, line 67](/source?path=testdata%2Fcash_application_engine.py&cell=8&start=67&end=67) [Cell 9, line 80](/source?path=testdata%2Fcash_application_engine.py&cell=9&start=80&end=80) [Cell 13, line 131](/source?path=testdata%2Fcash_application_engine.py&cell=13&start=131&end=131) [Cell 16, line 169](/source?path=testdata%2Fcash_application_engine.py&cell=16&start=169&end=169)
- **Fact** Receipts are matched to customer accounts using explicit payment references, customer name matching against aliases, or manual overrides. [Cell 14, lines 137-141](/source?path=testdata%2Fcash_application_engine.py&cell=14&start=137&end=141)
- **Fact** Unmatched receipts or unapplied funds are allocated using automated strategies such as reference matching, exact amount matching, FIFO allocation, and small balance write-offs. [Cell 30, lines 372-377](/source?path=testdata%2Fcash_application_engine.py&cell=30&start=372&end=377)

## Outcomes and impact

- **Fact** It writes allocation lines to the table 'fin_cash.alloc_lines', updates open items status in 'fin_cash.open_items_after', and appends records to the AR aging snapshot table 'fin_cash.ar_aging_snap' unless run in dry-run mode. [Cell 4, line 38](/source?path=testdata%2Fcash_application_engine.py&cell=4&start=38&end=38) [Cell 37, line 459](/source?path=testdata%2Fcash_application_engine.py&cell=37&start=459&end=459) [Cell 38, line 474](/source?path=testdata%2Fcash_application_engine.py&cell=38&start=474&end=474) [Cell 39, line 486](/source?path=testdata%2Fcash_application_engine.py&cell=39&start=486&end=486)
- **Fact** It sends email or notification alerts to the AR team and logs run metrics. [Cell 43, line 532](/source?path=testdata%2Fcash_application_engine.py&cell=43&start=532&end=532) [Cell 44, line 536](/source?path=testdata%2Fcash_application_engine.py&cell=44&start=536&end=536)

## Potential issues

- **Concern (medium)** The notebook relies on an external shared utility script '../shared/fin_utils' whose contents and behavior are entirely unknown from the notebook text. [Cell 5, line 44](/source?path=testdata%2Fcash_application_engine.py&cell=5&start=44&end=44)
- **Concern (low)** Fuzzy matching logic for customer names is commented out and disabled due to producing too many false positives on specific regional data. [Cell 20, line 230](/source?path=testdata%2Fcash_application_engine.py&cell=20&start=230&end=230)
