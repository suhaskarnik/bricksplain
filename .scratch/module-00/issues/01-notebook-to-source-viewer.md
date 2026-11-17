# 01: Notebook to Source Viewer

**What to build:** A user starts the app with `just serve`, sees an input page with the default Notebook path pre-filled, and can open the Source Viewer for any Cell and Line Range. This slice also lays down the project scaffold. See `spec.md` (Notebook model, Web app, Packaging and tooling) and `GLOSSARY.md`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Project uses a `src` layout managed with `uv`, installed editable; the stub entry script is replaced; dependencies added via `uv add`
- [ ] `just` recipes exist for serve, test, lint and fmt
- [ ] Server binds to 127.0.0.1 only
- [ ] Input page pre-fills the default sample Notebook path; relative paths resolve against the cwd
- [ ] Path is rejected with a clear message if missing, unreadable, not `.py`, or over ~500 KB
- [ ] Notebook is split into Cells on the Databricks separator; Cells numbered from 1 (the leading markdown header is Cell 1); line numbers are absolute and 1-based; separator lines belong to no Cell
- [ ] Cell kind (code, markdown, SQL, run directive) is detected from magic prefixes
- [ ] A file with no separators becomes a single Cell and a visible warning is shown
- [ ] Source Viewer shows the whole Notebook with Cell boundaries marked, highlights the requested Line Range and scrolls it into view
- [ ] A nonexistent Cell, or a Line Range outside the Cell, shows a clear message instead of an error
- [ ] Offline tests drive the app over HTTP against the sample Notebook and verify Cell numbering, Line Range highlighting and path validation
