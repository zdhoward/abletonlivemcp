"""[WRITING] T-006 proof: one write tool call is one Live undo step.

Creates 3 scratch MIDI tracks, renames all 3 with one batch ``live_set_tracks`` call, requires the
reply to report ``undo_steps: 1``, calls ``Song.undo`` once (through ``live_undo``) and requires all
3 names reverted while the 3 scratch tracks still exist (the batch did not merge into the track
creations before it). Disposable Set only; it never saves. Scratch tracks are left in the Set
(there is no delete tool yet).

Needs ``--allow-writes`` and ``"read_only": false`` in the private bridge config.

Undo through the bridge: the bridge has no method that calls ``Song.undo`` until T-010 ships
``live_undo`` (and T-011 ships the batch ``live_set_tracks``). This script does not add one. When
either tool is missing it says so and exits 2 before writing anything. ``live_undo`` is a
DESTRUCTIVE tool, so it also needs a client that can confirm it (T-007 elicitation); this harness
has none, and a ``confirmation_unavailable`` refusal also ends the run with exit 2.

Exit codes: 0 every required check passed; 1 a required check failed; 2 did not run.
"""

import sys

from live_harness import Abort, Refused, base_parser, run_proof

NEEDED = {
    "live_set_tracks": "batch track writes (T-011)",
    "live_undo": "Song.undo through the bridge (T-010)",
}
PREFIX = "ALMCP undo"


async def names(h, indices):
    rows = await h.tool("live_tracks")
    return [rows[i]["name"] for i in indices]


async def scenario(h, a, chk):
    missing = [f"{tool} ({why})" for tool, why in NEEDED.items() if tool not in h.tool_names]
    if missing:
        raise Abort(
            "Song.undo cannot be invoked through the bridge yet; missing tool(s): "
            + ", ".join(missing)
            + ". T-006 adds no undo handler of its own. Nothing was changed. "
            "Undo grouping itself is proven by P-03 (docs/release/probes/P-03.md)."
        )

    scratch = [await h.scratch_track("midi", PREFIX) for _ in range(3)]
    idx = [t.index for t in scratch]
    count = (await h.tool("live_session_info"))["track_count"]
    original = await names(h, idx)
    chk.info("scratch", f"tracks {idx} named {original}")

    targets = [
        {"track": i, "expect_name": old, "name": f"{PREFIX} {k}"}
        for k, (i, old) in enumerate(zip(idx, original, strict=True))
    ]
    reply = await h.tool("live_set_tracks", {"targets": targets})
    steps = reply.get("undo_steps") if isinstance(reply, dict) else None
    chk.require(steps == 1, "batch write reports undo_steps: 1", f"got {steps!r}")
    renamed = await names(h, idx)
    chk.require(
        renamed == [t["name"] for t in targets], "batch renamed all 3", str(renamed), fatal=True
    )

    try:
        await h.tool("live_undo", {"action": "undo", "steps": 1})
    except Refused as exc:
        if exc.code == "confirmation_unavailable":
            raise Abort(
                "live_undo is DESTRUCTIVE and this client cannot confirm it (no elicitation); "
                f"the 3 scratch tracks {idx} keep their batch names"
            ) from exc
        raise
    after = await names(h, idx)
    reverted = sum(1 for got, old in zip(after, original, strict=True) if got == old)
    chk.require(reverted == 3, "one Song.undo reverted all 3 renames", f"{reverted}/3: {after}")
    now = (await h.tool("live_session_info"))["track_count"]
    chk.require(now == count, "scratch tracks still exist (no merge with creations)", f"{now}")


def build_parser():
    p = base_parser(__doc__)
    p.add_argument("--allow-writes", action="store_true", help="required: this script WRITES")
    p.add_argument("--ticket", default="T-006", help="evidence file name (docs/release/v2/<>.md)")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    banner = f"mode: WRITING - 3 scratch tracks only on 127.0.0.1:{a.port}"
    if not a.allow_writes:
        print(banner)
        print("RESULT: REFUSED (exit 2): this script writes to Live; pass --allow-writes to run")
        return 2
    return run_proof(a.ticket, "one undo step per tool call (T-006)", scenario, a, banner)


if __name__ == "__main__":
    sys.exit(main())
