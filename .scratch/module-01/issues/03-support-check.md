# 03: Support check on every Claim

**What to build:** A reader can trust that each shown Claim follows from its own quote. After Citation verification, one extra LLM call per Audience Doc judges whether each Claim is supported by its quote; unsupported Claims are retried once with the reason, then dropped. See `spec.md` (Support check; stories 1-8; Supported Citation in `GLOSSARY.md`).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] A dedicated prompt for the support check is loaded at runtime from the prompts directory, with no domain vocabulary
- [ ] The call is batched: at most one extra call per Audience Doc
- [ ] Each Claim gets a supported/unsupported verdict and a short reason; unsupported Claims enter the existing retry-once-then-drop path
- [ ] The dropped-Claim count and log entries include support-check drops; reasons are logged only when LLM response logging is on
- [ ] A doc with dropped Claims is still not cached
- [ ] The cache key includes the support-check prompt text, so editing it invalidates stored docs
- [ ] Rate-limit and failure handling cover the extra call without breaking failure isolation between Audience Docs
- [ ] Offline tests with a scripted fake LLM cover: a Claim claiming a check halts the run while its quote only prints is dropped; a retry recovers a Claim; a failure in the support call is isolated to its Audience Doc; changing the prompt invalidates the cache
