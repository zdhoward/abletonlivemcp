"""Demo: build an EDM buildup at Intro (0) and drop at DROP (16) on the Arrangement.

    python scripts/build_buildup_demo.py [--fire]

Needs Live running with the Remote Script and ``"read_only": false`` in the private bridge config.
Safe to re-run on disposable Basic: replaces the eight Session clips and destination clips
wholly within beats 0..32, reuses effects, and rewrites automation. Never saves the Set.

Scene 0 "buildup" (16 beats): PAD chords swell, kick builds, hats go 8ths -> 16ths, bass enters
on bar 3, and an Auto Filter high-pass on PAD and Hats opens by clip automation.
Scene 1 "drop" (16 beats): full chords, four-on-the-floor kick, off-beat hats, driving bass.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROLES = {"PAD": "PAD", "KICK": "Core", "HATS": "Hats", "BASS": "MainBass"}  # role -> track name
FILTERED = ("PAD", "HATS")
FILTER = "Auto Filter"
BARS = 4  # both clips are 16 beats
CHORDS = [(55, 58, 62), (51, 55, 58), (58, 62, 65), (53, 57, 60)]  # Gm Eb Bb F
ROOTS = [31, 27, 34, 29]  # G Eb Bb F, one per bar


def note(pitch, start, length, velocity):
    return {"pitch": pitch, "start_time": start, "duration": length, "velocity": velocity}


def ramp(a, b, i, n):
    return round(a + (b - a) * i / max(n - 1, 1))


def chords(velocities):
    return [note(p, 4 * i, 3.9, velocities[i]) for i, chord in enumerate(CHORDS) for p in chord]


def patterns() -> dict[tuple[str, int], tuple[str, list]]:
    """(role, scene) -> (clip name, notes)."""
    hats = [note(42, i * 0.5, 0.2, ramp(50, 62, i, 8)) for i in range(8)]
    hats += [note(42, 4 + i * 0.5, 0.2, 62) for i in range(8)]
    hats += [note(42, 8 + i * 0.25, 0.15, ramp(74, 120, i, 32)) for i in range(32)]
    return {
        ("PAD", 0): ("Buildup Pad", chords([55, 68, 84, 100])),
        ("KICK", 0): (
            "Buildup Kick",
            [note(36, b, 0.25, [80, 88, 98, 110][b // 4]) for b in range(15)],
        ),
        ("HATS", 0): ("Buildup Hats", hats),
        ("BASS", 0): (
            "Buildup Bass",
            [note(31, 8 + i * 0.5, 0.4, ramp(70, 115, i, 16)) for i in range(16)],
        ),
        ("PAD", 1): ("Drop Pad", chords([95] * BARS)),
        ("KICK", 1): ("Drop Kick", [note(36, b, 0.25, 120) for b in range(16)]),
        ("HATS", 1): ("Drop Hats", [note(42, b + 0.5, 0.25, 105) for b in range(16)]),
        ("BASS", 1): ("Drop Bass", [note(ROOTS[b // 4], b + 0.5, 0.45, 115) for b in range(16)]),
    }


# Filter sweep on raw Frequency (0..1, logarithmic): slow rise over bars 1-3, steep in bar 4.
SWEEP = [
    {"start": 0, "end": 12, "from": 0.1, "to": 0.5, "steps": 24},
    {"start": 12, "end": 16, "from": 0.5, "to": 0.88, "steps": 16},
]


class Live:
    def __init__(self, session: ClientSession):
        self.session = session

    async def call(self, tool: str, args: dict | None = None):
        result = await self.session.call_tool(tool, args or {})
        text = "".join(getattr(c, "text", "") for c in result.content)
        failed = getattr(result, "is_error", getattr(result, "isError", False))
        if failed:
            raise SystemExit(f"{tool} failed: {text[:400]}")
        data = json.loads(text)
        data = data.get("data", data) if data.get("provenance") else data
        if data.get("status") in ("partial", "failed"):
            raise SystemExit(f"{tool} incomplete: {data}")
        return data


def step(text: str) -> None:
    print(f"- {text}")


async def find_tracks(live: Live) -> dict[str, int]:
    rows = (await live.call("live_get_tracks"))["tracks"]
    index = {r["name"]: r["track"] for r in rows if r["kind"] != "return"}
    missing = [name for name in ROLES.values() if name not in index]
    if missing:
        raise SystemExit(f"tracks not found (expected the Basic Set): {missing}")
    return {role: index[name] for role, name in ROLES.items()}


async def ensure_effect(live: Live, track: int, effect: str) -> int:
    """Reuse the named stock effect, loading one only when it has none."""
    devices = (await live.call("live_get_device_parameters", {"track": track}))["devices"]
    for d in devices:
        if d["name"] == effect:
            return d["index"]
    plan = await live.call(
        "live_plan_chain",
        {"track": track, "append": True, "stages": [{"device": effect, "root": "audio_effects"}]},
    )
    await live.call("live_build_chain", {"plan_id": plan["plan_id"]})
    devices = (await live.call("live_get_device_parameters", {"track": track}))["devices"]
    return next(d["index"] for d in devices if d["name"] == effect)


async def build(live: Live, fire: bool) -> None:
    await live.call("live_transport", {"action": "stop"})
    arrangement = await live.call("live_get_arrangement", {"include": ["cues"]})
    cues = {c["name"]: c["time"] for c in arrangement["cues"]}
    if cues.get("Intro") != 0 or cues.get("DROP") != 16:
        raise SystemExit("Basic must have Intro at 0 and DROP at 16 before building")
    tracks = await find_tracks(live)
    step(f"tracks: {tracks}")
    clips = [
        {"track": tracks[role], "scene": scene, "name": name, "length": 16, "notes": notes}
        for (role, scene), (name, notes) in patterns().items()
    ]
    made = await live.call("live_create_clips", {"clips": clips, "if_exists": "replace"})
    kept = len(made.get("skipped", []))
    step(f"clips: {len(clips) - kept} created, {kept} already there ({made['status']})")
    for role in FILTERED:
        track = tracks[role]
        slot = await ensure_effect(live, track, FILTER)
        step(f"{role}: {FILTER} at device {slot}")
        await live.call(
            "live_set_device_parameters",
            {
                "track": track,
                "path": [slot],
                "settings": [
                    {"parameter": "Type", "value": "High-pass"},
                    {"parameter": "Resonance", "value": {"raw": 0.25}},
                ],
            },
        )
        await live.call(
            "live_set_automation",
            {
                "targets": [
                    {
                        "clip": {"track": track, "scene": 0},
                        "parameter": {"device": [slot], "parameter": "Frequency"},
                        "clear": True,
                        "ramps": SWEEP,
                    }
                ]
            },
        )
        check = await live.call(
            "live_get_automation",
            {
                "clip": {"track": track, "scene": 0},
                "parameter": {"device": [slot], "parameter": "Frequency"},
                "sample_times": [0, 8, 12, 15.9],
            },
        )
        step(f"{role}: Frequency sweep written, samples {check.get('samples', check)}")
        await live.call(
            "live_set_automation",
            {
                "targets": [
                    {
                        "clip": {"track": track, "scene": 1},
                        "parameter": {"device": [slot], "parameter": "Frequency"},
                        "clear": True,
                        "steps": [{"time": 0, "length": 16, "value": 0.1}],
                    }
                ]
            },
        )
    track = tracks["KICK"]
    slot = await ensure_effect(live, track, "Saturator")
    if slot != 1:
        raise SystemExit(f"Core Saturator must follow Nexus at device 1, found {slot}")
    await live.call(
        "live_set_automation",
        {
            "targets": [
                {
                    "clip": {"track": track, "scene": 0},
                    "parameter": {"device": [slot], "parameter": "Drive"},
                    "clear": True,
                    "ramps": [{"start": 0, "end": 16, "from": 0.42, "to": 0.95, "steps": 64}],
                },
                {
                    "clip": {"track": track, "scene": 1},
                    "parameter": {"device": [slot], "parameter": "Drive"},
                    "clear": True,
                    "steps": [{"time": 0, "length": 16, "value": 0.42}],
                },
            ]
        },
    )
    placed = await live.call(
        "live_create_arrangement_clips",
        {
            "clips": [
                {
                    "track": tracks[role],
                    "kind": "from_session",
                    "scene": scene,
                    "start": scene * 16,
                    "replace": True,
                }
                for role, scene in patterns()
            ]
        },
    )
    if placed.get("status") != "complete":
        raise SystemExit(f"timeline placement incomplete: {placed}")
    await live.call("live_transport", {"action": "back_to_arranger"})
    await live.call("live_set_session", {"loop": {"on": False}})
    await live.call("live_transport", {"action": "jump_to", "beats": 0})
    await verify(live, tracks)
    if fire:
        await live.call("live_transport", {"action": "play"})
    print("Done. Arrangement: buildup beats 0-16, drop 16-32. Press Play from Intro.")


async def verify(live: Live, tracks: dict[str, int]) -> None:
    """Real Live proof: eight clips, exact bounds/names and complete note contents."""
    state = await live.call(
        "live_get_arrangement",
        {
            "tracks": list(tracks.values()),
            "include": ["clips", "cues"],
            "range": [0, 32],
            "response_format": "detailed",
        },
    )
    by_track = {row["track"]: row["clips"] for row in state["tracks"]}
    for (role, scene), (name, expected) in patterns().items():
        found = [c for c in by_track[tracks[role]] if c["start"] == scene * 16]
        assert len(found) == 1, (role, scene, found)
        clip = found[0]
        assert clip["name"] == name and clip["end"] == (scene + 1) * 16, clip
        actual = await live.call(
            "live_get_notes",
            {
                "clip": {"track": tracks[role], "arrangement": clip["arrangement"]},
                "response_format": "detailed",
            },
        )

        def canonical(rows):
            keys = ("pitch", "start_time", "duration", "velocity")
            return sorted(tuple(round(n[k], 4) for k in keys) for n in rows)

        assert canonical(actual["notes"]) == canonical(expected), (name, actual)
    step("verified all eight timeline clips, beat positions, names and notes")
    for role, parameter in (("PAD", "Frequency"), ("HATS", "Frequency"), ("KICK", "Drive")):
        for scene in (0, 1):
            result = await live.call(
                "live_get_automation",
                {
                    "clip": {"track": tracks[role], "scene": scene},
                    "parameter": {"device": [1], "parameter": parameter},
                    "sample_times": [0, 8, 15.9],
                },
            )
            values = [s["value"] for s in result["samples"]]
            expected = [0.1, 0.36087, 0.88] if scene == 0 else [0.1] * 3
            if parameter == "Drive":
                expected = [0.42, 0.68921, 0.95] if scene == 0 else [0.42] * 3
            assert all(abs(a - b) < 0.015 for a, b in zip(values, expected, strict=True)), (
                role, values
            )
            step(f"verified {role} scene {scene} {parameter}: {values}")
        device = await live.call("live_get_device_parameters", {
            "track": tracks[role], "path": [1], "response_format": "detailed",
        })
        actual = next(p for p in device["parameters"] if p["name"] == parameter)
        assert actual["automation_state"] == 1, (role, actual)
        step(f"verified {role} track parameter is automated")
    state = await live.call("live_get_session", {"include": ["transport", "cues"]})
    assert not state["is_playing"] and abs(state["current_song_time"]) < 0.01, state
    step("transport stopped at Intro; cue positions read back")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fire", action="store_true", help="also play the Arrangement from Intro")
    args = parser.parse_args()
    params = StdioServerParameters(command=sys.executable, args=["-m", "abletonlivemcp.server"])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        await build(Live(session), args.fire)


if __name__ == "__main__":
    asyncio.run(main())
