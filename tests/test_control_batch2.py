"""Batch 2 (session, tracks, scenes, recording, song extras, view): one small fake-Live test per
feature, through the real bridge gate (``make_dispatch``) and the host tool functions."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from AbletonLiveMCP import dom_tracks  # noqa: E402
from AbletonLiveMCP.handlers import make_dispatch  # noqa: E402
from AbletonLiveMCP.safety import Safety  # noqa: E402

# ---- fake Live -----------------------------------------------------------------------------


class Param:
    """A volume-like parameter whose display is a monotonic dB curve."""

    def __init__(self, value=0.85, lo=0.0, hi=1.0, db=True):
        self.value, self.min, self.max, self.db = value, lo, hi, db

    def str_for_value(self, v):
        if not self.db:
            return f"{v:.2f}"
        return "-inf dB" if v <= 0 else f"{(v - 0.85) * 80:.2f} dB"  # 0.85 -> 0 dB, 1 -> +12


class Mixer:
    def __init__(self, master=False):
        self.volume, self.panning = Param(), Param(0.0, -1.0, 1.0, db=False)
        self.sends = [Param(0.0)]
        self.track_activator = Param(1.0, 0.0, 1.0, db=False)
        self.crossfade_assign = 1
        if master:
            self.crossfader = Param(0.0, -1.0, 1.0, db=False)
            self.cue_volume = Param()


class RoutingType:
    def __init__(self, name):
        self.display_name = name


class Slot:
    def __init__(self):
        self.has_clip, self.clip = False, None
        self.is_playing = self.is_triggered = False
        self.fired = 0

    def fire(self):
        self.fired += 1
        self.is_triggered = True

    def stop(self):
        self.is_triggered = False


class Track:
    def __init__(self, name, scenes=2, midi=True):
        self.name, self.color_index, self.has_midi_input = name, 0, midi
        self.mute = self.solo = self.arm = False
        self.can_be_armed, self.is_foldable, self.fold_state = True, False, 0
        self.current_monitoring_state = 1
        self.devices, self.mixer_device = [], Mixer()
        self.clip_slots = [Slot() for _ in range(scenes)]
        self.group_track = None
        self.available_output_routing_types = [RoutingType("Master"), RoutingType("Sends Only")]
        self.output_routing_type = self.available_output_routing_types[0]
        self.available_output_routing_channels = [RoutingType("Track In")]
        self.output_routing_channel = self.available_output_routing_channels[0]
        self.stopped = 0

    def stop_all_clips(self):
        self.stopped += 1


class Scene:
    def __init__(self, name):
        self.name, self.color_index, self.is_triggered = name, 0, False
        self.tempo, self.tempo_enabled = 120.0, False
        self.time_signature_numerator = self.time_signature_denominator = 4
        self.time_signature_enabled = False

    def fire(self):
        self.is_triggered = True


class Groove:
    def __init__(self, name):
        self.name = name
        self.timing_amount = self.quantization_amount = 0.0
        self.random_amount = self.velocity_amount = 0.0


class SongView:
    def __init__(self):
        self.selected_track = self.selected_scene = self.detail_clip = None
        self.highlighted_clip_slot = None


class Song:
    def __init__(self):
        self.tempo, self.is_playing, self.current_song_time = 120.0, False, 0.0
        self.signature_numerator = self.signature_denominator = 4
        self.metronome, self.loop, self.loop_start, self.loop_length = False, False, 0.0, 16.0
        self.punch_in = self.punch_out = False
        self.root_note, self.scale_name, self.scale_mode = 0, "Major", False
        self.groove_amount, self.swing_amount = 1.0, 0.0
        self.clip_trigger_quantization, self.midi_recording_quantization = 4, 0
        self.is_ableton_link_enabled = self.is_ableton_link_start_stop_sync_enabled = False
        self.count_in_duration = 0
        self.session_record = self.record_mode = self.arrangement_overdub = False
        self.groove_pool = type("Pool", (), {"grooves": [Groove("Swing 16")]})()
        self.tracks = [Track("A"), Track("B")]
        self.return_tracks = [Track("Rev", midi=False)]
        self.master_track = Track("Master", midi=False)
        self.master_track.mixer_device = Mixer(master=True)
        self.scenes = [Scene("Intro"), Scene("Verse")]
        self.cue_points = []
        self.view = SongView()
        self.history, self.redone = [], []

    # undo
    @property
    def can_undo(self):
        return bool(self.history)

    @property
    def can_redo(self):
        return bool(self.redone)

    def undo(self):
        self.redone.append(self.history.pop())

    def redo(self):
        self.history.append(self.redone.pop())

    # transport
    def start_playing(self):
        self.is_playing = True

    def stop_playing(self):
        self.is_playing = False

    def jump_by(self, beats):
        self.current_song_time += beats

    # structure
    def create_midi_track(self, i):
        self.tracks.insert(len(self.tracks) if i == -1 else i, Track("new midi"))

    def create_audio_track(self, i):
        self.tracks.insert(len(self.tracks) if i == -1 else i, Track("new audio", midi=False))

    def create_return_track(self):
        self.return_tracks.append(Track("new return", midi=False))

    def delete_track(self, i):
        del self.tracks[i]

    def delete_return_track(self, i):
        del self.return_tracks[i]

    def duplicate_track(self, i):
        self.tracks.insert(i + 1, Track(self.tracks[i].name + " copy"))

    def create_scene(self, i):
        scene = Scene("")
        self.scenes.insert(len(self.scenes) if i == -1 else i, scene)
        for t in self.tracks:
            t.clip_slots.append(Slot())

    def delete_scene(self, i):
        del self.scenes[i]

    def duplicate_scene(self, i):
        self.scenes.insert(i + 1, Scene(self.scenes[i].name + " copy"))


class AppView:
    def __init__(self):
        self.visible = {"Session"}
        self.focused_document_view = "Session"

    def is_view_visible(self, name):
        return name in self.visible

    def show_view(self, name):
        self.visible.add(name)

    def hide_view(self, name):
        self.visible.discard(name)


class Item:
    def __init__(self, name, children=(), loadable=False):
        self.name, self.children = name, list(children)
        self.is_folder, self.is_loadable = bool(children), loadable


class Browser:
    def __init__(self):
        self.samples = Item("root", [Item("Kick.wav", loadable=True)])
        self.previewed = None

    def preview_item(self, item):
        self.previewed = item

    def stop_preview(self):
        self.previewed = None


class App:
    def __init__(self):
        self.view, self.browser = AppView(), Browser()

    def get_major_version(self):
        return 12

    def get_minor_version(self):
        return 2

    def get_bugfix_version(self):
        return 0

    def get_build_id(self):
        return "abc123"

    def get_variant(self):
        return "Suite"


@pytest.fixture
def live():
    song, app = Song(), App()
    d = make_dispatch(lambda: song, app, Safety(lambda: song, policy=lambda: False))
    gen = d("session_info", {})["generation"]
    return song, app, d, gen


def refs(d, *selectors):
    return [r["ref"] for r in d("ref_issue", {"targets": list(selectors)})["refs"]]


# ---- session -------------------------------------------------------------------------------


def test_hello_reports_build_variant_and_capabilities(live):
    _s, _a, d, _g = live
    out = d("hello", {})
    assert out["build_id"] == "abc123" and out["variant"] == "Suite"
    assert out["read_only"] is False and out["dev_probes"] is False
    assert out["capability_report"]["song.count_in"]["state"] == "unsupported"
    assert out["capability_report"]["track.routing"]["state"] == "unverified"


def test_get_session_sections(live):
    song, _a, d, _g = live
    out = d("get_session", {"include": ["loop", "groove", "link", "extras"]})
    assert out["loop"] == {"on": False, "start": 0.0, "length": 16.0}
    assert out["grooves"][0]["name"] == "Swing 16"
    assert out["link"] == {"link_enabled": False, "link_start_stop_sync": False}
    assert out["count_in_duration"] == 0 and "scale" not in out


def test_set_session_validates_all_before_writing(live):
    song, _a, d, g = live
    with pytest.raises(ValueError):
        d("set_session", {"generation": g, "tempo": 130, "signature": [4, 3]})
    assert song.tempo == 120.0  # nothing applied
    out = d(
        "set_session",
        {
            "generation": g,
            "tempo": 128.0,
            "loop": {"on": True, "length": 8},
            "punch": {"in": True},
            "scale": {"root_note": 9, "scale_name": "Minor"},
            "link_enabled": True,
            "grooves": [{"index": 0, "timing_amount": 50}],
        },
    )
    assert out["status"] == "complete" and out["mismatched"] == []
    assert song.loop and song.loop_length == 8 and song.punch_in and song.root_note == 9
    assert song.is_ableton_link_enabled and song.groove_pool.grooves[0].timing_amount == 50


def test_set_session_refuses_count_in_and_tuning(live):
    song, _a, d, g = live
    for field in ("count_in", "tuning"):
        out = d("set_session", {"generation": g, field: 1, "tempo": 99})
        assert out["code"] == "unsupported" and song.tempo == 120.0


def test_transport_jump_and_unverified_flag(live):
    song, _a, d, g = live
    out = d("transport", {"generation": g, "action": "jump_by", "beats": 4})
    assert song.current_song_time == 4 and out["unverified"] == ["transport.jump_by"]
    out = d("transport", {"generation": g, "action": "next_cue"})
    assert out["code"] == "unsupported"  # the fake Song has no jump_to_next_cue


def test_undo_and_redo_steps(live):
    song, _a, d, g = live
    song.history = [1, 2]
    out = d("undo", {"generation": g, "action": "undo", "steps": 5})
    assert out["done"] == 2 and out["status"] == "partial" and song.can_redo
    out = d("undo", {"generation": g, "action": "redo"})
    assert out["done"] == 1
    song.history, song.redone = [], []
    assert d("undo", {"generation": g})["code"] == "nothing_to_undo"


# ---- tracks and mixer ----------------------------------------------------------------------


def test_get_tracks_includes_returns_master_and_routing(live):
    _s, _a, d, _g = live
    out = d("get_tracks", {"include": ["mixer", "routing"]})
    sels = [r["track"] for r in out["tracks"]]
    assert sels == [0, 1, "return:0", "master"]
    assert out["tracks"][0]["output_routing"]["available"] == ["Master", "Sends Only"]
    assert "crossfader" in out["tracks"][3]["mixer"]


def test_create_tracks_batch(live):
    song, _a, d, g = live
    out = d(
        "create_tracks",
        {
            "generation": g,
            "tracks": [
                {"kind": "audio", "index": 0, "name": "Vox"},
                {"kind": "return", "name": "Dly"},
            ],
        },
    )
    assert [i["track"] for i in out["applied"]] == [0, "return:1"]
    assert song.tracks[0].name == "Vox" and song.return_tracks[1].name == "Dly"


def test_set_tracks_fields_and_routing_allowlist(live):
    song, _a, d, _g = live
    (ref,) = refs(d, {"kind": "track", "track": 0})
    bad = {"kind": "track", "ref": ref, "output_routing": {"type": "Nowhere"}}
    with pytest.raises(ValueError):
        d("set_tracks", {"targets": [bad]})
    item = {
        "kind": "track",
        "ref": ref,
        "expect_name": "A",
        "name": "Lead",
        "monitoring": "in",
        "output_routing": {"type": "Sends Only"},
    }
    out = d("set_tracks", {"targets": [item]})
    assert out["status"] == "complete"
    assert song.tracks[0].name == "Lead" and song.tracks[0].current_monitoring_state == 0
    assert song.tracks[0].output_routing_type.display_name == "Sends Only"


def test_set_tracks_expect_name_mismatch(live):
    song, _a, d, _g = live
    (ref,) = refs(d, {"kind": "track", "track": 1})
    out = d(
        "set_tracks", {"targets": [{"kind": "track", "ref": ref, "expect_name": "X", "mute": True}]}
    )
    assert out["code"] == "name_mismatch" and not song.tracks[1].mute


def test_db_bisection_within_tolerance():
    param, budget = Param(), dom_tracks._Budget()
    value = dom_tracks.db_to_value(param, -6.0, budget, "t")
    shown = dom_tracks.parse_db(param.str_for_value(value))
    assert abs(shown - -6.0) <= dom_tracks.DB_TOLERANCE
    with pytest.raises(ValueError):
        dom_tracks.db_to_value(param, 20.0, budget, "t")


def test_set_mixer_db_pan_send_and_master(live):
    song, _a, d, _g = live
    track_ref, master_ref = refs(
        d, {"kind": "track", "track": 0}, {"kind": "master", "track": "master"}
    )
    out = d(
        "set_mixer",
        {
            "targets": [
                {"kind": "track", "ref": track_ref, "volume_db": -6, "pan": -0.5, "crossfade": "A",
                 "sends": [{"send": 0, "db": -12}]},
                {"kind": "master", "ref": master_ref, "crossfader": 0.25},
            ]
        },
    )  # fmt: skip
    assert out["status"] == "complete" and out["mismatched"] == []
    mixer = song.tracks[0].mixer_device
    assert mixer.panning.value == -0.5 and mixer.crossfade_assign == 0
    assert song.master_track.mixer_device.crossfader.value == 0.25


def test_delete_and_duplicate_tracks(live):
    song, _a, d, _g = live
    r0, r1 = refs(d, {"kind": "track", "track": 0}, {"kind": "return_track", "track": "return:0"})
    out = d(
        "delete_tracks",
        {"targets": [{"kind": "track", "ref": r0, "expect_name": "A"},
                     {"kind": "return_track", "ref": r1, "expect_name": "Rev"}]},
    )  # fmt: skip
    assert out["status"] == "complete" and [t.name for t in song.tracks] == ["B"]
    assert song.return_tracks == []
    (ref,) = refs(d, {"kind": "track", "track": 0})
    with pytest.raises(ValueError):  # the last regular track stays
        d("delete_tracks", {"targets": [{"kind": "track", "ref": ref}]})
    out = d("duplicate_tracks", {"targets": [{"kind": "track", "ref": ref}]})
    assert out["applied"][0]["track"] == 1 and song.tracks[1].name == "B copy"


# ---- scenes and launch ---------------------------------------------------------------------


def test_scenes_create_set_and_read(live):
    song, _a, d, g = live
    d("create_scenes", {"generation": g, "scenes": [{"name": "Out", "tempo": 90}]})
    assert song.scenes[2].name == "Out" and song.scenes[2].tempo_enabled
    (ref,) = refs(d, {"kind": "scene", "scene": 0})
    d("set_scenes", {"targets": [{"ref": ref, "expect_name": "Intro", "signature": [3, 4]}]})
    rows = d("get_scenes", {"scenes": [0, 2]})["scenes"]
    assert rows[0]["signature"] == [3, 4] and rows[1]["tempo"] == 90


def test_launch_and_state(live):
    song, _a, d, _g = live
    scene, track = refs(d, {"kind": "scene", "scene": 1}, {"kind": "track", "track": 1})
    d("launch", {"action": "fire", "targets": [{"kind": "scene", "ref": scene}]})
    d("launch", {"action": "stop", "targets": [{"kind": "track", "ref": track}]})
    assert song.scenes[1].is_triggered and song.tracks[1].stopped == 1
    with pytest.raises(ValueError):  # a track only stops
        d("launch", {"action": "fire", "targets": [{"kind": "track", "ref": track}]})
    state = d("launch_state", {"targets": [{"kind": "scene", "scene": 1}]})["targets"]
    assert state[0]["is_triggered"] is True


def test_delete_and_duplicate_scenes(live):
    song, _a, d, _g = live
    (ref,) = refs(d, {"kind": "scene", "scene": 0})
    d("duplicate_scenes", {"targets": [{"ref": ref}]})
    assert [s.name for s in song.scenes] == ["Intro", "Intro copy", "Verse"]
    (ref,) = refs(d, {"kind": "scene", "scene": 2})
    out = d("delete_scenes", {"targets": [{"ref": ref, "expect_name": "Verse"}]})
    assert out["applied"][0]["name"] == "Verse" and len(song.scenes) == 2


# ---- recording and view --------------------------------------------------------------------


def test_record_is_bounded_and_restores(live):
    song, _a, d, g = live
    with pytest.raises(ValueError):  # turning on needs a length
        d("record", {"generation": g, "action": "session_record", "value": True})
    with pytest.raises(ValueError):  # 64 beats at 120 BPM is 32 s
        d("record", {"generation": g, "action": "session_record", "value": True, "length": 64})
    out = d("record", {"generation": g, "action": "session_record", "value": True, "length": 2})
    assert song.session_record and song.is_playing and out["unverified"] == ["session_record"]
    song.current_song_time = 3.0
    d.operations.tick()
    assert not song.session_record and not song.is_playing


def test_a_second_bounded_recording_is_refused_while_one_runs(live):
    """R8: an overlap would snapshot the first one's switch as "before" and leave it on."""
    song, _a, d, g = live
    song.current_song_time = 0.0
    first = {"generation": g, "action": "arrangement_record", "value": True, "length": 2}
    d("record", first)
    out = d("record", {**first, "action": "session_record"})
    assert out["code"] == "recording_active" and not song.session_record
    song.current_song_time = 3.0
    d.operations.tick()
    assert not song.record_mode and not song.is_playing
    assert d("record", {**first, "action": "session_record"})["operation"]["state"] == "pending"


def test_view_show_select_and_audition(live):
    song, app, d, g = live
    out = d("view", {"generation": g, "action": "show", "view": "Browser"})
    assert out["visible"]["Browser"] is True
    (ref,) = refs(d, {"kind": "scene", "scene": 1})
    out = d("select", {"targets": [{"kind": "scene", "ref": ref}]})
    assert out["selected"] and song.view.selected_scene is song.scenes[1]
    d("view", {"generation": g, "action": "audition", "root": "samples", "path": ["Kick.wav"]})
    assert app.browser.previewed.name == "Kick.wav"
    out = d("view", {"generation": g, "action": "zoom", "view": "Arranger", "direction": "up"})
    assert out["code"] == "unsupported"  # the fake has no zoom_view


# ---- host facades --------------------------------------------------------------------------


def test_live_delete_routes_children_first_and_needs_expect_name(monkeypatch):
    from abletonlivemcp.models_control import StructTarget
    from abletonlivemcp.tools import tracks as tools

    calls = []

    def fake_call(method, params=None):
        calls.append((method, params))
        if method == "ref_issue":
            return {"refs": [{"kind": t["kind"], "ref": f"r{i}", "name": "n"}
                             for i, t in enumerate(params["targets"])]}  # fmt: skip
        return {"status": "complete"}

    monkeypatch.setattr("abletonlivemcp.server._call", fake_call)
    monkeypatch.setattr(tools, "_call", fake_call)
    targets = [
        StructTarget(kind="track", track=0, expect_name="n"),
        StructTarget(kind="scene", scene=1, expect_name="n"),
    ]
    with pytest.raises(ValueError):
        tools.live_delete.__wrapped__([StructTarget(kind="scene", scene=0)])
    tools.live_delete.__wrapped__(targets)
    assert [m for m, _ in calls if m != "ref_issue"] == ["delete_scenes", "delete_tracks"]
    with pytest.raises(ValueError, match="device"):  # server.Refusal("unsupported", ...)
        tools.live_duplicate.__wrapped__([StructTarget(kind="device", track=0, path=[0])])
