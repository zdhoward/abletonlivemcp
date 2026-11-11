"""Device adapters: how a musical role (compressor, reverb, ...) maps onto one specific device.

A chain says WHAT it needs ("a compressor, ratio 4, attack 5 ms"). An adapter says how one device
does that ("Pro-C 2: its `Ratio` parameter, solved from the display"). The resolver (resolve.py)
picks a device the user prefers and actually has, and falls back to a stock device.

Adding a device means adding one `Adapter` here, nothing else. To write one, load the device on a
track and read its parameter names and displays with `live_get_device_parameters`.

How much of a device Live lets a script control ("access"), measured on Live 12.2:
  full    - every musically relevant parameter is exposed (Pro-C 2, ValhallaVintageVerb)
  partial - some are (Pro-L 2)
  opaque  - only `Device On` is exposed; the device loads but cannot be set (Pro-Q 3, Pro-R)

Parameter modes (`mode` in a param spec):
  display      - solve from Live's own display text, e.g. "-18 dB" (default)
  percent_raw  - the device shows a bare 0..1 number; "12 %" is written as raw 0.12
  levels       - the device shows a bare 0..1 number with an unknown scale, so a named level
                 ("short", "medium", "long") maps to a raw value. These are GUESSES, flagged
                 uncalibrated in the plan; nobody has measured them against real units.
"""

from __future__ import annotations

from dataclasses import dataclass, field

STOCK = "audio_effects"
PLUGINS = "plugins"


@dataclass(frozen=True)
class Adapter:
    role: str
    device: str  # the name the user sees
    root: str  # STOCK or PLUGINS
    access: str  # "full" | "partial" | "opaque"
    params: dict = field(default_factory=dict)  # intent key -> {"param": name, "mode": ...}
    setup: dict = field(default_factory=dict)  # intent key -> {param name: target} also written
    notes: str = ""


def _p(name: str, mode: str = "display", **extra) -> dict:
    return {"param": name, "mode": mode, **extra}


_COMP = {
    "threshold": _p("Threshold"),
    "ratio": _p("Ratio"),
    "attack": _p("Attack"),
    "release": _p("Release"),
}

ADAPTERS: list[Adapter] = [
    # -- compressor ------------------------------------------------------------------------
    Adapter("compressor", "Compressor", STOCK, "full", _COMP),
    Adapter("compressor", "Pro-C 2", PLUGINS, "full", {**_COMP, "style": _p("Style")}),
    # -- equalizer -------------------------------------------------------------------------
    Adapter(
        "eq",
        "EQ Eight",
        STOCK,
        "full",
        {
            "high_pass": _p("1 Frequency A"),
            "cut_freq": _p("2 Frequency A"),
            "cut_gain": _p("2 Gain A"),
        },
        setup={"high_pass": {"1 Filter On A": True, "1 Filter Type A": "High Pass 12dB"}},
    ),
    Adapter(
        "eq",
        "Pro-Q 3",
        PLUGINS,
        "opaque",
        notes="Live exposes only 'Device On'. Save your own settings as a Live preset instead.",
    ),
    # -- saturation ------------------------------------------------------------------------
    Adapter(
        "saturation",
        "Saturator",
        STOCK,
        "full",
        {"drive": _p("Drive"), "mix": _p("Dry/Wet")},
    ),
    # -- reverb ----------------------------------------------------------------------------
    Adapter(
        "reverb",
        "Reverb",
        STOCK,
        "full",
        {"predelay": _p("Predelay"), "decay": _p("Decay Time"), "mix": _p("Dry/Wet")},
    ),
    Adapter(
        "reverb",
        "ValhallaVintageVerb",
        PLUGINS,
        "full",
        {
            "mix": _p("Mix", "percent_raw"),
            # Decay shows a bare 0..1 number; its real length depends on the reverb mode.
            "decay": _p("Decay", "levels", levels={"short": 0.3, "medium": 0.42, "long": 0.65}),
        },
        notes="Shows no units: predelay is not mapped and decay levels are uncalibrated guesses.",
    ),
    Adapter(
        "reverb",
        "Pro-R",
        PLUGINS,
        "opaque",
        notes="Live exposes only 'Device On'. Save your own settings as a Live preset instead.",
    ),
]


def adapters_for(role: str) -> list[Adapter]:
    return [a for a in ADAPTERS if a.role == role]


def known_roles() -> list[str]:
    return sorted({a.role for a in ADAPTERS})
