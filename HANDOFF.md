# Handoff (2026-11-11, v1 hardened; public roadmap + detailed plan written; Wave 0 T-001 done)

Repo `zdhoward/abletonlivemcp` (PRIVATE until the owner is happy). `main` == `origin/main` at `81375d7`; no PRs, no worktrees, no tags
this session (last tag `v0.1.0`, `pyproject` still `0.0.1`). Directive: cover everything competitors do, then more, with
MCP best practices, to maintain and release publicly.

## Done this session
- Catchup: missing-param refusal (`_Params`), handshake advertises `methods`, second-process lease proven in real Live.
- Study (3 agents): `docs/research/live-api-map.md`, `docs/research/mcp-excellence.md`, repo audit (use cases vs code).
- Plans: `docs/plans/v2-public-roadmap.md` (phases P0-P6, owner answers) and `docs/plans/v2-detailed-plan.md` (Opus: parity matrix,
  core 31-tool surface + 13 opt-in toolsets, tickets T-001..T-083 in 9 waves, 26 probes, risks).
- P0 hygiene: honest README goals, knowledge INDEX status, todo M2 text, `CHANGELOG.md`, `NOTICE`.
- T-001 (merged `dea4b34`): handlers split into flat `dom_*.py` (METHODS tables merged fail-closed in `safety.py`), server tools in
  `tools/<domain>.py`, Jev/TypeSafe removed. Real Live proof: `docs/release/v2/T-001.md` (write/clip/chain proofs PASS, 27 tools, 262 tests, ruff clean).

## Decisions
- Live 12.2 is the floor; 12.3+/12.4 APIs version-gated by `probe()`. After core surface: original use cases (UC6/UC1/UC4), then arrangement.
- No arbitrary code-exec tool ever; probes are a fixed table in the Remote Script, never MCP tools.
- Real Live is one shared resource: only the orchestrator runs proofs/probes, serially (start/close/reinstall Live itself; memory `live-lifecycle-autonomy`).
- To test with writes: temporarily set `read_only:false` in `~/.abletonlivemcp/bridge.json`, restore `true` after (it is `true` now).
- Use `.venv\Scripts\python` (system python lacks `mcp`). In Git Bash `/tmp` is not visible to Windows Python; use repo-local temp files.

## Next steps (in order; see `tasks/todo.md` and the detailed plan section 3)
1. Wave 0 remainder: T-002 (toolset registry, annotations, outputSchema, response_format, selectors, auto-lease, snapshot test), T-003 (fixed-table
   probe runner), T-004 (proof harness `scripts/live_harness.py`) in parallel (disjoint files); then T-005 (reference kinds, needs P-01) , T-006 (undo step, needs P-03), T-007 (elicitation for destructive).
2. Wave 1 probes P-01..P-29 (serial in real Live), then Wave 2 core surface (mixer, returns/sends, note edit, device order, clip props, batch setters), Wave 3 MCP quality, Waves 4-6 UC1/UC4/UC6, Wave 7 arrangement, Wave 8 evals.
3. P2 packaging/distribution and P6 launch from the roadmap (publish/tag/accounts are owner-gated).
4. T-081 must re-verify the competitor matrix (it was written from memory; the fetch failed) before anything goes public.
5. Delegate implementation with explicit briefs (Opus for safety-seam tickets, Sonnet medium otherwise), worktree isolation, verify against the diff, run proofs in real Live myself.

## Owner-only
Package/registry names and accounts, public flip and tags, sample files + a Set with clips (UC1 drum rack, real `.als` validation), `read_only:false` for assistant writes outside tests.

## Known unproved (see `docs/release/m1b-live-evidence.md`)
Target-reorder refusal in real Live (no move/delete handler; unit-covered), non-stock loads, OneDrive reparse points, one unexplained "connection lost" after Live launch.

## Key files
Plans: `docs/plans/v2-detailed-plan.md`, `docs/plans/v2-public-roadmap.md`; research: `docs/research/`; evidence: `docs/release/`; safety contract: `remote_script/AbletonLiveMCP/safety.py`; ledger: `tasks/todo.md`, `tasks/lessons.md`.
