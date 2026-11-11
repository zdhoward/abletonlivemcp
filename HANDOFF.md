# Handoff (2026-11-10, end of v1 hardening: M1a + M1b done and proven in real Live)

Repo: `zdhoward/abletonlivemcp` (PRIVATE until the owner is happy with v1). Branch `main` at the wrapup commit; the
feature head is `4cd4e4b` plus this docs commit. **Nothing has been pushed or tagged by this session** (see Status).

## What this session did
Executed `docs/plans/v1-public-release.md` milestones M1a and M1b through delegated builders (Claude Sonnet 5.5 at
medium for builds, Opus 5.5 for the security review; Codex hit its quota mid-run), then proved the result in real Live 12.2.0.

- **M1a**: protocol-2 mutually authenticated, bounded bridge (`bridge.py` host side, `core.py` Remote Script side);
  transactional backup-preserving installer (`install.py`) and private config (`config.py`, `~/.abletonlivemcp/bridge.json`).
  Independent review found no blockers; 9 findings fixed (outcome text, readable refusals, SID via token not `whoami`,
  reader agreement, 2 s auth deadline, `BridgeBusy`, backup pruning, no `config.py` in the Live folder, cleanup can't hide errors).
- **M1b-01**: `safety.py` dispatch contract: writes need object references + `generation`, read-only policy read from
  `bridge.json` (missing/unreadable = read-only; only literal `false` enables writes), bounded lease (max 60 s).
  Refusals return a SUCCESSFUL result `{"refused":true,"applied":false,"code":...}`; the host treats it as an error.
- **M1b-02**: `operations.py` bounded browser paging/search, load preconditions, tick-driven load state machine
  (`pending/ready/failed/unknown`, quarantine on doubt, never retried).
- **M1b-03**: typed plans/receipts (`models.py`, `chain.py`), stop-on-failure chains, only the v1 core is registered
  (27 tools; knowledge/als/classifier/gear tools are no longer registered), local rules judge is the default.
- **M1b-04**: red tests migrated to the new contracts; 190 clip tests collapsed to 94; research tests detached.
- **M1b-05**: live scripts converted (assert, nonzero exit, `--allow-writes`); real-Live run recorded in
  `docs/release/m1b-live-evidence.md`. Two real-Live defects found and fixed: no `ctypes` in Live's Python
  (lazy imports + documented weaker fallback), and `generation` restarting at 1 after a Set change (random start).
  Append placement is now verified per load (`select_device`, last-position check in the tick).

## Status
- Branch/commits: `main` has everything; feature branches and worktrees were deleted after merge.
- PRs: none open. No push, no tag. Last tag is `v0.1.0` (older). `pyproject` version is still `0.0.1`.
- Validation: 255 tests pass, ruff clean. Real Live 12.2.0: chain EQ Eight, Compressor, Saturator, Reverb loads in order
  (complete receipt); write/clip/stdio scripts pass; lease and stale-reference/generation refusals observed.
- Live is running with the new script installed in `D:\Beatz\DAWs\Ableton 12\User Library\Remote Scripts\AbletonLiveMCP`.
  `bridge.json` has `read_only: true` (writes refused until the owner sets `false`; applies without restart).
- Backups of earlier installs sit OUTSIDE the library in `D:\Beatz\DAWs\Ableton 12\AbletonLiveMCP-*` (safe to delete).

## Decisions
- Claude starts/closes/reinstalls Live itself (see memory `live-lifecycle-autonomy`); Basic is disposable.
- Lifecycle control (kill/launch Live) stays as scripts, not MCP tools. Broad "run Python in Live" scope is a later,
  opt-in milestone, not v1.
- Live-side secret-file check is weaker than host side because Live has no `ctypes`; documented in
  `docs/release/bridge-protocol.md`. Host and installer still enforce the owner-only DACL.

## Remaining work (ordered)
1. Optional Sol review of `safety.py`, `operations.py`, chain receipts and the host/Remote Script seam (owner said wait).
2. DONE (catchup): missing handler params now give a readable refusal (`_Params` in `handlers.py`); the handshake advertises `dispatch.methods`. Both verified in real Live.
3. Unproved items listed in `docs/release/m1b-live-evidence.md` (target reorder, second-process lease, responsiveness,
   non-stock loads, one unexplained "connection lost" shortly after Live launched, OneDrive reparse points).
4. (done, see 2)
5. Remaining plan milestones after M1b (M2+ stock discovery, docs/release, packaging, tagging, public release): owner decisions.
6. Reconnect the knowledge/als tools later behind their own milestone (they were unregistered for v1).
7. Register `abletonlivemcp` from the `main` checkout in the owner's MCP client (no client config references it today).

## Owner-only
- Setting `read_only: false` when they want the assistant to write; release/tag/public decisions; sample files for M3/M4.

## Knowledge base (unchanged, 31 pages in `knowledge/`, raw evidence in `research/raw/`)
Core instruments/stages, five genre FX chains, genre songwriting, MIDI FX, drum machines/patterns/fills, studio
organization, mixing diagnostics, VST stock translations. Index: `knowledge/INDEX.md`. Not exposed by the v1 tool surface.

## Key files
- Plan: `docs/plans/v1-public-release.md`; evidence: `docs/release/m1b-live-evidence.md`; protocol: `docs/release/bridge-protocol.md`
- Safety contract: `remote_script/AbletonLiveMCP/safety.py` (module docstring); load state machine: `operations.py`
- Tracking: `tasks/todo.md`, `tasks/lessons.md`; memory: `live-lifecycle-autonomy`, `bridge-latency-floor`
