"""Batch 5: offline .als reading (confinement, limits, recency), labels, knowledge tool."""

import gzip
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

from AbletonLiveMCP import dom_labels  # noqa: E402
from abletonlivemcp import labelstore, server  # noqa: E402
from abletonlivemcp.als import AlsError, collect, read_set  # noqa: E402
from abletonlivemcp.als import paths as als_paths  # noqa: E402
from abletonlivemcp.als import reader as als_reader  # noqa: E402
from abletonlivemcp.als.paths import PathEscape, confine  # noqa: E402
from abletonlivemcp.als.usage import build_index, find_sets  # noqa: E402
from abletonlivemcp.models_library import LabelItem  # noqa: E402
from AbletonLiveMCP.safety import CLASSIFICATION, TARGETS, WRITE  # noqa: E402
from abletonlivemcp.tools import organize  # noqa: E402

PLUGIN = (
    '<PluginDevice><PluginDesc><Vst3PluginInfo><Name Value="Synth"/></Vst3PluginInfo>'
    "</PluginDesc></PluginDevice>"
)


def set_xml(content=""):
    return f"<Ableton><LiveSet>{content}</LiveSet></Ableton>".encode()


def write_set(path: Path, content="", age_days=0.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(set_xml(content)))
    when = path.stat().st_mtime - age_days * 86400
    os.utime(path, (when, when))
    return path


def junction(link: Path, target: Path):
    """A directory link without admin rights on Windows, a symlink elsewhere; skip if refused."""
    try:
        if os.name == "nt":
            done = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True
            )
            if done.returncode:
                pytest.skip("cannot create a junction here")
        else:
            link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("cannot create a link here")


# ---- path confinement ---------------------------------------------------------------------


def test_confine_accepts_paths_under_a_root(tmp_path):
    inside = tmp_path / "a" / "x.als"
    assert confine(inside, [tmp_path]) == inside


@pytest.mark.parametrize(
    "bad",
    [
        "{root}\\..\\outside.als",
        "{root}/sub/../../outside.als",
        "relative/x.als",
        "\\\\?\\{root}\\x.als",
        "{root}\\x.als:stream",
        "{outside}\\x.als",
        "{root}\x00x.als",
    ],
)
def test_path_escape_is_refused(tmp_path, bad):
    root = tmp_path / "root"
    root.mkdir()
    text = bad.format(root=root, outside=tmp_path / "other")
    with pytest.raises(PathEscape):
        confine(text, [root])


def test_sibling_with_the_same_prefix_is_outside(tmp_path):
    (tmp_path / "root").mkdir()
    with pytest.raises(PathEscape):
        confine(tmp_path / "root-evil" / "x.als", [tmp_path / "root"])


def test_junction_or_symlink_inside_a_root_is_refused_and_not_scanned(tmp_path):
    root, outside = tmp_path / "root", tmp_path / "outside"
    write_set(outside / "secret.als")
    write_set(root / "ok.als")
    junction(root / "link", outside)
    with pytest.raises(PathEscape):
        confine(root / "link" / "secret.als", [root])
    with pytest.raises(AlsError, match="refused"):
        read_set(root / "link" / "secret.als", roots=[root])
    assert find_sets(root) == [root / "ok.als"]
    got = collect([root], confine=[root])
    assert [s.path for s in got.summaries] == [root / "ok.als"]


def test_roots_come_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv(
        als_paths.ROOTS_ENV, os.pathsep.join([str(tmp_path), "relative", "C:/nope-x"])
    )
    monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", str(tmp_path / "absent.json"))
    assert als_paths.configured_roots() == [Path(os.path.abspath(tmp_path))]


# ---- XML and size limits ------------------------------------------------------------------


@pytest.mark.parametrize(
    "xml",
    [
        b'<?xml version="1.0"?><!DOCTYPE x><Ableton><LiveSet/></Ableton>',
        b'<!DOCTYPE x [<!ENTITY a "b">]><Ableton><LiveSet>&a;</LiveSet></Ableton>',
        b'<?xml version="1.0"?>' + b" " * 70000 + b'<!DOCTYPE x [<!ENTITY a "b">]><Ableton/>',
    ],
)
def test_dtd_and_entities_are_refused(xml):
    with pytest.raises(AlsError):
        als_reader.parse_xml_bytes(xml)


def test_node_and_depth_limits(monkeypatch):
    monkeypatch.setattr(als_reader, "MAX_NODES", 5)
    with pytest.raises(AlsError, match="more than 5"):
        als_reader.parse_xml_bytes(set_xml("<a/>" * 10))
    monkeypatch.setattr(als_reader, "MAX_NODES", 1000)
    monkeypatch.setattr(als_reader, "MAX_DEPTH", 4)
    with pytest.raises(AlsError, match="deeper"):
        als_reader.parse_xml_bytes(set_xml("<a>" * 5 + "</a>" * 5))


def test_decompressed_and_compressed_size_limits(tmp_path, monkeypatch):
    path = write_set(tmp_path / "big.als", "<a/>" * 2000)
    monkeypatch.setattr(als_reader, "MAX_XML_BYTES", 500)
    with pytest.raises(AlsError, match="decompresses"):
        read_set(path, roots=[tmp_path])
    monkeypatch.setattr(als_reader, "MAX_XML_BYTES", 10**6)
    monkeypatch.setattr(als_reader, "MAX_GZIP_BYTES", 10)
    with pytest.raises(AlsError, match="larger than"):
        read_set(path, roots=[tmp_path])
    with pytest.raises(AlsError, match="larger than"):
        read_set(path)


def test_confined_read_matches_a_plain_read(tmp_path):
    path = write_set(
        tmp_path / "a.als", "<MidiTrack><Name><EffectiveName Value='T'/></Name></MidiTrack>"
    )
    assert read_set(path, roots=[tmp_path]).tracks == read_set(path).tracks == ["T"]


# ---- usage and recency --------------------------------------------------------------------


def test_plugin_recency_and_filters(tmp_path):
    devices = f"<Devices><Reverb/>{PLUGIN}</Devices>"
    write_set(tmp_path / "new.als", devices, age_days=1)
    write_set(tmp_path / "old.als", devices, age_days=400)
    write_set(tmp_path / "Techno" / "t.als", devices, age_days=2)
    got = collect([tmp_path], confine=[tmp_path])
    assert got.found == 3 and not got.truncated
    index = build_index(got.summaries, got.errors, mtimes=got.mtimes, recent_days=90)
    (plugin,) = index.plugins
    assert (plugin.key, plugin.projects, plugin.recent) == ("vst3:Synth", 3, 2)
    newest = max(got.mtimes.values())
    assert plugin.last_seen == newest
    assert collect([tmp_path], since_days=30).found == 2
    assert collect([tmp_path], folder_glob="techno").found == 1
    assert len(collect([tmp_path], limit=1).summaries) == 1


def test_scan_and_usage_tools_end_to_end(tmp_path, monkeypatch):
    devices = f"<Devices><Reverb/>{PLUGIN}</Devices>"
    write_set(tmp_path / "a.als", f"<MidiTrack>{devices}</MidiTrack>")
    (tmp_path / "bad.als").write_bytes(b"not gzip")
    monkeypatch.setenv(als_paths.ROOTS_ENV, str(tmp_path))
    scan = server.tool("live_scan_projects")()
    data = scan["data"]
    assert data["sets_read"] == 1 and [e["path"] for e in data["errors"]] == [
        str(tmp_path / "bad.als")
    ]
    report = server.tool("live_usage_report")(kind="plugins", scan_id=data["scan_id"])
    assert [r["key"] for r in report["data"]["rows"]] == ["vst3:Synth"]
    assert server.tool("live_usage_report")(kind="devices")["data"]["rows"][0]["recent"] == 1
    with pytest.raises(ToolError, match="outside the configured roots"):
        server.tool("live_scan_projects")(roots=[str(tmp_path.parent)])
    with pytest.raises(ToolError, match="unknown scan_id"):
        server.tool("live_usage_report")(kind="samples", scan_id="nope")
    monkeypatch.delenv(als_paths.ROOTS_ENV)
    monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", str(tmp_path / "absent.json"))
    with pytest.raises(ToolError, match="no project roots"):
        server.tool("live_scan_projects")()


# ---- the global sidecar -------------------------------------------------------------------


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    path = tmp_path / "data"
    monkeypatch.setenv(labelstore.DATA_DIR_ENV, str(path))
    return path


def test_sidecar_is_atomic_isolated_and_merges(data_dir):
    assert labelstore.load()["entries"]["plugin"] == {}
    item = {
        "kind": "plugin",
        "key": "vst3:Serum",
        "labels": ["bass", "bass", "wt"],
        "category": "synth",
    }
    labelstore.apply([item], "replace")
    assert labelstore.load()["entries"]["plugin"]["vst3:Serum"] == {
        "labels": ["bass", "wt"],
        "category": "synth",
    }
    labelstore.apply([{**item, "labels": ["lead"], "category": None}], "add")
    assert labelstore.load()["entries"]["plugin"]["vst3:Serum"]["labels"] == ["bass", "wt", "lead"]
    labelstore.apply([{**item, "labels": ["bass", "wt", "lead"], "category": ""}], "remove")
    assert "vst3:Serum" not in labelstore.load()["entries"]["plugin"]
    assert sorted(p.name for p in data_dir.iterdir()) == ["labels.json"]  # no temp or lock left


def test_sidecar_refuses_corrupt_files_without_overwriting(data_dir):
    data_dir.mkdir()
    (data_dir / "labels.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(labelstore.LabelStoreError, match="not valid JSON"):
        labelstore.apply([{"kind": "plugin", "key": "k", "labels": ["a"]}], "replace")
    assert (data_dir / "labels.json").read_text(encoding="utf-8") == "{broken"


def test_sidecar_dir_must_be_absolute_and_not_a_link(tmp_path, monkeypatch):
    monkeypatch.setenv(labelstore.DATA_DIR_ENV, "relative/dir")
    with pytest.raises(labelstore.LabelStoreError, match="absolute"):
        labelstore.load()
    real = tmp_path / "real"
    real.mkdir()
    junction(tmp_path / "link", real)
    monkeypatch.setenv(labelstore.DATA_DIR_ENV, str(tmp_path / "link" / "data"))
    with pytest.raises(labelstore.LabelStoreError):
        labelstore.load()


def test_label_item_validation():
    assert LabelItem(kind="song", labels=["a"]).key is None
    for bad in (
        {"kind": "song", "key": 1},
        {"kind": "track"},
        {"kind": "track", "key": True},
        {"kind": "plugin", "key": ""},
        {"kind": "plugin", "key": "k", "expect_name": "x"},
        {"kind": "plugin", "key": "k", "labels": ["a\nb"]},
        {"kind": "plugin", "key": "k", "labels": ["x"] * 17},
        {"kind": "plugin", "key": "k", "extra": 1},
    ):
        with pytest.raises(ValueError):
            LabelItem(**bad)


# ---- labels in the Set (remote domain) ----------------------------------------------------


class Obj:
    def __init__(self, name="Obj"):
        self.name, self.store = name, {}

    def get_data(self, key, default=None):
        return self.store.get(key, default)

    def set_data(self, key, value):
        self.store[key] = value


def ctx_for(song):
    safety = SimpleNamespace(generation=7, quarantined={})
    return SimpleNamespace(song=song, safety=safety, capabilities=dom_labels.CAPABILITIES)


def make_song():
    song = Obj("song")
    song.tracks, song.return_tracks = [Obj("Bass"), Obj("Keys")], [Obj("Verb")]
    return song


def test_labels_are_declared_and_classified_at_the_gate():
    assert CLASSIFICATION["set_track_labels"] == WRITE == CLASSIFICATION["set_song_labels"]
    assert TARGETS["set_song_labels"] == () and TARGETS["set_track_labels"] == (
        ("items", "ref", "any"),
    )


def test_track_labels_round_trip_in_the_data_store():
    song = make_song()
    ctx = ctx_for(song)
    items = [
        {"kind": "track", "labels": ["bass", " sub "], "category": "low"},
        {"kind": "return_track", "labels": ["fx"]},
    ]
    targets = {
        "items": [SimpleNamespace(obj=song.tracks[0]), SimpleNamespace(obj=song.return_tracks[0])]
    }
    out = dom_labels.set_track_labels(ctx, {"items": items, "mode": "replace"}, targets)
    assert out["status"] == "complete" and out["unverified"] == ["labels.data"]
    assert out["applied"][0] == {
        "name": "Bass",
        "labels": {"labels": ["bass", "sub"], "category": "low"},
    }
    read = dom_labels.get_labels(ctx, {})
    assert [(r["kind"], r["index"]) for r in read["tracks"]] == [("track", 0), ("return_track", 0)]
    assert read["song"] is None and read["corrupt"] == []
    dom_labels.set_track_labels(
        ctx,
        {"items": [{"kind": "track", "labels": ["sub"], "category": ""}], "mode": "remove"},
        {"items": [SimpleNamespace(obj=song.tracks[0])]},
    )
    # remove with category "" drops the category as well as the listed label
    assert dom_labels.get_labels(ctx, {})["tracks"][0]["labels"] == {"labels": ["bass"]}


def test_song_labels_and_clearing():
    song = make_song()
    ctx = ctx_for(song)
    dom_labels.set_song_labels(ctx, {"item": {"labels": ["wip"]}, "generation": 7}, {})
    assert dom_labels.get_labels(ctx, {})["song"] == {"labels": ["wip"]}
    dom_labels.set_song_labels(ctx, {"item": {"labels": []}, "generation": 7}, {})
    assert dom_labels.get_labels(ctx, {})["song"] is None and song.store[dom_labels.KEY] == ""


def test_invalid_labels_and_corrupt_text_write_nothing():
    song = make_song()
    ctx = ctx_for(song)
    track = SimpleNamespace(obj=song.tracks[0])
    bad = [{"kind": "track", "labels": ["ok"]}, {"kind": "track", "labels": ["x" * 41]}]
    with pytest.raises(ValueError, match="at most 40"):
        dom_labels.set_track_labels(
            ctx,
            {"items": bad, "mode": "replace"},
            {"items": [track, SimpleNamespace(obj=song.tracks[1])]},
        )
    assert song.tracks[0].store == {} and song.tracks[1].store == {}  # pass 1 failed: none written
    song.tracks[0].store[dom_labels.KEY] = "{not json"
    assert dom_labels.get_labels(ctx, {})["corrupt"] == ["track/0"]
    one = {"items": [{"kind": "track", "labels": ["a"]}]}
    with pytest.raises(ValueError, match="unreadable"):
        dom_labels.set_track_labels(ctx, {**one, "mode": "add"}, {"items": [track]})
    dom_labels.set_track_labels(ctx, {**one, "mode": "replace"}, {"items": [track]})
    assert dom_labels.get_labels(ctx, {})["corrupt"] == []


def test_missing_data_api_is_refused_before_any_write():
    song = SimpleNamespace(tracks=[], return_tracks=[])  # no get_data/set_data at all
    with pytest.raises(Exception, match="get_data"):
        dom_labels.get_labels(ctx_for(song), {})


# ---- organize tools (host) ----------------------------------------------------------------


class FakeBridge:
    def __init__(self):
        self.calls = []

    def call(self, method, params=None):
        self.calls.append((method, params))
        if method == "get_labels":
            return {
                "song": {"labels": ["wip"]},
                "tracks": [
                    {"kind": "track", "index": 1, "name": "Keys", "labels": {"labels": ["pad"]}}
                ],
                "corrupt": [],
                "unverified": [],
            }
        return {"status": "complete", "applied": [], "items": []}


@pytest.fixture
def fake(monkeypatch, data_dir):
    bridge = FakeBridge()
    monkeypatch.setattr(organize, "_call", bridge.call)
    monkeypatch.setattr(organize, "_generation", lambda: 7)
    monkeypatch.setattr(
        server, "_writable", lambda *_args: None
    )  # the host's read_only gate is tested elsewhere

    def refs(selectors):
        names = {0: "Bass", 1: "Keys"}
        rows = []
        for s in selectors:
            name = names.get(s["track"], "Verb")
            if s.get("expect_name") not in (None, name):
                raise ValueError("name mismatch")
            rows.append(
                {
                    "kind": s["kind"],
                    "ref": f"r{s['track']}",
                    "name": name,
                    "expect_name": s.get("expect_name"),
                }
            )
        return rows

    monkeypatch.setattr(organize, "issue_refs", refs)
    return bridge


def test_set_labels_orders_writes_and_reports_a_receipt(fake, data_dir):
    items = [
        {"kind": "plugin", "key": "vst3:Serum", "labels": ["bass"]},
        {"kind": "song", "labels": ["wip"]},
        {"kind": "return_track", "key": 0, "labels": ["fx"], "expect_name": "Verb"},
        {"kind": "track", "key": 1, "labels": ["pad"]},
    ]
    out = server.tool("live_set_labels")(items=[LabelItem(**i) for i in items])
    assert out["status"] == "complete" and [i["outcome"] for i in out["items"]] == ["applied"] * 3
    methods = [c[0] for c in fake.calls]
    assert methods == ["set_track_labels", "set_song_labels"]
    sent = fake.calls[0][1]["items"]
    assert [(i["kind"], i["ref"], i["expect_name"]) for i in sent] == [
        ("return_track", "rreturn:0", "Verb"),
        ("track", "r1", None),
    ]
    assert fake.calls[1][1]["generation"] == 7
    assert labelstore.load()["entries"]["plugin"]["vst3:Serum"]["labels"] == ["bass"]


def test_set_labels_refuses_bad_input_before_any_write(fake, data_dir):
    items = [LabelItem(kind="track", key=0, labels=["a"], expect_name="Wrong")]
    with pytest.raises(ToolError, match="not applied"):
        server.tool("live_set_labels")(items=items)
    twice = [LabelItem(kind="plugin", key="k", labels=["a"])] * 2
    with pytest.raises(ToolError, match="repeats"):
        server.tool("live_set_labels")(items=twice)
    assert fake.calls == [] and not data_dir.exists()


def test_get_labels_merges_set_and_global_and_filters(fake, data_dir):
    labelstore.apply([{"kind": "sample", "key": "kick.wav", "labels": ["pad"]}], "replace")
    out = server.tool("live_get_labels")(label="pad")["data"]
    assert [(r["kind"], r["key"]) for r in out["set"]] == [("track", 1)]
    assert [(r["kind"], r["key"]) for r in out["global"]] == [("sample", "kick.wav")]
    only = server.tool("live_get_labels")(scope="global", kind="plugin")["data"]
    assert only["global"] == [] and "set" not in only
    assert [c[0] for c in fake.calls] == ["get_labels"]


# ---- knowledge tool -----------------------------------------------------------------------


def test_live_knowledge_search_read_and_refusals(tmp_path, monkeypatch):
    (tmp_path / "p.md").write_text(
        "# Page\n\nWidgets are tuned.\n\n## Part\n\nGadget text.\n", encoding="utf8"
    )
    monkeypatch.setenv("ABLETONLIVEMCP_KNOWLEDGE", str(tmp_path))
    tool = server.tool("live_knowledge")
    hit = tool(action="search", query="widgets")
    assert hit["action"] == "search" and hit["results"][0]["page"] == "p"
    page = tool(action="read", page="p", section="Part")
    assert "Gadget" in page["text"] and page["provenance"] == "knowledge_base_reference_data"
    for kwargs in (
        {"action": "search"},
        {"action": "search", "query": "a b", "page": "p"},
        {"action": "read"},
        {"action": "read", "page": "../x"},
        {"action": "read", "page": "p", "query": "x"},
    ):
        with pytest.raises(ToolError):
            tool(**kwargs)
    assert "live_knowledge_search" not in server.SPECS and "live_knowledge_read" not in server.SPECS


def test_knowledge_walk_skips_links_and_oversized_pages(tmp_path, monkeypatch):
    from abletonlivemcp import knowledge

    root, outside = tmp_path / "kb", tmp_path / "outside"
    root.mkdir()
    (root / "ok.md").write_text("# Ok\n", encoding="utf8")
    outside.mkdir()
    (outside / "leak.md").write_text("# Leak\n", encoding="utf8")
    junction(root / "link", outside)
    monkeypatch.setattr(knowledge, "MAX_PAGE_BYTES", 10)
    (root / "huge.md").write_text("# Huge page\n", encoding="utf8")
    monkeypatch.setenv("ABLETONLIVEMCP_KNOWLEDGE", str(root))
    assert [p["page"] for p in knowledge.list_pages()] == ["ok"]
