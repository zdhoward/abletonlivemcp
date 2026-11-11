# Handoff (2026-11-11, v2 surface built and merged; final Live proof 32/37 passing or demoted)

Repo `zdhoward/abletonlivemcp` (PRIVATE). Not released: `pyproject` still `0.0.1`, last tag `v0.1.0`.

## State
- All 6 batches of `docs/plans/v2-fast-track.md` are merged on `main`: 57 tools (30 core, core listing under the 40,000-byte budget, schema noise pruned in `server.py`). Contract: `docs/plans/v2-contracts.md`.
- Final Live 12.2 proof (`scripts/live_v2_final.py`, evidence `docs/release/v2-fast-track.md/.json`): 30 pass, 2 unsupported (demoted), 3 fail, 2 blocked of 37 scenarios.
  - Still failing: `control-tracks-mixer` (blocks `control-undo`, `control-duplicate-delete`), `dev-drums`, `clips-duplicate-delete`.
  - Cause of earlier round-2 failures: two agents shared one Live and shifted track indexes. Run the remaining scenarios ALONE: `live_v2_final.py --only <ids>`.
- Two background agents (Opus: clips/notes/arrangement/control; Sol: library/als/labels/dev) were still editing when this was written. Their uncommitted edits to scenarios, runner, `dom_browser.py`, `resources.py` are committed here as a checkpoint; check `git log` for their later commits.
- Suite: 383 pass, 2 fail (`test_chain_tools::test_policy_refusal...` stub lacks `_create_tracks`; `test_undo_step::test_probe_run...` fails because the real bridge config currently has `dev_probes: true`).

## Before release (do first)
1. Restore the real config `~/.abletonlivemcp/bridge.json`: `read_only: true`, remove `dev_probes`. Then rerun pytest; fix the stub in `tests/test_chain_tools.py` if it still fails.
2. Rerun only failing scenarios alone in Live (restart with `scripts/live_restart.ps1 -Reinstall`). Anything still failing: make it `refused:unsupported` and note it. Delete leftover ALMCP-FINAL tracks/returns (`scripts/live_final_cleanup.py --dry-run` first).
3. Set env for the proof: `ABLETONLIVEMCP_ALS_ROOTS`, `ABLETONLIVEMCP_DATA_DIR`, `ABLETONLIVEMCP_FILE_ROOTS`.
4. Update README/CHANGELOG tool list, bump version.

## Owner-only
Package/registry names and accounts, public flip, release tag, permanent `read_only:false`. Gated or unproven on 12.2 are listed in the proof evidence.

## Decisions
- Testing only at the end, no new fake-Live tests (`tasks/lessons.md`). Core cuts: simulator, generated .adg presets, crash-prone arrangement ops (split/move/take lanes/arrangement automation).
