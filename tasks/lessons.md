# Lessons

## 2026-11-11 - Final proof review and inherited workers
- Before using the shared Live process, inspect remaining T3 workers as well as Git worktrees;
  a settled parent can leave a child mutating the same fixture. Coordinate a stop before proofs.
- An MCP timeout cancels the await, not necessarily the native mutation. Abort subsequent writes,
  retain ownership immediately and write evidence in finally. Never accept transport errors as an
  expected feature refusal; match the specific code and message for negative checks.
- Apply-mode safety restoration must enclose discovery as well as writes. Verify the resulting
  policy and fresh object inventory after partial/unknown cleanup; never retry a mutation blindly.
- Check the actual device tree/path implementation before declaring a path-format gap. The 505
  kit's nested Simpler is reachable with existing alternating device/chain steps.

## Wording must match what actually happened (2026-11-10)
- Mistake: said "I'll start on the M1 bridge now" in a turn with no tool calls; the owner later
  asked why no agents were running. Future-tense wording implied work in progress that wasn't.
- Rules:
  - Don't say "starting" or "working on" unless a tool call that does the work is in that same turn.
  - Separate what was done, what was verified, and what is only planned. Name which is which.
  - State the exact scope of a check ("ran the reader on one 72 KB Set"), not a general "works".
  - Don't repeat facts I haven't checked this session (e.g. CI platform matrix) as if verified.

## 2026-11-10 - Don't ask the owner to do what I can do
- Correction: I asked the owner to close/start Ableton and re-select the control surface at every step. They said not to hold my hand.
- Rule: start, kill and reinstall Live myself (Basic is disposable). Ask only for credentials, payments, account and release decisions.
- Related: I asked for a Live close before the code to install existed. Finish the code first, then do the lifecycle steps in one go.

## 2026-11-10 - Real Live finds what fakes cannot
- Fakes passed while real Live 12.2 had no `ctypes` (script failed to load) and reset `generation` to 1 on a Set change.
- Rule: for anything importing outside the core stdlib or holding per-session state, run one real-Live load/Set-change check before calling it done, and record the module list from Log.txt.

## 2026-11-10 - Don't over-test with fakes
- Correction: stop testing against a fake Ableton; roughly one test per feature while developing.
- Rule: prove features in real Live via scripts/live_*.py. Add at most one small test per feature. Do not grow the fake-based suite.

## 2026-11-11 - Scope creep and agent overuse
- Correction: owner asked for a simple MCP; I ran probes per API, per-feature fake tests and many high-effort agents, burning ~15 h of usage across accounts.
- Rules: obey "testing at the end" in every brief (no fake tests, no per-area proofs); default to Sonnet/medium, not Opus/high; ask before changing an owner instruction ("use Sol to help" means alongside, not replacing); never run two agents against one Live (index shifts cause false failures); don't enable `dev_probes`/`read_only:false` without restoring it, tests read the real config.
