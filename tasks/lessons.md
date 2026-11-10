# Lessons

## Wording must match what actually happened (2026-11-10)
- Mistake: said "I'll start on the M1 bridge now" in a turn with no tool calls; the owner later
  asked why no agents were running. Future-tense wording implied work in progress that wasn't.
- Rules:
  - Don't say "starting" or "working on" unless a tool call that does the work is in that same turn.
  - Separate what was done, what was verified, and what is only planned. Name which is which.
  - State the exact scope of a check ("ran the reader on one 72 KB Set"), not a general "works".
  - Don't repeat facts I haven't checked this session (e.g. CI platform matrix) as if verified.
