# Developer Audience Doc

Notebook: `testdata/cash_application_engine.py`

## Notebook map by Cell

- **Fact** Cell 1 defines the notebook title and declares it as version 3 cash application logic replacing version 2. [Cell 1, line 3](/source?path=testdata%2Fcash_application_engine.py&cell=1&start=3&end=3)
- **Fact** Cell 2 imports PySpark functions, window functions, types, pandas, numpy, and standard utility libraries. [Cell 2, line 8](/source?path=testdata%2Fcash_application_engine.py&cell=2&start=8&end=8)
- **Fact** Cell 3 sets up input widgets for source path, run date, company, and dry run flag, retrieves their values, and defaults run date to today if empty. [Cell 3, line 18](/source?path=testdata%2Fcash_application_engine.py&cell=3&start=18&end=18)
- **Fact** Cell 4 defines global tolerances, maximum write-off amount, exclusion lists, target table, timer start, and sets Spark shuffle partitions to 8. [Cell 4, line 33](/source?path=testdata%2Fcash_application_engine.py&cell=4&start=33&end=33)
- **Fact** Cell 5 runs the shared financial utilities notebook. [Cell 5, line 44](/source?path=testdata%2Fcash_application_engine.py&cell=5&start=44&end=44)
- **Fact** Cell 6 reads bank receipts CSV data, cleans amount commas and types, parses valuation dates, and normalizes currency codes. [Cell 6, line 48](/source?path=testdata%2Fcash_application_engine.py&cell=6&start=48&end=48)
- **Fact** Cell 7 filters bank receipts for positive amounts, valuation dates on or before run date, maps bank accounts to companies, and applies company filters. [Cell 7, line 57](/source?path=testdata%2Fcash_application_engine.py&cell=7&start=57&end=57)
- **Fact** Cell 8 reads open items CSV data, casts amounts and dates, filters for positive open amounts, excludes specific customers, applies company filters, and parses dispute flags. [Cell 8, line 67](/source?path=testdata%2Fcash_application_engine.py&cell=8&start=67&end=67)
- **Fact** Cell 9 reads customers CSV data, creates a pool column using parent number or customer number, and caches the dataframe. [Cell 9, line 80](/source?path=testdata%2Fcash_application_engine.py&cell=9&start=80&end=80)
- **Fact** Cell 10 defines string normalization functions and UDFs as well as regex reference extraction functions and UDFs. [Cell 10, line 87](/source?path=testdata%2Fcash_application_engine.py&cell=10&start=87&end=87)
- **Fact** Cell 11 explodes customer aliases, normalizes them, and unions them with normalized customer names. [Cell 11, line 108](/source?path=testdata%2Fcash_application_engine.py&cell=11&start=108&end=108)
- **Fact** Cell 12 extracts payment references and normalized payer names on receipts, caches receipts, and displays a sample. [Cell 12, line 117](/source?path=testdata%2Fcash_application_engine.py&cell=12&start=117&end=117)
- **Fact** Cell 13 builds reference-based and name-based customer matching lookup tables and reads AR overrides. [Cell 13, line 124](/source?path=testdata%2Fcash_application_engine.py&cell=13&start=124&end=124)
- **Fact** Cell 14 joins overrides, reference matches, and name matches to determine final receipt customer identification source and pool. [Cell 14, line 136](/source?path=testdata%2Fcash_application_engine.py&cell=14&start=136&end=136)
- **Fact** Cell 15 contains commented-out legacy v2 exact and FIFO matching logic. [Cell 15, line 148](/source?path=testdata%2Fcash_application_engine.py&cell=15&start=148&end=148)
- **Fact** Cell 16 reads FX rates, casts types, and computes the latest FX rate per currency. [Cell 16, line 169](/source?path=testdata%2Fcash_application_engine.py&cell=16&start=169&end=169)
- **Fact** Cell 17 computes valuation date-specific FX rates for receipts. [Cell 17, line 178](/source?path=testdata%2Fcash_application_engine.py&cell=17&start=178&end=178)
- **Fact** Cell 18 joins FX rates to receipts and open items to calculate USD amounts. [Cell 18, line 185](/source?path=testdata%2Fcash_application_engine.py&cell=18&start=185&end=185)
- **Fact** Cell 19 runs data quality checks and prints warning counts. [Cell 19, line 196](/source?path=testdata%2Fcash_application_engine.py&cell=19&start=196&end=196)
- **Fact** Cell 20 contains commented-out fuzzy matching logic that was parked due to false positives. [Cell 20, line 209](/source?path=testdata%2Fcash_application_engine.py&cell=20&start=209&end=209)
- **Fact** Cell 21 displays aggregated receipt counts and amounts by company and currency. [Cell 21, line 234](/source?path=testdata%2Fcash_application_engine.py&cell=21&start=234&end=234)
- **Fact** Cell 22 displays aggregated open item counts and open amounts by company code and document currency. [Cell 22, line 238](/source?path=testdata%2Fcash_application_engine.py&cell=22&start=238&end=238)
- **Fact** Cell 23 defines aging-based allocation and aging report pivot table helper functions using pandas. [Cell 23, line 242](/source?path=testdata%2Fcash_application_engine.py&cell=23&start=242&end=242)
- **Fact** Cell 24 converts receipt and open item spark dataframes into pandas dataframes. [Cell 24, line 271](/source?path=testdata%2Fcash_application_engine.py&cell=24&start=271&end=271)
- **Fact** Cell 25 initializes dictionary balances, metadata, and pool groupings for open items. [Cell 25, line 277](/source?path=testdata%2Fcash_application_engine.py&cell=25&start=277&end=277)
- **Fact** Cell 26 defines Python core application functions for reference matching, exact matching, FIFO matching, write-offs, and balance checking. [Cell 26, line 286](/source?path=testdata%2Fcash_application_engine.py&cell=26&start=286&end=286)
- **Fact** Cell 27 filters, prints, and displays receipts lacking a resolved customer. [Cell 27, line 345](/source?path=testdata%2Fcash_application_engine.py&cell=27&start=345&end=345)
- **Fact** Cell 28 computes top customer pools by USD amount for assigned receipts. [Cell 28, line 353](/source?path=testdata%2Fcash_application_engine.py&cell=28&start=353&end=353)
- **Fact** Cell 29 prints total inward receipt and open item USD amounts, changes tolerance to 5.0, and prints count of receipts with references. [Cell 29, line 358](/source?path=testdata%2Fcash_application_engine.py&cell=29&start=358&end=358)
- **Fact** Cell 30 executes the main cash application loop over sorted receipts, applying reference, exact, FIFO, write-off, unapplied, and suspense logic. [Cell 30, line 366](/source?path=testdata%2Fcash_application_engine.py&cell=30&start=366&end=366)
- **Fact** Cell 31 builds the allocation lines pandas dataframe, merges receipt and open item details, and calculates receipt currency and document currency amounts. [Cell 31, line 387](/source?path=testdata%2Fcash_application_engine.py&cell=31&start=387&end=387)
- **Fact** Cell 32 reconciles rounding differences by adjusting the last non-write-off line amount per receipt. [Cell 32, line 397](/source?path=testdata%2Fcash_application_engine.py&cell=32&start=397&end=397)
- **Fact** Cell 33 maps GL accounts for each allocation line based on company and line type and assigns the run date. [Cell 33, line 410](/source?path=testdata%2Fcash_application_engine.py&cell=33&start=410&end=410)
- **Fact** Cell 34 performs reconciliation checks comparing allocated totals against receipt amounts and prints summary statistics. [Cell 34, line 421](/source?path=testdata%2Fcash_application_engine.py&cell=34&start=421&end=421)
- **Fact** Cell 35 computes identification source hit rates, automation rates, and fully applied receipt rates. [Cell 35, line 433](/source?path=testdata%2Fcash_application_engine.py&cell=35&start=433&end=433)
- **Fact** Cell 36 defines the schema for allocation lines, fills missing customer numbers, and creates a Spark dataframe with load timestamps. [Cell 36, line 443](/source?path=testdata%2Fcash_application_engine.py&cell=36&start=443&end=443)
- **Fact** Cell 37 writes allocation lines to the target Delta table if dry run is disabled, or prints a dry run message otherwise. [Cell 37, line 458](/source?path=testdata%2Fcash_application_engine.py&cell=37&start=458&end=458)
- **Fact** Cell 38 calculates open item post-application balances and statuses, and writes them to open_items_after if not a dry run. [Cell 38, line 466](/source?path=testdata%2Fcash_application_engine.py&cell=38&start=466&end=466)
- **Fact** Cell 39 computes AR aging snapshots from remaining open items and appends them to ar_aging_snap if not a dry run. [Cell 39, line 478](/source?path=testdata%2Fcash_application_engine.py&cell=39&start=478&end=478)
- **Fact** Cell 41 performs company-level bank-to-line reconciliation and checks for breaks. [Cell 41, line 501](/source?path=testdata%2Fcash_application_engine.py&cell=41&start=501&end=501)
- **Fact** Cell 42 groups customer application amounts by line type and sorts by unapplied amounts. [Cell 42, line 512](/source?path=testdata%2Fcash_application_engine.py&cell=42&start=512&end=512)
- **Fact** Cell 43 compiles application summary statistics and HTML notifications and sends them via notify_ar. [Cell 43, line 522](/source?path=testdata%2Fcash_application_engine.py&cell=43&start=522&end=522)
- **Fact** Cell 44 logs the notebook run metrics using log_run. [Cell 44, line 536](/source?path=testdata%2Fcash_application_engine.py&cell=44&start=536&end=536)
- **Fact** Cell 45 contains a commented-out SQL query querying allocation line types and sums from the target table. [Cell 45, line 541](/source?path=testdata%2Fcash_application_engine.py&cell=45&start=541&end=541)
- **Fact** Cell 46 contains commented-out SQL queries checking write-offs and grouping allocation lines by company and type. [Cell 46, line 546](/source?path=testdata%2Fcash_application_engine.py&cell=46&start=546&end=546)
- **Fact** Cell 47 exits the notebook, returning a JSON string with run status, receipt count, line count, and bad reconciliation count. [Cell 47, line 551](/source?path=testdata%2Fcash_application_engine.py&cell=47&start=551&end=551)

## Data flow

- **Fact** Reads raw CSV files for bank receipts, open items, customers, AR overrides, and FX rates from the source path. [Cell 6, line 48](/source?path=testdata%2Fcash_application_engine.py&cell=6&start=48&end=48) [Cell 8, line 67](/source?path=testdata%2Fcash_application_engine.py&cell=8&start=67&end=67) [Cell 9, line 80](/source?path=testdata%2Fcash_application_engine.py&cell=9&start=80&end=80) [Cell 13, line 131](/source?path=testdata%2Fcash_application_engine.py&cell=13&start=131&end=131) [Cell 16, line 169](/source?path=testdata%2Fcash_application_engine.py&cell=16&start=169&end=169)
- **Fact** Cleans, filters, and transforms receipts, open items, customers, and FX rates, identifying customer mappings via references, normalized names, and overrides. [Cell 7, line 57](/source?path=testdata%2Fcash_application_engine.py&cell=7&start=57&end=57) [Cell 14, line 136](/source?path=testdata%2Fcash_application_engine.py&cell=14&start=136&end=136)
- **Fact** Converts Spark dataframes to pandas dataframes and executes sequential cash application logic (REF, EXACT, FIFO, WO, UNAPP, SUSP). [Cell 24, line 271](/source?path=testdata%2Fcash_application_engine.py&cell=24&start=271&end=271) [Cell 30, lines 368-377](/source?path=testdata%2Fcash_application_engine.py&cell=30&start=368&end=377)
- **Fact** Builds final allocation lines dataframe, reconciles amounts, maps GL accounts, and writes outputs to Delta tables fin_cash.alloc_lines, fin_cash.open_items_after, and fin_cash.ar_aging_snap. [Cell 37, line 459](/source?path=testdata%2Fcash_application_engine.py&cell=37&start=459&end=459) [Cell 38, line 474](/source?path=testdata%2Fcash_application_engine.py&cell=38&start=474&end=474) [Cell 39, line 486](/source?path=testdata%2Fcash_application_engine.py&cell=39&start=486&end=486)

## Business rules

- **Fact** Bank receipts and open items with non-positive amounts (<= 0) are filtered out. [Cell 7, line 57](/source?path=testdata%2Fcash_application_engine.py&cell=7&start=57&end=57) [Cell 8, line 71](/source?path=testdata%2Fcash_application_engine.py&cell=8&start=71&end=71)
- **Fact** Bank receipts with valuation dates after run_dt are excluded. [Cell 7, line 57](/source?path=testdata%2Fcash_application_engine.py&cell=7&start=57&end=57)
- **Fact** Bank accounts not present in the bank account mapping dictionary (bk) are filtered out. [Cell 7, line 60](/source?path=testdata%2Fcash_application_engine.py&cell=7&start=60&end=60)
- **Fact** Open items belonging to excluded customer numbers ('C10077', 'C10412') are filtered out. [Cell 4, line 37](/source?path=testdata%2Fcash_application_engine.py&cell=4&start=37&end=37) [Cell 8, line 72](/source?path=testdata%2Fcash_application_engine.py&cell=8&start=72&end=72)
- **Fact** Customer identification priority order is Overrides (OV), References (REF), then Name matching (NM). [Cell 14, lines 137-141](/source?path=testdata%2Fcash_application_engine.py&cell=14&start=137&end=141)
- **Fact** Receipts are processed in ascending order of valuation date and receipt ID. [Cell 30, line 367](/source?path=testdata%2Fcash_application_engine.py&cell=30&start=367&end=367)
- **Fact** Reference matching (REF) allocates receipt remainder across explicit remittance document references if the open balance is positive. [Cell 26, lines 296-299](/source?path=testdata%2Fcash_application_engine.py&cell=26&start=296&end=299)
- **Fact** Exact matching (EXACT) applies if the receipt remainder is within EX_TOL (0.01) of a single non-disputed open item in the pool, sorted by document date. [Cell 4, line 35](/source?path=testdata%2Fcash_application_engine.py&cell=4&start=35&end=35) [Cell 26, lines 305-310](/source?path=testdata%2Fcash_application_engine.py&cell=26&start=305&end=310)
- **Fact** FIFO matching applies remaining amounts greater than TOL (5.0) to open items sorted descending by open balance. [Cell 29, line 361](/source?path=testdata%2Fcash_application_engine.py&cell=29&start=361&end=361) [Cell 30, line 375](/source?path=testdata%2Fcash_application_engine.py&cell=30&start=375&end=375) [Cell 26, lines 320-324](/source?path=testdata%2Fcash_application_engine.py&cell=26&start=320&end=324)
- **Fact** Write-offs (WO) apply when a matched open item has a remaining balance strictly between 0.005 and TOL (5.0). [Cell 4, line 33](/source?path=testdata%2Fcash_application_engine.py&cell=4&start=33&end=33) [Cell 29, line 361](/source?path=testdata%2Fcash_application_engine.py&cell=29&start=361&end=361) [Cell 26, lines 333-334](/source?path=testdata%2Fcash_application_engine.py&cell=26&start=333&end=334)
- **Fact** Unapplied (UNAPP) records are created when remaining receipt amounts exceed 0.005 and customer is not null, while suspense (SUSP) records are created when customer is null. [Cell 30, lines 378-382](/source?path=testdata%2Fcash_application_engine.py&cell=30&start=378&end=382)

## Inferred Glossary

- **Fact** bk: bank account to company mapping dictionary, defined at line 36 [Cell 4, line 36](/source?path=testdata%2Fcash_application_engine.py&cell=4&start=36&end=36)
- **Fact** EXCL: list of excluded customer numbers, defined at line 37 [Cell 4, line 37](/source?path=testdata%2Fcash_application_engine.py&cell=4&start=37&end=37)
- **Fact** tgt: target Delta table name for allocation lines, defined at line 38 [Cell 4, line 38](/source?path=testdata%2Fcash_application_engine.py&cell=4&start=38&end=38)
- **Fact** nrm: string normalization helper function, defined at line 87 [Cell 10, line 87](/source?path=testdata%2Fcash_application_engine.py&cell=10&start=87&end=87)
- **Fact** get_refs: regex reference extractor function, defined at line 99 [Cell 10, line 99](/source?path=testdata%2Fcash_application_engine.py&cell=10&start=99&end=99)
- **Fact** alloc_by_aging: aging-based allocation pandas function, defined at line 242 [Cell 23, line 242](/source?path=testdata%2Fcash_application_engine.py&cell=23&start=242&end=242)
- **Fact** aging_rpt: aging report pivot table generator function, defined at line 263 [Cell 23, line 263](/source?path=testdata%2Fcash_application_engine.py&cell=23&start=263&end=263)

## Gotchas and how to run

- **Concern (medium)** Global tolerance TOL is redefined in Cell 29 from 0.5 to 5.0, which alters FIFO vs unapplied behavior compared to earlier cells. [Cell 4, line 33](/source?path=testdata%2Fcash_application_engine.py&cell=4&start=33&end=33) [Cell 29, line 361](/source?path=testdata%2Fcash_application_engine.py&cell=29&start=361&end=361)
- **Concern (high)** Data writes to fin_cash.alloc_lines and fin_cash.open_items_after use mode overwrite when dry == 'N', replacing existing table contents. [Cell 37, line 459](/source?path=testdata%2Fcash_application_engine.py&cell=37&start=459&end=459) [Cell 38, line 474](/source?path=testdata%2Fcash_application_engine.py&cell=38&start=474&end=474)
