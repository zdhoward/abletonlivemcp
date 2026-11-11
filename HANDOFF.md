# Handoff (2026-11-10, end of study & knowledge base sprint)

Repo: `zdhoward/abletonlivemcp` (PRIVATE until the owner is happy with v1). Branch `main`.

## State
- **Bridge (M1)**: Remote Script `remote_script/AbletonLiveMCP/` (loopback `127.0.0.1:9877`, newline-framed JSON, main-thread queue via `update_display`) + MCP server `src/abletonlivemcp/server.py` (35 core tools + 3 conditional knowledge tools = 38 tools total) + installer `python -m abletonlivemcp.install "<User Library>"`.
- **Offline `.als` (M2)**: reader, sample extraction, `scan_projects`, tools `als_summary`, `als_usage_index` (`src/abletonlivemcp/als/`).
- **Knowledge Base (M6/M3/M5)**: Comprehensive 31-page knowledge base in `knowledge/` backed by 20 raw collector research files in `research/raw/`. All pages use evidence tags (`**FACT**`, `**CONVENTION**`, `**OPINION**`) and are dynamically indexed and queried via `knowledge_list`, `knowledge_search`, and `knowledge_read` MCP tools (`src/abletonlivemcp/knowledge.py`).
- **Target Environment**: Owner's Live is **12.2.0** (on Windows; 12.3+ APIs like `insert_device` and `DrumChain.in_note` are unavailable; devices load through the browser route `load_item`). Sandbox folder: `S:\AbletonMCP\projects`; User Library: `D:\Beatz\DAWs\Ableton 12\User Library`.

## Comprehensive Knowledge Base Inventory (31 Pages)
1. **Core Instruments & Stages**: `vocals.md`, `drums.md`, `busses-mixing.md`, `guitar-bass.md`, `keys-synths.md`, `mastering.md`
2. **Genre-Specific FX Chains**: `rock.md`, `hip-hop.md`, `pop.md`, `acoustic.md`, `edm.md`
3. **Genre Songwriting, Melody & Production**: `rock-songwriting-production.md`, `hip-hop-songwriting-production.md`, `pop-songwriting-production.md`, `acoustic-songwriting-production.md`, `edm-songwriting-production.md`
4. **Genre MIDI FX & Programming**: `rock-midi-fx.md`, `hip-hop-midi-fx.md`, `pop-midi-fx.md`, `acoustic-midi-fx.md`, `edm-midi-fx.md`
5. **Drum Machines, Patterns, Fills & Cymbals**: `drum-machines.md`, `drum-patterns.md`, `drum-fills-cymbals.md`
6. **Studio Organization & Engineering Habits**: `studio-organization-templates.md`, `producer-engineer-habits.md`
7. **Mixing Troubleshooting & Diagnostic Frameworks**: `mixing-troubleshooting.md`, `mixing-diagnostics-decision-tree.md`
8. **VST Processors, Instruments & Stock Translation**: `vst-processors.md`, `vst-instruments-stock-mappings.md`

## Verified in Real Live 12.2 (2026-11-10)
- Remote Script handshake, browser roots/list/search, `load_item` (Compressor to a new track), device parameter read/write with readback (tested on native devices and VST3 Nexus), track create/rename/color, tempo, range and index guards. Real stdio smoke test passed (`scripts/stdio_smoke.py`).
- Real clip and transport checks (`scripts/live_clip_test.py`): play/stop/get_transport, create/rename/fire scene, create MIDI clip, write/read 3 notes, fire/stop clip, bad-index and bad-pitch guards, settled transport checks.
- Jev judge layer evaluated (`src/abletonlivemcp/judge/`) across 40 real OpenRouter calls on synthetic names.
- Real project scan (`scan_projects`) verified on `S:\AbletonMCP\projects` (1 Set, 11 device instances including 4 VST3 Nexus instances, 0 sample references).

## Pre-Release Audits Completed
- `docs/plans/audits/hardening.md`: Local bridge authentication, request timeouts, and device indexing safety.
- `docs/plans/audits/reusability.md`: Packaging, wheel self-containment, and stranger onboarding.
- `docs/plans/audits/scope.md`: Scoping v1 to stock-first chain building and Session View assistant.

## Validation Status
- **pytest**: 332 passed in 2.47s (100% pass rate).
- **ruff**: clean (0 lint errors).
- **knowledge stdio smoke test**: verified tool execution (`scripts/knowledge_stdio_smoke.py`).
- **knowledge page parsing**: all 31 pages parsed with valid section counts and line numbers.

## Next Steps
1. **M6 Chain Builder / Browser Loading**: Connect the curated knowledge base and role adapters (`adapters.py`, `resolve.py`) to browser-based device loading (`load_item`) in real Live 12.2.
2. **Rules-first Jev Combination**: Implement rules-first classification with Jev fallback for ambiguous plugin names and sample roles.
3. **M3 Drum Rack Builder**: Build standard 16-pad drum rack generator when audio samples are provided.
4. **M4 Rack Grouping & Macro Mapping**: Implement parameter macro mapping within Live 12.2 capabilities.

## Owner-Only Actions
- Remove unsaved `ALMCP test` track/scene in open `Basic` Set if desired.
- Provide audio clip sample sets for M3/M4 drum rack testing.
- Public release and version publishing decisions.

## Key Files
- Knowledge index: `knowledge/INDEX.md`
- Task tracking & plan: `tasks/todo.md`
- Lessons learned: `tasks/lessons.md`
- Architecture & decisions: `docs/vision.md`, `docs/research-deep-review.md`
- Audits: `docs/plans/audits/`
