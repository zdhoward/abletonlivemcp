# v2 detailed plan: parity and beyond (2026-11-11)

Builds on `v2-public-roadmap.md` (phases, principles), `docs/research/live-api-map.md` (API facts, cited as "map
§n") and `docs/research/mcp-excellence.md`. Those files are not repeated here. P0 (hygiene), P2 (packaging) and P6 (launch)
tickets stay in the roadmap. This plan covers P1 (core surface), P3 (resources/prompts), P4 (use cases), arrangement and
automation, and P5 (evals).

Fixed constraints: Live 12.2 is the floor, and 12.3+/12.4 names are gated by `probe()` via `hasattr`. The default is
read-only. Every write goes through the reference + generation gate, takes the lease while one is held, is read back and
returns a receipt. There is no arbitrary code-exec tool, and no raw LOM, `eval` or OSC passthrough, including in dev
probes. Real Live is the proof (`scripts/live_*.py`), with at most one small fake test per feature (lessons 2026-11-10).

Competitor sources: **not re-fetched this session.** The fetch failed, so the matrix comes from the planner's prior knowledge of these projects plus the roadmap's competitor notes. T-081 must verify every row against live repos before anything goes public.
- A = ahujasid/ableton-mcp: `MCP_Server/server.py`, plus the #142 gap map.
- U = uisato/ableton-mcp-extended: main server and UDP server.
- L = dreamrec/LivePilot: 57 domains.
- N = nozomi-koborinai/ableton-osc-mcp.
- P = adamjmurray/producer-pal: `ppal-*`.

---

## 1. Parity matrix

The status column uses these values:
- **Have**: wrapped at `e33066a`.
- **Part**: partly wrapped.
- **Plan**: planned in the ticket shown.
- **Won't**: no Live 12.2 API, outside the product, or against the safety rules.

The Who column lists the competitors that have the capability. A letter in parentheses means a partial implementation, a PR only, or a limitation.

| Capability | Who | Us | Ticket |
|---|---|---|---|
| **Session / transport** | | | |
| Session info / snapshot | AULNP | Have | T-010 (merge with transport) |
| Play / stop | AULNP | Have | T-010 `live_transport` |
| Continue, stop-all-clips, jump to time, jump by | ULNP | Plan | T-010 |
| Tempo | AULNP | Have | T-010 `live_set_session` |
| Time signature write | LP | Plan | T-010 |
| Tap tempo / nudge | L | Plan (gated P-01) | T-010 |
| Metronome, count-in | LN | Plan | T-010; count-in T-075 |
| Song key / scale | NLP | Plan | T-010 |
| Tuning system | L | Plan | T-075 |
| Undo / redo | LP (A PR) | Plan | T-010 `live_undo`, T-006 grouping |
| Link enable / start-stop sync | L | Plan | T-075 |
| Loop region, punch in/out | ULP (A PR) | Plan | T-010 |
| Session / arrangement record, overdub, record mode | LN (A PR) | Plan | T-073 |
| Capture MIDI, capture-and-insert scene | LP | Plan | T-073 |
| Exclusive arm / solo | L | Plan (read; gated P-01) | T-011 |
| Groove pool, song groove/swing amount | L | Plan | T-010 (amounts), T-075 (pool) |
| UDP realtime control | U | Won't | Bridge is request/response, about 0.9 s per call; batching instead |
| Raw OSC / raw LOM escape hatch | NP | Won't | Safety rule |
| **Tracks / mixer / routing** | | | |
| Create MIDI/audio track | AULNP | Have | T-011 batch `live_create_tracks` |
| Create return track | LNP | Plan | T-011 |
| Rename, colour | AULNP | Have | T-011 batch |
| Delete track / return | ULNP | Plan | T-017 |
| Duplicate track | LNP | Plan | T-017 |
| Mute / solo / arm / monitoring | ULNP | Plan | T-011 |
| Group fold | LP | Plan | T-011 |
| Create group from tracks | (U README) | Won't | No API (map §3.2) |
| Freeze / flatten | L | Won't unless P-01 finds an API | P-01 |
| Input/output routing (incl. Resampling) | LNP | Plan | T-011 (P-17) |
| Volume / pan / sends, in dB | U(vol/pan) LNP (A PR) | Plan | T-011 `live_set_mixer` |
| Master volume / pan / crossfader / cue | LNP | Plan | T-011 |
| Return and master device params | NLP | Plan | T-015 (`TrackSel` return/master) |
| Meters (track, master) | LN | Plan | T-011 (`include: meters`) |
| Mix snapshot capture / restore | LN | Plan | T-011 read + `live_set_mixer`; `mix_check` prompt T-021 |
| Autogain | N | Plan (prompt recipe on meters + mixer) | T-021 |
| Sidechain routing (Compressor) | LN | Plan | T-077 |
| Take lanes | LP | Plan | T-071 |
| **Scenes** | | | |
| Create / rename / fire | ULNP | Have | T-012 batch |
| Delete / duplicate scene | ULP | Plan | T-017 |
| Scene colour, tempo, time signature | LP | Plan | T-012 |
| Scene follow actions | L | Won't | No follow-action API in 12.2 (map §4); P-01 confirms |
| Capture playing clips into scene | LP | Plan | T-073 |
| Scene clip matrix read | L | Plan | T-012 `include_slots` |
| **Clips / notes** | | | |
| Create MIDI session clip | AULNP | Have | T-013 batch |
| Audio clip from file (session) | AUN(L) | Plan | T-013 (P-08) |
| Fire / stop clip, fire empty slot | AULNP | Have (fire/stop) | T-012 `live_launch` |
| Delete clip | AULNP | Plan | T-017 |
| Duplicate clip (slot to slot) | LNP | Plan | T-017 |
| Clip name / colour / loop / markers | AULNP | Part (name read) | T-013 |
| Launch mode / quantization / legato / velocity amount | L | Plan | T-013 |
| Audio clip gain / pitch / warp mode / warping | LNP (A PR) | Plan | T-013 |
| Warp markers | L(M4L) | Plan, no M4L needed | T-074 |
| Crop / duplicate loop | (N no) | Plan | T-074 |
| Clip follow actions | UL | Won't | No API (map §4) |
| Add notes | AULNP | Have | T-014 `live_edit_notes` |
| Read notes with ids, probability, velocity deviation, release | UL | Part (no ids) | T-014 |
| Modify / remove / remove by id / replace | ULP (A PR) | Plan | T-014 |
| Quantize, transpose, duplicate region | UL | Plan | T-014 |
| Randomize timing, set probability | U | Plan (`modify` with fields; randomness stays in the model) | T-014 |
| Text / bar-beat note notation | NP | Won't-yet (JSON in beats; `bar:beat` helper in descriptions) | T-022 |
| Clip groove assign | L | Plan | T-075 |
| MIDI file import / export | L | Plan | T-078 |
| Clip scale / key consistency check | L | Plan (prompt over notes + song scale) | T-021 |
| Audio to MIDI (harmony/melody/drums) | P | Plan | T-031 (P-13) |
| **Arrangement** | | | |
| Read arrangement clips | AULNP | Plan | T-070 |
| Create arrangement MIDI / audio clip | ULP | Plan | T-071 (P-19) |
| Session clip to arrangement | AULNP | Plan | T-071 |
| Move / trim / split arrangement clip | P (L part) | Plan (move = duplicate + delete; trim = markers; split gated by P-19) | T-071 |
| Delete arrangement clip | ULNP | Plan | T-071 |
| Arrangement notes read/write | L (A read) | Plan (`ClipAddr` arrangement form) | T-071 |
| Locators: create / rename / delete / jump, race-free | AULP (A racy) | Plan | T-070 (P-16) |
| Write whole arrangement from sections | N | Plan (prompt `arrange_sections` over T-070/T-071) | T-021 follow-up |
| Back to arranger, view switch | AUP | Plan | T-010 (`back_to_arranger`), T-076 |
| **Automation** | | | |
| Session-clip envelope read / write / clear | ULNP | Plan | T-072 (P-10) |
| Arrangement automation write | L | Won't on 12.2 | `automation_envelope` returns None for arrangement clips (map §3.2). We refuse with that reason; L's claim is unverified |
| Shapes / recipes (sweep, pump) | L | Plan (`shape` param + prompt) | T-072 |
| Re-enable automation, automation state | L | Plan | T-015 |
| **Devices** | | | |
| Load native instrument / effect | AULNP | Part (audio effects on audio tracks only) | T-016 |
| Load VST/AU | ULP | Part (plugins root, audio tracks) | T-016 |
| Load M4L device | LP | Plan (`max_for_live` root) | T-016 |
| Load preset / navigate presets | NLP U | Plan (browser preset items; plugin `selected_preset_index`) | T-016, T-077 |
| Load into rack chain | LP | Plan (P-14) | T-016 |
| Native insert at index (12.3+) | L | Gated | T-016 uses `insert_device` when probe says present |
| Get / set params, batch | AULNP | Have | T-015 extends |
| Set param by display text / value item | N | Plan | T-015 |
| Reset param to default | - | Plan (beyond) | T-015 |
| Device on/off, rename, collapse | U | Plan | T-015 `live_set_devices` |
| Delete device | ULNP | Plan | T-017 |
| Move / reorder device | LP | Plan | T-015 `live_move_device` (P-04) |
| Duplicate device | P | Won't unless P-01 finds an API | P-01 |
| Hidden / unconfigured plugin params | L(M4L) | Plan (read names only via `get_parameter_names`, P-15) | T-077 |
| Rack chains / macros / variations read+set | LP | Plan | T-050 |
| Macro mapping / rename | (P read) | Won't on 12.2 API; experimental `.adg` route | T-052 (P-29) |
| Chain mixer | LP | Plan | T-050 |
| Group existing devices into rack | P (12.3+?) | Plan (move into new rack chain, P-04) | T-051 |
| Drum pads read; choke / out note / mute / solo; copy pad | ULNP | Plan | T-030 |
| Add drum pad with sample | L(M4L) | Plan (Conversions/hotswap, P-13/P-14) | T-033 |
| Simpler / slices | L(M4L) NP | Plan | T-032 |
| Wavetable mod matrix, device enum lists | L | Plan (lists + selectors) | T-077 |
| A/B compare | LP | Won't on 12.2 (12.3 Max only) | gated note |
| Device intent presets | N | Have (`live_plan_chain` stock-first presets) | T-018 extends |
| Device health / stuck dialog | L | Plan | T-019 (`live_hello` dialogs + CPU) |
| **Browser / library** | | | |
| Browse tree / folder | AULN | Have | T-016 (roots merged into list) |
| Search by name | LNP | Have (bounded) | - |
| Tags / categories / similar (12.4+) | P | Won't on 12.2 | gated |
| Plugin list | ULP | Plan (`plugins` root list) | T-016 |
| Preview / audition | LN | Plan | T-076 |
| Device knowledge base / atlas | L | Plan (`knowledge/` + resources) | T-062 |
| Sample search: Splice / catalog | LN | Won't (external service) | - |
| Usage frequency across projects | - | Plan (beyond: UC1/UC6) | T-034, T-061 |
| Labels / colour tags for plugins (UC2) | - | Plan (own labels via `set_data` + sidecar; native tags Won't, no API) | T-060 |
| **Audio / analysis / generation** | | | |
| Bounce / export without dialog | N | Plan-later (prompt recipe: Resampling route + record; no render API) | T-073 + prompt |
| Realtime spectrum / loudness | L(M4L) | Won't (needs M4L) | - |
| Offline WAV loudness / peak | LN | Backlog (stdlib WAV only) | T-083 |
| Key / BPM / chord detection of audio | LN | Won't (out of scope) | - |
| ElevenLabs TTS / SFX | U | Won't (external service) | - |
| **AI workflow** | | | |
| Theory / generation / composer / semantic moves | L | Won't as tools; prompts + model reasoning | T-021 |
| Taste learning / feedback tools | ALN | Won't (no telemetry) | - |
| Plan / preview / commit | L(experiments) | Have (`plan_chain` / `build_chain`) | T-033, T-051, T-063 extend |
| Persistent project memory | LP | Plan (`Song.set_data` labels) | T-060 |
| Subagents | P | Won't (client concern) | - |
| **MCP quality** | | | |
| Toolsets / profiles | L GitHub | Plan | T-002 |
| Diagnose / doctor | NL | Part (`live_hello`) | T-019; doctor in roadmap P2 |
| Read-only default, leases, readback, receipts | - | Have (differentiator) | all |
| Undo grouping per tool call | - | Plan (beyond) | T-006 |
| Elicitation for destructive ops | - | Plan (beyond) | T-007 |

---

## 2. Target tool surface

### 2.1 Conventions (all tools)

**Selectors** (`models.py`, T-002). Indices are 0-based. Tools take indices. The server reads references and writes in the same call, so the model never handles references.
- `TrackSel` is one of:
  - `int`: a regular track.
  - `"return:N"`: a return track.
  - `"master"`.
- `ClipAddr` is `{track:int, scene:int}`. The `arrangement` toolset also accepts the form `{track:int, arrangement:int}`, where the index is into `track.arrangement_clips` sorted by start.
- `DevicePath` is a list that alternates device and chain indices: `[device]` or `[device, chain, device, ...]`. An element `"pad:N"` selects drum pad note N. The maximum depth is 6.
- `ParamSel` is either `int`, or a `str` that matches exactly one parameter name (otherwise the call is refused as `ambiguous`).
- Every batch target may carry `expect_name`. If the indexed object's current name differs, the call is refused with `name_mismatch`. `live_delete` requires it.

**Batch rules**:
- At most 64 targets per call.
- Every target is validated before any write, so a validation failure means nothing is applied.
- Write sequence: one read (to get references), one write call, and one readback. The readback is merged into the write reply whenever possible, because each call costs about 0.9 s.

**Reply shape**:
- Write reply: `{applied:[readback rows], generation, undo_steps, receipt}`.
- Read reply: `{items, truncated, cursor}`, paged.
- `response_format: concise|detailed` (default `concise`) is available on every list or read tool.
- Strings that come from Live are wrapped with `_untrusted`.

**Annotation presets** (`server.py`):

| Preset | readOnlyHint | destructiveHint | idempotentHint |
|---|---|---|---|
| READ | T | F | T |
| CREATE | F | F | F |
| OVERWRITE | F | T | T |
| CONTROL (audible state only) | F | F | F |
| DESTRUCTIVE (+ elicitation, T-007) | F | T | F |

All presets set openWorld F.

**Bridge class**: `read`, `write` or `control` (leases only). New bridge methods are declared next to their handler (T-001). A method that is missing from the declarations is refused.

**Toolset switch**:
- Set with `ABLETONLIVEMCP_TOOLSETS` or the config key `toolsets`. The default is `core`.
- `all` turns on every toolset except `experimental`.
- An unknown name fails at startup.
- Read-only always wins over the toolset choice: write tools stay registered, but they refuse.
- `live_hello` lists the enabled and available toolsets.

### 2.2 Default toolset `core` (31 tools: 12 read, 19 write)

| Tool | Params (beyond `response_format`) | Preset / bridge class | Live API wrapped |
|---|---|---|---|
| `live_hello` | - | READ / read | `Application.get_major/minor/bugfix_version`, `get_variant`, `open_dialog_count`, `current_dialog_message`, `average_process_usage`; `probe()` (all 12.3+/12.4 gates) |
| `live_get_session` | `include?: [transport, loop, scale, groove, selection, undo]` | READ / read | `Song.tempo`, `signature_*`, `is_playing`, `current_song_time`, `loop*`, `punch_*`, `metronome`, `root_note`, `scale_name/mode`, `groove_amount`, `swing_amount`, `can_undo/redo`, `view.selected_*` |
| `live_get_tracks` | `tracks?: TrackSel[]`, `include?: [mixer, devices, slots, routing, meters, groups]` | READ / read | `Song.tracks`, `return_tracks`, `master_track`; `Track.name/color_index/mute/solo/arm/current_monitoring_state/is_foldable/fold_state/group_track/*_routing_*/output_meter_*`; `mixer_device.*`; device tree (depth ≤ 3) |
| `live_get_scenes` | `include_slots?: bool` | READ / read | `Scene.name/color_index/tempo/tempo_enabled/time_signature_*`, `ClipSlot.has_clip/is_playing/is_triggered` |
| `live_get_clips` | `clips?: ClipAddr[]`, `track?`, `scene?` | READ / read | `Clip.name/color_index/length/looping/loop_start/loop_end/start_marker/end_marker/launch_mode/launch_quantization/legato/velocity_amount/muted/is_audio_clip/warping/warp_mode/gain/gain_display_string/pitch_coarse/pitch_fine/signature_*`, `warp_markers` (detailed) |
| `live_get_notes` | `clip: ClipAddr`, `pitch_from=0`, `pitch_span=128`, `time_from=0`, `time_span?`, `limit=500`, `cursor?` | READ / read | `get_notes_extended` (`note_id`, `probability`, `velocity_deviation`, `release_velocity`) |
| `live_get_device_parameters` | `track: TrackSel`, `device: DevicePath`, `names?: str[]`, `limit=64`, `cursor?` | READ / read | `DeviceParameter.name/value/min/max/default_value/is_quantized/value_items/is_enabled/automation_state/str_for_value` |
| `live_browser_list` | `root?` (omit for the roots), `path?`, `limit=200`, `cursor?` | READ / read | `Browser.<roots>` (+`max_for_live`, `clips`, `user_folders`), `BrowserItem.children/uri/is_loadable/is_device` |
| `live_browser_search` | `root`, `query`, `limit=25`, `cursor?` | READ / read | same (bounded walk) |
| `live_get_operation` | `operation` | READ / read | (receipt store) |
| `live_plan_chain` | `track: TrackSel`, `stages`, `preferences?` | READ / read | browser reads |
| `live_vocal_presets` | - | READ / - | (static) |
| `live_set_session` | `tempo?`, `signature?:[n,d]`, `metronome?`, `loop?:{on,start,length}`, `punch?:{in,out}`, `scale?:{root_note,scale_name,scale_mode}`, `groove_amount?`, `swing_amount?` | OVERWRITE / write (generation) | `Song` setters |
| `live_transport` | `action: play\|stop\|continue\|stop_all_clips\|jump_to\|jump_by\|next_cue\|prev_cue\|tap_tempo\|back_to_arranger`, `beats?` | CONTROL / write (generation) | `start_playing`, `stop_playing`, `continue_playing`, `stop_all_clips`, `current_song_time=`, `jump_by`, `jump_to_next_cue/prev_cue`, `tap_tempo` (gated), `back_to_arranger` |
| `live_undo` | `action: undo\|redo`, `steps=1..10` | DESTRUCTIVE / write (generation) | `Song.undo/redo/can_undo/can_redo` |
| `live_create_tracks` | `tracks: [{kind: midi\|audio\|return, index=-1, name?, color_index?}]` | CREATE / write (generation) | `create_midi_track`, `create_audio_track`, `create_return_track` |
| `live_set_tracks` | `targets: [{track, expect_name?, name?, color_index?, mute?, solo?, arm?, monitoring?: in\|auto\|off, fold?, input_routing?:{type,channel}, output_routing?:{type,channel}}]` | OVERWRITE / write | `Track.*` setters; routing by `display_name` match against `available_*` |
| `live_set_mixer` | `targets: [{track, expect_name?, volume_db?\|volume?, pan?(-1..1), sends?:{idx: db\|normalized}, activator?, crossfade?: A\|none\|B, crossfader?, cue_volume_db?}]` | OVERWRITE / write | `mixer_device.volume/panning/sends/track_activator/crossfade_assign`; master `crossfader/cue_volume`. dB is converted to a value by bisection over `str_for_value` inside one bridge call (P-06) |
| `live_create_scenes` | `scenes: [{index=-1, name?, color_index?, tempo?, signature?}]` | CREATE / write (generation) | `create_scene`, `Scene.*` |
| `live_set_scenes` | `targets: [{scene, expect_name?, name?, color_index?, tempo?\|null, signature?\|null}]` | OVERWRITE / write | `Scene.name/color_index/tempo/tempo_enabled/time_signature_*` |
| `live_launch` | `action: fire\|stop`, `targets: [{clip}\|{slot: ClipAddr}\|{scene}\|{track, all: true}]` | CONTROL / write | `Clip.fire/stop`, `ClipSlot.fire/stop`, `Scene.fire`, `Track.stop_all_clips` |
| `live_create_clips` | `clips: [{track, scene, kind: midi\|audio, length_beats?, file?: abs path, name?, color_index?, notes?}]` | CREATE / write | `ClipSlot.create_clip`, `ClipSlot.create_audio_clip` (12.2), `add_new_notes` |
| `live_set_clips` | `targets: [{clip, expect_name?, name?, color_index?, looping?, loop?:[s,e], markers?:[s,e], launch_mode?, launch_quantization?, legato?, velocity_amount?, muted?, gain?, pitch?:{coarse,fine}, warping?, warp_mode?, signature?}]` | OVERWRITE / write | `Clip.*` setters, written in an order that keeps them valid (widen before narrowing) |
| `live_edit_notes` | `clip`, `add?: Note[]`, `modify?: [{note_id, pitch?, start_time?, duration?, velocity?, mute?, probability?, velocity_deviation?, release_velocity?}]`, `remove_ids?`, `remove_range?`, `quantize?:{grid, amount}`, `transpose?:{semitones, ids?}`, `duplicate_region?:{start,length,dest,pitch?}` | OVERWRITE / write | `add_new_notes`, `apply_note_modifications`, `get_notes_by_id`, `remove_notes_by_id`, `remove_notes_extended`, `quantize`, `duplicate_region` |
| `live_set_device_parameters` | `writes: [{track, device: DevicePath, parameter: ParamSel, value?\|display?\|reset?, re_enable_automation?}]` | OVERWRITE / write | `DeviceParameter.value`, `value_items`, `default_value`, `re_enable_automation` |
| `live_set_devices` | `targets: [{track, device, expect_name?, on?, name?, collapsed?}]` | OVERWRITE / write | `parameters[0]` (Device On), `Device.name`, `view.is_collapsed` |
| `live_move_device` | `track`, `device: DevicePath`, `to_track`, `to_chain?: DevicePath`, `position` | OVERWRITE / write | `Song.move_device`, `find_device_position` |
| `live_load_item` | `track: TrackSel`, `root`, `path`, `into?: DevicePath` (a rack chain), `after?` | CREATE / write (async op) | `Browser.load_item`, `Song.view.selected_track`, `select_device`, `RackDevice.view.selected_chain`; `Track.insert_device` when gated in |
| `live_build_chain` | `plan_id`, `accept_omissions` | CREATE / write + lease | as now + `move_device`; progress notifications |
| `live_delete` | `targets: [{kind: track\|return\|scene\|clip\|device, ...selector, expect_name}]` | DESTRUCTIVE / write | `Song.delete_track/delete_return_track/delete_scene`, `ClipSlot.delete_clip`, `Track/Chain.delete_device` |
| `live_duplicate` | `targets: [{kind: track\|scene\|clip, ...selector, to?: ClipAddr}]` | CREATE / write | `Song.duplicate_track/duplicate_scene`, `ClipSlot.duplicate_clip_to`, `Track.duplicate_clip_slot` |

Renames: nothing has been tagged yet, so no aliases are needed (roadmap principle 5).

| Old tool | New tool |
|---|---|
| `live_session_info`, `live_get_transport` | `live_get_session` |
| `live_tracks` | `live_get_tracks` |
| `live_list_scenes` | `live_get_scenes` |
| `live_browser_roots` | `live_browser_list()` |
| `live_device_parameters` | `live_get_device_parameters` |
| `live_get_clip` | `live_get_clips` |
| `live_add_notes` | `live_edit_notes` |
| `live_create_track` | `live_create_tracks` |
| `live_set_track` | `live_set_tracks` |
| `live_set_transport` | `live_set_session` + `live_transport` |
| `live_create_scene` | `live_create_scenes` |
| `live_set_scene_name` | `live_set_scenes` |
| `live_fire_scene`, `live_fire_clip`, `live_stop_clip` | `live_launch` |
| `live_create_clip` | `live_create_clips` |

### 2.3 Opt-in toolsets

| Toolset | Tool | Params | Preset | Live API |
|---|---|---|---|---|
| `drums` (UC1) | `live_get_drum_rack` | `track`, `device` | READ | `RackDevice.drum_pads/visible_drum_pads`, `DrumPad.name/note/mute/solo/chains`, `DrumChain.out_note/choke_group` |
| | `live_set_drum_pads` | `track`, `device`, `pads?:[{note, mute?, solo?, choke_group?, out_note?}]`, `copy?:[{from,to}]`, `clear?:[note]` | OVERWRITE (clear: DESTRUCTIVE) | `DrumPad.mute/solo`, `DrumChain.choke_group/out_note`, `RackDevice.copy_pad`, `DrumPad.delete_all_chains` |
| | `live_convert` | `kind: audio_to_midi_{harmony\|melody\|drums}\|drum_rack_from_clip\|simpler_track_from_clip\|sliced_simpler_to_drum_rack\|track_from_drum_pad\|devices_to_drum_pad`, `source` | CREATE | `Live.Conversions.*` (map §3.3) |
| | `live_get_simpler` / `live_set_simpler` | `track`, `device`, fields (`playback_mode`, `voices`, `retrigger`, `reverse`?, markers, slices add/move/remove/clear) | READ / OVERWRITE | `SimplerDevice.*`, `Sample.*` |
| | `live_plan_drum_rack` | `samples:[{file\|browser_path, role}]` or `usage_report`, `layout: gm` | READ | browser reads, file checks |
| | `live_build_drum_rack` | `plan_id` | CREATE + lease + progress | route chosen by P-13/P-14 |
| `racks` (UC4) | `live_get_rack` | `track`, `device` | READ | `chains`, `return_chains`, macro params, `visible_macro_count`, `has_macro_mappings`, `variation_count`, `selected_variation_index`, `Chain.mixer_device` |
| | `live_set_rack` | `macros?:[{index, value}]`, `visible_macros?`, `variation?: store\|recall\|recall_last\|delete\|select:N`, `randomize?`, `chains?:[{chain, name?, color_index?, mute?, solo?, volume_db?, pan?}]` | OVERWRITE | `add_macro/remove_macro`, `store_variation`, `recall_selected_variation`, `recall_last_used_variation`, `delete_selected_variation`, `randomize_macros`, `Chain.*` |
| | `live_plan_fx_rack` / `live_build_fx_rack` | `track`, `groups:[{macro_name, targets:[{device, parameter, min, max}]}]` | READ / CREATE + lease | browser load of an empty Audio Effect Rack, `Song.move_device` into its chain, macro values. Returns exact manual mapping steps, because the 12.2 API has no macro mapping |
| `experimental` (off, even in `all`) | `live_write_rack_preset` | same groups + `name` | CREATE (writes new files only) | offline `.adg` generation into `User Library/AbletonLiveMCP/`, then `load_item` (P-29) |
| `organize` (UC6) | `live_get_labels` / `live_set_labels` | `scope: set\|global`, `items:[{kind, key, labels, category}]` | READ / OVERWRITE (+ elicitation on replace) | `Song.get_data/set_data` + sidecar `~/.abletonlivemcp/labels.json` |
| | `live_plan_organize` | `strategy: by_role\|by_usage`, `apply_colors` | READ | tracks + labels + usage. The plan is applied with `live_set_tracks` |
| `als` | `live_scan_projects` | `roots?` (MCP roots or config allowlist), `since_days?`, `folder_glob?`, `limit` | READ | offline `.als` reader (gzip XML, entity/size limits) |
| | `live_usage_report` | `kind: samples\|devices\|plugins`, `scan_id`, `top` | READ | usage index |
| `library` | `live_knowledge_search` / `live_knowledge_read` | `query` / `id` | READ | `knowledge/`, path-confined. Also served as `knowledge://` resources |
| `arrangement` | `live_get_arrangement` | `tracks?`, `range?`, `include?: [clips, cues, take_lanes]` | READ | `Track.arrangement_clips`, `take_lanes`, `Song.cue_points`, `song_length` |
| | `live_create_arrangement_clips` | `[{track, kind: midi\|audio\|from_session, start, length?, file?, source?: ClipAddr, take_lane?}]` | CREATE | `Track.create_midi_clip` (12.1.10), `create_audio_clip` (12.2), `duplicate_clip_to_arrangement`, `create_take_lane`, `TakeLane.create_*_clip` |
| | `live_edit_arrangement_clips` | `[{clip, move_to?, markers?, loop?, delete?, split_at?}]` | OVERWRITE (delete: DESTRUCTIVE) | markers, `Track.delete_clip`, move = duplicate + delete (P-19) |
| | `live_set_cue_points` | `[{action: add\|rename\|delete\|jump, time?, cue?, name?}]` | OVERWRITE | `set_or_delete_cue` (after a `current_song_time` write and readback), `CuePoint.name/jump` |
| `automation` | `live_get_automation` | `clip`, `track`, `device`, `parameter`, `range?` | READ | `Clip.automation_envelope`, `Envelope.events_in_range/value_at_time` |
| | `live_set_automation` | `clip`, param selector, `action: steps\|shape\|clear\|clear_all`, `steps?:[{time,length,value}]`, `shape?:{kind: linear\|exp\|sine\|square, from, to, start, length, resolution}` | OVERWRITE | `create_automation_envelope`, `Envelope.insert_step/delete_events_in_range`, `clear_envelope`, `clear_all_envelopes` |
| `recording` | `live_record` | `action: session_record\|arrangement_record\|overdub\|record_mode\|trigger_session_record\|capture_midi\|capture_and_insert_scene`, `value?`, `length?`, `destination?` | CONTROL (capture: CREATE) | `session_record`, `record_mode`, `arrangement_overdub`, `trigger_session_record`, `capture_midi`, `can_capture_midi`, `capture_and_insert_scene` |
| `editing` | `live_edit_audio_clip` | `clip`, `warp_markers?:{add,move,remove}`, `crop?`, `duplicate_loop?` | OVERWRITE | `add/move/remove_warp_marker`, `crop`, `duplicate_loop` |
| `song` | `live_get_song_advanced` / `live_set_song_advanced` | `grooves`, `clip_groove`, `tuning`, `link`, `count_in` | READ / OVERWRITE | `groove_pool.grooves`, `Groove.*`, `Clip.groove`, `tuning_system.*`, `is_ableton_link_enabled`, `*_start_stop_sync_enabled`, `count_in_duration` |
| `view` | `live_view` | `action: show\|hide\|focus\|zoom\|scroll`, `view` | CONTROL | `Application.View.*` |
| | `live_select` | `track?`, `scene?`, `device?`, `clip?`, `chain?`, `pad?` | CONTROL | `Song.view.selected_*`, `select_device`, `RackDevice.view.selected_chain/selected_drum_pad` |
| | `live_preview` | `action: play\|stop`, `root`, `path` | CONTROL | `Browser.preview_item/stop_preview` |
| `devices-advanced` | `live_get_device_extras` | `track`, `device` | READ | `PluginDevice.presets/selected_preset_index/get_parameter_names`, `MaxDevice.get_bank_*`, Wavetable/HybridReverb/Eq8/Compressor/Roar/Looper lists |
| | `live_set_device_extras` | `track`, `device`, `preset_index?`, `option?:{name, value}` | OVERWRITE | `selected_preset_index`, `Eq8.edit_mode/oversample`, Compressor sidechain routing, Wavetable/IR selection |
| `files` | `live_import_midi` / `live_export_midi` | `file` (roots-confined), `clip` | CREATE (export writes new files only) | stdlib SMF parser/writer + `add_new_notes` / `get_notes_extended` |

**Resources** (T-020; each one is also reachable through a tool):
- `live://session`
- `live://tracks`
- `live://track/{t}`
- `live://track/{t}/device/{path}/parameters`
- `live://operation/{id}`
- `docs://conventions/units`
- `docs://safety`
- `knowledge://{id}`

**Prompts** (T-021):
- `vocal_chain`
- `organize_session`
- `setup_scene`
- `mix_check`
- `explain_chain`
- `diagnose_connection`
- `safe_tweak`
- `build_drum_rack`
- `macro_fx_rack`
- `arrange_sections`

`SKILL.md` mirrors the prompts.

---

## 3. Tickets

### Shared conventions

**Files**:
- Per-domain Remote Script modules are flat files, `remote_script/AbletonLiveMCP/dom_<d>.py`. The installer copies only flat `*.py` files (`install.py` `glob("*.py")`), so a subpackage would not install.
- Server tool modules go in `src/abletonlivemcp/tools/<d>.py`.
- Each domain gets one tool-surface snapshot, `tests/tool_surface/<d>.json`.
- Each domain gets one real-Live proof, `scripts/live_<d>_test.py`, built on the harness from T-004.
- Each domain gets at most one fake test, `tests/test_<d>.py`.

**Proof contract**:
- Exit code 0 means pass, 1 means a required check failed, 2 means the proof could not run.
- The proof drives the real stdio server, creates its own scratch objects in the disposable Set, never touches pre-existing objects, and checks readback and refusals.
- Evidence goes in `docs/release/v2/<ticket>.md`, with Live version, module list from `Log.txt`, and output.

**Real Live is a single shared resource.** Implementers code in parallel, but the orchestrator runs every proof and probe one at a time. It starts, closes and reloads Live itself (memory: Live lifecycle autonomy).

**Hot files are pre-split in Wave 0**:
- T-001 creates every planned `dom_*.py` and `tools/*.py` as an empty stub.
- T-001 also gives `tools/__init__.py` and `handlers.py` a fixed import list naming all of them.
- As a result, later tickets touch only their own domain files.

### Wave 0: foundations (in order; inside a row, the tickets run in parallel)

| Order | Tickets |
|---|---|
| 1 | T-001 |
| 2 | T-002, T-003, T-004 (disjoint files) |
| 3 | T-005, with P-01 running in real Live |
| 4 | T-006 (after P-03), T-007 |

**T-001 Split hot files, no behaviour change.** Opus, high.
- **Goal**:
  - Split `handlers.py` by domain into `dom_common.py` (selectors, limits, `_number`, notes validation), `dom_session.py`, `dom_tracks.py`, `dom_scenes.py`, `dom_clips.py`, `dom_notes.py`, `dom_devices.py` and `dom_browser.py`.
  - Create empty stubs for `dom_drums.py`, `dom_racks.py`, `dom_arrangement.py`, `dom_automation.py`, `dom_recording.py`, `dom_editing.py`, `dom_song.py`, `dom_view.py`, `dom_devx.py` and `dom_labels.py`.
  - Each module exports `METHODS = {name: (handler, kind, targets)}`.
  - `safety.py` builds `CLASSIFICATION` and `TARGETS` by merging the modules. A duplicate or unclassified name fails import, so the gate stays fail-closed.
  - `handlers.py` keeps `make_dispatch`, `probe` and `_Params`, and re-exports what the tests import.
  - Split `server.py` the same way: core helpers (`_register`, `_call`, `_settled`, `_untrusted`) stay in `server.py`, and tools move into `tools/{session,tracks,scenes,clips,notes,devices,browser,chain}.py` plus stubs for the opt-in toolsets.
- **Files**: `remote_script/AbletonLiveMCP/{handlers,safety,dom_*}.py`, `src/abletonlivemcp/{server.py,tools/*}`, `tests/test_handlers*.py` (imports only).
- **Live API**: none new.
- **Accept**:
  - `pytest` passes.
  - `scripts/live_write_test.py`, `live_clip_test.py` and `live_chain_test.py` exit 0 in real Live.
  - `Log.txt` shows every `dom_*` module loaded.
  - A reinstall with `abletonlivemcp-install` copies all modules (lesson: real-Live load check).
- **Deps**: none.

**T-002 MCP surface infrastructure.** Opus, medium. This ticket touches the mutation wrapper.
- **Goal**:
  - Add the toolset registry and env/config switch, with startup failure on unknown names.
  - Add annotation presets (READ, CREATE, OVERWRITE, CONTROL, DESTRUCTIVE) and a `title` on every tool.
  - Declare an `outputSchema` from typed return models.
  - Add a `response_format` helper.
  - Add the shared selectors (`TrackSel`, `ClipAddr`, `DevicePath`, `ParamSel`, `expect_name`).
  - Attach the lease automatically to every write (replace `WRITE_METHODS`).
  - Add the per-module tool-surface snapshot test and a total size budget (serialized `list_tools` ≤ 40 KB for `core`).
- **Files**: `src/abletonlivemcp/{server.py,models.py,tools/__init__.py}`, `tests/test_tool_surface.py`, `tests/tool_surface/`.
- **Accept**:
  - `scripts/stdio_smoke.py` lists the tools with titles, annotations and output schemas.
  - `ABLETONLIVEMCP_TOOLSETS=bogus` exits non-zero.
  - `live_hello` reports the enabled toolsets in real Live.
- **Deps**: T-001.

**T-003 Fixed-table dev probe runner.** Opus, medium. This is safety-seam work.
- **Goal**:
  - Add a bridge method `probe_run(name)` with probes `probe_pNN.py` (stubs pre-created for P-01 to P-29) and a fixed list in `dom_probe.py`.
  - Introspection probes are classed `read`.
  - Behavioural probes are classed `write`. They also require `"dev_probes": true` in the private config, the lease, and only scratch objects they created themselves.
  - Probes are never registered as MCP tools, and there is no argument-driven attribute access. Each probe is a fixed function.
- **Files**: `remote_script/AbletonLiveMCP/{dom_probe.py,probe_p*.py}`, `scripts/live_probe_run.py`, `docs/release/probes/`.
- **Accept**: `live_probe_run.py P-01` writes `docs/release/probes/P-01.md` and `docs/data/live-12.2-api.json` with owner paths stripped. With `dev_probes` absent, the run is refused.
- **Deps**: T-001.

**T-004 Live proof harness.** Sonnet, medium.
- **Goal**: Write `scripts/live_harness.py`. It runs a stdio MCP client against the server, provides `Checks` and the exit codes, has `scratch_track(kind)` and `expect_refusal(code)`, and writes the evidence file. Port `live_write_test.py` onto it as the example.
- **Files**: `scripts/live_harness.py`, `scripts/live_write_test.py`.
- **Accept**: the ported test exits 0 in real Live, with the same checks as before.
- **Deps**: T-001.

**T-005 Reference kinds for the full tree.** Opus, high.
- **Goal**: Extend `Safety._valid` and the issuing code. New kinds:
  - `return_track`, `master` (pinned identity)
  - nested `device` and `chain` along a `DevicePath`, with layout snapshot per level
  - `drum_pad` (note index)
  - `mixer_param` (parameter of `mixer_device`)
  - `arr_clip` (member of `track.arrangement_clips`)
  - `cue` (member of `cue_points`)
  - `take_lane`
  - The existing `scene` kind for scene-level writes.
- **Files**: `safety.py`, `dom_common.py`, one test.
- **Accept**: `scripts/live_refs_test.py` checks the following in real Live:
  - Each new kind validates.
  - Each kind refuses after its object is deleted, moved or reordered.
  - All references refuse after a Set change.
- **Deps**: T-001, P-01.

**T-006 One undo step per tool call.** Opus, medium.
- **Goal**: Wrap every write dispatch in `begin_undo_step`/`end_undo_step` (in a `finally`) and report `undo_steps: 1`. Skip the wrapping if P-03 fails, and record why.
- **Files**: `handlers.py` (dispatch only).
- **Accept**: `scripts/live_undo_test.py` makes a batch `live_set_tracks` on 3 scratch tracks, calls `Song.undo` once, and sees all 3 reverted.
- **Deps**: T-001, P-03.

**T-007 Elicitation for the DESTRUCTIVE preset.** Opus, medium.
- **Goal**: Before any DESTRUCTIVE tool, the server elicits a human confirm in form mode, listing the targets and their `expect_name`. When the client lacks the capability, it refuses with `refused:confirmation_unavailable` and nothing is applied. A model-supplied `confirm` argument is never accepted.
- **Files**: `server.py`, `tools/__init__.py`.
- **Accept**:
  - A fake-client test covers accept, decline and absent capability.
  - In real Live, a `live_delete` proof (T-017) is declined and the object is still present.
- **Deps**: T-002.

### Wave 1: probes (section 4)

Coding is parallel. Runs in real Live are serial. P-01 runs first, because its dump settles most `hasattr` questions.

### Wave 2: core surface

These tickets are all parallel, since each touches only its own `dom_<d>`, `tools/<d>`, `scripts/live_<d>_test.py` and snapshot. Every ticket depends on T-002, T-004 and T-005.

**T-010 Session and transport.** Sonnet, medium.
- **Tools**: `live_get_session`, `live_set_session`, `live_transport`, `live_undo`.
- **API**: see section 2.2.
- **Accept**: `live_session_test.py` checks the following:
  - It sets tempo, signature, loop and scale, then reads back and restores the originals.
  - It runs play → jump_to 8 → stop with readback of `current_song_time`.
  - `undo` reverts the last write.
  - `tap_tempo` is refused with `unsupported` if P-01 found no API.
- **Deps**: P-01, P-22.
- **Parallel with**: T-011 to T-015.

**T-011 Tracks, mixer, routing.** Sonnet, medium.
- **Tools**: `live_get_tracks`, `live_create_tracks`, `live_set_tracks`, `live_set_mixer`.
- **Accept**: `live_tracks_test.py` checks the following:
  - It creates a midi, an audio and a return track in one call.
  - It sets mute, solo, arm, monitoring and colour on all of them in one call.
  - It sets volume −6 dB with readback `-6.0 dB`, pan −0.5, and send A −12 dB.
  - It routes output to the return.
  - `expect_name` mismatch is refused.
  - Master volume is written and restored.
- **Deps**: P-06, P-17.

**T-012 Scenes and launch.** Sonnet, medium.
- **Tools**: `live_get_scenes`, `live_create_scenes`, `live_set_scenes`, `live_launch`.
- **Accept**: `live_scenes_test.py` checks the following:
  - It creates 2 scenes with name, colour and tempo.
  - It fires a scene and then stops it, with `is_triggered`/`is_playing` readback after settle.
  - It stops all clips on a track.
- **Deps**: P-01.

**T-013 Clips.** Sonnet, medium.
- **Tools**: `live_get_clips`, `live_create_clips`, `live_set_clips`.
- **Accept**: `live_clips_test.py` checks the following:
  - It creates a MIDI clip and an audio clip from a Core Library WAV (no owner files).
  - It sets loop and markers, launch mode, gain, pitch and warp mode, with readback.
  - An invalid marker order is refused with nothing applied.
- **Deps**: P-08, P-09.

**T-014 Notes.** Sonnet, high.
- **Tools**: `live_get_notes` (ids and per-note fields), `live_edit_notes`.
- **Accept**: `live_notes_test.py` checks the following:
  - It adds 8 notes, modifies 2 by id (velocity, probability), removes 1 by id, transposes the rest by +12, quantizes and duplicates a region.
  - The readback count matches Live.
  - A note added past the clip end is reported as dropped, not as written (A #138).
- **Deps**: P-07.

**T-015 Devices and parameters.** Sonnet, high.
- **Tools**: `live_get_device_parameters` (paging, nested path, return/master), `live_set_device_parameters` (`display`, `reset`, `re_enable_automation`), `live_set_devices`, `live_move_device`.
- **Accept**: `live_devices_test.py` checks the following:
  - It loads 2 stock effects on a scratch track and reorders them with `move_device`, confirmed by readback order.
  - It turns a device off and back on.
  - It writes a parameter by `display` text and resets it to default.
  - It writes a device parameter on a return track.
  - It writes a parameter of a device inside a rack chain (after T-016 into-chain load, or with a stock rack preset).
- **Deps**: P-04, P-27.

**T-016 Browser and load targets.** Opus, medium. This ticket touches `operations.py` quarantine rules.
- **Goal**:
  - Add the roots `max_for_live`, `clips` and `user_folders`, and merge roots into `live_browser_list`.
  - Extend `live_load_item` to instruments, sounds and drums on MIDI tracks, MIDI effects, M4L devices, return and master tracks, and loads into a selected rack chain.
  - Use `Track.insert_device` when it is gated in (12.3+).
  - The operation record verifies placement for each target kind.
- **Files**: `dom_browser.py`, `operations.py`, `tools/browser.py`.
- **Accept**: `live_browser_test.py` loads the following, each reaching state `ready` with correct placement:
  - Drift onto a MIDI track.
  - A Drum Rack preset from `drums`.
  - Reverb onto a return.
  - EQ Eight into chain 0 of an Audio Effect Rack.
- **Deps**: P-14, P-24.

**T-017 Delete and duplicate.** Opus, medium.
- **Tools**: `live_delete`, `live_duplicate`.
- **Accept**: `live_delete_test.py` checks the following on scratch objects:
  - Duplicate a track, a scene and a clip; the readback names match.
  - Delete each duplicate after elicitation is accepted.
  - A declined elicitation leaves the object present.
  - A missing `expect_name` is refused.
  - A stale index is refused with `name_mismatch`.
- **Deps**: P-05, T-007.

**T-018 Chain builder upgrade.** Opus, medium.
- **Goal**: `plan_chain`/`build_chain` work on MIDI tracks (instrument first) and return tracks, repair order with `move_device`, and send progress notifications for each stage.
- **Files**: `src/abletonlivemcp/{chain.py,resolve.py,tools/chain.py}`.
- **Accept**: `live_chain_test.py` (extended) builds the vocal chain on a return and an instrument+FX chain on a MIDI track, with progress events seen by the harness.
- **Deps**: T-015, T-016.

**T-019 Diagnostics in `live_hello`.** Sonnet, low.
- **Goal**: Add the variant, dialogs, CPU, the gated-API map, and the enabled toolsets.
- **Files**: `dom_session.py` (the hello part only, coordinated with T-010 by doing it inside T-010 if they run together), `tools/session.py`.
- **Accept**: shown in `live_session_test.py`.
- **Deps**: T-010.

### Wave 3: MCP quality (parallel)

**T-020 Resources.** Sonnet, medium.
- **Goal**: Register the resources in section 2.3 in `resources.py`, each backed by an existing tool.
- **Accept**: `scripts/live_resources_test.py` reads every URI over stdio in real Live.

**T-021 Prompts and SKILL.md.** Sonnet, medium.
- **Goal**: Add the prompts in `prompts.py` and `SKILL.md`.
- **Accept**: a stdio prompts/list and get smoke test. `mix_check` is run end to end in real Live and makes 0 writes, verified by an unchanged generation and unchanged mixer values.

**T-022 Descriptions and size.** Sonnet, medium.
- **Goal**: Every description gets units (dB, beats, normalized), the index base, the meaning of "applied", one example, and a `bar:beat→beats` note. Each stays at or under 150 words. Settle the snapshot.
- **Accept**: the size budget test passes.

**T-023 Fake-bridge conformance test.** Sonnet, medium.
- **Goal**: List the tools, call every READ tool, and assert that refusals are `isError` with stable text and that stdout carries only protocol traffic.
- **Accept**: passes in CI.

### Wave 4: UC1 drum rack (toolset `drums`, plus `als` for usage)

| Order | Tickets |
|---|---|
| 1 | T-030, T-031, T-032, T-034 (parallel) |
| 2 | T-033 |

**T-030 Drum pads.** Sonnet, medium.
- **Tools**: `live_get_drum_rack`, `live_set_drum_pads`.
- **Accept**: `live_drums_test.py` loads a stock kit and reads 16 pads (name and note). It sets choke group 1 on the hats, sets `out_note`, runs `copy_pad` 36→48 and clears 48 after elicitation, all with readback.
- **Deps**: P-12, T-016.

**T-031 Conversions.** Sonnet, high.
- **Tools**: `live_convert`.
- **Behaviour**: the outcome is observed like a load operation (new track or device, by identity diff).
- **Accept**: `live_convert_test.py` does the following from a Core Library drum loop clip:
  - Runs `drum_rack_from_clip` and `audio_to_midi_drums`.
  - Each conversion yields exactly one new track, whose devices and notes are read back.
  - A non-convertible clip is refused.
- **Deps**: P-13, T-013.

**T-032 Simpler.** Sonnet, medium.
- **Tools**: `live_get_simpler`, `live_set_simpler`.
- **Accept**: `live_simpler_test.py` checks the following on a Simpler made by `simpler_track_from_clip`:
  - It sets playback mode, voices and markers.
  - It adds and removes a slice.
- **Deps**: P-20, T-031.

**T-034 `.als` reader hardening and usage scan** (toolset `als`). Opus, medium. This ticket handles a file-system boundary.
- **Goal**:
  - Reconnect `src/abletonlivemcp/als/`.
  - Roots come from MCP `roots/list` or the config allowlist. Paths are confined (no symlink escape).
  - Limits: 50 MB gzip, a decompressed-size cap, entities off, and a node budget.
  - The reader is read-only and never opens the Set that is currently open.
- **Tools**: `live_scan_projects`, `live_usage_report`.
- **Accept**:
  - `scripts/live_als_test.py` scans the disposable Set saved by P-02 plus Live's bundled demo Sets, and reports the devices and samples that appear in the open Set.
  - A path outside the roots is refused.
- **Deps**: T-002.

**T-033 Drum rack builder.** Opus, high.
- **Tools**: `live_plan_drum_rack`, `live_build_drum_rack`.
- **Behaviour**:
  - Builds a GM layout (kick 36, rim 37, snare 38, clap 39, closed hat 42, pedal hat 44, open hat 46, toms 41/43/45/47/48/50, crash 49, ride 51, perc 52+).
  - The input is either explicit samples with roles or a `live_usage_report` result (roles inferred from names, which the user confirms in the plan).
  - The route is the one P-13/P-14 proved: hotswap a sample onto the selected pad, or a Conversions step per sample, followed by `move_devices_on_track_to_new_drum_rack_pad` / `copy_pad`.
  - Uses the lease and progress notifications. Readback verifies the pad name, the note, and that each sample's `file_path` matches.
- **Accept**: `live_drumbuild_test.py` builds an 8-pad rack from Core Library one-shots, and every pad lands on its GM note.
- **Deps**: T-030, T-031, T-034, T-016.

### Wave 5: UC4 macros (toolset `racks`)

| Order | Tickets |
|---|---|
| 1 | T-050 |
| 2 | T-051, and T-052 in parallel with it (T-052 also needs P-29 to pass) |

**T-050 Racks.** Sonnet, medium.
- **Tools**: `live_get_rack`, `live_set_rack`.
- **Accept**: `live_racks_test.py` checks the following on a stock Audio Effect Rack preset that has mapped macros:
  - It sets 3 macro values; the readback of the mapped parameter moves.
  - It changes the visible macro count.
  - It stores, recalls and deletes a variation.
  - It sets chain mute and volume.
- **Deps**: P-11, T-015.

**T-051 FX-rack wrap.** Opus, medium.
- **Tools**: `live_plan_fx_rack`, `live_build_fx_rack`.
- **Behaviour**:
  - Loads an empty Audio Effect Rack at the end of the track.
  - Moves the existing devices into chain 0, keeping their order.
  - Sets macro values.
  - Returns a mapping checklist with the macro name, the target parameter and the min/max range. On 12.2 the user does the mapping, and the checklist says so.
- **Accept**: `live_fxrack_test.py` wraps 3 stock effects. The device order inside the chain matches the original, and the parameter values are unchanged after the move.
- **Deps**: T-050, P-04.

**T-052 `.adg` macro preset experiment** (toolset `experimental`). Opus, high.
- **Goal**:
  - Use a template captured from a real `.adg` saved in Live (P-29).
  - Write to `User Library/AbletonLiveMCP/<name>.adg`. The file must be new; existing files are never overwritten.
  - Load the result through the browser.
- **Accept**: `live_adg_test.py` loads the generated rack. `has_macro_mappings` is true for the configured macros, the macro names read back, and moving macro 1 moves the mapped parameter across its declared range.
- **Deps**: P-29.
- **Kill rule**: if the schema differs between two 12.2 saves, stop and keep T-051 only.

### Wave 6: UC6 organize (toolsets `organize`, `library`)

| Order | Tickets |
|---|---|
| 1 | T-060, T-061, T-062 (parallel) |
| 2 | T-063 |

**T-060 Labels.** Sonnet, medium.
- **Tools**: `live_get_labels`, `live_set_labels`.
- **Accept**: `live_labels_test.py` sets labels on 3 tracks and a plugin key. The agent then saves the Set with SendKeys, restarts Live, reopens the Set, and the labels read back. The sidecar also holds the global labels.
- **Deps**: P-02.

**T-061 Usage-aware organize data.** Sonnet, medium.
- **Goal**: `live_usage_report` gains `kind: plugins` with recency.
- **Accept**: shown in `live_als_test.py`.
- **Deps**: T-034.

**T-062 Knowledge.** Sonnet, medium.
- **Tools**: `live_knowledge_search`, `live_knowledge_read`, and the `knowledge://` resources.
- **Rules**: path confinement and size caps; the knowledge files ship in the wheel. `knowledge/` has parallel writers, so the tools read it at call time and never cache an index on disk.
- **Accept**: `scripts/knowledge_stdio_smoke.py` (extended) passes.

**T-063 Organize planner.** Sonnet, medium.
- **Tools**: `live_plan_organize`, plus the `organize_session` prompt.
- **Behaviour**: the plan is applied by a single `live_set_tracks` batch.
- **Accept**: `live_organize_test.py` names and colours 8 scratch tracks in 1 write call, with one undo step.
- **Deps**: T-060, T-011.

### Wave 7: arrangement, automation, the rest

| Order | Tickets |
|---|---|
| 1 | T-070, T-072, T-073, T-074, T-075, T-076, T-077, T-078 (all parallel) |
| 2 | T-071 |

**T-070 Arrangement reads and locators.** Sonnet, medium.
- **Tools**: `live_get_arrangement`, `live_set_cue_points`.
- **Accept**: `live_arrangement_test.py` adds cues at 0, 16 and 32 (song-time write, readback, then `set_or_delete_cue`, then a check that exactly one new cue exists). It renames one, jumps to it, and deletes one. Repeating the add at the same time does not toggle the cue away.
- **Deps**: P-16, T-005.

**T-071 Arrangement clips.** Sonnet, high.
- **Tools**: `live_create_arrangement_clips`, `live_edit_arrangement_clips`, and arrangement `ClipAddr` support in `dom_notes.py`/`dom_clips.py`.
- **Accept**: `live_arrclips_test.py` checks the following:
  - It creates a MIDI and an audio arrangement clip and copies a session clip to bar 9.
  - It writes notes into the arrangement clip.
  - It trims markers, moves a clip (via duplicate + delete), creates a take lane with a clip, and deletes a clip after elicitation.
  - The test runs on a scratch Set only (12.2 crash risk, map §3.2).
- **Deps**: P-19, T-070, T-013, T-014 (it edits their modules, so it runs after them).

**T-072 Session-clip automation.** Sonnet, high.
- **Tools**: `live_get_automation`, `live_set_automation`.
- **Accept**: `live_automation_test.py` writes a linear filter sweep over 8 bars in a session clip and reads it back with `value_at_time` at 5 points (within tolerance). Clearing the envelope gives `has_envelopes` false. An arrangement clip is refused with the reason text.
- **Deps**: P-10.

**T-073 Recording.** Sonnet, medium.
- **Tools**: `live_record`.
- **Accept**: `live_record_test.py` checks the following:
  - It toggles `session_record` and `record_mode` with readback and restore.
  - `capture_midi` is refused with `nothing_to_capture` when `can_capture_midi` is false.
  - `capture_and_insert_scene` creates 1 scene.
- **Deps**: P-18.

**T-074 Audio clip editing.** Sonnet, medium.
- **Tools**: `live_edit_audio_clip`.
- **Accept**: `live_editing_test.py` adds, moves and removes a warp marker on a Core Library loop, then runs `crop` and `duplicate_loop`. The readback length is correct.
- **Deps**: P-09.

**T-075 Song extras.** Sonnet, medium.
- **Tools**: `live_get_song_advanced`, `live_set_song_advanced`.
- **Accept**: `live_song_test.py` sets the groove pool's timing amount, assigns a groove to a clip, changes the tuning reference pitch and restores it, toggles Link and restores it, and sets the count-in.
- **Deps**: P-22.

**T-076 View.** Sonnet, low.
- **Tools**: `live_view`, `live_select`, `live_preview`.
- **Accept**: `live_view_test.py` shows the Detail/Clip view (`is_view_visible` true), selects a track and a device with readback, and runs preview play and stop on a Core Library sample without error.
- **Deps**: P-23, P-24, P-14.

**T-077 Advanced devices.** Sonnet, medium.
- **Tools**: `live_get_device_extras`, `live_set_device_extras`.
- **Accept**: `live_devx_test.py` checks the following:
  - It sets the Compressor sidechain source to a scratch track.
  - It sets Eq8 to `oversample` on.
  - It lists Hybrid Reverb IR categories and selects one.
  - It changes a plugin preset index when a VST is present, and logs `info` otherwise.
- **Deps**: P-15, P-01.

**T-078 MIDI files.** Sonnet, medium.
- **Tools**: `live_import_midi`, `live_export_midi`.
- **Rules**: the stdlib SMF reader/writer handles format 0/1; files are confined to roots; export writes new files only.
- **Accept**: `live_midifile_test.py` exports a clip and re-imports it into a new slot. The notes are equal.
- **Deps**: T-014.

### Wave 8: evals and acceptance

**T-080 Simulator and eval tasks.** Sonnet, high.
- **Goal**: Build an in-memory Live simulator behind the bridge interface, plus 12 tasks from mcp-excellence §3.4. Two of them are `build_drum_rack` and `macro_fx_rack`. The calls, tokens and errors go in `docs/evals/`.
- **Deps**: Waves 2 to 6.

**T-081 Public parity table.** Sonnet, low.
- **Goal**: Put section 1 into the README and ROADMAP, using the status column.

**T-082 v2 real-Live acceptance pass.** Sonnet, medium.
- **Goal**: Run every `scripts/live_*_test.py` in sequence on a fresh disposable Set and record the results in `docs/release/v2-live-evidence.md`.
- **Deps**: all.

**T-083 (backlog) Offline WAV analysis.** Sonnet, low.
- **Goal**: Read peak, RMS and an approximate LUFS from a WAV file using stdlib `wave` only.
- **Accept**: a known test tone measures within ±0.5 dB.

---

## 4. Probe tickets

Every probe goes through T-003, runs on scratch objects, and writes `docs/release/probes/P-NN.md` with one of three verdicts:
- **go**: the call shape is proven.
- **no-go**: the reason is recorded.
- **gated**: the API is absent on 12.2.

All probes use Sonnet at medium effort.

| ID | API(s) | Question | Pass condition |
|---|---|---|---|
| P-01 | `dir()` and docstrings of `Song`, `Song.View`, `Track`, `ClipSlot`, `Clip`, `Clip.View`, `Scene`, `Device`, `RackDevice`, `DrumPad`, `Chain`, `DrumChain`, `SimplerDevice`, `Sample`, `PluginDevice`, `MaxDevice`, `MixerDevice`, `CuePoint`, `Envelope`, `TakeLane`, `GroovePool`, `Groove`, `TuningSystem`, `Browser`, `BrowserItem`, `Application`, `Application.View`, `Live.Conversions` (read-only) | Settle `hasattr` for `tap_tempo`, `nudge_*`, `exclusive_arm/solo`, `back_to_arranger`, freeze, follow actions, device duplicate, `note_number_to_name` owner, `Track.delete_clip`, `begin_undo_step`, `get_data` | JSON dump committed. Each `hasattr` question answered |
| P-02 | `Song.get_data/set_data` | Value types (str, JSON str, dict, list); size limit; survival across Save and reopen (saved with SendKeys) | A JSON string of 4 KB round-trips after the reopen |
| P-03 | `begin_undo_step/end_undo_step`, `Song.undo` | Is a 3-write batch one undo entry? Does it merge into a user step? | One `undo` reverts all 3, and only them |
| P-04 | `Song.move_device`, `find_device_position` | Reorder within a track, move across tracks, move into and out of a rack chain; the invalid-type error | The 3 moves read back correctly; the error text is captured |
| P-05 | `delete_track/return/scene`, `ClipSlot.delete_clip`, `Track.delete_device`, `Chain.delete_device`, `duplicate_track/scene`, `duplicate_clip_slot`, `duplicate_clip_to` | Return values, index effects, undo | Every call is observed by readback |
| P-06 | `mixer_device.volume/panning/sends`, master `crossfader/cue_volume`, `str_for_value` | dB↔value mapping; is −inf and +6 dB reachable; sends on returns | Bisection hits a −6.0 dB display in ≤ 1 call |
| P-07 | `get_notes_extended` fields, `apply_note_modifications`, `get_notes_by_id`, `remove_notes_by_id`, `duplicate_notes_by_id`, `remove_notes_extended`, `quantize`, `duplicate_region`, `MidiNoteSpecification` extra fields | Id stability; per-note fields writable; notes past the clip end | All calls work; the drop behaviour is documented |
| P-08 | `ClipSlot.create_audio_clip(path)`, `Track.create_audio_clip(path, start)`, `Track.create_midi_clip` | Path forms, warp default, non-audio error, length | A Core Library WAV clip is created; the error text is captured |
| P-09 | Clip setters (`loop_*`, `*_marker`, launch, `warp_mode`, `gain`, `pitch_*`, `signature`), `warp_markers`, `add/move/remove_warp_marker`, `crop`, `duplicate_loop` | Write-order constraints; warp marker object shape | Each write reads back; the constraint list is recorded |
| P-10 | `automation_envelope`, `create_automation_envelope`, `insert_step`, `events_in_range`, `value_at_time`, `delete_events_in_range`, `clear_*` | Step vs breakpoint semantics; arrangement returns None | Ramp emulation by steps is within 2% at 5 points |
| P-11 | Macro params, `visible_macro_count`, `add_macro/remove_macro`, `has_macro_mappings`, variations, `randomize_macros`, `Chain.mixer_device` | Behaviour on a stock rack | Each call reads back |
| P-12 | `drum_pads`, `DrumPad.mute/solo/delete_all_chains`, `copy_pad`, `DrumChain.out_note/choke_group` | Writes and copy semantics (does it overwrite the destination?) | Readback matches; the overwrite behaviour is recorded |
| P-13 | All 6 `Live.Conversions` functions | Signatures, sync or async result, selection needs, failure modes | Each function has a documented call shape and observed outcome |
| P-14 | `Browser.load_item` with a MIDI track, drum pad or rack chain selected; `hotswap_target`; `preview_item/stop_preview` | Sample onto the selected pad; instrument onto a MIDI track; load into a chain | Placement observed for each case |
| P-15 | `PluginDevice.get_parameter_names`, `presets`, `selected_preset_index` | Coverage beyond the configured parameters | Counts recorded for 2 plugins |
| P-16 | `set_or_delete_cue`, `CuePoint.name/time/jump`, `jump_to_next/prev_cue` | Race-free add at a time | Add, rename and delete are deterministic |
| P-17 | `available_*_routing_types/channels`, routing setters | Set by object; Resampling; return as output | Writes read back |
| P-18 | `session_record`, `record_mode`, `arrangement_overdub`, `trigger_session_record`, `capture_midi`, `can_capture_midi`, `capture_and_insert_scene` | Behaviour without input | States read back; the refusal conditions are known |
| P-19 | `arrangement_clips`, `duplicate_clip_to_arrangement`, `Track.delete_clip`, arrangement markers, `create_take_lane`, `TakeLane.create_*_clip` | Move/trim/split feasibility; 12.2 crash check | No crash in 20 operations; split verdict |
| P-20 | `SimplerDevice.*`, `Sample.*` slices | Writable fields | Readback for each field |
| P-22 | `root_note/scale_*`, `groove_pool`, `Groove.*`, `Clip.groove`, `tuning_system.*`, Link fields, `count_in_duration` | Writability (Link may need a preference to be on) | Readback or a recorded reason |
| P-23 | `Application.View.*`, `open_dialog_count`, `current_dialog_message`, `average_process_usage` | Values and view names | Recorded |
| P-24 | `Song.view.selected_track/scene/detail_clip`, `select_device`, `RackDevice.view.selected_chain/selected_drum_pad` | Writable selection for load targets | Readback |
| P-27 | `DeviceParameter.display_value` write, `value_items`, `default_value`, `re_enable_automation`, `automation_state` | Write by display; default for quantized parameters | Readback |
| P-29 | `.adg` schema: save 2 racks in Live (with and without mapped macros) and diff the XML; load a generated copy | Minimal mapping XML; does Live accept a generated file? | A generated rack loads with its mapping (else T-052 is killed) |

P-21, P-25 and P-26 are not used. Listeners are skipped because there is no push channel, `MidiMap` is not wrapped, and `note_number_to_name` is covered by P-01.

---

## 5. Risks

| Risk | Mitigation |
|---|---|
| A single Live instance serializes all proofs, at about 0.9 s per call | The orchestrator queues the runs. Batch bridge methods do read, write and readback in ≤ 2 calls. Proofs stay small |
| 12.2 crash bugs in arrangement create/duplicate (fixed in 12.4) | P-19 runs on a scratch Set with a crash counter. The bridge refuses known-bad shapes |
| `move_device` into chains, Conversions and hotswap are unverified, and UC1/UC4 depend on them | The probes come first. If one fails, the documented fallbacks apply: T-051 checklist only, or the drum rack is built through Conversions per sample |
| Macro mapping is impossible on 12.2 | The limit is stated honestly. The `.adg` experiment has a kill rule. The owner's 12.3+ upgrade decision stays open (roadmap Q1) |
| `set_data` persistence needs a Save, and Live has no save API | The proof saves with SendKeys from outside Live. The sidecar JSON is the source of truth for global labels |
| Undo grouping may fold a user's own edit into our step, or fail | The P-03 pass condition requires exactly our writes. Otherwise no grouping, and the receipts list the originals |
| Deletes are irreversible if undo fails | Every delete requires elicitation, `expect_name` and the lease. There is no delete in batch-of-unknowns form |
| Index drift between the model's read and its write | `expect_name` on every target. References are re-read inside the same call |
| Clients without elicitation cannot delete | They refuse with a clear reason. Read-only users are unaffected |
| Tool-count creep beyond 35 | The size and count budget test fails CI. Growth goes into toolsets |
| Hot-file conflicts in parallel waves | T-001 pre-creates the stubs and fixed import lists. Snapshots are per module |
| The installer copies flat `*.py` only | Domain files stay flat (`dom_*.py`, `probe_p*.py`) |
| Untrusted text: track names, browser names, `.als` content, file paths | `_untrusted` wrapping, a roots-confined file access audit in T-034, XML entity and size limits |
| Dev probes look like a code-exec backdoor | Fixed function table, a config flag, the lease, scratch objects only, never an MCP tool |
| `knowledge/` has parallel writers (Gemini) | Read it at call time. Never write to it from tools |
| The MCP spec and `mcp` package churn (elicitation form rules) | The conformance test (T-023) and a pin of `mcp>=2,<3` |
| Modal dialogs in Live block loads | `live_hello` reports dialogs, and a load timeout says "dialog open" |
