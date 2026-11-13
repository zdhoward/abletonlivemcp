# Changelog

All notable changes to this project are recorded here. Format: [Keep a Changelog](https://keepachangelog.com),
versioning: [SemVer](https://semver.org). Versions below 1.0 may change tool names; renames keep an alias for one
minor version once the first public release is tagged.

## [Unreleased]

- Track selectors describe their string forms (`"return:N"`, `"master"`) in every tool's
  input schema. The default-listing byte budget rises to 84 KB to fit them.
- `live_get_clips` concise rows keep `end` and `arrangement_length` for arrangement clips;
  `length` stays the loop/source length.
- Warp-marker reads flag Live's trailing sentinel marker (1/32 beat after the last real
  one) with `"sentinel": true` instead of hiding it. Remote Script change: reinstall it.
- `live_get_device_parameters` on a device adds a `device` header (`name`, `class_name`,
  `type`; needs the updated Remote Script) and tidies `display`: surrounding whitespace is
  stripped and a doubled unit collapses (`"4.00dB dB"` -> `"4.00dB"`).

## [1.0.0] - 2026-11-12

Upgrade: upgrade the host package, close Live, reinstall the Remote Script with
`abletonlivemcp-install "<path to your User Library>"`, then restart Live and your MCP
client. Preserve your private bridge configuration. Server and script must match;
check `live_hello`. Existing configs without `permissions` retain their earlier policy;
add an explicit list as described in [permissions](docs/permissions.md).

- Add client setup examples, troubleshooting, public package metadata and CI for
  Python 3.10 through 3.14. Live qualification remains limited to
  12.2 on Windows; see [validation](docs/validation.md).

- Fix: a cue add accepts only a cue at the requested time or on its bar. Before, any new
  cue counted, so a cue someone else added at 200 during an add at 10 was renamed and
  reported applied. Live 12.2 puts a new cue on the nearest bar of the Set's signature
  (exact ties go to the later bar). Another change now ends the operation `unknown`
  (`ambiguous_change`), nothing is renamed, and the result lists what appeared or went.
  If a cue is already alone on the landing bar it is reused. Any other cue within half a
  bar refuses the add before the toggle, which would delete that cue.
- Fix: a cue delete no longer ends `unknown` (ArgumentError). It used to read the handle of
  the cue Live had just deleted.
- Fix: cue edits plan their playhead moves. Before, a fixed 40-tick budget abandoned
  reachable returns. A distance over 48 steps (about 1,400 beats past the content) refuses
  before the playhead moves. Seeks and the return run while they make progress. Running
  out of time is reported as `cleanup_issue`, and the cue change stays applied.
- Fix: paged reads check the scope on collection lengths before reading any note or clip.
  An arrangement page bounds its native work (about 4,096 tracks, lanes and clips) and its
  take lane rows (256), and a track over 16 take lanes refuses. Before, 80 lanes x 256
  clips were fetched for one page, and 2,400 empty lanes made a reply too large to send.
- Docs: `docs://safety` no longer claims every write is one undo step, and
  `live_set_cue_points` no longer promises exact cue times.
- Fix: a cue add or delete moves the playhead forward (a seek or the toggle) only while the
  time left covers its planned return. Before, a first tick that arrived late could toggle
  after the return's cutoff, and the return then failed as a `cleanup_issue`. Now the task
  stops with nothing toggled, and the return may run until just before the deadline.
- Fix: an arrangement read that includes `cues` supports up to 512 cue points and refuses
  `beyond_scope` past it. Before, every page listed every cue, and 3,000 cues made a reply
  too large to send.
- Docs: cue operation guidance says to poll only while `pending`. `ready`, `failed` and
  `unknown` are final, and after `unknown` the state must be read back before another write.

- Fix: a bounded recording whose cleanup fails now ends `unknown` (reason
  `cleanup_failed`), never ready. Before, a raising record-switch restore left
  `session_record` and the transport on, the task said applied and another recording could
  start. The cleanup reads each step back. Until a fresh readback shows the prior state (or
  the Set changes), the task still blocks new recordings.
- Fix: a whole-clip transpose or quantize of 9,000 notes applied, then its receipt passed
  the reply cap and came back `ReplyTooLarge` (outcome unknown). Write receipts now carry
  each row once (in `applied`; `items` keeps index, outcome and op). A note edit lists at most
  4000 note ids, with `note_ids_total` and `note_ids_truncated`; counts stay exact.
- Fix: `live_duplicate` ignored a clip's `to` and always copied into the next empty slot
  below. `to` is now honored. It must be an empty Session slot on a regular track that takes
  the clip's kind, not claimed by another item; anything else refuses before any write.
  Without `to`, the next-empty-slot behavior is unchanged.
- Fix: `live_get_notes` pages come from one snapshot. The first page reads the window once;
  more pages continue with an opaque single-use `cursor` (replaces `offset`/`next_offset`)
  bound to the Set, the clip and the window. A replaced clip refuses `stale_cursor`, and
  the last page refuses if any note changed. `live_export_midi` writes the file only after
  every page is consistent. Before, a clip replaced or edited between pages produced a
  mixed file reported as success.
- Fix: paged reads do bounded native work: pages between the first and last read no notes.
  The documented scope is enforced: a note window over 12,000 notes, or a track or take lane
  over 256 arrangement clips, refuses `beyond_scope`. Before, a 257-clip track was cut to 256
  rows.
- Fix: a cue add or delete with the playhead parked past the arrangement content no longer
  comes back `unknown` while the cue changed. In Live 12.2 the song end follows the
  playhead, and setting it past the song end raises. The task moves the playhead in steps. A
  return Live still refuses is reported as `cleanup_issue`, and the cue change stays applied.
- Fix: a cue Live places on its bar grid (an add at 289 lands at 288) is reported applied at
  its real time, with `requested` beside it, and is renamed. Before, it came back `unknown`.
- Docs: Set labels are experimental; survival across save and reopen is not qualified. The
  runtime texts (tools, resource, capability report) now say so.

- Fix: on MCP 2026-07-28 clients, a confirmation could approve objects other than the ones it
  showed. Resuming after the answer read the targets again, so a track replaced by another
  with the same name while the form was open was deleted and reported complete. Each
  question now carries a single-use approval (expires after 10 minutes, at most 64 open) bound
  to the tool, its arguments and the targets read before asking. The write uses exactly
  those targets, so a replacement is refused `stale_target` (not applied) on both protocol
  versions.
- Fix: note limits now fit the bridge's signed frame (16,384 JSON values). The old limits
  allowed requests the bridge could not carry: 1000-row reads failed `ReplyTooLarge`, and
  2000-note writes could not be encoded. `live_get_notes` pages at most 500 notes. A write
  takes at most 400 notes in all, also summed across the clips of one
  `live_create_clips`/`live_create_arrangement_clips` call. `modify` takes at most 200
  rows and each id list at most 500. MIDI import keeps the first 1000 notes, and
  `live_export_midi` reads 500-note pages. An oversized request is refused
  `RequestTooLarge` before anything is sent.
- Removed: `live_record` action `trigger_session_record`. It could run unbounded (no length,
  or up to 1024 beats), outside the operation registry and the one-recording guard. Use the
  bounded `session_record` switch.
- Fix: when a bounded recording ends, every cleanup step runs even if an earlier one fails.
  A failed record-switch restore no longer leaves the transport playing. The result lists
  each step under `cleanup` and reads the state back under `restored`.
- Fix: `live_edit_notes` checks `duplicate_region` against the notes as the earlier edits
  leave them. Before, modifying a note to pitch 127 and duplicating it transposed +1 applied
  the modify and then failed.
- Dev only: a `ref_lab` cue that Live placed at another time is reported
  `applied_mismatch` (it exists), not as a not-applied refusal.
- The real-Live write ledger records the build each result ran on: git revision, Remote
  Script build, Live version, environment roots and a hash of the scenario. `--only` reruns
  go to separate files and merge only results from the same build. The scratch write policy
  restores `bridge.json` byte for byte.
- Docs: saving and reopening a Set is not qualified by this server (the Live 12.2 API cannot
  save or open a Set). Validation lists the qualified build and the measured paging cost of
  dense clips.

- Fix: `live_get_arrangement` failed with a bare `HandlerError` whenever the read included a
  group track, which every whole-Set read does. Group rows now say `group: true`, and an
  arrangement-clip reference or placement on a group track refuses with a readable message.
- The Remote Script logs each unexpected handler failure to Live's `Log.txt` (method,
  exception type and code locations; never the message or arguments).
- Optional tool inputs no longer advertise a redundant `null` branch (~3 KB smaller default
  listing; explicit nulls are still accepted). A test now budgets the default 36-tool listing.
- README and validation docs: current version, dated validation status, and the buildup
  section no longer documents flags the example script does not have.
- Fix: `live_create_clips(if_exists="replace")` deleted the occupied clips before the new
  clips were validated, so a refused create (for example a MIDI clip on an audio track) still
  lost the originals. Replace now runs as one bridge call that validates every target first,
  then deletes and creates; each replaced row says `replaced` (the old clip's name).
- Fix: every call that deletes now needs the `delete` permission and your confirmation, like
  `live_delete`: cue deletes in `live_set_cue_points` (previously `edit` only, on both the
  server and the Remote Script), `live_create_clips(if_exists="replace")` and
  `live_create_arrangement_clips` with `replace: true` (previously permission only, no
  confirmation). Calls of those tools that delete nothing are unchanged.
- `live_hello` reports `script` (the running Remote Script's version and content build id
  next to this host's) and a `warning` when they differ, so a stale installed script shows up
  even at the same version. The version now has one source
  (`remote_script/AbletonLiveMCP/version.py`), read by the package build and the bridge, which
  used to report a fixed "0.9.0".
- Fix: an explicit `null` for an optional input is accepted everywhere. Fourteen inputs
  (for example `live_get_session.include`, every `live_set_session` field,
  `live_transport.beats`, `live_get_tracks` and the view/recording tools) refused it with a
  validation error. The advertised schemas are unchanged.
- Fix: `live_get_arrangement` without `tracks` no longer refuses on a Set with more than 64
  tracks. A whole-Set read returns 256 clip rows per page and a `cursor`; call again with
  `cursor` to continue exactly where the page stopped, including inside a track with more than
  256 clips (that row says `partial`). A cursor is refused as `stale_cursor` when the Set
  changed between pages. (Replaces the `next_track` of an earlier unreleased build, which
  skipped the rest of such a track.)
- Fix: `live_transport` and `live_launch` reported "(not applied)" when the command succeeded
  but the state readback after it failed. They now return the command's reply with
  `settled` / `state` set to null and a `verification` message.
- Privacy: an unexpected error inside a batch write, undo/redo, clip readback or device load
  no longer echoes Live's exception text (which can contain paths or names) into the reply.
  Replies say the exception type and a stable code (for example
  `RuntimeError: write_failed`); deliberate refusals stay readable. Live's log records where
  it failed (code locations only) through one shared helper.
- Fix: a running cue add/delete operation kept writing after writes were switched off
  (`read_only`) or the needed permission was removed. It now rereads the policy before each
  change and stops: `partial` with the earlier results kept, or `failed` (`not_applied`) when
  nothing had changed yet. This includes the rename of a newly added cue, and any ending puts
  a moved playhead back and reports it (`playhead`). The reply no longer claims `undo_steps`.
- Security: `"replace"` on the clip-creating bridge methods must be a JSON boolean. A string
  such as `"true"` used to replace clips while the permission check saw no delete; it is now
  refused before any permission decision, and the gate and the handler read the flag the same
  way.
- Confirmations of deletes (`live_delete`, `live_set_cue_points` deletes and the replace modes
  of `live_create_clips` / `live_create_arrangement_clips`) list the objects read from Live
  just before asking (names, cue times, clip spans), and the write is bound to exactly those
  objects: if the Set changes while the form is open, the call refuses (`stale_target` /
  `target_changed`) instead of deleting something else. Bridge replace targets now carry
  `expect_clip` / `expect_replace`.
- Privacy: only deliberate refusals (a dedicated refusal class) are echoed; any other error,
  including a native `ValueError` from Live, is logged by type and location and reported
  without its text, on the Remote Script and the server.
- Fix: once a bridge call has written, a later failure in that call (state readback,
  `end_undo_step`) keeps the receipt instead of reporting "not applied". `live_launch` treats
  a malformed readback as a verification note.
- Fix: a second bounded recording while one runs is refused (`recording_active`); overlapping
  recordings used to leave recording armed and playback running.
- Fix: a long bridge command (for example creating many tracks) no longer comes back as "may
  have been applied" after 5 s while Live is still running it; the client waits for the reply
  up to the exchange deadline. Track batches are capped at what Live 12.2 finishes inside the
  bridge budget: 32 per create/delete call, 16 per duplicate call.
- Build: developer probe modules are no longer shipped in wheels built straight from the
  source tree; the distribution check refuses probes, caches and development directories.
- Docs: the README's list of tools that can take several undo steps is corrected.
- Fix: `live_plan_chain`/`live_build_chain` (chains and drum racks) failed on a running
  server: the confirmation cache rebound the module's plan store at import.
- Fix: a destructive confirmation's targets now travel inside the request that asked. They
  were cached by tool and arguments, so two identical concurrent calls could swap forms and
  one could delete what the other's human saw; declined or failed plans no longer linger.
- Fix: a deferred cue delete re-checks, just before toggling, that the confirmed cue is still
  the only cue at its time; otherwise it stops with nothing toggled.
- Fix: a bounded recording or cue task that times out, errors or loses the script session
  still runs its cleanup (recording off, transport stopped if the call started it, playhead
  back) and reports it in `result.cleanup`; the outcome stays `unknown`.
- Fix: `if_exists="replace"` (Session) and `replace: true` (Arrangement) into empty
  destinations no longer refuse before asking.
- Fix: the whole-Set `live_get_arrangement` cursor is an opaque, single-use token held by the
  Remote Script and bound to the Set's tracks (identity and order) and the read's arguments;
  a changed Set or other arguments refuse (`stale_cursor`, `cursor_mismatch`), an unknown
  token refuses `unknown_cursor`.
- Fix: replies no longer carry native exception text (preferences file, dev probes); a dev
  `ref_lab` failure reports "may have applied" instead of "not applied".

## [0.11.0] - 2026-11-11

Upgrade: reinstall the Remote Script (`abletonlivemcp-install`) and restart Live; server and
script must be the same version.

- `examples/filter_sweep_buildup.py`: a generic buildup on any Set over stdio. The owner-specific
  demo and restart scripts left this repository.
- `live_set_device_parameters` with display targets on two or more continuous parameters
  ("100 Hz", "25 %") no longer returns "partial" with "at most 129 display values": sample
  requests are grouped by the Remote Script's value budget.
- `live_hello` reports `read_only` and `dev_probes`, and `toolsets.how_to_enable`. The bridge
  config is re-read on every call; the read_only refusal says no restart is needed.
- The `clip.*` note-API probe flags are `null` (unknown) when no Session clip was sampled, for
  example on an Arrangement-only Set, instead of a misleading `false`.
- README documents the `toolsets` key in the bridge config. pytest runs against `src/`.
- The restart helper refuses to close Live while a non-Basic Set is open (`-Force` overrides).

- Buildup demo preserves existing Arrangement MIDI and uses a separate instrument effects
  bus with Wider, GHOST//PUMP, Auto Filter and inline Reverb/Delay. Reverb reaches 100% wet;
  wet FX switch off at DROP, restoring the dry beat. Apply FX and invite owner preview.
  Note generation requires both an explicit flag and a MIDI pitch map; occupied slots refuse.
- Session automation accepts 2-3 `points` with linear interpolation, using step insertion
  and interior-event deletion instead of dense steps. Live retains coincident boundary
  guards; `--shape` adjusts the demo's middle point. Native Bezier curvature is unavailable.

- Session-to-Arrangement copying via `live_create_arrangement_clips` (`kind: from_session`,
  `scene`, `start`), with bounds/overlap validation and clip readback. Optional `replace`
  requires delete permission and refuses clips extending outside the destination. Arrangement
  joins the default toolsets (36 default tools).
- Targeted P-19 on Live 12.2: PAD Session copy/delete/restore did not crash; its Frequency
  track lane survived deleting the copy (visible UI and automation_state=1). Other P-19
  operations remain disabled. Restart helper quotes Basic's path and verifies its window title.
- Automation steps now accept beat 0 (and refuse a zero-duration step at the clip end),
  allowing explicit drop/reset envelopes at the first beat.

- `automation` is now a default toolset (32 default tools); `live_set_automation` and
  `live_get_automation` accept a parameter name or index; `live_create_clips` gains
  `if_exists` (`error` | `skip` | `replace`); `live_launch` scene state reports real playback.
- `bridge.json` with a UTF-8 BOM is accepted.

## [0.10.0] - 2026-11-11

### Upgrade notes
- Reinstall the Remote Script (`abletonlivemcp-install`) and restart Live; server and script
  must be the same version.
- MIDI import/export now need `ABLETONLIVEMCP_FILE_ROOTS`; home and temp are no longer allowed.

### Changed
- Advertise typed outputs for all tools and bounded chain, browser, and note inputs.
- Core tool descriptions name the neighbouring tool to use instead.
- Developer probe modules and proof metadata are no longer shipped in wheels or source
  archives; the Remote Script loads probes all-or-none from a source checkout only.
- `ABLETONLIVEMCP_AUDIT=1` logs every allowed write (tool and permissions, no arguments).
- README documents Claude Code config scopes (user scope recommended) and first use on a real project.
- Add local transport/edit/files/delete permissions and optional read-only discovery.
- Require explicit MIDI file roots instead of granting home/temp access by default.
- Keep personal knowledge and development material local; check runtime-only archives
  and clean stdio wheel installation in CI. Preserve tests and their support files in Git.
- Existing private configs without a permission list retain their previous behavior;
  new configurations start read-only with transport/edit permissions only.

## [0.9.0] - 2026-11-11

First public beta for hands-on testing. Tested on Ableton Live 12.2/Windows; see
[validation and limitations](docs/validation.md). Read-only by default.

### Added
- 57 tools across core (30) and opt-in toolsets: mixer/routing, notes, clips, arrangement,
  automation, recording/view, racks/drums/Simpler, MIDI files, offline usage and labels.
- Optional local knowledge access, resources and ten workflow prompts; compact core schemas.
- One serial final Live scenario runner with scratch ownership and confirmation checks.
- Protocol 2 mutually authenticated, bounded bridge; transactional installer; private config file.
- Safety layer: object references with a generation counter, read-only policy (default), bounded mutation lease.
- Bounded browser paging/search and a verified device-load state machine (`pending/ready/failed/unknown`).
- Typed plans and receipts; stop-on-failure chain building with stock vocal presets.
- Handshake advertises the method list.

### Changed
- Remote Script handlers split into per-domain `dom_*.py` modules, each declaring its bridge methods;
  the safety gate merges them and refuses to import on a duplicate or malformed declaration.
- MCP tools split into `abletonlivemcp/tools/<domain>.py`; names, descriptions and schemas unchanged.

### Removed
- The external judge backend and its dependencies; the local rules judge is the only backend.

### Fixed
- A missing request parameter now returns a readable refusal ("not applied") instead of a generic error.
- Remote Script loads without `ctypes` (not available in Live's embedded Python).
- `generation` starts at a random number so a reloaded script never matches a stale client.
