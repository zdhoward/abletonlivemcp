"""Transport, scene and clip handlers under the M1b contract.

Reads find objects by index and hand back references; every write names its target by a
reference (or the Set ``generation`` for global writes) and runs under a writable policy, as in
tests/test_handlers.py (which owns the generic safety scenarios: read-only policy, stale and
wrong-kind references, leases). Here: one shared bare-index guard table across the supported
features, plus each feature's own validation, readback and bounds.
"""

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
    song.tracks[0].clip_slots[0].create_clip(4)
    return song.tracks[0].clip_slots[0].clip, clip_ref(dispatch), dispatch


def note(**changes):
    return {"pitch": 60, "start_time": 0, "duration": 1, "velocity": 100, **changes}


# ---- shared guard: a bare index never authorizes a write ---------------------------------------

BARE_INDEX_WRITES = [  # one scenario per supported feature
    ("set_scene_name", {"scene": 0, "name": "X"}, "reference_required"),
    ("fire_scene", {"scene": 0}, "reference_required"),
    ("create_clips", {"targets": [{"ref": 0}]}, "reference_required"),
    ("edit_notes", {"targets": [{"kind": "clip", "ref": 0}]}, "reference_required"),
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
        "create_scene", "set_scene_name", "fire_scene", "create_clips", "edit_notes",
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
        ("get_notes", {"track": True, "scene": 0}, "track"),
    ],
)
def test_clip_reads_validate_indices(env, method, params, key):
    _song, _app, dispatch = env
    with pytest.raises(ValueError, match=key):
        dispatch(method, params)


# ---- clip lifecycle ----------------------------------------------------------------------------


# ---- notes -------------------------------------------------------------------------------------


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
