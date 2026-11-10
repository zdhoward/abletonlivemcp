# Busses and general mixing

Role/routing knowledge for group/bus, send/return, parallel and sidechain structures. Source evidence: `research/raw/2026-11-10-busses-mixing.md`. Sibling pages: [vocals](vocals.md), [drums](drums.md), [mastering](mastering.md), [guitar-bass](guitar-bass.md), [keys-synths](keys-synths.md).

## 1. Scope and how to read this page

- Labels: FACT = documented for a named engineer/record. CONVENTION = repeated teaching or manufacturer guidance. OPINION = blog/forum view.
- Status: CONFIRMED = re-opened on 2026-11-10 and matched. UNCONFIRMED-NUMBER = not re-opened or page blocked.
- Most documented engineer examples are 2007-2010 analogue-hybrid mixes (SOS "Secrets of the Mix Engineers"). One 2024 metal piece. Treat numbers as examples, not defaults.
- No source gives send levels in dB for any named engineer.

## 2. Mix-bus and group-bus processing

| Setting | Value | Source | Label / status |
|---|---|---|---|
| Mix bus ratio | 1.5:1 to 2:1 | SOS Haas 2008; Waves 2025 (2:1) | CONVENTION, CONFIRMED |
| Mix bus attack | medium; 30 ms (Waves), about 50 ms (Peter Moore) | same | CONVENTION, CONFIRMED |
| Mix bus release | Auto (Waves table) or medium, about 250 ms (Moore); Waves text elsewhere says 0.1 | same | CONVENTION, CONFIRMED (Waves internally inconsistent) |
| Mix bus gain reduction | 1-3 dB (SOS) / 2-4 dB (Waves); over 4-5 dB "usually over-compressed" (Waves) | same | CONVENTION, CONFIRMED |
| Drum bus | 4:1, 10 ms, release listed "0.1-0.3", 4-6 dB GR | Waves | CONVENTION, CONFIRMED (release unit as printed; Waves lists "ms") |
| Vocal group | 2:1, 3 ms, Auto, 1-2 dB | Waves | CONVENTION, CONFIRMED |
| Make-up gain | match to bypass level | Waves, SOS | CONVENTION |
| Sidechain HPF on bus comp | filter lows so kick does not cause pumping (no Hz in SOS) | SOS | CONVENTION, CONFIRMED |
| Multiband on mix bus | not recommended (Moore) | SOS | CONVENTION, CONFIRMED |

- Timing: insert the bus compressor from the start, mix through it, leave settings static (SOS; Waves top-down). CONFIRMED.
- Drum bus note: Born Creative (Ableton chain, OPINION, snippet only) uses Glue ratio 4 for 2-4 dB GR, sidechain HPF 80-100 Hz. UNCONFIRMED-NUMBER.
- Group count: aim for eight main faders or fewer (Paul White 2006). CONFIRMED.

Who does / does not use bus compression:

| Engineer | Documented | Status |
|---|---|---|
| Spike Stent | SSL quad comp across stereo bus, 2:1, "pumping"; GML EQ lift above 10k | FACT, CONFIRMED |
| Alan Parsons | "never compress or limit a mix" | FACT, CONFIRMED |
| Scheps | no bus comp on master in "In Solitude" mix; rear bus instead (section 5) | FACT |
| Brauer | final stereo compressor "barely acts" | FACT |
| Blake | historically only 1-2 dB on master | FACT-ish (secondary) |
| Marroquin | Manley Passive on stereo bus (EQ cut 2-3 dB at 3k); not described as compressing the stereo mix | FACT |
| Joshua | no stereo bus compressor documented | FACT (absence) |
| Lord-Alge | not documented | gap |
| Pensado | "never liked compression"; mix-bus processing not documented | FACT, CONFIRMED |

## 3. Send/return structure

- Reverb/delay on sends at 100% wet so channels share a space (Houghton 2007: "send effects should be set to 100 percent wet"). CONFIRMED.
- Template of 3-6 FX channels (Houghton uses six: short ambience, mid, long reverb; three delays). CONFIRMED.
- Sends post-fader by default; pre-fader if the source is compressed but you want a livelier reverb. CONFIRMED.
- Return filtering: HPF about 200 Hz and LPF about 10 kHz, 12 or 18 dB/oct, before or after the reverb (Paul White 2020). CONFIRMED. Paul White 2006 also: low cut from about 200 Hz on returns. CONFIRMED.
- Delay feeding a reverb: cut lows about 300 Hz, highs above about 1.2 kHz (White 2020). CONFIRMED.
- Correction: Houghton does not describe return-EQ; he filters the reverb input (lows cut for clarity, highs cut to push back).
- Depth: cut highs to push back; start reverb near 20% wet equivalent and back off 3-4 dB (White 2006). CONFIRMED.
- Pan sends separately; avoid hard-panning reverb; harder panning suits delays (Houghton). Delays tempo-synced unless very short.
- Ducking: compressor (or gate with negative attenuation) after the reverb/delay, external sidechain from the dry source (lead vocal). Reverb swells in gaps. CONFIRMED (White 2020). Attack/release by ear, no numbers.
- Parallel compression: duplicate or aux-send the bus, compress heavily, blend under dry. Sweetwater pages returned 403 and Sage/Reverb pages were snippet-only: ratio 20:1 claim UNCONFIRMED-NUMBER.
- Sidechain routing in Live (Ableton manual, per search summary, not fetched): Glue meant for Main or Group tracks; sidechain can tap any routing point including returns. UNCONFIRMED.
- Sidechain examples: Odeholm kick sidechains most things via one multiband band below about 120 Hz; Bogren vocal ducks rhythm guitar bus and vocal delay return (2024 metal, FACT). Blake rarely uses sidechain.

## 4. Workflow and order conventions

- Gain staging: tracks average about -18 dBFS at unity (sometimes -20) (iZotope Messitte). CONFIRMED. Submix -14 dBFS is specific to the author's analogue summing, not universal. CONFIRMED. Master: only "do not hit 0 dBFS".
- Track peaks about -10 dB (Paul White 2006). CONFIRMED.
- Mix-bus peak about -6 dBFS: blog-level only (KAN Samples, Audiospectra), no manufacturer or engineer source. UNCONFIRMED-NUMBER.
- Order of work (White): rough balance, group buses, headroom, EQ/comp with purpose (cut rather than boost; wide gentle boosts, narrow deeper cuts), high-pass, pan, reverb, mono check.
- EQ vs compression order: no consensus. "Sandwich" (EQ, comp, EQ; subtractive first, additive after) is OPINION only (Boris FX 2025).
- High-pass: reverb returns about 200 Hz; bass below 50 Hz is rarely reproduced at home (White gives no exact cutoff). Senior (2012) endorses systematic HPF in small studios, prefers peaking/shelf cuts for masking.
- Panning: bass and lead vocal centre; kits and piano moderate; spread backings and doubles (White). Low content centred/mono: thresholds 100/120/200 Hz vary in blogs. OPINION, UNCONFIRMED-NUMBER.
- Masking: kick/bass 60-100 Hz, fix by carving and sidechain (blogs). OPINION, UNCONFIRMED.

## 5. Named-engineer routing (as documented)

| Engineer / record | Routing | Status |
|---|---|---|
| Jaycen Joshua, "Baby" (2010) | Three groups (rhythm, music, vocals) to SSL sub busses, each on two faders (six-channel submix). Drum submix SSL G384 + GML 8200 EQ; music untouched; vocal Avalon 2055 EQ. Parallel kick: dbx 160x into Pultec EQP1A blended with original (Bob Powers chain via Pensado). Parallel snare: 160x into API 550A. | FACT, CONFIRMED |
| Brauer, "Violet Hill" (2008) | Four compressed stereo buses A-D plus a clean bus; each compressor L/R unlinked, "no more than a couple of dB". Lead vocal off the multibus; six aux compressor sends returning on own channels. Reverb on vocals only. | FACT, CONFIRMED (per SOS multi-stage article) |
| Lord-Alge, "Black Parade" (2007) | No dedicated drum bus; per-channel compression (4:1 and 2:1, about 4-5 dB). Reverb returns on stereo channels, delays on channels 1-4; tempo-set delays; long hall switched off for rock sections. | FACT |
| Marroquin, "Stronger" (2007) | Stems printed with effects; Manley Passive on stereo bus; kick, keyboard, vocal buses with compressor chains (ratios 3:1-5:1). Sidechain de-esser with +12 dB narrow boost 6-7k on sidechain. | FACT |
| Pensado, "Beep/Buttons" (2007) | Effects on separate aux via send, not insert. Eventide 2016 return: pre-delay 16th/32nd note, top rolled off about 5k (sometimes 4k), bottom from 300 Hz. Mix-bus and parallel structure not documented. Forum claim of "three parallel compression submixes" is LOW CONFIDENCE (Gearspace thread returned 403). | FACT (SOS, CONFIRMED); forum claim LOW CONFIDENCE |
| Scheps rear bus | All tracks to stereo bus; parallel send from nearly everything except drums to a rear bus with multi-mono (unlinked) 1176-style comp, low ratio, slow attack, fast release, no numbers. Leads trigger compression instead of drums. | FACT, CONFIRMED; no settings |
| Scheps "In Solitude" (2024) | Aux buses for snare/tom/global reverbs; master bus no compression. | FACT |
| Tchad Blake | Master bus chain with ML4000 limiter on from start, removed for mastering; drum bus C4 + SSL comp; sends Echoboy/Altiverb. | secondary (Tuts+, not direct quotes), medium |

## 6. Conflicts between sources

| Topic | Positions |
|---|---|
| Bus compression at all | Stent 2:1 across stereo bus vs Parsons/Scheps/Pensado none or minimal |
| Bus-comp GR | SOS 1-3 dB vs Waves 2-4 dB (both CONFIRMED); Brauer/Blake 1-2 dB |
| Bus-comp release | Waves table "Auto" vs Waves text "0.1" vs Moore about 250 ms |
| EQ vs comp order | EQ first, comp first, or sandwich; no named engineer cited |
| High-pass policy | Senior: systematic in small studios; Exeter: none, shelves only; White: returns/bass specifically |
| Return HPF | 200 Hz (White, CONFIRMED) vs 300 Hz (Audeobox Ableton guide, snippet, UNCONFIRMED-NUMBER; Pensado uses 300 Hz on his own Eventide reverb, CONFIRMED) vs 100-200 Hz (Vector DSP, UNCONFIRMED-NUMBER) |
| Return LPF | 10 kHz (White) vs 8 kHz (Audeobox) vs 6-10 kHz (Vector DSP); Pensado 4-5k |
| Master headroom | -6 dBFS peak (blogs) vs master only below 0 dBFS (iZotope) |

## 7. Uncertainty and gaps

- Scheps rear-bus settings, Joshua/Marroquin send levels, Lord-Alge stereo bus: not documented.
- No SOS article for Ghenea or Blake. Ghenea claims are secondary and not used.
- Waves release unit ("0.1-0.3 ms") is as printed; SSL release is normally in seconds, so do not implement as ms without checking.
- Sweetwater pages (403); Ableton manual not fetched. Gearspace threads blocked.
- iZotope page date (9 Oct 2026) may be a refresh date.

## 8. Sources and re-verification

Re-verified 2026-11-10 (9 pages): all numbers above marked CONFIRMED.

| Source | URL | Status |
|---|---|---|
| Waves SSL bus comp guide (2025) | https://www.waves.com/how-to-use-ssl-bus-compressor-classic-mix-glue | re-verified |
| SOS Guide To Mix Compression (2008) | https://www.soundonsound.com/techniques/sos-guide-mix-compression | re-verified |
| SOS Optimise Reverb (2020) | https://www.soundonsound.com/techniques/how-optimise-your-reverb-treatments | re-verified |
| SOS Mixing Essentials (2006) | https://www.soundonsound.com/techniques/mixing-essentials | re-verified |
| SOS Using Reverb & Delay (2007) | https://www.soundonsound.com/techniques/using-reverb-delay | re-verified |
| iZotope gain staging | https://www.izotope.com/en/learn/gain-staging-what-it-is-and-how-to-do-it.html | re-verified |
| SOS Multi-stage Compression | https://www.soundonsound.com/techniques/multi-stage-compression | re-verified |
| SOS Pensado | https://www.soundonsound.com/techniques/secrets-mix-engineers-david-pensado | re-verified |
| SOS Joshua | https://www.soundonsound.com/techniques/secrets-mix-engineers-jaycen-joshua | re-verified |
| Gearspace Pensado thread | https://gearspace.com/board/so-much-gear-so-little-time/21633-dave-pensado-i-think-i-figured-out-how-you-get-away-without-mixbus-compression.html | 403, not verified |
| SOS Brauer | https://www.soundonsound.com/techniques/secrets-mix-engineers-michael-brauer | collector-fetched only |
| SOS Lord-Alge | https://www.soundonsound.com/techniques/secrets-mix-engineers-chris-lord-alge | collector-fetched only |
| SOS Marroquin | https://www.soundonsound.com/techniques/secrets-mix-engineers-manny-marroquin | collector-fetched only |
| SOS Masters of Mixing (Mynett 2024) | https://www.soundonsound.com/techniques/masters-art-mixing | collector-fetched only |
| SOS Senior HPF Q&A (2012) | https://www.soundonsound.com/sound-advice/q-do-mixes-benefit-low-pass-filtering-mixdown | collector-fetched only |
| Tuts+ Blake | https://music.tutsplus.com/i-turn-knobs-until-it-sounds-good-mixing-with-tchad-blake--cms-28866a | collector-fetched only |
| Boris FX EQ vs comp | https://borisfx.com/blog/eq-before-or-after-compression-best-for-mix/ | collector-fetched only |
| Sweetwater parallel comp | https://www.sweetwater.com/insync/parallel-compression-explained/ | 403, snippet only |
| KAN Samples / Audiospectra (-6 dBFS) | https://kansamples.com/blogs/learn/gain-staging-routing-mix ; https://audiospectra.net/gain-staging/ | snippet only |
| Audeobox / Vector DSP / Born Creative (Ableton) | https://www.audeobox.com/learn/ableton/return-tracks-guide/ ; https://vector-dsp.com/blog/eq-on-return-track/ ; https://borncreativeaudio.com/blog/ableton-drum-bus-chain | snippet only |
| Ableton Live 12 manual | https://www.ableton.com/en/manual/live-audio-effect-reference/ | not fetched |
