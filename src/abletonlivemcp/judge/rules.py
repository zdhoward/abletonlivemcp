"""Keyword fallback judge. Coarse by design: it says 'unsure' rather than guessing."""

from __future__ import annotations

import re

from . import PluginJudgment, SampleJudgment

_DRUM_WORDS = {
    "kick": ("kick", "bd", "bassdrum"),
    "snare": ("snare", "snr", "sd"),
    "clap": ("clap", "clp"),
    "hat_open": ("openhat", "ohh", "oh"),
    "hat_closed": ("closedhat", "chh", "ch", "hat", "hihat", "hh"),
    "tom": ("tom",),
    "cymbal": ("crash", "ride", "cymbal", "cym"),
    "percussion": ("perc", "shaker", "conga", "bongo", "tamb", "rim"),
}
_LOOP_WORDS = ("loop", "bpm", "phrase", "groove", "break")

_PLUGIN_WORDS = {
    "eq": ("eq", "equaliz", "equalis", "proq"),
    "compressor": ("comp", "compress"),
    "limiter": ("limit", "maximi"),
    "reverb": ("reverb", "verb", "hall", "plate"),
    "delay": ("delay", "echo"),
    "saturation": ("sat", "drive", "distort", "tape", "tube", "overdrive"),
    "modulation": ("chorus", "phaser", "flanger", "tremolo", "ensemble"),
    "filter": ("filter",),
    "synth": ("synth", "nexus", "serum", "massive", "sylenth", "diva", "wavetable"),
    "sampler": ("sampler", "kontakt", "simpler"),
    "utility": ("utility", "gain", "pan", "meter"),
}


def _tokens(text: str) -> list[str]:
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return [t for t in re.split(r"[^A-Za-z0-9]+", spaced.lower()) if t]


def _has(words: tuple[str, ...], toks: list[str]) -> bool:
    """Short keywords must be a whole token; longer ones may sit inside a token."""
    joined = "".join(toks)
    return any((w in toks) if len(w) <= 3 else (w in joined) for w in words)


class RuleJudge:
    name = "rules"

    def classify_sample(self, file_name: str, folders: list[str]) -> SampleJudgment:
        toks = _tokens(file_name)
        if _has(_LOOP_WORDS, toks) or re.search(r"\b\d{2,3}\s*bpm\b", file_name, re.I):
            return SampleJudgment(file_name, "no", None, self.name)
        for dtype, words in _DRUM_WORDS.items():
            if _has(words, toks):
                return SampleJudgment(file_name, "yes", dtype, self.name)
        return SampleJudgment(file_name, "unsure", None, self.name)

    def classify_plugin(self, plugin_name: str, plugin_format: str | None) -> PluginJudgment:
        toks = _tokens(plugin_name)
        for category, words in _PLUGIN_WORDS.items():
            if _has(words, toks):
                return PluginJudgment(plugin_name, category, self.name)
        return PluginJudgment(plugin_name, None, self.name)
