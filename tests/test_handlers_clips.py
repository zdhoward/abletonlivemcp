"""Transport, scene and clip handlers under the M1b contract.

Reads find objects by index and hand back references; every write names its target by a
reference (or the Set ``generation`` for global writes) and runs under a writable policy, as in
tests/test_handlers.py (which owns the generic safety scenarios: read-only policy, stale and
wrong-kind references, leases). Here: one shared bare-index guard table across the supported
features, plus each feature's own validation, readback and bounds.
"""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from AbletonLiveMCP import handlers  # noqa: E402
from AbletonLiveMCP.safety import CLASSIFICATION, WRITE, Safety  # noqa: E402
from test_handlers import App, Song, Track  # noqa: E402


class Scene:
    def __init__(self, name="Scene"):
        self.name = name
        self.is_triggered = False

    def fire(self):
        self.is_triggered = True


class Clip:
    def __init__(self, length=4):
        self.name = "MIDI clip"
        self.length = length
        self.is_playing = False
        self.looping = True
        self.is_midi_clip = True
        self.notes = []
        self.writes = 0

    def set_notes(self, notes):
        self.writes += 1
        self.notes.extend(notes)

    def get_notes(self, start, pitch, span, pitches):
        assert (start, pitch, span, pitches) == (0.0, 0, self.length, 128)
        return (
            n
            for n in self.notes
            if start <= n[1] < start + span and pitch <= n[0] < pitch + pitches
        )

    def fire(self):
        self.is_playing = True

    def stop(self):
        self.is_playing = False


class ModernClip(Clip):
    def add_new_notes(self, notes):
        self.writes += 1
        self.notes.extend((n.pitch, n.start_time, n.duration, n.velocity, n.mute) for n in notes)

    def set_notes(self, notes):
        pytest.fail("modern API must take precedence over set_notes")

    def get_notes_extended(self, pitch, pitches, start, span):
        assert (pitch, pitches, start, span) == (0, 128, 0.0, self.length)
        return (
            SimpleNamespace(pitch=p, start_time=s, duration=d, velocity=v, mute=m)
            for p, s, d, v, m in self.notes
            if start <= s < start + span
        )


class Slot:
    def __init__(self):
        self.clip = None

    @property
    def has_clip(self):
        return self.clip is not None

    def create_clip(self, length):
        assert not self.has_clip
        self.clip = Clip(length)


class Session(Song):
    current_song_time = 12.5

    def __init__(self):
        super().__init__()
        self.scenes = [Scene("Intro"), Scene("Verse")]
        audio = Track("Audio")
        audio.has_midi_input = False
        self.tracks.append(audio)
        for track in self.tracks:
            track.clip_slots = [Slot(), Slot()]

    def start_playing(self):
        self.is_playing = True

    def stop_playing(self):
        self.is_playing = False

    def create_scene(self, index):
        index = len(self.scenes) if index == -1 else index
        self.scenes.insert(index, Scene("New scene"))
        for track in self.tracks:
            track.clip_slots.insert(index, Slot())


@pytest.fixture
def env():
    """Writable policy (the same fixture style as tests/test_handlers.py)."""
    song, app = Session(), App()
    safety = Safety(lambda: song, policy=lambda: False)
    return song, app, handlers.make_dispatch(lambda: song, app, safety)


def gen(dispatch):
    return {"generation": dispatch.safety.generation}


def slot_ref(dispatch, track=0, scene=0):
    return dispatch("clip_slot", {"track": track, "scene": scene})["slot"]


def clip_ref(dispatch, track=0, scene=0):
    return dispatch("clip_slot", {"track": track, "scene": scene})["clip"]


def scene_ref(dispatch, index=0):
    return dispatch("scenes", {})[index]["ref"]


@pytest.fixture
def clip_env(env):
    """A fresh clip in track 0 / scene 0 plus its reference."""
    song, app, dispatch = env
    dispatch("create_clip", {"slot": slot_ref(dispatch), "length_beats": 4})
    return song.tracks[0].clip_slots[0].clip, clip_ref(dispatch), dispatch


def note(**changes):
    return {"pitch": 60, "start_time": 0, "duration": 1, "velocity": 100, **changes}


def add(dispatch, ref, notes):
    return dispatch("add_notes", {"clip": ref, "notes": notes})


# ---- shared guard: a bare index never authorizes a write ---------------------------------------

BARE_INDEX_WRITES = [  # one scenario per supported feature
    ("set_scene_name", {"scene": 0, "name": "X"}, "reference_required"),
    ("fire_scene", {"scene": 0}, "reference_required"),
    ("create_clip", {"slot": 0, "length_beats": 4}, "reference_required"),
    ("add_notes", {"clip": 0, "notes": [note()]}, "reference_required"),
    ("fire_clip", {"clip": 0}, "reference_required"),
    ("stop_clip", {"clip": 0}, "reference_required"),
    ("create_scene", {"index": -1}, "stale_generation"),  # global writes need the generation
    ("play", {}, "stale_generation"),
    ("stop", {}, "stale_generation"),
]


@pytest.mark.parametrize("method,params,code", BARE_INDEX_WRITES)
def test_writes_without_a_reference_or_generation_are_refused_and_change_nothing(
    env, method, params, code
):
    song, _app, dispatch = env
    result = dispatch(method, params)
    assert result["refused"] is True and result["applied"] is False and result["code"] == code
    assert [s.name for s in song.scenes] == ["Intro", "Verse"] and not song.is_playing
    assert not any(slot.has_clip for t in song.tracks for slot in t.clip_slots)
    assert not any(s.is_triggered for s in song.scenes)


def test_every_scene_clip_and_transport_write_is_in_the_guard_table():
    guarded = {m for m, _p, _c in BARE_INDEX_WRITES}
    feature = {
        "create_scene", "set_scene_name", "fire_scene", "create_clip", "add_notes",
        "fire_clip", "stop_clip", "play", "stop",
    }  # fmt: skip
    assert feature <= {m for m, k in CLASSIFICATION.items() if k == WRITE}
    assert guarded == feature


def test_a_scene_reference_is_not_a_clip_reference(env):
    _song, _app, dispatch = env
    result = dispatch("fire_clip", {"clip": scene_ref(dispatch)})
    assert result["refused"] and result["code"] == "stale_reference"


# ---- transport ---------------------------------------------------------------------------------


def test_transport_readbacks(env):
    song, _app, dispatch = env
    assert dispatch("get_transport", {}) == {
        "is_playing": False,
        "tempo": 120.0,
        "signature": [4, 4],
        "current_song_time": 12.5,
    }
    assert (
        dispatch("play", gen(dispatch)) == {"is_playing": song.is_playing} == {"is_playing": True}
    )
    assert dispatch("stop", gen(dispatch)) == {"is_playing": False}


def test_transport_returns_actual_state_if_start_is_delayed(env, monkeypatch):
    song, _app, dispatch = env
    monkeypatch.setattr(song, "start_playing", lambda: None)
    assert dispatch("play", gen(dispatch)) == {"is_playing": False}


# ---- scenes ------------------------------------------------------------------------------------


@pytest.mark.parametrize("index", [None, -1, 0, 2])
def test_create_scene(env, index):
    song, _app, dispatch = env
    params = {**gen(dispatch), **({} if index is None else {"index": index})}
    result = dispatch("create_scene", params)
    actual = 2 if index in (None, -1) else index
    assert result == {"scene_count": 3, "index": actual, "name": song.scenes[actual].name}
    assert len(song.tracks[0].clip_slots) == 3


@pytest.mark.parametrize("index", [True, 1.5, "0", -2, 3])
def test_create_scene_invalid_index(env, index):
    song, _app, dispatch = env
    with pytest.raises(ValueError, match="index"):
        dispatch("create_scene", {"index": index, **gen(dispatch)})
    assert len(song.scenes) == 2


def test_scene_name_and_launch_readbacks(env):
    song, _app, dispatch = env
    ref = scene_ref(dispatch)
    assert dispatch("set_scene_name", {"scene": ref, "name": "Chorus"}) == {"name": "Chorus"}
    assert song.scenes[0].name == "Chorus"
    assert dispatch("fire_scene", {"scene": ref}) == {"name": "Chorus", "is_triggered": True}
    assert song.scenes[0].is_triggered


@pytest.mark.parametrize("name", [None, 42, True, []])
def test_scene_name_requires_string(env, name):
    song, _app, dispatch = env
    with pytest.raises(ValueError, match="name"):
        dispatch("set_scene_name", {"scene": scene_ref(dispatch), "name": name})
    assert song.scenes[0].name == "Intro"


# ---- clip reads: indices find objects and are validated ----------------------------------------


@pytest.mark.parametrize(
    "method,params,key",
    [
        ("clip_slot", {"track": 3, "scene": 0}, "track"),  # past the last track
        ("clip_slot", {"track": 0, "scene": 2}, "scene"),  # past the last scene
        ("clip_slot", {"track": True, "scene": 0}, "track"),  # bool is not an index
        ("get_clip", {"track": 0, "scene": -1}, "scene"),
        ("get_notes", {"track": "0", "scene": 0}, "track"),
    ],
)
def test_clip_reads_validate_indices(env, method, params, key):
    _song, _app, dispatch = env
    with pytest.raises(ValueError, match=key):
        dispatch(method, params)


def test_empty_and_missing_slots(env):
    song, _app, dispatch = env
    assert dispatch("clip_slot", {"track": 0, "scene": 0})["has_clip"] is False
    assert "clip" not in dispatch("clip_slot", {"track": 0, "scene": 0})
    for method in ("get_clip", "get_notes"):
        with pytest.raises(ValueError, match="empty"):
            dispatch(method, {"track": 0, "scene": 0})
    song.tracks[0].clip_slots = []
    with pytest.raises(ValueError, match="no clip slot"):
        dispatch("get_clip", {"track": 0, "scene": 0})


# ---- clip lifecycle ----------------------------------------------------------------------------


def test_create_get_launch_and_stop_clip(env):
    song, _app, dispatch = env
    read = {"track": 0, "scene": 1}
    assert dispatch("create_clip", {"slot": slot_ref(dispatch, 0, 1), "length_beats": 1024}) == {
        "name": "MIDI clip",
        "length": 1024,
        "is_playing": False,
        "looping": True,
    }
    clip = song.tracks[0].clip_slots[1].clip
    assert dispatch("get_clip", read)["length"] == clip.length
    ref = clip_ref(dispatch, 0, 1)
    assert dispatch("fire_clip", {"clip": ref})["is_playing"] is clip.is_playing is True
    assert dispatch("stop_clip", {"clip": ref})["is_playing"] is clip.is_playing is False


def test_create_clip_refuses_an_occupied_slot_without_replacing_it(clip_env):
    clip, _ref, dispatch = clip_env
    song = dispatch.safety.song()
    with pytest.raises(ValueError, match="occupied"):
        dispatch("create_clip", {"slot": slot_ref(dispatch), "length_beats": 4})
    assert song.tracks[0].clip_slots[0].clip is clip


@pytest.mark.parametrize("length", [0, -1, 1024.1, True, "4", None, float("nan"), float("inf")])
def test_create_clip_bad_length(env, length):
    song, _app, dispatch = env
    with pytest.raises(ValueError, match="length_beats"):
        dispatch("create_clip", {"slot": slot_ref(dispatch), "length_beats": length})
    assert not song.tracks[0].clip_slots[0].has_clip


def test_create_clip_rejects_audio_track_and_accepts_fractions(env):
    song, _app, dispatch = env
    with pytest.raises(ValueError, match="MIDI track"):
        dispatch("create_clip", {"slot": slot_ref(dispatch, 2, 0), "length_beats": 4})
    assert not song.tracks[2].clip_slots[0].has_clip
    made = dispatch("create_clip", {"slot": slot_ref(dispatch), "length_beats": 0.25})
    assert made["length"] == 0.25


# ---- notes -------------------------------------------------------------------------------------


def test_legacy_notes_add_and_readback(clip_env):
    clip, ref, dispatch = clip_env
    read = {"track": 0, "scene": 0}
    assert dispatch("get_notes", read) == {"notes": [], "truncated": False}
    assert add(dispatch, ref, [note()]) == {"notes": [note(mute=False)], "truncated": False}
    result = add(dispatch, ref, [note(pitch=127, mute=True)])
    assert result["notes"] == [note(mute=False), note(pitch=127, mute=True)]
    assert len(clip.notes) == 2 and clip.writes == 2


def test_note_value_boundaries(clip_env):
    _clip, ref, dispatch = clip_env
    notes = [note(pitch=0, velocity=1, duration=0.25), note(pitch=127, velocity=127)]
    assert add(dispatch, ref, notes) == {
        "notes": [{**n, "mute": False} for n in notes],
        "truncated": False,
    }


def test_modern_notes_preferred_and_probed(env, monkeypatch):
    song, app, dispatch = env
    monkeypatch.setitem(
        sys.modules,
        "Live",
        SimpleNamespace(Clip=SimpleNamespace(MidiNoteSpecification=SimpleNamespace)),
    )
    clip = song.tracks[0].clip_slots[0].clip = ModernClip()
    result = add(dispatch, clip_ref(dispatch), [note()])
    assert result == {"notes": [note(mute=False)], "truncated": False}
    assert clip.writes == 1
    caps = handlers.probe(song, app)
    for key in ("add_new_notes", "set_notes", "get_notes_extended", "get_notes"):
        assert caps[f"clip.{key}"] is True
    assert caps["Live.Clip.MidiNoteSpecification"] is True
    assert caps["clip.note_api_sample_count"] == 1


@pytest.mark.parametrize("modern", [False, True])
def test_notes_read_is_bounded(env, modern):
    song, _app, dispatch = env
    clip = song.tracks[0].clip_slots[0].clip = ModernClip() if modern else Clip()
    clip.notes = [(60, 0, 1, 100, False)] * (handlers.NOTE_LIMIT + 1)
    result = dispatch("get_notes", {"track": 0, "scene": 0})
    assert len(result["notes"]) == handlers.NOTE_LIMIT
    assert result["truncated"] is True


@pytest.mark.parametrize("count", [0, handlers.NOTE_LIMIT])
def test_note_batch_boundaries(clip_env, count):
    clip, ref, dispatch = clip_env
    result = add(dispatch, ref, [note()] * count)
    assert len(result["notes"]) == count and result["truncated"] is False
    assert len(clip.notes) == count


@pytest.mark.parametrize("notes", [None, {}, (), [None], [note()] * (handlers.NOTE_LIMIT + 1)])
def test_bad_note_batches(clip_env, notes):
    clip, ref, dispatch = clip_env
    with pytest.raises(ValueError):
        add(dispatch, ref, notes)
    assert clip.writes == 0


@pytest.mark.parametrize("field,value", [
    ("pitch", -1), ("pitch", 128), ("pitch", True), ("pitch", 60.0), ("pitch", "60"),
    ("start_time", -0.1), ("start_time", True), ("start_time", float("nan")),
    ("duration", 0), ("duration", -1), ("duration", "1"), ("duration", float("inf")),
    ("velocity", 0), ("velocity", 128), ("velocity", False), ("velocity", 100.5),
    ("mute", 0), ("mute", "false"),
])  # fmt: skip
def test_note_fields_validate_entire_batch_before_write(clip_env, field, value):
    clip, ref, dispatch = clip_env
    with pytest.raises(ValueError, match=field):
        add(dispatch, ref, [note(), note(**{field: value})])  # the bad note is the second one
    assert clip.writes == 0 and clip.notes == []


@pytest.mark.parametrize("field", ["pitch", "start_time", "duration", "velocity"])
def test_note_missing_fields(clip_env, field):
    clip, ref, dispatch = clip_env
    value = note()
    del value[field]
    with pytest.raises(ValueError, match=field):
        add(dispatch, ref, [value])
    assert clip.writes == 0


@pytest.mark.parametrize("method", ["get_notes", "add_notes"])
def test_notes_reject_audio_clips(clip_env, method):
    clip, ref, dispatch = clip_env
    clip.is_midi_clip = False
    params = {"track": 0, "scene": 0} if method == "get_notes" else {"clip": ref, "notes": [note()]}
    with pytest.raises(ValueError, match="MIDI clip"):
        dispatch(method, params)
    assert clip.writes == 0


def test_missing_write_api_and_probe(env):
    song, app, dispatch = env
    clip = song.tracks[0].clip_slots[0].clip = SimpleNamespace(
        is_midi_clip=True, get_notes=lambda *args: (), length=4
    )
    ref = clip_ref(dispatch)
    with pytest.raises(ValueError, match="neither add_new_notes nor set_notes"):
        add(dispatch, ref, [note()])
    caps = handlers.probe(song, app)
    assert caps["clip.add_new_notes"] is False
    assert caps["clip.set_notes"] is False
    assert caps["clip.get_notes"] is True
    del clip.get_notes
    with pytest.raises(ValueError, match="neither get_notes_extended nor get_notes"):
        add(dispatch, ref, [note()])
    with pytest.raises(ValueError, match="neither get_notes_extended nor get_notes"):
        dispatch("get_notes", {"track": 0, "scene": 0})


@pytest.mark.parametrize("live", [None, SimpleNamespace(), SimpleNamespace(Clip=SimpleNamespace())])
def test_missing_note_specification(env, monkeypatch, live):
    song, app, dispatch = env
    monkeypatch.setitem(sys.modules, "Live", live)
    clip = song.tracks[0].clip_slots[0].clip = ModernClip()
    assert handlers.probe(song, app)["Live.Clip.MidiNoteSpecification"] is False
    with pytest.raises(ValueError, match="MidiNoteSpecification is unavailable"):
        add(dispatch, clip_ref(dispatch), [note()])
    assert clip.writes == 0


def test_probe_empty_session(env):
    song, app, _dispatch = env
    song.tracks = []
    caps = handlers.probe(song, app)
    assert caps["clip.note_api_sample_count"] == 0
    assert caps["clip.add_new_notes"] is False


def test_probe_slot_sampling_is_bounded(env, monkeypatch):
    song, app, _dispatch = env
    monkeypatch.setattr(handlers, "LIST_LIMIT", 1)
    song.tracks[0].clip_slots[1].clip = ModernClip()
    caps = handlers.probe(song, app)
    assert caps["clip.note_api_sample_count"] == 0
    assert caps["clip.add_new_notes"] is False


# ---- safety: nothing destructive exists --------------------------------------------------------


@pytest.mark.parametrize("method", ["delete_scene", "delete_clip", "delete_notes"])
def test_no_destructive_handlers(env, method):
    _song, _app, dispatch = env
    assert method not in CLASSIFICATION
    with pytest.raises(ValueError, match="unclassified"):
        dispatch(method, {})


# ---- MCP wrappers: registered, and writes forward references (settle: test_server_settle) ------


@pytest.mark.parametrize(
    "tool,args,method,params",
    [
        ("live_create_scene", {"index": 1}, "create_scene", {"index": 1, "generation": 5}),
        ("live_set_scene_name", {"scene": 1, "name": "B"}, "set_scene_name",
         {"scene": "R1", "name": "B"}),
        ("live_fire_scene", {"scene": 0}, "fire_scene", {"scene": "R0"}),
        ("live_create_clip", {"track": 0, "scene": 1, "length_beats": 4}, "create_clip",
         {"slot": "SLOT", "length_beats": 4}),
        ("live_add_notes", {"track": 0, "scene": 1, "notes": [note()]}, "add_notes",
         {"clip": "CLIP", "notes": [note()]}),
    ],
)  # fmt: skip
def test_mcp_write_tools_forward_references_and_readbacks(monkeypatch, tool, args, method, params):
    from abletonlivemcp import server

    calls = []
    readback = {"actual": "readback"}

    def call(name, arguments=None):
        calls.append((name, arguments))
        return {
            "session_info": {"generation": 5},
            "scenes": [{"index": i, "ref": f"R{i}", "name": "s"} for i in range(2)],
            "clip_slot": {"slot": "SLOT", "has_clip": True, "clip": "CLIP"},
        }.get(name, readback)

    monkeypatch.setattr(server._bridge, "call", call)
    monkeypatch.setattr(server, "_writable", lambda: None)
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert tool in names
    assert getattr(server, tool)(**args) is readback
    assert calls[-1] == (method, params)
