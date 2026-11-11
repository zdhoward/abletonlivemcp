"""Automate Basic's existing Arrangement music without writing MIDI or saving the Set.

python scripts/build_buildup_demo.py [--shape 0.3] [--fire]
Optional --create-notes --pitch-map FILE creates a Session-only sketch in empty slots.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
import wave
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROLES = {"PAD": "PAD", "KICK": "Core", "HATS": "Hats", "BASS": "MainBass"}
BUS = "Buildup FX"
CARRIERS = ("ALMCP Buildup automation", "ALMCP Drop reset")
PLUGINS = {"Wider": ["VST3", "Infected Mushroom", "Wider"],
           "GHOST//PUMP": ["VST3", "ZXAudio", "GHOST//PUMP"]}


class Live:
    def __init__(self, session):
        self.session = session

    async def call(self, tool, args=None):
        result = await self.session.call_tool(tool, args or {})
        text = "".join(getattr(c, "text", "") for c in result.content)
        if getattr(result, "is_error", getattr(result, "isError", False)):
            raise RuntimeError(f"{tool}: {text[:700]}")
        data = json.loads(text)
        data = data.get("data", data) if data.get("provenance") else data
        if data.get("status") in ("partial", "failed"):
            raise RuntimeError(f"{tool} incomplete: {data}")
        return data


def step(text):
    print(f"- {text}", flush=True)


async def inventory(live):
    rows = (await live.call("live_get_tracks"))["tracks"]
    names = {r["name"]: r["track"] for r in rows}
    if len(names) != len(rows):
        raise RuntimeError("duplicate track names; refusing ambiguous targets")
    return names


async def ensure_effect(live, track, name):
    devices = (await live.call("live_get_device_parameters", {"track": track}))["devices"]
    matches = [d for d in devices if d["name"] == name]
    if not matches:
        if name in PLUGINS:
            found = await live.call("live_browser_search", {"root": "plugins", "query": name})
            if not any(r["path"] == PLUGINS[name] for r in found["results"]):
                raise RuntimeError(f"required plugin unavailable: {name}; no substitute")
            loaded = await live.call("live_load_item", {"track": track, "root": "plugins",
                "path": PLUGINS[name], "append": True})
            for _ in range(20):
                op = await live.call("live_get_operation", {"operation": loaded["operation"]})
                if op["state"] == "ready":
                    break
                if op["state"] != "pending":
                    raise RuntimeError(f"inspect plugin load: {op}")
            else:
                raise RuntimeError("plugin still pending; do not repeat the load")
        else:
            plan = await live.call("live_plan_chain", {"track": track, "append": True,
                "stages": [{"device": name, "root": "audio_effects"}]})
            await live.call("live_build_chain", {"plan_id": plan["plan_id"]})
        devices = (await live.call("live_get_device_parameters", {"track": track}))["devices"]
        matches = [d for d in devices if d["name"] == name]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {name}: {devices}")
    return matches[0]["index"]


def silent_file(tempo):
    path = Path(tempfile.gettempdir()) / "abletonlivemcp-demo" / "automation-carrier.wav"
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        with wave.open(str(path), "wb") as f:
            f.setparams((1, 2, 44100, 0, "NONE", "not compressed"))
            f.writeframes(b"\0\0" * round(16 * 60 / tempo * 44100))
    return str(path)


async def create_requested_notes(live, names, pitch_map, scene):
    """Explicit pitches only, empty Session slots only, never replace existing notes."""
    if not isinstance(pitch_map, dict) or not pitch_map or set(pitch_map) - set(ROLES):
        raise ValueError(f"pitch map must contain roles from {list(ROLES)}")
    clips = []
    for role, pitches in pitch_map.items():
        if not isinstance(pitches, list) or not pitches or any(
            type(p) is not int or not 0 <= p <= 127 for p in pitches
        ):
            raise ValueError(f"{role}: supply MIDI integers 0..127")
        clips.append({"track": names[ROLES[role]], "scene": scene, "length": 16,
            "name": f"Explicit {role} sketch", "notes": [
                {"pitch": pitches[b % len(pitches)], "start_time": b,
                 "duration": 0.25, "velocity": 90} for b in range(16)]})
    await live.call("live_create_clips", {"clips": clips, "if_exists": "error"})


async def build(live, args):
    state = await live.call("live_get_session", {"include": ["cues", "transport"]})
    cues = {c["name"]: c["time"] for c in state["cues"]}
    if cues.get("Intro") != 0 or cues.get("DROP") != 16:
        raise RuntimeError("Basic must have Intro(0) and DROP(16)")
    names = await inventory(live)
    if any(n not in names for n in [*ROLES.values(), "INSTRUMENTAL",
                                    "C-INSTR Verb", "D-INSTR Delay"]):
        raise RuntimeError("expected Basic tracks and instrument returns")
    await live.call("live_transport", {"action": "stop"})
    music = [names[n] for n in ROLES.values()]
    music_state = await live.call("live_get_arrangement", {
        "tracks": music, "include": ["clips"]})
    if not any(r["clips"] for r in music_state["tracks"]):
        raise RuntimeError("supply existing Arrangement music first")
    if args.create_notes:
        await create_requested_notes(live, names, args.pitch_map, args.note_scene)
    if BUS not in names:
        await live.call("live_create_tracks", {"tracks": [{"kind": "audio", "name": BUS}]})
        names = await inventory(live)
    bus = names[BUS]
    existing = await live.call("live_get_clips", {"track": bus})
    for c in existing["clips"]:
        if c["scene"] in (0, 1) and c["name"] != CARRIERS[c["scene"]]:
            raise RuntimeError("bus slot contains an unrelated clip")
    timeline = await live.call("live_get_arrangement", {"tracks": [bus], "include": ["clips"]})
    if any(c["name"] not in CARRIERS for c in timeline["tracks"][0]["clips"]):
        raise RuntimeError("bus timeline contains unrelated clips")
    await live.call("live_create_clips", {"if_exists": "skip", "clips": [
        {"track": bus, "scene": i, "kind": "audio", "file": silent_file(state["tempo"]),
         "name": name} for i, name in enumerate(CARRIERS)]})
    await live.call("live_set_clips", {"targets": [
        {"clip": {"track": bus, "scene": i}, "warping": True,
         "loop": [0, 16], "markers": [0, 16]} for i in (0, 1)]})
    slots = {n: await ensure_effect(live, bus, n)
             for n in ("Auto Filter", "Wider", "GHOST//PUMP", "Reverb", "Delay")}
    # Static settings precede automation. Never set these envelope targets manually afterward.
    await live.call("live_set_device_parameters", {"track": bus,
        "path": [slots["Auto Filter"]], "settings": [
            {"parameter": "Type", "value": "High-pass"},
            {"parameter": "Resonance", "value": {"raw": 0.15}}]})
    await live.call("live_set_device_parameters", {"track": bus,
        "path": [slots["GHOST//PUMP"]], "settings": [
            {"parameter": "Boost", "value": {"raw": 0}}]})
    await live.call("live_set_device_parameters", {"track": bus,
        "path": [slots["Reverb"]], "settings": [
            {"parameter": "Decay Time", "value": {"raw": 0.6}}]})
    await live.call("live_set_device_parameters", {"track": bus,
        "path": [slots["Delay"]], "settings": [
            {"parameter": "Feedback", "value": {"raw": 0.3}}]})
    targets = [({"device": [slots["Auto Filter"]], "parameter": "Frequency"}, 0.88),
               ({"device": [slots["Reverb"]], "parameter": "Dry/Wet"}, 1),
               ({"device": [slots["Delay"]], "parameter": "Dry/Wet"}, 0.4)]
    for name, parameter, end in (("Wider", "Amount", 0.75),
                                  ("GHOST//PUMP", "Pump A", 1),
                                  ("GHOST//PUMP", "Pump B", 1)):
        params = await live.call("live_get_device_parameters", {
            "track": bus, "path": [slots[name]], "response_format": "detailed"})
        if any(p["name"] == parameter and p["is_enabled"] for p in params["parameters"]):
            targets.append(({"device": [slots[name]], "parameter": parameter}, end))
        else:
            step(f"MANUAL: {name}: Configure {parameter} in Live, then rerun; no substitute")
    edits = []
    for selector, end in targets:
        edits += [{"clip": {"track": bus, "scene": 0}, "parameter": selector,
                   "clear": True, "points": [{"time": 0, "value": 0},
                       {"time": 8, "value": end * args.shape}, {"time": 16, "value": end}]},
                  {"clip": {"track": bus, "scene": 1}, "parameter": selector,
                   "clear": True, "steps": [{"time": 0, "length": 16, "value": 0}]}]
    for name in ("Reverb", "Delay"):
        for scene in (0, 1):
            edits.append({"clip": {"track": bus, "scene": scene},
                "parameter": {"device": [slots[name]], "parameter": "Device On"},
                "clear": True, "steps": [{"time": 0, "length": 16, "value": 1-scene}]})
    for send in (2, 3):
        for scene in (0, 1):
            edits.append({"clip": {"track": bus, "scene": scene},
                "parameter": {"mixer": "send", "send": send}, "clear": True,
                "steps": [{"time": 0, "length": 16, "value": 0}]})
    await live.call("live_set_automation", {"targets": edits})
    await live.call("live_create_arrangement_clips", {"clips": [
        {"track": bus, "kind": "from_session", "scene": i,
         "start": i * 16, "replace": True} for i in (0, 1)]})
    await live.call("live_set_tracks", {"targets": [
        {"track": bus, "monitoring": "in", "input_routing": {"type": "No Input"},
         "output_routing": {"type": "Main"}},
        {"track": names["INSTRUMENTAL"], "output_routing": {"type": BUS}}]})
    await live.call("live_transport", {"action": "back_to_arranger"})
    await live.call("live_set_session", {"loop": {"on": False}})
    await live.call("live_transport", {"action": "jump_to", "beats": 0})
    if args.fire:
        await live.call("live_transport", {"action": "play"})
    print("Ready for preview: airy buildup 0-16, fully wet reverb, FX cut at DROP(16). "
          "Original MIDI preserved; Basic remains unsaved.", flush=True)


async def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fire", action="store_true")
    parser.add_argument("--shape", type=float, default=0.3,
                        help="amount fraction at beat 8 (0..1), using three linear points")
    parser.add_argument("--create-notes", action="store_true")
    parser.add_argument("--pitch-map", type=Path, help='JSON file, e.g. {"HATS":[80,72]}')
    parser.add_argument("--note-scene", type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.shape <= 1:
        parser.error("--shape must be 0..1")
    if args.create_notes != bool(args.pitch_map):
        parser.error("note creation requires both --create-notes and --pitch-map")
    if args.pitch_map:
        args.pitch_map = json.loads(args.pitch_map.read_text(encoding="utf-8-sig"))
    params = StdioServerParameters(command=sys.executable, args=["-m", "abletonlivemcp.server"])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        await build(Live(session), args)


if __name__ == "__main__":
    asyncio.run(main())
