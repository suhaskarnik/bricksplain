# 11: README with design decision records

**What to build:** A README that tells a portfolio reader what Bricksplain is and why each key decision was made. See `spec.md` (Documentation).

**Blocked by:** 07, 08, 10

**Status:** ready-for-agent

- [ ] States the purpose and the problem (a working but not understood Notebook, three Audiences)
- [ ] Records each decision with alternatives rejected: verified structured citations, caching as cost control, offline versus live testing and the Eval Case approach, the `.env` split between central keys and per-app model, logging and redaction, the domain-agnostic prompt rule
- [ ] Explains how to run, test, eval and debug-serve using the `just` recipes
- [ ] Documents the Eval Cases and the generality fixture
- [ ] Uses `GLOSSARY.md` vocabulary and does not duplicate it
- [ ] No separate ADR files are created
