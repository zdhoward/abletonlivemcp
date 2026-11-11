# Roadmap to the public Ableton Live MCP (draft for owner review, 2026-11-11)

Inputs: `docs/research/live-api-map.md` (what Live exposes), `docs/research/mcp-excellence.md` (what makes an MCP good,
competitors), the repo audit (use cases vs. code), `docs/vision.md`, `docs/plans/v1-public-release.md`.
Claims marked unverified in the research stay unverified until probed in real Live.

## Positioning
**The trustworthy, efficient Ableton MCP.** Competitors have breadth and mindshare; their issues show the same failures
(writes reported as done that Live dropped, token-heavy chatty tools, merge backlog, Max for Live required, unsafe
code-exec). We own: verified writes with receipts, read-only by default, batch calls with numbers to prove it, stock-first
chain building plus a producer knowledge base, a careful installer, and fast maintenance. We do not chase tool count.

## Principles
1. Every write is read back and reports stored state, not the request. Never retry a mutation.
2. 25-35 default tools, nouns with batch setters; growth goes behind opt-in toolsets, never a generic "run Python" tool.
3. Every resource is also reachable through a tool; prompts are recipes, not logic.
4. Real Live is the proof; at most one small fake-based test per feature (lesson 2026-11-10). Evals use a simulator, kept separate.
5. Tool names are public API after the first tag: aliases for one minor version on rename.
6. Live 12.2 is the floor; 12.3+/12.4 APIs are version-gated by `probe()`.

## Phases (each ends with real-Live evidence in `docs/release/` and a verified commit)

### P0 Truth and hygiene (small, first)
Fix stale docs (README claims of full parity and knowledge tools; `tasks/todo.md` M2 text; `knowledge/INDEX.md`; Live 12.4 in
`docs/research.md`); one version number (decide 0.x line, drop the stray `v0.1.0` confusion); `CHANGELOG.md`; `NOTICE`
(credit ableton-mcp upstream); strip owner paths from `docs/data/*.json`; move `docs/plans/audits/` and `HANDOFF.md` out of
the public surface; remove the Jev/typesafe dev dependency.

### P1 Core surface worth publishing (the real product)
Close the top gaps from the Live map, in value order, each probed in real Live before wrapping:
1. Mixer: volume, pan, sends, mute, solo, arm, return tracks and sends, monitoring.
2. Note edit/delete/modify (we can only add today), note ids.
3. Device order: `Song.move_device`, delete, find position (completes 12.2 chain building); rack macro values and variations (read/set, not map).
4. Clip properties (loop, markers, launch mode, warp, gain, pitch, color) and scene tempo.
5. Batch setters on every noun (`targets: [...]`), `response_format: concise|detailed`, unit/index-base/example in every description.
6. MCP quality: `title`, annotations (readOnly/destructive/idempotent), typed `outputSchema` from `models.py`, toolset switch
   (`ABLETONLIVEMCP_TOOLSETS`), tool-surface snapshot test, size budget.
7. Elicitation for first write and overwrite-class ops (fallback: refuse), progress notifications in chain builds.

### P2 Packaging and distribution
Wheel/sdist content test in CI (ships Remote Script and knowledge data, excludes research/tasks/bytecode); clean-venv install
and fake-bridge conformance test; `abletonlivemcp doctor`; PyPI Trusted Publishing workflow; `server.json` + `mcp-name`;
`.mcpb` bundle (uv type); README with support matrix, threat model, per-client snippets tested on Windows.
Publishing itself is owner-gated.

### P3 Knowledge, prompts, resources
Harden then reconnect `knowledge/` (path confinement, size caps, ship in wheel) as `knowledge://` resources + a search tool;
resources `live://session|tracks|track/{i}|device parameters|operation`; 6-7 prompts (vocal_chain, organize_session,
setup_scene, mix_check, explain_chain, diagnose_connection, safe_tweak) and a portable `SKILL.md`.

### P4 Differentiating capabilities (the owner's original use cases)
Probe first (unverified list in the Live map section 7): `Live.Conversions` drum-rack builders, `Song.get_data/set_data`,
undo steps, hotswap sample loads, `get_parameter_names`. Then, by outcome:
- UC6 organize: reconnect `.als` reader + usage index (read-only, roots-based, XML/entity limits), labels stored with
  `Song.set_data` + sidecar JSON; native color tags stay "recommendations only".
- UC1 drum rack: Conversions route (no file writes) if the probe passes; needs owner sample files.
- UC4 macros: honest scope: group/macro value control now; true mapping only via `.adg` generation experiment (high risk) or 12.3+.
- Arrangement (biggest competitor complaint): audio/MIDI clip creation, cue points, session-clip automation envelopes.
- Browser extras and loading onto MIDI tracks/rack chains.

### P5 Evals
In-memory Live simulator behind the bridge interface; 10-15 verifiable multi-step tasks (organize 8 tracks, vocal chain,
scene with clips, read-only must not write, stale reference must refuse, prompt injection in a track name). Publish call and
token counts in `docs/evals/`.

### P6 Launch and maintenance
Public ROADMAP from the not-yet list, triage SLA (first response within a week), `good first issue` labels, small PRs,
release checklist, real-Live acceptance before each minor release, dependency watch on the `mcp` major.

## Owner decisions needed
1. Upgrade Live to 12.3+ (unlocks `insert_device`, `insert_chain`, `DrumChain.in_note`) or keep 12.2 as the development floor.
2. Scope order after P1: arrangement first, or the original use cases (UC6/UC1/UC4)?
3. Package and registry name, PyPI and registry accounts, public flip date, version line (account/release gates).
4. Provide sample files and a Set with clips (needed for P4 drum rack and real `.als` schema validation).

## Autonomous without asking
All of P0-P3 and P5 code, real-Live probes, installs and Live restarts, commits and pushes to the private repo.
