# Handoff (2026-11-10)

Repo: `zdhoward/abletonlivemcp` (PRIVATE until the owner is happy with v1). Branch `main`, no open PRs, clean tree after this commit.

## Accomplished
- Founding prompt recorded verbatim: `docs/original-prompt.md` (immutable; direction changes go in the `docs/vision.md` decision log).
- Requirements, plan and milestones: `docs/vision.md`, `tasks/todo.md`.
- M0 repo foundations: MIT license, README, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, issue/PR templates, CI (ruff + pytest on Linux/Windows, py3.10/3.13), pyproject, `.gitignore` blocking Ableton/audio files.
- Deep feasibility review (delegated to gpt-6.1-sol, medium): `docs/research-deep-review.md` (45 sources).
- M2 partial: offline `.als` reader + usage index in `src/abletonlivemcp/als/` (5 tests, synthetic XML).

## Decisions
- Target Live 12.4 only (owner is on 12.4); 12.3+ APIs usable; Live 11 unsupported for now.
- MIT, no telemetry, repo private until v1.
- UC1/UC4 go through generated/edited `.adg`/`.adv` preset files (no LOM macro-map or grouping API found). UC2 automatic plugin color tags blocked pending a metadata diff; ship ranked recommendations first.
- GPL projects (Ziforge, DawVert) are reference-only.

## Validation
- `ruff check .` clean, `pytest` 5 passed (local, Windows, Python 3.13 venv at `.venv/`, gitignored).
- GitHub Actions CI has NOT been observed running yet; check the first run.
- The `.als` reader has never touched a real Live Set; schema is inferred.

## Remaining / next steps
1. Run the reader read-only against a real projects folder (need owner's path) and fix schema mismatches.
2. M1: read-only bridge + capability probe: Remote Script (loopback, length/newline framed JSON, main-thread queue via `update_display`, request IDs, version handshake) + MCP server. Needs the owner's Live User Library path to test install.
3. Then Live parity, drum rack generator, rack/macro proof of concept, gear catalog, Collections experiment (order in `tasks/todo.md`).
4. Ask owner for the synthetic sample pack when M4/M5 begin (list in `docs/research-deep-review.md` section 8).

## Blockers
None. Owner-only: making the repo public, releases/tags for a public repo.

## Key files
`docs/original-prompt.md`, `docs/vision.md`, `docs/research-deep-review.md`, `tasks/todo.md`, `src/abletonlivemcp/als/`, `tests/test_als.py`.

No version tag applied: 0.0.1 is a pre-alpha skeleton; first tag planned at M1 (v0.1.0).
