"""Targeted P-19 Session-copy proof on disposable Basic; never saves the Set.

Requires the demo's PAD Session clip and Auto Filter. Copies at beat 0, samples track
automation, deletes that copy, samples again, then restores the copy. All deletions are
limited to clips wholly within PAD beats 0..16. Run with the source/installed bridge matched.
"""

import asyncio
import json
import sys

from build_buildup_demo import Live
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from abletonlivemcp.bridge import BridgeClient


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "abletonlivemcp.server"],
        env={**__import__("os").environ, "ABLETONLIVEMCP_TOOLSETS": "arrangement"},
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        live = Live(session)
        await live.call("live_transport", {"action": "stop"})
        target = {"track": 7, "kind": "from_session", "scene": 0, "start": 0, "replace": True}
        receipt = await live.call("live_create_arrangement_clips", {"clips": [target]})
        assert receipt["status"] == "complete", receipt
        await live.call("live_transport", {"action": "back_to_arranger"})

        async def sample():
            out = []
            for beat in (0, 12):
                await live.call("live_transport", {"action": "jump_to", "beats": beat})
                await live.call("live_transport", {"action": "play"})
                rows = await live.call(
                    "live_get_device_parameters",
                    {"track": 7, "path": [1], "response_format": "detailed"},
                )
                await live.call("live_transport", {"action": "stop"})
                freq = next(p for p in rows["parameters"] if p["name"] == "Frequency")
                out.append({k: freq[k] for k in ("name", "value", "automation_state")})
            return out

        before = await sample()
        # Test cleanup uses the bridge's normal reference and delete permission gates.
        bridge = BridgeClient()
        state = await live.call(
            "live_get_arrangement",
            {"tracks": [7], "include": ["clips"], "response_format": "detailed"},
        )
        clip = next(c for c in state["tracks"][0]["clips"] if c["start"] == 0)
        assert clip["end"] == 16 and clip["name"] == "Buildup Pad", clip
        refs = bridge.call(
            "ref_issue",
            {"targets": [{"kind": "arr_clip", "track": 7, "arrangement": clip["arrangement"]}]},
        )
        ref = refs["refs"][0]
        deleted = bridge.call(
            "delete_clips", {"targets": [{"kind": "arr_clip", "ref": ref["ref"]}]}
        )
        after = await sample()
        restored = await live.call("live_create_arrangement_clips", {"clips": [target]})
        assert restored["status"] == "complete", restored
        assert all(p["automation_state"] == 1 for p in before + after), (before, after)
        await live.call("live_transport", {"action": "jump_to", "beats": 0})
        print(
            json.dumps(
                {
                    "copy": receipt,
                    "before_delete": before,
                    "deleted": deleted,
                    "after_delete": after,
                    "restored": restored,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
