"""P-04: Song.move_device and find_device_position: reorder, cross-track, into/out of a rack chain.

Behavioural (write) probe. A probe cannot load a device (the browser load is asynchronous), so the
devices come from copies: it reads the Set (read-only) for the first track with at least two devices
and the first track holding a rack with chains, and duplicates each with ``Song.duplicate_track``.
Only the duplicates (adopted into ``scratch`` so they are deleted afterwards) and two scratch tracks
are ever written; pre-existing tracks are only read. With no such devices in the Set the verdict is
``no-go`` with ``needs_fixture: true``.

Moves checked by readback: (1) reorder within a track, (2) move across tracks (to a scratch MIDI
track, device type permitting), (3) into a rack chain and back out. The invalid-type error is
captured by moving an instrument onto a scratch audio track (or any move ``find_device_position``
reports as -1).

Verdict: ``gated`` when ``move_device``/``find_device_position`` are absent; ``go`` when the three
moves read back correctly and an invalid-type error text was captured; otherwise ``no-go``.
"""

from .dom_common import WRITE, _same

PROBE_ID = "P-04"
KIND = WRITE


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def verdict_for(api_present, reorder_ok, cross_ok, chain_ok, error_text):
    """Pure verdict rule (kept separate so it is unit-testable)."""
    if not api_present:
        return "gated"
    return "go" if reorder_ok and cross_ok and chain_ok and bool(error_text) else "no-go"


def _devs(container):
    return list(container.devices)


def _index(container, device):
    for i, d in enumerate(_devs(container)):
        if _same(d, device):
            return i
    return -1


def _name(device):
    try:
        return device.name
    except Exception as exc:  # noqa: BLE001
        return f"<{_err(exc)}>"


def _duplicate(song, scratch, index):
    """Duplicate track ``index`` and adopt the new track into scratch (so it is cleaned up)."""
    before = list(song.tracks)
    song.duplicate_track(index)
    new = [t for t in song.tracks if not any(_same(t, b) for b in before)]
    if len(new) != 1:
        raise RuntimeError("could not identify the duplicated track")
    scratch.created.append(("track", new[0]))
    return new[0]


def _rack(track):
    for d in _devs(track):
        if getattr(d, "can_have_chains", False) and len(list(d.chains)) > 0:
            return d
    return None


def run(ctx, scratch):
    song = ctx.song
    api_present = all(hasattr(song, n) for n in ("move_device", "find_device_position"))
    if not api_present:
        return {"verdict": "gated", "reason": "move_device/find_device_position absent"}

    tracks = list(song.tracks)
    src_multi = next((i for i, t in enumerate(tracks) if len(_devs(t)) >= 2), None)
    src_rack = next((i for i, t in enumerate(tracks) if _rack(t) is not None), None)
    out = {"source_tracks": {"two_devices": src_multi, "rack": src_rack}}
    if src_multi is None and src_rack is None:
        out.update(verdict="no-go", needs_fixture=True, reason="no track with 2+ devices or a rack")
        return out

    multi = _duplicate(song, scratch, src_multi) if src_multi is not None else None
    if src_rack is not None and src_rack == src_multi:
        rack_track = multi
    elif src_rack is not None:
        rack_track = _duplicate(song, scratch, src_rack)
    else:
        rack_track = None
    midi = scratch.midi_track()
    audio = scratch.audio_track()

    # 1. reorder within a track: first device to the end.
    reorder = {"ran": False, "ok": False, "error": None}
    if multi is not None:
        before = [_name(d) for d in _devs(multi)]
        first = _devs(multi)[0]
        try:
            pos = song.find_device_position(first, multi, len(before))
            ret = song.move_device(first, multi, len(before))
            after = [_name(d) for d in _devs(multi)]
            reorder.update(
                ran=True,
                find_position=pos,
                return_value=ret,
                names_before=before,
                names_after=after,
                ok=_index(multi, first) == len(before) - 1 and len(after) == len(before),
            )
        except Exception as exc:  # noqa: BLE001
            reorder["error"] = _err(exc)
    out["reorder"] = reorder

    # 2. across tracks, and the invalid-type error. A device the position finder accepts for the
    # scratch MIDI track is moved there; an instrument sent to the audio track is the invalid case.
    cross = {"ran": False, "ok": False, "error": None}
    invalid = {"error": None, "find_position": None, "attempted": None}
    pool = [(t, d) for t in (multi, rack_track) if t is not None for d in _devs(t)]
    seen = []
    for track, device in pool:
        if any(_same(device, s) for s in seen):
            continue
        seen.append(device)
        try:
            if not cross["ran"]:
                pos = song.find_device_position(device, midi, 0)
                if pos >= 0:
                    n_src = len(_devs(track))
                    ret = song.move_device(device, midi, 0)
                    cross.update(
                        ran=True,
                        device=_name(device),
                        find_position=pos,
                        return_value=ret,
                        ok=_index(midi, device) == 0
                        and _index(track, device) == -1
                        and len(_devs(track)) == n_src - 1,
                    )
            if invalid["error"] is None:
                pos = song.find_device_position(device, audio, 0)
                if pos < 0:
                    invalid.update(find_position=pos, attempted=_name(device))
                    try:
                        song.move_device(device, audio, 0)
                        invalid["error"] = "<no error raised>"
                    except Exception as exc:  # noqa: BLE001
                        invalid["error"] = _err(exc)
        except Exception as exc:  # noqa: BLE001
            cross["error"] = cross["error"] or _err(exc)
        if cross["ran"] and invalid["error"] is not None:
            break
    out["cross_track"], out["invalid_type"] = cross, invalid

    # 3. into a rack chain and back out (to the scratch MIDI track, or the rack's own track).
    chain = {"ran": False, "ok": False, "error": None}
    rack = _rack(rack_track) if rack_track is not None else None
    if rack is not None:
        done = False
        candidates = [d for t in (multi, rack_track, midi) if t is not None for d in _devs(t)]
        for device in candidates:
            if done or _same(device, rack):
                continue
            home = next(
                (t for t in (multi, rack_track, midi) if t is not None and _index(t, device) >= 0),
                None,
            )
            for ch in list(rack.chains):
                try:
                    pos = song.find_device_position(device, ch, len(_devs(ch)))
                    if pos < 0:
                        continue
                    ret = song.move_device(device, ch, pos)
                    into = _index(ch, device) >= 0 and _index(home, device) == -1
                    back_pos = song.find_device_position(device, home, 0)
                    ret_out = song.move_device(device, home, 0) if back_pos >= 0 else None
                    outof = back_pos >= 0 and _index(home, device) >= 0 and _index(ch, device) == -1
                    chain.update(
                        ran=True,
                        device=_name(device),
                        into_return=ret,
                        out_find_position=back_pos,
                        out_return=ret_out,
                        into_ok=into,
                        out_ok=outof,
                        ok=bool(into and outof),
                    )
                    done = True
                    break
                except Exception as exc:  # noqa: BLE001
                    chain["error"] = chain["error"] or _err(exc)
            if done:
                break
    else:
        chain["note"] = "no rack with chains in the duplicates"
    out["rack_chain"] = chain

    verdict = verdict_for(True, reorder["ok"], cross["ok"], chain["ok"], invalid["error"])
    out["verdict"] = verdict
    if verdict == "no-go" and not (multi and rack_track):
        out["needs_fixture"] = True
    return out
