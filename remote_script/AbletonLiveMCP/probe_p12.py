"""P-12: drum pads: mute/solo/delete_all_chains, copy_pad, DrumChain out_note/choke_group.

Behavioural probe (write), two stages like P-11 (a device load lands on a later tick): it
creates a scratch MIDI track, requests a stock drum kit on it, and returns ``pending`` with
``stage: "load_requested"`` if the Drum Rack is not there yet. With the rack present:

- ``drum_pads`` count and the first pads that hold chains (``chains`` non-empty);
- ``mute`` and ``solo`` write/readback on a populated pad (restored afterwards);
- ``DrumChain.out_note`` and ``choke_group`` write/readback on that pad's first chain;
- ``copy_pad(source_note, destination_note)`` to a destination pad that already holds chains,
  recording chain count and first chain name before and after (overwrite vs append);
- ``delete_all_chains`` on the destination pad, chain count afterwards.

Only this scratch track's rack is touched. Verdict: ``gated`` when members are absent,
``pending`` when the rack did not land, ``go`` when every write reads back and copy/delete
behave, else ``go-with-limits``; the overwrite behaviour is recorded as evidence.
"""

from .dom_common import WRITE

PROBE_ID = "P-12"
KIND = WRITE


def err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def attempt(fn):
    """Run ``fn``; the outcome is evidence either way."""
    try:
        return {"ok": True, "value": fn()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": err(exc)}


def _close(a, b, tol=1e-6):
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return a == b


def rw(obj, attr, value, tol=1e-6):
    """Write ``obj.attr = value`` and read it back: {wrote, readback, match | error}."""
    out = {"attr": attr, "wrote": value}
    try:
        setattr(obj, attr, value)
    except Exception as exc:  # noqa: BLE001
        out.update(match=False, error=err(exc))
        return out
    try:
        got = getattr(obj, attr)
    except Exception as exc:  # noqa: BLE001
        out.update(match=False, error=f"readback {err(exc)}")
        return out
    out.update(readback=got, match=_close(got, value, tol))
    return out


WALK_BUDGET = 4000


def request_kit(app, song, track):
    """Ask the browser to load the first .adg under drums onto ``track``; returns the name."""
    stack, visited, item = [app.browser.drums], 0, None
    while stack and item is None and visited < WALK_BUDGET:
        node = stack.pop()
        for child in reversed(list(getattr(node, "children", None) or ())):
            visited += 1
            if getattr(child, "is_loadable", False) and child.name.lower().endswith(".adg"):
                item = child
            elif getattr(child, "is_folder", False):
                stack.append(child)
    if item is None:
        raise RuntimeError("no drum kit preset found within the walk budget")
    song.view.selected_track = track
    app.browser.load_item(item)
    return item.name


def find_rack(track):
    return next(
        (
            d
            for d in track.devices
            if getattr(d, "can_have_drum_pads", None) is not None
            and hasattr(d, "visible_macro_count")
        ),
        None,
    )


def verdict_for(have_rack, checks):
    """Pure verdict rule (unit-testable)."""
    if not have_rack:
        return "pending"
    return "go" if checks and all(checks) else "go-with-limits"


def _chain_state(pad):
    chains = attempt(lambda: list(pad.chains))
    if not chains["ok"]:
        return {"error": chains["error"]}
    names = [attempt(lambda c=c: c.name).get("value") for c in chains["value"][:3]]
    return {"count": len(chains["value"]), "names": names}


def run(ctx, scratch):
    track = scratch.midi_track()
    try:
        kit = request_kit(ctx.app, ctx.song, track)
    except Exception as exc:  # noqa: BLE001
        return {"verdict": "gated", "reason": f"kit load not possible: {err(exc)}"}
    rack = find_rack(track)
    if rack is None:
        return {
            "verdict": "pending",
            "stage": "load_requested",
            "kit": kit,
            "note": "device loads land on a later tick; the scratch track is deleted by cleanup, "
            "so a re-run loads again and the runner should retry.",
        }
    missing = [n for n in ("drum_pads", "copy_pad") if not hasattr(rack, n)]
    if missing:
        return {"verdict": "gated", "missing_members": missing}

    pads = list(rack.drum_pads)
    full = [p for p in pads if _chain_state(p).get("count")]
    out = {"stage": "loaded", "kit": kit, "pad_count": len(pads), "populated_pads": len(full)}
    if len(full) < 2:
        out["verdict"] = "go-with-limits"
        out["reason"] = "fewer than two populated pads; copy semantics not tested"
        return out
    src, dst = full[0], full[1]
    checks = []

    out["mute"] = rw(src, "mute", True)
    out["mute_restore"] = rw(src, "mute", False)
    out["solo"] = rw(src, "solo", True)
    out["solo_restore"] = rw(src, "solo", False)
    checks += [
        out["mute"]["match"],
        out["mute_restore"]["match"],
        out["solo"]["match"],
        out["solo_restore"]["match"],
    ]

    chain = attempt(lambda: list(src.chains)[0])
    if chain["ok"]:
        c = chain["value"]
        out["out_note"] = rw(c, "out_note", 60)
        out["choke_group"] = rw(c, "choke_group", 3)
        checks += [out["out_note"]["match"], out["choke_group"]["match"]]
    else:
        out["chain_error"] = chain["error"]
        checks.append(False)

    src_note, dst_note = int(src.note), int(dst.note)
    before_src, before_dst = _chain_state(src), _chain_state(dst)
    copied = attempt(lambda: rack.copy_pad(src_note, dst_note))
    after_dst = _chain_state(dst)
    out["copy_pad"] = {
        "ok": copied["ok"],
        "error": copied.get("error"),
        "source_note": src_note,
        "destination_note": dst_note,
        "source_before": before_src,
        "destination_before": before_dst,
        "destination_after": after_dst,
        "overwrote_destination": (
            copied["ok"]
            and after_dst.get("names") == before_src.get("names")
            and after_dst.get("count") == before_src.get("count")
        ),
        "appended_to_destination": (
            copied["ok"]
            and after_dst.get("count") == (before_dst.get("count", 0) + before_src.get("count", 0))
        ),
    }
    checks.append(copied["ok"])

    deleted = attempt(dst.delete_all_chains)
    after_delete = _chain_state(dst)
    out["delete_all_chains"] = {
        "ok": deleted["ok"],
        "error": deleted.get("error"),
        "after": after_delete,
    }
    checks.append(deleted["ok"] and after_delete.get("count") == 0)

    out["verdict"] = verdict_for(True, checks)
    return out
