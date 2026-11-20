# Spec: Trustworthy, complete Audience Docs and a reproducible repo

Status: ready-for-agent

Vocabulary follows `GLOSSARY.md` (including Supported Citation and Coverage).

## Problem Statement

A reader of an Audience Doc needs to be able to act on it. Three things stop that from being true for every Audience:

- A Claim can have a Verified Citation and still say something its own quote does not support. Verification proves the quoted text exists; it does not prove the Claim follows from it.
- The docs can leave out the risks that matter most to their Audience. A manager can be shown minor concerns while a production-table overwrite goes unmentioned; an AI coding agent can be given only a handful of invariants and no runnable way to check a change.
- Citations can be too coarse to check. A one-line citation can sit behind a statement about a whole Cell, so the reader clicks through and still cannot confirm the statement. There is also no way to see which parts of the Notebook a doc never touches.

Separately, someone who clones the repository cannot reproduce the generated docs or open their citation links, because the sample Notebook is not in the repository, and starting the app takes several manual steps.

## Solution

Every Claim in every Audience Doc is a Supported Citation: its quote exists in the cited lines, the cited Line Range covers what the Claim asserts, and the quote actually backs the Claim. Claims that fail any of these checks are dropped or retried, and the count is shown.

The docs search for a generic class of risks in every Notebook: names that disagree with behaviour, constants defined but never used, constants reassigned mid-run, destructive overwrite writes, and checks that only print. These surface in each Audience Doc in the register that suits it. A minimum number of Concerns is expected, waived when the Notebook shows no such risk.

Each Audience Doc reports its Coverage, so a reader can see which Cells and lines no Claim cites.

The sample Notebook and its data live in the repository, the app starts with a single command, and the README, screenshots and generated docs are consistent with one another and reproducible by a reader.

## User Stories

### Trust in Claims
1. As a manager, I want every statement about the Notebook to follow from the lines it cites, so that I can rely on it without reading code.
2. As a developer, I want a Claim whose quote does not back it to be removed, so that I am never misled by a statement that merely sits next to real code.
3. As an AI coding agent, I want Claims that describe behaviour (such as "halts the run") to be dropped when the cited code only prints, so that I do not rely on a safeguard that does not exist.
4. As a reader, I want the number of dropped Claims shown on each doc, so that I know the output was filtered and by how much.
5. As a maintainer, I want unsupported Claims retried once with the failing Claims fed back (the decision model gives a score, not a reason), so that a flaky generation is not discarded when it could be repaired.
6. ~~As a maintainer, I want a doc with dropped Claims left uncached~~ — superseded: docs with dropped Claims are cached to avoid repeat cost (a documented compromise in the README); Regenerate retries.
7. ~~As a maintainer, I want the support check to cost no more than one extra LLM call per Audience Doc~~ — superseded: the Support Check is one small decision-model call per Claim (Jev on OpenRouter), run concurrently.
8. As a maintainer, I want the support check to be cached together with its Audience Doc and invalidated when its question text, decision model or threshold changes, so that I do not pay twice for the same result.

### Citation granularity
9. As a developer, I want a Claim about a whole Cell to cite that Cell's range, so that clicking it highlights everything the Claim is about.
10. As a developer, I want a one-line citation accepted only for a one-line assertion, so that I can check the Claim at a glance.
11. As a reader, I want a Claim that spans several Cells to carry one Citation per Cell, so that each link opens exactly the evidence for that part.
12. As a reader, I want a rejected over-narrow citation retried with a clear reason, so that a good Claim is not lost to a formatting choice.

### Risks surfaced per Audience
13. As a manager, I want destructive writes (such as overwrite-mode saves to shared tables) described in business terms with their consequence, so that I understand the stakes.
14. As a manager, I want settings that change partway through a run called out, so that I know the outcome depends on more than the visible configuration.
15. As a developer, I want a constant that is defined but never used flagged as a Concern, so that I do not assume it constrains behaviour.
16. As a developer, I want a name that disagrees with what its code does flagged as a Concern, so that I am not misled by it.
17. As a developer, I want a constant reassigned after its first use flagged, with both locations cited, so that I know which value applies where.
18. As an AI coding agent, I want a list of invariants I must preserve, each cited, so that my change does not break them.
19. As an AI coding agent, I want risky areas listed with the reason each is risky, so that I can take extra care there.
20. As an AI coding agent, I want concrete checks I can run to confirm a change is safe, each cited, so that I can verify my work.
21. As an AI coding agent, I want checks that only print, rather than stop the run, identified as such, so that I do not treat them as guards.
22. As a reader of a clean Notebook, I want no invented Concerns, so that every Concern I see is real.
23. As a maintainer, I want the risk checklist to be generic and domain-free, so that it works for any Notebook.

### Coverage
24. As a reader, I want each Audience Doc to report the share of Cells and lines it cites, so that I can see what it leaves out.
25. As a reader, I want the Cells no Claim cites listed by number with links, so that I can inspect them myself.
26. As a maintainer, I want Coverage included in the Markdown download, so that the information travels with the document.
27. As a maintainer, I want Coverage to be informational only, so that it never causes padding or a rejection.

### Reproducibility
28. As a reviewer, I want the sample Notebook and its data in the repository, so that I can run the app on it immediately.
29. As a reviewer, I want every citation link in the committed docs to open real lines, so that I can verify them.
30. As a user, I want to start the app with one command, so that I do not assemble steps by hand.
31. As a user, I want `just` to remain available but optional, so that people without it are not blocked.
32. As a reader of the README, I want clear, correctly numbered sections and a layout section that does not interrupt the design decisions, so that I can follow it.
33. As a reviewer, I want screenshots next to the screen recording, so that I can see the app without playing a video.
34. As a reviewer, I want the committed Audience Docs to come from the strongest model available through the same configuration, so that they show the app at its best.
35. As a reviewer, I want the README to record which model produced the committed docs, so that I can judge them fairly.

### Evaluation
36. As a maintainer, I want Eval Cases for the risk classes above, so that quality regressions are caught by `just eval`.
37. As a maintainer, I want an Eval Case that fails if the agent doc claims a print-only check halts the run, so that the support check is tested against a known false statement.
38. As a maintainer, I want the unrelated fixture Notebook to carry equivalent planted risks, so that the checklist is shown to generalise.
39. As a maintainer, I want the offline suite to script both generation and support-check responses, so that these behaviours are tested without keys or network.

## Implementation Decisions

- **Support check**: after generation and Citation verification, each Claim is scored by a decision model (Jev, OpenRouter-only, independent of the generation provider): the cited quotes are the state, the Claim is the question, and the returned probability is compared with a threshold of 0.5. Unsupported Claims join the existing retry-once-then-drop path. One call per Claim, run concurrently.
- **Citation coverage rule**: the Citation schema stays `(cell, start line, end line, verbatim quote)`. A Citation passes only if its range lies in the Cell, the quote appears in it, and the range is consistent with the Claim's kind: a Claim marked as describing a Cell must cite that Cell's full range; any other Claim may cite a narrower range but the support check judges whether it is enough. A Claim spanning Cells carries a list of Citations, one per Cell.
- **Risk checklist**: a short, generic list is added to every Audience prompt: names that disagree with behaviour; constants defined but never used; constants reassigned after first use; overwrite or destructive writes; checks that print but do not stop the run; behaviour defined outside the Notebook. Each prompt says how to express a finding for its Audience (business consequence for managers, code reality for developers, a precaution or check for agents).
- **Concern minimum**: each prompt requires the model to work through the checklist and report every finding it supports. A minimum applies only when the checklist yields findings; the model may report none for a clean Notebook, and the schema allows an explicit "no findings" statement.
- **Coverage**: computed deterministically after verification from the Citations that survive, as the Cells and lines cited at least once. It is attached to each Audience Doc and shown as a short summary with uncited Cells linked to the Source Viewer. It does not feed back into generation.
- **Cache keys**: add the support-check question text, decision-model alias and threshold and the checklist text so a change to either invalidates stored docs. The existing key components remain.
- **Prompts**: remain one file per Audience plus one for the support check, loaded at runtime, and contain no domain vocabulary.
- **Repository contents**: the sample Notebook and its data are committed under an examples directory; the default path in the app points there; the ignore rules no longer exclude it. Committed Audience Docs cite that location.
- **Start-up**: a single documented command starts the app and syncs dependencies if needed; the existing `just` recipes remain as optional shortcuts.
- **README**: fix the duplicate section number; move Layout after the design decisions; add a design decision for support checking and Citation granularity; move the semantic-verification item out of Next Steps; record the model used for the committed docs; add screenshots.
- **Provider**: no changes to configuration. The committed docs are produced by changing the model setting only.

## Testing Decisions

- A good test drives the HTTP app with a fake LLM client and asserts on what the user sees (rendered docs, dropped counts, Coverage summary, downloads), not on internal functions.
- **Offline seam**: the existing HTTP-app-with-fake-LLM seam. The fake is extended to return scripted generation and support-check responses so each behaviour is covered: an unsupported Claim is dropped, a retry recovers a Claim, an over-narrow citation is rejected, Coverage is correct for a known Notebook, a "no findings" response on a clean Notebook is accepted, and the Markdown download includes Coverage.
- **Configuration and start-up**: verified through the existing config tests and a check that the default Notebook path exists and parses.
- **Live seam**: the existing `just eval` runner. New Eval Cases target: the reassigned constant, the overwrite writes and the unused constant surfaced in the manager doc; at least one invariant and one runnable check in the agent doc; the name-versus-ordering mismatch raised as a Concern in the developer doc; no Claim that a print-only check halts the run.
- **Generality**: the unrelated fixture Notebook gains equivalent planted risks, and the vocabulary-leak check continues to run for every Audience.
- **Prior art**: the existing eval-case integrity test, which confirms each case's expected Citation points at real lines, applies to the new cases unchanged.

## Out of Scope

- Chunking or map-reduce for Notebooks beyond the model's context window.
- Fix proposals, a human-in-the-loop gate, CI mode and observability integrations.
- Treating Coverage as a pass/fail threshold.
- Prompt-injection evals.
- Changes to provider selection or logging; key resolution changes only to require `OPENROUTER_API_KEY` for the Support Check.

## Further Notes

- The Support Check costs one small paid call per Claim; cache behaviour and the retry limit matter.
- If a Notebook is clean, the checklist must not force invention; this is what the generality fixture and the "no findings" path protect.
- Possible ADR once implemented: verifying that a quote supports its Claim, a hard-to-reverse choice with a real trade-off between cost and a second source of error.
