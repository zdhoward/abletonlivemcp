# Live test session retro notes (2026-11-11)

Goal: "turn the Intro section into an EDM buildup with the drop on DROP" via plain English.
Format: [severity] issue, evidence, suggested fix. Severity: bug / gap / ux / mine (my own mistake).

## MCP issues

1. [ux] `live_hello` does not report `read_only`. First write failed with
   "read_only: writes are disabled..." and nothing earlier signalled it.
   Fix: add `read_only` (and `dev_probes`) to the hello payload and the capability report.
2. [ux] Editing `bridge.json` only takes effect after a Live restart; the refusal text says
   "set read_only to false there" and does not say a restart is needed. Retried once and got the same error.
   Fix: say "restart Live after changing" in the message, or re-read the config per call.
3. [bug] `bridge.json` with a UTF-8 BOM (PowerShell 5.1 `Set-Content -Encoding utf8`) makes the
   Remote Script fail with "private bridge config unavailable; reinstall or repair" and the MCP side
   return `ConfigError` for every call. Fix: read with `utf-8-sig` in config.py and the Remote Script,
   and say "BOM" or "invalid JSON" in the error.
4. [gap] `core` toolset has no way to create or edit cue markers or arrangement clips, so "buildup at the
   Intro label, drop at DROP" can only be built as Session clips in scenes.
   Markers were also lost when Live was restarted (unsaved).
5. [bug/ux] `live_set_device_parameters` with a display value for a continuous parameter
   (`"100 Hz"`, `"25 %"`) returns status "partial" with `ValueError: at most 129 display values in total per request`.
   Type (quantized) applied; Frequency and Resonance did not. Raw values worked.
   Fix: accept display values for continuous parameters (cheap bisection), or raise the budget,
   or tell the caller up front to use `{"raw": x}`. "partial" is easy to miss.
6. [gap] No tool to enable toolsets at runtime; `ABLETONLIVEMCP_TOOLSETS` lives in the client's MCP config
   and needs a reconnect. `live_hello` lists `available` toolsets but not how to enable them.
7. [ux] `capability_report` says `clip.get_notes`/`add_new_notes` false while `notes.extended` is supported.
   Writes worked through `live_create_clips`, so the flags read as failures when they are not.

## My mistakes (process)

8. [mine] Restarted Live after checking only that the saved `Basic.als` contained the strings "Intro"/"DROP".
   Those strings were elsewhere in the file; the cue markers were unsaved and were lost. Verify with
   cue points, not substrings, or ask before closing Live with a user-opened set.
9. [mine] Wrote `bridge.json` with `Set-Content -Encoding utf8` (BOM) and cost an extra restart.
10. [mine] Chose drum pitches (kick 36, hat 42) without checking what Nexus maps; needs a listen.

## Other

11. A grep of `~/.claude_cpamc/.claude.json` showed a live Stripe key in plaintext (unrelated to this MCP).

## Work done

- 8 Session clips (scenes 0-1: Buildup, Drop) on PAD, Core, Hats, MainBass; all notes read back.
- Auto Filter (stock) on PAD and Hats, high-pass 100 Hz, 25% resonance. Automation pending the toolset.

## Later findings (same session)

### Arrangement implementation and targeted P-19 (implementation worker)

- Implemented `live_create_arrangement_clips(kind="from_session", scene, start)` with the
  existing reference gates, full-batch validation, exact position/length readback and overlap
  refusal. Explicit replace requires delete permission at host and bridge and only removes
  clips wholly inside the destination span. Session copy has its own capability so the
  unqualified Arrangement-to-Arrangement duplicate, split, move and take-lane routes stay shut.
- Measured on real Live 12.2 in Basic: PAD scene 0 -> beat 0 succeeded, Buildup Pad at
  [0,16], length 16. No crash on copy, delete or restore. After deleting the copy, the
  Frequency curve remained visible in PAD's Auto Filter/Frequency track lane, with the
  note clip absent (local evidence `tasks/frequency-menu.png`); automation_state stayed 1
  before/after (`tasks/p19-session-copy.log`). The playback samples were all 0.1 because
  the 16-beat buildup had elapsed by readback; they do not prove audible ramp playback.
- No Set was saved. The existing read-only ALS reader reads saved disk state, so using it
  on Basic.als would falsely describe the current unsaved timeline. Used Live's own visible
  lane plus parameter automation state instead. No request for owner inspection was needed.
- Demo now replaces its Session clips, reuses effects, writes buildup/drop envelopes,
  adds Core Saturator at index 1 with Drive 0.42->0.95, copies eight musical clips onto
  beats 0/16, returns to Arrangement, disables the 16-beat loop and verifies notes/bounds.
  Musical clips are retained for notes; the verified lane retention needs no cleanup tool.
- Arrangement joins the default toolsets (36 tools). Default Arrangement reads omit
  take-lane traversal, which failed on this Basic set; explicit take-lane reads remain opt-in.
- Quoted the Basic path in the restart helper and added a Basic window-title assertion/fallback.
  Before each restart checked Basic's title; after opening checked Intro(0), DROP(16) before building.
- Final validation: two full real-Live demo runs passed on the same Basic Set. Both verified
  all eight Arrangement clips, exact [0,16]/[16,32] bounds/names and full note contents, all
  six Session envelopes (buildup/drop on three parameters), cues and stopped transport at 0.
  Repeat additionally confirmed automation_state=1 on all three track parameters. Core Drive
  requested 0.42->0.95 read back approximately 0.416667->0.95 (Live's initial value resolution).
  Evidence: local `tasks/arrangement-demo-live.log` and `tasks/arrangement-demo-repeat.log`.
  All 401 repository tests, seven tool-surface checks, Ruff and diff whitespace checks passed.
  No fake harness was extended. Final screenshot: local `tasks/arrangement-final.png`.
- During visual setup a brief Arrangement playback reached bar 3 with PAD's Frequency at
  273 Hz, versus 39.9 Hz stopped at Intro; meters were active (`tasks/arrangement-visible.png`).
  Stopped playback immediately, and the repeat verification subsequently confirmed transport
  stopped at beat 0. All three automation selectors/curves are left visible. Basic is unsaved.
- First full demo correctly refused before writing a drop reset: existing automation step
  validation wrongly required time > 0. Fixed time to allow 0 and explicitly reject the
  clip end (which would produce a zero-duration step). Reinstalled/restarted after that fix.
- A build attempt overlapped the restart/set-loading window and refused Unreachable before
  mutations. Waited for restart completion and re-read Basic title and actual cue points,
  then reran. Do not start the builder while the restart helper is still running.

12. [FIXED, proven in real Live] BOM in bridge.json: config.py now reads utf-8-sig; remote_script core.py and safety.py strip a BOM. Live started with a BOM'd config after reinstall. Not committed yet. Add one small test.
13. [DESIGN] The canonical demo (buildup with filter sweeps) needs automation, but `automation` is not in the default `core` toolset, so a default install cannot do it. Proposal: move `automation` into the default set (CORE_MODULES / default toolsets), update README "30 tools" and any count tests.
14. [UX] Toolset changes need a new host session: the host caches the MCP config at session start; killing the server only respawns it with the old env. Worked around with scripts/mcp_call.py (spawns a server with chosen toolsets). Server also accepts a `toolsets` key in bridge.json, not documented in the setup flow.
15. [UX] live_set_automation takes `parameter` as an integer index; live_set_device_parameters takes a name. Make both accept either.
16. [UX] live_launch scene readback returns `is_playing: null` and an empty scene name; cannot confirm playback from the receipt.
17. [UX] live_create_clips on an occupied slot fails the whole batch ("clip slot is occupied (not applied)"); a re-run of a demo script is not idempotent. Consider an `if_exists: skip|replace` option so workflows are repeatable from a fresh Basic.
18. [UX] mcp client package differs by version (`is_error` vs `isError`); scripts/mcp_call.py handles both.
19. [mine] I killed the running MCP server process to try to reload it; the host did not reload toolsets, so this only wasted a step. Do not restart servers to pick up config.
