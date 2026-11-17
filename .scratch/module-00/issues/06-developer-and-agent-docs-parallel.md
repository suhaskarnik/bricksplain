# 06: Developer and Agent docs, tabs and parallel generation

**What to build:** Generate now produces all three Audience Docs concurrently, each in its own tab that fills in as it finishes, and one doc failing does not block the others. See `spec.md` (Audience Docs, Generation and caching).

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] Developer doc skeleton: Notebook map by Cell, Data flow, Business rules, Inferred Glossary, Gotchas and how to run
- [ ] Every Inferred Glossary entry is cited to where the term is defined or first used; the glossary appears only in the Developer doc
- [ ] Agent doc skeleton: Purpose, Invariants, Risky areas, How to verify changes; terse fragments, accuracy over grammar
- [ ] One prompt file per Audience, all loaded at runtime and domain-free
- [ ] The three calls run concurrently; each tab shows pending, running, done or failed and updates as it finishes
- [ ] A failure in one doc leaves the other two unaffected
- [ ] Offline HTTP-seam tests cover all three docs, the parallel flow and per-doc failure isolation
