# Bricksplain

You have a Databricks **Notebook** that works but that nobody understands. Bricksplain explains it to three **Audiences** (a non-technical manager, a new developer, an AI coding agent) and proves each statement by linking it to the Notebook's own lines. Terms such as Claim, Citation and Verified Citation are defined in [GLOSSARY.md](GLOSSARY.md) and used here without redefining them.

It is a localhost web app. Point it at a Notebook path, press Generate, and get three Audience Docs in tabs, each downloadable as Markdown. It never executes the Notebook and knows nothing about any business domain.

## Run it

Requires Python 3.12 and [`uv`](https://docs.astral.sh/uv/). `just` is optional.

```
echo 'BRICKSPLAIN_MODEL=groq/<model id>' > .env   # provider is groq, openrouter or google
uv run bricksplain        # syncs dependencies if needed, serves http://127.0.0.1:8000
```

The input page is prefilled with the committed sample Notebook, `examples/cash_application_engine.py` (data in `examples/sample_data/`), so Generate works straight after cloning and every citation link opens real lines.

| Recipe | What it does |
|---|---|
| `just serve` | Same as `uv run bricksplain`: run the app, bound to 127.0.0.1 only |
| `just serve-debug` | Same, but logs go to `.logs/` inside the project and LLM responses are logged, so an assistant without access to your home directory can read them |
| `just test` | Offline test suite: no network, no API keys |
| `just eval` | Live evaluation against the configured provider (not part of `just test`) |
| `just lint` / `just fmt` | Ruff check / format |

Note: the `just` recipes are optional shortcuts; it can be installed from [GitHub](https://github.com/casey/just). Alternatively, you can open the justfile and run the relevant recipes from the command line.

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

### 8. Secure By Design

Two sets of LLMs were involved in this solution: Claude built it using Claude Code, and Gemini (or Groq/OpenRouter models) is used to generate the actual documents. Neither of these sets can see the secret, which in this case is the LLM API key. This is structurally enforced, not via prompt. The secret is stored in a different directory outside this project, and therefore not visible to Claude Code. This secret is also not sent to Gemini/Groq/OpenRouter. 

There is still one shortcut that was taken though, see the next steps for more details. 

## Layout

- `src/bricksplain/`: the app (`notebook.py` parsing, `audience_doc.py` schema, verification and Markdown, `jobs.py` concurrent generation, `cache.py`, `llm.py`, `config.py`, `logging_setup.py`, `app.py`)
- `evals/`: Eval Cases, the live runner and the generality fixture
- `tests/`: the offline suite
- `examples/`: the sample Notebook and its data

### 8. Outputs

The code was executed with the provided notebook, and the results are in the `outputs` directory. 

### 9. Next Steps

What I'd do next:

| Improvement | Type | Affects | Description |
|---|---|---|---|
| Fix Proposals | Functional | Business Value | Along with providing the concerns and severity, propose fixes to the identified problems. Add a HITL gate that allows fixing as well, subject to org quality controls |
| Enhance eval suite | Non-Functional | Reliability, Cost Control | Add more evals to score behaviour against other types of notebooks (ML training runs, other business domains etc). This enables switching to cheaper models with an evidence-based approach |
| Observability | Non-Functional | Reliability, Logging, Cost Control | Use tools like LangFuse or MLFlow to monitor how many tokens are being consumed and the quality of answers | 
| AI Gateway Integration | Non-Functional | Reliability, Model Flexibility, Cost Control | Use an AI Gateway such as Unity Gateway or Bifrost etc. This allows an enterprise to control (white/blacklist) models, observe which models are being used, and attribute usage (and thus costs) to teams |
| UX Improvements | Non-Functional |  UX | Responsive (desktop/tablet/phone) UI, Dark mode. Make the Markdown file more readable |
| Secret vaulting | Non-Functional | Security | Currently the secret is stored as a `.env` file. It's outside the repo, so it is neither in git nor is it visible to a coding agent; however, a better security posture is for it to be stored in a proper secret store in Azure Key Vault, AWS Secrets Mgr or Hashicorp Vault | 
| Citation coverage metrics | Non-Functional | Reliability, Trust | Report the share of Notebook lines and Cells that no Claim cites, so a reader can see what the doc does not cover. Today every statement can verify while important parts of the Notebook are silently omitted |
| Large Notebook handling | Non-Functional | Reliability, Scalability, Cost Control | Add chunking or a map-reduce pass for Notebooks that exceed the model's context window or the free-tier token limits. Citations must still verify against the original Cells, not the chunks |
| Prompt injection evals | Non-Functional | Security, Reliability | Notebook content is untrusted input to the LLM; a comment such as "ignore prior instructions" could alter the output. Add Eval Cases with planted injections and check that Citations still verify and no uncited prose appears |
| Semantic Verification | Non-Functional | Trust, Cost Control | The verifier proves that a quote exists, not that the Claim follows from it. Add a check that the quote actually supports the Claim, using a Decision Model like Jev, which is cheaper than a general-purpose LLM. Claims that fail are dropped or retried like any other failed Citation |
| CI mode | Functional | Developer Experience, Business Value | A CLI or GitHub Action that regenerates the Audience Docs on a pull request and fails the check if a Notebook changed and its docs are stale |
