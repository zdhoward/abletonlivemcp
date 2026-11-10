"""Starting-point vocal chains made only of Live's stock effects, and a rough gear lookup.

CAVEAT: these values come from general mixing practice. They are NOT taken from any artist or
article and have not been judged by ear; treat them as a first pass to adjust. The gear lookup
names the closest stock device and the character to aim for; it is an approximation, not an
emulation.
"""

from __future__ import annotations

_EQ_CLEAN = {
    "1 Filter On A": True,
    "1 Filter Type A": "High Pass 12dB",
    "1 Frequency A": "80 Hz",
    "2 Frequency A": "250 Hz",
    "2 Gain A": "-2 dB",
}

PRESETS: dict[str, dict] = {
    "vocal_clean_lead": {
        "description": "Transparent lead vocal: high-pass, mud cut, gentle compression, light "
        "saturation, short reverb.",
        "stages": [
            {"device": "EQ Eight", "params": _EQ_CLEAN},
            {
                "device": "Compressor",
                "params": {"Threshold": "-18 dB", "Ratio": 4, "Attack": "5 ms", "Release": "80 ms"},
            },
            {"device": "Saturator", "params": {"Drive": "3 dB", "Dry/Wet": "30 %"}},
            {
                "device": "Reverb",
                "params": {"Predelay": "20 ms", "Decay Time": "1.2 s", "Dry/Wet": "12 %"},
            },
        ],
    },
    "vocal_aggressive": {
        "description": "Forward, dense vocal: harder compression and more saturation, tighter "
        "reverb.",
        "stages": [
            {"device": "EQ Eight", "params": _EQ_CLEAN},
            {
                "device": "Compressor",
                "params": {"Threshold": "-24 dB", "Ratio": 8, "Attack": "1 ms", "Release": "50 ms"},
            },
            {"device": "Saturator", "params": {"Drive": "8 dB", "Dry/Wet": "50 %"}},
            {
                "device": "Reverb",
                "params": {"Predelay": "10 ms", "Decay Time": "0.8 s", "Dry/Wet": "8 %"},
            },
        ],
    },
}

# gear name (lowercase) -> closest stock device and what to aim for
GEAR: dict[str, dict] = {
    "1176": {
        "device": "Compressor",
        "aim": "fast attack (about 0.3-1 ms), ratio 4-8, quick release",
    },
    "la-2a": {"device": "Compressor", "aim": "slow attack, soft knee, ratio 3-4, slow release"},
    "distressor": {"device": "Compressor", "aim": "ratio 4-6, medium attack, add Saturator after"},
    "ssl bus compressor": {"device": "Glue Compressor", "aim": "ratio 2-4, attack 10-30 ms"},
    "pultec": {"device": "EQ Eight", "aim": "broad low and high shelves, gentle boosts"},
    "neve 1073": {"device": "EQ Eight", "aim": "shelves plus a mid bell; add Saturator for color"},
    "de-esser": {"device": "Multiband Dynamics", "aim": "compress the 5-8 kHz band only"},
    "plate reverb": {"device": "Reverb", "aim": "decay 1-2 s, high diffusion, predelay 10-30 ms"},
    "tape delay": {"device": "Echo", "aim": "wobble and noise on, feedback 30-40%"},
}


def stock_equivalent(gear: str) -> dict:
    hit = GEAR.get(gear.strip().lower())
    if hit is None:
        return {"gear": gear, "known": False, "known_gear": sorted(GEAR)}
    return {"gear": gear, "known": True, **hit, "approximate": True}
