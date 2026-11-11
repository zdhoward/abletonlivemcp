"""P-22: Song scale/root, count-in, Link, groove pool, Clip.groove and tuning system writability.

Behavioural probe (write). For each field the probe reads the value, sets a different one, reads it
back and restores the original in a ``finally``; a field that cannot be set records the exact error
as its reason (Ableton Link fields may need Link enabled in Live's preferences, which is also
recorded as the reason). The grooves in the pool and the tuning system belong to the Set, not to
the probe, so they are only touched through the same set/readback/restore sequence and the
restoration is read back. ``Clip.groove`` is exercised on a clip in a scratch track's first slot.

Verdict: ``gated`` when the Song has none of the probed members; ``no-go`` when no field could be
read; otherwise ``go`` (every field has a readback or a recorded reason), with ``writable`` and
``reasons`` counts in the result.
"""

from .dom_common import WRITE

PROBE_ID = "P-22"
KIND = WRITE

SONG_FIELDS = (
    "root_note",
    "scale_mode",
    "scale_name",
    "count_in_duration",
    "groove_amount",
    "midi_recording_quantization",
    "is_ableton_link_enabled",
    "is_ableton_link_start_stop_sync_enabled",
)
GROOVE_FIELDS = ("timing_amount", "quantization_amount", "random_amount", "velocity_amount")
TUNING_FIELDS = ("reference_pitch", "lowest_note", "highest_note")
MAX_GROOVES = 3


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def _plain(value):
    return (
        value if value is None or isinstance(value, (bool, int, float, str)) else repr(value)[:80]
    )


def _candidates(old, name):
    if isinstance(old, bool):
        return [not old]
    if isinstance(old, int):
        return [old + 1, old - 1]
    if isinstance(old, float):
        return [old + 0.1, old - 0.1]
    if isinstance(old, str) and name == "scale_name":
        return ["Minor", "Major"]
    return []


def _same_value(a, b):
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) < 1e-4
        except (TypeError, ValueError):
            return False
    return a == b


def probe_field(obj, name):
    """Never raises; ``ok`` means a set read back, ``reason`` says why not."""
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
    options = _candidates(old, name)
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


def verdict_for(records):
    """Pure verdict rule over ``probe_field`` records."""
    present = [r for r in records if r.get("reason") != "absent"]
    if not present:
        return "gated"
    readable = [r for r in present if "before" in r]
    if not readable:
        return "no-go"
    return "go" if all(r["ok"] or r.get("reason") for r in readable) else "no-go"


def _groove_pool(song):
    rec = {"present": False}
    try:
        pool = song.groove_pool
        grooves = list(pool.grooves)
    except Exception as exc:  # noqa: BLE001
        rec["error"] = _err(exc)
        return rec, []
    rec.update(present=True, count=len(grooves))
    fields = []
    for groove in grooves[:MAX_GROOVES]:
        for name in GROOVE_FIELDS:
            fields.append(
                dict(probe_field(groove, name), groove=_plain(getattr(groove, "name", None)))
            )
    return rec, fields


def _clip_groove(song, scratch, grooves):
    rec = {"tried": False}
    if not grooves:
        rec["reason"] = "the groove pool is empty"
        return rec
    track = scratch.midi_track()
    slot = track.clip_slots[0]
    try:
        slot.create_clip(4.0)
        clip = slot.clip
        rec["tried"] = True
        rec["has_groove_before"] = _plain(clip.has_groove)
        clip.groove = grooves[0]
        rec["has_groove_after_set"] = _plain(clip.has_groove)
        rec["groove_name"] = _plain(getattr(clip.groove, "name", None))
        clip.groove = None
        rec["has_groove_after_clear"] = _plain(clip.has_groove)
        rec["ok"] = rec["has_groove_after_set"] is True and rec["has_groove_after_clear"] is False
    except Exception as exc:  # noqa: BLE001
        rec["error"] = _err(exc)
        rec["ok"] = False
    return rec


def run(ctx, scratch):
    song = ctx.song
    fields = [probe_field(song, n) for n in SONG_FIELDS]
    pool, groove_fields = _groove_pool(song)
    tuning_fields = []
    try:
        tuning = song.tuning_system
        tuning_fields = [probe_field(tuning, n) for n in TUNING_FIELDS]
        tuning_name = _plain(getattr(tuning, "name", None))
    except Exception as exc:  # noqa: BLE001
        tuning_name = f"<{_err(exc)}>"
    try:
        grooves = list(song.groove_pool.grooves)
    except Exception:  # noqa: BLE001
        grooves = []
    clip_groove = _clip_groove(song, scratch, grooves)
    records = fields + groove_fields + tuning_fields
    return {
        "verdict": verdict_for(records),
        "song_fields": fields,
        "groove_pool": pool,
        "groove_fields": groove_fields,
        "tuning_system": {"name": tuning_name, "fields": tuning_fields},
        "clip_groove": clip_groove,
        "writable": sum(1 for r in records if r["ok"]),
        "reasons": {r["field"]: r["reason"] for r in records if r.get("reason")},
        "link_note": "Link fields may only be writable with Link enabled in Live's preferences",
    }
