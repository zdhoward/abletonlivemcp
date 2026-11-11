"""[WRITING, dev] T-005 proof: every reference kind validates, then refuses once its object is
deleted, moved or reordered, and after a Set change.

Needs ``--allow-writes`` and, in the private bridge config, ``"read_only": false`` and
``"dev_probes": true`` (the ``ref_lab`` bridge method is dev-only). Runs under the mutation
lease. It creates its own scratch objects through ``ref_lab`` (3 MIDI tracks named
"ALMCP refs", 2 return tracks, 2 scenes, 2 take lanes, 3 arrangement clips, 2 cue points at
``--cue-time`` and +8 beats, one drum kit from the browser's Drums root) and deletes or moves
only those; ``ref_lab`` refuses anything under a root it did not create. It moves the stopped
playhead for cue edits and puts it back. Disposable Set only; it never saves.

Set change: with ``--set-change-wait S`` it issues one fresh reference of every kind, then waits
up to S seconds for the Set to change (open another Set in Live, e.g. relaunch Live with the
Basic Set) and requires every one of them to refuse. Without it that step is skipped (info) and
the remaining scratch objects are deleted.

Exit codes: 0 every required check passed; 1 a required check failed; 2 did not run.
"""

import sys
import time

from live_harness import Abort, Refused, base_parser, run_proof

from abletonlivemcp.bridge import BridgeError

STALE = ("unknown_reference", "stale_reference", "stale_target")
LEASE_TTL = 60.0


class Lab:
    """Raw bridge helpers: lab actions under a lease (renewed before it runs out), batched
    reference issue/check."""

    def __init__(self, h, generation):
        self.h, self.generation = h, generation
        self.lease, self.until = None, 0.0

    def _lease(self):
        if self.lease is None or time.monotonic() > self.until - 15:
            if self.lease is not None:
                self.h.call("lease_release", {"lease": self.lease})
            self.lease = self.h.call("lease_acquire", {"ttl": LEASE_TTL})["lease"]
            self.until = time.monotonic() + LEASE_TTL
        return self.lease

    def act(self, action, **params):
        params.update(action=action, lease=self._lease(), generation=self.generation)
        return self.h.call("ref_lab", params)

    def release(self):
        if self.lease is not None:
            try:
                self.h.call("lease_release", {"lease": self.lease})
            except (Refused, BridgeError):
                pass
            self.lease = None

    def issue(self, **targets):
        """name -> selector dict; returns name -> {"kind", "ref"}."""
        names = list(targets)
        out = self.h.call("ref_issue", {"targets": [targets[n] for n in names]})["refs"]
        return {n: {"kind": r["kind"], "ref": r["ref"]} for n, r in zip(names, out, strict=True)}

    def check(self, refs):
        """name -> (valid, code) for every reference in ``refs``."""
        names = list(refs)
        res = self.h.call("ref_check", {"refs": [refs[n] for n in names]})["results"]
        return {n: (r["valid"], r.get("code")) for n, r in zip(names, res, strict=True)}


def expect(chk, lab, refs, refuse, keep=(), step=""):
    """After ``step``: ``refuse`` names must refuse (stale code); ``keep`` names stay valid."""
    state = lab.check({n: refs[n] for n in (*refuse, *keep)})
    for n in refuse:
        valid, code = state[n]
        chk.require(not valid and code in STALE, f"{step}: {n} refuses", str(code))
    for n in keep:
        chk.require(state[n][0], f"{step}: {n} still validates", str(state[n][1]))


def wait_for(fn, timeout, every=1.0):
    end = time.monotonic() + timeout
    while True:
        try:
            value = fn()
        except (Refused, BridgeError, ValueError, KeyError):
            value = None
        if value or time.monotonic() >= end:
            return value
        time.sleep(every)


async def scenario(h, a, chk):
    info = h.call("session_info")
    if info["is_playing"]:
        raise Abort("stop the transport first (cue edits move the stopped playhead)")
    lab = Lab(h, info["generation"])
    try:
        await _run(h, a, chk, lab)
    finally:
        lab.release()


async def _run(h, a, chk, lab):
    try:
        t1 = lab.act("create_track")["track"]
    except Refused as exc:
        if exc.code == "dev_probes_disabled":
            raise Abort('set "dev_probes": true in bridge.json (ref_lab is dev-only)') from exc
        raise
    t2, t3 = lab.act("create_track")["track"], lab.act("create_track")["track"]
    r1, r2 = lab.act("create_return")["return"], lab.act("create_return")["return"]
    s1, s2 = lab.act("create_scene")["scene"], lab.act("create_scene")["scene"]
    chk.info("scratch", f"tracks {t1},{t2},{t3} returns {r1},{r2} scenes {s1},{s2}")
    own = lab.issue(t1={"kind": "track", "track": t1}, t3={"kind": "track", "track": t3})
    for _ in range(2):
        lab.act("create_take_lane", **own["t1"])
    for start in (0.0, 8.0):
        lab.act("create_arr_clip", **own["t1"], start=start, length=4.0)
    lane0 = lab.issue(x={"kind": "take_lane", "track": t1, "take_lane": 0})["x"]
    lab.act("create_arr_clip", **lane0, start=16.0, length=4.0)
    c0 = lab.act("create_cue", time=a.cue_time)["cue"]
    c1 = lab.act("create_cue", time=a.cue_time + 8)["cue"]
    kit = lab.act("load_kit", **own["t3"], **({"kit": a.kit} if a.kit else {}))["kit"]
    chk.info("kit", f"loading {kit!r} onto track {t3}")
    rack = {"kind": "device", "track": t3, "path": [0]}
    chk.require(wait_for(lambda: lab.issue(x=rack), a.load_timeout), "drum kit loaded", fatal=True)
    pads = []
    for note in range(36, 52):  # first two pads holding a device in their first chain
        sel = {"kind": "device", "track": t3, "path": [0, f"pad:{note}", 0]}
        if wait_for(lambda s=sel: lab.issue(x=s), 0):
            pads.append(note)
            if len(pads) == 2:
                break
    chk.require(len(pads) == 2, "kit has two pads with a device", str(pads), fatal=True)
    pa, pb = (f"pad:{n}" for n in pads)

    refs = lab.issue(
        t1={"kind": "track", "track": t1},
        t2={"kind": "track", "track": t2},
        r2={"kind": "return_track", "track": f"return:{r2}"},
        master={"kind": "master", "track": "master"},
        s2={"kind": "scene", "scene": s2},
        send={"kind": "mixer_param", "track": t1, "role": "send", "send": r2},
        vol={"kind": "mixer_param", "track": t1, "role": "volume"},
        master_vol={"kind": "mixer_param", "track": "master", "role": "volume"},
        ret_pan={"kind": "mixer_param", "track": f"return:{r2}", "role": "panning"},
        lane0={"kind": "take_lane", "track": t1, "take_lane": 0},
        lane1={"kind": "take_lane", "track": t1, "take_lane": 1},
        arr0={"kind": "arr_clip", "track": t1, "arrangement": 0},
        arr1={"kind": "arr_clip", "track": t1, "arrangement": 1},
        lane_arr={"kind": "arr_clip", "track": t1, "take_lane": 0, "arrangement": 0},
        cue0={"kind": "cue", "cue": c0},
        cue1={"kind": "cue", "cue": c1},
        rack=rack,
        chain0={"kind": "chain", "track": t3, "path": [0, 0]},
        chain_vol={"kind": "mixer_param", "track": t3, "path": [0, 0], "role": "volume"},
        pad_a={"kind": "drum_pad", "track": t3, "path": [0, pa]},
        pad_b={"kind": "drum_pad", "track": t3, "path": [0, pb]},
        dev_a={"kind": "device", "track": t3, "path": [0, pa, 0]},
        dev_b={"kind": "device", "track": t3, "path": [0, pb, 0]},
        param_a={"kind": "param", "track": t3, "path": [0, pa, 0], "parameter": 0},
    )
    every = lab.check(refs)
    for name, (valid, code) in every.items():
        chk.require(valid, f"{refs[name]['kind']} reference {name} validates", str(code))
    wrong = lab.check({"m": {"kind": "track", "ref": refs["master"]["ref"]}})["m"]
    chk.require(wrong == (False, "stale_reference"), "a master ref used as 'track' refuses")

    # nested devices: move B's device to the front of A's chain (B moved, A reordered). Live may
    # refuse an instrument in front of another; then move A out to an empty track instead.
    try:
        lab.act(
            "move_device",
            **refs["dev_b"],
            to_kind="drum_pad",
            to_ref=refs["pad_a"]["ref"],
            position=0,
        )
        expect(
            chk,
            lab,
            refs,
            ("dev_a", "dev_b", "param_a"),
            ("pad_a", "pad_b", "rack"),
            "device moved in front of another pad's device (moved + reordered)",
        )
        victim = lab.issue(x={"kind": "device", "track": t3, "path": [0, pa, 1]})["x"]
    except (Refused, BridgeError) as exc:
        chk.info("nested reorder not possible in this kit (device-level reorder unproven)", exc)
        t2_track = lab.issue(x={"kind": "track", "track": t2})["x"]["ref"]
        lab.act("move_device", **refs["dev_a"], to_kind="track", to_ref=t2_track, position=0)
        expect(
            chk,
            lab,
            refs,
            ("dev_a", "param_a"),
            ("pad_a", "pad_b", "dev_b", "rack"),
            "nested device moved out to another track",
        )
        victim = lab.issue(x={"kind": "device", "track": t2, "path": [0]})["x"]
    lab.act("delete", **victim)
    expect(chk, lab, {"victim": victim}, ("victim",), (), "device deleted")
    lab.act("delete", **refs["pad_a"])  # DrumPad.delete_all_chains
    expect(chk, lab, refs, ("pad_a",), ("pad_b",), "pad cleared")
    chk.info("chain0 after pad cleared", str(lab.check({"c": refs["chain0"]})["c"]))
    t2_ref = lab.issue(x={"kind": "track", "track": t2})["x"]
    lab.act("move_device", **refs["rack"], to_kind="track", to_ref=t2_ref["ref"], position=0)
    expect(chk, lab, refs, ("rack", "pad_b", "chain_vol"), ("t2",), "rack moved to another track")

    lab.act("delete", **refs["arr0"])
    expect(chk, lab, refs, ("arr0",), ("arr1", "lane_arr"), "arrangement clip deleted")
    lab.act("delete", **refs["cue0"])
    expect(chk, lab, refs, ("cue0",), ("cue1",), "cue deleted")
    s1_ref = lab.issue(x={"kind": "scene", "scene": s1})["x"]
    lab.act("delete", **s1_ref)
    expect(chk, lab, refs, ("s2",), (), "earlier scene deleted (s2 reordered)")
    s2_now = lab.issue(x={"kind": "scene", "scene": s1})["x"]  # s2 now sits at s1's index
    lab.act("delete", **s2_now)
    expect(chk, lab, {"s2_now": s2_now}, ("s2_now",), (), "scene deleted")
    r1_ref = lab.issue(x={"kind": "return_track", "track": f"return:{r1}"})["x"]
    lab.act("delete", **r1_ref)
    expect(
        chk,
        lab,
        refs,
        ("r2", "send", "ret_pan"),
        ("master", "master_vol", "vol"),
        "earlier return deleted (sends and returns shift)",
    )
    t1_ref = lab.issue(x={"kind": "track", "track": t1})["x"]
    lab.act("delete", **t1_ref)
    expect(
        chk,
        lab,
        refs,
        ("t1", "t2", "vol", "lane0", "lane1", "arr1", "lane_arr"),
        ("master",),
        "earlier track deleted (t2 reordered, t1 children gone)",
    )

    # Set change: one fresh reference of every kind that still has an object.
    t2, t3, r = t2 - 1, t3 - 1, r1  # t1 deleted; r2 now sits at r1's index
    t2_ref = lab.issue(x={"kind": "track", "track": t2})["x"]
    lab.act("create_take_lane", **t2_ref)
    lab.act("create_arr_clip", **t2_ref, start=0.0, length=4.0)
    last = lab.issue(
        track={"kind": "track", "track": t3},
        return_track={"kind": "return_track", "track": f"return:{r}"},
        master={"kind": "master", "track": "master"},
        scene={"kind": "scene", "scene": 0},
        cue={"kind": "cue", "cue": c1 - 1},
        device={"kind": "device", "track": t2, "path": [0]},
        chain={"kind": "chain", "track": t2, "path": [0, 0]},
        drum_pad={"kind": "drum_pad", "track": t2, "path": [0, pb]},
        mixer_param={"kind": "mixer_param", "track": "master", "role": "volume"},
        take_lane={"kind": "take_lane", "track": t2, "take_lane": 0},
        arr_clip={"kind": "arr_clip", "track": t2, "arrangement": 0},
    )
    state = lab.check(last)
    chk.require(all(v for v, _ in state.values()), "fresh refs of every kind validate", str(state))
    if a.set_change_wait <= 0:
        chk.info("Set change", "skipped (no --set-change-wait); deleting scratch objects")
        for name in ("track", "return_track", "cue"):
            lab.act("delete", **last[name])
        lab.act("delete", **t2_ref)
        return
    generation = lab.generation
    lab.release()
    print(f"ACTION: open another Set in Live now (waiting up to {a.set_change_wait:.0f} s)")
    changed = wait_for(
        lambda: h.call("session_info")["generation"] != generation, a.set_change_wait, 2.0
    )
    chk.require(changed, "Set change observed (generation changed)", fatal=True)
    after = lab.check(last)
    for name, (valid, code) in after.items():
        chk.require(not valid and code in STALE, f"{name} refuses after the Set change", str(code))


def build_parser():
    p = base_parser(__doc__)
    p.add_argument("--allow-writes", action="store_true", help="required: this script WRITES")
    p.add_argument("--kit", help="exact drum kit preset name (default: the first .adg found)")
    p.add_argument("--cue-time", type=float, default=4000.0, help="beat of the first scratch cue")
    p.add_argument("--load-timeout", type=float, default=30.0, help="seconds to wait for the kit")
    p.add_argument(
        "--set-change-wait", type=float, default=0.0, help="seconds to wait for a Set change"
    )
    p.add_argument("--ticket", default="T-005", help="evidence file name (docs/release/v2/<>.md)")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    banner = f"mode: WRITING (dev ref_lab) - scratch objects only on 127.0.0.1:{a.port}"
    if not a.allow_writes:
        print(banner)
        print("RESULT: REFUSED (exit 2): this script writes to Live; pass --allow-writes to run")
        return 2
    return run_proof(a.ticket, "reference kinds (T-005)", scenario, a, banner)


if __name__ == "__main__":
    sys.exit(main())
