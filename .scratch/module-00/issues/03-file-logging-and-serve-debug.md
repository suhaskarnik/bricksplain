# 03: File logging and `just serve-debug`

**What to build:** The app writes a per-start log file at a predictable location, never leaks secrets, and a debug serve variant writes logs inside the project so an AI assistant can read them. See `spec.md` (Logging).

**Blocked by:** 02 (redaction needs the configured key values)

**Status:** done

- [x] One log file per app start, named `log_YYYYMMDD_hhmmss.log` from the start time
- [x] Directory chosen in order: `BRICKSPLAIN_LOG_PATH` (a directory), `$XDG_STATE_HOME/bricksplain/`, `$HOME/.local/state/bricksplain/`; created if missing
- [x] Default level INFO; `LOG_LEVEL` overrides
- [x] A redaction filter masks configured API key values and key-shaped strings (including `Bearer ...`)
- [x] Prompts and Notebook content are not logged by default; LLM response bodies are logged only on explicit debug opt-in
- [x] `just serve-debug` sets `BRICKSPLAIN_LOG_PATH` to a directory inside the project, which is gitignored
- [x] Tests prove precedence of the three locations and that a secret value never appears in the log file
