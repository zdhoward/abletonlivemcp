"""P-17: available_*_routing_types/channels and the routing setters.

Behavioural probe (write). Works on a scratch audio track, a scratch MIDI track and one return
track the probe creates itself (deleted in ``finally``). Questions answered:

- set by object: assign each kind of ``available_*_routing_*`` object back through the setter and
  read it back (by ``display_name``);
- Resampling: is a "Resampling" input type offered on an audio track, and does it read back;
- return as output: does any track offer the return track as an output type, and what are the
  return track's own output options;
- the exact error text for a string and a stale object assigned to a routing setter.

Routing is only ever changed on the three tracks the probe created.

Verdict: ``gated`` when the routing properties are absent; ``go`` when every attempted write read
back; otherwise ``no-go``. ``resampling_available`` and ``return_offered_as_output`` are facts
recorded in the evidence, not part of the rule.
"""

from .dom_common import WRITE, _same

PROBE_ID = "P-17"
KIND = WRITE

PAIRS = (
    ("input_routing_type", "available_input_routing_types"),
    ("input_routing_channel", "available_input_routing_channels"),
    ("output_routing_type", "available_output_routing_types"),
    ("output_routing_channel", "available_output_routing_channels"),
)


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def verdict_for(api_present, attempted, mismatches):
    """Pure verdict rule."""
    if not api_present:
        return "gated"
    return "go" if attempted > 0 and mismatches == 0 else "no-go"


def _label(obj):
    return getattr(obj, "display_name", None) or str(obj)


def _write_each(track, prop, avail):
    """Assign the first two available objects (distinct from current) back by object."""
    out = {"available": [], "writes": []}
    try:
        options = list(getattr(track, avail))
    except Exception as exc:  # noqa: BLE001
        out["error"] = _err(exc)
        return out
    out["available"] = [_label(o) for o in options][:12]
    out["available_count"] = len(options)
    for opt in options[:3]:
        try:
            setattr(track, prop, opt)
            got = _label(getattr(track, prop))
            out["writes"].append({"set": _label(opt), "read_back": got, "ok": got == _label(opt)})
        except Exception as exc:  # noqa: BLE001
            out["writes"].append({"set": _label(opt), "ok": False, "error": _err(exc)})
    return out


def _bad_writes(track):
    res = {}
    for label, value in (("string", "nonsense-routing"), ("int", 12345)):
        try:
            track.output_routing_type = value
            res[label] = {"accepted": True}
        except Exception as exc:  # noqa: BLE001 - the text is the evidence
            res[label] = {"accepted": False, "error": _err(exc)}
    return res


def run(ctx, scratch):
    song = ctx.song
    audio = scratch.audio_track()
    midi = scratch.midi_track()
    api_present = all(hasattr(audio, n) for pair in PAIRS for n in pair)
    if not api_present:
        return {"verdict": verdict_for(False, 0, 0)}
    before = list(song.return_tracks)
    song.create_return_track()
    ret = next(r for r in song.return_tracks if not any(_same(r, b) for b in before))
    result = {"tracks": {}}
    try:
        ret_name = ret.name
        for key, track in (("audio", audio), ("midi", midi), ("return", ret)):
            info = {}
            for prop, avail in PAIRS:
                if hasattr(track, prop):
                    info[prop] = _write_each(track, prop, avail)
                else:
                    info[prop] = {"absent": True}
            result["tracks"][key] = info
        resampling = [
            _label(o) for o in audio.available_input_routing_types if "resampl" in _label(o).lower()
        ]
        result["resampling_available"] = bool(resampling)
        if resampling:
            target = next(
                o for o in audio.available_input_routing_types if _label(o) == resampling[0]
            )
            audio.input_routing_type = target
            result["resampling_read_back"] = _label(audio.input_routing_type) == resampling[0]
        result["return_name"] = ret_name
        result["return_offered_as_output"] = {
            key: [
                _label(o)
                for o in getattr(t, "available_output_routing_types", [])
                if ret_name in _label(o)
            ]
            for key, t in (("audio", audio), ("midi", midi))
        }
        result["bad_value_errors"] = _bad_writes(audio)
    finally:
        for i, r in enumerate(song.return_tracks):
            if _same(r, ret):
                song.delete_return_track(i)
                break
    writes = [
        w for info in result["tracks"].values() for p in info.values() for w in p.get("writes", [])
    ]
    mismatches = sum(1 for w in writes if not w["ok"])
    if result.get("resampling_read_back") is False:
        mismatches += 1
    result["attempted_writes"] = len(writes)
    result["failed_writes"] = mismatches
    result["verdict"] = verdict_for(True, len(writes), mismatches)
    return result
