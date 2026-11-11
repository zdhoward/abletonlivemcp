"""P-10: session-clip automation envelopes (step vs breakpoint semantics, arrangement).

Behavioural probe (write): a scratch MIDI track with a 4-beat session clip and a stock-free
parameter, the track's own mixer volume, which belongs to the scratch track. Steps:

1. ``clip.automation_envelope(param)`` before any envelope exists (expected None) and
   ``create_automation_envelope(param)``;
2. ``insert_step(time, length, value)`` ramp emulation: 8 steps of 0.5 beat across the clip
   (values 0.0..0.7 of the parameter range, linear in the parameter's own value space), then
   ``value_at_time`` at 5 points compared with the ideal ramp (tolerance 2% of the range);
3. ``events_in_range`` count/shape (does a step come back as one event or breakpoints?);
4. ``delete_events_in_range`` then ``clear_envelope(param)``; ``has_envelopes`` readback;
5. arrangement: ``automation_envelope`` on an arrangement clip made with ``create_midi_clip``
   (expected None per plan; recorded either way).

Verdict: ``gated`` when Envelope/clip members are absent; ``no-go`` when no envelope can be
created; ``go`` when the five-point ramp is within 2%; else ``go-with-limits``.
"""

from .dom_common import WRITE

PROBE_ID = "P-10"
KIND = WRITE

STEPS = 8
STEP_LEN = 0.5
TOLERANCE = 0.02


def err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def attempt(fn):
    """Run ``fn``; the outcome is evidence either way."""
    try:
        return {"ok": True, "value": fn()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": err(exc)}


def verdict_for(have_envelope, max_error_fraction):
    """Pure verdict rule (unit-testable). ``max_error_fraction`` is of the parameter range."""
    if not have_envelope:
        return "no-go"
    if max_error_fraction is not None and max_error_fraction <= TOLERANCE:
        return "go"
    return "go-with-limits"


def _event(ev):
    out = {}
    for attr in ("time", "value", "length", "step_length", "is_step"):
        if hasattr(ev, attr):
            out[attr] = attempt(lambda a=attr: getattr(ev, a)).get("value")
    return out


def run(ctx, scratch):
    track = scratch.midi_track()
    slot = track.clip_slots[0]
    try:
        slot.create_clip(4.0)
    except Exception as exc:  # noqa: BLE001
        return {"verdict": "no-go", "reason": f"clip not created: {err(exc)}"}
    clip = slot.clip
    param = track.mixer_device.volume
    needed = ("automation_envelope", "create_automation_envelope", "clear_envelope")
    members = {n: hasattr(clip, n) for n in needed}
    if not all(members.values()):
        return {"verdict": "gated", "members": members}

    lo, hi = float(param.min), float(param.max)
    span = hi - lo
    initial = attempt(lambda: clip.automation_envelope(param))
    created = attempt(lambda: clip.create_automation_envelope(param))
    env = created.get("value")
    out = {
        "param_range": [lo, hi],
        "envelope_before_create": {
            "ok": initial["ok"],
            "is_none": initial.get("value") is None,
            "error": initial.get("error"),
        },
        "create": {"ok": created["ok"], "error": created.get("error"), "is_none": env is None},
    }
    if env is None:
        out["verdict"] = verdict_for(False, None)
        return out
    env_members = {
        n: hasattr(env, n)
        for n in ("insert_step", "events_in_range", "value_at_time", "delete_events_in_range")
    }
    out["envelope_members"] = env_members
    if not all(env_members.values()):
        out["verdict"] = "gated"
        return out

    ideal = []
    steps = []
    for i in range(STEPS):
        frac = 0.7 * i / (STEPS - 1)
        value = lo + span * frac
        ideal.append((i * STEP_LEN + STEP_LEN / 2.0, frac))
        steps.append(attempt(lambda t=i * STEP_LEN, v=value: env.insert_step(t, STEP_LEN, v)))
    out["insert_step_errors"] = [s["error"] for s in steps if not s["ok"]][:3]

    points = []
    max_err = 0.0
    for t, frac in [ideal[0], ideal[2], ideal[4], ideal[6], ideal[7]]:
        got = attempt(lambda t=t: env.value_at_time(t))
        entry = {"time": t, "ideal_fraction": round(frac, 4)}
        if got["ok"]:
            gfrac = (float(got["value"]) - lo) / span
            entry["got_fraction"] = round(gfrac, 4)
            max_err = max(max_err, abs(gfrac - frac))
        else:
            entry["error"] = got["error"]
            max_err = float("inf")
        points.append(entry)
    out["ramp_points"] = points
    out["max_error_fraction"] = None if max_err == float("inf") else round(max_err, 4)

    events = attempt(lambda: list(env.events_in_range(0.0, 4.0)))
    if events["ok"]:
        out["events_in_range"] = {
            "count": len(events["value"]),
            "first": [_event(e) for e in events["value"][:3]],
        }
    else:
        out["events_in_range"] = {"error": events["error"]}

    deleted = attempt(lambda: env.delete_events_in_range(0.0, 4.0))
    after_delete = attempt(lambda: len(list(env.events_in_range(0.0, 4.0))))
    cleared = attempt(lambda: clip.clear_envelope(param))
    out["delete_events"] = {
        "ok": deleted["ok"],
        "error": deleted.get("error"),
        "events_after": after_delete.get("value"),
    }
    out["clear_envelope"] = {
        "ok": cleared["ok"],
        "error": cleared.get("error"),
        "has_envelopes_after": attempt(lambda: clip.has_envelopes).get("value"),
    }

    arr_track = scratch.midi_track()
    arr = attempt(lambda: arr_track.create_midi_clip(0.0, 4.0))
    if arr["ok"] and arr.get("value") is not None:
        arr_clip = arr["value"]
        arr_param = arr_track.mixer_device.volume
        got = attempt(lambda: arr_clip.automation_envelope(arr_param))
        out["arrangement"] = {
            "returns_none": got["ok"] and got["value"] is None,
            "ok": got["ok"],
            "error": got.get("error"),
        }
    else:
        out["arrangement"] = {"clip_error": arr.get("error")}

    out["verdict"] = verdict_for(True, None if max_err == float("inf") else max_err)
    return out
