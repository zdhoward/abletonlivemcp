# Plan (awaiting owner check-in)

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
Live 12.3+ APIs (`insert_device`, `insert_chain`, `DrumChain.in_note`) must be version-gated.

## Proposed architecture (draft)

- `remote_script/` : Python control surface script running inside Live (stdlib only), TCP/JSON bridge.
- `mcp_server/` : Python MCP server (official `mcp` SDK), talks to the bridge.
- `als/` : offline project/preset parser and writer (no Live needed; unit-testable).
- `knowledge/` : gear equivalence data (hardware -> emulations/alternatives) as plain, contributable data files.

## Milestones

- [x] M0 Repo foundations: license (MIT), README, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, issue/PR templates, CI (lint+tests), `.gitignore`, pyproject. Repo stays private until the owner is happy with v1 (owner decision 2026-11-10). Research notes: `docs/research.md`.
- [ ] M1 Parity with upstream ableton-mcp (session info, tracks, clips, devices, params, browser load, transport). Start with the read-only bridge + capability probe (Remote Script + MCP server, loopback, framed JSON, main-thread queue). NEXT.
- [~] M2 Offline `.als` reader + usage index (UC1/UC6 foundation). Reader + usage index done on synthetic XML (`src/abletonlivemcp/als/`); still to do: validate against real Sets (read-only scan of owner's projects), MCP tool wrapper, sample-vs-used classification (`referenced` / `potentially_triggered`).
- [ ] M3 Drum rack builder, standard layout (UC1).
- [ ] M4 Rack grouping + macro mapping from natural-language spec (UC4).
- [ ] M5 Organization: color tags, labels, categories (UC2/UC6).
- [ ] M6 Chain replication w/ gear-equivalence knowledge base (UC3).
- [ ] M7 Public release (owner decision; push guard installed first).

## Next step

Owner confirms/edits this plan; then M0 starts and the research questions above get resolved first (they decide M3-M5).
