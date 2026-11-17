# 09: Eval harness and sample-Notebook Eval Cases

**What to build:** A live evaluation command that checks whether the generated docs surface the known problems in the sample Notebook. See `spec.md` (Testing Decisions, Further Notes).

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] `just eval` runs Eval Cases against the real configured provider and is excluded from `just test`
- [ ] Eval Cases are stored as code data: a name, the fixture Notebook, the Audience, what must be surfaced, the expected cited Cell and Line Range, and why it matters
- [ ] Cases for the sample Notebook cover: tolerance constant reassigned mid-run, declared but unused write-off cap, a "FIFO" step that orders by largest balance, an overwrite-mode table write, and the unseen included dependency
- [ ] An offline test in the default suite verifies that every case's expected Citation points at real lines in its fixture
- [ ] Eval output reports pass or fail per case
- [ ] No Eval Case vocabulary leaks into prompts or application code
