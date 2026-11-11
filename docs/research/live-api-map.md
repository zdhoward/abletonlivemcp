# Live API map: what Live 12.x exposes to a Remote Script / Python / Max for Live

Written 2026-11-10 for owner Live **12.2.0 (Windows, Suite)**. Purpose: one authoritative table of what an assistant can read, write and listen to, what our repo already wraps, and where the hard gaps are.

## 0. Evidence and how to read this file

No Live process was started or touched. Everything marked L-* was read statically from the installed files (string extraction and `marshal` read of `.pyc`; nothing executed).

| Tag | Source | What it proves |
|---|---|---|
| **L-LOM** | `C:\ProgramData\Ableton\Live 12 Suite\Resources\MIDI Remote Scripts\_MxDCore\LomTypes.pyc` (disassembled with Python 3.11, magic matches) | The exact per-class property/function list that Live 12.2.0 exposes to Max for Live. The `Live` Python module is a superset (see L-EXE). Entries with `(4,3)` are gated to a Max/EPII version, not a Live version. |
| **L-EXE** | `C:\ProgramData\Ableton\Live 12 Suite\Program\Ableton Live 12 Suite.exe`, embedded Boost.Python docstrings (byte offsets ~108.45M to 108.60M) | The real Python `Live.*` API of 12.2.0 with Ableton's own docstrings: access words "Get/Set" = read/write, "Const access"/"Returns" = read-only. Absence of a name in the whole binary = not in 12.2.0. |
| **L-RS** | `...\MIDI Remote Scripts\_Framework`, `ableton\v2`, `ableton\v3`, `_MxDCore`, `Push2` (only `.pyc`, no `.pyi` stubs exist) | How Ableton's own scripts use the API (e.g. `schedule_message`, `ControlSurface`). |
| **C74** | https://docs.cycling74.com/apiref/lom/ (pages per class; covers Live 12.4.5) | Official LOM access columns (get/set/observe) and "since" markers. Only `clip` and `song` pages were fetched in full here; other pages are covered by L-LOM/L-EXE. |
| **REL** | https://www.ableton.com/en/release-notes/live-12/ (first 200k of 310k characters read; 12.0 through 12.0.4 and late 12.4.x were not fully read) | Version gates. |
| **R-DR** | `docs/research-deep-review.md` (already in repo, not redone) | Prior secondary-source findings (open-source bridges, file formats). |

"Listen" column: the Python bindings generate `add_<prop>_listener` / `remove_<prop>_listener` / `<prop>_has_listener` for observable properties (L-EXE docstring templates). C74 marks which are observable for Max; for classes not fetched, treat listenability as **unverified per property**.

Status column: **W** = wrapped in `remote_script/AbletonLiveMCP/handlers.py` at `a79d95c`; **-** = not wrapped; **partial** = some of the capability.

Windows/Live 12.2.0 facts that matter: Live embeds Python 3.11.6 since 12.1 (REL 12.1); our own run found `ctypes` is missing in that interpreter (`docs/release/m1b-live-evidence.md`).

## 1. Threading and runtime constraints

| Constraint | Detail | Source |
|---|---|---|
| Single Live thread | All `Live.*` object access must happen on Live's main/control-surface thread. Our bridge already marshals via display ticks. Never touch Live objects from a socket thread. | R-DR section 1; L-RS (`ControlSurface` has `schedule_message`, `_do_send_midi`, task group) |
| Scheduling primitives | `ControlSurface.schedule_message(delay_ticks, callable)` and a `Task`/`TaskGroup` framework are what Ableton's own scripts use. `Live.Timer` (interval/restart, errors in callback stop the timer) also exists in the binary. | L-RS `_Framework/ControlSurface.pyc`; L-EXE ("A timer that will trigger a callback after a certain interval") |
| Listeners are callbacks on the main thread | Install with `add_*_listener`; they fire inside Live's event handling. Keep them tiny; enqueue and return. | L-EXE |
| Objects die | LOM objects become invalid after deletes/Set change; Ableton uses `liveobj_valid`. Dead-object access raises. Our `Safety` reference/generation scheme already handles this. | L-RS (`liveobj_valid` imported by `_MxDCore`); repo `safety.py` |
| Set change reloads scripts | Confirmed in real Live (new untitled set reloads the script). | m1b-live-evidence.md |
| Undo | `Song.begin_undo_step()` / `end_undo_step()` exist in the Python module (docstring-less in the binary) so a multi-write tool call can be one undo entry. Not in the M4L LOM list. | L-EXE (names present at offsets ~108.47M); **unverified behaviour** |
| Limits | create_* raises a "limitation error" when track/scene limits are exceeded (e.g. Intro/Standard editions). Our owner has Suite. | L-EXE docstrings |
| Python import paths | Live can add paths to the Python search path (string "Added ... to the Python import search paths"). Mechanism not established. | L-EXE; **unverified** |
| Max for Live LOM | Runs on a separate path (`_MxDCore`), serialized through Live; a bad API call can lag Live (12.3.2 fixed an M4L API freeze). | L-RS; REL 12.3.2 |

## 2. Version gates (what 12.2.0 does and does not have)

| Item | Gate | Present on owner's 12.2.0? | Source |
|---|---|---|---|
| `Clip.add_new_notes`, `get_notes_extended`, `apply_note_modifications`, `remove_notes_extended`, note ids, per-note probability/velocity_deviation/release_velocity | Live 11.0 | Yes | C74 clip; L-EXE |
| `Clip.groove`, `launch_mode`, `launch_quantization`, `legato`, `velocity_amount`, `GroovePool` | Live 11.0 | Yes | C74 |
| `Clip.get_all_notes_extended` | 11.1 | Yes | C74 |
| `Song.tuning_system` and TuningSystem class; `LooperDevice.export_to_clip_slot`; Python 3.11.6 | 12.1 | Yes | REL 12.1 |
| `Track.create_midi_clip` (arrangement) | 12.1.10 | Yes | REL |
| `Track.create_audio_clip`, `Track.create_take_lane`, `TakeLane.name`/`create_*_clip`, `Clip.start_time` observable, `DeviceParameter.display_value` | 12.2 | Yes | REL 12.2; L-LOM; L-EXE |
| **`Track.insert_device`, `Chain.insert_device`, `RackDevice.insert_chain`, `DrumChain.in_note`** | **12.3** | **No** (0 occurrences in the 12.2.0 binary; not in L-LOM) | REL 12.3; L-EXE scan |
| Device A/B compare in Max API | 12.3 | No | REL 12.3 |
| `SimplerDevice.replace_sample` | 12.4 | No | REL 12.4 |
| Plug-in editor window open/close via LOM | 12.4.3 | No | REL 12.4.3 |
| `Clip.root_note/scale_name/scale_mode/scale_intervals` (Song-level equivalents exist already) | 12.4.15 | Song-level yes, Clip-level no | REL 12.4.15; L-LOM |
| `CcControlDevice` LOM properties accessible | 12.4.15 | Class present, properties newer | REL; L-EXE |
| Python `Live.Conversions` (audio-to-MIDI, drum rack builders) | present in 12.2.0 binary | Yes | L-EXE |

Rule: our `probe()` must keep gating every 12.3+ name by `hasattr` (it does for `insert_device`).

## 3. Capability tables

Columns: capability | API | version | access | repo status | notes. Access letters: R read, W write, L listenable (Python listener), F function call.

### 3.1 Application, Song (transport, structure)

| Capability | API | Ver | Access | Repo | Notes |
|---|---|---|---|---|---|
| Live version | `Application.get_major/minor/bugfix_version`, `get_version_string`, `get_build_id`, `get_variant` (Suite/Standard/...) | all | R | partial (version only) | Variant useful for limit awareness (L-EXE). |
| Tempo | `Song.tempo` | all | R W L | W (`set_tempo`) | Bridge clamps 20..999. |
| Transport | `is_playing`, `start_playing`, `stop_playing`, `continue_playing`, `current_song_time` (RWL), `jump_by`, `scrub_by`, `play_selection`, `stop_all_clips` | all | R W F | partial (play/stop/read) | Missing: continue, jump, stop_all_clips, song_time write. |
| Loop/punch/metronome | `loop`, `loop_start`, `loop_length`, `punch_in/out`, `metronome`, `count_in_duration` (R), `is_counting_in` | all | R W L | - | C74 song. |
| Recording | `record_mode`, `session_record`, `arrangement_overdub`, `session_record_status`, `trigger_session_record(record_length)`, `capture_midi(destination)`, `can_capture_midi`, `capture_and_insert_scene` | capture_midi 11+ | R W F | - | Capture MIDI is high value: "grab what I just played". |
| Time signature | `signature_numerator/denominator` | all | R W L | R only | |
| Scale / key | `root_note`, `scale_name`, `scale_mode`, `scale_intervals` (R) | present 12.2.0 | R W (intervals R) | - | Valid scale names listed in L-EXE docstring (35 names). |
| Tuning | `Song.tuning_system` (`name`, `reference_pitch`, `note_tunings`, `lowest_note`, `highest_note`, `pseudo_octave_in_cents`) | 12.1 | R W L | - | Niche. |
| Cue points | `Song.cue_points`, `CuePoint.name/time` (RWL), `jump`, `set_or_delete_cue`, `jump_to_next/prev_cue`, `can_jump_*` | all | R W F | - | Locators: write via set_or_delete_cue at current time + `CuePoint.name`. Arrangement markers editable only that way. |
| Groove | `groove_amount`, `swing_amount`, `groove_pool.grooves` -> `Groove.base/quantization_amount/timing_amount/random_amount/velocity_amount` | 11.0 | R W L | - | Groove files cannot be created via API; only existing pool grooves edited. |
| Undo/redo | `undo`, `redo`, `can_undo`, `can_redo`, `begin_undo_step/end_undo_step` | all | F | - | Undo step grouping unverified. |
| Link | `is_ableton_link_enabled`, `..._start_stop_sync_enabled`, `force_link_beat_time` | 11+ | R W | - | Toggle must be visible in prefs (L-EXE error text). |
| Persisted per-Set data | `get_data(key, default)` / `set_data(key, value)` on `Live.Song` | present 12.2.0 | R W | - | "Persistent and restored when loading the Live Set" (L-EXE). Best place to store our own labels/usage metadata inside the .als without writing the file. Python-only; not in M4L LOM. Exact value types **unverified**. |
| Tracks / returns / master | `tracks`, `visible_tracks`, `return_tracks`, `master_track`, `scenes` | all | R L | W (`tracks`, `scenes` list) | Python tuples are read-only containers. |
| Create/delete/duplicate | `create_audio_track(idx)`, `create_midi_track(idx)`, `create_return_track`, `create_scene(idx)`, `delete_track`, `delete_return_track`, `delete_scene`, `duplicate_track`, `duplicate_scene` | all | F | partial (create track/scene) | Delete/duplicate not wrapped; both destructive, need lease/guards. Create returns the new object in Python. |
| Device move | `Song.move_device(device, target, pos)`, `find_device_position(device, target, pos)` | 11+ | F | - | Reorder devices in a chain or move between tracks/chains. Valid device-type checks done by Live. |
| Appointed device / selection | `appointed_device` (RWL), `view.selected_track/selected_scene/selected_parameter/detail_clip/highlighted_clip_slot/draw_mode/follow_song` | all | R W L | partial (`select_device`, `selected_track`) | Selection is also the insertion point for browser loads. |

### 3.2 Track, ClipSlot, Clip, Scene

| Capability | API | Ver | Access | Repo | Notes |
|---|---|---|---|---|---|
| Name, color | `Track.name` (RWL), `color`, `color_index` | all | R W L | W (name, color_index) | `color` (RGB) maps to nearest palette entry. `is_auto_colored` exists on Chain. |
| Mute/solo/arm | `mute`, `solo`, `arm`, `can_be_armed`, `implicit_arm`, `muted_via_solo` | all | R W L | - | Solo does not clear others (docstring). |
| Monitoring | `current_monitoring_state` (AUTO/IN/OFF) | all | R W L | - | |
| Routing | `available_input/output_routing_types/channels`, `input/output_routing_type/channel` (current_* are deprecated aliases) | 11+ | R W L | - | Objects with `display_name`; sidechain and resampling go through these. Compressor has its own sidechain routing (L-LOM). |
| Mixer | `mixer_device.volume/panning/sends/track_activator/crossfade_assign/panning_mode/left_split_stereo/right_split_stereo`, master `crossfader/cue_volume/song_tempo` | all | R W L (DeviceParameter) | partial (via generic parameter write only if reached through `devices`; mixer not exposed) | `devices` includes no mixer in Python docs; mixer is separate. Volume/pan/sends are the most common assistant action. |
| Meters | `input_meter_left/right/level`, `output_meter_*` | all | R L | - | Audio meters not for MIDI tracks. Useful for gain staging feedback. |
| Groups / fold | `is_foldable`, `is_grouped`, `group_track`, `fold_state` (RW), `is_part_of_selection`, `is_visible` | all | R (fold W) | - | **Cannot create a group** (see gaps). |
| Freeze | `can_be_frozen`, `is_frozen` (R) | all | R | - | No freeze/flatten call (gaps). |
| Clip slots | `Track.clip_slots`, `playing_slot_index`, `fired_slot_index`, `stop_all_clips`, `delete_clip`, `duplicate_clip_slot`, `duplicate_clip_to_arrangement`, `jump_in_running_session_clip`, `back_to_arranger` | all (duplicate_clip_to_arrangement 11+) | R W F | partial | |
| ClipSlot | `has_clip`, `clip`, `create_clip(len)` (MIDI), `create_audio_clip(path)` (12.2), `fire(record_length, launch_quantization, force_legato)`, `stop`, `delete_clip`, `duplicate_clip_to`, `has_stop_button` (RW), `playing_status`, `is_triggered`, `will_record_on_start`, `color/color_index` (R) | mostly all | R W F | partial (create_clip MIDI, fire/stop via clip) | `create_audio_clip` from a file path = import a sample into a Session slot (needs absolute path; error if not audio). High value. |
| Arrangement clips | `Track.create_midi_clip(start, length)` (12.1.10), `create_audio_clip(path, start)` (12.2), `arrangement_clips` (R), `duplicate_clip_to_arrangement(clip, time)`, `take_lanes`, `create_take_lane`, `TakeLane.name/arrangement_clips/create_*_clip` | 12.1.10-12.2 | R W F | - | Arrangement is writable for clips (not automation). Time range [0, 1576800] beats (L-EXE). Crashes fixed in 12.4 for duplicate/create (REL): consider avoiding on 12.2. |
| Clip core | `name`, `color`, `color_index` (RWL), `length` (R), `start_marker`, `end_marker`, `loop_start`, `loop_end`, `looping` (RWL), `muted`, `signature_*`, `position/start_time/end_time`, `is_playing`, `is_triggered`, `is_recording`, `is_overdubbing`, `playing_position`, `fire`, `stop`, `move_playing_pos`, `scrub`, `stop_scrub`, `crop`, `duplicate_loop` | all | R W L | partial (name, length, is_playing, looping read; fire/stop) | C74 clip table. Marker/loop writes not wrapped. Units: beats for MIDI/warped audio, seconds for unwarped (L-EXE). |
| Launch settings | `launch_mode`, `launch_quantization`, `legato`, `velocity_amount` | 11.0 | R W L | - | **No follow actions**: `follow_action` strings exist only in Live's internal model (L-EXE), not in `Live.Clip` or L-LOM. |
| MIDI notes read | `get_notes_extended(from_pitch, pitch_span, from_time, time_span)`, `get_all_notes_extended`, `get_selected_notes_extended`, `get_notes_by_id`, `MidiNote` (pitch, start_time, duration, velocity, mute, note_id, probability, velocity_deviation, release_velocity) | 11.0 | R | W (get_notes) | Our output omits probability, velocity_deviation, release_velocity, note_id. |
| MIDI notes write | `add_new_notes(MidiNoteSpecification...)`, `apply_note_modifications` (by id, preserves per-note events), `remove_notes_extended`, `remove_notes_by_id`, `duplicate_notes_by_id`, `duplicate_region`, `quantize`, `quantize_pitch`, select helpers | 11.0 (dup ids 11.1.2) | W F | partial (add only) | **Replace/modify/delete notes is the main missing edit path.** Docs warn: do not emulate modify by remove+add (loses per-note events). Legacy `set_notes/get_notes/remove_notes` are deprecated (L-EXE). |
| Note names | `Clip.View`? no: `note_number_to_name` (clip, scale/tuning-aware) | 12.x | R | - | Name of function appears next to Clip.View docs in L-EXE; owner class **unverified**. |
| Audio clip props | `gain` (RW), `gain_display_string`, `pitch_coarse` (-48..48), `pitch_fine` (-500..500), `warping`, `warp_mode`, `available_warp_modes`, `ram_mode`, `sample_rate`, `sample_length`, `file_path`, `warp_markers` (R), `add_warp_marker`, `move_warp_marker`, `remove_warp_marker`, `beat_to_sample_time`, `sample_to_beat_time`, `seconds_to_sample_time` | 11+ | R W F | - | C74 notes `warp_markers` get since 11.0. WarpMode: beats, tones, texture, repitch, complex, complex_pro (L-EXE). Warp markers returned as list; JSON form via MxD conversion only in M4L. |
| Audio-to-MIDI | `Live.Conversions.audio_to_midi_clip(song, audio_clip, audio_to_midi_type)`; types `harmony_to_midi`, `melody_to_midi`, `drums_to_midi`; `is_convertible_to_midi(audio_clip)` | present 12.2.0 | F | - | **Not in M4L LOM; Python only.** Creates a new MIDI track with the notes. High value. |
| Clip view | `Clip.View.grid_quantization`, `grid_is_triplet`, `show_loop`, `show_envelope`, `hide_envelope`, `select_envelope_parameter` | 11+ | R W F | - | Cosmetic but helps "show me". |
| Automation (clip) | `Clip.automation_envelope(param)`, `create_automation_envelope(param)`, `automation_envelopes`, `clear_envelope`, `clear_all_envelopes`, `has_envelopes`; `Envelope.value_at_time`, `insert_step(time, length, value)`, `events_in_range`, `delete_events_in_range` | present 12.2.0 | R W F | - | L-EXE docstring: `automation_envelope` returns None for Arrangement clips and for params from another track. So **clip (session) automation is writable; arrangement/track automation is not**. `EnvelopeEvent` read via `events_in_range`. `insert_step` is the only documented writer (step, not breakpoint curve); exact breakpoint semantics **unverified**. |
| Scene | `Scene.name` (RW), `color/color_index` (RW), `fire`, `fire_as_selected`, `is_empty`, `is_triggered`, `clip_slots`, `tempo`/`tempo_enabled`, `time_signature_*` | tempo/time sig per scene 11+ | R W F | partial (create, name, fire) | Scene tempo/time-signature is useful for "build a song structure". |

### 3.3 Devices, parameters, racks, drums, samplers

| Capability | API | Ver | Access | Repo | Notes |
|---|---|---|---|---|---|
| Device identity | `Device.name` (RW), `class_name`, `class_display_name`, `type` (audio_effect/instrument/midi_effect), `is_active`, `can_have_chains`, `can_have_drum_pads`, `latency_in_ms/samples`, `canonical_parent`, `view.is_collapsed` (RWL) | all | R, name W | partial (name, class_name read) | |
| Parameters | `Device.parameters` -> `DeviceParameter.name`, `original_name`, `value` (RWL), `min`, `max`, `default_value`, `display_value` (RW, 12.2 for M4L), `is_quantized`, `value_items`, `short_value_items`, `str_for_value`, `state` (enabled/irrelevant/disabled), `is_enabled`, `automation_state` (none/active/overridden), `re_enable_automation`, `begin_gesture/end_gesture` | all | R W L F | W (read, write, batch, sample) | **`is_enabled` false = macro-mapped or disabled by Max** (L-EXE). `value_items` lets us write quantized params by name. `default_value` (non-quantized only) enables "reset parameter" - not wrapped. `parameters[0]` is always "Device On". |
| Banks | `MaxDevice.get_bank_count/name/parameters` ("best-of" bank = -1), `Device.store_chosen_bank` | all | R | - | The "best of" bank is Ableton's own curated parameter list for hardware: useful priority list for large devices. Max devices only. |
| Plug-in parameters | `PluginDevice.parameters` (only the configured ones), `presets`, `selected_preset_index` (RW), `get_parameter_names(begin,end)` | all | R W | - | `get_parameter_names` is on `Live.PluginDevice` in L-EXE: may list names beyond the configured set - **unverified**; probe in real Live. Existing `docs/data/plugin-params-probe.json` is the repo's earlier evidence. No API to "Configure". |
| Move/insert device | Browser `load_item` (12.2), `Song.move_device`; `Track.insert_device(name, idx)` and `Chain.insert_device` only 12.3+ | see gates | F | W (browser load audio_effects/plugins onto audio tracks only) | On 12.2 loading onto MIDI tracks, into chains, and at arbitrary indices is not verified. `Track.delete_device(i)` / `Chain.delete_device(i)` exist (R-DR). |
| Delete device | `Track.delete_device(index)`, `Chain.delete_device(index)` | all | F | - | Destructive. |
| Rack | `RackDevice.chains`, `return_chains`, `visible_macro_count` (RL), `add_macro`, `remove_macro` (change visibility), `has_macro_mappings` (list of bool per macro), `randomize_macros`, `store_variation`, `recall_selected_variation`, `recall_last_used_variation`, `delete_selected_variation`, `variation_count`, `selected_variation_index` (RW), `chain_selector`, `is_showing_chains`, `can_show_chains`, `view.selected_chain/is_showing_chain_devices/selected_drum_pad/drum_pads_scroll_position` | macros up to 16 since 11; variations in LOM list | R W F | - | Macro **values** are ordinary DeviceParameters (named "Macro 1"...; names read-only via LOM). Variations (store/recall) are fully scriptable: great for "snapshot this sound". |
| Chain | `Chain.name`, `color`, `color_index`, `is_auto_colored` (RW), `mute`, `solo` (RW), `devices`, `mixer_device` (`volume`, `panning`, `sends`, `chain_activator`), `delete_device`, `has_audio/midi_input/output` | 11+ | R W | - | Chain `delete`/`create` is not in the 12.2 API. |
| Drum rack | `RackDevice.drum_pads` (128), `visible_drum_pads`, `DrumPad.name` (R), `note` (R), `mute`, `solo` (RW), `chains`, `delete_all_chains`, `RackDevice.copy_pad(src, dst)`; `DrumChain.out_note`, `choke_group` (RW) | 11+ | R W F | - | **`DrumChain.in_note` is 12.3**; on 12.2 only `out_note` and `choke_group`. Pad receiving note cannot be remapped on 12.2 via API. |
| Drum rack builders | `Live.Conversions.create_drum_rack_from_audio_clip(song, audio_clip)`, `sliced_simpler_to_drum_rack(song, simpler)`, `move_devices_on_track_to_new_drum_rack_pad(song, track_index)` (onto C1/36), `create_midi_track_with_simpler(song, audio_clip)`, `create_midi_track_from_drum_pad(song, drum_pad)` | present 12.2.0 | F | - | **Python-only; best route for UC1** (drum rack from real samples) without file writes. Needs a clip in the Set (e.g. via `ClipSlot.create_audio_clip(path)`). Exact signatures from docstrings; call shape **unverified**. |
| Simpler | `SimplerDevice.sample`, `playback_mode`, `retrigger`, `voices`, `reverse`, `multi_sample_mode`, `pad_slicing`, `slicing_playback_mode`, `crop`, `warp_as/half/double`, `can_warp_*`, `guess_playback_length`, `playing_position`, `view.selected_slice`; Python extras `sample_start/end/loop_*`, `note_pitch_bend_range`, `get_available_voice_numbers` | 11+ | R W F | - | |
| Sample (in Simpler) | `Sample.file_path`, `length`, `sample_rate`, `gain`, `warping`, `warp_mode`, `warp_markers`, `slices`, `insert_slice`, `move_slice`, `remove_slice`, `clear_slices`, `reset_slices`, `slicing_style/beat_division/region_count/sensitivity`, `start_marker`, `end_marker`, per-warp-mode params | 11+ | R W F | - | **No `load_sample` in 12.2.0.** `replace_sample` arrives in 12.4. |
| Native device specifics | Wavetable (wavetable index/category lists, modulation matrix get/set), Drift (mod matrix lists), Meld, Roar (routing mode, env_listen), Eq8 (`edit_mode`, `global_mode`, `oversample`, `view.selected_band`), Compressor (sidechain routing), HybridReverb (IR category/file lists), Looper (record/overdub/play/stop/clear/undo/export_to_clip_slot, `tempo`, `loop_length`), Shifter, SpectralResonator, DrumCell (`gain`), CcControl | 11-12.2 | R W F | - | Lists give enum names that parameters do not (e.g. Wavetable category names, IR files). Mostly niche for an assistant; HybridReverb IR and Wavetable are worth it. Source L-LOM. |
| Hot-swap, A/B compare | `Browser.hotswap_target`, `relation_to_hotswap_target` (L-EXE); A/B compare via Max 12.3 | - | R | - | |

### 3.4 Browser

| Capability | API | Ver | Access | Repo | Notes |
|---|---|---|---|---|---|
| Roots | `Browser.instruments, sounds, drums, audio_effects, midi_effects, max_for_live, plugins, clips, samples, packs, user_library, current_project, user_folders, legacy_libraries` (empty), `colors` (items "containing the configured colors"), `hotswap_target`, `filter_type` | 12.2.0 binary | R | partial (10 roots; `max_for_live`, `clips`, `user_folders`, `colors` not in `BROWSER_ROOTS`) | L-EXE. Add `max_for_live`, `clips`, `user_folders`. |
| Items | `BrowserItem.name`, `uri`, `source`, `is_folder`, `is_device`, `is_loadable`, `is_selected`, `children`, `iter_children` | all | R | W | `uri` is the stable id. |
| Load / preview | `Browser.load_item(item)`, `preview_item(item)`, `stop_preview()` | all | F | partial (load only) | Preview audition is a nice assistant feature ("play me this sample"), not wrapped. Load target = selected track/hotswap; see our `append_unverified` machinery. |
| Search | none in API | - | - | W (our own bounded walk) | We walk `children`; 4000-node budget. |
| Tags / favorites / collections write | **none** | - | - | - | `colors` is read-only listing. See gaps. |

### 3.5 Application view, dialogs, control surface

| Capability | API | Ver | Access | Repo | Notes |
|---|---|---|---|---|---|
| View control | `Application.View.show_view/hide_view/focus_view/is_view_visible/scroll_view/zoom_view/toggle_browse/available_main_views/focused_document_view/browse_mode` | all | R F L | - | Lets the assistant show Detail/Device/Browser panes. |
| Dialogs | `open_dialog_count`, `current_dialog_message`, `current_dialog_button_count`, `press_current_dialog_button`, `show_message` | all | R F | - | Useful for detecting a stuck modal that blocks loads (e.g. missing plugin license). |
| CPU | `average_process_usage`, `peak_process_usage` | all | R | - | |
| Status message | `ControlSurface.show_message`, `log_message` | all | F | - | Display assistant activity in Live's status bar; log to `Log.txt`. |
| MIDI mapping | `Live.MidiMap.map_midi_cc/note/pitchbend(...)`, `forward_midi_*`, feedback rules | all | F | - | Maps incoming MIDI to a DeviceParameter inside a ControlSurface context (`request_rebuild_midi_map`). A parameter-mapping primitive; **not** a Rack macro mapping. |
| Raw MIDI out | `ControlSurface.send_midi`, `received_midi` | all | F | - | |

## 4. Hard gaps, workarounds and risks

| Gap | Evidence | Best workaround | Risk |
|---|---|---|---|
| **No macro mapping / macro rename** in `Live.RackDevice` | 0 hits for `macro_map`/`rename_macro` as Python names in 12.2.0; the strings exist only as internal `push_live_model` messages (`Message_macro_map`, `Message_rename_macro`) used by Push (L-EXE). `DeviceParameter.name` is get-only (C74; R-DR). | (a) Offline: write an `.adg` Audio Effect Rack with mappings to a User Library folder and load via browser (R-DR sections 2, 8). (b) Max for Live helper using `live.remote~`/`live.map`-style mapping inside an M4L device (maps a parameter to a macro-like control, but is not a Rack macro). (c) Guide the user to map manually, with the bridge setting macro values. | (a) High: reverse-engineered XML, per-version fixtures, no hot reload. (b) Medium: M4L dependency, needs the device installed, ties assistant to Max. (c) Low. |
| **No grouping of existing devices into a rack** | `group_devices` exists only as internal `Message_group_devices@Track/@Chain` (L-EXE); no Python method. Ziforge reports unsupported (R-DR). | Build the chain inside a rack from the start: load an empty Audio Effect Rack preset, then use browser loads with the rack's chain selected (12.2), or `Chain.insert_device` on 12.3+. Or `.adg` offline. | Medium; 12.2 nested insertion is unproven (m1b: only top-level appends verified). |
| **No rack chain creation / deletion on 12.2** | `insert_chain` is 12.3 (REL); only `delete_all_chains` on DrumPad exists. | Upgrade to 12.3+ (owner decision), or use presets. | Low, once on 12.3. |
| **No device insert at index on 12.2** | `Track.insert_device` is 12.3 (REL; 0 hits in binary). | Today: select device then `load_item` and verify (already built, M1b). Then `Song.move_device` to reorder (L-EXE; **unverified in real Live**). | Medium: browser load depends on UI selection state. |
| **No VST/AU parameter exposure beyond "Configure"d ones** | `PluginDevice.parameters` = configured set (R-DR, manual); `get_parameter_names(begin,end)` exists (L-EXE). | Probe `get_parameter_names` for the full list; if it lists unconfigured params, they still cannot be written. Otherwise ask the owner to Configure (or save a configured default preset). `docs/data/plugin-params-probe.json` records current probes. | Medium; adds owner steps. Opaque plugin state is never readable. |
| **No color tag / favorites / Collections write**, no Live 12 browser tags | `Browser.colors` read-only; no setter (L-EXE); R-DR section 4. | Store our own labels via `Song.set_data` (in-Set) and a local sidecar JSON; surface "tag suggestions" only. File edit of `Ableton Folder Info` XMP is unverified and unsafe live. | Our own metadata is safe; native tags High risk (corruption, no reload). |
| **No follow actions** | `follow_action` only in internal strings (L-EXE); absent from L-LOM and C74 clip table. | None via API. Offline `.als`/`.alc` edit or manual. | High for any file approach. |
| **No arrangement/track automation writing** | `Clip.automation_envelope` returns None for Arrangement clips (L-EXE). | Write automation inside **session** clips (`create_automation_envelope` + `insert_step`), then user drags to arrangement. Or sample + `parameter.value` writes during playback (poor). | Low-medium; breakpoint semantics unverified. |
| **No .als / .adg / .alc write via API** | No save/export API: no `save_set`, `export_audio`, `new_set`, `open_set` names in the binary (scan). `Application` has no save call. | Offline gzip-XML tooling on **copies** (R-DR sections 2, 8). Never edit an open Set's file. | High: undocumented schema, version drift. |
| **No sample load into Simpler/Drum Rack pad on 12.2** | No `load_sample`/`replace_sample`/`import_sample` in binary; `replace_sample` is 12.4 (REL). | `ClipSlot.create_audio_clip(path)` then `Conversions.create_drum_rack_from_audio_clip` / `create_midi_track_with_simpler` (L-EXE). Or browser `load_item` of a sample item when a pad is the hotswap target (`drum_pad_hotswap`, `instrument_hotswap` present in L-EXE; **unverified**). | Medium; Conversions call shapes need real-Live probes. |
| **No pad receiving-note remap (12.2)** | `DrumChain.in_note` is 12.3 (REL). | `RackDevice.copy_pad(src, dst)` moves content between pad indices (note indices) (L-EXE). | Low; but overwrites the destination. |
| **No freeze/flatten/consolidate/export** | `is_frozen`/`can_be_frozen` read-only (L-EXE); no render calls (the render dialog is UI-only). | None. Offline bounce by the user. | n/a |
| **No project save/load, no plugin window control (12.2)** | No such Python names; plug-in window open/close LOM is 12.4.3 (REL). | n/a | n/a |
| **Stable track/device ids** | Objects are handles; indices shift. `Track.canonical_parent` exists. | Our reference/generation layer (already built). | Low |
| **Max-only parameters and visibility** | `DeviceParameter.is_enabled` false when macro-mapped/disabled by Max (L-EXE). | Check `is_enabled` before write (already done in `_checked_write`). | Low |

## 5. What other layers add

| Layer | What it adds beyond our Python Remote Script | Cost / risk | Source |
|---|---|---|---|
| **Max for Live device (LOM via `live.object`/`live.path`)** | Same LOM, plus observers, `live.remote~` / `live.modulate~` (parameter mapping and modulation by a device), audio-rate access, MIDI Tools, note-level UI, file dialogs and file I/O from Max/JS (so a device could save a preset or read `.als` metadata), `this_device`. M4L-only bits: `ControlSurface` proxy objects, `getinfo`, JSON-formatted properties via `_MxDCore.Conversions`. Does **not** add macro-rename or grouping (L-LOM has no such member). | Requires Suite/M4L, the user must place a device in the Set; extra process boundary; LOM freeze risks reported (REL 12.3.2). | L-LOM; C74; REL |
| **Python-only extras (already in our script)** | `Application.browser`, `Live.Conversions`, `Song.begin_undo_step`, `get_data/set_data`, `Envelope` API, `DeviceParameter.begin_gesture/end_gesture`, `Clip.automation_envelope`, `PluginDevice.get_parameter_names`, `Live.MidiMap`, `Timer`. Not in the Max LOM. | None beyond the main-thread rule. | L-EXE |
| **OSC (AbletonOSC)** | Another Remote Script exposing song/track/clip/device get/set and listeners over UDP; no feature beyond the Python module; useful as reference for listener patterns. | Different security model, no auth; duplicates our bridge. | R-DR section 7 (https://github.com/ideoforms/AbletonOSC) |
| **MIDI remote layer (Control Surface framework)** | `_Framework`/`ableton.v2/v3` components (session, mixer, device, drum rack) and `Live.MidiMap` mapping of external MIDI to parameters. Gives Ableton-standard banks (`MaxDevice.get_bank_parameters`, best-of bank) and `DrumGroupComponent` behaviours. | Heavy; scripts are `.pyc`-only in the install, so use the public Live module instead. | L-RS |
| **Offline file layer** | `.als/.adg/.adv/.alc` read (usage analysis) and cautious write. | See R-DR; high risk. | R-DR |

## 6. Top 15 highest-value unwrapped capabilities

Ranked by value to the vision's use cases (UC1 to UC6) and to "assist, not automate" use, with feasibility on owner's 12.2.0. Each is available **today** unless noted.

1. **Note edit/delete/modify** (`apply_note_modifications`, `remove_notes_extended`, `remove_notes_by_id`, `duplicate_*`, read probability/velocity_deviation/release_velocity). Core of "fix this pattern"; we can only add notes.
2. **Mixer control**: `mixer_device` volume, pan, sends, activator, crossfade assign, return tracks; plus `mute/solo/arm/monitoring`. Most common assistant action; entirely missing.
3. **Return tracks and sends** (`create_return_track`, read `return_tracks`, send parameters): needed for "build a vocal chain with reverb/delay returns".
4. **`ClipSlot.create_audio_clip(path)` (12.2) and arrangement `create_audio_clip/create_midi_clip`**: sample import into Session/Arrangement.
5. **`Live.Conversions` drum-rack builders** (`create_drum_rack_from_audio_clip`, `sliced_simpler_to_drum_rack`, `create_midi_track_with_simpler`, `create_midi_track_from_drum_pad`, `move_devices_on_track_to_new_drum_rack_pad`): the realistic UC1 route with no file writes. Needs real-Live probes of call shapes.
6. **Drum rack inspection and copy**: `drum_pads` (name, note, mute, solo), `DrumChain.out_note`, `choke_group`, `copy_pad`: needed to verify/normalize a layout (UC1).
7. **Rack macros and variations**: read macro DeviceParameters, `visible_macro_count`, `has_macro_mappings`, `add/remove_macro`, `store_variation`/`recall_*`, `randomize_macros` (UC4 partial: can set macro values and snapshot, cannot map).
8. **`Song.move_device` / `find_device_position` / `delete_device`**: reorder and remove devices; completes chain building on 12.2.
9. **Capture MIDI and recording controls** (`capture_midi`, `can_capture_midi`, `record_mode`, `session_record`, `trigger_session_record`, `arm`).
10. **Per-Set metadata store** `Song.get_data/set_data`: label/category/usage notes saved inside the Set (UC6 without file writes). Verify value types first.
11. **Clip properties**: markers, loop, launch mode/quantization/legato, warp mode, pitch, gain, `warping`, warp markers, color (audio/MIDI). Also scene tempo/time signature.
12. **Cue points / locators** (`set_or_delete_cue`, `CuePoint.name/time/jump`, `jump_to_*`): song structure labeling.
13. **Clip (session) automation envelopes** (`create_automation_envelope`, `insert_step`, `events_in_range`): "fade this filter over 8 bars".
14. **Browser extras**: add `max_for_live`, `clips`, `user_folders` roots; `preview_item`/`stop_preview`; load onto MIDI tracks (instruments, drums, sounds) and into rack chains (needs real-Live verification of hot-swap targets).
15. **Parameter niceties and plug-ins**: `value_items` writes by name, `default_value` reset, `short_value_items`, `display_value` write (12.2), `PluginDevice.get_parameter_names`, plugin `presets`/`selected_preset_index`; plus `Application` dialog and CPU reads for diagnosing stuck loads.

## 7. Unverified items to test in real Live (read-only first)

- Call signatures and failure modes of `Live.Conversions.*` and whether they need a selected/valid clip.
- Whether `Song.get_data/set_data` accept dicts/JSON strings and survive Save/Reopen.
- `Song.begin_undo_step/end_undo_step` behaviour from a Remote Script.
- `PluginDevice.get_parameter_names()` coverage versus configured parameters.
- `Song.move_device` across tracks and into rack chains on 12.2.
- Browser `drum_pad_hotswap`/`instrument_hotswap` loads of a sample onto a selected pad.
- Which property of the 12.2.0 `Live` module owns `note_number_to_name`.
- Listener availability per property outside Clip/Song (C74 pages for other classes were not fetched).
- REL coverage gap: 12.0 to 12.0.4 and later 12.4.x notes were not fully read; no gate was inferred from them.
