# 04: Manager doc end to end with verified citations

**What to build:** The user presses Generate and receives the Manager Audience Doc, in which every Fact and Concern carries a Verified Citation that links into the Source Viewer. This is the core tracer: LLM client, prompt, schema, verification and rendering. See `spec.md` (Claim model and verification, Audience Docs, Prompts, LLM access).

**Blocked by:** 01, 02, 03

**Status:** done

- [x] Generate button produces the Manager Audience Doc with the fixed skeleton: Summary, How it works in business terms, Outcomes and impact, Potential issues
- [x] LLM client talks to both providers via the OpenAI-compatible interface with a provider table; structured-output mode where supported, otherwise prompt plus validation
- [x] The system prompt is a separate file loaded at runtime, contains no domain-specific words, and tells the LLM to report out-of-Notebook dependencies as unknown and commented-out code as disabled
- [x] The LLM returns structured Facts, Concerns (with severity) and Context; Context has no Citation and is visibly marked as not from the Notebook
- [x] Verification checks each citation: Cell exists, lines lie inside the Cell, quote appears in those lines (whitespace-normalised); only Verified Citations render as links
- [x] Failing Claims are dropped (retry comes in ticket 05) and the dropped count is shown and logged
- [x] Prose is rendered from validated structure only
- [x] Clicking a Citation opens the Source Viewer on that Cell with the Line Range highlighted
- [x] LLM request metadata (provider, model, latency, tokens, status) is logged
- [x] Offline tests at the HTTP seam use a fake LLM client with canned output, covering a valid doc, a bad Cell, out-of-range lines and a quote mismatch
