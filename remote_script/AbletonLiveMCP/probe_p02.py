"""P-02: Song.get_data/set_data: value types, size limit, survival across Save and reopen.

Behavioural (write) probe. ``Song.set_data`` writes into the open Set (the Set is expected to be a
disposable one), under keys that all start with ``almcp_p02_``. Every key is overwritten with ``""``
afterwards except ``almcp_p02_reopen``, which keeps a 4096-character JSON string on purpose: the
save and reopen half cannot be automated here, so the result carries ``needs_reopen_check: true``
and the key, length and checksum to compare after the Set is saved and reopened.
checked on a scratch track the probe made through ``scratch``.

Verdict: ``gated`` when ``Song.get_data``/``set_data`` are absent; ``go`` when a plain string and
the 4 KB JSON string round-trip in this session (reopen check still pending); else ``no-go``.
"""

import json

from .dom_common import WRITE

PROBE_ID = "P-02"
KIND = WRITE

PREFIX = "almcp_p02_"
REOPEN_KEY = PREFIX + "reopen"
REOPEN_LENGTH = 4096
MISSING = "<almcp-missing>"
SIZES = (1024, 4096, 16384, 65536, 262144, 1048576)


def _err(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def reopen_payload():
    """A JSON string of exactly REOPEN_LENGTH characters (deterministic)."""
    head = json.dumps({"probe": "P-02", "pad": ""})
    pad = "abcdefghij" * (REOPEN_LENGTH // 10 + 1)
    return json.dumps({"probe": "P-02", "pad": pad[: REOPEN_LENGTH - len(head)]})


def verdict_for(api_present, str_ok, json_ok):
    """Pure verdict rule (kept separate so it is unit-testable)."""
    if not api_present:
        return "gated"
    return "go" if str_ok and json_ok else "no-go"


def _roundtrip(obj, key, value):
    """set then get one value; returns a small evidence dict."""
    info = {"set_error": None, "get_error": None}
    try:
        obj.set_data(key, value)
    except Exception as exc:  # noqa: BLE001 - the exact error text is the evidence
        info["set_error"] = _err(exc)
        info["equal"] = False
        return info
    try:
        got = obj.get_data(key, MISSING)
    except Exception as exc:  # noqa: BLE001
        info["get_error"] = _err(exc)
        info["equal"] = False
        return info
    info["returned_type"] = type(got).__name__
    info["equal"] = bool(got == value and type(got) is type(value))
    info["value_equal"] = bool(got == value)
    info["sample"] = repr(got)[:60]
    return info


def run(ctx, scratch):
    song = ctx.song
    api_present = all(hasattr(song, n) for n in ("get_data", "set_data"))
    if not api_present:
        return {
            "verdict": "gated",
            "reason": "Song.get_data/set_data absent",
            "needs_reopen_check": False,
        }

    cases = [
        ("str", "hello"),
        ("unicode", "héllo ✓"),
        ("int", 42),
        ("float", 1.5),
        ("bool", True),
        ("none", None),
        ("list", [1, "a", 2.5]),
        ("dict", {"a": 1, "b": [1, 2]}),
    ]
    types = {}
    written = []
    sizes = {}
    track_info = None
    reopen = None
    try:
        for label, value in cases:
            key = PREFIX + label
            written.append(key)
            types[label] = _roundtrip(song, key, value)

        # Missing key: the default comes back.
        try:
            missing = song.get_data(PREFIX + "never_set", MISSING) == MISSING
        except Exception as exc:  # noqa: BLE001
            missing = _err(exc)

        size_key = PREFIX + "size"
        written.append(size_key)
        max_ok = 0
        for n in SIZES:
            info = _roundtrip(song, size_key, "x" * n)
            sizes[str(n)] = {
                "equal": info["equal"],
                "set_error": info["set_error"],
                "get_error": info["get_error"],
            }
            if not info["equal"]:
                break
            max_ok = n

        payload = reopen_payload()
        reopen_info = _roundtrip(song, REOPEN_KEY, payload)
        json_ok = bool(reopen_info["equal"]) and json.loads(payload)["probe"] == "P-02"
        reopen = {
            "key": REOPEN_KEY,
            "length": len(payload),
            "checksum": sum(map(ord, payload)) % 1000003,
            "round_trip_in_session": reopen_info,
        }

        track = scratch.midi_track()
        if hasattr(track, "set_data"):
            track_info = _roundtrip(track, PREFIX + "track", "track-data")
        else:
            track_info = {"absent": True}
    finally:
        cleared = {}
        for key in written:  # there is no delete: overwrite so the Set does not keep large values
            try:
                song.set_data(key, "")
                cleared[key] = True
            except Exception as exc:  # noqa: BLE001
                cleared[key] = _err(exc)

    str_ok = bool(types["str"]["equal"])
    return {
        "verdict": verdict_for(True, str_ok, json_ok),
        "needs_reopen_check": True,
        "reopen_check": reopen,
        "types": types,
        "missing_key_returns_default": missing,
        "size_limit": {
            "max_ok_chars": max_ok,
            "tried": sizes,
            "ceiling_not_reached": max_ok == SIZES[-1],
        },
        "track_data": track_info,
        "cleared_keys": cleared,
    }
