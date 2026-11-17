# 10: Generality fixture

**What to build:** Proof that the app is domain-agnostic: a second, deliberately different Notebook whose docs contain none of the first Notebook's domain vocabulary. See `spec.md` (Testing Decisions, Further Notes) and `GLOSSARY.md` (Eval Case).

**Blocked by:** 09

**Status:** ready-for-agent

- [ ] A hand-written Notebook from an unrelated domain (such as an ETL or ML feature pipeline) is added as a fixture, with planted quirks
- [ ] Eval Cases for it assert that the planted quirks are surfaced
- [ ] The eval asserts the generated docs contain no vocabulary from the cash-application domain
- [ ] The eval asserts every Citation verifies
- [ ] An offline test verifies that the new Eval Cases' expected Citations point at real fixture lines
