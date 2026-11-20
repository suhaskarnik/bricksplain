# 01: Reproducible repo and one-command start

**What to build:** Someone who clones the repo can start the app with a single command and generate docs for the sample Notebook, with every citation link opening real lines. See `spec.md` (Implementation Decisions: Repository contents, Start-up) and `GLOSSARY.md`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] The sample Notebook and its data are committed under an examples directory and no longer excluded by the ignore rules
- [ ] The app's default Notebook path points at the committed sample
- [ ] One documented command syncs dependencies if needed and starts the app, bound to 127.0.0.1
- [ ] The existing `just` recipes still work and are described as optional shortcuts
- [ ] Offline test: the default path exists, parses into Cells, and its Source Viewer page opens for a Cell and Line Range
- [ ] README run instructions describe the single command
