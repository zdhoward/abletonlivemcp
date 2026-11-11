"""P-20: SimplerDevice and Sample (slice) writable fields.

Behavioural probe (write). A scratch MIDI track is created and a stock ``Simpler`` is loaded onto
it through the browser. Live applies a browser load on a later main-thread tick, so the device
usually is not visible inside the same call: then (and when no Simpler exists in the browser, or
the Simpler has no sample) the verdict is ``gated`` with the reason recorded and no field is
written. When a Simpler is present, each writable-candidate field of the device (and of its
``Sample``) is read, set to a different value, read back and restored in a ``finally``; the
slice calls (``insert_slice``/``move_slice``/``remove_slice``/``reset_slices``) run only on a
sample on the scratch track. Everything touched lives on the scratch track, which the runner
deletes afterwards.

Verdict: ``gated`` without a usable Simpler/Sample; ``go`` when every field present reads back;
``go-with-limits`` when some do not; ``no-go`` when none do.
"""

from .dom_common import WRITE

PROBE_ID = "P-20"
KIND = WRITE

DEVICE_FIELDS = (
    "playback_mode",
    "retrigger",
    "voices",
    "pad_slicing",
    "multi_sample_mode",
    "slicing_playback_mode",
    "pitch_bend_range",
    "playing_position_enabled",
)
SAMPLE_FIELDS = (
    "gain",
    "warping",
    "warp_mode",
    "start_marker",
    "end_marker",
    "slicing_style",
    "slicing_sensitivity",
    "slicing_beat_division",
    "slicing_region_count",
    "beats_granulation_resolution",
    "texture_grain_size",
    "texture_flux",
)
MAX_BROWSER_NODES = 400


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def _plain(value):
    return (
        value if value is None or isinstance(value, (bool, int, float, str)) else repr(value)[:80]
    )


def _candidates(old):
    if isinstance(old, bool):
        return [not old]
    if isinstance(old, int):
        return [old + 1, old - 1]
    if isinstance(old, float):
        return [old + 0.25, old - 0.25, old * 0.5]
    return []


def _same_value(a, b):
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) < 1e-4
        except (TypeError, ValueError):
            return False
    return a == b


def probe_field(obj, name):
    """Read, set, read back, restore one field; never raises. ``ok`` means the set read back."""
    rec = {"field": name, "ok": False}
    try:
        old = getattr(obj, name)
    except AttributeError:
        rec["reason"] = "absent"
        return rec
    except Exception as exc:  # noqa: BLE001
        rec["reason"] = f"read failed: {_err(exc)}"
        return rec
    rec["before"] = _plain(old)
    options = _candidates(old)
    if not options:
        rec["reason"] = f"no alternative value for {type(old).__name__}"
        return rec
    errors = []
    try:
        for new in options:
            try:
                setattr(obj, name, new)
                back = getattr(obj, name)
            except Exception as exc:  # noqa: BLE001
                errors.append(_err(exc))
                continue
            rec["set"], rec["readback"] = _plain(new), _plain(back)
            rec["ok"] = _same_value(back, new)
            if rec["ok"]:
                break
    finally:
        try:
            setattr(obj, name, old)
            rec["restored"] = _same_value(getattr(obj, name), old)
        except Exception as exc:  # noqa: BLE001
            rec["restore_error"] = _err(exc)
    if not rec["ok"]:
        rec["reason"] = "; ".join(errors) if errors else "readback differs from the value set"
    return rec


def verdict_for(fields, usable=True):
    """Pure verdict rule over a list of ``probe_field`` records."""
    if not usable:
        return "gated"
    present = [f for f in fields if f.get("reason") != "absent"]
    ok = [f for f in present if f["ok"]]
    if not ok:
        return "no-go"
    return "go" if len(ok) == len(present) else "go-with-limits"


def _find_simpler(browser):
    stack, seen = [browser.instruments], 0
    while stack and seen < MAX_BROWSER_NODES:
        node = stack.pop()
        for child in reversed(list(getattr(node, "children", None) or ())):
            seen += 1
            if getattr(child, "is_loadable", False) and child.name == "Simpler":
                return child
            if getattr(child, "is_folder", False):
                stack.append(child)
    return None


def _slice_ops(sample):
    ops = {}

    def attempt(name, fn):
        try:
            ops[name] = {"ok": True, "detail": _plain(fn())}
        except Exception as exc:  # noqa: BLE001
            ops[name] = {"ok": False, "error": _err(exc)}

    def count():
        return len(list(sample.slices))

    attempt("slices_before", count)
    attempt("insert_slice", lambda: (sample.insert_slice(sample.length // 2), count())[1])
    attempt("remove_slice", lambda: (sample.remove_slice(sample.length // 2), count())[1])
    attempt("reset_slices", lambda: (sample.reset_slices(), count())[1])
    return ops


def run(ctx, scratch):
    track = scratch.midi_track()
    out = {"verdict": "gated"}
    browser = ctx.app.browser
    item = _find_simpler(browser)
    out["simpler_in_browser"] = item is not None
    if item is None:
        out["reason"] = "no Simpler found under browser.instruments"
        return out
    ctx.song.view.selected_track = track
    browser.load_item(item)
    simplers = [d for d in track.devices if d.class_name == "OriginalSimpler"]
    out["devices_after_load"] = [d.class_name for d in track.devices]
    if not simplers:
        out["reason"] = "the device is added on a later tick; re-run with a Simpler already placed"
        return out
    device = simplers[0]
    fields = [probe_field(device, n) for n in DEVICE_FIELDS]
    sample = None
    try:
        sample = device.sample
    except Exception as exc:  # noqa: BLE001
        out["sample_error"] = _err(exc)
    if sample is None:
        out["reason"] = "the Simpler has no sample"
        out["device_fields"] = fields
        out["verdict"] = "gated"
        return out
    sample_fields = [probe_field(sample, n) for n in SAMPLE_FIELDS]
    out.update(
        device_fields=fields,
        sample_fields=sample_fields,
        slice_ops=_slice_ops(sample),
        verdict=verdict_for(fields + sample_fields),
    )
    return out
