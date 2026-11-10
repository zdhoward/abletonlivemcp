import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from AbletonLiveMCP import handlers  # noqa: E402
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
            n for n in self.notes
            if start <= n[1] < start + span and pitch <= n[0] < pitch + pitches
        )

    def fire(self):
        self.is_playing = True

    def stop(self):
        self.is_playing = False


class ModernClip(Clip):
    def add_new_notes(self, notes):
        self.writes += 1
        self.notes.extend(
            (n.pitch, n.start_time, n.duration, n.velocity, n.mute) for n in notes
        )

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
    song, app = Session(), App()
    return song, app, handlers.make_dispatch(song, app)


@pytest.fixture
def clip_env(env):
    song, app, dispatch = env
    dispatch("create_clip", {"track": 0, "scene": 0, "length_beats": 4})
    return song.tracks[0].clip_slots[0].clip, app, dispatch


def note(**changes):
    return {"pitch": 60, "start_time": 0, "duration": 1, "velocity": 100, **changes}


def test_transport_readbacks(env):
    song, _app, dispatch = env
    assert dispatch("get_transport", {}) == {
        "is_playing": False,
        "tempo": 120.0,
        "signature": [4, 4],
        "current_song_time": 12.5,
    }
    assert dispatch("play", {}) == {"is_playing": song.is_playing} == {"is_playing": True}
    assert dispatch("stop", {}) == {"is_playing": song.is_playing} == {"is_playing": False}


def test_transport_returns_actual_state_if_start_is_delayed(env, monkeypatch):
    song, _app, dispatch = env
    monkeypatch.setattr(song, "start_playing", lambda: None)
    assert dispatch("play", {}) == {"is_playing": False}


@pytest.mark.parametrize("index", [None, -1, 0, 2])
def test_create_scene(env, index):
    song, _app, dispatch = env
    result = dispatch("create_scene", {} if index is None else {"index": index})
    actual = 2 if index in (None, -1) else index
    assert result == {"scene_count": 3, "index": actual, "name": song.scenes[actual].name}
    assert len(song.tracks[0].clip_slots) == 3


@pytest.mark.parametrize("index", [True, False, 1.5, "0", None, -2, 3])
def test_create_scene_invalid_index(env, index):
    song, _app, dispatch = env
    with pytest.raises(ValueError, match="index"):
        dispatch("create_scene", {"index": index})
    assert len(song.scenes) == 2


def test_scene_name_and_launch_readbacks(env):
    song, _app, dispatch = env
    assert dispatch("set_scene_name", {"scene": 0, "name": "Chorus"}) == {
        "name": song.scenes[0].name
    } == {"name": "Chorus"}
    assert dispatch("fire_scene", {"scene": 0}) == {"name": "Chorus", "is_triggered": True}
    assert song.scenes[0].is_triggered


@pytest.mark.parametrize("name", [None, 42, True, []])
def test_scene_name_requires_string(env, name):
    song, _app, dispatch = env
    with pytest.raises(ValueError, match="name"):
        dispatch("set_scene_name", {"scene": 0, "name": name})
    assert song.scenes[0].name == "Intro"


@pytest.mark.parametrize("method", ["set_scene_name", "fire_scene"])
@pytest.mark.parametrize("index", [-1, 2, True, False, "0", 0.0, None])
def test_scene_bad_indexes(env, method, index):
    _song, _app, dispatch = env
    with pytest.raises(ValueError, match="scene"):
        dispatch(method, {"scene": index, "name": "New"})


@pytest.mark.parametrize(
    "method", ["create_clip", "get_clip", "add_notes", "get_notes", "fire_clip", "stop_clip"]
)
@pytest.mark.parametrize("key,bad", [("track", 3), ("scene", 2)])
@pytest.mark.parametrize("value", [-1, True, False, "0", 0.0, None, "outside"])
def test_clip_bad_indexes(env, method, key, bad, value):
    _song, _app, dispatch = env
    params = {"track": 0, "scene": 0, "length_beats": 4, "notes": []}
    params[key] = bad if value == "outside" else value
    with pytest.raises(ValueError, match=key):
        dispatch(method, params)


def test_create_get_launch_and_stop_clip(env):
    song, _app, dispatch = env
    params = {"track": 0, "scene": 1, "length_beats": 1024}
    assert dispatch("create_clip", params) == {
        "name": "MIDI clip", "length": 1024, "is_playing": False, "looping": True
    }
    clip = song.tracks[0].clip_slots[1].clip
    assert dispatch("get_clip", params)["length"] == clip.length
    assert dispatch("fire_clip", params)["is_playing"] is clip.is_playing is True
    assert dispatch("stop_clip", params)["is_playing"] is clip.is_playing is False
    with pytest.raises(ValueError, match="occupied"):
        dispatch("create_clip", params)
    assert song.tracks[0].clip_slots[1].clip is clip


@pytest.mark.parametrize("length", [0, -1, 1024.1, True, "4", None, float("nan"), float("inf")])
def test_create_clip_bad_length(env, length):
    song, _app, dispatch = env
    with pytest.raises(ValueError, match="length_beats"):
        dispatch("create_clip", {"track": 0, "scene": 0, "length_beats": length})
    assert not song.tracks[0].clip_slots[0].has_clip


def test_create_clip_rejects_audio_track(env):
    song, _app, dispatch = env
    with pytest.raises(ValueError, match="MIDI track"):
        dispatch("create_clip", {"track": 2, "scene": 0, "length_beats": 4})
    assert not song.tracks[2].clip_slots[0].has_clip


def test_fractional_clip_length(env):
    _song, _app, dispatch = env
    assert dispatch("create_clip", {"track": 0, "scene": 0, "length_beats": 0.25})[
        "length"
    ] == 0.25


@pytest.mark.parametrize("method", ["get_clip", "get_notes", "add_notes", "fire_clip", "stop_clip"])
def test_empty_slot(env, method):
    _song, _app, dispatch = env
    with pytest.raises(ValueError, match="empty"):
        dispatch(method, {"track": 0, "scene": 0, "notes": []})


def test_missing_slot(env):
    song, _app, dispatch = env
    song.tracks[0].clip_slots = []
    with pytest.raises(ValueError, match="no clip slot"):
        dispatch("get_clip", {"track": 0, "scene": 0})


def test_legacy_notes_add_and_readback(clip_env):
    clip, _app, dispatch = clip_env
    params = {"track": 0, "scene": 0}
    assert dispatch("get_notes", params) == {"notes": [], "truncated": False}
    assert dispatch("add_notes", {**params, "notes": [note()]}) == {
        "notes": [note(mute=False)], "truncated": False
    }
    result = dispatch("add_notes", {**params, "notes": [note(pitch=127, mute=True)]})
    assert result["notes"] == [note(mute=False), note(pitch=127, mute=True)]
    assert len(clip.notes) == 2 and clip.writes == 2


def test_note_value_boundaries(clip_env):
    _clip, _app, dispatch = clip_env
    notes = [note(pitch=0, velocity=1, duration=0.25), note(pitch=127, velocity=127)]
    result = dispatch("add_notes", {"track": 0, "scene": 0, "notes": notes})
    assert result == {"notes": [{**n, "mute": False} for n in notes], "truncated": False}


def test_modern_notes_preferred_and_probed(env, monkeypatch):
    song, app, dispatch = env
    monkeypatch.setitem(sys.modules, "Live", SimpleNamespace(
        Clip=SimpleNamespace(MidiNoteSpecification=SimpleNamespace)
    ))
    clip = song.tracks[0].clip_slots[0].clip = ModernClip()
    result = dispatch("add_notes", {"track": 0, "scene": 0, "notes": [note()]})
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
    clip, _app, dispatch = clip_env
    result = dispatch("add_notes", {"track": 0, "scene": 0, "notes": [note()] * count})
    assert len(result["notes"]) == count
    assert result["truncated"] is False
    assert len(clip.notes) == count


@pytest.mark.parametrize("notes", [None, {}, (), [None], [note()] * (handlers.NOTE_LIMIT + 1)])
def test_bad_note_batches(clip_env, notes):
    clip, _app, dispatch = clip_env
    with pytest.raises(ValueError):
        dispatch("add_notes", {"track": 0, "scene": 0, "notes": notes})
    assert clip.writes == 0


@pytest.mark.parametrize("field,value", [
    ("pitch", -1), ("pitch", 128), ("pitch", True), ("pitch", 60.0), ("pitch", "60"),
    ("start_time", -0.1), ("start_time", True), ("start_time", float("nan")),
    ("duration", 0), ("duration", -1), ("duration", "1"), ("duration", float("inf")),
    ("velocity", 0), ("velocity", 128), ("velocity", False), ("velocity", 100.5),
    ("mute", 0), ("mute", "false"),
])
def test_note_fields_validate_entire_batch_before_write(clip_env, field, value):
    clip, _app, dispatch = clip_env
    with pytest.raises(ValueError, match=field):
        dispatch("add_notes", {"track": 0, "scene": 0, "notes": [note(), note(**{field: value})]})
    assert clip.writes == 0 and clip.notes == []


@pytest.mark.parametrize("field", ["pitch", "start_time", "duration", "velocity"])
def test_note_missing_fields(clip_env, field):
    clip, _app, dispatch = clip_env
    value = note()
    del value[field]
    with pytest.raises(ValueError, match=field):
        dispatch("add_notes", {"track": 0, "scene": 0, "notes": [value]})
    assert clip.writes == 0


@pytest.mark.parametrize("method", ["get_notes", "add_notes"])
def test_notes_reject_audio_clips(clip_env, method):
    clip, _app, dispatch = clip_env
    clip.is_midi_clip = False
    with pytest.raises(ValueError, match="MIDI clip"):
        dispatch(method, {"track": 0, "scene": 0, "notes": [note()]})
    assert clip.writes == 0


def test_missing_write_api_and_probe(env):
    song, app, dispatch = env
    clip = song.tracks[0].clip_slots[0].clip = SimpleNamespace(
        is_midi_clip=True, get_notes=lambda *args: (), length=4
    )
    with pytest.raises(ValueError, match="neither add_new_notes nor set_notes"):
        dispatch("add_notes", {"track": 0, "scene": 0, "notes": [note()]})
    caps = handlers.probe(song, app)
    assert caps["clip.add_new_notes"] is False
    assert caps["clip.set_notes"] is False
    assert caps["clip.get_notes"] is True
    del clip.get_notes
    for method in ("get_notes", "add_notes"):
        with pytest.raises(ValueError, match="neither get_notes_extended nor get_notes"):
            dispatch(method, {"track": 0, "scene": 0, "notes": [note()]})


@pytest.mark.parametrize("live", [None, SimpleNamespace(), SimpleNamespace(Clip=SimpleNamespace())])
def test_missing_note_specification(env, monkeypatch, live):
    song, app, dispatch = env
    monkeypatch.setitem(sys.modules, "Live", live)
    clip = song.tracks[0].clip_slots[0].clip = ModernClip()
    assert handlers.probe(song, app)["Live.Clip.MidiNoteSpecification"] is False
    with pytest.raises(ValueError, match="MidiNoteSpecification is unavailable"):
        dispatch("add_notes", {"track": 0, "scene": 0, "notes": [note()]})
    assert clip.writes == 0


def test_probe_empty_session(env):
    song, app, _dispatch = env
    song.tracks = []
    caps = handlers.probe(song, app)
    assert caps["clip.note_api_sample_count"] == 0
    assert caps["clip.add_new_notes"] is False


@pytest.mark.parametrize("method", ["delete_scene", "delete_clip", "delete_notes"])
def test_no_destructive_handlers(env, method):
    _song, _app, dispatch = env
    with pytest.raises(ValueError, match="unknown method"):
        dispatch(method, {})


@pytest.mark.parametrize("method,params", [
    ("play", {}), ("stop", {}), ("get_transport", {}),
    ("create_scene", {"index": -1}),
    ("set_scene_name", {"scene": 0, "name": "Chorus"}),
    ("fire_scene", {"scene": 0}),
    ("create_clip", {"track": 0, "scene": 1, "length_beats": 4}),
    ("get_clip", {"track": 0, "scene": 1}),
    ("add_notes", {"track": 0, "scene": 1, "notes": [note()]}),
    ("get_notes", {"track": 0, "scene": 1}),
    ("fire_clip", {"track": 0, "scene": 1}),
    ("stop_clip", {"track": 0, "scene": 1}),
])
def test_mcp_tools_registered_and_forward_readbacks(monkeypatch, method, params):
    from abletonlivemcp import server

    calls = []
    readback = {"actual": "readback"}

    def call(name, arguments=None):
        calls.append((name, arguments or {}))
        return readback

    monkeypatch.setattr(server._bridge, "call", call)
    monkeypatch.setattr(server.time, "sleep", lambda _s: None)
    names = {tool.name for tool in asyncio.run(server.mcp.list_tools())}
    assert f"live_{method}" in names
    assert getattr(server, f"live_{method}")(**params) is readback
    # Play/stop/launch re-read the real state after Live applies them (see test_server_settle).
    follow_up = {"play": "get_transport", "stop": "get_transport"}.get(
        method, "get_clip" if method in ("fire_clip", "stop_clip") else None
    )
    expected = [(method, params)]
    if follow_up:
        expected.append((follow_up, {} if follow_up == "get_transport" else params))
    assert calls == expected


def test_probe_slot_sampling_is_bounded(env, monkeypatch):
    song, app, _dispatch = env
    monkeypatch.setattr(handlers, "LIST_LIMIT", 1)
    song.tracks[0].clip_slots[1].clip = ModernClip()
    caps = handlers.probe(song, app)
    assert caps["clip.note_api_sample_count"] == 0
    assert caps["clip.add_new_notes"] is False
