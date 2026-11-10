"""Starting-point vocal chains expressed as roles, and a rough gear lookup.

CAVEAT: these values come from general mixing practice. They are NOT taken from any artist or
article and have not been judged by ear; treat them as a first pass to adjust. The gear lookup
names the closest stock device and the character to aim for; it is an approximation, not an
emulation.
"""

from __future__ import annotations

_EQ_CLEAN = {"high_pass": "80 Hz", "cut_freq": "250 Hz", "cut_gain": "-2 dB"}

# Stages name a ROLE and an intent, not a device. `plan_chain` (resolve.py) turns them into the
# devices this user prefers and owns, falling back to stock. A reverb decay carries a physical
# value for devices that show units and a level for devices that do not.
PRESETS: dict[str, dict] = {
    "vocal_clean_lead": {
        "description": "Transparent lead vocal: high-pass, mud cut, gentle compression, light "
        "saturation, short reverb.",
        "stages": [
            {"role": "eq", "intent": _EQ_CLEAN},
            {
                "role": "compressor",
                "intent": {
                    "style": "Vocal",
                    "threshold": "-18 dB",
                    "ratio": 4,
                    "attack": "5 ms",
                    "release": "80 ms",
                },
            },
            {"role": "saturation", "intent": {"drive": "3 dB", "mix": "30 %"}},
            {
                "role": "reverb",
                "intent": {
                    "predelay": "20 ms",
                    "decay": {"value": "1.2 s", "level": "short"},
                    "mix": "12 %",
                },
            },
        ],
    },
    "vocal_aggressive": {
        "description": "Forward, dense vocal: harder compression and more saturation, tighter "
        "reverb.",
        "stages": [
            {"role": "eq", "intent": _EQ_CLEAN},
            {
                "role": "compressor",
                "intent": {
                    "style": "Punch",
                    "threshold": "-24 dB",
                    "ratio": 8,
                    "attack": "1 ms",
                    "release": "50 ms",
                },
            },
            {"role": "saturation", "intent": {"drive": "8 dB", "mix": "50 %"}},
            {
                "role": "reverb",
                "intent": {
                    "predelay": "10 ms",
                    "decay": {"value": "0.8 s", "level": "short"},
                    "mix": "8 %",
                },
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
