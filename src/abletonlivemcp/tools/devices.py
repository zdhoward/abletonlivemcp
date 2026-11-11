"""Device tools: read and set device parameters."""

from __future__ import annotations

from .. import chain
from ..models import RawValue, Setting
from ..server import _call, _explain, _overwrite, _read, _untrusted


@_read
def live_device_parameters(track: int, device: int) -> dict:
    """Name, value, range and display text of each parameter of a device (names untrusted)."""
    rows = _call("device_parameters", {"track": track, "device": device})
    return _untrusted([{k: v for k, v in r.items() if k != "ref"} for r in rows])


@_overwrite
def live_set_device_parameters(track: int, device: int, settings: list[Setting]) -> dict:
    """Set up to 32 device parameters, by parameter name. A value is a display target such as
    "-18 dB", 4, "Vocal" or true (solved against Live's own display text) or {"raw": 0.3} (the
    stored 0..1 value, written as given). Each result has Live's actual display and stored value,
    the original value, and `exact`; a request that landed off target says so. Disabled or
    macro-controlled parameters are refused, never overridden."""
    if not 1 <= len(settings) <= 32:
        raise ValueError("'settings' must hold 1..32 items")
    params = _call("device_parameters", {"track": track, "device": device})
    items = []
    for s in settings:
        target = {"raw": s.value.raw} if isinstance(s.value, RawValue) else s.value
        q = chain._resolve(params, s.parameter)
        if not q.get("is_enabled", True):
            raise ValueError(f"{s.parameter!r} is disabled or controlled elsewhere")
        items.append((q, target))
    try:
        results, problems = chain.set_parameters(_call, {"track": track, "device": device}, items)
    except chain.WriteInterrupted as exc:
        return {
            "status": "partial",
            "results": exc.results,
            "problems": exc.problems + [_explain(exc.cause)],
        }
    ok = not problems and all(r["exact"] for r in results)
    return {"status": "complete" if ok else "partial", "results": results, "problems": problems}
