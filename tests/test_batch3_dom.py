"""Batch 3 bridge handlers on a fake Live: one small test per feature (clips, notes, arrangement,
cue points, automation, audio editing). Live 12.2 facts are modelled where they matter: the raw
note object identity (P-07), WarpMarker struct-only adds (P-09), arrangement envelopes = None
(P-10) and the late playhead for cue adds (P-16)."""

import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from AbletonLiveMCP import handlers  # noqa: E402
from AbletonLiveMCP.safety import Safety  # noqa: E402


class Spec:
    def __init__(self, **kw):
        self.__dict__.update(kw)


@pytest.fixture(autouse=True)
def live_module(monkeypatch):
    live = types.ModuleType("Live")
    live.Clip = types.SimpleNamespace(MidiNoteSpecification=Spec)
    monkeypatch.setitem(sys.modules, "Live", live)


class Note:
    def __init__(self, note_id, pitch, start_time, duration, velocity=100.0, mute=False):
        self.note_id, self.pitch, self.start_time = note_id, pitch, start_time
        self.duration, self.velocity, self.mute = duration, velocity, mute
        self.probability, self.velocity_deviation, self.release_velocity = 1.0, 0.0, 64.0


class RawNotes(tuple):
    """What get_notes_extended returns; apply_note_modifications accepts only this object."""


class WarpMarker:
    def __init__(self, beat_time, sample_time):
        self.beat_time, self.sample_time = beat_time, sample_time


class Envelope:
    def __init__(self):
        self.steps = []

    def insert_step(self, time, length, value):
        self.steps.append((time, length, value))

    def value_at_time(self, t):
        hits = [v for s, d, v in self.steps if s <= t < s + d]
        return hits[-1] if hits else 0.0

    def events_in_range(self, a, b):
        return [types.SimpleNamespace(time=s, value=v) for s, _d, v in self.steps if a <= s < b]

    def delete_events_in_range(self, a, b):
        self.steps = [x for x in self.steps if not a <= x[0] < b]


class Clip:
    def __init__(self, length=4.0, audio=False, start=None):
        self.name, self.length, self.color_index, self.muted = "clip", length, 0, False
        self.is_audio_clip, self.is_midi_clip = audio, not audio
        self.looping, self.loop_start, self.loop_end = True, 0.0, length
        self.start_marker, self.end_marker = 0.0, length
        self.launch_mode = self.launch_quantization = 0
        self.legato, self.velocity_amount, self.is_playing = False, 0.0, False
        self.signature_numerator = self.signature_denominator = 4
        self.is_arrangement_clip = start is not None
        if start is not None:
            self.start_time, self.end_time = start, start + length
        self.notes, self._raw, self._next_id = [], None, 1
        self.envelopes = {}
        if audio:
            self.gain, self.pitch_coarse, self.pitch_fine = 0.5, 0, 0.0
            self.warping, self.warp_mode, self.available_warp_modes = True, 0, [0, 1, 4]
            self.file_path, self.warp_markers = "C:/a.wav", [WarpMarker(0.0, 0.0)]
            self.gain_display_string = "0 dB"

    def __setattr__(self, name, value):
        bounds = {"loop_start": "loop_end", "start_marker": "end_marker"}
        if name in bounds and hasattr(self, bounds[name]) and value >= getattr(self, bounds[name]):
            raise RuntimeError(f"{name} must stay before {bounds[name]}")  # Live's own rule
        super().__setattr__(name, value)

    # notes
    def get_notes_extended(self, pitch, span, start, length):
        self._raw = RawNotes(
            n
            for n in self.notes
            if pitch <= n.pitch < pitch + span and start <= n.start_time < start + length
        )
        return self._raw

    def apply_note_modifications(self, raw):
        assert raw is self._raw, "P-07: only the raw get_notes_extended object is accepted"

    def add_new_notes(self, specs):
        ids = []
        for s in specs:
            self.notes.append(Note(self._next_id, s.pitch, s.start_time, s.duration, s.velocity))
            ids.append(self._next_id)
            self._next_id += 1
        return tuple(ids)

    def remove_notes_by_id(self, ids):
        self.notes = [n for n in self.notes if n.note_id not in ids]

    def remove_notes_extended(self, pitch, span, start, length):
        self.notes = [
            n
            for n in self.notes
            if not (pitch <= n.pitch < pitch + span and start <= n.start_time < start + length)
        ]

    # automation
    @property
    def has_envelopes(self):
        return bool(self.envelopes)

    def automation_envelope(self, param):
        return None if self.is_arrangement_clip else self.envelopes.get(id(param))

    def create_automation_envelope(self, param):
        return self.envelopes.setdefault(id(param), Envelope())

    def clear_envelope(self, param):
        self.envelopes.pop(id(param), None)

    # audio editing
    def add_warp_marker(self, marker):
        if not isinstance(marker, WarpMarker):
            raise TypeError("No registered converter (P-09)")
        self.warp_markers.append(marker)

    def move_warp_marker(self, beat, distance):
        next(m for m in self.warp_markers if m.beat_time == beat).beat_time += distance

    def remove_warp_marker(self, beat):
        self.warp_markers = [m for m in self.warp_markers if m.beat_time != beat]

    def crop(self):
        self.length = self.loop_end - self.loop_start

    def fire(self):
        self.is_playing = True

    def stop(self):
        self.is_playing = False


class Slot:
    def __init__(self, track):
        self.clip, self.track = None, track

    @property
    def has_clip(self):
        return self.clip is not None

    def create_clip(self, length):
        self.clip = Clip(length)

    def create_audio_clip(self, path):
        self.clip = Clip(8.0, audio=True)

    def delete_clip(self):
        self.clip = None

    def duplicate_clip_to(self, other):
        other.clip = Clip(self.clip.length, self.clip.is_audio_clip)
        other.clip.name = self.clip.name


class Param:
    def __init__(self, name):
        self.name, self.min, self.max, self.value = name, 0.0, 1.0, 0.5


class Device:
    name, class_name = "Dev", "Dev"

    def __init__(self):
        self.parameters = [Param("On"), Param("Cutoff")]


class Track:
    def __init__(self, name, midi=True):
        self.name, self.has_midi_input, self.color_index = name, midi, 0
        self.clip_slots = [Slot(self), Slot(self), Slot(self)]
        self.arrangement_clips, self.take_lanes = [], []
        self.devices = [Device()]

    def create_midi_clip(self, start, length):
        self.arrangement_clips.append(Clip(length, start=start))

    def create_audio_clip(self, path, start):
        self.arrangement_clips.append(Clip(8.0, audio=True, start=start))

    def delete_clip(self, clip):
        self.arrangement_clips.remove(clip)


class Cue:
    def __init__(self, time, name=""):
        self.time, self.name = time, name

    def jump(self):
        pass


class Song:
    tempo, is_playing, song_length, loop_start, loop_length = 120.0, False, 64.0, 0.0, 16.0
    signature_numerator = signature_denominator = 4
    return_tracks = []

    def __init__(self):
        self.tracks = [Track("Keys"), Track("Drums", midi=False)]
        self.scenes = [types.SimpleNamespace(name=f"S{i}") for i in range(3)]
        self.cue_points = [Cue(8.0, "Verse")]
        self._time, self._pending = 0.0, None
        self.view = types.SimpleNamespace(selected_track=None)

    @property
    def current_song_time(self):
        return self._time

    @current_song_time.setter
    def current_song_time(self, value):
        self._pending = value  # applies on the next tick (P-16)

    def settle(self):
        if self._pending is not None:
            self._time, self._pending = self._pending, None

    def is_cue_point_selected(self):
        return any(c.time == self._time for c in self.cue_points)

    def set_or_delete_cue(self):
        hit = [c for c in self.cue_points if c.time == self._time]
        if hit:
            self.cue_points.remove(hit[0])
        else:
            self.cue_points.append(Cue(self._time))


@pytest.fixture
def env():
    song = Song()
    safety = Safety(lambda: song, policy=lambda: False)
    dispatch = handlers.make_dispatch(lambda: song, types.SimpleNamespace(), safety)
    return song, dispatch


def refs(dispatch, *selectors):
    out = dispatch("ref_issue", {"targets": list(selectors)})
    assert "refs" in out, out
    return out["refs"]


def item(r, **fields):
    return {"kind": r["kind"], "ref": r["ref"], **fields}


def bad(dispatch, method, params, match):
    with pytest.raises(ValueError, match=match):
        dispatch(method, params)


def ok(result):
    assert result.get("status") == "complete", result
    return result


def midi_clip(song, notes=()):
    song.tracks[0].clip_slots[0].clip = clip = Clip(4.0)
    for i, (p, s) in enumerate(notes, 1):
        clip.notes.append(Note(i, p, s, 0.5))
    clip._next_id = len(notes) + 1
    return clip


# ---- clips -------------------------------------------------------------------------------------


def test_create_clips_midi_with_notes_and_audio_needs_audio_track(env, tmp_path):
    song, dispatch = env
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"RIFF")
    a, b = refs(
        dispatch, {"kind": "slot", "track": 0, "scene": 1}, {"kind": "slot", "track": 1, "scene": 0}
    )  # noqa: E501
    note = {"pitch": 60, "start_time": 0, "duration": 1}
    out = ok(
        dispatch(
            "create_clips",
            {
                "targets": [
                    {"ref": a["ref"], "kind": "midi", "length": 8, "notes": [note]},
                    {"ref": b["ref"], "kind": "audio", "file": str(wav)},
                ]
            },
        )
    )
    assert out["applied"][0]["note_ids"] == [1] and out["applied"][1]["kind"] == "audio"
    (c,) = refs(dispatch, {"kind": "slot", "track": 0, "scene": 2})
    bad(
        dispatch,
        "create_clips",
        {"targets": [{"ref": c["ref"], "kind": "audio", "file": str(wav)}]},
        "audio track",
    )  # noqa: E501
    assert not song.tracks[0].clip_slots[2].has_clip


def test_create_clips_replace_validates_everything_before_deleting(env):
    song, dispatch = env
    old = song.tracks[1].clip_slots[0].clip = Clip(8.0, audio=True)
    keys = midi_clip(song)
    a, b = refs(
        dispatch, {"kind": "slot", "track": 0, "scene": 0}, {"kind": "slot", "track": 1, "scene": 0}
    )
    # a MIDI clip on the audio track refuses: neither occupied slot loses its clip
    targets = [{"ref": a["ref"], "replace": True}, {"ref": b["ref"], "replace": True}]
    bad(dispatch, "create_clips", {"targets": targets}, "MIDI track")
    assert song.tracks[0].clip_slots[0].clip is keys and song.tracks[1].clip_slots[0].clip is old
    out = ok(dispatch("create_clips", {"targets": targets[:1]}))
    assert out["applied"][0]["replaced"] == "clip" and song.tracks[0].clip_slots[0].clip is not keys


def test_replace_flag_is_strict_at_the_gate_and_needs_delete(env):
    """R1, through the real dispatcher and write gate with only the ``edit`` permission: a
    malformed ``replace`` refuses before any permission decision, a real one needs ``delete``,
    and nothing is deleted either way."""
    song = env[0]
    gate = Safety(lambda: song, policy=lambda: False, permissions=lambda: {"edit"})
    dispatch = handlers.make_dispatch(lambda: song, types.SimpleNamespace(), gate)
    keys = midi_clip(song)
    song.tracks[0].arrangement_clips.append(arr := Clip(4.0, start=8.0))
    slot, track = refs(
        dispatch, {"kind": "slot", "track": 0, "scene": 0}, {"kind": "track", "track": 0}
    )
    for method, target in (("create_clips", slot), ("create_arrangement_clips", track)):
        base = {"ref": target["ref"], "start": 8, "length": 4}
        if method == "create_clips":
            base = {"ref": target["ref"]}
        for value in ("true", 1, "replace", None, [True]):
            targets = [{**base, "replace": value}]
            bad(dispatch, method, {"targets": targets}, "'replace' must be a bool")
        out = dispatch(method, {"targets": [{**base, "replace": True}]})
        assert out.get("code") == "permission_denied", (method, out)
        bad(dispatch, method, {"targets": [base]}, "occupied|overlaps")  # absent = no replace
    assert song.tracks[0].clip_slots[0].clip is keys and song.tracks[0].arrangement_clips == [arr]


def test_set_clips_widens_loop_before_narrowing(env):
    song, dispatch = env
    clip = midi_clip(song)
    (r,) = refs(dispatch, {"kind": "clip", "track": 0, "scene": 0})
    out = ok(dispatch("set_clips", {"targets": [item(r, loop=[6.0, 10.0], name="Hook")]}))
    assert (clip.loop_start, clip.loop_end, clip.name) == (6.0, 10.0, "Hook")
    assert out["applied"][0]["loop"] == [6.0, 10.0]


def test_set_clips_rejects_audio_fields_on_midi_and_writes_nothing(env):
    song, dispatch = env
    clip = midi_clip(song)
    (r,) = refs(dispatch, {"kind": "clip", "track": 0, "scene": 0})
    bad(dispatch, "set_clips", {"targets": [item(r, name="X"), item(r, gain=0.3)]}, "audio clip")
    assert clip.name == "clip"


def test_get_clips_scan_and_address_rows(env):
    song, dispatch = env
    midi_clip(song)
    rows = dispatch("get_clips", {})["clips"]
    assert [(r["track"], r["scene"]) for r in rows] == [(0, 0)]
    one = dispatch("get_clips", {"clips": [{"track": 0, "scene": 1}], "detail": True})
    assert one["clips"][0]["empty"] is True


def test_delete_and_duplicate_session_clips(env):
    song, dispatch = env
    midi_clip(song)
    (r,) = refs(dispatch, {"kind": "clip", "track": 0, "scene": 0})
    dup = ok(dispatch("duplicate_clips", {"targets": [item(r)]}))
    assert dup["applied"][0]["scene"] == 1 and song.tracks[0].clip_slots[1].has_clip
    (r,) = refs(dispatch, {"kind": "clip", "track": 0, "scene": 0})
    ok(dispatch("delete_clips", {"targets": [item(r)]}))
    assert not song.tracks[0].clip_slots[0].has_clip


# ---- notes -------------------------------------------------------------------------------------


def test_get_notes_lists_notes_past_the_clip_end(env):
    song, dispatch = env
    midi_clip(song, [(60, 0.0), (62, 6.0)])  # 6.0 is past the 4-beat clip end
    out = dispatch("get_notes", {"track": 0, "scene": 0})
    assert out["total"] == 2 and out["past_clip_end"] == 1
    assert set(out["notes"][0]) >= {"note_id", "probability", "release_velocity"}


def test_edit_notes_modifies_through_the_raw_object(env):
    song, dispatch = env
    clip = midi_clip(song, [(60, 0.1), (64, 1.0)])
    (r,) = refs(dispatch, {"kind": "clip", "track": 0, "scene": 0})
    out = ok(
        dispatch(
            "edit_notes",
            {
                "targets": [item(r)],
                "modify": [{"note_id": 2, "velocity": 50}],
                "transpose": {"semitones": 12, "ids": [1]},
                "quantize": {"grid": 0.25},
            },
        )
    )
    by_id = {n.note_id: n for n in clip.notes}
    assert by_id[1].pitch == 72 and by_id[1].start_time == 0.0 and by_id[2].velocity == 50
    assert out["items"][0]["op"] == "modify"


def test_edit_notes_remove_add_and_duplicate_region(env):
    song, dispatch = env
    clip = midi_clip(song, [(60, 0.0), (62, 1.0)])
    (r,) = refs(dispatch, {"kind": "clip", "track": 0, "scene": 0})
    out = ok(
        dispatch(
            "edit_notes",
            {
                "targets": [item(r)],
                "remove_ids": [2],
                "duplicate_region": {"start": 0, "length": 1, "dest": 2},
                "add": [{"pitch": 67, "start_time": 3, "duration": 1}],
            },
        )
    )
    assert sorted((n.pitch, n.start_time) for n in clip.notes) == [(60, 0.0), (60, 2.0), (67, 3.0)]
    assert out["note_count"] == 3


def test_edit_notes_rejects_bad_ids_and_out_of_range_transpose(env):
    song, dispatch = env
    clip = midi_clip(song, [(120, 0.0)])
    (r,) = refs(dispatch, {"kind": "clip", "track": 0, "scene": 0})
    bad(dispatch, "edit_notes", {"targets": [item(r)], "remove_ids": [9]}, "unknown")
    bad(dispatch, "edit_notes", {"targets": [item(r)], "transpose": {"semitones": 12}}, "0..127")
    assert [n.pitch for n in clip.notes] == [120]


# ---- arrangement -------------------------------------------------------------------------------


def test_arrangement_create_read_and_overlap_refusal(env):
    song, dispatch = env
    (t,) = refs(dispatch, {"kind": "track", "track": 0})
    ok(
        dispatch(
            "create_arrangement_clips", {"targets": [{"ref": t["ref"], "start": 4, "length": 4}]}
        )
    )
    bad(
        dispatch,
        "create_arrangement_clips",
        {"targets": [{"ref": t["ref"], "start": 6}]},
        "overlaps",
    )
    assert len(song.tracks[0].arrangement_clips) == 1
    out = dispatch("get_arrangement", {"tracks": [0]})
    assert out["tracks"][0]["clips"][0]["start"] == 4 and out["cues"][0]["name"] == "Verse"


def test_disabled_arrangement_branches_refuse_unsupported(env):
    song, dispatch = env
    song.tracks[0].arrangement_clips.append(Clip(4.0, start=0.0))
    (t,) = refs(dispatch, {"kind": "track", "track": 0})
    (c,) = refs(dispatch, {"kind": "arr_clip", "track": 0, "arrangement": 0})
    for method, params in [
        (
            "create_arrangement_clips",
            {"targets": [{"ref": t["ref"], "start": 8, "kind": "from_session"}]},
        ),  # noqa: E501
        ("edit_arrangement_clips", {"targets": [{"ref": c["ref"], "split_at": 2.0}]}),
        ("edit_arrangement_clips", {"targets": [{"ref": c["ref"], "move_to": 16.0}]}),
        ("duplicate_clips", {"targets": [item(c)]}),
    ]:
        out = dispatch(method, params)
        assert out.get("code") == "unsupported", (method, out)
    assert len(song.tracks[0].arrangement_clips) == 1


class GroupTrack(Track):
    is_foldable = True

    @property
    def arrangement_clips(self):
        raise RuntimeError("group tracks have no arrangement clips")  # Live 12.2

    @arrangement_clips.setter
    def arrangement_clips(self, _value):
        pass


def test_group_track_is_marked_in_a_whole_set_read_and_refused_as_a_reference(env):
    song, dispatch = env
    song.tracks.append(GroupTrack("Bus"))
    out = dispatch("get_arrangement", {})
    assert out["tracks"][2] == {"track": 2, "name": "Bus", "group": True}, out
    sel = {"kind": "arr_clip", "track": 2, "arrangement": 0}
    bad(dispatch, "ref_issue", {"targets": [sel]}, "a group track has no arrangement clips")


def test_whole_set_read_pages_past_64_tracks(env):
    song, dispatch = env
    song.tracks = [Track(f"T{i}") for i in range(70)]
    for t in song.tracks:  # 4 clips per track: the 256-row budget ends inside track 64
        t.arrangement_clips = [Clip(1.0, start=float(k)) for k in range(4)]
    first = dispatch("get_arrangement", {"include": ["clips"]})
    assert len(first["tracks"]) == 64 and first["truncated"] is False, first.get("next_track")
    assert first["next_track"] == 64
    rest = dispatch("get_arrangement", {"include": ["clips"], "next_track": 64})
    assert [r["track"] for r in rest["tracks"]] == list(range(64, 70)) and "next_track" not in rest


def test_cue_add_is_asynchronous_and_exact(env):
    song, dispatch = env
    gen = dispatch.safety.generation
    out = ok(
        dispatch(
            "set_cue_points",
            {"cues": [], "add": [{"time": 16.0, "name": "Drop"}, {"time": 8.0}], "generation": gen},
        )
    )
    op = out["applied"][0]["operation"]
    assert len(song.cue_points) == 1  # nothing toggled in the call itself
    for _ in range(12):
        dispatch.operations.tick()
        song.settle()
    snap = dispatch.operations.get(op)
    assert snap["state"] == "ready", snap
    assert sorted((c.time, c.name) for c in song.cue_points) == [(8.0, "Verse"), (16.0, "Drop")]
    assert snap["result"]["results"][1]["reused"] is True


def test_cue_task_stops_when_writes_are_switched_off_midway():
    song, read_only = Song(), [False]
    safety = Safety(lambda: song, policy=lambda: read_only[0])
    dispatch = handlers.make_dispatch(lambda: song, types.SimpleNamespace(), safety)

    def start():
        p = {"cues": [], "add": [{"time": 16.0}, {"time": 24.0}], "generation": safety.generation}
        out = ok(dispatch("set_cue_points", p))
        return out["applied"][0]["operation"]

    op = start()
    while len(song.cue_points) == 1:  # until the first add has toggled
        dispatch.operations.tick()
        song.settle()
    read_only[0] = True
    for _ in range(12):
        dispatch.operations.tick()
        song.settle()
    snap = dispatch.operations.get(op)
    assert snap["state"] == "ready" and snap["result"]["status"] == "partial", snap
    assert [r["time"] for r in snap["result"]["results"]] == [16.0]  # earlier result kept
    assert "refused:read_only" in snap["result"]["error"] and len(song.cue_points) == 2
    read_only[0] = False
    op = start()
    read_only[0] = True  # off before the first tick: nothing changes, the task failed
    dispatch.operations.tick()
    assert dispatch.operations.get(op)["state"] == "failed" and len(song.cue_points) == 2


@pytest.mark.parametrize("revoke", ["read_only", "permission"])
@pytest.mark.parametrize(
    ("ticks", "status", "cues", "playhead_moved"),
    [
        (0, "not_applied", [8.0], False),  # before the seek
        (1, "not_applied", [8.0], True),  # after the seek, before the toggle
        (2, "partial", [8.0, 16.0], True),  # toggled; the new cue's rename is a write too
    ],
)
def test_cue_task_rechecks_policy_before_every_write(revoke, ticks, status, cues, playhead_moved):
    """R4: revoking writes (read_only, or the edit permission) at any phase stops the task
    before its next write; a moved playhead goes back and the outcome says what changed."""
    song, read_only, perms = Song(), [False], {"edit", "delete"}
    safety = Safety(lambda: song, policy=lambda: read_only[0], permissions=lambda: set(perms))
    dispatch = handlers.make_dispatch(lambda: song, types.SimpleNamespace(), safety)
    song._time = 4.0
    p = {"cues": [], "add": [{"time": 16.0, "name": "Drop"}], "generation": safety.generation}
    out = ok(dispatch("set_cue_points", p))
    assert "undo_steps" not in out  # its writes land later, outside this call's undo step
    op = out["applied"][0]["operation"]
    for _ in range(ticks):
        dispatch.operations.tick()
        song.settle()
    read_only[0] = revoke == "read_only"
    if revoke == "permission":
        perms.discard("edit")
    for _ in range(4):
        dispatch.operations.tick()
        song.settle()
    snap = dispatch.operations.get(op)
    result = snap["result"]
    assert result["status"] == status and "refused:" in result["error"], snap
    assert snap["state"] == ("failed" if status == "not_applied" else "ready")
    assert sorted(c.time for c in song.cue_points) == cues
    assert all(c.name != "Drop" for c in song.cue_points)  # never renamed after revocation
    assert result["playhead"]["moved"] is playhead_moved and song.current_song_time == 4.0


def test_cue_add_refuses_while_playing(env):
    song, dispatch = env
    song.is_playing = True
    out = dispatch(
        "set_cue_points",
        {"cues": [], "add": [{"time": 4.0}], "generation": dispatch.safety.generation},
    )  # noqa: E501
    assert out.get("code") == "transport_playing"


# ---- automation --------------------------------------------------------------------------------


def test_session_automation_ramp_and_arrangement_refusal(env):
    song, dispatch = env
    clip = midi_clip(song)
    c, p = refs(
        dispatch,
        {"kind": "clip", "track": 0, "scene": 0},
        {"kind": "param", "track": 0, "path": [0], "parameter": 1},
    )
    ramp = {"start": 0, "end": 4, "from": 0.0, "to": 1.0, "steps": 4}
    out = ok(
        dispatch(
            "set_automation",
            {"targets": [item(c, param=p["ref"], param_kind="param", ramps=[ramp])]},
        )
    )  # noqa: E501
    assert out["applied"][0]["events"] == 4 and clip.has_envelopes
    read = dispatch(
        "get_automation",
        {"track": 0, "scene": 0, "parameter": {"kind": "param", "path": [0], "parameter": 1}},
    )  # noqa: E501
    assert read["has_envelope"] and read["samples"][0]["value"] == 0.0
    song.tracks[0].arrangement_clips.append(Clip(4.0, start=0.0))
    (a,) = refs(dispatch, {"kind": "arr_clip", "track": 0, "arrangement": 0})
    out = dispatch(
        "set_automation", {"targets": [item(a, param=p["ref"], param_kind="param", clear=True)]}
    )  # noqa: E501
    assert out.get("code") == "unsupported"


# ---- audio editing -----------------------------------------------------------------------------


def test_warp_markers_use_the_struct_and_beat_times(env):
    song, dispatch = env
    song.tracks[1].clip_slots[0].clip = clip = Clip(8.0, audio=True)
    (r,) = refs(dispatch, {"kind": "clip", "track": 1, "scene": 0})
    ops = [
        {"action": "add", "beat_time": 4.0, "sample_time": 2.0},
        {"action": "move", "beat_time": 4.0, "distance": 0.5},
    ]
    out = ok(dispatch("edit_audio_clip", {"targets": [item(r)], "warp_markers": ops, "gain": 0.7}))
    assert [m.beat_time for m in clip.warp_markers] == [0.0, 4.5] and clip.gain == 0.7
    assert out["clip"]["warp_markers"][1] == {"beat_time": 4.5, "sample_time": 2.0}


def test_warp_marker_add_refuses_without_an_existing_marker(env):
    song, dispatch = env
    song.tracks[1].clip_slots[0].clip = clip = Clip(8.0, audio=True)
    clip.warp_markers = []
    (r,) = refs(dispatch, {"kind": "clip", "track": 1, "scene": 0})
    add = [{"action": "add", "beat_time": 1.0, "sample_time": 0.5}]
    bad(dispatch, "edit_audio_clip", {"targets": [item(r)], "warp_markers": add}, "no warp marker")
    assert clip.warp_markers == []
