# Drums: FX chains by role

Related pages: [vocals](vocals.md), [busses-mixing](busses-mixing.md), [mastering](mastering.md), [guitar-bass](guitar-bass.md), [keys-synths](keys-synths.md).

## 1. Scope and how to read this page

Covers acoustic and programmed drums: per-drum chains, drum bus glue, parallel compression, kick-to-bass ducking. Organized by ROLE and stage order. Brand names appear only as "used in source X".

Labels:
- FACT: documented for a named record or a device's behaviour.
- CONVENTION: taught by a named engineer as common practice.
- OPINION: one author's or blog's recipe.

Confirmation status:
- CONFIRMED: number re-opened on the original URL on 2026-11-10 and matched.
- CORRECTED: the collector's number was wrong or imprecise; the fix is noted.
- UNCONFIRMED-NUMBER: not re-opened.
- LOW CONFIDENCE: seen only as a search snippet.

All settings are starting ranges, not rules. Sources are heavily hedged ("by ear", "probably").

## 2. Consensus patterns (by role and stage order)

### Per-drum

| Drum | Stage order | Setting range | Label, status, source |
|---|---|---|---|
| Kick | 1. gate | Sidechain filter upper limit about 1.5 kHz (or a little lower), fast attack (no number), release by ear, range about 12-15 dB (not full cut) | CONVENTION, CONFIRMED, White (SOS 2011) |
| Kick | 2. EQ | HPF below 30-40 Hz; boost 70-90 Hz; cut about 160-180 Hz (typically about 180 Hz); optional dip about 220 Hz; boost 3-4 kHz for beater | CONVENTION, CONFIRMED, White |
| Kick | 3. compressor | Attack about 20 ms, release about 80 ms, 3:1-4:1; optional limiter trimming about 6 dB off peaks | CONVENTION, CONFIRMED, White |
| Kick/snare | layering | Layer samples behind the original; check polarity and delay (flip polarity, find the cleanest attack) | CONVENTION, Senior 2003 and Brauer (Brauer: FACT) |
| Snare | crush | Parallel crushing of kick and snare alone, not the whole kit, keeps cymbals from harshening | CONVENTION; Joshua (FACT), White, Rogers |
| Snare (live kit) | gated overheads | Overheads gated, keyed from the snare track: lookahead 0, attack 1 ms, hold 30 ms, release 42 ms, reduction -6 dB, overheads fader +6 dB | CONVENTION, CONFIRMED, Senior 2003 (Logic-specific) |
| Toms | compressor | Compression for "explosive" tone, no settings found | FACT (Brauer); settings absent |
| Overheads / rooms | texture | Treat rooms as an aggressive, grainy compressed texture; overheads and far room about 4:1 at tracking (hedged, 2:1 sometimes for far room) | FACT, Avron, Brauer, Padgham |
| Hats | send level | Hats kept out of the parallel crush or sent low (hats 0 dB in a dirt bus, overheads -6 dB) | OPINION, Kim blog; Born Creative says send kick/snare/claps, not hats |

### Drum bus glue

| Parameter | Range | Status | Source |
|---|---|---|---|
| Ratio | 2:1 to 4:1 | CONFIRMED (Senior 2:1); Born Creative 4 | Senior (CONVENTION), Born Creative (OPINION) |
| Gain reduction | 2-4 dB on peaks; 6-8 dB for heavy pumping | CONFIRMED | Senior, Born Creative |
| Attack | 10 or 30 ms | CONFIRMED | Born Creative (OPINION) |
| Release | Over about 80 ms but resetting between hits; 0.1-0.2 s or Auto | CONFIRMED | Senior, Born Creative |
| Detection | Peak, hard knee preferred | UNCONFIRMED-NUMBER (not a number, not re-read) | Senior |
| Sidechain HPF | 80-100 Hz when the kick drives all compression | CONFIRMED | Born Creative |

Born Creative's Ableton bus chain (OPINION, CONFIRMED figures): Utility bass mono at 100-120 Hz, then EQ low cut 12 dB/oct at 20-30 Hz, then drum-shaping stage (Drum Buss with its comp off, low drive, damp lowered until fizz is gone), then glue compressor, then optional multiband on highs, then limiter or saturator last. Keep the 808/sub off the drum bus.

Other stage options (CONVENTION): a sidechain EQ low-passed isolates the kick; high-passed protects kick low end; band-passed reacts to the snare. Without a sidechain EQ, use equal-and-opposite EQ before and after the compressor (Senior, example 12 dB shelf cut above 100 Hz, CONFIRMED).

Routing (Rogers, SOS 2023, CONVENTION, structure only): three group buses (close mics, overheads, rooms/effects) feed one drum bus. Gate and EQ sit at the kick and snare subgroups. Parallel compression, saturation and distortion are aux channels fed from the groups.

### Parallel ("New York") compression

| Parameter | Range across sources | Status |
|---|---|---|
| Topology | Separate send/return so the squashed signal can be EQ'd; whole kit, or kick+snare only | CONVENTION (Senior, Rogers) |
| Ratio | 4:1 (Kim write-up) to 8:1+ (White) to 10:1 (Vesco, Born Creative) | CONFIRMED each |
| Attack | 0.03 ms (Vesco), "fastest" (Born Creative), 3 ms (Kim setup step; 1-5 ms in its description) | CONFIRMED |
| Release | 50 ms (Vesco), 0.1 s or Auto (Born Creative), brisk tempo-tuned (White) | CONFIRMED |
| Gain reduction | 6-12 dB average, peaks 12+ (Vesco); 8-15 dB (Born Creative); 10-15 dB (Kim); about 25 dB on peaks (White) | CONFIRMED |
| Return EQ | Low shelf +9 dB at 100 Hz, high shelf +9 dB at 7 kHz (Vesco); or low cut about 100-150 Hz after the compressor (Born Creative) | CONFIRMED. These are opposed approaches (boost lows vs cut lows) |
| Blend | About -15 dB (White); -12 to -18 dB (Kim); -10 to -15 dB (Kim KS Crush); by ear between "think I hear it" and "sounds like rap" (Vesco) | CONFIRMED |

Notes: White says parallel adds more in the gaps between hits. Senior warns about phase (use linear-phase EQ if in doubt) and that parallel is hard to bypass at matched level.

### Kick-to-bass ducking (role: sidechain ducking)

| Approach | Setting | Status |
|---|---|---|
| Natural | Compressor on bass keyed from kick, about 3 dB dip; more for pumping styles. White tip: set to maximum, tune release to groove, then back off | CONFIRMED, White (CONVENTION) |
| Band-only (preferred in source) | Duck only the 808's lows (band about 200 Hz) | CONFIRMED, Mixelite (OPINION, FL Studio-oriented) |
| Full duck | About 4:1, threshold for about 7-10 dB dip; warns full ducking makes the kick pump | CONFIRMED, Mixelite |
| Ableton device note | Sidechain EQ on the compressor restricts the trigger band; with only a mixed drum track, low-pass it to isolate the kick | FACT (manual); not re-opened |

Also: other bass layers low-cut at 100 Hz so one sound owns the sub; never cut the kick's sub; keep the 808 about 3 dB under the kick (all CONFIRMED, Mixelite, OPINION).

### Device facts (FACT, not re-opened, manual read only partially)

Ableton Drum Buss controls: Trim, Comp (fixed compressor before distortion), Drive types (Soft, Medium, Hard, Crunch), Damp (low-pass), Transients (above 100 Hz; negative shortens sustain), Boom/Freq/Decay, Dry/Wet. No recommended settings from the manual. Glue Compressor section was not read.

## 3. Electronic drums / 808 / trap (weak sourcing)

- No documented trap, 909 or 808 chain from a primary engineer source.
- Joshua's "Baby" (programmed drums) is the only documented programmed-drum chain: 808 got board EQ and light contouring only (FACT per collector, not re-opened for that line).
- The 808 owns the sub, the kick is a click, and duck only the 808 lows: Mixelite OPINION (confirmed above).
- LOW CONFIDENCE (search snippets, not opened): trap hi-hat rolls at 1/16-1/64 with velocity ramps and pitch down 1-2 semitones (veena.studio); Drum Buss starting points Crunch 5-30%, Damp 6-12 kHz, Transients +10 to +30 (onefootstep). Do not encode these as defaults.

## 4. Documented named-record chains

| Record / engineer | Documented (FACT) | Settings? |
|---|---|---|
| "In the Air Tonight", Padgham (Mix, 2005) | Two U87 room mics 12-15 ft from kit, each compressed with an 1176; very heavy compressor on the talkback mic (desk modified to record it); ambient mics noise-gated; close kick and snare added for snap. Quote "90 percent of the sound was the live room mics" | None. No gate thresholds |
| "Baby", Joshua (SOS 2010) | Kick: parallel dbx 160x into Pultec EQP1A. Snare: parallel dbx 160x into API 550A, "or you risk things sounding thin". Crash: mono, 21.19 ms delay hard-panned opposite the original, deliberately not tempo-synced. Drum submix: SSL G384 compressor and GML 8200 EQ (the latter two per collector, not re-confirmed) | None for any compressor or EQ |
| "This Ain't A Scene", Avron (SOS 2008) | Kick gated, then EQ'd with a small boost around 154 Hz and a cut around 400 Hz "for definition". Drums to 24-track tape at 30 ips. Mono far room about 4:1 (sometimes 2:1), overheads about 4:1, both hedged ("probably") | No gate or compressor settings |
| "Violet Hill", Brauer (SOS 2008) | Kick and snare EQ with samples layered behind; toms through stereo Pye, 1176 and EMI-type compressors; rooms through old Compex compressors; drums and bass bus through Distressors then an EQ; no drum reverb. Per collector, not re-opened | None; compressors used for tone |
| Scheps (Kim blog 2025, secondary) | Three parallel chains: KS Crush (kick+snare 0 dB send into dbx 160, 10-15 dB GR, return -10 to -15 dB), Drums Dirt (distortion, overheads at -6 dB, return very low), Drum Parallel (full kit, about 4:1, 3 ms attack, 10-15 dB, -12 to -18 dB) | Numbers are the blog author's, not attributed to Scheps. Gear named, settings not Scheps's |

## 5. Conflicts between sources

| Topic | Positions | Reading |
|---|---|---|
| Parallel ratio/attack | 4:1 with 3 ms (Kim) vs 8:1+ (White) vs 10:1 with 0.03 ms (Vesco) | Range, not a fact. Choose by taste |
| Return EQ | Vesco boosts lows and highs (+9 dB shelves); Born Creative cuts below 100-150 Hz | Opposed goals (phatness vs clean low end) |
| Parallel scope | Whole kit via group sends (Rogers, Vesco) vs kick/snare only (Joshua, Kim) | Decide by cymbal harshness. Brauer used no parallel on drums |
| Kick EQ | 70-90 Hz boost, 160-180 Hz cut (White) vs 154 Hz boost, 400 Hz cut (Avron) | Kick-dependent. Avron is one record |
| Ducking depth | About 3 dB (White) vs 7-10 dB full duck (Mixelite) | Genre: natural vs pumping or 808 |
| Gated reverb vs compressed rooms | Mix article cites gated ambient mics plus heavy compression; Gearspace (snippet only, UNVERIFIED) says compressed room sound, not true gated reverb | Both agree the room mics dominate. No gate numbers anywhere |
| Kim blog internal | Drum Parallel 10-20 dB in description, 10-15 dB in setup; blend 15-20% vs -12 to -18 dB | Treat its numbers as soft |

## 6. Uncertainty and gaps

- No gate settings beyond White's kick gate and Senior's Logic overhead gate. No tom gate settings.
- No snare reverb decay times, no transient shaper settings from any named record. Only the Ableton Drum Buss Transients control is described, with no values.
- Joshua, Avron and Brauer give no ratios, attack or release. Numeric defaults come only from teaching articles.
- Scheps primaries (Puremix, Audiofanzine) were not opened. No SSL/API/UAD/FabFilter/iZotope manufacturer material, no Tape Op or Mix With The Masters.
- Ableton Glue Compressor manual section not read.
- The collector's "return about -15 dB" for KS Crush is really a start point; the page gives -10 to -15 dB.

## 7. Sources and re-verification

| Source | URL | Status |
|---|---|---|
| White, Mix Tips For Kick & Bass (SOS 2011) | https://www.soundonsound.com/techniques/mix-tips-kick-bass | RE-VERIFIED |
| Senior, Compression: Fashion The Drum Sound (SOS 2017) | https://www.soundonsound.com/techniques/compression-fashion-drum-sound-you-want | RE-VERIFIED |
| Vesco, NY parallel part 2 (2007) | http://www.benvesco.com/blog/mixing/2007/phat-drums-new-york-style-parallel-compression-part-2/ | RE-VERIFIED |
| Mixelite, Kick and 808 | https://mixelite.com/blog/how-to-mix-kick-and-808/ | RE-VERIFIED |
| Born Creative, Ableton drum bus chain | https://borncreativeaudio.com/blog/ableton-drum-bus-chain | RE-VERIFIED |
| Kim, Scheps parallel drums | https://blog.imseankim.com/andrew-scheps-parallel-processing-drums-mixing-masterclass/ | RE-VERIFIED, CORRECTED (attribution) |
| Tingen, Avron (SOS 2008) | https://www.soundonsound.com/techniques/secrets-mix-engineers-neal-avron | RE-VERIFIED |
| Senior, Snazzier Snares In Logic (SOS 2003) | https://www.soundonsound.com/techniques/snazzier-snares-logic | RE-VERIFIED |
| Flans, In the Air Tonight (Mix 2005) | https://www.mixonline.com/recording/classic-tracks/classic-tracks-phil-collins-air-tonight-365521 | RE-VERIFIED, CORRECTED (gating attribution) |
| Tingen, Joshua (SOS 2010) | https://www.soundonsound.com/techniques/secrets-mix-engineers-jaycen-joshua | RE-VERIFIED (partial) |
| Rogers, Controlling Your Drum Mix (SOS 2023) | https://www.soundonsound.com/techniques/controlling-your-drum-mix | not re-opened (structure only) |
| Tingen, Brauer (SOS 2008) | https://www.soundonsound.com/techniques/secrets-mix-engineers-michael-brauer | not re-opened (no numbers) |
| Ableton manual, Audio Effect Reference | https://www.ableton.com/en/manual/live-audio-effect-reference/ | not re-opened |
| Snippet only, LOW CONFIDENCE | majormixing.com/parallel-drum-compression, tailout.de/2026/07/25/parallel-compression-on-drums-new-york-trick, unison.audio/drum-bus-compression, puremix.com/blog/kick-and-snare-parallel-compression-a-better-drum-bus-setup, ableton.onefootstep.us/processing/compression-glue.html, veena.studio/blog/drum-programming-trap, gearspace.com/threads/drums-in-phil-collins-in-the-air-tonight.1252452/ | not opened |
