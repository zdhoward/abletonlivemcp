"""Song extras (batch 2): groove pool, Link, quantization, count-in and tuning. No bridge methods of
its own: ``dom_session``'s ``get_session``/``set_session`` read and write these as session fields
(the ``song`` toolset is a compatibility name). Evidence: P-22 (go).

- Groove pool amounts, song groove amount, scale, MIDI recording quantization and both Link
  fields were written and read back on 12.2 (P-22). Link may need Link enabled in preferences.
- ``count_in_duration`` has no setter and the tuning fields are absent on 12.2: reads only, a
  write is refused ``unsupported`` before any native call.
"""

from .core import Invalid
from .dom_common import Refused, _index, _number, require

CAPABILITIES = {
    "song.groove_pool": ("supported", "P-22: groove amounts written and read back"),
    "song.link": ("supported", "P-22: both Link fields written and read back"),
    "song.count_in": ("unsupported", "P-22: count_in_duration has no setter on 12.2"),
    "song.tuning": ("unsupported", "P-22: tuning_system fields absent on 12.2"),
}

GROOVE_FIELDS = ("timing_amount", "quantization_amount", "random_amount", "velocity_amount")
LINK_FIELDS = {
    "link_enabled": "is_ableton_link_enabled",
    "link_start_stop_sync": "is_ableton_link_start_stop_sync_enabled",
}
GROOVE_LIMIT = 64


def _get(obj, attribute, default=None):
    try:
        return getattr(obj, attribute)
    except Exception:  # noqa: BLE001 - a read never fails the whole reply
        return default


def read_grooves(song):
    pool = _get(song, "groove_pool")
    grooves = list(_get(pool, "grooves", ()) or ())[:GROOVE_LIMIT]
    return [
        {"index": i, "name": _get(g, "name"), **{f: _get(g, f) for f in GROOVE_FIELDS}}
        for i, g in enumerate(grooves)
    ]


def read_link(song):
    return {key: _get(song, attr) for key, attr in LINK_FIELDS.items()}


def read_extras(song):
    """Read-only extras: count-in (no setter) and tuning (absent fields read as None)."""
    tuning = _get(song, "tuning_system")
    return {
        "count_in_duration": _get(song, "count_in_duration"),
        "tuning": None
        if tuning is None
        else {
            "name": _get(tuning, "name"),
            "reference_pitch": _get(tuning, "reference_pitch"),
        },
    }


def validate_grooves(ctx, items):
    """Pass 1 for ``grooves: [{index, expect_name?, <amount fields>}]`` -> prepared writes."""
    if not isinstance(items, list) or not 1 <= len(items) <= GROOVE_LIMIT:
        raise Invalid(f"'grooves' must be a list of 1..{GROOVE_LIMIT} objects")
    require(ctx, "song.groove_pool", ((ctx.song, "groove_pool"),))
    grooves = list(ctx.song.groove_pool.grooves)
    out = []
    for n, item in enumerate(items):
        if not isinstance(item, dict):
            raise Invalid("each groove must be an object")
        groove = grooves[_index(item.get("index"), f"grooves[{n}].index", len(grooves))]
        expected = item.get("expect_name")
        if expected is not None and expected != groove.name:
            raise Refused("name_mismatch", f"grooves[{n}]: the groove is named {groove.name!r}")
        values = {
            f: _number(item[f], f, -100 if f == "velocity_amount" else 0, 100)
            for f in GROOVE_FIELDS
            if item.get(f) is not None
        }
        if not values:
            raise Invalid(f"grooves[{n}]: give at least one amount")
        for field, value in values.items():
            out.append((f"groove[{item['index']}].{field}", groove, field, float(value)))
    return out


def validate_link(ctx, p):
    out = []
    for key, attribute in LINK_FIELDS.items():
        if p.get(key) is None:
            continue
        if not isinstance(p[key], bool):
            raise Invalid(f"{key!r} must be a bool")
        require(ctx, "song.link", ((ctx.song, attribute),))
        out.append((key, ctx.song, attribute, p[key]))
    return out


def refuse_read_only_extras(ctx, p):
    """Count-in and tuning writes: refused before any native call (never attempted)."""
    if p.get("count_in") is not None:
        require(ctx, "song.count_in")
    if p.get("tuning") is not None:
        require(ctx, "song.tuning")


METHODS = {}
