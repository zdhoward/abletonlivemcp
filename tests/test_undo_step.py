"""T-006: every write dispatch is one undo step; reads, refusals and probes are not wrapped."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from AbletonLiveMCP.handlers import make_dispatch  # noqa: E402
from AbletonLiveMCP.safety import Safety  # noqa: E402


class Track:
    def __init__(self, name):
        self.name, self.color_index, self.has_midi_input, self.devices = name, 0, True, []


class View:
    selected_track = None


class Song:
    tempo = 120.0
    is_playing = False
    signature_numerator = signature_denominator = 4
    return_tracks = []
    scenes = []

    def __init__(self):
        self.tracks, self.view, self.log = [Track("A"), Track("B")], View(), []

    def begin_undo_step(self):
        self.log.append("begin")

    def end_undo_step(self):
        self.log.append("end")


class BareSong(Song):
    begin_undo_step = end_undo_step = None  # an older Live without the API


def dispatcher(song):
    return make_dispatch(lambda: song, object(), Safety(lambda: song, policy=lambda: False))


def test_write_is_one_undo_step_and_reads_are_not():
    song = Song()
    d = dispatcher(song)
    ref = d("tracks", {})[0]["ref"]
    assert song.log == []  # a read opens no step
    assert d("set_track_name", {"track": ref, "name": "X"}) == {"name": "X", "undo_steps": 1}
    assert song.log == ["begin", "end"]
    gen = d("session_info", {})["generation"]
    assert d("set_tempo", {"bpm": 90, "generation": gen})["undo_steps"] == 1
    assert song.log == ["begin", "end"] * 2


def test_refusals_and_failures_close_the_step_and_claim_nothing():
    song = Song()
    d = dispatcher(song)
    stale = d("set_tempo", {"bpm": 90, "generation": -1})  # refused by the gate, before any step
    assert stale["refused"] is True and "undo_steps" not in stale and song.log == []
    ref = d("tracks", {})[0]["ref"]
    with pytest.raises(ValueError):  # handler fails mid-write: the step is still closed
        d("set_track_color", {"track": ref, "color_index": "not a number"})
    assert song.log == ["begin", "end"]


def test_song_without_undo_api_runs_ungrouped():
    song = BareSong()
    d = dispatcher(song)
    ref = d("tracks", {})[0]["ref"]
    assert d("set_track_name", {"track": ref, "name": "Y"}) == {"name": "Y"}
    assert song.tracks[0].name == "Y"


def test_probe_run_manages_its_own_undo_steps(monkeypatch):
    song = Song()
    d = dispatcher(song)
    monkeypatch.setattr(Safety, "dev_probes_enabled", lambda self: False)
    gen = d("session_info", {})["generation"]
    # passes the gate, then the handler refuses (dev probes off); no outer step was opened
    reply = d("probe_run", {"name": "P-03", "generation": gen})
    assert reply["code"] == "dev_probes_disabled" and song.log == []
