# 02: Model and key resolution

**What to build:** The app resolves which LLM to use and which API key to use from `.env` files, and shows the resolved provider and model on the page. Misconfiguration fails at startup with a clear message. See `spec.md` (LLM access and configuration).

**Blocked by:** 01

**Status:** done

- [x] `BRICKSPLAIN_MODEL` is read only from the cwd `.env`, never from the `$LLM_PROVIDERS` file or the process environment
- [x] The value is `<provider>/<model id>`, split on the first `/`; the remainder is passed on verbatim; providers are `groq` and `openrouter`
- [x] Unknown provider or missing slash fails at startup with a clear message
- [x] `GROQ_API_KEY` / `OPENROUTER_API_KEY` are resolved per key: the `.env` under the directory named by `LLM_PROVIDERS` first, then the cwd `.env`
- [x] Only the chosen provider's key is required; a missing key error names the key and never prints any value
- [x] Resolved provider and model are displayed on the page
- [x] Tested directly (seam 2) with temp directories and env vars, covering precedence, per-key fallback and the model-only-from-cwd rule
