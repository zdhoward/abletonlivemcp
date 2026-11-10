# Plan (owner approved 2026-11-10; target Live 12.2+, see `docs/vision.md` decision log)

Source of intent: `docs/original-prompt.md`. Requirements: `docs/vision.md`.

## Open architectural questions (to verify by research before building)

The Live Object Model (LOM) is what a Remote Script can reach. Several of the owner's use cases may exceed it:

1. **Macro mapping & grouping (UC4)**: LOM exposes rack macros' values but, to my knowledge, not creating Macro->parameter mappings or grouping existing devices into a rack. Likely route: generate Live preset files (`.adg`/`.adv`, gzipped XML) with the mapping baked in and load them via the browser. Verify.
2. **Reading past projects (UC1)**: `.als` files are gzipped XML, so parse them offline (no running Live needed). Verify format for Live 11/12.
3. **Drum rack fill (UC1/UC5)**: loading samples to pads via browser/`Simpler` vs. generating `.adg` drum rack presets. Verify standard (GM-like) pad layout.
4. **Plugin color tags (UC2)**: Live's color tags on browser items live in Live's own database/Collections; check whether LOM or files allow writing.
5. **Plugin parameters (UC3)**: VST parameters are exposed only if "configured" (Configure button); check `Device.parameters` behavior for VST2/VST3.
6. **Usage frequency (UC6)**: derive from `.als` scans (count device/sample usage across projects) into a local index.

## Deep review result (2026-11-10, `docs/research-deep-review.md`)

| Use case | Verdict |
|---|---|
| UC3 vocal chain, UC5 scene/VST stack, UC6 local organize | Buildable now (within exposed params; "owned" must be owner-confirmed) |
| UC1 drum rack, UC4 group + macros | Need sample files (file-level preset generation; LOM has no macro-map or group API) |
| UC2 plugin color tags | Blocked: no write API found; ranked recommendations only until a metadata diff proves a safe write |

Build order from the review: (1) read-only bridge + capability probe, (2) offline `.als` reader + usage index,
(3) Live parity + stack creation, (4) drum rack generator, (5) rack/macro proof of concept, (6) gear catalog,
(7) Collections experiment. Sample pack and anonymization steps are in section 8 of the review.
Licensing: Ziforge (GPL-3) and DawVert (GPL-3) are reference-only; write our own code. Upstream telemetry is not imported.
Live 12.3+ APIs (`insert_device`, `insert_chain`, `DrumChain.in_note`) must be version-gated; the owner's Live is 12.2, so they are unavailable there and `probe()` reports `track.insert_device: false`.

## Proposed architecture (draft)

- `remote_script/` : Python control surface script running inside Live (stdlib only), TCP/JSON bridge.
- `mcp_server/` : Python MCP server (official `mcp` SDK), talks to the bridge.
- `als/` : offline project/preset parser and writer (no Live needed; unit-testable).
- `knowledge/` : gear equivalence data (hardware -> emulations/alternatives) as plain, contributable data files.

## Milestones

- [x] M0 Repo foundations: license (MIT), README, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, issue/PR templates, CI (lint+tests), `.gitignore`, pyproject. Repo stays private until the owner is happy with v1 (owner decision 2026-11-10). Research notes: `docs/research.md`.
- [~] M1 Parity with upstream ableton-mcp. Bridge + 15 MCP tools committed (e6fb9c6). Verified in real Live 12.2 (2026-11-10): handshake, browser roots/list/search, `load_item` (Compressor onto a new track), device parameter read + write with readback, track create/rename/color, tempo, and range/index guards. Remaining: transport, scenes, clips (in progress, fake-tested only), then real-Live check of those after a Live restart; loading from `plugins`/drum kits/racks untested.
- [~] M2 Offline `.als` reader + usage index (UC1/UC6 foundation). Reader, usage scan and MCP tools (`als_summary`, `als_usage_index`) done (ebd1bd6, e6fb9c6). Sample extraction is synthetic-tested only; needs a real Set with audio clips.
  - [x] Extract sample filenames, relative paths, sizes, and conservative clip/note classifications (`referenced` / `potentially_triggered`); synthetic coverage includes clips, Simpler, DrumCell, and Drum Rack pads.
  - [x] Expose `scan_projects`, aggregate device classes/plugin formats and names/sample references, skip Backup directories, and retain corrupt/unreadable file errors.
  - [x] Verify synthetic coverage, full pytest/Ruff, and read-only real-project scan (2026-11-10): `S:/AbletonMCP/projects` contained one Set, no errors, 11 device instances including four VST3 Nexus instances, and no sample references. Real audio-clip/sample schema validation still needs a Set containing samples.
- [ ] M3 Drum rack builder, standard layout (UC1).
- [ ] M4 Rack grouping + macro mapping from natural-language spec (UC4).
- [ ] M5 Organization: color tags, labels, categories (UC2/UC6).
- [ ] M6 Chain replication w/ gear-equivalence knowledge base (UC3).
- [ ] M7 Public release (owner decision; push guard installed first).

## Catchup ledger (2026-11-10)

| Item | Tag | Source / note |
|---|---|---|
| Commit M1 bridge + M2 scan | auto, DONE | ebd1bd6, e6fb9c6 |
| Correct Live 12.4 -> 12.2 in docs | auto, DONE | `docs/vision.md` decision log; `HANDOFF.md` |
| Transport, scenes, clips handlers | auto, in progress | delegated; fake-tested only |
| Push + confirm CI | auto | after final commit |
| Real-Live check of new transport/clip handlers | blocked | needs Live restart to load the new script |
| Remove `ALMCP test` track from the open Set | owner | unsaved test track in `Basic`; Ctrl+Z or close without saving |
| Sample files + a Set with clips (M3 drum rack, M4 macros, real sample-schema check) | owner | list in `docs/research-deep-review.md` section 8 |
| Make repo public / tag releases | owner | release decision |

Assumptions: target Live 12.2+ (owner's install); `0.1.0` tag waits until the transport/clip work is verified in real Live (a tag is a milestone marker on a private repo).

## Next step

Finish M1 (transport/scenes/clips), then M3 (drum rack builder, needs samples) or M6 (vocal chain, no samples needed).
