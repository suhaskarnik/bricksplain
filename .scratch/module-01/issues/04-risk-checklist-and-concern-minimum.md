# 04: Generic risk checklist in every Audience prompt

**What to build:** Each Audience Doc surfaces the classes of risk a Notebook can hide, expressed for its Audience: business consequence for managers, code reality for developers, a precaution or runnable check for agents. A clean Notebook yields an explicit "no findings" rather than invented Concerns. See `spec.md` (Risk checklist, Concern minimum; stories 13-23).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Every Audience prompt includes the same generic checklist: names that disagree with behaviour; constants defined but never used; constants reassigned after first use; overwrite or destructive writes; checks that print but do not stop the run; behaviour defined outside the Notebook
- [ ] Each prompt says how to express a finding for its Audience; the agent prompt requires cited invariants, risky areas with reasons, and runnable checks
- [ ] A minimum applies only when the checklist yields supported findings; the schema allows an explicit "no findings" statement that renders visibly and needs no Citation
- [ ] The checklist text is part of the cache key
- [ ] Prompts and application code contain no domain vocabulary
- [ ] Offline tests: scripted responses with findings render as Concerns with Citations; a "no findings" response on a clean Notebook is accepted and shown; editing the checklist invalidates the cache
