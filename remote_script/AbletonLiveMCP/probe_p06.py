"""P-06: mixer_device volume/panning/sends, master crossfader/cue_volume, str_for_value dB mapping.

Behavioural (write) probe. Writes only go to the mixer of a scratch MIDI track made through
``scratch``. The master track and return tracks are only read (``min``/``max``/``value`` and
the pure ``str_for_value``). The scratch track has sends only when the Set has return
tracks; with none, ``sends`` is reported as ``no_returns`` and not counted against the verdict.

dB mapping: ``bisect_db`` searches the volume parameter's value range with ``str_for_value`` (the
display text parsed to a number), then the found value is written to the scratch track and
read back.

Verdict: ``gated`` when ``volume`` or ``str_for_value`` is absent; ``go`` when a -6.0 dB display is
reached within 0.05 dB, the maximum value displays about +6 dB and the minimum displays -inf;
otherwise ``no-go``.
"""

from .dom_common import WRITE

PROBE_ID = "P-06"
KIND = WRITE

TARGET_DB = -6.0
TOLERANCE_DB = 0.05
MAX_STEPS = 40


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def parse_db(text):
    """'-6.0 dB' -> -6.0; '-inf dB' -> -inf; anything unparseable -> None."""
    if not isinstance(text, str):
        return None
    token = text.strip().split(" ")[0].replace("−", "-").replace(",", ".")
    if token.lower() in ("-inf", "-∞"):
        return float("-inf")
    try:
        return float(token)
    except ValueError:
        return None


def verdict_for(api_present, found_db, max_db, min_db):
    """Pure verdict rule (kept separate so it is unit-testable)."""
    if not api_present:
        return "gated"
    hit = found_db is not None and abs(found_db - TARGET_DB) <= TOLERANCE_DB
    plus6 = max_db is not None and max_db >= 5.9
    minus_inf = min_db == float("-inf")
    return "go" if hit and plus6 and minus_inf else "no-go"


def bisect_db(param, target_db):
    """Find ``value`` whose display is ``target_db``; assumes the display grows with the value.
    Returns (value, display_text, str_for_value_calls)."""
    lo, hi, calls = float(param.min), float(param.max), 0
    best = (lo, param.str_for_value(lo))
    calls += 1
    for _ in range(MAX_STEPS):
        mid = (lo + hi) / 2
        text = param.str_for_value(mid)
        calls += 1
        db = parse_db(text)
        best = (mid, text)
        if db is None:
            break
        if abs(db - target_db) <= TOLERANCE_DB / 2:
            break
        if db < target_db:
            lo = mid
        else:
            hi = mid
    return best[0], best[1], calls


def _param_info(param):
    return {
        "min": param.min,
        "max": param.max,
        "default": param.default_value,
        "is_quantized": param.is_quantized,
        "at_min": param.str_for_value(param.min),
        "at_max": param.str_for_value(param.max),
        "at_default": param.str_for_value(param.default_value),
    }


def _set_read(param, value):
    """Write ``value``, read back (value, display); errors become evidence."""
    try:
        param.value = value
        return {
            "requested": value,
            "value": param.value,
            "display": param.str_for_value(param.value),
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"requested": value, "error": _err(exc)}


def run(ctx, scratch):
    song = ctx.song
    track = scratch.midi_track()
    mixer = track.mixer_device
    volume = getattr(mixer, "volume", None)
    if volume is None or not hasattr(volume, "str_for_value"):
        return {"verdict": "gated", "reason": "mixer_device.volume or str_for_value absent"}

    out = {"volume": _param_info(volume)}
    value, text, calls = bisect_db(volume, TARGET_DB)
    written = _set_read(volume, value)
    found_db = parse_db(written.get("display"))
    out["bisect_minus_6_db"] = {
        "value": value,
        "display": text,
        "str_for_value_calls": calls,
        "readback": written,
    }
    ceiling = parse_db(volume.str_for_value(volume.max))
    floor = parse_db(volume.str_for_value(volume.min))
    out["extremes"] = {
        "max_display": volume.str_for_value(volume.max),
        "min_display": volume.str_for_value(volume.min),
        "write_max": _set_read(volume, volume.max),
        "write_min": _set_read(volume, volume.min),
    }
    zero_value, zero_text, zero_calls = bisect_db(volume, 0.0)
    out["bisect_0_db"] = {
        "value": zero_value,
        "display": zero_text,
        "str_for_value_calls": zero_calls,
    }

    panning = mixer.panning
    out["panning"] = {
        "info": _param_info(panning),
        "writes": [_set_read(panning, v) for v in (panning.min, 0.0, panning.max)],
    }

    activator = {}
    try:
        activator["before"] = track.mixer_device.track_activator.value
        activator["write_off"] = _set_read(mixer.track_activator, 0)
        activator["write_on"] = _set_read(mixer.track_activator, 1)
    except Exception as exc:  # noqa: BLE001
        activator["error"] = _err(exc)
    out["track_activator"] = activator

    crossfade = {}
    try:
        crossfade["assignments"] = str(mixer.crossfade_assignments)[:80]
        crossfade["writes"] = []
        for v in (0, 1, 2):
            try:
                mixer.crossfade_assign = v
                crossfade["writes"].append(
                    {"requested": v, "value": mixer.crossfade_assign, "error": None}
                )
            except Exception as exc:  # noqa: BLE001
                crossfade["writes"].append({"requested": v, "error": _err(exc)})
    except Exception as exc:  # noqa: BLE001
        crossfade["error"] = _err(exc)
    out["crossfade_assign"] = crossfade

    sends = list(mixer.sends)
    if sends:
        send = sends[0]
        out["sends_on_scratch_track"] = {
            "count": len(sends),
            "info": _param_info(send),
            "write_max": _set_read(send, send.max),
            "write_min": _set_read(send, send.min),
        }
    else:
        out["sends_on_scratch_track"] = "no_returns"
    returns = list(song.return_tracks)
    out["sends_on_returns"] = [
        {"return": i, "send_count": len(list(r.mixer_device.sends))} for i, r in enumerate(returns)
    ] or "no_returns"

    master = {}
    master_mixer = song.master_track.mixer_device
    for name in ("crossfader", "cue_volume", "volume", "panning"):  # read only
        p = getattr(master_mixer, name, None)
        try:
            master[name] = _param_info(p) if p is not None else "absent"
        except Exception as exc:  # noqa: BLE001
            master[name] = {"error": _err(exc)}
    out["master_read_only"] = master

    out["verdict"] = verdict_for(True, found_db, ceiling, floor)
    return out
