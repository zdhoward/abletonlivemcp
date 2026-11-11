"""T-003 dev probes: fixed table, fail-closed classification, dev_probes, lease, scratch."""

import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "remote_script"))

from AbletonLiveMCP import dom_probe, probe_p02, safety  # noqa: E402
from AbletonLiveMCP.handlers import make_dispatch  # noqa: E402
from AbletonLiveMCP.safety import Safety  # noqa: E402

_spec = importlib.util.spec_from_file_location("live_probe_run", ROOT / "scripts/live_probe_run.py")
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)


class Song:
    def __init__(self):
        self.tracks, self.scenes, self.return_tracks = [object()], [object()], []

    def create_midi_track(self, _index):
        self.tracks.append(object())

    def delete_track(self, index):
        del self.tracks[index]


class App:
    def get_major_version(self):
        return 12

    def get_minor_version(self):
        return 2

    def get_bugfix_version(self):
        return 5


def dispatcher(dev=True, writable=True):
    song = Song()
    gate = Safety(lambda: song, policy=lambda: not writable, dev_probes=lambda: dev)
    return song, make_dispatch(lambda: song, App(), gate)


def test_fixed_table_is_classified_and_never_an_mcp_tool():
    assert len(dom_probe.PROBES) == 25 and "P-21" not in dom_probe.PROBES
    reads = {pid for pid, (_r, kind) in dom_probe.PROBES.items() if kind == "read"}
    assert reads == {"P-01", "P-23"}
    assert safety.CLASSIFICATION["probe_run"] == "write" and safety.TARGETS["probe_run"] == ()
    assert safety.CLASSIFICATION["probe_read"] == safety.CLASSIFICATION["probe_list"] == "read"
    server = (ROOT / "src/abletonlivemcp").rglob("*.py")
    assert not any("probe_run" in p.read_text(encoding="utf-8") for p in server)


def _mod(name, **attrs):
    module = types.ModuleType(f"AbletonLiveMCP.{name}")
    module.__dict__.update({"PROBE_ID": "P-90", "KIND": "write", "run": lambda c, s: {}, **attrs})
    return module


@pytest.mark.parametrize(
    "modules",
    [
        (probe_p02, _mod("probe_p02", PROBE_ID="P-02")),  # duplicate id
        (_mod("probe_p90", KIND="admin"),),  # unclassified
        (_mod("probe_p90", KIND=None),),
        (_mod("probe_p90", run=None),),
        (_mod("probe_p91"),),  # id does not match the file
        (_mod("probe_p90", PROBE_ID="X-90"),),
    ],
)
def test_bad_probe_tables_fail_closed(modules):
    with pytest.raises(dom_probe.ProbeTableError):
        dom_probe._table(modules)


def test_release_archives_without_probes_load_an_empty_table(monkeypatch):
    monkeypatch.setattr(dom_probe, "PROBE_NUMBERS", (97, 98))  # no such modules anywhere
    assert dom_probe._load_probe_modules() == ()
    assert dom_probe._table(()) == {}


def test_a_partial_probe_set_fails_closed(monkeypatch):
    monkeypatch.setattr(dom_probe, "PROBE_NUMBERS", (1, 98))
    with pytest.raises(dom_probe.ProbeTableError, match="probe_p98"):
        dom_probe._load_probe_modules()


def test_refusals_happen_before_any_probe_runs(monkeypatch):
    _song, off = dispatcher(dev=False)
    for method in ("probe_list", "probe_read"):
        assert off(method, {"name": "P-01"})["code"] == "dev_probes_disabled"
    gen = off("hello", {})["generation"]
    lease = off("lease_acquire", {"ttl": 5})["lease"]
    params = {"name": "P-02", "generation": gen, "lease": lease}
    assert off("probe_run", params)["code"] == "dev_probes_disabled"

    _song, ro = dispatcher(writable=False)  # the write gate runs first
    assert ro("probe_run", {"name": "P-02"})["code"] == "read_only"

    _song, d = dispatcher()
    for bad in ("P-99", "probe_p01", "__class__", 1, None):
        assert d("probe_read", {"name": bad})["code"] == "unknown_probe"
    assert d("probe_read", {"name": "P-02"})["code"] == "wrong_probe_kind"
    gen = d("hello", {})["generation"]
    assert d("probe_run", {"name": "P-01", "generation": gen})["code"] == "wrong_probe_kind"
    assert d("probe_run", {"name": "P-02", "generation": gen})["code"] == "lease_required"
    assert d("probe_run", {"name": "P-02", "lease": "x"})["code"] == "lease_expired"
    lease = d("lease_acquire", {"ttl": 5})["lease"]
    reply = d("probe_run", {"name": "P-29", "generation": gen, "lease": lease})
    assert reply == {
        "probe": "P-29",
        "kind": "write",
        "ok": True,
        "result": {"verdict": "not_implemented"},
        "scratch": [],
    }


def test_scratch_objects_are_cleaned_up_even_when_a_probe_raises(monkeypatch):
    song, d = dispatcher()
    original = list(song.tracks)

    def boom(_ctx, scratch):
        assert scratch.owns(scratch.midi_track()) and not scratch.owns(original[0])
        raise RuntimeError("probe failed")

    monkeypatch.setitem(dom_probe.PROBES, "P-02", (boom, "write"))
    gen = d("hello", {})["generation"]
    lease = d("lease_acquire", {"ttl": 5})["lease"]
    reply = d("probe_run", {"name": "P-02", "generation": gen, "lease": lease})
    assert reply["ok"] is False and reply["error"] == "RuntimeError: probe failed"
    assert reply["scratch"] == [{"kind": "track", "deleted": True}]
    assert song.tracks == original


def test_p01_dumps_fixed_classes_and_answers_hasattr(monkeypatch):
    class SongCls:
        """The Song."""

        def tap_tempo(self):
            """Tap."""

        def get_data(self):
            pass

    class SongView:
        pass

    SongCls.View = SongView
    live = types.ModuleType("Live")
    live.Song = types.ModuleType("Live.Song")
    live.Song.Song = SongCls
    monkeypatch.setitem(sys.modules, "Live", live)
    _song, d = dispatcher()
    reply = d("probe_read", {"name": "P-01"})
    assert reply["ok"] is True
    result = reply["result"]
    assert result["verdict"] == "go" and result["live_version"] == [12, 2, 5]
    assert result["classes"]["Song"]["members"]["tap_tempo"] == "Tap."
    assert result["hasattr"]["tap_tempo"] == ["Song"] and result["hasattr"]["nudge_up"] == []
    assert "Track" in result["missing"] and set(result["modules"]) == {"Song"}


def test_dev_probes_config_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", str(tmp_path / "missing.json"))
    assert safety.config_dev_probes() is False
    for bad in (None, "true", 1, {}):
        assert Safety(lambda: None, dev_probes=lambda bad=bad: bad).dev_probes_enabled() is False


class FakeClient:
    def __init__(self, replies):
        self.replies, self.calls = replies, []

    def call(self, method, params=None):
        self.calls.append(method)
        return self.replies[method]


def test_runner_refuses_without_dev_probes_and_strips_owner_paths(tmp_path):
    refused = {"refused": True, "code": "dev_probes_disabled", "message": "off"}
    client = FakeClient({"hello": {"live_version": [12, 2, 5]}, "probe_list": refused})
    with pytest.raises(runner.Abort, match="dev_probes_disabled"):
        runner.run_probe(client, "P-01")

    home = "C:\\Users\\Zq7user"
    result = {
        "verdict": "go",
        "hasattr": {"tap_tempo": ["Song"]},
        "classes": {"Song": {"path": "Live.Song.Song", "doc": "", "members": {}}},
        "note": f"{home}\\Music and /home/zq8user/x and C:/Users/Zq9user/AppData",
    }
    replies = {
        "hello": {"live_version": [12, 2, 5], "protocol": 2},
        "probe_list": {"probes": {"P-01": "read"}},
        "probe_read": {"probe": "P-01", "kind": "read", "ok": True, "result": result},
    }
    hello, reply = runner.run_probe(FakeClient(replies), "P-01")
    written = runner.write_evidence("P-01", hello, reply, root=tmp_path, home=home)
    assert [p.relative_to(tmp_path).as_posix() for p in written] == [
        "docs/data/live-12.2-api.json",
        "docs/release/probes/P-01.md",
    ]
    for path in written:
        text = path.read_text(encoding="utf-8")
        assert "Zq7user" not in text and "zq8user" not in text and "Zq9user" not in text
    assert "~\\\\Music" in written[0].read_text(encoding="utf-8")
    assert "| `tap_tempo` | Song |" in written[1].read_text(encoding="utf-8")
