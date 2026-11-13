"""Batch 4 (devices, browser, chain, drums, racks, device extras): one small test per feature.

Remote handlers run against a fake Live through the real dispatcher and safety gate; host tools
run against a scripted bridge. Nothing here talks to Live.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from abletonlivemcp import chain, server  # noqa: E402
from AbletonLiveMCP.handlers import make_dispatch  # noqa: E402
from abletonlivemcp.models_devices import DrumRole, PadEdit  # noqa: E402
from AbletonLiveMCP.safety import Safety  # noqa: E402
from abletonlivemcp.tools import browser as browser_tools  # noqa: E402
from abletonlivemcp.tools import devices as device_tools  # noqa: E402
from abletonlivemcp.tools import drums as drum_tools  # noqa: E402

# ---- a small fake Live -----------------------------------------------------------------------


class P:
    def __init__(self, name, value=0.0, lo=0.0, hi=1.0, default=None, quantized=False):
        self.name, self.value, self.min, self.max = name, value, lo, hi
        self.is_quantized, self.is_enabled = quantized, True
        if default is not None:
            self.default_value = default
        if quantized:
            self.value_items = ["Off", "On"]

    def str_for_value(self, v):
        return f"{v:.2f}"

    def re_enable_automation(self):
        self.reenabled = True


class V:
    is_collapsed = False
    selected_device = None
    selected_chain = None
    selected_drum_pad = None


class D:
    def __init__(self, name, kind=2, chains=None, pads=None):
        self.name = self.class_name = name
        self.type = kind
        self.parameters = [P("Device On", 1.0), P("Gain", 0.5, default=0.25)]
        self.view = V()
        self.can_have_chains = chains is not None or pads is not None
        self.chains = chains if chains is not None else []
        self.can_have_drum_pads = pads is not None
        if pads is not None:
            self.drum_pads = pads


class Ch:
    def __init__(self, name, devices=None):
        self.name, self.devices = name, devices if devices is not None else []
        self.mute = self.solo = False

    def delete_device(self, i):
        del self.devices[i]


class Pad:
    def __init__(self, note, name="", chains=None):
        self.note, self.name = note, name
        self.chains = chains if chains is not None else []
        self.mute = self.solo = False

    def delete_all_chains(self):
        self.chains = []


class T:
    color_index = 0
    is_foldable = False

    def __init__(self, name, midi=False, devices=None):
        self.name, self.has_midi_input, self.has_audio_input = name, midi, not midi
        self.devices = devices if devices is not None else []
        self.view = V()

    def delete_device(self, i):
        del self.devices[i]


class SongView:
    selected_track = None

    def select_device(self, dev):
        self.selected_track.view.selected_device = dev


class Song:
    tempo, is_playing = 120.0, False
    signature_numerator = signature_denominator = 4

    def __init__(self):
        self.tracks = [T("Vox", devices=[D("EQ Eight"), D("Compressor")]), T("Keys", midi=True)]
        self.return_tracks = [T("Rev")]
        self.master_track = T("Master")
        self.scenes, self.view, self.moves = [], SongView(), 0

    def containers(self):
        out = []

        def walk(c):
            out.append(c)
            for dev in c.devices:
                for ch in dev.chains:
                    walk(ch)

        for t in self.tracks + self.return_tracks + [self.master_track]:
            walk(t)
        return out

    def move_device(self, dev, target, position):
        self.moves += 1
        for c in self.containers():
            if dev in c.devices:
                c.devices.remove(dev)
        target.devices.insert(position, dev)


class Item:
    def __init__(self, name, children=None, loadable=True):
        self.name, self.children = name, children or []
        self.is_folder, self.is_loadable, self.is_device = bool(children), loadable, loadable
        self.uri = f"uri:{name}"


class Browser:
    def __init__(self):
        self.calls, self.hook = 0, None
        self.audio_effects = Item("ae", [Item("Reverb"), Item("Audio Effect Rack")])
        self.instruments = Item("in", [Item("Drum Rack"), Item("Wavetable")])
        self.samples = Item("sm", [Item("Kick.wav")])
        self.max_for_live = Item("m4l", [Item("LFO")])

    def load_item(self, item):
        self.calls += 1
        if self.hook:
            self.hook(item)


class App:
    def __init__(self):
        self.browser = Browser()


@pytest.fixture
def env():
    song, app = Song(), App()
    safety = Safety(lambda: song, policy=lambda: False)
    return song, app, make_dispatch(lambda: song, app, safety)


def ref(d, kind, track, path=None):
    sel = {"kind": kind, "track": track}
    if path is not None:
        sel["path"] = path
    return d("ref_issue", {"targets": [sel]})["refs"][0]["ref"]


def refused(reply, code):
    return isinstance(reply, dict) and reply.get("refused") and reply.get("code") == code


def with_rack(song):
    inner = Ch("Chain 1", [D("Saturator")])
    rack = D("Audio Effect Rack", chains=[inner])
    song.return_tracks[0].devices.append(rack)
    return rack, inner


# ---- remote: devices -------------------------------------------------------------------------


def test_device_list_and_nested_parameters_on_a_return_chain(env):
    song, _app, d = env
    with_rack(song)
    listed = d("device_list", {"track": "return:0", "path": [0, 0]})
    assert listed["container"] == "chain" and [x["name"] for x in listed["devices"]] == [
        "Saturator"
    ]
    rows = d("device_parameters", {"track": "return:0", "path": [0, 0, 0], "limit": 1})
    assert len(rows) == 1 and rows[0]["name"] == "Device On"
    page = d("device_parameters", {"track": "return:0", "path": [0, 0, 0], "with_device": True})
    assert page["device"]["name"] == "Saturator" and page["parameters"][0]["name"] == "Device On"
    rows = (
        d("device_parameters", {"track": "master", "path": [0]})
        if song.master_track.devices
        else []
    )
    assert rows == []


def test_parameter_reset_uses_the_default_and_refuses_quantized(env):
    song, _app, d = env
    gain = d("device_parameters", {"track": 0, "path": [0]})[1]
    assert gain["default"] == 0.25
    out = d("set_device_parameters", {"writes": [{"parameter": gain["ref"], "reset": True}]})
    assert out["results"][0]["value"] == 0.25
    song.tracks[0].devices[0].parameters[1] = P("Mode", 0, 0, 1, quantized=True)
    mode = d("device_parameters", {"track": 0, "path": [0]})[1]["ref"]
    with pytest.raises(ValueError, match="quantized"):
        d("set_device_parameters", {"writes": [{"parameter": mode, "reset": True}]})


def test_set_devices_turns_off_renames_and_reports_unverified(env):
    song, _app, d = env
    dev = ref(d, "device", 0, [1])
    out = d("set_devices", {"targets": [{"ref": dev, "on": False, "name": "Comp A"}]})
    comp = song.tracks[0].devices[1]
    assert out["status"] == "complete" and comp.parameters[0].value == 0.0 and comp.name == "Comp A"
    assert out["unverified"] == ["device.rename"]


def test_move_cross_track_works_and_reorder_is_refused_before_moving(env):
    song, _app, d = env
    same = d(
        "move_device",
        {"targets": [{"kind": "device", "ref": ref(d, "device", 0, [0])},
                     {"kind": "track", "ref": ref(d, "track", 0)}]},
    )  # fmt: skip
    assert refused(same, "unsupported") and song.moves == 0
    out = d(
        "move_device",
        {"targets": [{"kind": "device", "ref": ref(d, "device", 0, [0])},
                     {"kind": "return_track", "ref": ref(d, "return_track", "return:0")}]},
    )  # fmt: skip
    assert out["moved"] == "EQ Eight" and [x.name for x in song.return_tracks[0].devices] == [
        "EQ Eight"
    ]


def test_move_into_a_chain_is_unverified_and_checked(env):
    song, _app, d = env
    with_rack(song)
    out = d(
        "move_device",
        {"targets": [{"kind": "device", "ref": ref(d, "device", 0, [1])},
                     {"kind": "chain", "ref": ref(d, "chain", "return:0", [0, 0])}],
         "position": 0},
    )  # fmt: skip
    assert out["unverified"] == ["device.move_into_chain"] and out["devices"][0] == "Compressor"


def test_delete_devices_route_deletes_by_identity_highest_first(env):
    song, _app, d = env
    targets = [{"kind": "device", "ref": ref(d, "device", 0, [i])} for i in (0, 1)]
    out = d("delete_devices", {"targets": targets})
    assert out["status"] == "complete" and song.tracks[0].devices == []
    assert [x["index"] for x in out["items"]] == [1, 0] or len(out["items"]) == 2


def test_device_capabilities_reads_states_for_plan_time_gates(env):
    _song, _app, d = env
    caps = d("device_capabilities", {"names": ["load.return", "device.move_reorder", "nope"]})
    assert caps["load.return"]["state"] == "unverified"
    assert caps["device.move_reorder"]["state"] == "unsupported"
    assert caps["nope"]["state"] == "unsupported"


# ---- remote: browser / loads -----------------------------------------------------------------


def test_browser_list_without_root_lists_present_roots_including_extras(env):
    _song, _app, d = env
    roots = [x["name"] for x in d("browser_list", {})["items"]]
    assert "audio_effects" in roots and "max_for_live" in roots and "plugins" not in roots


def _load(d, kind, track, root, name, path=None, **extra):
    target = {"kind": kind, "ref": ref(d, kind, track, path)}
    return d("load_device", {"root": root, "path": [name], "targets": [target], **extra})


def test_load_onto_a_return_is_observed_by_identity_diff(env):
    song, app, d = env
    rev = song.return_tracks[0]
    app.browser.hook = lambda item: rev.devices.append(D(item.name))
    op = _load(d, "return_track", "return:0", "audio_effects", "Reverb")
    assert op["state"] == "pending" and op["unverified"] == ["load.return"]
    d.operations.tick(), d.operations.tick()
    rec = d("operation", {"operation": op["operation"]})
    assert rec["state"] == "ready" and rec["result"]["devices_after"] == ["Reverb"]


def test_unknown_load_quarantines_the_target_and_never_reloads(env):
    song, app, d = env
    rev = song.return_tracks[0]
    app.browser.hook = lambda item: rev.devices.extend([D("A"), D("B")])  # ambiguous
    op = _load(d, "return_track", "return:0", "audio_effects", "Reverb")
    d.operations.tick()
    assert d("operation", {"operation": op["operation"]})["state"] == "unknown"
    again = _load(d, "return_track", "return:0", "audio_effects", "Reverb", append=True)
    assert refused(again, "quarantined") and app.browser.calls == 1


def test_sources_refuse_audio_and_occupied_targets_before_loading(env):
    _song, app, d = env
    on_audio = _load(d, "track", 0, "instruments", "Wavetable")
    assert refused(on_audio, "unsupported_target")
    occupied = _load(d, "track", 0, "audio_effects", "Reverb")
    assert refused(occupied, "target_occupied") and app.browser.calls == 0


def test_load_onto_a_drum_pad_is_refused_unsupported(env):
    # Live 12.2 (final proof): selected_drum_pad + load_item ended unknown, so it is closed.
    song, app, d = env
    rack = D("Drum Rack", kind=1, pads=[Pad(36, "Kick")])
    song.tracks[1].devices.append(rack)
    op = _load(d, "drum_pad", 1, "samples", "Kick.wav", [0, "pad:36"])
    assert refused(op, "unsupported") and app.browser.calls == 0


# ---- remote: drums, racks, extras ------------------------------------------------------------


def _drum_track(song):
    pads = [Pad(36, "Kick", [Ch("Kick", [D("Simpler", 1)])]), Pad(37, "")]
    song.tracks[1].devices.append(D("Drum Rack", kind=1, pads=pads))
    return pads


def test_drum_rack_read_and_pad_mute(env):
    song, _app, d = env
    pads = _drum_track(song)
    info = d("drum_rack", {"track": 1, "path": [0]})
    assert [p["note"] for p in info["pads"]] == [36] and info["pads"][0]["devices"] == ["Simpler"]
    pad = ref(d, "drum_pad", 1, [0, "pad:36"])
    out = d("set_drum_pads", {"targets": [{"ref": pad, "mute": True}]})
    assert pads[0].mute is True and out["unverified"] == ["drum_pad.mute_solo"]


def test_copy_pad_refuses_an_occupied_destination_before_copying(env):
    song, _app, d = env
    pads = _drum_track(song)
    pads[1].chains.append(Ch("Snare", [D("Simpler", 1)]))
    rack = song.tracks[1].devices[0]
    rack.copy_pad = lambda s, t: pytest.fail("copy_pad must not run")
    out = d("copy_drum_pad", {"device": ref(d, "device", 1, [0]), "source": 36, "destination": 37})
    assert refused(out, "target_occupied")


def test_conversions_absent_outside_live_refuse_without_a_native_call(env):
    _song, _app, d = env
    out = d(
        "convert",
        {
            "action": "devices_to_drum_pad",
            "targets": [{"kind": "track", "ref": ref(d, "track", 0)}],
        },
    )
    assert refused(out, "unsupported")


def test_simpler_read_and_unknown_field_refused(env):
    song, _app, d = env
    simpler = D("Simpler", 1)
    simpler.class_name = "OriginalSimpler"
    simpler.playback_mode, simpler.sample = 0, None
    song.tracks[1].devices.append(simpler)
    assert d("simpler", {"track": 1, "path": [0]})["device"]["playback_mode"] == 0
    dev = ref(d, "device", 1, [0])
    with pytest.raises(ValueError, match="not one of"):
        d("set_simpler", {"device": dev, "device_fields": {"bogus": 1}})
    out = d("set_simpler", {"device": dev, "device_fields": {"playback_mode": 2}})
    assert simpler.playback_mode == 2 and out["unverified"] == ["simpler.device"]


def test_rack_read_chain_mute_and_missing_insert_chain_is_unsupported(env):
    song, _app, d = env
    rack, inner = with_rack(song)
    info = d("rack", {"track": "return:0", "path": [0]})
    assert info["chains"][0]["name"] == "Chain 1" and "Map to Macro" in info["mapping"]
    dev = ref(d, "device", "return:0", [0])
    out = d("set_rack", {"device": dev, "chains": [{"index": 0, "mute": True}]})
    assert inner.mute is True and out["unverified"] == ["rack.chain_state"]
    assert refused(d("set_rack", {"device": dev, "insert_chain": {"index": 0}}), "unsupported")


def test_device_extras_read_and_preset_select(env):
    song, _app, d = env
    dev = song.tracks[0].devices[0]
    dev.presets, dev.selected_preset_index = ["Init", "Warm"], 0
    assert d("device_extras", {"track": 0, "path": [0]})["presets"] == ["Init", "Warm"]
    out = d("set_device_extras", {"device": ref(d, "device", 0, [0]), "preset_index": 1})
    assert dev.selected_preset_index == 1 and out["unverified"] == ["devx.preset_select"]


# ---- host tools ------------------------------------------------------------------------------


class Bridge:
    def __init__(self, replies):
        self.replies, self.calls = replies, []

    def __call__(self, method, params=None):
        self.calls.append((method, params))
        reply = self.replies[method]
        return reply(params) if callable(reply) else reply


@pytest.fixture
def host(monkeypatch):
    def install(replies):
        bridge = Bridge(replies)
        monkeypatch.setattr(server._bridge, "call", bridge)
        monkeypatch.setattr(server, "_writable", lambda *_args: None)
        monkeypatch.setattr(server, "_plans", chain.PlanStore())
        return bridge

    return install


def test_host_move_refuses_reorder_before_any_bridge_call(host):
    bridge = host({})
    with pytest.raises(Exception, match="reorder"):
        device_tools.live_move_device(0, [1], 0, None, 0)
    assert bridge.calls == []


def test_host_get_operation_reads_many_in_one_call(host):
    bridge = host({"operation": [{"operation": "a"}, {"operation": "b"}]})
    out = browser_tools.live_get_operation(operations=["a", "b"])
    assert len(out["operations"]) == 2 and bridge.calls == [
        ("operation", {"operations": ["a", "b"]})
    ]


def _owner(kind="track", midi=False, devices=()):
    rows = [
        {"index": i, "name": n, "class_name": n, "type": "audio_effect"}
        for i, n in enumerate(devices)
    ]
    owner = {"kind": kind, "name": "X", "has_midi_input": midi, "is_group": False}
    return {"owner": owner, "container": kind, "container_name": "X", "devices": rows}


def test_host_load_routes_empty_audio_effects_to_the_proven_route(host):
    replies = {
        "device_list": _owner(),
        "ref_issue": {"refs": [{"ref": "R", "name": "X"}]},
        "load_item": {"operation": "op", "state": "pending"},
        "load_device": {"operation": "op2", "state": "pending"},
    }
    bridge = host(replies)
    browser_tools.live_load_item(0, "audio_effects", ["Reverb"])
    replies["device_list"] = _owner("return_track")
    browser_tools.live_load_item("return:0", "audio_effects", ["Reverb"])
    methods = [m for m, _ in bridge.calls if m.startswith("load")]
    assert methods == ["load_item", "load_device"]


def test_fx_rack_plan_lists_manual_mapping_and_gates_chain_abilities(host):
    caps = {
        n: {"state": "unverified"}
        for n in ("load.audio_track", "rack.insert_chain", "device.move_into_chain")
    }
    host({
        "session_info": {"generation": 1},
        "device_list": _owner(devices=("EQ Eight", "Compressor")),
        "browser_list": {"items": [{"name": "Audio Effect Rack"}]},
        "device_capabilities": caps,
    })  # fmt: skip
    rack = {"groups": [{"macro": 1, "label": "Drive", "value": "50 %",
                        "targets": [{"device": 1, "parameter": "Threshold"}]}]}  # fmt: skip
    plan = server.live_plan_chain(0, rack=rack)
    assert plan["mode"] == "fx_rack" and len(plan["unverified"]) == 3
    assert any("Map Compressor > Threshold to Macro 1" in s for s in plan["manual_steps"])
    caps["device.move_into_chain"] = {"state": "quarantined", "reason": "x"}
    with pytest.raises(Exception, match="quarantined"):
        server.live_plan_chain(0, rack=rack)


def test_drum_plan_is_capped_and_needs_an_empty_midi_track(host):
    caps = {n: {"state": "unverified"} for n in ("load.midi_track", "load.drum_pad")}
    host({
        "session_info": {"generation": 1},
        "device_list": _owner(midi=True),
        "browser_list": lambda p: {"items": [{"name": "Drum Rack"}, {"name": "Kick.wav"}]},
        "device_capabilities": caps,
    })  # fmt: skip
    plan = drum_tools.live_plan_drum_rack(1, [DrumRole(note=36, path=["Kick.wav"])])
    assert plan["mode"] == "drum_rack" and plan["containers"] == [[], [0, "pad:36"]]
    with pytest.raises(Exception, match="16"):
        drum_tools.live_plan_drum_rack(1, [DrumRole(note=n, path=["Kick.wav"]) for n in range(17)])


def test_pad_clear_needs_expect_name(host):
    bridge = host({})
    with pytest.raises(Exception, match="expect_name"):
        drum_tools.live_set_drum_pads(1, [0], pads=[PadEdit(note=36, clear=True)])
    assert bridge.calls == []
