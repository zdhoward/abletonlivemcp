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

## Owner corrections: note preservation, sparse automation and VST buildup

- Saved Basic was inspected read-only through the ALS reader parser. It contains Arrangement
  MIDI, no Session clips: Hats [16,32], Core [0,32], PAD [0,15]/[16,31], MainBass [16,32].
  Hats uses MIDI 80. Owner confirms open G#4=80 and closed C4=72 in Live's C3=60 convention.
  The repository exposes MIDI integers; its API dump identifies the native
  Clip.note_number_to_name helper (scale/spelling-aware), not a GM kit map. No kick map
  is confirmed; Core's saved 45/52 are historical notes, not a mapping claim.
- Reopened Basic with the restart helper to discard the prior generated MIDI. Never saved
  Basic. Every restart confirmed Basic's window title and actual Intro(0)/DROP(16) cues.
- Zero-length insert_step calls returned 8 coincident events and constant volume 0.85:
  not usable breakpoints. Two half-clip steps yielded 6 events; deleting interior events
  in (0.0001,15.9999) left 4 events at two endpoint times, with interpolated values
  0.1004375 / 0.275 / 0.45 / 0.625 / 0.7995625 at beats .01/4/8/12/15.99.
- Added points (2-3, clear=true, full clip span) to live_set_automation. It inserts steps
  then deletes interior boundaries. A seed extending beyond the source clip forces the
  terminal breakpoint when the end value equals the original/default value: without this,
  Pump A/B=1 coalesced away the endpoint and flattened after beat 8 (caught before copying).
  The temporary seed's restoring event lies outside the copied clip span. Coincident
  boundary guards remain; distinct breakpoint positions and raw event counts are reported
  separately. Native Envelope has no interpolation/Bezier curvature setter.
- Browser search found Wider VST/VST3 and GHOST//PUMP VST3. Loaded both real VST3s, no stock
  substitutions. Wider exposes Device On + Amount; GHOST//PUMP exposes 20 parameters,
  including Pump A/B, Rate, Sync, Shape A/B, Boost. The native PluginDevice API lists
  get_parameter_names and read-only parameters, with no Configure/add-parameter method.
  These installed plugins expose the required parameters without manual configuration.
- To avoid copying empty Session carriers over the owner's Arrangement notes, the new demo
  uses a separate Buildup FX audio bus for INSTRUMENTAL. It carries silent audio clips,
  stock Auto Filter, Wider, GHOST//PUMP, sends to C-INSTR Verb (stock Reverb) and D-INSTR
  Delay (stock Delay). No musical clips are replaced. Default path never creates notes.
  Both returns read back Dry/Wet=100%; Reverb decay=2.50 s, Delay feedback=21%.
  Explicit --create-notes requires a supplied pitch map and refuses occupied Session slots.
- Buildup targets at 0/8/16: reverb send 0/.3/1, delay 0/.15/.5, Frequency 0/.195/.65,
  Wider Amount 0/.15/.5, Pump A/B 0/.3/1; all reset at DROP. --shape changes the middle
  fraction; segments are linear and owner-editable. Pump Boost is set to zero before
  envelopes, so its init preset's +3 dB is not added. No parameter is manually set after
  writing its envelope.
- Validation so far: 401 existing tests passed; updated automation surface (7 checks), Ruff
  and whitespace checks passed. No fake-Live tests added. bridge.json remains BOM-less
  UTF-8, read_only=false; dev probes were not enabled. Final Live proof is recorded below.

### Final installed build proof

- Installed with C:\Python313\python.exe pip --user --force-reinstall --no-deps and
  scripts/live_restart.ps1 -Reinstall; Basic window title and cues confirmed again.
- tasks/buildup-final.log: every buildup envelope has exactly three distinct positions
  (0,8,16). Native counts: reverb send 4, delay send 4, Frequency 5, Wider Amount 4,
  Pump A 5, Pump B 5. All four interpolation samples per envelope passed, including
  Pump A/B at .15/.3/.65/.999125 at beats 4/8/12/15.99. Drop envelopes read zero.
- Carriers copied to exact Arrangement spans [0,16]/[16,32]. Readback confirmed all 24
  original musical clips, their bounds and full note contents (including IDs) unchanged.
  Note-writing mode was not run. All previous invented GM notes were discarded by reopening
  saved Basic; original Hats clips use MIDI 80 and start at DROP.
- PowerShell 5 reports redirected native stderr INFO lines as NativeCommandError; the
  demo itself reached its final Done after every assertion, with no traceback. Subsequent
  playback proof uses subprocess capture to preserve the actual Python exit code.
- Direct Arrangement envelope event reads remain unavailable. Source event counts above
  must not be presented as a separately measured timeline-lane event count. Timeline
  behavior is qualified by the playback proof; native curve editing remains a Live UI step.
- First playback range assertion failed because Song.start_playing restarted from the
  stored start position, despite a stopped current_song_time seek to 12. Receipt showed
  current_song_time=12 before play but settled=4.990869 and then position=9.524203 with
  loop_start=12. The early frequency read therefore preceded the late loop. This was a
  proof timing error, not evidence of curve conversion. Continue also resumed a prior
  stop position (22+) after a stopped seek to 0. The final proof starts playback first,
  seeks while running and verifies actual position is inside each sample loop before reads.
- Final playback evidence: tasks/buildup-playback-running-seek.log. With actual positions
  checked in loops [0,4], [12,16], [16,20], all six automated controls rise into their
  expected late ranges and reset to zero at DROP; every device parameter reports
  automation_state=1. Late Wider=47.30%, Pump A/B=69%, reverb send=.759728 and delay=.379878
  were read in the late loop. DROP Frequency=20 Hz, Wider/Pump A/B=0, both sends=-inf dB.
  Bus audio meters are active in every phase. Transport is restored stopped at Intro,
  loop off, Arrangement active. This proves copied ramp/reset playback without claiming
  an unavailable direct timeline event count or human listening evaluation.

### Owner feedback supersedes the testing workflow and parallel-send design

- Owner asked for quick FX/automation application, then "ready for preview". API checks
  cannot evaluate sound. No more playback tests; use the owner's listening feedback.
- Applied inline Reverb and Delay after the widening/pump chain on Buildup FX. Reverb
  Dry/Wet rises 0/.35/1 at 0/8/16, Delay 0/.12/.4, filter 0/.3/.88, Wider 0/.2/.75;
  existing Pump A/B rise remains. Reverb decay raw=.6, delay feedback raw=.3.
- Reverb and Delay Device On are automated on during Intro, off at DROP. Dry/Wet resets
  to zero too. Parallel instrument sends are zeroed so their tails do not wash over the
  drop. Original MIDI is untouched. Applied via tasks/apply_airy_buildup.py; receipt log
  tasks/airy-buildup-apply.log. No listening/test claims for this revised sound design.
- Demo now follows this inline wet-to-dry direction and no longer runs a note comparison
  or playback/automation test sequence by default. Await owner's preview feedback.
