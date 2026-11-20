# 06: Eval Cases and generality fixture for the risk classes

**What to build:** `just eval` checks that the real model surfaces the risk classes for the right Audience, that it does not claim a print-only check halts the run, and that the checklist generalises to an unrelated Notebook. See `spec.md` (Testing Decisions; stories 36-39).

**Blocked by:** 03, 04

**Status:** done

- [ ] New Eval Cases: the manager doc surfaces the reassigned constant, the overwrite writes or the unused constant; the agent doc has at least one invariant and one runnable check, each cited; the developer doc raises the name-versus-ordering mismatch as a Concern
- [ ] A case that fails if the agent doc claims a print-only check halts the run
- [ ] The unrelated fixture Notebook gains equivalent planted risks, and the vocabulary-leak check still runs for every Audience
- [ ] A clean-fixture case checks that no Concerns are invented
- [ ] The eval-case integrity test in the offline suite covers the new cases
