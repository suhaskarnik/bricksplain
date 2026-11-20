# Bricksplain

You have a Databricks **Notebook** that works but that nobody understands. Bricksplain explains it to three **Audiences** (a non-technical manager, a new developer, an AI coding agent) and proves each statement by linking it to the Notebook's own lines. Terms such as Claim, Citation and Verified Citation are defined in [GLOSSARY.md](GLOSSARY.md) and used here without redefining them.

It is a localhost web app. Point it at a Notebook path, press Generate, and get three Audience Docs in tabs, each downloadable as Markdown. It never executes the Notebook and knows nothing about any business domain.

## Run it

Requires Python 3.12 and [`uv`](https://docs.astral.sh/uv/). `just` is optional.

```
## Run with Gemini-3.5 Flash (default)
uv run bricksplain        # syncs dependencies if needed, serves http://127.0.0.1:8000

## OR

just serve
```

The input page is prefilled with the committed sample Notebook, `examples/cash_application_engine.py` (data in `examples/sample_data/`), so Generate works straight after cloning and every citation link opens real lines.

| Recipe | What it does |
|---|---|
| `just serve` | Same as `uv run bricksplain`: run the app, bound to 127.0.0.1 only |
| `just serve-debug` | Same, but logs go to `.logs/` inside the project and LLM responses are logged, so an assistant without access to your home directory can read them |
| `just test` | Offline test suite: no network, no API keys |
| `just eval` | Live evaluation against the configured provider (not part of `just test`) |
| `just lint` / `just fmt` | Ruff check / format |

Note: the `just` recipes are optional shortcuts; it can be installed from [GitHub](https://github.com/casey/just)

## Design decisions

### 1. Every Claim carries a Verified Citation

The LLM returns structured JSON: sections of items typed Fact, Concern or Context. Facts and Concerns must cite `(cell, start line, end line, verbatim quote)`. Before anything is shown, each Citation is checked: the Cell exists, the lines lie inside it, and the quote appears in those lines (whitespace-normalised, ignoring the `# MAGIC` prefix Databricks puts on markdown and SQL lines). A Claim that fails triggers one retry of that doc with the failures fed back; Claims still failing are dropped, and the count is shown and logged. Citations render as links that open the Source Viewer at the Line Range.

Rejected:
- *Trust the LLM's prose.* Nothing lets a reader check it.
- *Fuzzy or semantic re-anchoring of bad citations.* It would quietly repair evidence instead of rejecting it, defeating the point.
- *Free-text output rendered as is.* Prose is never taken from the LLM unstructured, so there is nowhere for an uncited statement to hide. Generic framing is allowed only as Context, visibly marked and uncited.

This is the central bet: it turns "trust the LLM" into "check the evidence in one click". The verifier is deliberately strict, so prompts ask for short quotes (long multi-line quotes get miscopied and dropped).

### 2. Caching is cost control

Each Audience Doc costs one LLM call, and the free tiers are rate-limited. The generated, Citation-verified draft is cached on disk, keyed by Notebook content, model string, prompt text and section skeleton, so editing a prompt invalidates old results. The Support Check (decision 9) is never cached: it runs again on every load, cached or not, so a change to Jev's question, threshold or inputs takes effect at once and the draft is not frozen with old verdicts. A cached draft is not regenerated when the check drops Claims; Regenerate is the way to try again, because every retry spends LLM quota.

Rejected: *no cache* (burns quota on every click); *keying on file path or mtime* (stale after edits, misses after renames); *a database* (a directory of JSON files is enough for one user).

### 3. Offline tests for behaviour, live evals for model quality

The default suite is fully offline. Its main seam is the HTTP app with a fake LLM client, so parsing, verification, rendering, retry, caching and failure isolation are tested through what a user sees. Configuration resolution is tested directly because its precedence rules are hard to reach through HTTP.

Whether a real model *notices* real problems cannot be tested offline, so `just eval` calls the real provider. **Eval Cases** are code (`evals/cases.py`): a name, the fixture Notebook, the Audience, what must be surfaced, the expected Cell and Line Range with a quote, and why it matters. A case passes when some Claim in that Audience's doc cites lines overlapping the expected range (or any listed alternative range; some cases require the Claim to be a Concern). Further cases require a cited invariant and a cited runnable check in the agent doc, fail if a Claim says a print-only check halts the run, and require that a clean Notebook gets no invented Concerns. Output is PASS or FAIL per case.

A default-suite test checks that every case's expected Citation points at real lines in its fixture, so cases cannot rot silently when a fixture changes.

Rejected: *live calls in the default suite* (slow, flaky, needs keys, costs money); *judging answers with another LLM* (adds a second source of error to a check that line overlap does deterministically).

### 4. A generality fixture guards against overfitting

The sample Notebook (a cash-application engine, with planted quirks such as a tolerance constant reassigned mid-run, an unused cap constant, a "FIFO" step that orders by largest balance, an overwrite-mode write and an unseen `%run`) is easy to overfit to. `evals/fixtures/sensor_feature_pipeline.py` is a hand-written, unrelated ML feature pipeline with its own planted quirks (the target used as a feature, scaling fitted before the split, an ignored seed, an overwrite-mode write, an unseen `%run`, an unused cap constant, a constant reassigned after first use and a check that only prints). `evals/fixtures/clean_temperature_report.py` has no risks at all and guards the opposite failure: invented Concerns. `just eval` checks, for every Audience, that the docs for it contain none of the first domain's vocabulary and that every Citation verifies. An offline test checks the fixture itself contains none of that vocabulary.

### 5. The prompts are domain-agnostic

Prompts (`src/bricksplain/prompts/`, one file per Audience) fix only the skeleton and the rules: never guess, behaviour defined outside the Notebook is reported as unknown and raised as a Concern, commented-out code is described only as disabled, a name that disagrees with its code is a Concern. A shared, domain-free risk checklist (`prompts/checklist.txt`) is added to every Audience prompt: names that disagree with behaviour, constants never used or reassigned after first use, overwrite writes, checks that print but do not stop the run, and behaviour defined outside the Notebook. It may report no findings for a clean Notebook. They contain no domain words, and neither does application code; Eval Case vocabulary lives only in `evals/`. A Notebook's own terminology reaches the reader only through the Inferred Glossary, which the LLM derives from that Notebook.

Rejected: *domain-tuned prompts* (better on one Notebook, wrong on the next, and impossible to tell apart from overfitting).

### 6. Model in the working directory, keys shared centrally

`BRICKSPLAIN_MODEL=<provider>/<model id>` is read only from the working directory's `.env`, never from the process environment or the central file, because the model is a per-app choice. API keys are shared across the author's apps, so each key resolves from the `.env` under the directory named by `LLM_PROVIDERS` first, then the working directory's `.env`. Only the selected provider's key is required, plus `OPENROUTER_API_KEY` when the optional Support Check (decision 9) is switched on, and errors name the missing key without printing values.

Rejected: *one config file for everything* (would duplicate keys per app or force one model on all of them); *the environment for the model* (a stray exported variable silently changes which model is used).

### 7. Logging with redaction

One file per app start, `log_YYYYMMDD_hhmmss.log`, in `BRICKSPLAIN_LOG_PATH`, else `$XDG_STATE_HOME/bricksplain`, else `~/.local/state/bricksplain`. Level is INFO unless `LOG_LEVEL` says otherwise. It records LLM failures, rate limits with retry timing, retries, citation failures and dropped-Claim counts, and request metadata (provider, model, latency, tokens, status).

Set `BRICKSPLAIN_REASONING_EFFORT` (`none`, `minimal`, `low`, `medium`, `high`) in the working directory `.env` to cap hidden reasoning tokens on OpenRouter models; it is ignored for other providers and unset by default. The request log line includes `reasoning_tokens` when the provider reports it.

Prompts and Notebook content are never logged. A formatter masks the configured key values and anything key-shaped, in the final formatted text, so tracebacks are covered too. LLM response bodies, and the text and quotes of failing Claims, are logged only when `BRICKSPLAIN_LOG_LLM_RESPONSES=1` (which `just serve-debug` sets).

Rejected: *logging prompts for debuggability* (private code ends up in log files); *redacting by call site* (one forgotten call leaks a key).

### 8. Secure By Design

Two sets of LLMs were involved in this solution: Claude built it using Claude Code, and Gemini (or Groq/OpenRouter models) is used to generate the actual documents. Neither of these sets can see the secret, which in this case is the LLM API key. This is structurally enforced, not via prompt. The secret is stored in a different directory outside this project, and therefore not visible to Claude Code. This secret is also not sent to Gemini/Groq/OpenRouter. 

There is still one shortcut that was taken though, see the next steps for more details. 

### 9. Support checking and Citation granularity

**Status: implemented but off by default; see Known issues.** Set `BRICKSPLAIN_SUPPORT_CHECK=1` in the working directory's `.env` (and provide `OPENROUTER_API_KEY`) to switch it on. Without it, every Verified Citation is shown and no decision-model call is made.

Verification proves a quote exists, not that the Claim follows from it. After generation and verification, each Claim is put to a decision model (Jev, `jev-1.13`, which exists only on OpenRouter) as a Support Check: the full text of the cited Line Range(s), not just the quote, each headed `Cell N, lines a-b:` so a Claim that names its Cell can be matched, is the `state`, the Claim is the question, and the `noul` answer is the probability that the quote establishes it. A score below `SUPPORT_THRESHOLD` in `decision.py` (currently 0.5; every score is logged at INFO to tune it against the Eval Cases) makes the Claim unsupported, and an unsupported Claim is dropped and counted, so every shown Claim is a Supported Citation. Only Citation failures (which come with a precise reason) trigger the retry of decision 1; Jev gives a score and no reason, so retrying on its verdicts spent a full LLM call for a worse rewrite, and Regenerate is the way to try again. The decision model is independent of `BRICKSPLAIN_MODEL`, so `OPENROUTER_API_KEY` is required at startup even when another provider writes the docs. The calls run concurrently. Verdicts are not cached (decision 2): only the draft is, so the check is repeated on every load, which costs a few cheap calls and no LLM tokens.

Citations must also be fine enough to check. The schema stays `(cell, start, end, quote)`, but a Claim marked as describing a Cell must cite that Cell's full range, a one-line citation is accepted only for a one-line assertion, and a Claim spanning Cells carries one Citation per Cell. Each doc also reports its Coverage (the share of Cells and lines cited, with uncited Cells linked); it is informational and never feeds back into generation, so it cannot cause padding.

Rejected: *the same LLM judging its own Claims with a batched yes/no prompt* (the first version; it costs one call per doc but the writer and the judge share blind spots, and the answer is a free-text verdict rather than a calibrated score); *Coverage as a pass/fail threshold* (rewards padding with irrelevant citations).

The trade-offs: the check costs one small paid call per Claim instead of one per doc; the decision model returns a score and no reason, so a dropped Claim cannot be repaired by a targeted retry; and it is a second source of error, since it can wrongly reject a good Claim. Dropped counts are shown. A Jev failure fails that Audience Doc rather than showing it unchecked. A cached draft whose Claims are dropped on a later load is not retried automatically (see decision 2); press Regenerate.

## Layout

- `src/bricksplain/`: the app (`notebook.py` parsing, `audience_doc.py` schema, verification and Markdown, `jobs.py` concurrent generation, `cache.py`, `llm.py`, `config.py`, `logging_setup.py`, `app.py`)
- `evals/`: Eval Cases, the live runner and the generality fixture
- `tests/`: the offline suite
- `examples/`: the sample Notebook and its data

## Outputs

The code was executed with the provided notebook, and the results are in the `outputs` directory. 

## Known issues

**The Support Check drops too many good Claims, so it is switched off by default.** With `BRICKSPLAIN_SUPPORT_CHECK` unset, a Claim is shown when its Citation is verified (the Cell and lines exist and contain the quote), which proves the quote is real but not that the Claim follows from it. A Claim that cites a print-only line can still say it "halts the run".

What was found while tuning it (Jev, `jev-1.13`, threshold 0.5):

- Jev separates cleanly when the Claim and the evidence match: in a hand-labelled set of 11 Claims, true ones scored 0.75 to 0.94 and false ones 0.02 to 0.14, including print-only "halts the run" Claims.
- Real generated docs score far lower. On the sample Notebook the developer doc lost 43 of about 100 Claims, nearly all of them the Inferred Glossary entries and `data_flow` Claims. Many dropped Claims are fair: a Claim about two Cells that cites one, a glossary entry that states a purpose its one cited line doesn't show, or "never used" backed only by the definition line.
- Some are Jev misses. Evidence without its location scored Claims that name a Cell ("defined in cell 3") low. Heading the evidence `Cell N, lines a-b:` kept 85 of 101 Claims instead of 57 without letting the labelled false Claims through, and that is in the code. The count was still too high to ship, and most mid-range scores (0.3 to 0.55) look like noise.
- Retrying on a Support Check drop cost a full LLM call and was worse than the first pass, so only Citation failures are retried.

Next steps to fix it: rewrite the developer prompt so each glossary entry and `data_flow` Claim states only what its cited lines show and cites every Cell it names; collect labelled Claims from real docs to set the threshold; or replace the decision model with a cheaper LLM judge that returns a reason.

## Next Steps

What I'd do next:

| Improvement | Type | Affects | Description |
|---|---|---|---|
| Fix Proposals | Functional | Business Value | Along with providing the concerns and severity, propose fixes to the identified problems. Add a HITL gate that allows fixing as well, subject to org quality controls |
| Enhance eval suite | Non-Functional | Reliability, Cost Control | Add more evals to score behaviour against other types of notebooks (ML training runs, other business domains etc). This enables switching to cheaper models with an evidence-based approach |
| Observability | Non-Functional | Reliability, Logging, Cost Control | Use tools like LangFuse or MLFlow to monitor how many tokens are being consumed and the quality of answers | 
| AI Gateway Integration | Non-Functional | Reliability, Model Flexibility, Cost Control | Use an AI Gateway such as Unity Gateway or Bifrost etc. This allows an enterprise to control (white/blacklist) models, observe which models are being used, and attribute usage (and thus costs) to teams |
| UX Improvements | Non-Functional |  UX | Responsive (desktop/tablet/phone) UI, Dark mode. Make the Markdown file more readable |
| Secret vaulting | Non-Functional | Security | Currently the secret is stored as a `.env` file. It's outside the repo, so it is neither in git nor is it visible to a coding agent; however, a better security posture is for it to be stored in a proper secret store in Azure Key Vault, AWS Secrets Mgr or Hashicorp Vault | 
| Large Notebook handling | Non-Functional | Reliability, Scalability, Cost Control | Add chunking or a map-reduce pass for Notebooks that exceed the model's context window or the free-tier token limits. Citations must still verify against the original Cells, not the chunks |
| Prompt injection evals | Non-Functional | Security, Reliability | Notebook content is untrusted input to the LLM; a comment such as "ignore prior instructions" could alter the output. Add Eval Cases with planted injections and check that Citations still verify and no uncited prose appears |
| CI mode | Functional | Developer Experience, Business Value | A CLI or GitHub Action that regenerates the Audience Docs on a pull request and fails the check if a Notebook changed and its docs are stale |
