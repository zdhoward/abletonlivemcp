"""Production tool surface and plan-then-build contract, against a scripted bridge boundary.

`Bridge` below is a project-owned stub of `BridgeClient.call`: it answers reads, replays the
Remote Script's operation/refusal result shapes and logs every call, so a test can show that
nothing was called after a stop. It is not a fake Live and does no DSP.
"""

import asyncio
import json
import subprocess
import sys

import pytest

from abletonlivemcp import chain, server
from abletonlivemcp.bridge import BridgeError
from abletonlivemcp.chain_presets import PRESETS
from abletonlivemcp.models_control import NewTrack
from abletonlivemcp.server import ToolFailure
from abletonlivemcp.tools import chain as chain_tools

REMOVED = {
    "als_summary",
    "als_usage_index",
    "classify_samples",
    "classify_plugins",
    "judge_status",
    "knowledge_list",
    "knowledge_search",
    "knowledge_read",
    "stock_equivalent_for_gear",
    "live_build_role_chain",
    "live_set_device_parameter",
    "live_tracks",
    "live_session_info",
    "live_create_track",
    "live_set_track",
    "live_fire_clip",
}
DUMMY_ENV = {
    "ABLETONLIVEMCP_KNOWLEDGE": ".",
    "OPENROUTER_API_KEY": "not-a-real-key",
    "ABLETONLIVEMCP_JUDGE": "rules",
}


def _tools():
    return {t.name: t for t in asyncio.run(server.mcp.list_tools())}


def test_production_surface_has_no_deferred_tools_even_with_their_env_vars(tmp_path):
    code = (
        "import asyncio, json, sys\n"
        "from abletonlivemcp import server\n"
        "names = sorted(t.name for t in asyncio.run(server.mcp.list_tools()))\n"
        "print(json.dumps({'names': names}))\n"
    )
    env = {**__import__("os").environ, **DUMMY_ENV, "ABLETONLIVEMCP_KNOWLEDGE": str(tmp_path)}
    out = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True
    )
    seen = json.loads(out.stdout.strip().splitlines()[-1])
    assert not REMOVED & set(seen["names"])
    assert {"live_plan_chain", "live_build_chain", "live_get_operation"} <= set(seen["names"])


def test_annotations_mark_reads_mutations_and_creates_honestly():
    tools = _tools()
    for name in ("live_get_tracks", "live_plan_chain", "live_get_operation", "live_browser_list"):
        a = tools[name].annotations
        assert a.read_only_hint is True and a.destructive_hint is False, name
    for name in ("live_create_tracks", "live_create_scenes", "live_load_item", "live_build_chain"):
        a = tools[name].annotations
        assert a.read_only_hint is False and a.idempotent_hint is False, name
    a = tools["live_set_device_parameters"].annotations
    assert a.read_only_hint is False and a.destructive_hint is True and a.idempotent_hint is True
    schema = json.dumps(tools["live_set_device_parameters"].input_schema)
    assert '"raw"' in schema and "settings" in schema
    assert "plan_id" in tools["live_build_chain"].input_schema["properties"]


def test_presets_are_well_formed_role_stages():
    for preset in PRESETS.values():
        assert 1 <= len(preset["stages"]) <= 12
        for stage in preset["stages"]:
            assert stage["role"] and stage["intent"] and "device" not in stage


class Bridge:
    """Scripted `BridgeClient.call`. `script` maps a method name to a list of replies consumed
    in order (an Exception is raised); the last one repeats."""

    def __init__(self, **script):
        self.calls = []
        self.script = script
        self.generation = 7
        self.devices = []  # class names on the target track
        self.write_value = None  # force the value a write reads back as (off target)
        self.write_display = None

    def methods(self):
        return [m for m, _ in self.calls]

    def call(self, method, params=None):
        self.calls.append((method, params))
        replies = self.script.get(method)
        if replies:
            reply = replies.pop(0) if len(replies) > 1 else replies[0]
            if isinstance(reply, Exception):
                raise reply
            if method == "load_item" and "refused" not in reply:
                self.devices.append(params["path"][-1])  # a scripted load still lands on the track
            return reply
        return getattr(self, f"_{method}")(params)

    def _session_info(self, _p):
        return {"generation": self.generation}

    def _get_tracks(self, _p):
        devices = [{"name": n, "class_name": n} for n in self.devices]
        row = {"index": 0, "name": "Vox", "has_midi_input": False, "devices": devices}
        return {"track_count": 1, "return_count": 0, "tracks": [row]}

    def _device_list(self, _p):
        rows = [
            {"index": i, "name": n, "class_name": n, "type": "audio_effect"}
            for i, n in enumerate(self.devices)
        ]
        owner = {"kind": "track", "name": "Vox", "has_midi_input": False, "is_group": False}
        return {"owner": owner, "container": "track", "container_name": "Vox", "devices": rows}

    def _ref_issue(self, p):
        return {"refs": [{"ref": "trk", "name": "Vox"} for _ in p["targets"]]}

    def _browser_list(self, _p):
        return {"items": [{"name": n} for n in ("Compressor", "EQ Eight", "Reverb")]}

    def _lease_acquire(self, _p):
        return {"lease": "LEASE", "ttl": 60.0, "generation": self.generation}

    def _lease_release(self, _p):
        return {"released": True}

    def _load_item(self, p):
        self.devices.append(p["path"][-1])
        return {"operation": f"op{len(self.devices)}", "state": "pending"}

    def _operation(self, p):
        return {
            "operation": p["operation"],
            "state": "ready",
            "devices_after": list(self.devices),
        }

    def _device_parameters(self, _p):
        param = {
            "index": 0, "ref": "p0", "name": "Level", "value": 0.2, "min": 0.0, "max": 1.0,
            "is_quantized": False, "is_enabled": True, "display": "-48.0 dB",
        }  # fmt: skip
        return [param]

    def _sample_parameters(self, p):
        shown = [[f"{-60 + 60 * v:.1f} dB" for v in r["values"]] for r in p["requests"]]
        return {"results": [{"name": "Level", "displays": d} for d in shown]}

    def _set_device_parameters(self, p):
        value = self.write_value if self.write_value is not None else 0.5
        display = self.write_display or f"{-60 + 60 * value:.1f} dB"
        return {
            "results": [{"name": "Level", "value": value, "display": display}] * len(p["writes"])
        }


def _wire(monkeypatch, tmp_path) -> "Bridge":
    bridge = Bridge()
    monkeypatch.setattr(server._bridge, "call", bridge.call)
    monkeypatch.setattr(server, "_writable", lambda *_args: None)
    monkeypatch.setattr(chain, "POLL", 0)
    monkeypatch.setenv("ABLETONLIVEMCP_PREFS", str(tmp_path / "none.json"))
    return bridge


@pytest.fixture
def live(monkeypatch, tmp_path):
    bridge = _wire(monkeypatch, tmp_path)
    monkeypatch.setattr(server, "_plans", chain.PlanStore())
    return bridge


def test_plan_then_build_works_on_the_module_state_the_server_starts_with(monkeypatch, tmp_path):
    """Regression: a confirmation cache once rebound ``server._plans`` to a dict at import, so
    every plan/build failed in production while the store-replacing fixture hid it."""
    assert type(server._plans) is chain.PlanStore  # as imported, nothing replaced
    live = _wire(monkeypatch, tmp_path)
    live.write_value = 0.5
    plan = server.live_plan_chain(0, [{"device": "Compressor", "params": {"Level": "-30 dB"}}])
    assert server.live_build_chain(plan["plan_id"])["status"] == "complete"


def _plan(*stages):
    return server.live_plan_chain(0, list(stages))


RAW = {"device": "Compressor", "params": {"Level": {"raw": 0.5}}}
RAW2 = {"device": "Reverb", "params": {"Level": {"raw": 0.5}}}


def test_partial_receipt_when_the_second_load_is_refused_and_nothing_follows(live):
    plan = _plan(RAW, RAW2, {"device": "EQ Eight"})
    first = {"operation": "op1", "state": "pending"}
    refused = {"refused": True, "applied": False, "code": "append_unverified", "message": "no"}
    live.script["load_item"] = [first, refused]
    live.script["operation"] = [
        {"operation": "op1", "state": "ready", "devices_after": ["Compressor"]}
    ]
    receipt = server.live_build_chain(plan["plan_id"])
    assert receipt["status"] == "partial" and receipt["intent_fulfilled"] is False
    assert (receipt["completed"], receipt["stopped_at"]) == ([0], 1)
    assert receipt["stop_reason"] == "append_unverified"
    s0, s1, s2 = receipt["stages"]
    assert s0["outcome"] == "applied" and s0["params"][0]["exact"] is True
    assert s0["params"][0]["original"] == {"value": 0.2, "display": "-48.0 dB"}
    assert s1["outcome"] == "not_applied" and s2["reason"] == "not_attempted"
    methods = live.methods()
    assert methods.count("load_item") == 2  # the refused one is the last load ever attempted
    assert methods[-2:] == ["load_item", "lease_release"]
    loads = [p for m, p in live.calls if m == "load_item"]
    assert loads[0]["lease"] == "LEASE" and loads[1]["after"] == "op1"


def test_unknown_load_outcome_stops_without_retry_or_fallback(live):
    plan = _plan(RAW, RAW2, {"device": "EQ Eight"})
    lost = BridgeError("Timeout", "no reply", may_have_applied=True)
    live.script["load_item"] = [{"operation": "op1", "state": "pending"}, lost]
    live.script["operation"] = [
        {"operation": "op1", "state": "ready", "devices_after": ["Compressor"]}
    ]
    receipt = server.live_build_chain(plan["plan_id"])
    assert receipt["status"] == "partial" and receipt["stages"][1]["outcome"] == "unknown"
    assert receipt["unknown"] == ["stage 1: Timeout"]
    assert live.methods().count("load_item") == 2


def test_pending_load_that_never_resolves_is_unknown_not_absent(live, monkeypatch):
    plan = _plan(RAW)
    ticks = iter(range(0, 1000, 10))
    monkeypatch.setattr(chain, "LOAD_WAIT", 25.0)
    live.script["operation"] = [{"operation": "op1", "state": "pending"}]
    _mode, planned = server._plans.claim(plan["plan_id"])
    receipt = chain.execute(
        server._call, planned, "trk", sleep=lambda _s: None, clock=lambda: next(ticks)
    )
    assert receipt.status == "pending" and receipt.stages[0].outcome == "unknown"
    assert live.methods().count("load_item") == 1


def test_off_target_raw_write_is_reported_and_stops_the_chain(live):
    live.write_value = 0.9  # Live stored something other than the 0.5 asked for
    plan = _plan(RAW, RAW2)
    receipt = server.live_build_chain(plan["plan_id"])
    p = receipt["stages"][0]["params"][0]
    assert (p["raw"], p["exact"], p["off_target"], p["actual_raw"]) == (True, False, True, 0.9)
    assert receipt["status"] == "partial" and receipt["stop_reason"] == "off_target"
    assert receipt["stages"][1]["reason"] == "not_attempted"
    assert live.methods().count("load_item") == 1


def test_off_target_display_write_is_reported_not_claimed_exact(live):
    live.write_display = "-12.0 dB"
    plan = _plan({"device": "Compressor", "params": {"Level": "-18 dB"}})
    receipt = server.live_build_chain(plan["plan_id"])
    p = receipt["stages"][0]["params"][0]
    assert (p["raw"], p["exact"], p["actual"]) == (False, False, "-12.0 dB")
    assert receipt["status"] == "partial" and receipt["intent_fulfilled"] is False


def test_complete_build_is_exact_and_fulfilled(live):
    plan = _plan({"device": "Compressor", "params": {"Level": "-30 dB"}})
    live.write_value = 0.5
    receipt = server.live_build_chain(plan["plan_id"])
    assert receipt["status"] == "complete" and receipt["intent_fulfilled"] is True
    assert receipt["stages"][0]["params"][0]["exact"] is True


def test_plan_is_consumed_once_expires_and_refuses_a_changed_target(live, monkeypatch):
    now = [0.0]
    monkeypatch.setattr(server, "_plans", chain.PlanStore(clock=lambda: now[0]))
    plan = _plan(RAW)
    first = server.live_build_chain(plan["plan_id"])
    again = server.live_build_chain(plan["plan_id"])
    assert again["already_built"] is True and again["status"] == first["status"]
    assert live.methods().count("load_item") == 1  # reuse never starts a second build

    live.devices.clear()
    changed = _plan(RAW2)
    live.generation += 1  # the Set changed after planning
    with pytest.raises(ToolFailure, match="changed since planning"):
        server.live_build_chain(changed["plan_id"])
    live.generation -= 1
    assert server.live_build_chain(changed["plan_id"])["status"] == "complete"  # was not consumed

    live.devices.clear()
    stale = _plan(RAW)
    now[0] += chain.PLAN_TTL + 1
    with pytest.raises(ToolFailure, match="unknown or expired plan_id"):
        server.live_build_chain(stale["plan_id"])
    with pytest.raises(ToolFailure, match="unknown or expired plan_id"):
        server.live_build_chain("nope")


def test_occupied_target_is_refused_at_plan_time(live):
    live.devices.append("Compressor")
    with pytest.raises(ToolFailure, match="must be empty"):
        _plan(RAW)


def test_omitted_intent_cannot_become_complete_success(live, monkeypatch):
    def resolver(call, stages, prefs):
        stage = {"device": "Compressor", "params": {}}
        return {"stages": [stage], "report": [{"role": "compressor", "notes": ["x: 'a' skipped"]}]}

    monkeypatch.setattr(chain_tools, "plan_chain", resolver)
    plan = _plan({"role": "compressor", "intent": {"a": 1}})
    assert plan["intent_complete"] is False and plan["stages"][0]["omitted"]
    with pytest.raises(ToolFailure, match="omits intent"):
        server.live_build_chain(plan["plan_id"])
    assert live.methods().count("load_item") == 0
    receipt = server.live_build_chain(plan["plan_id"], accept_omissions=True)
    assert receipt["status"] == "complete" and receipt["intent_fulfilled"] is False
    assert receipt["omitted"]


def test_unsupported_roots_and_unknown_devices_are_refused_at_plan_time(live):
    with pytest.raises(ToolFailure, match="can be built"):
        _plan({"device": "Clip", "root": "clips", "path": ["Clip"]})
    with pytest.raises(ToolFailure, match="empty MIDI"):  # a source never lands on audio
        _plan({"device": "Wavetable", "root": "instruments", "path": ["Wavetable"]})
    with pytest.raises(ToolFailure, match="not in Live"):
        _plan({"device": "Pultec"})


def test_policy_refusal_and_bridge_refusal_are_errors_that_say_not_applied(live, monkeypatch):
    monkeypatch.undo()  # back to the real policy check, with no readable private config
    monkeypatch.setattr(server, "load_config", lambda: {"read_only": True})
    monkeypatch.setattr(server._bridge, "call", live.call)
    with pytest.raises(ToolFailure, match=r"read_only: .*\(not applied\)"):
        server.live_create_tracks([NewTrack(kind="audio")])
    assert live.calls == []  # refused before any bridge call

    monkeypatch.setattr(server, "_writable", lambda *_args: None)
    live.script["session_info"] = [{"generation": live.generation}]
    live.script["create_tracks"] = [
        {"refused": True, "applied": False, "code": "stale_generation", "message": "moved"}
    ]
    with pytest.raises(ToolFailure, match=r"refused:stale_generation: moved \(not applied\)"):
        server.live_create_tracks([NewTrack(kind="audio")])
    live.script["create_tracks"] = [BridgeError("Timeout", "lost", may_have_applied=True)]
    with pytest.raises(ToolFailure, match="may have been applied"):
        server.live_create_tracks([NewTrack(kind="audio")])


def test_mutations_are_serialized_by_one_lock(live, monkeypatch):
    monkeypatch.setattr(server, "LOCK_WAIT", 0.01)
    with server._mutation_lock:
        with pytest.raises(ToolFailure, match="busy: another mutation"):
            server.live_create_tracks([NewTrack(kind="audio")])
    assert "create_tracks" not in live.methods()


def test_untrusted_names_are_wrapped_and_references_are_not_leaked(live):
    out = server.live_get_tracks()
    assert out["provenance"] == "live_object_text_untrusted"
    row = out["data"]["tracks"][0]
    assert "ref" not in row and row["name"] == "Vox"
