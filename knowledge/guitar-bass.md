# Guitar and Bass FX chains (knowledge page)

Synthesized from `research/raw/2026-11-10-guitar-bass.md`, then spot-checked against the original pages on 2026-11-10. Chains are organized by ROLE and stage order. Brand names appear only as "used in source X".

Related pages: [vocals](vocals.md), [drums](drums.md), [busses-mixing](busses-mixing.md), [mastering](mastering.md), [keys-synths](keys-synths.md).

## 1. Scope and how to read this page

- Covers electric guitar (pedal and amp-sim), bass (DI plus amp, parallel distortion, compression), acoustic guitar (weak sourcing), and a few named records.
- Evidence labels: **FACT** = documented for a named recording or workflow. **CONVENTION** = widely repeated technique. **OPINION** = blog, forum or fan analysis.
- Confirmation status: **CONFIRMED** = I re-opened the URL and the number matches. **UNCONFIRMED-NUMBER** = could not re-open or the page did not state it. **LOW-CONFIDENCE** = secondhand or search-snippet only.
- Fetching used a summarizing tool, so exact quotes are not guaranteed. Treat numbers as presets to audition, not law.

## 2. Consensus patterns

### 2a. Guitar pedal order (CONVENTION)

| Stage | Role | Note |
|---|---|---|
| 1 | tuner | utility |
| 2 | wah / filter | swaps with drive are common |
| 3 | compressor | see conflict 5c |
| 4 | drive (OD / distortion / fuzz) | |
| 5 | modulation | often moved to the amp FX loop with high-gain amps |
| 6 | delay | after drive; delay before reverb |
| 7 | reverb | usually FX loop unless amp is very clean |
| 8 | amp / cab | |

- Sources: BOSS bass-order page (CONFIRMED for the bass order only); Premier Guitar, Guitar World and BOSS guitar pages were search-only (LOW-CONFIDENCE). PG says order is taste, not law.
- Thorn (Premier Guitar, CONFIRMED): put delay after gain devices, use the FX loop; echo ahead of a dirty amp is messy but gives dynamic, classic results. Start delay mix "just above minimum", feedback low; repeats should lose treble. Readjust delay mix if gain changes.

### 2b. Guitar in the box, by voicing

| Voicing | Chain (stage order) | Ranges and status |
|---|---|---|
| Clean | (comp) > amp/cab > EQ > spring or plate reverb, top rolled off | Reverb 2-3 s (country) and slapback 80-100 ms single repeat CONFIRMED (White 1996). Jazz/pop clean: comp after EQ, slow attack, no numbers. |
| Crunch | drive pedal > amp > cab > EQ; delay/reverb after | No documented numeric settings beyond order. |
| High-gain (amp sim) | DI at moderate level > edit/gate > boost-style pedal sim (Drive 0, Tone ~6, Level 10) > amp, gain ~5-6 > cab/IR > HPF 80-100 Hz, LPF 10-12 kHz, narrow cuts of a few dB in 2-5 kHz > gate > bus light saturation/comp | All numbers CONFIRMED in Nail The Mix amp-sim FAQ. Order is assembled from separate tips, not stated by the article. Boost is to tighten, not add gain. Cab/IR is the main source of fizz or thinness. |
| Ambient | reverse reverb (short decay) > fuzz > clean amp; or time-based loops via a send | See section 4. Only manufacturer starting points and one fan/press account exist. |

- Guitar EQ start points (CONFIRMED, SOS "Using EQ"): HPF about 80 Hz; warmth 125-250 Hz; attack 3-5 kHz; cabs roll off above ~4 kHz so boosting beyond mostly adds noise.
- Acoustic-style from electric (CONFIRMED, White 1996): boost ~150 Hz, cut 500 Hz-1 kHz hard, peak 4-6 kHz. Funk: boost 3-6 kHz, release about 0.5 s or less (CONFIRMED).
- DI tracking level: see conflict 5a. DI edit step (CONFIRMED, Nail The Mix DI): HPF 80-100 Hz, optionally "a tiny bit" of fast-attack compression for inconsistent players.
- Buffer 64 or 128 samples while tracking (CONFIRMED).

### 2c. Bass

Chain order across sources (BOSS bass order CONFIRMED: tuner, compression, wah/filter, octaves, drive, noise suppressor, EQ, modulation, volume, delay, reverb, amp; EQ after drive restores low end).

| Block | Role | Settings (source) |
|---|---|---|
| Cleanup | gate/edit | fix uneven notes with region gain, not compression (Lockwood). |
| HPF | eq | 30 Hz at 12-18 dB/oct (Lockwood, CONFIRMED); 20-30 Hz safety (Senior, CONFIRMED); secondary bass parts ~100 Hz; acoustic bass ~35 Hz. |
| Tone EQ | eq | Lockwood: -8 dB at 500 Hz Q 0.2; high shelf -3 dB from ~3 kHz; +4 dB Q ~0.3 at 100-120 Hz (sweep 90-150); optional -4 dB at 1 kHz; optional +3 dB at 4-5 kHz Q 0.7. All CONFIRMED. Senior: boost ~1 kHz for cut-through, LPF 2-3 kHz if heavy, avoid 3-6 kHz. |
| Main compressor | compressor | Lockwood: 2:1, max about 4-5 dB GR, attack 10-20 ms, release auto or ~100 ms, RMS. Senior: 4:1 or higher, hard knee, attack 1-30 ms. See conflict 5b. |
| Low-band salvage | compressor (multiband) | Senior: lowest band ~8:1, ~5 ms attack, ~80 ms release, 8-12 dB GR, before main comp (CONFIRMED). |
| Parallel compression | compressor (aux) | Lockwood: 6:1 or 8:1, ~10 dB GR, fast attack/release (CONFIRMED). |
| Parallel distortion | drive/saturation | HPF below ~100 Hz before, LPF above 2 kHz after (Lockwood, CONFIRMED). Optional pre-distortion comp 4:1, 6-10 dB GR. Senior: distortion only in parallel, heavily EQ'd (no frequencies). |
| Two-band split | filters | Lows: HPF 30 Hz + 24 dB/oct LPF 300 Hz; Highs: 24 dB/oct HPF 400 Hz; drive and modulation fed from Highs only (Lockwood, CONFIRMED). |
| DI + amp/cab blend | amp/cab | Lockwood: DI -6 dB at ~1 kHz Q 0.3, 18 dB/oct roll-off at 30 Hz, DI blended at lowest audible level (CONFIRMED). Align polarity/timing first and re-check after EQ (Senior). One layer owns sub-100 Hz. |
| Modulation | modulation | parallel, lows removed from return; main bass stays mono (Lockwood; no rates). |
| Ducking | compressor | 2-3 dB per kick hit via sidechain or group (Senior, CONFIRMED). |
| Returns | reverb/delay | high-pass returns; short stereo reverb or chorus (Senior). |

- Bass EQ points (CONFIRMED, SOS "Using EQ"): weight 80-100 Hz, warmth 100-300 Hz, attack/boxy 500-1500 Hz, string noise 2-5 kHz.
- Sub synth bass (Senior): single sine or triangle oscillator, no detune. See also [keys-synths](keys-synths.md).

## 3. Acoustic guitar (weak sourcing)

- SOS "Using EQ" (CONFIRMED, CONVENTION): weight 80-120 Hz, boom 200-300 Hz, nasal 1-1.5 kHz, clarity 2-5 kHz, sparkle 5-10 kHz.
- Blogs (OPINION, search-snippet only, UNCONFIRMED-NUMBER): HPF 70-150 Hz depending on role, cut ~250 Hz (-2 to -3 dB), boost ~3 kHz, 10 kHz shelf, compression 4-8 dB GR, attack 15-30 ms, release 60-100 ms. Used in sources musicguymixing, danmurtagh, tonyosomusic, Lewitt, Johnny Copland. No engineer attribution; no recording documented.

## 4. Documented named-player and record chains

| Subject | What is documented | Label / status |
|---|---|---|
| Eddie Van Halen, "Ain't Talkin' 'Bout Love" | Late-60s Marshall Super Lead with all knobs on 10; Echoplex EP-3 into the front of the amp; 300 ms, one repeat (Thorn, PG) | FACT as stated by author; CONFIRMED |
| Joe Walsh "The Bomber" | Echoplex into front of amp; regeneration no number | FACT per author; UNCONFIRMED-NUMBER (none given) |
| The Edge (U2) | Dotted eighth 3/16 = 45,000 / BPM ms (450 ms at 100 BPM). Estimates: With or Without You 410 ms; Still Haven't Found 450 L + 150 R; Bad 467 + 221; Streets 350 R + 525 L. Two delays, mostly 1-2 repeats | Tim Darling's FAN ANALYSIS of recordings, not Edge's statement. Numbers CONFIRMED against the page (first ~100k of ~225k chars read); commenters dispute some songs. Gear list (Memory Man, SDD-3000, TC 2290, AC30) not re-verified. |
| My Bloody Valentine, Loveless | Guitars through Yamaha SPX90 reverse reverb; Roger Meyers Active Fuzz plus Octave Fuzz (gating effect when Octave Fuzz is driven); raised-and-locked tremolo arm glide; one song with two amps facing each other with different tremolos, mics between; mostly mono | FACT per Happy Mag attributing to Moulder; CONFIRMED. No pedal order or settings given. |
| Shoegaze starting point (Red Panda) | Guitar > reverse reverb > fuzz > amp. Reverse: blend 2:00, predelay 11:15, decay 10:30 (short), high 3:00, low ~1:30, mod 3:00-5:00; delay time ~11:15, feedback ~11:00. Clock positions, not units | Manufacturer starting point, NOT a recording chain. CONFIRMED. Page does not name Shields. |
| Alan Moulder, Nine Inch Nails / Smashing Pumpkins (The Fragile) | Guitar to amp, DI, or both; send to Eventide DSP4000 sample-card loops, built up, captured to DAT, chopped; compressor pedal; DI | FACT, low detail; not re-verified |
| Hugh Padgham (Andy Summers, Police) | Roland JC120, MD421 on each of two 12-in speakers, panned L/R; one speaker straight, one chorused | FACT via reprint; CONFIRMED |
| Mike Hedges | Three guitar tracks (clean, half-driven, fully driven) faded through the song | FACT via reprint; CONFIRMED |
| John Leckie | SM58 plus U67, U67 usually 10-15 dB down (also "20-30 dB down" at times) | FACT via reprint; CONFIRMED |
| Jack Douglas | "Phase EQ": SM57, MD421, condenser in a triangle, flip polarity on one mic | FACT via reprint; CONFIRMED (the "10 dB pad ~1 ft" detail was not seen in the fetch: UNCONFIRMED-NUMBER) |
| Joe Barresi | SM57 + MD421 close to speaker; splitter to several amps | FACT via reprint; CONFIRMED |
| Mic distances | Albini starts 10-12 in; Parsons ~1 ft up to 4 ft | CONFIRMED. Al Schmitt 15-20 ft: UNCONFIRMED-NUMBER |

Reprint caveat: the amp-recording article is read via solodallas.com, a reprint of the SOS 2007 piece; cite SOS only after confirming there.

LOW-CONFIDENCE bass-player claims (TalkBass paraphrases of Bass Player; Guitar World Wolstenholme page body never loaded): Wolstenholme keeps one amp clean with distortion on a split path; Commerford blends clean, overdrive and in-between amps; Chancellor keeps a clean path via a splitter. No settings. Not used for presets.

## 5. Conflicts between sources

| Topic | Position A | Position B | Resolution |
|---|---|---|---|
| a. DI record level | -12 to -10 dBFS peaks (Nail The Mix DI article; CONFIRMED) | -18 to -12 dBFS peaks (Nail The Mix amp-sim FAQ; CONFIRMED) | Both same publisher; unresolved. Use -18 to -10 dBFS as a safe window; peaks are the target, not average. |
| b. Bass compression | 2:1 main, ~4-5 dB GR, plus 6:1-8:1 parallel (Lockwood) | 4:1 or higher hard knee, attack 1-30 ms (Senior, chart styles) | Different intent: gentle main plus parallel vs. firm control. Offer both as styles. |
| c. Comp before or after drive | Before drive (BOSS/PG order) | Not after drive, it amplifies noise (Guitar World, search-only, LOW-CONFIDENCE) | Default compressor before drive; both are common. Debated per aggregator results. |
| d. Comp before or after EQ | Before EQ = bright, wiry, snappy (White 1996, CONFIRMED) | After EQ = smooth, sustained (White 1996) | Not a conflict: a tone choice. |
| e. DI vs amp blend | 60-70% DI / 30-40% amp (Hollyland, search-only) | DI at lowest audible level (Lockwood, CONFIRMED) | Opinion vs workflow; prefer Lockwood, start low. |

## 6. Uncertainty and gaps

- No manufacturer or modeler article (Neural DSP, Kemper, Line 6, Fractal, UA) was read.
- No Mix with the Masters, Tape Op or Bass Player primary text.
- High-gain metal: no named-engineer chain with numbers; amp-sim numbers come from one publisher.
- Clean/crunch with named recordings: only White's 1996 style guide (dated gear, many "no setting given").
- Ambient: no engineer interview with reverb decay or pedal order; delay times for ambient guitar rarely stated.
- Cockos forum DI HPF ~60-70 Hz, amp track HPF ~300 Hz, LPF ~5k: OPINION, UNCONFIRMED-NUMBER.
- Funk "condenser" mic detail and several 1996 per-style comments not re-verified.

## 7. Sources

| Source | URL | Re-verified |
|---|---|---|
| Lockwood, Mixing DI Bass Guitar, SOS 2022 | https://www.soundonsound.com/techniques/mixing-di-bass-guitar | Yes |
| Senior, Mixing Bass, SOS 2012 | https://www.soundonsound.com/techniques/mixing-bass | Yes |
| Senior/White, Using EQ, SOS 2001 | https://www.soundonsound.com/techniques/using-eq | Yes |
| White, Electric Guitar Styles, SOS 1996 | https://www.soundonsound.com/techniques/producing-recording-electric-guitar-styles | Yes |
| Senior, Guitar Amp Recording (reprint) | https://solodallas.com/blogs/blog/guitar-amp-recording-from-sound-on-sound | Yes (partial) |
| Nail The Mix, Guitar DI for Metal | https://www.nailthemix.com/how-to-record-a-guitar-di | Yes |
| Nail The Mix, Amp Sim FAQs | https://www.nailthemix.com/amp-sim-faqs | Yes |
| Thorn, PG, Echo and the Dirty Amp | https://www.premierguitar.com/tone-tips-echo-and-the-dirty-amp | Yes |
| BOSS, Bass effects order | https://articles.boss.info/order-of-operation-a-guide-to-bass-effects-signal-chain/ | Yes |
| Red Panda shoegaze reverse reverb | https://support.redpandalab.com/support/solutions/articles/43000644553-shoegaze-reverse-reverb | Yes |
| Happy Mag, Loveless | https://happymag.tv/engineering-the-sound-my-bloody-valentines-loveless/ | Yes |
| Darling, Edge delay study | https://www.amnesta.net/edge_delay/ | Yes (first 100k chars) |
| Buskin, Alan Moulder, SOS 2000 | https://www.soundonsound.com/people/alan-moulder-recording-nine-inch-nails-smashing-pumpkins | No |
| PG Recording Dojo, pedals for recordings | https://www.premierguitar.com/diy/recording-dojo/using-pedals-to-enhance-tracks | No |
| PG, Guitar World, BOSS guitar order, PG State of the Stomp | premierguitar.com/explains/pedals-effects; guitarworld.com/gear/where-to-place-your-effect-pedals-in-your-signal-chain; articles.boss.info/the-ultimate-guide-to-guitar-effects-pedal-order-and-signal-chain/; premierguitar.com/articles/21915-state-of-the-stomp-a-solid-case-for-doing-it-wrong | No (search-only) |
| TalkBass / Guitar World Wolstenholme | talkbass.com threads 265221, 347041; guitarworld.com Wolstenholme feature | No (LOW-CONFIDENCE) |
| Bass blend and acoustic blogs | forum.cockos.com/showthread.php?t=240483; theproaudiofiles.com/mixing-bass-guitar/; hollyland.com/blog/topics/record-bass-guitar; musicguymixing.com/eqing-acoustic-guitar/; danmurtagh.com/acoustic-guitar-eq; tonyosomusic.com (acoustic EQ cheat sheet); lewitt-audio.com/blog/how-to-mix-acoustic-guitar; johnnycopland.com | No (search-only, OPINION) |
