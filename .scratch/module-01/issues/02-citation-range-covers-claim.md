# 02: Citation range covers what the Claim asserts

**What to build:** A reader who clicks a Citation sees lines that cover everything the Claim asserts. A Claim that describes a whole Cell cites that Cell's range; a Claim spanning Cells carries one Citation per Cell; an over-narrow citation is rejected, retried with a clear reason, then dropped. See `spec.md` (Citation coverage rule; stories 9-12).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] The output schema lets a Claim carry several Citations, one per Cell, and marks a Claim as describing a Cell
- [ ] A Claim marked as describing a Cell passes only if it cites that Cell's full range
- [ ] An over-narrow citation is fed back on the existing retry path with a specific reason, then dropped if it still fails; the dropped count is shown
- [ ] Prompts explain the rule, with no domain vocabulary
- [ ] Rendering and Markdown download show every Citation of a multi-Cell Claim as separate links
- [ ] Offline tests with the fake LLM cover: whole-Cell Claim with full range accepted, with a narrow range rejected, retry recovers it, multi-Cell Claim renders one link per Cell
