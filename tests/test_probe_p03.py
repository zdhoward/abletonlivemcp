"""P-03 probe logic against a fake Song with a real undo stack (no Live needed)."""

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "remote_script"))

from AbletonLiveMCP import dom_probe, probe_p03  # noqa: E402


class Track:
    def __init__(self, song, name="t"):
        self._song, self._name = song, name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        old = self._name
        self._name = value
        self._song.record(lambda: setattr(self, "_name", old))


class Song:
    """Undo entries are closures; grouping can be switched off to model a no-go Live."""

    can_undo = True

    def __init__(self, group=True):
        self.tracks, self.stack, self.open, self.group = [], [], None, group

    def record(self, undo):
        if self.open is not None and self.group:
            self.open.append(undo)
        else:
            self.stack.append([undo])

    def begin_undo_step(self):
        self.open = []

    def end_undo_step(self):
        if self.open:
            self.stack.append(self.open)
        self.open = None

    def undo(self):
        for fn in reversed(self.stack.pop()):
            fn()

    def create_midi_track(self, _index):
        track = Track(self)
        self.tracks.append(track)
        self.record(lambda: self.tracks.remove(track))


def _run(group):
    song = Song(group)
    scratch = dom_probe.Scratch(song)
    ctx = types.SimpleNamespace(song=song)
    return probe_p03.run(ctx, scratch), song


def test_one_undo_reverts_the_three_writes_and_only_them():
    result, _ = _run(group=True)
    assert result["verdict"] == "go"
    assert result["phase_a_rename"]["reverted"] == 3
    assert result["marker"]["kept"] is True
    assert result["phase_b_create"]["removed_by_one_undo"] == 3


def test_ungrouped_batch_is_no_go():
    result, _ = _run(group=False)
    assert result["verdict"] == "no-go"
    assert result["phase_a_rename"]["reverted"] == 1


def test_verdict_rule():
    v = probe_p03.verdict_for
    assert v(3, True, True, 3, 3) == "go"
    assert v(3, True, True, 0, 3) == "go-with-limits"
    assert v(3, True, False, 3, 3) == "no-go"
    assert v(2, True, True, 3, 3) == "no-go"
