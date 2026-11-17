# 07: Disk cache and Regenerate

**What to build:** Re-generating for an unchanged Notebook is free and instant; a Regenerate action forces a fresh LLM call. This is the cost-control decision. See `spec.md` (Generation and caching).

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] Each Audience Doc is cached on disk independently, keyed by Notebook content hash, model string and prompt hash
- [ ] A cache hit makes no LLM call; reloading the page or revisiting the Notebook shows the cached result immediately
- [ ] Changing the Notebook, the model or a prompt invalidates the relevant entries automatically
- [ ] Regenerate bypasses the cache and refreshes it
- [ ] Cache hits and misses are logged at INFO
- [ ] Offline tests prove no LLM call on a hit, and invalidation on each of the three key components
