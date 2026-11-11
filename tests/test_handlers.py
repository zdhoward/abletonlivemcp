import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from AbletonLiveMCP import handlers  # noqa: E402
from AbletonLiveMCP import safety as safety_module  # noqa: E402
from AbletonLiveMCP.handlers import make_dispatch  # noqa: E402
from AbletonLiveMCP.safety import CLASSIFICATION, READ, WRITE, Safety  # noqa: E402


class Item:
    def __init__(self, name, children=None, loadable=False, device=None):
        self.name = name
        self.children = children or []
        self.is_folder = bool(children)
        self.is_loadable = loadable
        self.is_device = loadable if device is None else device
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


class AudioTrack(Track):
    def __init__(self, name):
        super().__init__(name)
        self.has_midi_input = False
        self.devices = []


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
        self.calls = 0
        self.hook = None  # what the fake "Live" does when a load starts
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
        self.calls += 1
        if self.hook:
            self.hook(item)


class App:
    def __init__(self):
        self.browser = Browser()


@pytest.fixture
def env():
    song, app = Song(), App()
    safety = Safety(lambda: song, policy=lambda: False)  # writes enabled for these tests
    return song, app, make_dispatch(lambda: song, app, safety)


def track_ref(d, i):
    return d("tracks", {})[i]["ref"]


def param_ref(d, track, device, parameter):
    return d("device_parameters", {"track": track, "device": device})[parameter]["ref"]


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


class Wide:
    """A huge child collection that counts how many children were actually pulled."""

    def __init__(self, n):
        self.n, self.yielded = n, 0

    def __iter__(self):
        for i in range(self.n):
            self.yielded += 1
            yield Item(f"n{i}", loadable=True)


def test_browser_bounds_pages_cursors_and_display_cap(env):
    _s, app, d = env
    clock = [0.0]
    d.operations.cursors._clock = lambda: clock[0]
    wide = Wide(450)
    app.browser.plugins = Item("plugins", wide)
    # listing: pages of <= 200, lazy (201 pulled for the first page, not 450)
    page = d("browser_list", {"root": "plugins"})
    print("\nlist page 1:", len(page["items"]), "pulled", wide.yielded, page["truncated"])
    assert len(page["items"]) == 200 and page["truncated"] and wide.yielded == 201
    sizes = [200]
    while page["cursor"]:
        page = d("browser_list", {"root": "plugins", "cursor": page["cursor"]})
        sizes.append(len(page["items"]))
    assert sizes == [200, 200, 50] and page["complete"] and not page["truncated"]
    with pytest.raises(ValueError):
        d("browser_list", {"root": "plugins", "limit": 201})
    # search: 4000 visited per slice, then a cursor; a wide child loop cannot exceed it
    wide = Wide(10000)
    app.browser.plugins = Item("plugins", wide)
    s = d("browser_search", {"root": "plugins", "query": "zzz"})
    print("search slice 1:", s["visited"], "pulled", wide.yielded, s["budget_exhausted"])
    assert s["visited"] == 4000 == wide.yielded and s["budget_exhausted"] and not s["complete"]
    seen = s["visited"]
    while s["cursor"]:
        s = d("browser_search", {"root": "plugins", "cursor": s["cursor"]})
        seen += s["visited"]
    assert seen == 10000 and s["complete"] and wide.yielded == 10000
    # result cap: 100 per slice, flagged truncated rather than silently cut
    r = d("browser_search", {"root": "plugins", "query": "n", "limit": 100})
    assert len(r["results"]) == 100 and r["truncated"] and r["cursor"]
    with pytest.raises(ValueError):
        d("browser_search", {"root": "plugins", "query": "n", "limit": 101})
    # cursors: at most 4 live, single use, 30 s expiry
    first = d("browser_list", {"root": "plugins", "limit": 1})["cursor"]
    for _ in range(4):
        d("browser_list", {"root": "plugins", "limit": 1})
    assert len(d.operations.cursors) == 4
    assert d("browser_list", {"root": "plugins", "cursor": first})["code"] == "unknown_cursor"
    live = d("browser_list", {"root": "plugins", "limit": 1})["cursor"]
    clock[0] += 31
    assert d("browser_list", {"root": "plugins", "cursor": live})["code"] == "unknown_cursor"
    # display sampling: 129 conversions per request in total, not 64 x 129
    loc = {"track": 0, "device": 0}
    ok = [{"parameter": 0, "values": [0.5] * 64}, {"parameter": 1, "values": [0.5] * 65}]
    assert len(d("sample_parameters", {**loc, "requests": ok})["results"]) == 2
    for requests in (
        [{"parameter": 0, "values": [0.5] * 64}, {"parameter": 1, "values": [0.5] * 66}],
        [{"parameter": 0, "values": [0.5] * 129}] * 64,
    ):
        with pytest.raises(ValueError, match="in total"):
            d("sample_parameters", {**loc, "requests": requests})


def _append_setup(env):
    """An audio track holding one ready owned device; returns (song, app, d, audio, base, op)."""
    song, app, d = env
    audio = AudioTrack("Audio")
    song.tracks.append(audio)
    base = {"track": track_ref(d, 2), "root": "audio_effects", "path": ["Reverb"]}
    app.browser.hook = lambda item: audio.devices.append(Dev())
    op = d("load_item", base)
    d.operations.tick(), d.operations.tick()
    assert d("operation", {"operation": op["operation"]})["state"] == "ready"
    audio.view = types.SimpleNamespace(selected_device=None)

    def select(device):
        audio.view.selected_device = device

    song.view.select_device = select
    return song, app, d, audio, base, op


def test_append_selects_last_device_and_verifies_placement(env):
    song, app, d, audio, base, op = _append_setup(env)
    first = audio.devices[0]
    app.browser.hook = lambda item: audio.devices.insert(
        audio.devices.index(audio.view.selected_device) + 1, Dev()
    )
    second = d("load_item", {**base, "after": op["operation"]})
    assert second["state"] == "pending" and audio.view.selected_device is first
    d.operations.tick(), d.operations.tick()
    done = d("operation", {"operation": second["operation"]})
    print("\nappend ready:", done["state"], done["devices_after"], "calls", app.browser.calls)
    assert done["state"] == "ready" and done["devices_after"] == ["Eq8", "Eq8"]
    assert (
        audio.devices[0] is first
        and d.safety.resolve("device", done["device"], song).obj is (audio.devices[1])
    )
    # a third append selects the (new) last device
    third = d("load_item", {**base, "after": second["operation"]})
    assert audio.view.selected_device is audio.devices[1] and third["state"] == "pending"


def test_append_wrong_position_is_unknown_and_quarantined(env):
    _song, app, d, audio, base, op = _append_setup(env)
    app.browser.hook = lambda item: audio.devices.insert(0, Dev())  # Live ignored the selection
    bad = d("load_item", {**base, "after": op["operation"]})
    d.operations.tick()
    r = d("operation", {"operation": bad["operation"]})
    print("\nwrong position:", r["state"], r["reason"], r["device"])
    assert (r["state"], r["reason"], r["device"]) == ("unknown", "unexpected_placement", None)
    calls = app.browser.calls
    assert d("load_item", {**base, "after": op["operation"]})["code"] == "quarantined"
    assert app.browser.calls == calls and len(audio.devices) == 2  # nothing undone or retried


def test_append_without_select_device_refuses_before_browser(env):
    song, app, d, audio, base, op = _append_setup(env)
    del song.view.select_device
    calls = app.browser.calls
    r = d("load_item", {**base, "after": op["operation"]})
    print("\nno select_device:", r["code"], "browser calls", app.browser.calls - calls)
    assert r["code"] == "append_unverified" and r["applied"] is False
    assert app.browser.calls == calls and len(audio.devices) == 1
    song.view.select_device = lambda device: None  # selection that is not observed
    assert d("load_item", {**base, "after": op["operation"]})["code"] == "append_unverified"
    assert app.browser.calls == calls


def test_load_state_contract(env):
    song, app, d = env
    audio, other = AudioTrack("Audio"), AudioTrack("Other")
    full = AudioTrack("Full")
    full.devices = [Dev()]
    song.tracks += [audio, other, full]
    ops, now = d.operations, [0.0]
    ops._clock = lambda: now[0]
    app.browser.audio_effects.children.append(Item("Preset", loadable=True, device=False))
    base = {"track": track_ref(d, 2), "root": "audio_effects", "path": ["Reverb"]}
    refused = {
        "midi track": {**base, "track": track_ref(d, 1)},
        "occupied audio track": {**base, "track": track_ref(d, 4)},
        "folder item": {**base, "path": ["Dynamics"]},
        "preset item": {**base, "path": ["Preset"]},
        "missing item": {**base, "path": ["Nope"]},
        "unsupported root": {**base, "root": "samples"},
        "bad 'after'": {**base, "after": "nope"},
    }
    print("\npre-load refusals:")
    for name, params in refused.items():
        r = d("load_item", params)
        print(f"  {name}: {r['code']}")
        assert r["refused"] and r["applied"] is False
    assert app.browser.calls == 0 and song.view.selected_track is None

    # start: pending, no device reference, nothing to write to yet; a second load is refused
    app.browser.hook = lambda item: audio.devices.append(Dev())
    op = d("load_item", base)
    assert (op["state"], op["device"], op["may_have_applied"]) == ("pending", None, True)
    assert song.view.selected_track is audio and app.browser.calls == 1
    assert d("load_item", {**base, "track": track_ref(d, 3)})["code"] == "load_pending"
    assert ops.tick() == 1 and d("operation", {"operation": op["operation"]})["state"] == "pending"
    assert ops.tick() == 1  # no request arrived in between: idle ticks advance the load
    done = d("operation", {"operation": op["operation"]})
    print("ready:", done["state"], done["devices_after"], "calls", app.browser.calls)
    assert done["state"] == "ready" and done["applied"] is True and done["devices_after"] == ["Eq8"]
    assert d.safety.resolve("device", done["device"], song).obj is audio.devices[0]
    # occupied now: a fresh load is refused; this fake View has no select_device, so append refuses
    assert d("load_item", {**base, "track": track_ref(d, 2)})["code"] == "target_occupied"
    after = {**base, "after": op["operation"]}
    assert d("load_item", after)["code"] == "append_unverified" and app.browser.calls == 1
    audio.devices.append(Dev())  # a user edit: no longer exactly the owned prefix
    assert d("load_item", after)["code"] == "prefix_mismatch" and app.browser.calls == 1

    # timeout is unknown, never absent: target quarantined, no retry; a late device is observed
    app.browser.hook = None
    t3 = {**base, "track": track_ref(d, 3)}
    lost = d("load_item", t3)
    now[0] += 21
    ops.tick()
    assert d("operation", {"operation": lost["operation"]})["reason"] == "timeout"
    assert d("load_item", t3)["code"] == "quarantined" and app.browser.calls == 2
    other.devices.append(Dev())
    ops.tick(), ops.tick()
    late = d("operation", {"operation": lost["operation"]})
    assert (late["state"], late["reason"]) == ("ready", "late")

    # never choose by count: two new devices at once are ambiguous, not "the last one"
    third = AudioTrack("Third")
    song.tracks.append(third)
    app.browser.hook = lambda item: third.devices.extend([Dev(), Dev()])
    amb = d("load_item", {**base, "track": track_ref(d, 5)})
    ops.tick()
    r = d("operation", {"operation": amb["operation"]})
    print("ambiguous:", r["state"], r["reason"])
    assert (r["state"], r["reason"], r["device"]) == ("unknown", "ambiguous_change", None)
    assert d("load_item", {**base, "track": track_ref(d, 5)})["code"] == "quarantined"


def test_entry_point_tick_and_disconnect_wiring(env):
    import AbletonLiveMCP as package

    song, app, d = env
    audio = AudioTrack("Audio")
    song.tracks.append(audio)
    app.browser.hook = lambda item: audio.devices.append(Dev())
    calls = []

    class Base:  # stands in for Live's ControlSurface
        def update_display(self):
            calls.append("super.update_display")

        def disconnect(self):
            calls.append("super.disconnect")

        def log_message(self, message):
            calls.append(f"log:{message}")

    class Server:
        def drain(self):
            calls.append("server.drain")

        def stop(self):
            calls.append("server.stop")

    real_tick = d.operations.tick
    d.operations.tick = lambda: calls.append("operations.tick") or real_tick()
    entry_class = type("Entry", (package.AbletonLiveMCP, Base), {})
    entry = entry_class.__new__(entry_class)  # skip Live-only __init__
    entry._server, entry._dispatch = Server(), d
    op = d("load_item", {"track": track_ref(d, 2), "root": "audio_effects", "path": ["Reverb"]})
    for _ in range(2):  # empty request queue: only update_display runs
        entry.update_display()
    print("\nupdate_display order:", calls)
    assert calls == ["super.update_display", "server.drain", "operations.tick"] * 2
    assert d("operation", {"operation": op["operation"]})["state"] == "ready"
    # a second load goes pending, then disconnect invalidates it and stops later ticks
    audio.devices.clear()
    gen = d.safety.generation
    again = d("load_item", {"track": track_ref(d, 2), "root": "audio_effects", "path": ["Reverb"]})
    calls.clear()
    entry.disconnect()
    print("disconnect order:", calls)
    assert calls == ["server.stop", "super.disconnect"] and d.safety.generation == gen + 1
    gone = d("operation", {"operation": again["operation"]})
    assert (gone["state"], gone["reason"]) == ("unknown", "session_ended")
    entry.update_display()
    assert real_tick() == 0 and d("operation", {"operation": again["operation"]}) == gone


def test_set_parameter_readback_and_guards(env):
    song, _a, d = env
    gain, macro = param_ref(d, 0, 0, 0), param_ref(d, 0, 0, 1)
    r = d("set_device_parameter", {"parameter": gain, "value": 0.75})
    assert r["value"] == 0.75 and song.tracks[0].devices[0].parameters[0].value == 0.75
    with pytest.raises(ValueError, match="outside"):
        d("set_device_parameter", {"parameter": gain, "value": 2})
    with pytest.raises(ValueError, match="not enabled"):
        d("set_device_parameter", {"parameter": macro, "value": 0.5})
    assert d("set_device_parameter", {"parameter": True, "value": 0.5})["code"] == (
        "reference_required"
    )


def test_sample_parameter_reads_displays_without_writing(env):
    song, _app, d = env
    r = d("sample_parameter", {"track": 0, "device": 0, "parameter": 0, "values": [0, 0.25, 1]})
    assert r == {"name": "Gain", "displays": ["0.00", "0.25", "1.00"]}
    assert song.tracks[0].devices[0].parameters[0].value == 0.5  # untouched
    bad = [[], "x", [2], [True], ["0.5"], [0.5] * 130]
    for values in bad:
        with pytest.raises(ValueError):
            d("sample_parameter", {"track": 0, "device": 0, "parameter": 0, "values": values})
    with pytest.raises(ValueError):
        d("sample_parameter", {"track": 0, "device": 0, "parameter": 9, "values": [0.5]})


def test_batch_sample_and_write_validate_everything_before_writing(env):
    song, _app, d = env
    loc = {"track": 0, "device": 0}
    gain = param_ref(d, 0, 0, 0)
    r = d("sample_parameters", {**loc, "requests": [{"parameter": 0, "values": [0, 1]}]})
    assert r == {"results": [{"name": "Gain", "displays": ["0.00", "1.00"]}]}
    r = d("set_device_parameters", {"writes": [{"parameter": gain, "value": 0.75}]})
    assert r["results"][0]["value"] == 0.75
    assert song.tracks[0].devices[0].parameters[0].value == 0.75
    # one bad entry means nothing at all is written
    bad = [{"parameter": gain, "value": 0.1}, {"parameter": gain, "value": 5}]
    with pytest.raises(ValueError):
        d("set_device_parameters", {"writes": bad})
    assert song.tracks[0].devices[0].parameters[0].value == 0.75
    for items in ["x", [3], [{}] * 65]:
        with pytest.raises(ValueError):
            d("set_device_parameters", {"writes": items})
    with pytest.raises(ValueError):
        d("set_device_parameters", {"writes": []})
    with pytest.raises(ValueError):
        d("set_device_parameters", {"writes": [{"parameter": gain, "value": True}]})


def test_create_track_name_color_tempo(env):
    song, _a, d = env
    gen = {"generation": d.safety.generation}
    assert d("create_track", {"kind": "midi", **gen})["track_count"] == 3
    with pytest.raises(ValueError):
        d("create_track", {"kind": "video", **gen})
    t0 = track_ref(d, 0)
    assert d("set_track_name", {"track": t0, "name": "Lead"})["name"] == "Lead"
    assert d("set_track_color", {"track": t0, "color_index": 5})["color_index"] == 5
    assert d("set_tempo", {"bpm": 128, **gen})["tempo"] == 128
    with pytest.raises(ValueError):
        d("set_tempo", {"bpm": 5, **gen})
    with pytest.raises(ValueError, match="missing required parameter 'bpm'"):
        d("set_tempo", dict(gen))
    assert d.methods and "set_tempo" in d.methods


class Clip:
    name, length, is_playing, looping, is_midi_clip = "c", 4.0, False, True, True
    fired = False

    def fire(self):
        self.fired = True


class Slot:
    def __init__(self):
        self.has_clip, self.clip = True, Clip()


class Scene:
    name, is_triggered = "s", False
    fired = False

    def fire(self):
        self.fired = True


def test_safety_contract_classification_refusal_and_leases(env, tmp_path, monkeypatch):
    song, app, d = env
    song.scenes = [Scene()]
    song.tracks[0].clip_slots = [Slot()]
    now = [100.0]
    safe = Safety(lambda: song, policy=lambda: False, clock=lambda: now[0])
    d = make_dispatch(lambda: song, app, safe)

    # 1. every handler is classified; writes have a target spec; classification table
    table = handlers._handlers(song, app, safe)
    assert set(table) == {m for m, k in CLASSIFICATION.items() if k in (READ, WRITE)}
    assert {m for m, k in CLASSIFICATION.items() if k == WRITE} == set(safety_module.TARGETS)
    print("\nmethod classification:")
    for kind in (READ, WRITE, "control"):
        print(f"  {kind:7}", sorted(m for m, k in CLASSIFICATION.items() if k == kind))
    with pytest.raises(ValueError, match="unclassified"):
        d("delete_everything", {})

    # 2. refusals happen before any write: index-only, wrong kind, stale layout, stale gen
    gen = {"generation": safe.generation}
    gain_ref = param_ref(d, 0, 0, 0)
    refusals = {
        "index-only parameter": d("set_device_parameter", {"parameter": 0, "value": 0.9}),
        "index-only track": d("set_track_name", {"track": 0, "name": "X"}),
        "wrong-kind ref": d("set_track_name", {"track": gain_ref, "name": "X"}),
        "invented ref": d("set_track_name", {"track": "deadbeef", "name": "X"}),
        "no generation": d("set_tempo", {"bpm": 90}),
        "stale generation": d("set_tempo", {"bpm": 90, "generation": 99}),
    }
    for name, r in refusals.items():
        print(f"  refused {name}: {r['code']}")
        assert r["refused"] and r["applied"] is False
    assert song.tempo == 120.0 and song.tracks[0].name == "A"
    assert song.tracks[0].devices[0].parameters[0].value == 0.5

    # stale: a device is removed/inserted after the read, parameter ref must now be refused
    song.tracks[0].devices.append(Dev())
    r = d("set_device_parameter", {"parameter": gain_ref, "value": 0.9})
    print("  refused stale device layout:", r["code"])
    assert r["code"] == "stale_target" and song.tracks[0].devices[0].parameters[0].value == 0.5
    song.tracks[0].devices.pop()
    # a track removed from the Set (reorder/delete) invalidates its reference
    t1 = track_ref(d, 1)
    removed = song.tracks.pop(1)
    assert d("set_track_name", {"track": t1, "name": "X"})["code"] == "stale_target"
    song.tracks.insert(1, removed)
    # clip/scene refs: valid then stale when the clip leaves its slot
    clip_ref = d("clip_slot", {"track": 0, "scene": 0})["clip"]
    scene_ref = d("scenes", {})[0]["ref"]
    assert d("fire_clip", {"clip": clip_ref})["is_playing"] is False
    assert d("fire_scene", {"scene": scene_ref})["name"] == "s"
    song.tracks[0].clip_slots[0].has_clip = False
    assert d("fire_clip", {"clip": clip_ref})["code"] == "stale_target"
    song.tracks[0].clip_slots[0].has_clip = True

    # 3. read-only policy refuses every write method, first, even with valid refs
    ro = make_dispatch(lambda: song, app, Safety(lambda: song, policy=lambda: True))
    t0 = ro("tracks", {})[0]["ref"]
    for method in sorted(safety_module.TARGETS):
        assert ro(method, {"track": t0})["code"] == "read_only", method
    for bad in (None, "false", 0, {}):  # only the literal False enables writes
        assert Safety(lambda: song, policy=lambda bad=bad: bad).read_only() is True
    assert song.tracks[0].name == "A"

    # real config path: fail closed on missing/invalid, False only when explicit
    cfg = tmp_path / "bridge.json"
    monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", str(cfg))
    assert safety_module.config_read_only() is True  # missing file
    monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", "relative.json")
    assert safety_module.config_read_only() is True  # not absolute, no home fallback

    # 4. lease: competing owner refused, wrong token refused, expiry, release, invalidation
    lease = d("lease_acquire", {"ttl": 5})
    assert d("lease_acquire", {"ttl": 5})["code"] == "lease_held"
    assert d("set_tempo", {"bpm": 90, **gen})["code"] == "lease_held"  # no token
    assert d("set_tempo", {"bpm": 90, **gen, "lease": "x" * 32})["code"] == "lease_held"
    assert d("set_tempo", {"bpm": 90, **gen, "lease": lease["lease"]})["tempo"] == 90
    now[0] += 5.0
    assert d("set_tempo", {"bpm": 91, **gen, "lease": lease["lease"]})["code"] == "lease_expired"
    assert d("lease_acquire", {"ttl": 1000})["ttl"] == safety_module.MAX_LEASE_TTL  # capped
    assert d("lease_acquire", {})["code"] == "lease_held"
    assert d("lease_release", {"lease": "nope"})["code"] == "lease_mismatch"
    now[0] += safety_module.MAX_LEASE_TTL
    again = d("lease_acquire", {"ttl": 5})  # expiry freed the bridge
    assert d("lease_release", {"lease": again["lease"]}) == {"released": True}
    held = d("lease_acquire", {"ttl": 5})
    safe.invalidate()  # disconnect/session end drops lease and refs
    assert d("set_tempo", {"bpm": 95, "generation": safe.generation}) == {"tempo": 95}
    assert d("set_track_name", {"track": t0, "name": "X"})["code"] in {"unknown_reference"}
    print(
        "  lease outcomes: held/wrong-token refused, expiry, release, invalidation ok", held["ttl"]
    )

    # 5. Set change: a different Song object bumps generation and expires every reference
    ref = track_ref(d, 0)
    old_generation = safe.generation
    other = Song()
    song_box = [other]
    safe._supplier = lambda: song_box[0]
    r = d("set_track_name", {"track": ref, "name": "Z"})
    assert r["refused"] and safe.generation == old_generation + 1
    assert other.tracks[0].name == "A" and song.tracks[0].name == "A"

    # 6. bounded registry
    for _ in range(safety_module.MAX_REFS + 50):
        safe.issue(("track", other.tracks[0], {}))
    assert len(safe._refs) == safety_module.MAX_REFS
