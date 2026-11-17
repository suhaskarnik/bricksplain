# 05: Retry, rate limits and failure handling

**What to build:** Flaky or rate-limited LLM calls and bad Citations are handled gracefully and are diagnosable from the logs. See `spec.md` (Claim model and verification, Logging).

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] When a doc has failing Claims, generation is retried once with the validation failures fed back; remaining failures are dropped and counted
- [ ] HTTP 429 is handled by honouring `Retry-After`, with bounded retries
- [ ] All LLM failures, rate limits (with retry timing), retries and validation failures are logged without prompts or keys
- [ ] When retries are exhausted, the doc shows a clear error state in the UI instead of a stack trace
- [ ] Offline tests with a fake LLM covering: succeed after retry, drop after retry, 429 then success, persistent failure
