# Validation and limits (1.0.0)

This release targets Ableton Live 12.2 on Windows. Host Python is 3.10 or later. Other Live
versions and operating systems have not been qualified against a running DAW.

The evidence below predates the 1.0.0 version bump; original versions and build IDs are
retained for traceability. No new Live run was performed for the packaging/docs release.
The package retains its Beta classifier: this record covers disposable, unsaved Sets,
and several failure paths have offline coverage only. A 1.0 version does not expand
the qualified scope. macOS remains untested.

What has been checked, newest first:

- **Unreleased, review round 8 (2026-11-12, Live 12.2, disposable Basic Set, never saved).**
  Targeted fixes only; no full ledger rerun. Remote Script reinstalled from git `c066c1b` and
  Live restarted. Through `BridgeClient`: an arrangement cue read returned Intro 0 and DROP
  16 (playhead 8). An add at 40 (a free bar) was ready (`complete`, 5 ticks, playhead
  restored to 8). The delete of that cue was ready (`complete`, 5 ticks, playhead restored).
  The cues read back as before. Live's `Log.txt` shows no handler error.
  - F1: before each forward seek step and the toggle, a cue task checks that the time left
    covers the planned return (0.1 s per planned step plus a 1 s reserve). Otherwise it stops
    with nothing toggled. The return runs until 0.25 s before the 10 s deadline. Unit
    tests only: `test_a_late_cue_step_never_toggles_without_time_for_the_return` (a delayed
    first tick and a seek observed late; both toggled on the old code).
  - F2: an arrangement read supports 512 cue points and refuses `beyond_scope` on the count.
    512 cues plus the largest clip/lane page measure 14,446 of 16,384 JSON nodes.
    `test_arrangement_cues_are_scoped_and_the_largest_page_fits_the_signed_reply` sends
    that reply through the signed framing, and 513 refuse with no cue field read. Not
    exercised in Live.
  - F3: tool and resource text names every terminal operation state.
- **Unreleased, review round 7 (2026-11-12, Live 12.2.0 build 2025-05-20_1c7a2c5dac,
  disposable Basic Set, never saved).** Qualified build: git `cae1b07` (clean tree), Remote
  Script 0.11.0 build `sha256:37ec9964034b3165` (matches the host). The script was
  reinstalled and Live restarted before the checks, then restarted again before the ledger.
  - Full write ledger (`scripts/live_v2_final.py --scratch-writes`, one full run, no `--only`
    merge): 37 scenarios and every registered tool. 34 passed and 3 were explicit
    `unsupported` (`dev-extras`, `dev-fx-rack`, `dev-drums`, as before). None failed or
    blocked, and there were no coverage gaps. `ABLETONLIVEMCP_FILE_ROOTS` and
    `ABLETONLIVEMCP_ALS_ROOTS` were set. Live's `Log.txt` shows no handler error during the
    run.
  - `scripts/live_final_cleanup.py --apply` deleted 1 scratch cue, 5 scratch tracks, 1
    scratch return track and the MIDI export. Read-back afterwards: 10 tracks, 4 returns, only
    the Set's own cues (Intro 0, DROP 16).
  - Cue placement, measured in Live. A new cue goes on the nearest bar of the Set's
    signature, and an exact tie goes to the later bar. In 4/4: 33 -> 32, 42 -> 44, 51 -> 52,
    61.5 -> 60, 86.5 -> 88, 98 -> 100, 46.5 -> 48. In 3/4: 113 -> 112, 127 -> 126,
    137.5 -> 138. `set_or_delete_cue` deletes a cue within half a bar of the playhead
    instead of adding one. An add at 33 deleted the cue at 32. In 3/4, 113 deleted 112 and
    45.4 deleted 44, while 101.6 left 100 alone. On the fixed build, the 4/4 cases are
    ready with `requested`. 33.5 next to the cue at 32 reuses it with no toggle. 34 (a tie,
    with a cue at 32) refuses `not_applied` with nothing toggled. A delete at 48 is ready.
  - Playhead return, measured in Live. Setting the playhead at the song end stretches the
    song by 32 beats (232 -> 264 -> 296 -> 328), in 4/4 and 3/4 alike. On the fixed build:
    an add at 1400 from 8 is ready in 42 ticks. With the playhead parked at 1400, a delete
    there and an add at 40 (a 1,360-beat return) are ready and the playhead is restored to
    1400. A 3-cue delete from 1400 took 48 ticks. An add at 9000 refuses `beyond_scope`
    (239 steps planned, limit 48) with the playhead untouched. Supported range: 48 planned
    steps per call, about 1,400 beats past the content.
  - Regression tests:
    `test_a_cue_add_accepts_only_its_own_bar_and_never_toggles_another_cue` (unrelated
    arrival, snap, tie, collision, occupied, delete, two cues gone),
    `test_a_cue_edit_plans_the_playhead_return_or_refuses_before_moving` (long, unreachable,
    timeout), `test_arrangement_pages_bound_lane_work_and_fit_the_signed_reply` (native
    fetches counted per page, real signed framing),
    `test_paged_reads_do_bounded_native_work_and_enforce_scope` (no note field read past
    scope), `test_safety_doc_names_every_multi_step_write_the_readme_lists`.

- **Unreleased, review round 6 (2026-11-12, Live 12.2.0, disposable Basic Set, never saved).**
  Qualified build: git `ff992fc` (clean tree), Remote Script 0.11.0 build
  `sha256:bf378cce783b59d2` (matches the host), reinstalled and Live restarted before the run.
  - Full write ledger (`scripts/live_v2_final.py`, one full run, no `--only` merge): 37
    scenarios and every registered tool. 34 passed and 3 were explicit `unsupported`
    (`dev-extras`, `dev-fx-rack`, `dev-drums`, as before). None failed or blocked, with no
    coverage gaps, and Live's `Log.txt` shows no handler error during the run. File and ALS
    roots were set.
  - The proof cleanup (`scripts/live_final_cleanup.py --apply`) deleted the scratch cue, 5
    scratch tracks, 1 scratch return track and the MIDI export. Read-back afterwards: no scratch tracks, only the
    Set's own cues. The round-5 open item is fixed. Root cause, reproduced in Live: setting
    `current_song_time` past `song_length` raises `RuntimeError`, and `song_length` stretches
    about 32 beats past the playhead. A playhead parked past the content is legal where it
    is, but the cue seek shrinks the song, so the direct return raised. The task now moves
    the playhead in steps and reports a refused return as `cleanup_issue`. Verified in Live
    with the playhead at 300 and content ending at 232: add and delete are ready and the
    playhead is restored. Also found: Live puts a new cue on the nearest bar (289 -> 288,
    290 -> 292). It is now reported applied with `requested`.
  - Paging, 12,000-note clip, same script, before (round-5 script `ec56089`) and after
    (`ff992fc`). Median of 3; one bridge round trip measured 2.1 s for `session_info`:

    | Read | Before | After |
    | --- | --- | --- |
    | `get_notes`, first 500-note page | 2.68 s | 2.56 s |
    | `get_notes`, middle page (median of 22) | 2.52 s | 2.54 s |
    | Full paged read (24 pages) | 60.5 s | 60.3 s |
    | `get_arrangement`, 256-clip track | 2.65 s | 2.44 s |
    | 1-row continuation page (fetch cost isolated) | n/a | 2.22 s (first 1-row page 2.06 s) |

    Live's native fetch of 12,000 notes was never the cost. Each page is the bridge round
    trip (about 2.1 s) plus 0.3-0.4 s of payload. The change bounds native work (middle
    pages read no notes, counted in the regression test) and enforces the scope. It does
    not shorten wall time.
  - Regression tests: N3
    `test_control_batch2.py::test_a_failed_recording_cleanup_is_unknown_and_keeps_the_guard`
    (stopped and playing; completed, late tick and disconnect). N1
    `test_bridge.py::test_whole_clip_note_edit_receipt_fits_the_signed_reply` (the real
    handler at 12,000 notes through signed framing). N2
    `test_batch3_dom.py::test_duplicate_clips_honors_to_and_refuses_before_any_write`. N4
    `test_batch3_tools.py::test_export_refuses_a_clip_changed_between_pages` (the host tool
    against the real Remote Script handler). F8
    `test_batch3_dom.py::test_paged_reads_do_bounded_native_work_and_enforce_scope`. Cue
    `test_batch3_dom.py::test_cue_delete_returns_a_playhead_parked_past_the_content` and
    `test_batch3_dom.py::test_a_cue_live_places_on_its_grid_is_reported_applied_at_its_real_time`.
  - Not verified on Live: save and reopen (no API; labels stay experimental), the N3
    failed-cleanup path (a restore that raises cannot be forced in Live), N2's `to`, the N4
    mid-export change, and the N1 9,000-note receipt (each covered offline at the failing
    layer only).

- **Unreleased, review round 5 (2026-11-12, Live 12.2.0, disposable Basic Set, never saved).**
  Qualified build: git `c3db845` (clean tree), Remote Script 0.11.0 build
  `sha256:f8097f8b0e94c3b7` (matches the host), reinstalled before the runs.
  - Full write ledger (`scripts/live_v2_final.py`, one full run, no `--only` merge) covered
    37 scenarios and every registered tool. 34 passed and 3 were explicit `unsupported`
    (`dev-extras`, `dev-fx-rack`, `dev-drums`, as in round 4). None failed or blocked, with
    no coverage gaps. `ABLETONLIVEMCP_FILE_ROOTS` and `ABLETONLIVEMCP_ALS_ROOTS` were set.
    Every row records this build, Live's version, the environment roots and its scenario
    hash.
  - Confirmation bound to the shown plan, through a real MCP client against Live in both
    the legacy and input-required (2026-07-28) flows. While the form was open, the confirmed
    track was replaced by a same-named track at the same index. `live_delete` refused
    `stale_target` (not applied) and the replacement remained. The question was asked once
    and carried its approval token.
  - Paging cost (median of 3 calls; one bridge round trip measured ~2.1 s this session for
    `session_info`):

    | Read | Latency |
    | --- | --- |
    | `get_notes`, 1-note clip | 2.2 s |
    | `get_notes`, 500-note page of a 2000-note clip | 2.5-2.7 s |
    | Full paged read of 2000 notes (4 pages) | 10.0 s |
    | `get_notes`, 500-note page of a 12,000-note clip | 2.5-2.7 s (2.2 s for a 1-note clip) |
    | `get_arrangement`, empty track | 2.1 s |
    | `get_arrangement`, 256-clip track | 2.4 s |
    | `get_arrangement`, whole Set (2 pages) | 4.9 s |
    | Track duplicate, empty | 2.3 s |
    | Track duplicate, 2000 notes + 256 arrangement clips | 2.2 s |

    Each page still re-reads and sorts the whole clip in Live. Measured overhead stays under
    0.5 s per page even at 12,000 notes, so pages are not windowed. Supported and measured
    limits: 12,000 notes per clip and 256 arrangement clips per track.
  - Regression tests: F1
    `test_destructive_confirm.py::test_a_same_named_replacement_while_asking_is_refused_not_deleted`
    (legacy + input-required). F2
    `test_bridge.py::test_published_note_limits_fit_full_signed_envelopes` (real signed
    framing). F3 `test_control_batch2.py::test_trigger_session_record_is_not_exposed`. F4
    `test_control_batch2.py::test_a_failing_switch_restore_still_stops_the_transport`. F5
    `test_batch3_dom.py::test_edit_notes_validates_duplicates_in_the_edited_state`. F6
    `test_batch3_dom.py::test_lab_cue_that_lands_elsewhere_is_reported_applied_not_refused`.
    F7 `test_final_safety.py::test_reruns_merge_only_same_build_rows_and_never_touch_the_full_run`.
  - Open (fixed in round 6): after this run, the proof cleanup's scratch cue delete (`scripts/live_final_cleanup.py`)
    reported `unknown`. Restoring the playhead raised `RuntimeError` in Live (Log.txt:
    `dom_arrangement.py:420`, finalizer `:467`). A read-back showed the cue was deleted. The
    cause is not verified.
  - Not verified on Live: save and reopen (no API, see Limits), and the F3/F4/F5 paths
    (covered offline only).

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
- Save and reopen is not qualified by this server. The Live 12.2 API dump
  (`docs/data/live-12.2-api.json`) has no member that saves a Set to a path or opens one
  (only read-only `file_path` properties and a `saved` mention in documentation text), and
  driving Live's dialogs from outside is not used (round 4: unreliable and unsafe). Set labels
  passed an in-session roundtrip; their persistence after a save is experimental for v1.
- Supported scope, enforced since round 6: 12,000 notes per note read window and 256
  arrangement clips per track or take lane; since round 7 also 16 take lanes per track (with
  `take_lanes`), checked on collection lengths before any object is read. A larger read
  refuses `beyond_scope`. An arrangement page ends after about 4,096 tracks, lanes and clips
  scanned, or before it would list more than 256 take lanes. Since round 8 an arrangement read
  that includes `cues` supports up to 512 cue points (every page lists them all); more refuses
  `beyond_scope` on the count before any cue is read. Read clips without `cues` instead.
- Cue adds and deletes (since round 7): one call plans at most 48 playhead steps (each seek,
  the return, and one step per 32 beats past the song end), so a cue edit reaches about
  1,400 beats past the arrangement content; a longer distance refuses `beyond_scope` before
  the playhead moves. Since round 8 each forward move also needs time left for the
  planned return; otherwise the edit stops with nothing toggled. A note
  edit receipt lists at most 4000 note ids, flags `note_ids_truncated` and always gives exact
  counts.
- Knowledge is optional local reference material, not an audio analysis or automatic mixing engine.

Writes are off by default. Unknown mutation outcomes must be read back before any further edits;
never retry blindly. Keep backups of valuable Sets.
