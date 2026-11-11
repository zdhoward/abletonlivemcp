"""P-15: PluginDevice.get_parameter_names, presets, selected_preset_index (coverage vs parameters).

Behavioural probe (write), two stages (a load lands on a later tick). State lives in ``_STATE``
(the Remote Script process); ``complete: false`` in the result means "re-run":

- stage 1: find up to two loadable plugin items under ``Browser.plugins`` and load each onto its
  own scratch MIDI track. The tracks are handed off from ``scratch`` to this module so the
  end-of-run scratch cleanup does not delete them before the load lands; they are deleted here
  at the final stage, or if a stage fails.
- stage 2: for each loaded ``PluginDevice`` record ``len(parameters)`` (the configured
  parameters), ``len(get_parameter_names())``, ``len(presets)`` and ``selected_preset_index``.

Limits recorded in the evidence: the probe needs two installed plugins (VST/AU); fewer is a
``no-go`` with the count found. Presets are read, never selected.

Verdict: ``gated`` when ``PluginDevice`` lacks the three members (or ``Browser.plugins`` is
absent); ``go`` when two plugins were read with all counts recorded; otherwise ``no-go``.
"""

from .dom_common import WRITE, _same

PROBE_ID = "P-15"
KIND = WRITE

WANT = 2
MAX_WAIT_RUNS = 3
WALK_BUDGET = 800
MEMBERS = ("get_parameter_names", "presets", "selected_preset_index")
_STATE = {}


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def verdict_for(api_present, plugins):
    """Pure verdict rule. ``plugins`` is a list of per-plugin dicts (``counts_ok`` flag)."""
    if not api_present:
        return "gated"
    ok = [p for p in plugins if p.get("counts_ok")]
    return "go" if len(ok) >= WANT else "no-go"


def _children(item):
    it = getattr(item, "iter_children", None)
    return list(it) if it is not None else list(getattr(item, "children", []))


def _find_all(root, limit, budget=WALK_BUDGET):
    found, queue, seen = [], [root], 0
    while queue and seen < budget and len(found) < limit:
        node = queue.pop(0)
        seen += 1
        for child in _children(node):
            if getattr(child, "is_loadable", False) and getattr(child, "is_device", False):
                if len(found) < limit and all(child.name != f.name for f in found):
                    found.append(child)
            elif getattr(child, "is_folder", False):
                queue.append(child)
    return found


def _drop(song, tracks):
    for t in tracks:
        for i, cur in enumerate(song.tracks):
            if _same(cur, t):
                song.delete_track(i)
                break


def _read(track):
    for d in track.devices:
        if all(hasattr(d, m) for m in MEMBERS):
            info = {"name": d.name, "class_name": getattr(d, "class_name", None)}
            try:
                info["parameters"] = len(list(d.parameters))
                info["parameter_names"] = len(list(d.get_parameter_names()))
                info["presets"] = len(list(d.presets))
                info["selected_preset_index"] = d.selected_preset_index
                info["counts_ok"] = True
            except Exception as exc:  # noqa: BLE001
                info.update(counts_ok=False, error=_err(exc))
            return info
    return None


def run(ctx, scratch):
    browser, song = ctx.app.browser, ctx.song
    if not hasattr(browser, "plugins"):
        return {"verdict": verdict_for(False, []), "reason": "Browser.plugins is absent"}
    st = _STATE.get("st")
    if st is not None and not all(any(_same(c, t) for c in song.tracks) for t in st["tracks"]):
        _STATE.clear()
        st = None
    if st is None:
        items = _find_all(browser.plugins, WANT)
        if len(items) < WANT:
            return {
                "verdict": "no-go",
                "complete": True,
                "reason": f"needs {WANT} installed plugins; found {len(items)}",
                "found": [i.name for i in items],
            }
        tracks, errors = [], {}
        try:
            for item in items:
                track = scratch.midi_track()
                tracks.append(track)
                try:
                    song.view.selected_track = track
                    browser.load_item(item)
                except Exception as exc:  # noqa: BLE001
                    errors[item.name] = _err(exc)
        finally:
            scratch.created[:] = [(k, o) for k, o in scratch.created if o not in tracks]
        _STATE["st"] = {
            "tracks": tracks,
            "items": [i.name for i in items],
            "errors": errors,
            "waits": 0,
        }
        return {
            "verdict": "no-go",
            "complete": False,
            "stage": 1,
            "next": "re-run P-15",
            "loading": [i.name for i in items],
        }
    st["waits"] += 1
    try:
        plugins = [_read(t) for t in st["tracks"]]
        if None in plugins and st["waits"] < MAX_WAIT_RUNS:
            return {
                "verdict": "no-go",
                "complete": False,
                "stage": 1,
                "next": "re-run P-15 (a load has not landed yet)",
            }
        plugins = [p for p in plugins if p is not None]
        report = {
            "verdict": verdict_for(True, plugins),
            "complete": True,
            "requested": st["items"],
            "plugins": plugins,
            "errors": st["errors"],
            "limits": [
                f"needs {WANT} installed plugins",
                "presets are read, not selected",
                "plugins that are not PluginDevice (e.g. Max devices) are not counted",
            ],
        }
        _drop(song, st["tracks"])
        _STATE.clear()
        return report
    except Exception:
        _drop(song, st["tracks"])
        _STATE.clear()
        raise
