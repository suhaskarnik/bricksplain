# 07: Regenerate committed docs, README and screenshots

**What to build:** The repo shows the app at its best and a reviewer can follow it end to end: committed Audience Docs produced with the strongest reachable model through the existing model setting, a README that matches the shipped behaviour, and screenshots beside the recording. See `spec.md` (Repository contents, README; stories 28-35).

**Blocked by:** 01, 02, 03, 04, 05, 06

**Status:** ready-for-agent

- [ ] The three Audience Docs are regenerated from the committed sample Notebook and every citation link in them opens real lines
- [ ] The README records which model produced them and how to switch models
- [ ] The README fixes the duplicate section number, moves Layout after the design decisions, adds a design decision for support checking and Citation granularity, and moves semantic verification out of Next Steps
- [ ] Screenshots of the input page, an Audience Doc with its Coverage, and the Source Viewer on a citation are added beside the recording
- [ ] Eval results for the strongest and a weaker model are summarised in the README
- [ ] `just test` passes offline; no secrets appear in any committed file
