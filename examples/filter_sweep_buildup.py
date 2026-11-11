"""Make a 16-beat filter-sweep buildup on any Set, using the MCP over stdio.

    python examples/filter_sweep_buildup.py [--length 16] [--play]

It adds one new MIDI track ("Buildup Sweep"), puts an Auto Filter on it, writes a
16th-note clip into scene 0 and automates the filter Frequency from closed to open across
the clip. Existing tracks and clips are never touched. Live must be running with the
bridge installed and writes enabled. Nothing is saved; undo with Cmd/Ctrl+Z in Live.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TRACK_NAME = "Buildup Sweep"


class Live:
    """Thin wrapper: call a tool, return its JSON data, raise on any error or partial result."""

    def __init__(self, session: ClientSession):
        self.session = session

    async def call(self, tool: str, args: dict | None = None) -> dict:
        result = await self.session.call_tool(tool, args or {})
        text = "".join(getattr(c, "text", "") for c in result.content)
        if getattr(result, "isError", False):
            raise RuntimeError(f"{tool}: {text[:500]}")
        data = json.loads(text)
        data = data.get("data", data) if data.get("provenance") else data
        if data.get("status") in ("partial", "failed"):
            raise RuntimeError(f"{tool} incomplete: {data}")
        return data


async def build(live: Live, length: int, play: bool) -> None:
    tracks = (await live.call("live_get_tracks"))["tracks"]
    if any(t["name"] == TRACK_NAME for t in tracks):
        raise RuntimeError(f"a track named {TRACK_NAME!r} already exists; rename or delete it")

    await live.call("live_create_tracks", {"tracks": [{"kind": "midi", "name": TRACK_NAME}]})
    tracks = (await live.call("live_get_tracks"))["tracks"]
    track = next(t["track"] for t in tracks if t["name"] == TRACK_NAME)

    plan = await live.call("live_plan_chain", {"track": track, "append": True,
        "stages": [{"device": "Auto Filter", "root": "audio_effects"}]})
    await live.call("live_build_chain", {"plan_id": plan["plan_id"]})
    devices = (await live.call("live_get_device_parameters", {"track": track}))["devices"]
    slot = next(d["index"] for d in devices if d["name"] == "Auto Filter")

    await live.call("live_set_device_parameters", {"track": track, "path": [slot],
        "settings": [{"parameter": "Type", "value": "High-pass"}]})

    notes = [{"pitch": 60, "start_time": i * 0.25, "duration": 0.2, "velocity": 70 + i}
             for i in range(length * 4)]
    await live.call("live_create_clips", {"if_exists": "error", "clips": [
        {"track": track, "scene": 0, "length": length, "name": TRACK_NAME, "notes": notes}]})

    await live.call("live_set_automation", {"targets": [
        {"clip": {"track": track, "scene": 0},
         "parameter": {"device": [slot], "parameter": "Frequency"},
         "clear": True,
         "points": [{"time": 0, "value": 0.0},
                    {"time": length / 2, "value": 0.3},
                    {"time": length, "value": 1.0}]}]})

    if play:
        await live.call("live_launch", {"action": "fire",
            "targets": [{"kind": "slot", "track": track, "scene": 0}]})
    print(f"Done: track {track} ({TRACK_NAME}) sweeps the high-pass open over {length} beats.")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--length", type=int, default=16, help="clip length in beats")
    parser.add_argument("--play", action="store_true", help="launch the clip afterwards")
    args = parser.parse_args()
    params = StdioServerParameters(command=sys.executable, args=["-m", "abletonlivemcp.server"])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        await build(Live(session), args.length, args.play)


if __name__ == "__main__":
    asyncio.run(main())
