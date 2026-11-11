# Handoff (2026-11-11, catchup verification)

Repo `zdhoward/abletonlivemcp` (PRIVATE). Not released: `pyproject` still `0.0.1`, last tag `v0.1.0`.

## State
- Six fast-track batches are merged: 57 tools, 30 core; serialized core listing 38,238 UTF-8 bytes (40,000 limit). Contract: `docs/plans/v2-contracts.md`.
- Merged serial Live 12.2 evidence: 34 pass, 3 unsupported, zero failed/blocked scenarios. Existing passing evidence was retained; focused repair runs covered clips, control and drums. `dev-drums` includes nested Simpler read/write/readback and restores retrigger. The wrong-device checks require exact ValueError messages.
- Unsupported paths: plugin preset selection, FX rack chain insertion, custom drum-pad load/build and pad copy. A scenario's supported refusal is not proof of musical capability. The stock kit's nested Simpler is reachable via `[0, "pad:36", 0, 0, 0]`; the earlier claimed path-grammar gap was incorrect.
- Offline baseline: 385 tests passed; 3 added host orchestration boundary tests passed, with affected chain/undo tests (23 total). Ruff passed. Wheel 0.0.1 built with 49 bundled remote modules. No new fake Live tests.
- Policy tests now isolate private config. Proof runner has `--scratch-writes` with safe defaults restored in finally, stops all further scenarios on unknown outcomes, and preserves scratch evidence on abort/interruption. Cleanup defaults to dry-run and restores policy even when apply-mode discovery fails.
- Real audio Set read-only validation: 23 sample references, all with absolute/relative paths and recorded sizes; classification `referenced`. No private Set/sample content committed.
- Final cleanup removed 9 scratch tracks, 3 returns, 1 cue and 6 MIDI exports. Fresh dry-run: empty target list and zero scratch cues; config readback: read_only true, dev_probes absent.
- Previous parent's remaining worker was stopped after detecting concurrent scratch use; no other proof process remains. All subsequent Live work was serial. Only main and its origin tracking branch exist; no open GitHub issues or PRs.

## Remaining blocker
Save/reopen Set-label persistence is unproved. Actual bridge `save_document` call returned `ValueError: unknown or unclassified method` (not applied). No desktop control capability is available in this session. Once desktop automation is available, save an isolated scratch Set containing a song label, reopen it, and read the same label. Do not claim persistence from the existing in-session roundtrip. No owner sample files are needed.

## Next-session operations
Use `tasks/todo.md` current ledger; historical checklists are superseded by the fast-track plan. Reuse successful checks. For a necessary focused proof, set isolated ALS/file/data roots and run `scripts/live_v2_final.py --scratch-writes --only <ids>`; dependencies are included. Never share Live with another worker. Afterward run `scripts/live_final_cleanup.py --dry-run`, then `--apply`, then read back the empty inventory and safe config. Never save the disposable Basic Set.

## Owner-only
Package/registry names and accounts, public flip, release/version/tag approval, permanent `read_only:false`. Development metadata remains 0.0.1 pending release approval. Generated ADG/macros, simulator/evals and WAV analysis remain explicitly deferred scope; competitor claims need primary-source verification immediately before publication.

## Decisions
- Testing only at the end, no new fake-Live tests (`tasks/lessons.md`). Core cuts: simulator, generated .adg presets, crash-prone arrangement ops (split/move/take lanes/arrangement automation).
