# Bricksplain

You have a Databricks **Notebook** that works but that nobody understands. Bricksplain explains it to three **Audiences** (a non-technical manager, a new developer, an AI coding agent) and proves each statement by linking it to the Notebook's own lines. Terms such as Claim, Citation and Verified Citation are defined in [GLOSSARY.md](GLOSSARY.md) and used here without redefining them.

It is a localhost web app. Point it at a Notebook path, press Generate, and get three Audience Docs in tabs, each downloadable as Markdown. It never executes the Notebook and knows nothing about any business domain.

## Run it

Requires Python 3.12, [`uv`](https://docs.astral.sh/uv/) and [`just`](https://just.systems/).

```
uv sync
echo 'BRICKSPLAIN_MODEL=groq/<model id>' > .env   # provider is groq, openrouter or google
just serve        # http://127.0.0.1:8000
```

| Recipe | What it does |
|---|---|
| `just serve` | Run the app, bound to 127.0.0.1 only |
| `just serve-debug` | Same, but logs go to `.logs/` inside the project and LLM responses are logged, so an assistant without access to your home directory can read them |
| `just test` | Offline test suite: no network, no API keys |
| `just eval` | Live evaluation against the configured provider (not part of `just test`) |
| `just lint` / `just fmt` | Ruff check / format |

## Design decisions

### 1. Every Claim carries a Verified Citation

The LLM returns structured JSON: sections of items typed Fact, Concern or Context. Facts and Concerns must cite `(cell, start line, end line, verbatim quote)`. Before anything is shown, each Citation is checked: the Cell exists, the lines lie inside it, and the quote appears in those lines (whitespace-normalised, ignoring the `# MAGIC` prefix Databricks puts on markdown and SQL lines). A Claim that fails triggers one retry of that doc with the failures fed back; Claims still failing are dropped, and the count is shown and logged. Citations render as links that open the Source Viewer at the Line Range.

Rejected:
- *Trust the LLM's prose.* Nothing lets a reader check it.
- *Fuzzy or semantic re-anchoring of bad citations.* It would quietly repair evidence instead of rejecting it, defeating the point.
- *Free-text output rendered as is.* Prose is never taken from the LLM unstructured, so there is nowhere for an uncited statement to hide. Generic framing is allowed only as Context, visibly marked and uncited.

This is the central bet: it turns "trust the LLM" into "check the evidence in one click". The verifier is deliberately strict, so prompts ask for short quotes (long multi-line quotes get miscopied and dropped).

### 2. Caching is cost control

Each Audience Doc costs one LLM call, and the free tiers are rate-limited. Docs are cached on disk, keyed by Notebook content, model string, prompt text and section skeleton, so editing a prompt invalidates old results. Regenerate bypasses the cache. A doc with dropped Claims is not cached, so a flaky generation is not frozen in.

Rejected: *no cache* (burns quota on every click); *keying on file path or mtime* (stale after edits, misses after renames); *a database* (a directory of JSON files is enough for one user).

### 3. Offline tests for behaviour, live evals for model quality

The default suite is fully offline. Its main seam is the HTTP app with a fake LLM client, so parsing, verification, rendering, retry, caching and failure isolation are tested through what a user sees. Configuration resolution is tested directly because its precedence rules are hard to reach through HTTP.

Whether a real model *notices* real problems cannot be tested offline, so `just eval` calls the real provider. **Eval Cases** are code (`evals/cases.py`): a name, the fixture Notebook, the Audience, what must be surfaced, the expected Cell and Line Range with a quote, and why it matters. A case passes when some Claim in that Audience's doc cites lines overlapping the expected range. Output is PASS or FAIL per case.

A default-suite test checks that every case's expected Citation points at real lines in its fixture, so cases cannot rot silently when a fixture changes.

Rejected: *live calls in the default suite* (slow, flaky, needs keys, costs money); *judging answers with another LLM* (adds a second source of error to a check that line overlap does deterministically).

### 4. A generality fixture guards against overfitting

The sample Notebook (a cash-application engine, with planted quirks such as a tolerance constant reassigned mid-run, an unused cap constant, a "FIFO" step that orders by largest balance, an overwrite-mode write and an unseen `%run`) is easy to overfit to. `evals/fixtures/sensor_feature_pipeline.py` is a hand-written, unrelated ML feature pipeline with its own planted quirks (the target used as a feature, scaling fitted before the split, an ignored seed, an overwrite-mode write, an unseen `%run`). `just eval` checks, for every Audience, that the docs for it contain none of the first domain's vocabulary and that every Citation verifies. An offline test checks the fixture itself contains none of that vocabulary.

### 5. The prompts are domain-agnostic

Prompts (`src/bricksplain/prompts/`, one file per Audience) fix only the skeleton and the rules: never guess, behaviour defined outside the Notebook is reported as unknown and raised as a Concern, commented-out code is described only as disabled, a name that disagrees with its code is a Concern. They contain no domain words, and neither does application code; Eval Case vocabulary lives only in `evals/`. A Notebook's own terminology reaches the reader only through the Inferred Glossary, which the LLM derives from that Notebook.

Rejected: *domain-tuned prompts* (better on one Notebook, wrong on the next, and impossible to tell apart from overfitting).

### 6. Model in the working directory, keys shared centrally

`BRICKSPLAIN_MODEL=<provider>/<model id>` is read only from the working directory's `.env`, never from the process environment or the central file, because the model is a per-app choice. API keys are shared across the author's apps, so each key resolves from the `.env` under the directory named by `LLM_PROVIDERS` first, then the working directory's `.env`. Only the selected provider's key is required, and errors name the missing key without printing values.

Rejected: *one config file for everything* (would duplicate keys per app or force one model on all of them); *the environment for the model* (a stray exported variable silently changes which model is used).

### 7. Logging with redaction

One file per app start, `log_YYYYMMDD_hhmmss.log`, in `BRICKSPLAIN_LOG_PATH`, else `$XDG_STATE_HOME/bricksplain`, else `~/.local/state/bricksplain`. Level is INFO unless `LOG_LEVEL` says otherwise. It records LLM failures, rate limits with retry timing, retries, citation failures and dropped-Claim counts, and request metadata (provider, model, latency, tokens, status).

Prompts and Notebook content are never logged. A formatter masks the configured key values and anything key-shaped, in the final formatted text, so tracebacks are covered too. LLM response bodies, and the text and quotes of failing Claims, are logged only when `BRICKSPLAIN_LOG_LLM_RESPONSES=1` (which `just serve-debug` sets).

Rejected: *logging prompts for debuggability* (private code ends up in log files); *redacting by call site* (one forgotten call leaks a key).

## Layout

- `src/bricksplain/`: the app (`notebook.py` parsing, `audience_doc.py` schema, verification and Markdown, `jobs.py` concurrent generation, `cache.py`, `llm.py`, `config.py`, `logging_setup.py`, `app.py`)
- `evals/`: Eval Cases, the live runner and the generality fixture
- `tests/`: the offline suite
- `testdata/`: the sample Notebook (git-ignored)
