"""P-14: Browser.load_item onto a MIDI track, a drum pad and a rack chain; hotswap; preview.

Behavioural probe (write), three stages. A load lands on a later tick, so one run cannot read it
back. State lives in ``_STATE`` (the Remote Script process); ``complete: false`` in the result
means "re-run":

- stage 1: two scratch MIDI tracks. Select track 1 and load a stock instrument; select track 2 and
  load a Drum Rack; ``preview_item`` then ``stop_preview`` on a drum sample. The two tracks are
  handed off from ``scratch`` to this module (so the end-of-run scratch cleanup does not delete
  them before the load lands) and are deleted here at the final stage, or if a stage fails.
- stage 2: read both tracks. Select the Drum Rack's pad (note 36) and load a drum sample with that
  pad selected; record ``hotswap_target`` and the load errors.
- stage 3: read the pad's chain (a ``DrumChain``, the rack-chain case) and delete both tracks.

Limits recorded in the evidence: a load *into an Instrument Rack chain* is not run (it needs a
chain-bearing rack the probe would have to build); the drum pad's chain is the chain case.

Verdict: ``gated`` when ``Browser.load_item`` or ``hotswap_target`` is absent; ``go`` when the
instrument landed on the MIDI track and the sample landed in the selected pad's chain; else
``no-go``.
"""

from .dom_common import WRITE, _same

PROBE_ID = "P-14"
KIND = WRITE

MAX_WAIT_RUNS = 3
WALK_BUDGET = 600
PREFERRED_INSTRUMENTS = ("Operator", "Wavetable", "Analog", "Simpler", "Sampler")
_STATE = {}


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def verdict_for(api_present, instrument_landed, sample_in_pad_chain):
    """Pure verdict rule."""
    if not api_present:
        return "gated"
    return "go" if instrument_landed and sample_in_pad_chain else "no-go"


def _children(item):
    it = getattr(item, "iter_children", None)
    return list(it) if it is not None else list(getattr(item, "children", []))


def _find(root, accept, budget=WALK_BUDGET):
    """Breadth-first search for the first browser item ``accept`` approves."""
    queue, seen = [root], 0
    while queue and seen < budget:
        node = queue.pop(0)
        seen += 1
        for child in _children(node):
            if accept(child):
                return child
            if getattr(child, "is_folder", False):
                queue.append(child)
    return None


def _device_names(track):
    return [d.name for d in track.devices]


def _drop(song, tracks):
    gone = 0
    for t in tracks:
        for i, cur in enumerate(song.tracks):
            if _same(cur, t):
                song.delete_track(i)
                gone += 1
                break
    return gone


def _stage1(ctx, scratch):
    browser, song = ctx.app.browser, ctx.song
    t1, t2 = scratch.midi_track(), scratch.midi_track()
    st = {"stage": 1, "tracks": [t1, t2], "waits": 0, "errors": {}}
    instrument = None
    for name in PREFERRED_INSTRUMENTS:
        instrument = _find(browser.instruments, lambda c, n=name: c.name == n and c.is_loadable)
        if instrument:
            break
    rack = _find(browser.instruments, lambda c: c.name == "Drum Rack" and c.is_loadable)
    st["instrument_name"] = instrument.name if instrument else None
    st["rack_found"] = rack is not None
    st["hotswap_target_at_start"] = str(browser.hotswap_target)
    sample = _find(browser.drums, lambda c: c.is_loadable and not c.is_device)
    if sample is not None:
        try:
            browser.preview_item(sample)
            st["preview"] = {"ok": True, "item": sample.name}
        except Exception as exc:  # noqa: BLE001
            st["preview"] = {"ok": False, "error": _err(exc)}
        finally:
            try:
                browser.stop_preview()
            except Exception as exc:  # noqa: BLE001
                st["errors"]["stop_preview"] = _err(exc)
    for key, track, item in (("instrument", t1, instrument), ("drum_rack", t2, rack)):
        if item is None:
            continue
        try:
            song.view.selected_track = track
            browser.load_item(item)
        except Exception as exc:  # noqa: BLE001
            st["errors"][f"load_{key}"] = _err(exc)
    st["devices_immediately"] = [_device_names(t1), _device_names(t2)]
    scratch.created[:] = [(k, o) for k, o in scratch.created if o is not t1 and o is not t2]
    return st


def _stage2(ctx, st):
    browser, song = ctx.app.browser, ctx.song
    t1, t2 = st["tracks"]
    st["t1_devices"], st["t2_devices"] = _device_names(t1), _device_names(t2)
    rack = next((d for d in t2.devices if getattr(d, "can_have_drum_pads", False)), None)
    if rack is None:
        return False
    st["pad_chains_before"] = None
    pad = next((p for p in rack.drum_pads if p.note == 36), None)
    st["pad_found"] = pad is not None
    sample = _find(browser.drums, lambda c: c.is_loadable and not c.is_device)
    st["sample_name"] = sample.name if sample else None
    if pad is None or sample is None:
        return True
    st["pad_chains_before"] = len(list(pad.chains))
    try:
        song.view.selected_track = t2
        song.view.select_device(rack)
        song.view.selected_drum_pad = pad if hasattr(song.view, "selected_drum_pad") else None
    except Exception as exc:  # noqa: BLE001
        st["errors"]["select_pad"] = _err(exc)
    try:
        rack.view.selected_drum_pad = pad
        st["selected_pad_via_rack_view"] = True
    except Exception as exc:  # noqa: BLE001
        st["selected_pad_via_rack_view"] = False
        st["errors"]["rack_view_selected_drum_pad"] = _err(exc)
    st["hotswap_target_before_sample_load"] = str(browser.hotswap_target)
    try:
        browser.load_item(sample)
    except Exception as exc:  # noqa: BLE001
        st["errors"]["load_sample"] = _err(exc)
    return True


def _final(st):
    t2 = st["tracks"][1]
    rack = next((d for d in t2.devices if getattr(d, "can_have_drum_pads", False)), None)
    pad = next((p for p in rack.drum_pads if p.note == 36), None) if rack else None
    chains = list(pad.chains) if pad else []
    chain_devices = [[d.name for d in c.devices] for c in chains]
    landed = any("Operator" == n or n == st.get("instrument_name") for n in st["t1_devices"])
    in_chain = len(chains) > (st.get("pad_chains_before") or 0) and any(chain_devices)
    return landed, in_chain, chain_devices, len(list(t2.devices))


def run(ctx, scratch):
    browser = ctx.app.browser
    api_present = hasattr(browser, "load_item") and hasattr(browser, "hotswap_target")
    if not api_present:
        return {"verdict": verdict_for(False, False, False)}
    st = _STATE.get("st")
    song = ctx.song
    if st is not None and not all(any(_same(c, t) for c in song.tracks) for t in st["tracks"]):
        _STATE.clear()
        st = None
    if st is None:
        try:
            st = _stage1(ctx, scratch)
        except Exception:
            _STATE.clear()
            raise
        _STATE["st"] = st
        return {
            "verdict": "no-go",
            "complete": False,
            "stage": 1,
            "next": "re-run P-14",
            "instrument": st["instrument_name"],
            "rack_found": st["rack_found"],
        }
    try:
        if st["stage"] == 1:
            st["waits"] += 1
            if not _stage2(ctx, st):
                if st["waits"] < MAX_WAIT_RUNS:
                    return {
                        "verdict": "no-go",
                        "complete": False,
                        "stage": 1,
                        "next": "re-run P-14 (the load has not landed yet)",
                    }
                st["final"] = (False, False, [], 0)
            else:
                st["stage"] = 2
                return {
                    "verdict": "no-go",
                    "complete": False,
                    "stage": 2,
                    "next": "re-run P-14",
                    "t1_devices": st["t1_devices"],
                    "t2_devices": st["t2_devices"],
                }
        else:
            st["final"] = _final(st)
        landed, in_chain, chain_devices, t2_count = st["final"]
        report = {
            "verdict": verdict_for(True, landed, in_chain),
            "complete": True,
            "instrument_on_midi_track": {"landed": landed, "devices": st.get("t1_devices")},
            "drum_rack_track_devices": st.get("t2_devices"),
            "pad_note_36": {
                "found": st.get("pad_found"),
                "sample": st.get("sample_name"),
                "chains_before": st.get("pad_chains_before"),
                "chain_devices_after": chain_devices,
                "selected_via_rack_view": st.get("selected_pad_via_rack_view"),
            },
            "hotswap_target": {
                "at_start": st["hotswap_target_at_start"],
                "before_sample_load": st.get("hotswap_target_before_sample_load"),
            },
            "preview": st.get("preview"),
            "errors": st["errors"],
            "not_run": ["load into an Instrument Rack chain (needs a chain-bearing rack)"],
            "tracks_deleted": 0,
        }
        report["tracks_deleted"] = _drop(song, st["tracks"])
        _STATE.clear()
        return report
    except Exception:
        _drop(song, st["tracks"])
        _STATE.clear()
        raise
