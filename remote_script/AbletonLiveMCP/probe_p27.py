"""P-27: DeviceParameter display_value write, value_items, default_value, automation_state.

Behavioural probe (write): every parameter it touches belongs to a scratch track it created
through ``scratch`` (mixer ``volume``, ``panning``, ``track_activator`` and the first send's
parameter if present). Nothing is loaded and no existing object is read for writing.

Checks (each ``True``/``False``/``None`` for not applicable) plus raw readbacks:

- ``display_write_volume``: ``volume.display_value = -6.0`` then ``display_value`` reads -6.0
  within 0.05 and ``value`` moved; ``display_write_panning`` the same with ``25.0`` (+/- 0.5).
- ``value_items_quantized``: ``track_activator.is_quantized`` and ``value_items`` is a non-empty
  list; ``value_items_unquantized_raises``: ``volume.value_items`` raises (documented).
- ``default_value_unquantized``: ``volume.default_value`` is a number inside min..max;
  ``default_value_quantized``: recorded only (documented as unavailable for quantized).
- ``automation_state``: readable on a scratch parameter and ``0`` (no automation);
  ``re_enable_automation``: the call succeeds and the state stays ``0``.

Verdict: ``gated`` when the DeviceParameter lacks ``display_value``, ``value_items``,
``default_value``, ``automation_state`` or ``re_enable_automation``; ``no-go`` when the display
write on the volume does not read back; ``go`` when every applicable check passes (a display
write that works on volume and panning, quantized ``value_items``, unquantized ``default_value``,
automation members); otherwise ``go-with-limits``. The automation *overridden* state is not
reached (it needs a playing automated parameter) and is listed under ``untested``.
"""

from .dom_common import WRITE

PROBE_ID = "P-27"
KIND = WRITE

MEMBERS = (
    "display_value",
    "value_items",
    "default_value",
    "automation_state",
    "re_enable_automation",
)
CORE = ("display_write_volume",)
EXTRA = (
    "display_write_panning",
    "value_items_quantized",
    "default_value_unquantized",
    "automation_state_readable",
    "re_enable_automation_ok",
)
TOL_DB = 0.05
TOL_PAN = 0.5


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def verdict_for(missing, checks):
    """Pure verdict rule (kept separate so it is unit-testable)."""
    if missing:
        return "gated"
    if checks.get("display_write_volume") is not True:
        return "no-go"
    if all(checks.get(k) in (True, None) for k in EXTRA):
        return "go"
    return "go-with-limits"


def _try(fn):
    try:
        return fn(), None
    except Exception as exc:  # noqa: BLE001 - a failing member is evidence
        return None, _err(exc)


def _display_write(param, target, tol):
    """Write display_value, read it back; returns (ok, info)."""
    value_before, _ = _try(lambda: param.value)
    _, set_err = _try(lambda: setattr(param, "display_value", target))
    shown, read_err = _try(lambda: param.display_value)
    value_after, _ = _try(lambda: param.value)
    text, _ = _try(lambda: param.str_for_value(param.value))
    ok = (
        set_err is None
        and read_err is None
        and isinstance(shown, (int, float))
        and abs(shown - target) <= tol
        and value_after != value_before
    )
    return ok, {
        "target": target,
        "set_error": set_err,
        "read_error": read_err,
        "display_after": shown,
        "value_before": value_before,
        "value_after": value_after,
        "str_for_value": text,
    }


def run(ctx, scratch):
    track = scratch.midi_track()
    mixer = track.mixer_device
    volume, panning, activator = mixer.volume, mixer.panning, mixer.track_activator
    # class-level check: hasattr on an instance evaluates the property, and Live raises
    # non-AttributeError errors for some (value_items on a non-quantized parameter)
    missing = [
        m for m in MEMBERS if not all(hasattr(type(p), m) for p in (volume, panning, activator))
    ]
    if missing:
        return {"verdict": verdict_for(missing, {}), "missing_members": missing, "checks": {}}

    checks, detail = {}, {}

    ok, info = _display_write(volume, -6.0, TOL_DB)
    checks["display_write_volume"], detail["display_write_volume"] = ok, info
    ok, info = _display_write(panning, 25.0, TOL_PAN)
    checks["display_write_panning"], detail["display_write_panning"] = ok, info

    quantized, qerr = _try(lambda: activator.is_quantized)
    items, ierr = _try(lambda: list(activator.value_items))
    checks["value_items_quantized"] = bool(quantized) and bool(items)
    detail["value_items_quantized"] = {
        "is_quantized": quantized,
        "error": qerr or ierr,
        "items": items,
        "short_items": _try(lambda: list(activator.short_value_items))[0],
    }
    _, vi_err = _try(lambda: volume.value_items)
    detail["value_items_unquantized"] = {"raises": vi_err is not None, "error": vi_err}

    default, derr = _try(lambda: volume.default_value)
    checks["default_value_unquantized"] = (
        derr is None and isinstance(default, (int, float)) and volume.min <= default <= volume.max
    )
    detail["default_value_unquantized"] = {
        "default_value": default,
        "error": derr,
        "min": volume.min,
        "max": volume.max,
        "str_for_default": _try(lambda: volume.str_for_value(default))[0],
    }
    qdefault, qderr = _try(lambda: activator.default_value)
    detail["default_value_quantized"] = {"value": qdefault, "error": qderr}  # recorded only

    state, serr = _try(lambda: volume.automation_state)
    checks["automation_state_readable"] = serr is None and state == 0
    detail["automation_state"] = {"state": state, "error": serr}
    _, rerr = _try(lambda: volume.re_enable_automation())
    state_after, _ = _try(lambda: volume.automation_state)
    checks["re_enable_automation_ok"] = rerr is None and state_after == 0
    detail["re_enable_automation"] = {"error": rerr, "state_after": state_after}

    return {
        "verdict": verdict_for([], checks),
        "missing_members": [],
        "checks": checks,
        "detail": detail,
        "untested": ["automation_state overridden/playing (needs a playing automated parameter)"],
    }
