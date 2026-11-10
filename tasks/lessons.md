# Lessons

## Wording must match what actually happened (2026-11-10)
- Mistake: said "I'll start on the M1 bridge now" in a turn with no tool calls; the owner later
  asked why no agents were running. Future-tense wording implied work in progress that wasn't.
- Rules:
  - Don't say "starting" or "working on" unless a tool call that does the work is in that same turn.
  - Separate what was done, what was verified, and what is only planned. Name which is which.
  - State the exact scope of a check ("ran the reader on one 72 KB Set"), not a general "works".
  - Don't repeat facts I haven't checked this session (e.g. CI platform matrix) as if verified.

## 2026-11-10 - Don't over-test with fakes
- Correction: stop testing against a fake Ableton; roughly one test per feature while developing.
- Rule: prove features in real Live via scripts/live_*.py. Add at most one small test per feature. Do not grow the fake-based suite.
