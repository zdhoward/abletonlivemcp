"""P-24: Song.view selection, select_device, rack view selected chain/drum pad.

Behavioural probe (write): the only things it creates are scratch tracks/scenes/one scratch clip
(through ``scratch``). It changes the user's *selection* and restores it in a ``finally``.

Items, each ``ok`` (written and read back), ``fail`` (error or no readback), ``absent`` (the
member does not exist on this Live) or ``untested`` (nothing to test it on; no rack in the Set):

- ``selected_track``: set a scratch track (twice, two different ones), read it back.
- ``selected_scene``: set a scratch scene, read it back.
- ``detail_clip``: create a clip on a scratch track, set it as the detail clip, read it back.
- ``select_device``: ``Song.view.select_device`` on an existing device (a scratch track has no
  device and the probe loads none), read back through the owner track's ``view.selected_device``.
- ``selected_chain``: set ``Song.view.selected_chain`` / the rack view's ``selected_chain`` to a
  chain of an existing rack, read it back.
- ``selected_drum_pad``: set the drum rack view's ``selected_drum_pad``, read it back.

Verdict: ``gated`` when ``Song.View`` lacks ``selected_track`` or ``select_device`` (the load-target
selection API is absent); ``no-go`` when ``selected_track`` is not ``ok``; ``go`` when
``selected_track``, ``selected_scene`` and ``select_device`` are ``ok`` and no item is ``fail``;
otherwise ``go-with-limits``.
"""

from .dom_common import WRITE, _same

PROBE_ID = "P-24"
KIND = WRITE

CORE = ("selected_track", "selected_scene", "select_device")
REQUIRED_MEMBERS = ("selected_track", "select_device")


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def verdict_for(items, members_absent):
    """Pure verdict rule (kept separate so it is unit-testable)."""
    if members_absent:
        return "gated"
    if items.get("selected_track") != "ok":
        return "no-go"
    if all(items.get(k) == "ok" for k in CORE) and "fail" not in items.values():
        return "go"
    return "go-with-limits"


def _get(obj, attr):
    try:
        return getattr(obj, attr), None
    except Exception as exc:  # noqa: BLE001 - an unreadable member is evidence
        return None, _err(exc)


def _set_check(obj, attr, value):
    """Set ``obj.attr = value`` and read it back. Returns (status, detail)."""
    if not hasattr(type(obj), attr):  # class level: no property evaluation
        return "absent", {"error": f"no member {attr!r}"}
    try:
        setattr(obj, attr, value)
    except Exception as exc:  # noqa: BLE001
        return "fail", {"set_error": _err(exc)}
    got, read_err = _get(obj, attr)
    if read_err:
        return "fail", {"read_error": read_err}
    same = _same(got, value)
    return ("ok" if same else "fail"), {"readback_same": same}


def _find(song, wanted):
    """First device (top-level, on any track) for which ``wanted(device)`` is true."""
    tracks = list(song.tracks) + list(song.return_tracks) + [song.master_track]
    for track in tracks:
        for device in list(track.devices):
            try:
                if wanted(device):
                    return track, device
            except Exception:  # noqa: BLE001
                continue
    return None, None


def run(ctx, scratch):
    song = ctx.song
    view = song.view
    absent = [m for m in REQUIRED_MEMBERS if not hasattr(type(view), m)]
    if absent:
        return {"verdict": verdict_for({}, absent), "absent_members": absent, "items": {}}

    items, detail, restore = {}, {}, []
    originals = {
        "track": _get(view, "selected_track")[0],
        "scene": _get(view, "selected_scene")[0],
        "detail_clip": _get(view, "detail_clip")[0],
        "chain": _get(view, "selected_chain")[0],
    }
    owner = rack = drum = None
    saved = {}
    try:
        a, b = scratch.midi_track(), scratch.midi_track()
        scene = scratch.scene()

        s1, d1 = _set_check(view, "selected_track", a)
        s2, d2 = _set_check(view, "selected_track", b)
        items["selected_track"] = "ok" if s1 == s2 == "ok" else (s1 if s1 != "ok" else s2)
        detail["selected_track"] = [d1, d2]

        status, info = _set_check(view, "selected_scene", scene)
        items["selected_scene"], detail["selected_scene"] = status, info

        # detail_clip: a clip in slot 0 of a scratch track (the only thing written)
        try:
            slot = a.clip_slots[0]
            slot.create_clip(4.0)
            items["detail_clip"], detail["detail_clip"] = _set_check(view, "detail_clip", slot.clip)
        except Exception as exc:  # noqa: BLE001
            items["detail_clip"], detail["detail_clip"] = "fail", {"error": _err(exc)}

        # select_device on an existing device (selection only; restored below)
        owner, device = _find(song, lambda d: True)
        if device is None:
            items["select_device"] = "untested"
            detail["select_device"] = {"reason": "no device on any track"}
        else:
            before_dev = _get(owner.view, "selected_device")[0]
            saved["device"] = (owner, before_dev)
            try:
                view.select_device(device)
                got, rerr = _get(owner.view, "selected_device")
                track_now = _get(view, "selected_track")[0]
                ok = rerr is None and _same(got, device)
                items["select_device"] = "ok" if ok else "fail"
                detail["select_device"] = {
                    "readback_same": ok,
                    "read_error": rerr,
                    "selected_track_is_owner": _same(track_now, owner),
                }
            except Exception as exc:  # noqa: BLE001
                items["select_device"], detail["select_device"] = "fail", {"error": _err(exc)}

        # selected_chain on an existing rack
        _rt, rack = _find(song, lambda d: getattr(d, "can_have_chains", False) and len(d.chains))
        if rack is None:
            items["selected_chain"] = "untested"
            detail["selected_chain"] = {"reason": "no rack with chains"}
        else:
            chain = rack.chains[0]
            rview = rack.view
            saved["rack_chain"] = _get(rview, "selected_chain")[0]
            status, info = _set_check(rview, "selected_chain", chain)
            sv_status, sv_info = _set_check(view, "selected_chain", chain)
            if status == "absent" and sv_status == "absent":
                items["selected_chain"] = "absent"
            elif "ok" in (status, sv_status):
                items["selected_chain"] = "ok"
            else:
                items["selected_chain"] = "fail"
            detail["selected_chain"] = {
                "rack_view": [status, info],
                "song_view": [sv_status, sv_info],
                "rack_view_members": sorted(n for n in dir(rview) if not n.startswith("_"))[:60],
            }

        # selected_drum_pad on an existing drum rack
        _dt, drum = _find(song, lambda d: getattr(d, "can_have_drum_pads", False))
        if drum is None:
            items["selected_drum_pad"] = "untested"
            detail["selected_drum_pad"] = {"reason": "no drum rack"}
        else:
            dview = drum.view
            saved["drum_pad"] = _get(dview, "selected_drum_pad")[0]
            pads = list(drum.drum_pads)
            items["selected_drum_pad"], detail["selected_drum_pad"] = _set_check(
                dview, "selected_drum_pad", pads[0]
            )
    finally:
        restore = _restore(song, view, originals, saved, rack, drum)

    verdict = verdict_for(items, [])
    return {
        "verdict": verdict,
        "absent_members": [],
        "items": items,
        "detail": detail,
        "restore": restore,
    }


def _restore(song, view, originals, saved, rack, drum):
    """Put the selection back; every step is attempted and reported."""
    report = {}

    def attempt(name, fn):
        try:
            fn()
            report[name] = "restored"
        except Exception as exc:  # noqa: BLE001
            report[name] = f"failed: {_err(exc)}"

    if "drum_pad" in saved and saved["drum_pad"] is not None and drum is not None:
        attempt("drum_pad", lambda: setattr(drum.view, "selected_drum_pad", saved["drum_pad"]))
    if "rack_chain" in saved and saved["rack_chain"] is not None and rack is not None:
        attempt("rack_chain", lambda: setattr(rack.view, "selected_chain", saved["rack_chain"]))
    if originals["chain"] is not None:
        attempt("song_chain", lambda: setattr(view, "selected_chain", originals["chain"]))
    if "device" in saved:
        owner, before_dev = saved["device"]
        if before_dev is not None:
            attempt("device", lambda: view.select_device(before_dev))
        else:
            report["device"] = "not restorable: no device was selected before"
    if originals["track"] is not None:
        attempt("track", lambda: setattr(view, "selected_track", originals["track"]))
    if originals["scene"] is not None:
        attempt("scene", lambda: setattr(view, "selected_scene", originals["scene"]))
    if originals["detail_clip"] is not None:
        attempt("detail_clip", lambda: setattr(view, "detail_clip", originals["detail_clip"]))
    return report
