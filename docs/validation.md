# Validation and limits (v0.11 beta)

This beta targets Ableton Live 12.2 on Windows. Host Python is 3.10 or later. Other Live
versions and operating systems have not been qualified against a running DAW.

What has been checked, newest first:

- **Unreleased, review round 4 (2026-11-12, Live 12.2.0, disposable Basic Set, never saved;
  Remote Script reinstalled with every round-4 fix before the runs):**
  - The full write ledger (`scripts/live_v2_final.py`, 37 scenarios, every registered tool)
    ran against the current bridge: 34 pass and 3 explicit `unsupported` (`dev-extras`: no
    preset selection on that device; `dev-fx-rack`: no `insert_chain`; `dev-drums`: pad load
    disabled), with nothing failed or blocked. The MIDI file round trip, clip
    duplicate/delete and project scan scenarios need `ABLETONLIVEMCP_FILE_ROOTS` and
    `ABLETONLIVEMCP_ALS_ROOTS`. They were rerun with those set and passed.
  - On a running server, `live_plan_chain` then `live_build_chain` (EQ Eight, Compressor)
    completed. Before this round the plan store was overwritten at import.
  - Populated tracks (a MIDI track with a 4-note clip, an audio track with EQ Eight and
    Compressor): a duplicate kept the clip, and both devices read back. Undo reverted one
    rename. Replace into an empty slot asked and created the clip. Replace into an occupied
    slot listed the old clip and swapped it.
  - Concurrency: two stdio server processes sent the same confirmed `live_delete` with both
    forms open at once. One deleted the track; the other refused `stale_target` (not
    applied). A declined confirmation deleted nothing, and a fresh accept then deleted the
    clip. Parallel writes and reads through one server all landed. Across two server
    processes, a call that hits the other's open bridge exchange is refused
    `BridgeBusy ... (not applied)`, and the read-back confirmed nothing was applied.
  - Deferred ticks: a cue add, then a confirmed cue delete, both `ready`, with the playhead
    back where it was (8.0 -> 8.0). A bounded 2-beat Session recording ended `ready` with
    recording off and the transport stopped. A forged whole-Set arrangement cursor was refused
    `unknown_cursor`.
  - Not verified on Live: saving a copy and reopening it. Driving Live's Save As dialog from
    outside was not reliable. The timeout, step-error and disconnect cleanup paths are covered
    offline only.
- **Unreleased, review round 2 (2026-11-12, Live 12.2, disposable Basic Set, never saved;
  Remote Script reinstalled before each run):**
  - A `"replace"` of `"true"`, `1` or `"replace"` sent straight to the bridge with only `edit`
    was refused ("must be a bool"); `replace: true` was refused `permission_denied`; the
    occupant clip stayed.
  - Confirmations over stdio with an elicitation client: the question listed the track
    (`'r3-a' (track 10)`), the cue (`'r3-cue' at beat 200.0`) and the occupant clip read from
    Live. Shifting the track index while the form was open made `live_delete` refuse
    `stale_target` (nothing deleted); swapping the occupant made the replace refuse
    `target_changed` (the newcomer stayed); adding an earlier cue while the form was open
    still deleted only the confirmed cue. A fresh accept deleted exactly what was shown.
  - Cue add with `read_only` or the `edit` permission revoked as it started: `failed` /
    `not_applied`, no cue, playhead unmoved, no `undo_steps` claim. An unrevoked add put the
    playhead back (4 -> 4, reported `restored`). The task finishes within one bridge round
    trip, so a revocation between its seek and toggle could not be timed from outside; that
    phase is covered offline.
  - A track with 300 arrangement clips read through the whole-Set cursor in 2 pages (first
    page `partial` at 232 of that track's rows): all 300 rows, none repeated; a delete between
    pages made the old cursor refuse `stale_cursor`.
  - A second bounded recording during a 12-beat arrangement recording was refused
    `recording_active`; afterwards recording was off and transport stopped.
  - Track batches: create 8/16/32 took 4.9/5.5/7.9 s, delete 2.6/3.3/5.1 s, duplicate 32 empty
    tracks 7.6 s; create 64 took 8.7-14.2 s and once exceeded the 10 s request budget
    (`TimeoutAfterStart`, all 64 created), hence the 32/16 caps.
- **Unreleased (after 0.11.0):** on Live 12.2 with a Set containing nested group tracks,
  `live_get_arrangement` read the whole Set (group rows marked `group: true`), and an
  arrangement-clip reference on a group track refused with a readable message. Before this
  fix any group track made the whole read fail.
- **0.10.0:** seven read-only tools validated against their schemas over stdio on Live 12.2.0.
- **0.9.0:** the full real-Live scenario ledger below (rerun in review round 4 above with the
  same totals).

The 0.9.0 real-Live scenario ledger records 34 passing scenarios and 3 scenarios with explicit
unsupported results, with no failed or blocked scenarios. It covers the 57 registered tools,
including connection, mixer/routing, clips/notes, MIDI files, device loading/parameters/movement,
stock racks/drums, nested Simpler read/write/readback, arrangement, undo, confirmed deletion,
offline usage, labels, resources and prompts. Tool coverage does not prove every enum/target combination.

The offline suite covers protocol authentication/bounds, installer safety, path confinement,
bounded XML parsing, schemas, confirmations and tool contracts. CI runs Python 3.10 and 3.13
on Windows and Linux. Size contracts keep the 30-tool core listing below 68,000 UTF-8 bytes
(request schemas below 30,000) and the default 36-tool listing below 80,000 (request schemas
below 36,000), including typed output schemas.

Distribution CI builds wheel and source archives, checks their allowed contents and embedded
Remote Script completeness, then installs the wheel in an isolated environment and initializes
the stdio MCP server from outside the checkout. This check lists tools without connecting to Live.
Personal knowledge and development artifacts are excluded from both package formats.

Release 0.10.0 passed 398 local tests, Ruff, archive checks (no developer probes in either
archive) and a clean wheel stdio install. Over stdio against Live 12.2.0, seven read-only tools
(`live_hello`, session, tracks, scenes, clips, device list, browser roots) returned output that
validated against their schemas. Report write problems found in real projects as issues.

## Known limits

Targeted P-19, 2026-11-11, Basic on Live 12.2: copying PAD's 16-beat Session clip with
`Track.duplicate_clip_to_arrangement` to beat 0 returned a clip at [0,16] without a crash.
Deleting it and restoring it also succeeded. With the clip deleted, the Auto Filter Frequency
curve remained visible in PAD's track automation lane; the parameter's automation_state stayed
1 (automated). Samples taken after the short buildup had passed were static, so those samples
do not establish ramp playback. Basic was never saved; no saved-file claim is made for these
unsaved edits. This qualifies Session-to-Arrangement copy only, not the full P-19 probe.

The complete buildup demo then passed twice in the same Set: eight timeline clips with full
note readback at [0,16] and [16,32], six buildup/drop Session envelopes, actual Intro/DROP
locators and transport stopped at 0. The repeat confirmed automation_state=1 for PAD/Hats
Frequency and Core Saturator Drive. All three curves were inspected on screen. 401 repository
tests and Ruff passed. Server wheel and Remote Script were reinstalled before this Live proof.

- Automatic rack-chain insertion/grouping and macro mapping are unavailable on Live 12.2.
- Custom drum-pad browser loading/building and pad copying refuse unsupported. Stock kit
  loading, pad reads/mute, rack macro edits and nested Simpler edits were exercised.
- Plugin preset selection depends on the plugin and exposed API; the tested unsupported path refuses.
- Unsafe arrangement split/move/take-lane writes and arrangement automation are disabled.
- Native browser Collections cannot be written; organization uses local labels and track properties.
- Set labels passed an in-session roundtrip. Persistence after saving/reopening is unproved.
- Knowledge is optional local reference material, not an audio analysis or automatic mixing engine.

Writes are off by default. Unknown mutation outcomes must be read back before any further edits;
never retry blindly. Keep backups of valuable Sets while testing the beta.
