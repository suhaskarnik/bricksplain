# 05: Coverage on every Audience Doc

**What to build:** Each Audience Doc shows its Coverage: the share of Cells and lines at least one Claim cites, and the Cells no Claim cites, linked to the Source Viewer. It is informational only and also appears in the Markdown download. See `spec.md` (Coverage; stories 24-27; Coverage in `GLOSSARY.md`).

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Coverage is computed deterministically after verification from the surviving Citations, per Audience Doc
- [ ] The page shows cited Cells and lines as a share, and lists uncited Cells by number with Source Viewer links
- [ ] The Markdown download includes the same summary
- [ ] Coverage never causes a rejection and is not passed back to the LLM
- [ ] Offline tests over a known small Notebook check the shares and the uncited Cell list, including a Claim with several Citations and overlapping ranges counted once
