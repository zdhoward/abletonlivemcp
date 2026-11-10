import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from AbletonLiveMCP.handlers import make_dispatch  # noqa: E402

from AbletonLiveMCP import handlers  # noqa: E402


class Item:
    def __init__(self, name, children=None, loadable=False):
        self.name = name
        self.children = children or []
        self.is_folder = bool(children)
        self.is_loadable = loadable
        self.uri = f"uri:{name}"


class Param:
    def __init__(self, name, value, lo, hi, enabled=True):
        self.name, self.value, self.min, self.max = name, value, lo, hi
        self.is_quantized = False
        self.is_enabled = enabled

    def str_for_value(self, v):
        return f"{v:.2f}"


class Dev:
    name = "EQ Eight"
    class_name = "Eq8"

    def __init__(self):
        self.parameters = [
            Param("Gain", 0.5, 0.0, 1.0),
            Param("Macro", 0.0, 0.0, 1.0, enabled=False),
        ]


class Track:
    def __init__(self, name):
        self.name = name
        self.color_index = 0
        self.has_midi_input = True
        self.devices = [Dev()]


class View:
    selected_track = None


class Song:
    tempo = 120.0
    is_playing = False
    signature_numerator = signature_denominator = 4
    return_tracks = []
    scenes = []

    def __init__(self):
        self.tracks = [Track("A"), Track("B")]
        self.view = View()

    def create_midi_track(self, i):
        self.tracks.append(Track("new midi"))

    def create_audio_track(self, i):
        self.tracks.append(Track("new audio"))


class Browser:
    def __init__(self):
        self.loaded = None
        self.audio_effects = Item(
            "root",
            [
                Item("Reverb", loadable=True),
                Item(
                    "Dynamics",
                    [Item("Compressor", loadable=True), Item("Limiter", loadable=True)],
                ),
            ],
        )

    def load_item(self, item):
        self.loaded = item


class App:
    def __init__(self):
        self.browser = Browser()


@pytest.fixture
def env():
    song, app = Song(), App()
    return song, app, make_dispatch(song, app)


def test_browser_roots_only_those_present(env):
    _s, _a, d = env
    assert d("browser_roots", {}) == ["audio_effects"]


def test_browser_list_and_path(env):
    _s, _a, d = env
    names = [i["name"] for i in d("browser_list", {"root": "audio_effects"})["items"]]
    assert names == ["Reverb", "Dynamics"]
    inner = d("browser_list", {"root": "audio_effects", "path": ["Dynamics"]})["items"]
    assert [i["name"] for i in inner] == ["Compressor", "Limiter"]
    with pytest.raises(ValueError):
        d("browser_list", {"root": "audio_effects", "path": ["Nope"]})
    with pytest.raises(ValueError):
        d("browser_list", {"root": "bogus"})


def test_browser_search_returns_paths(env):
    _s, _a, d = env
    r = d("browser_search", {"root": "audio_effects", "query": "compr"})
    assert r["results"][0]["path"] == ["Dynamics", "Compressor"]
    assert r["budget_exhausted"] is False


def test_browser_search_budget_is_bounded(env, monkeypatch):
    _s, _a, d = env
    monkeypatch.setattr(handlers, "WALK_BUDGET", 2)
    assert d("browser_search", {"root": "audio_effects", "query": "zzz"})["budget_exhausted"]


def test_load_item_selects_track_and_loads(env):
    song, app, d = env
    r = d("load_item", {"track": 1, "root": "audio_effects", "path": ["Dynamics", "Limiter"]})
    assert song.view.selected_track is song.tracks[1]
    assert app.browser.loaded.name == "Limiter" and r["loaded"] == "Limiter"


def test_load_item_rejects_folder_and_bad_track(env):
    _s, app, d = env
    with pytest.raises(ValueError):
        d("load_item", {"track": 0, "root": "audio_effects", "path": ["Dynamics"]})
    with pytest.raises(ValueError):
        d("load_item", {"track": 9, "root": "audio_effects", "path": ["Reverb"]})
    assert app.browser.loaded is None


def test_set_parameter_readback_and_guards(env):
    song, _a, d = env
    r = d("set_device_parameter", {"track": 0, "device": 0, "parameter": 0, "value": 0.75})
    assert r["value"] == 0.75 and song.tracks[0].devices[0].parameters[0].value == 0.75
    with pytest.raises(ValueError, match="outside"):
        d("set_device_parameter", {"track": 0, "device": 0, "parameter": 0, "value": 2})
    with pytest.raises(ValueError, match="not enabled"):
        d("set_device_parameter", {"track": 0, "device": 0, "parameter": 1, "value": 0.5})
    with pytest.raises(ValueError):
        d("set_device_parameter", {"track": 0, "device": 0, "parameter": True, "value": 0.5})


def test_create_track_name_color_tempo(env):
    song, _a, d = env
    assert d("create_track", {"kind": "midi"})["track_count"] == 3
    with pytest.raises(ValueError):
        d("create_track", {"kind": "video"})
    assert d("set_track_name", {"track": 0, "name": "Lead"})["name"] == "Lead"
    assert d("set_track_color", {"track": 0, "color_index": 5})["color_index"] == 5
    assert d("set_tempo", {"bpm": 128})["tempo"] == 128
    with pytest.raises(ValueError):
        d("set_tempo", {"bpm": 5})
