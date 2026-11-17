# Spec: Bricksplain: cited explanations of an undocumented Databricks Notebook

Status: ready-for-agent

Source requirements: `req.md` (same directory). Vocabulary follows `GLOSSARY.md`.

## Problem Statement

Teams have Databricks Notebooks that work but that nobody understands: no comments, cryptic names, rules scattered across Cells. The people who need to understand them are different readers with different needs. A non-technical manager wants to know what the Notebook does for the business and where it might go wrong. A new developer needs an onboarding guide. An AI coding agent needs a terse, accurate briefing so it can change the Notebook safely.

Today, anyone asking an LLM to "explain this notebook" gets plausible prose that cannot be trusted, because nothing ties a statement back to the lines that justify it. A reader cannot tell a fact from a guess, and a hallucinated rule looks the same as a real one.

## Solution

Bricksplain is a localhost web app. The user points it at a Notebook (a default path is pre-filled with the sample cash-application Notebook) and presses Generate. The app produces three Audience Docs, one per Audience: manager, developer, AI coding agent.

Every statement about the Notebook is a Claim (a Fact or a Concern) and carries a Citation. A Citation is a link that opens a Source Viewer on the cited Cell with the Line Range highlighted. The app verifies each Citation against the Notebook before showing it, so a reader can trust that a cited line really exists and really contains what the Claim says it does. Generic explanatory framing that is not about the Notebook is allowed only as Context, visibly marked as such and carrying no Citation.

The app knows nothing about any particular business domain. It works for any Notebook, and a Notebook's own terminology reaches the reader only through an Inferred Glossary that the LLM derives from that Notebook.

The user chooses the LLM through a single model setting in the working directory's `.env`. API keys are kept centrally and shared across the user's other apps.

## User Stories

### Pointing the app at a Notebook
1. As a user, I want a path field pre-filled with the sample Notebook, so that I can generate docs immediately without typing.
2. As a user, I want to change the path to any other local Notebook, so that I can use the app on my own projects.
3. As a user, I want a clear error when the path does not exist or cannot be read, so that I know what to fix.
4. As a user, I want files that are not `.py` rejected with an explanation, so that I don't feed the app something it cannot parse.
5. As a user, I want files over the size cap rejected with an explanation, so that I don't accidentally spend money sending a huge file to an LLM.
6. As a user, I want a file with no Cell separators treated as one Cell with a visible warning, so that I still get output and understand the limitation.
7. As a user, I want the app reachable only from my own machine, so that nobody else on the network can make it read my files.
8. As a user, I want relative paths resolved against the working directory, so that the default path works wherever I launch the app from.

### Generating the Audience Docs
9. As a user, I want one Generate button that produces all three Audience Docs, so that I don't have to run each separately.
10. As a user, I want the three docs generated in parallel, so that I don't wait three times as long.
11. As a user, I want each Audience Doc in its own tab that fills in as soon as it finishes, so that I can start reading while the others are still running.
12. As a user, I want a failure in one Audience Doc not to block the other two, so that a single flaky call does not cost me the whole run.
13. As a user, I want a visible per-doc progress and error state, so that I know what is running, done or failed.
14. As a user, I want a Regenerate action per run that bypasses the cache, so that I can get a fresh answer when I'm unhappy with one.
15. As a user, I want to reload the page or revisit the same Notebook and get the previous result immediately, so that I don't pay for the same call twice.
16. As a user, I want the cache to invalidate automatically when the Notebook, the model or the prompts change, so that I never see stale output after a change.
17. As a user, I want a Download .md button on each Audience Doc, so that I can share it or commit it elsewhere.
18. As a user, I want the downloaded Markdown's Citations to remain usable as links, so that the evidence trail survives export.

### Trust and evidence
19. As a reader, I want every statement about the Notebook to carry a Citation with Cell number and Line Range, so that I can check it myself.
20. As a reader, I want to click a Citation and land in the Source Viewer on the right Cell with the Line Range highlighted, so that verification takes one click.
21. As a reader, I want Citations validated by the server before display, so that I never follow a link to lines that don't exist or don't match.
22. As a reader, I want a Claim whose Citation fails validation retried once and then dropped or visibly flagged, so that a hallucination never appears as a trusted statement.
23. As a reader, I want Facts, Concerns and Context visually distinguishable, so that I know whether I'm reading what the code does, a judgment about it, or generic background.
24. As a reader, I want Concerns to show a severity, so that I know which to read first.
25. As a reader, I want Context to carry no Citation and a clear "not from the Notebook" marker, so that I never mistake it for evidence.
26. As a reader, I want behaviour that depends on code outside the Notebook (for example an included helper Notebook) reported as unknown and not guessed, so that the docs don't invent logic.
27. As a reader, I want that unseen dependency raised as a Concern, so that I know the explanation has a blind spot.
28. As a reader, I want commented-out code described only as disabled and never as live behaviour, so that I'm not misled about what runs.
29. As a reader, I want disabled code cited as design history when it is informative, so that I learn what was tried and parked.
30. As a reader, I want Cell numbers and line numbers to match what I see in an editor and in the Source Viewer, so that no mental translation is needed.

### Source Viewer
31. As a reader, I want to view the whole Notebook with Cell boundaries marked, so that I can see structure and context around a cited Line Range.
32. As a reader, I want a cited Line Range highlighted and scrolled into view, so that I don't hunt for it.
33. As a reader, I want a link to a nonexistent Cell or Line Range to show a clear message, so that stale links fail gracefully.
34. As a reader, I want to browse back to the Audience Doc from the viewer, so that I can continue reading after checking a Citation.

### Manager Audience Doc
35. As a non-technical manager, I want a plain-language summary of what the Notebook does, so that I understand its business purpose without reading code.
36. As a non-technical manager, I want an explanation of how it works in business terms, so that I can reason about its behaviour.
37. As a non-technical manager, I want its outcomes and impact described, so that I know what it produces and who depends on it.
38. As a non-technical manager, I want a Potential Issues section of Concerns, so that I know where risk sits.
39. As a non-technical manager, I want jargon avoided or explained in the doc, so that I can read it unaided.

### Developer Audience Doc
40. As a new developer, I want a map of the Notebook by Cell, so that I know where things live.
41. As a new developer, I want a description of data flow from inputs to outputs, so that I can trace how data moves.
42. As a new developer, I want the business rules extracted and cited, so that I can find the exact lines that implement each.
43. As a new developer, I want an Inferred Glossary of the Notebook's own cryptic names and terms, so that I can decode abbreviations.
44. As a new developer, I want each Inferred Glossary entry cited to where the term is defined or first used, so that I can verify the interpretation.
45. As a new developer, I want gotchas and how-to-run notes (parameters, side effects, write behaviour), so that I don't cause damage on my first run.

### AI coding agent Audience Doc
46. As an AI coding agent, I want a concise statement of the Notebook's purpose, so that I orient fast.
47. As an AI coding agent, I want invariants listed as terse cited fragments, so that I know what must stay true.
48. As an AI coding agent, I want risky areas flagged with citations, so that I take extra care there.
49. As an AI coding agent, I want guidance on how to verify a change is safe, so that I can check my own work.
50. As an AI coding agent, I want grammar sacrificed for brevity but never accuracy, so that I spend few tokens and still trust the content.

### Domain-agnostic behaviour
51. As a user, I want the app to work on a Notebook from any business domain, so that it is reusable beyond the sample.
52. As a user, I want no domain vocabulary baked into the prompts or output skeletons, so that documentation of an unrelated Notebook isn't polluted.
53. As a user, I want the same fixed section skeleton for each Audience regardless of Notebook, so that the docs are predictable.

### Model and provider configuration
54. As a user, I want to choose the model with one setting in the working directory's `.env`, so that each of my apps can use a different model.
55. As a user, I want the setting to be `<provider>/<model id>` with provider `groq` or `openrouter`, so that the provider is explicit.
56. As a user, I want the model id after the first slash passed verbatim to the provider, so that provider-style ids with slashes work.
57. As a user, I want an unknown provider or a missing slash to fail at startup with a clear message, so that misconfiguration is caught early.
58. As a user, I want API keys read from my central providers directory (named by `LLM_PROVIDERS`) first and then from the working directory, so that credentials stay centralised.
59. As a user, I want a missing key in the central file to fall back to the working directory's `.env` for that key, so that partial setups still work.
60. As a user, I want the model setting honoured only from the working directory's `.env`, so that a shared central file can never force a model on every app.
61. As a user, I want only the chosen provider's key required, so that I don't need both providers to run.
62. As a user, I want a startup error naming the missing key (never its value), so that I can fix configuration safely.

### Logging and observability
63. As a user, I want a log file per app start named by its start time, so that runs are easy to tell apart.
64. As a user, I want the log location chosen from an explicit override, then the XDG state directory, then the home fallback, so that logs go where my machine convention says.
65. As a user, I want INFO as the default level and an override, so that logs are useful but quiet by default.
66. As a user, I want all LLM failures and rate limits (including retry timing) logged, so that I can diagnose flaky runs.
67. As a user, I want retries and citation-validation failures logged, so that I can see why a Claim was dropped.
68. As a user, I want request metadata logged (provider, model, latency, token counts, status), so that I can track cost and speed.
69. As a user, I want prompts and Notebook content never logged by default, so that private code stays out of log files.
70. As a user, I want API keys and anything key-shaped redacted from logs, so that credentials never leak even by accident.
71. As a developer working with an AI assistant, I want a debug serve command that writes logs inside the project directory, so that the assistant, which cannot see my home directory, can read them.
72. As a developer, I want debug-level logging of LLM responses to require explicit opt-in, so that sensitive output is not logged by accident.

### Prompts
73. As a maintainer, I want all system prompts stored as separate files loaded at runtime, so that they are reviewed and versioned like code.
74. As a maintainer, I want a prompt change to invalidate cached results, so that edits take effect on the next generation.

### Quality and evaluation
75. As a maintainer, I want an offline test suite that needs no network or API keys, so that it runs anywhere, fast.
76. As a maintainer, I want a separate live evaluation command, so that I can measure real model output without it running in routine tests.
77. As a maintainer, I want Eval Cases stored as code, so that expectations are reviewed alongside the behaviour they check.
78. As a maintainer, I want Eval Cases for the sample Notebook covering the planted risks (a tolerance constant silently reassigned, an unused cap constant, a "FIFO" step that orders by largest balance, an overwrite-mode write, and an unseen included dependency), so that I can tell whether the docs surface real problems.
79. As a maintainer, I want a second, deliberately different, hand-written Notebook as a generality check, so that overfitting to the first domain is detected.
80. As a maintainer, I want that check to assert the output contains none of the first domain's vocabulary and that every Citation verifies, so that domain-agnosticism is tested and not assumed.
81. As a maintainer, I want an offline test that each Eval Case's expected Citation points at real lines in its fixture, so that cases cannot silently rot when fixtures change.

### Documentation and project hygiene
82. As a reader of the portfolio, I want a README stating the purpose and each design decision with the alternatives rejected, so that I can judge the engineering.
83. As a reader of the portfolio, I want the caching decision documented as cost control, so that the rationale is explicit.
84. As a reader of the portfolio, I want the offline-versus-live testing split and the evaluation approach explained, so that the quality strategy is clear.
85. As a developer, I want common commands (serve, debug serve, test, eval, lint, format) as `just` recipes, so that I don't memorise invocations.
86. As a developer, I want an editable install in a `src` layout managed with `uv`, so that setup is one command and edits take effect immediately.

## Implementation Decisions

**Notebook model**
- A Notebook is parsed into ordered Cells, split on the Databricks separator line. Cells are numbered from 1, and the leading markdown header counts as Cell 1. The separator lines and the very first source-marker line belong to no Cell.
- Line numbers are absolute, 1-based file lines. A Line Range must lie inside a single Cell.
- A file with no separators is one Cell and raises a warning shown to the user.
- Cell kind (code, markdown, SQL, run directive) is detected from magic prefixes so the LLM and viewer can treat a run directive as an external dependency.
- The app is read-only with respect to the Notebook. It never executes it, and sample data files are never read by the app.

**Claim model and verification**
- The LLM returns structured JSON. Each Audience Doc is a fixed set of sections, each containing items typed as Fact, Concern or Context.
- Facts and Concerns carry one or more citations of the form (cell number, start line, end line, verbatim quote). Concerns also carry a severity. Context carries no citation.
- A verification step checks, for every citation: the Cell exists, the lines lie within that Cell, and the quote appears in those lines (whitespace-normalised). Only Verified Citations are rendered as links.
- A Claim with a failing Citation triggers one retry of that Audience Doc's generation with the failures fed back. After the retry, remaining failing Claims are dropped and the count of dropped Claims is shown and logged.
- Rendering takes validated structure and produces HTML. Prose is never taken as free text from the LLM.
- Citation links target a Source Viewer URL carrying the Cell number and Line Range. Markdown export keeps these as relative links.
- Behaviour defined outside the Notebook is reported as unknown, never inferred, and is surfaced as a Concern.
- Commented-out code is described only as disabled.

**Audience Docs** (skeleton fixed by the output schema; no domain words)
- Manager: Summary; How it works in business terms; Outcomes and impact; Potential issues.
- Developer: Notebook map by Cell; Data flow; Business rules; Inferred Glossary; Gotchas and how to run.
- Agent: Purpose; Invariants; Risky areas; How to verify changes. Terse fragments, accuracy over grammar.
- The Inferred Glossary lives only in the Developer doc, each entry cited to its definition or first use.

**Prompts**
- One system prompt per Audience, stored as separate text files inside the package and loaded at runtime via package resources. None may contain domain-specific words. Prompts are treated as code and changes are reviewed.

**Generation and caching**
- One LLM call per Audience Doc, run concurrently. The whole Notebook is sent in one call, since typical Notebooks fit in context.
- Each Audience Doc is independently cached on disk, keyed by Notebook content hash, model string and prompt hash. Regenerate bypasses the cache. Caching is a cost-control decision, since free-tier calls are rate-limited and each doc costs a call.
- One Audience Doc failing does not affect the others. The UI shows per-doc states: pending, running, done, failed.

**Web app**
- A localhost-only server (bound to 127.0.0.1) rendering server-side HTML with partial updates, with no JavaScript build step. Pages: the input page with path field and tabs for the three Audience Docs, and the Source Viewer.
- The Source Viewer shows the entire Notebook with Cell boundaries and highlights the requested Line Range, scrolling it into view. Bad Cell or line parameters show a clear message.
- Path input validation: must exist, readable, a `.py` file, no larger than about 500 KB. Relative paths resolve against the working directory. The default path is the sample Notebook.
- Each Audience Doc has a Markdown download.

**LLM access and configuration**
- Two providers, `groq` and `openrouter`, both reached through the OpenAI-compatible chat interface via a small provider table of base URLs. Structured-output mode is used where the provider and model support it, with prompt-plus-validation as the fallback.
- The model setting is `BRICKSPLAIN_MODEL` of the form `<provider>/<model id>`, split on the first slash. The remainder is passed verbatim. Unknown provider or missing slash is a startup error.
- The model is read only from the working directory's `.env`, never from the central providers file or the process environment.
- API keys (`GROQ_API_KEY`, `OPENROUTER_API_KEY`) are resolved per key: the `.env` under the directory named by `LLM_PROVIDERS` first, then the working directory's `.env`. Only the selected provider's key is required. Errors name the missing key and never print values.
- The LLM client is the one external dependency replaced by a fake in tests.

**Logging**
- One file per app start, named `log_YYYYMMDD_hhmmss.log` from start time.
- Directory chosen in order: `BRICKSPLAIN_LOG_PATH` (a directory), then `XDG_STATE_HOME` plus `bricksplain`, then `~/.local/state/bricksplain`.
- Default level INFO, overridable by `LOG_LEVEL`.
- Logged: LLM failures, rate limits with retry-after, retries, citation-validation failures and dropped Claim counts, and request metadata (provider, model, latency, token counts, status).
- Never logged by default: prompts, Notebook content, API keys. A redaction filter masks key-shaped strings and the values of the configured key variables. LLM response bodies are logged only on explicit debug opt-in.
- A debug serve variant sets the log directory to a gitignored directory inside the project so an AI assistant without access to the user's home can read the logs.

**Packaging and tooling**
- Python 3.12, `uv` for dependencies (`uv add`, never `pip`), `src` layout with an editable install during development.
- `just` recipes for: serve, debug serve, test, eval, lint, format.
- The existing stub entry script is replaced by the package.

**Documentation**
- `README.md` states purpose and records design decisions in decision-record style with alternatives rejected: verified citations, caching and cost control, offline-versus-live testing and evaluation, the `.env` split between central keys and per-app model, logging and redaction, and the domain-agnostic prompt rule.
- `GLOSSARY.md` already exists and holds app-level terms only. No separate ADR files are created, because the README is the requested home for decisions.

## Testing Decisions

**What makes a good test here:** assert external behaviour only: what a user sees, what is written to the log, what the cache returns. Do not assert on internal function structure, prompt wording, or intermediate data shapes. Tests must run without network or API keys.

**Seam 1 (primary): the HTTP app with a fake LLM client.** Tests drive the app end to end with a Notebook path and canned structured LLM output, and assert on rendered Audience Docs, Verified Citations and their Source Viewer links, dropped-Claim handling, retry behaviour, cache hit and bypass, per-doc failure isolation, path validation, Markdown download, and Source Viewer highlighting. Parsing, verification, rendering, prompt loading and caching are all exercised through this seam and not unit-tested in isolation.

**Seam 2: configuration resolution** (env files and variables in, resolved model, keys and log directory out). It is tested directly because it has strict precedence rules, such as the model coming only from the working directory `.env`, that are impractical to reach through HTTP. It also covers log-path precedence, the redaction guarantee (a secret value never appears in the log file) and startup errors.

**Seam 3 (live, not in routine tests): the evaluation command.** It calls the real provider and checks Eval Cases for the sample Notebook and the generality Notebook. It is excluded from the default test run and from CI.

**Offline guard on the evals:** a default-suite test verifies that every Eval Case's expected Citation points at real lines in its fixture, so cases cannot silently rot.

**Prior art:** none. The repository is a fresh scaffold, and the fixtures are the two sample Notebooks.

## Out of Scope

- Executing the Notebook, or reading or analysing the sample CSV data.
- Providers beyond `groq` and `openrouter`.
- Notebook formats other than the Databricks `.py` export (for example `.ipynb` or DBC archives).
- Multi-user hosting, authentication, or exposure beyond localhost.
- Editing or writing back to the Notebook, or auto-fixing the issues found.
- Chunking or summarising Notebooks too large for one LLM call (the size cap rejects them instead).
- Fuzzy or semantic re-anchoring of citations whose lines don't match (they are dropped, not repaired).
- Persisting history of past runs beyond the on-disk cache.
- Separate ADR files.

## Further Notes

- Why verified, structured citations is the central design bet: it turns "trust the LLM" into "check the evidence in one click", and is the main portfolio differentiator.
- The sample Notebook contains real quirks that the Eval Cases target: a tolerance constant reassigned mid-run, a declared but unused write-off cap, a step labelled FIFO that orders by largest balance, an overwrite-mode table write, an externally defined helper Notebook, and large blocks of commented-out legacy logic. These are fixtures for evaluation only and must never appear in prompts or the app's own code paths.
- The user's own `XDG` convention: the standard variable is `XDG_STATE_HOME`. An earlier draft used a non-standard name, which was corrected.
- The user cannot expose their home directory to the AI assistant, so anything needing the host machine (viewing real logs, checking their `LLM_PROVIDERS` file) must be asked of them or routed through the debug serve variant.
- Suggested build order: scaffold and configuration; Notebook parsing and citation verification; LLM client and generation; web app and Source Viewer; evals; README.
