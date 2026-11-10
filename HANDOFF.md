# Handoff (2026-11-10, end of catchup)

Repo: `zdhoward/abletonlivemcp` (PRIVATE until the owner is happy with v1). Branch `main`.

## State
- **Bridge (M1)**: Remote Script `remote_script/AbletonLiveMCP/` (loopback `127.0.0.1:9877`, newline-framed JSON, main-thread queue via `update_display`) + MCP server `src/abletonlivemcp/server.py` (27 tools) + installer `python -m abletonlivemcp.install "<User Library>"`.
- **Offline `.als` (M2)**: reader, sample extraction, `scan_projects`, tools `als_summary`, `als_usage_index` (`src/abletonlivemcp/als/`).
- **Owner's Live is 12.2.0** (NOT 12.4; earlier notes were wrong, corrected in `docs/vision.md`). 12.3+ APIs (`insert_device`, `insert_chain`, `DrumChain.in_note`) are unavailable; load devices through the browser (`load_item`).
- Owner folders: sandbox projects `S:\AbletonMCP\projects` (never touch anything else); User Library `D:\Beatz\DAWs\Ableton 12\User Library` (script installed in `Remote Scripts\AbletonLiveMCP`).

## Verified in REAL Live 12.2 (2026-11-10)
Handshake, browser roots/list/search, `load_item` (Compressor to a new track), device parameter read/write with readback (also on VST3 Nexus), track create/rename/color, tempo, range and index guards. MCP server launched over real stdio and called tools (`scripts/stdio_smoke.py`).

## NOT verified in real Live
Transport, scenes, clips, notes handlers (fake-tested only; note API calls `add_new_notes`/`MidiNoteSpecification` are the riskiest). Loading from `plugins`, drum kits, racks. Sample extraction from a real Set (only synthetic; `Basic.als` has no samples).
The script in the User Library is current, but the running Live still holds the older code until restarted.

## Next steps
1. Restart Live, open `Basic.als`, then run the transport/scene/clip checks (write a `scripts/live_clip_test.py` like `scripts/live_write_test.py`; it must touch only new tracks/scenes) and fix whatever fails. Then tag `v0.1.0`.
2. M3 drum rack builder and M4 macro mapping need sample files (list: `docs/research-deep-review.md` section 8). M6 vocal-chain building needs no samples and can start now via the browser route.
3. Add `delete_track`/`delete_clip` only with an explicit design (currently none by choice).

## Owner-only
- Remove the unsaved `ALMCP test` track in the open `Basic` Set (Ctrl+Z, or close without saving; `Basic.als` on disk was never modified).
- Provide a Set with audio clips plus sample files for M3/M4.
- Make repo public / releases.

## Validation
`pytest` 244 passed, `ruff check .` clean (local, Windows, Python 3.13 in `.venv/`). CI: see latest run after push.

## Key files
`docs/vision.md` (decision log), `tasks/todo.md` (plan + catchup ledger), `tasks/lessons.md`, `docs/research-deep-review.md`, `remote_script/AbletonLiveMCP/`, `src/abletonlivemcp/`, `scripts/`.
