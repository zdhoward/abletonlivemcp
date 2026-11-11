# Reference projects (read for ideas only)

Read 2026-11-11 on the owner's suggestion. **Licence rule:** Ziforge/ableton-liveapi-tools is
GPL-3.0 and ideoforms/pylive has no licence file (all rights reserved). Use them only to learn which
API surface exists and how others structure it. **Never copy code**; re-derive from the Live API
and our own probes.

## Ziforge/ableton-liveapi-tools (220 tools, Remote Script over TCP 9004)

- Same core design as ours: a socket thread queues commands, the main thread runs them from
  `update_display` (about 60 Hz), and responses return by request id. Nothing new to adopt.
- It has **no** `apply_note_modifications`, `add_warp_marker`, `move_device`, `begin_undo_step` or
  `insert_device`, so it cannot settle our open probes. Its `undo`/`redo` are bare, with no grouping.
- Its tool list is a breadth checklist. Features it lists that our parity matrix does not mention,
  checked against our P-01 dump (`docs/data/live-12.2-api.json`, run on Live 12.2.0):

| Feature | In the 12.2 dump? | Action |
|---|---|---|
| Jump to next/prev cue, `can_jump_to_*_cue` | yes (`Song`) | add to transport tools (cheap, read+control) |
| Tap tempo, nudge up/down, punch in/out | yes (`Song`) | transport; check the plan has all |
| Clip `ram_mode`, `start_time` | yes (`Clip`) | audio clip props |
| `Application.get_build_id`, `get_variant` | yes | add to `live_hello` |
| `Application.show_message` / `show_on_the_fly_message` | yes | skip (UI side effect) |
| `Track.is_grouped`, `group_track`, `is_foldable` | yes | track tools; check the plan |
| Follow actions, clip fades, annotations, track delay, `consolidate` | **absent under the names Ziforge uses** | gated; its tools for them likely fail on 12.2 |
| `send_midi_cc`, `send_program_change` | not in the Python API | skip (needs Max for Live) |
| `show_message_box`, `open_document` | absent | skip |

  Follow actions may exist under other member names; a keyword search for `follow` matched only
  `tempo_follower`, so treat as absent unless a probe finds them.
- GPL means we cannot vendor it. Treat as a checklist only.

## ideoforms/pylive (Python client over LiveOSC, 635 stars)

- Runs through the third-party LiveOSC Remote Script, not the native API, so it exposes less than we
  do. Value is ergonomics only.
- Ideas worth borrowing (independently implemented):
  - **Set scan cache** (`scan`, `load_or_scan`, `save`): a cached session snapshot keyed by the
    bridge generation could cut the 0.9 s per-call latency (memory: bridge latency floor).
  - **Lookup by name** (`get_track_named`, `get_group_named`): we plan `expect_name` already; a
    name selector for read tools may still help.
  - **Beat callbacks** (`wait_for_next_beat`): hints at a quantised-action wait. Out of v2 scope.
  - **Open a Set from a path** (`open`): our `scripts/live_restart.ps1` covers it for proofs. No MCP
    tool (outward and destructive).
- Its test Set (`tests/Tests Project`) is a minimal fixture layout; ours go under `tests/fixtures`.

## Actions

- Checked the plan: cue navigation, tap tempo, nudge, punch and group tracks are already in the
  matrix (`live_transport`, `live_set_session`, `live_get_tracks`). Nothing to add there.
- Only new item: `live_hello` gains `build_id` and `variant` (cheap, read-only).
- No code is taken from either project.
