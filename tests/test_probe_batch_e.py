"""P-24 and P-27 probe logic against fakes (no Live needed): verdict rules and the run paths."""

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "remote_script"))

from AbletonLiveMCP import dom_probe, probe_p24, probe_p27  # noqa: E402

# ---- P-24 -------------------------------------------------------------------------------------


def test_p24_verdict_rule():
    v = probe_p24.verdict_for
    ok = {"selected_track": "ok", "selected_scene": "ok", "select_device": "ok"}
    assert v(ok, ["select_device"]) == "gated"
    assert v(ok, []) == "go"
    assert v({**ok, "selected_chain": "untested", "detail_clip": "absent"}, []) == "go"
    assert v({**ok, "selected_chain": "fail"}, []) == "go-with-limits"
    assert v({**ok, "select_device": "untested"}, []) == "go-with-limits"
    assert v({**ok, "selected_track": "fail"}, []) == "no-go"


class Slot:
    def __init__(self):
        self.clip = None

    def create_clip(self, _length):
        self.clip = object()


class RackView:
    selected_chain = None
    selected_drum_pad = None


class Rack:
    can_have_chains = True
    can_have_drum_pads = False

    def __init__(self):
        self.chains = [object(), object()]
        self.drum_pads = []
        self.view = RackView()


class TrackView:
    selected_device = None


class Track:
    def __init__(self, devices=()):
        self.devices = list(devices)
        self.clip_slots = [Slot()]
        self.view = TrackView()


class SongView:
    selected_track = None
    selected_scene = None
    detail_clip = None
    selected_chain = None

    def __init__(self, song, writable=True):
        self._song, self._writable = song, writable

    def select_device(self, device):
        for track in self._song.tracks:
            if device in track.devices:
                track.view.selected_device = device
                self.selected_track = track


class FrozenView(SongView):
    """selected_track silently ignores writes (a no-go Live)."""

    @property
    def selected_track(self):
        return None

    @selected_track.setter
    def selected_track(self, _value):
        pass


class Song:
    def __init__(self, frozen=False, with_rack=True):
        self.tracks = [Track([Rack()] if with_rack else [])]
        self.return_tracks = []
        self.master_track = Track()
        self.scenes = []
        self.view = (FrozenView if frozen else SongView)(self)

    def create_midi_track(self, _index):
        self.tracks.append(Track())

    def create_scene(self, _index):
        self.scenes.append(object())


def _run24(song):
    scratch = dom_probe.Scratch(song)
    return probe_p24.run(types.SimpleNamespace(song=song), scratch), song


def test_p24_go_and_restores_selection():
    song = Song()
    original = song.tracks[0]
    song.view.selected_track = original
    result, _ = _run24(song)
    assert result["verdict"] == "go"
    assert result["items"]["selected_track"] == "ok"
    assert result["items"]["selected_chain"] == "ok"
    assert result["items"]["selected_drum_pad"] == "untested"
    assert song.view.selected_track is original  # restored in the finally


def test_p24_no_rack_is_untested_not_fail():
    result, _ = _run24(Song(with_rack=False))
    assert result["items"]["select_device"] == "untested"
    assert result["verdict"] == "go-with-limits"


def test_p24_selection_ignored_is_no_go():
    result, _ = _run24(Song(frozen=True))
    assert result["items"]["selected_track"] == "fail"
    assert result["verdict"] == "no-go"


def test_p24_absent_api_is_gated():
    song = Song()
    song.view = types.SimpleNamespace()  # no selected_track / select_device
    result, _ = _run24(song)
    assert result["verdict"] == "gated"
    assert result["absent_members"] == ["selected_track", "select_device"]


# ---- P-27 -------------------------------------------------------------------------------------


def test_p27_verdict_rule():
    v = probe_p27.verdict_for
    good = {"display_write_volume": True, **{k: True for k in probe_p27.EXTRA}}
    assert v(["display_value"], good) == "gated"
    assert v([], good) == "go"
    assert v([], {**good, "value_items_quantized": None}) == "go"
    assert v([], {**good, "value_items_quantized": False}) == "go-with-limits"
    assert v([], {**good, "display_write_volume": False}) == "no-go"


class Param:
    """A DeviceParameter fake: ``display_value`` maps linearly onto ``value``."""

    quantized = False

    def __init__(self, lo, hi, default, display_ok=True):
        self.min, self.max, self._default = lo, hi, default
        self.value = default
        self._display_ok = display_ok

    automation_state = 0  # class level, like a Live property

    @property
    def display_value(self):
        return self.value

    @display_value.setter
    def display_value(self, v):
        if self._display_ok:
            self.value = v

    @property
    def is_quantized(self):
        return self.quantized

    @property
    def value_items(self):
        if not self.quantized:
            raise RuntimeError("not quantized")
        return ["Off", "On"]

    short_value_items = value_items

    @property
    def default_value(self):
        if self.quantized:
            raise RuntimeError("quantized")
        return self._default

    def str_for_value(self, v):
        return str(v)

    def re_enable_automation(self):
        pass


class Activator(Param):
    quantized = True


class Mixer:
    def __init__(self, display_ok):
        self.volume = Param(-70.0, 6.0, 0.0, display_ok)
        self.panning = Param(-50.0, 50.0, 0.0, display_ok)
        self.track_activator = Activator(0, 1, 1)


class Song27:
    def __init__(self, display_ok=True):
        self.tracks, self._ok = [], display_ok

    def create_midi_track(self, _index):
        self.tracks.append(types.SimpleNamespace(mixer_device=Mixer(self._ok)))


def _run27(**kw):
    song = Song27(**kw)
    return probe_p27.run(types.SimpleNamespace(song=song), dom_probe.Scratch(song))


def test_p27_go():
    result = _run27()
    assert result["verdict"] == "go"
    assert result["checks"]["display_write_volume"] is True
    assert result["detail"]["value_items_unquantized"]["raises"] is True
    assert result["detail"]["value_items_quantized"]["items"] == ["Off", "On"]


def test_p27_display_write_ignored_is_no_go():
    assert _run27(display_ok=False)["verdict"] == "no-go"


def test_p27_missing_member_is_gated():
    song = Song27()
    song.create_midi_track(-1)
    mixer = song.tracks[0].mixer_device

    class NoDisplay:  # lacks display_value at class level
        min = max = 0

    mixer.volume = NoDisplay()
    scratch = dom_probe.Scratch(types.SimpleNamespace(tracks=[], create_midi_track=lambda i: None))
    scratch.midi_track = lambda: song.tracks[0]
    result = probe_p27.run(types.SimpleNamespace(song=song), scratch)
    assert result["verdict"] == "gated"
    assert "display_value" in result["missing_members"]
