# Keys and synths: FX chain patterns by role

Synthesized 2026-11-10 from `research/raw/2026-11-10-keys-synths.md`. Related pages: [vocals](vocals.md), [drums](drums.md), [busses-mixing](busses-mixing.md), [mastering](mastering.md), [guitar-bass](guitar-bass.md).

## 1. Scope and how to read this page

**No famous-recording chains.** The collector found NO chain tied to a named famous recording for keys or synths. Nothing below is "the chain from record X". Everything is a documented author workflow, a convention or an opinion. Do not present any of it as a famous chain.

Labels:
- FACT: an author's documented workflow (not a famous record).
- CONVENTION: an engineer's or educator's general recommendation.
- OPINION: single-blog or wiki advice.

Confirmation status (re-opened on 2026-11-10):
- CONFIRMED: number matched the original page.
- UNCONFIRMED-NUMBER: not re-checked, or the page could not be read.
- UNVERIFIED: page unreadable (both MusicRadar pages truncated even after a retry). Content from them is excluded from all tables.

Stage order used for keys and synths: EQ/high-pass, compression, saturation (optional), modulation or widener, then reverb and delay on returns (filtered, often ducked).

## 2. Consensus patterns by instrument type

### Piano
| Role | Setting range | Source / label / status |
|---|---|---|
| EQ | small cut 300-600 Hz; HP ~200 Hz when heavy bass/kick; dip ~6 dB at 2-3 kHz to sit behind vocals; lift near 9 kHz (no gain given) | Music Guy Mixing (OPINION, CONFIRMED); Sage Audio (OPINION, CONFIRMED) |
| Compressor | 3:1, attack 5-10 ms, ~5 dB GR or less; release is in conflict (section 3) | both CONFIRMED |
| Mono | near-mono in busy mixes | Music Guy (OPINION, not re-checked) |
| Chorus/modulation | on a send, before reverb, no numbers | Music Guy (OPINION, UNCONFIRMED-NUMBER n/a) |
| Reverb | send, 100% wet, ~1.5 s decay, 20-30 ms pre-delay, filter lows and highs off the return | Music Guy (OPINION, CONFIRMED) |

### Electric piano (Ableton workflow)
Order: instrument (mono) -> tremolo/auto-pan (creates stereo) -> L/R-mode EQ (highs cut one side, lows the other) -> parallel chorus/flanger/phaser rack with dry chain -> optional tube/overdrive/saturation -> amp + cabinet last, in Dual mode. Mono amp mode only if all stereo effects follow it. Mallet Stiffness/Force: avoid much below 50%. Source: Rhodes Hog, Sound on Sound (FACT as a workflow, CONFIRMED). No frequencies, rates or amounts exist in the source.

### Organ
No usable source. See section 4.

### Pads and strings
| Role | Setting range | Source / label / status |
|---|---|---|
| High-pass / mud cut | 150-250 Hz (Myloops); ~200 Hz or ~300 Hz (Senior, conflict in section 3); 50-100 Hz for sampled/orchestral strings (wiki) | CONFIRMED |
| Presence cut | 4-6 dB around 3-4 kHz (narrow); strings 2-4 kHz, -2 to -5 dB | Senior (CONVENTION, CONFIRMED); strings wiki (OPINION, cut dB/Q not re-checked) |
| Compression (sampled strings) | 2:1, attack 30-80 ms, release 150-300 ms | strings wiki (OPINION, CONFIRMED) |
| Modulation before reverb | gentle stereo chorus/flanger/detune first; strings detune 5-10 cents with 20-50 ms delays on detuned copies (the source gives these for choirs and says strings can reuse them) | Paul White 1994 (CONVENTION, CONFIRMED, dated) |
| Widening | chorus/flanger/phaser, M/S, L/R pitch offsets; unison + low cut with correlation meter | Senior; Ableton blog (CONVENTION, CONFIRMED) |
| Reverb | warm pads: none; short reverb for bright pads needing width. Strings: hall 2.5-4 s, 10-20 ms pre-delay (wiki), return HP 150-200 Hz; White says ~3 s | CONFIRMED |
| Level / automation | "if you can hear it, it's too loud"; automate highs out in verses | Senior (not re-checked verbatim); Ableton blog (CONVENTION) |
| Detune (Wavetable) | 1-10%, first oscillator near zero; vibrato LFO ~10%; noise unison ~40% | Ableton blog (CONVENTION, CONFIRMED) |

### Plucks, leads, arps
- Leads stay mostly untouched; duck the reverb and delay returns instead (Myloops, OPINION).
- Plucks: no dedicated settings in any confirmed source. Arps: filter lows and highs so they sit back (EDMProd, thin).
- Delay: ping-pong or short stereo offset, HP the return (Serkan Cura, OPINION; return HP value not given).

### Synth bass
| Role | Setting range | Source / status |
|---|---|---|
| Layers | one layer owns sub <100 Hz; HP other layers ~100 Hz | Senior 2012 (CONVENTION, CONFIRMED) |
| Compressor | 4:1 or higher, attack 1-30 ms (White: 10-50 ms) | CONFIRMED |
| Multiband | lowest band only, ~8:1, attack ~5 ms, release ~80 ms, 8-12 dB GR | CONFIRMED |
| Sidechain | duck 2-3 dB per kick | CONFIRMED |
| Tone | LP ~2-3 kHz after mid boosts; narrow cut Q ~8 | CONFIRMED |
| Placement | mostly dry, centre pan | White (CONFIRMED) |

### Supersaw and trance leads
Order (Serkan Cura, OPINION, low-medium confidence): mono sub saw plus wide stack -> HP 100-150 Hz on wide layer -> saturation on summed stack -> EQ dip 2-4 dB at 200-400 Hz -> stereo imaging last. Detune total spread: <5 cents thickening, 8-20 classic, 25-40 deliberate (all CONFIRMED). Reverb: mono send, stereo return, send HP 300-400 Hz, LP ~8 kHz (CONFIRMED). Lead sidechain 40-80 ms release, 2-4 dB (CONFIRMED). The Syntorial patch (FACT, workflow only, not re-checked) goes light distortion -> compression -> large damped reverb, no delay, no EQ.

### Sidechain tiers (pads, returns)
| Tier | Ratio | Attack | Release | Reduction | Status |
|---|---|---|---|---|---|
| Subtle breathing pad | 2:1 | 5-10 ms | 250-400 ms | 3-5 dB | Myloops (OPINION, CONFIRMED) |
| Obvious pump | 4:1+ | fast | 1/8 note or 150-400 ms | 6-12 dB | UNCONFIRMED-NUMBER (RingMod, Producer's Bible not opened) |
| Reverb return duck | 4:1 | fastest | 200-300 ms | 4-7 dB | Myloops (CONFIRMED) |
| Delay return duck | similar | fast | ~150 ms | 3-5 dB | Myloops (CONFIRMED) |
| Strings reverb duck (kick) | n/a | 1-5 ms | 80-150 ms | 4-6 dB | strings wiki (CONFIRMED) |

Chain note from Myloops: widener/chorus before the compressor, reverb after it so the tail is not chopped.

## 3. Conflicts between sources

| Topic | Values | Reading |
|---|---|---|
| Piano compressor release | 50 ms (Music Guy) vs ~1000 ms (Sage) | Both CONFIRMED and unresolved. Sage calls ~1000 ms the gentler, dynamics-preserving setting. Treat 50 ms as tight/controlled and ~1000 ms as smooth; expose as a choice. |
| Piano compressor attack | 5 ms vs 10 ms | Minor; use 5-10 ms. |
| Pad high-pass | ~300 Hz (Senior caption) vs "below ~200 Hz rarely useful" (Senior text) vs 150-250 Hz (Myloops) | Same article disagrees with itself. Use 150-300 Hz, start ~200 Hz. |
| Strings vs pad HP | 50-100 Hz vs 150-300 Hz | Instrument-dependent (sampled orchestral vs synth pad). Not a real conflict. |
| Pad sidechain release | 100-150 ms (Ramesh) vs 250-400 ms (Myloops) | Ramesh not opened (UNCONFIRMED-NUMBER). Tiers likely explain it. |

## 4. Uncertainty and gaps

- No usable source: organ/Leslie (only forum opinion; SOS Hammond article is about modelling, 800 Hz crossover UNVERIFIED), trap keys, ambient pads, pop keys.
- Electric piano: only the Ableton workflow, no numbers. The "suitcase tremolo -> chorus -> echo" idea was a forum guess, not recorded.
- Synthwave (EDMProd): thin, little keys-specific data.
- Paul White (1994) is hardware-era; ordering is useful, numbers less so.
- Several 2026 pages (Myloops, Serkan Cura, Music Production Wiki) are single-site blog content with no cited sources: treat as OPINION.
- MusicRadar piano/keys chain and sidechain pages: UNVERIFIED (truncated twice). Their claimed content (air EQ, 2:1-4:1 bus-style compression, tempo-synced stereo delay, pad swell by dropping kicks) is not used.
- Generic Ableton arp/pluck chain (EDMProd, Splice) and vocal-oriented return numbers (tunedrip): not opened, excluded.
- Ableton Reference Manual not consulted.

## 5. Sources and re-verification status

| Source | URL | Status |
|---|---|---|
| Music Guy Mixing, piano | https://www.musicguymixing.com/mix-piano/ | RE-VERIFIED |
| Sage Audio, piano | https://www.sageaudio.com/articles/mix-piano-pt-1 | RE-VERIFIED |
| SOS, synth pads (Senior 2010) | https://www.soundonsound.com/techniques/creating-using-synth-pad-sounds | RE-VERIFIED |
| Myloops, trance sidechain | https://www.myloops.net/sidechain-compression-techniques-for-trance | RE-VERIFIED |
| Serkan Cura, supersaw | https://www.serkancura.com/en/muzik-en/anatomy-of-the-supersaw/ | RE-VERIFIED |
| SOS, Mixing Bass (Senior 2012) | https://www.soundonsound.com/techniques/mixing-bass | RE-VERIFIED |
| Music Production Wiki, strings | https://musicproductionwiki.com/articles/how-to-mix-strings | RE-VERIFIED |
| SOS, keyboard effects (White 1994) | https://www.soundonsound.com/techniques/using-effects-keyboards | RE-VERIFIED |
| Ableton blog, pads | https://www.ableton.com/en/blog/pad-it-out-10-ways-make-distinctive-pad-sounds/ | RE-VERIFIED |
| SOS, Rhodes Hog | https://www.soundonsound.com/techniques/rhodes-hog | RE-VERIFIED |
| Syntorial, supersaw lead | https://www.syntorial.com/tutorials/synth-quickie-supersaw-trance-lead/ | not re-checked (collector read) |
| EDMProd, synthwave | https://www.edmprod.com/how-to-make-synthwave/ | not re-checked (collector read) |
| MusicRadar piano and keys chain | https://www.musicradar.com/how-to/save-time-with-this-solid-piano-and-keys-mixing-chain | UNVERIFIED (truncated twice) |
| MusicRadar pumping sidechain | https://www.musicradar.com/tuition/tech/how-to-create-classic-pumping-sidechain-compression-624915 | UNVERIFIED (truncated twice) |
| Ramesh, Producer's Bible, RingMod | rameshmusic.com/sidechain-compression-tutorial/ ; musicproductionwiki.com/bible/sidechain-compression ; ringmodsidechain.com/blog/sidechain-compression-settings | not opened, UNCONFIRMED-NUMBER |
