"""P-11: rack macros, variations, randomize_macros, Chain.mixer_device.

Behavioural probe (write), two stages because a device load lands on a later tick:

- the probe creates a scratch MIDI track and asks the browser to load the first drum kit
  (``.adg``, a stock Drum Rack) onto it, as the ref_lab ``load_kit`` does. The device lands on a
  later tick, so inside this call the rack is normally absent: the result is then
  ``verdict: "pending"`` with ``stage: "load_requested"``. The scratch track is deleted by the
  runner's cleanup, so a re-run cannot reuse it; a pending verdict means the runner needs a
  multi-call drive (ref_lab ``load_kit`` then probe reads) that this module cannot do alone.

With a rack present: ``visible_macro_count`` / ``macros_mapped`` / ``has_macro_mappings`` read,
``add_macro`` then ``remove_macro`` each read back, ``store_variation`` +
``variation_count`` + ``recall_selected_variation`` + ``delete_selected_variation``,
``randomize_macros`` (macro parameter values before and after), and the first chain's
``mixer_device`` volume write/readback.

Verdict: ``gated`` when RackDevice members are absent; ``pending`` when the device did not land
in this call; ``go`` when every call reads back; else ``go-with-limits``.
"""

from .dom_common import WRITE

PROBE_ID = "P-11"
KIND = WRITE

WALK_BUDGET = 4000
MEMBERS = (
    "visible_macro_count",
    "add_macro",
    "remove_macro",
    "has_macro_mappings",
    "variation_count",
    "store_variation",
    "randomize_macros",
    "chains",
)


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


def verdict_for(have_rack, checks):
    """Pure verdict rule (unit-testable). ``checks`` is a list of booleans."""
    if not have_rack:
        return "pending"
    return "go" if checks and all(checks) else "go-with-limits"


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


def _macro_values(rack):
    res = attempt(lambda: [round(float(p.value), 4) for p in list(rack.parameters)[1:9]])
    return res.get("value", res.get("error"))


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
            "so a re-run loads again. Re-run, or drive the load through ref_lab load_kit "
            "(scratch tracks are shared only within one call).",
        }
    missing = [n for n in MEMBERS if not hasattr(rack, n)]
    if missing:
        return {"verdict": "gated", "missing_members": missing}

    out = {"stage": "loaded", "kit": kit, "rack": attempt(lambda: rack.name).get("value")}
    checks = []

    def read(name):
        return attempt(lambda: getattr(rack, name)).get("value")

    out["initial"] = {
        k: read(k)
        for k in ("visible_macro_count", "macros_mapped", "has_macro_mappings", "variation_count")
    }
    before = read("visible_macro_count")
    add = attempt(rack.add_macro)
    after_add = read("visible_macro_count")
    rem = attempt(rack.remove_macro)
    after_rem = read("visible_macro_count")
    out["add_remove_macro"] = {
        "add": {"ok": add["ok"], "error": add.get("error")},
        "after_add": after_add,
        "remove": {"ok": rem["ok"], "error": rem.get("error")},
        "after_remove": after_rem,
        "before": before,
    }
    checks.append(add["ok"] and rem["ok"] and after_rem == before)

    vc = read("variation_count")
    store = attempt(rack.store_variation)
    vc_after = read("variation_count")
    recall = attempt(rack.recall_selected_variation)
    delete = attempt(rack.delete_selected_variation)
    vc_deleted = read("variation_count")
    out["variations"] = {
        "store": {"ok": store["ok"], "error": store.get("error")},
        "count": [vc, vc_after, vc_deleted],
        "recall": {"ok": recall["ok"], "error": recall.get("error")},
        "delete": {"ok": delete["ok"], "error": delete.get("error")},
    }
    checks.append(store["ok"] and vc_after == (vc or 0) + 1 and delete["ok"] and vc_deleted == vc)

    macros_before = _macro_values(rack)
    rnd = attempt(rack.randomize_macros)
    out["randomize_macros"] = {
        "ok": rnd["ok"],
        "error": rnd.get("error"),
        "before": macros_before,
        "after": _macro_values(rack),
    }
    checks.append(rnd["ok"])

    chains = attempt(lambda: list(rack.chains))
    if chains["ok"] and chains["value"]:
        mixer = attempt(lambda: chains["value"][0].mixer_device)
        if mixer["ok"]:
            vol = mixer["value"].volume
            out["chain_mixer"] = rw(vol, "value", (float(vol.min) + float(vol.max)) / 2.0, 1e-3)
            checks.append(bool(out["chain_mixer"]["match"]))
        else:
            out["chain_mixer"] = {"error": mixer["error"]}
            checks.append(False)
    else:
        out["chain_mixer"] = {"note": "no chains", "error": chains.get("error")}
        checks.append(False)

    out["verdict"] = verdict_for(True, checks)
    return out
