# Vocals: FX chains by role

Synthesized from `research/raw/2026-11-10-vocals.md` (2026-11-10). Sibling pages: [drums](drums.md), [busses-mixing](busses-mixing.md), [mastering](mastering.md), [guitar-bass](guitar-bass.md), [keys-synths](keys-synths.md).

## 1. Scope and how to read this page

- Organized by ROLE and stage order. Brand names appear only as "used in source X"; any plugin of the same role can substitute.
- Evidence labels: **FACT** = documented by the engineer/manufacturer for a named recording or workflow; **CONVENTION** = widely repeated technique; **OPINION** = blog/forum view.
- Confirmation: **VERIFIED** = number re-opened on the original page in this pass (10 pages, 2026-11-10). **UNCONFIRMED-NUMBER** = not re-opened. **UNVERIFIED** = only a search snippet or second-hand relay.
- Most named-record sources give plugin lists with few numbers. Treat ranges as starting points, not presets.

## 2. Consensus patterns (role order, typical ranges)

Typical lead-vocal stage order (the order of EQ / comp / de-ess is disputed, see section 5):

| # | Role | Typical setting / range | Source (label, status) |
|---|------|------------------------|------------------------|
| 1 | Pitch correction / cleanup (before dynamics, on dry signal) | Subtle; Auto-Tune lightly on 9 of 12 tracks incl. rap | [iZotope basic chain](https://www.izotope.com/en/learn/crafting-a-basic-vocal-chain) CONVENTION; [Shebib/Drake](https://www.soundonsound.com/techniques/noah-40-shebib-recording-drakes-headlines) FACT, UNCONFIRMED-NUMBER |
| 2 | High-pass / low cut | ~100 Hz cut when tracking; ~30 Hz sub removal before compressor (Dua Lipa) | [Ogan](https://www.recordingmag.com/resources/recording-info/mics-miking/vocal-sessions-la-style/) FACT, VERIFIED ("around 100 Hz"); [Gudwin](https://www.soundonsound.com/techniques/inside-track-dua-lipa-dont-start-now) FACT, VERIFIED (~30 Hz) |
| 3 | Compressor, FET-style (most-named) | 3-7 dB GR (iZotope); 3-6 dB (Ogan); ~3 dB mild to ~10 dB aggressive at 4:1 (Hanes); 4:1 quick release (CLA) | [iZotope](https://www.izotope.com/en/learn/crafting-a-basic-vocal-chain) VERIFIED; [Ogan](https://www.recordingmag.com/resources/recording-info/mics-miking/vocal-sessions-la-style/) VERIFIED; [Ghenea/Hanes](https://mixandmastermysong.com/serban-ghenea-vocal-chain-revealed/) VERIFIED (relay); [CLA](https://www.soundonsound.com/techniques/secrets-mix-engineers-chris-lord-alge) UNCONFIRMED-NUMBER |
| 3b | Second compressor: optical/leveler, slow attack/release, evens level; or parallel squashed FET | Slow/slow for the leveler after a fast/fast FET | [Elmhirst/Adele](https://www.soundonsound.com/techniques/tom-elmhirst-recording-adele-rolling-deep) FACT, VERIFIED (qualitative); parallel: Weeknd, Lee, Kendrick guests FACT |
| 4 | EQ (subtractive + colour/air) | Air boost ~12 kHz; low boost ~100 Hz small gain; mids cut 200 Hz-2 kHz | [Gudwin](https://www.soundonsound.com/techniques/inside-track-dua-lipa-dont-start-now) VERIFIED; [Elmhirst](https://www.soundonsound.com/techniques/tom-elmhirst-recording-adele-rolling-deep) VERIFIED; [Eilish](https://www.soundonsound.com/techniques/inside-track-billie-eilish-bad-guy) VERIFIED |
| 5 | De-esser | Singer-dependent: >3 kHz (iZotope); 4-10 kHz, down to 1.5 kHz (iZotope 2025); ~5500 Hz / ~6 dB GR (Hanes); 6557 Hz (Eilish); two at 5449 and 11004 Hz (Adele chorus) | [iZotope](https://www.izotope.com/en/learn/crafting-a-basic-vocal-chain) VERIFIED (>3 kHz); [de-ess dos/don'ts](https://www.izotope.com/community/blog/the-dos-and-donts-of-de-essing) UNCONFIRMED-NUMBER (4-10 kHz, 1.5 kHz); Hanes, Eilish, Adele VERIFIED |
| 6 | Level rider / automation | ~1.5 dB of riding at end of chain (Eilish) | [Eilish](https://www.soundonsound.com/techniques/inside-track-billie-eilish-bad-guy) FACT, VERIFIED |
| 7 | Reverb on aux send, return filtered | Pre-delay 16th or 32nd note; roll off top ~5 kHz (sometimes 4k), bottom from 300 Hz | [Pensado](https://www.soundonsound.com/techniques/secrets-mix-engineers-david-pensado) FACT (stated preference), VERIFIED |
| 8 | Tempo-synced delay on aux send | 1/8, dotted 1/8, 1/4 (many sources); L/R offset 1/64, feedback 0 for widening | [iZotope](https://www.izotope.com/en/learn/crafting-a-basic-vocal-chain) VERIFIED (1/64); [Lee](https://www.soundonsound.com/techniques/inside-track-twice-scientist?page=2) VERIFIED (eighth) |
| 9 | Pitch-shift doubler / micro-shift width send | Short detune pair; high end reduced after the doubler so doubled sibilance does not distract | [Weeknd](https://www.soundonsound.com/techniques/inside-track-weeknd) FACT, UNCONFIRMED-NUMBER; [Lee](https://www.soundonsound.com/techniques/inside-track-twice-scientist?page=2) FACT VERIFIED (doubler aux exists) |
| 10 | Vocal bus glue (compressor, saturation/inflator) | Bus comp 4:1 stereo-linked (Eilish); inflator on lead folder (Lee) | [Eilish](https://www.soundonsound.com/techniques/inside-track-billie-eilish-bad-guy) VERIFIED; [Lee](https://www.soundonsound.com/techniques/inside-track-twice-scientist?page=2) VERIFIED |

Other consensus points (FACT unless noted):
- Time effects live on aux sends, not inserts ([Pensado](https://www.soundonsound.com/techniques/secrets-mix-engineers-david-pensado), [Gudwin](https://www.soundonsound.com/techniques/inside-track-dua-lipa-dont-start-now), [Weeknd](https://www.soundonsound.com/techniques/inside-track-weeknd), [Lee](https://www.soundonsound.com/techniques/inside-track-twice-scientist?page=2)). Pensado also puts a delay as an insert on one track; sends are the norm, not a rule.
- Compressor attack: slow for staccato, fast for legato; release set so it recovers before the syllable ends ([Hanes relay](https://mixandmastermysong.com/serban-ghenea-vocal-chain-revealed/), VERIFIED only as descriptive guidance, no numbers).
- Backing vocals get their own bus/space and fewer sends than lead ([Lee](https://www.soundonsound.com/techniques/inside-track-twice-scientist?page=2), [Weeknd](https://www.soundonsound.com/techniques/inside-track-weeknd), [Eilish](https://www.soundonsound.com/techniques/inside-track-billie-eilish-bad-guy)).
- Sibilance often rises after a high-end EQ boost; clip gain/automation before de-essing; consider de-essing sends before reverb/distortion ([iZotope](https://www.izotope.com/community/blog/the-dos-and-donts-of-de-essing), CONVENTION, UNCONFIRMED-NUMBER).
- Vocal throw (CONVENTION, vendor blog, VERIFIED): [Meshplugins](https://shop.meshplugins.com/blogs/the-hidden-sauce/vocal-throw-delay) delay 1/4 (500 ms at 120 BPM) or dotted 1/8 (375 ms); feedback 30-45% (~35% = 4-5 repeats, >60% runs into next section); return 100% wet, HP 400 Hz, LP 4-5 kHz; automate the send from -inf to 0 dB across the word, not the mix knob; instrumental bus -1 dB for 1/2 bar; 2-3 throws per song.
- Stacking (FACT, [Ogan](https://www.recordingmag.com/resources/recording-info/mics-miking/vocal-sessions-la-style/)): doubles panned ~50% L/R (VERIFIED); pop 5-part lead pans centre, 100%, 50% (UNCONFIRMED-NUMBER).

## 3. Genre/role variants (ordered, role terms)

| Variant | Chain | Source |
|---------|-------|--------|
| Pop lead (modern) | HP/sub cleaner, FET or light comp, optical leveler, resonance suppressor, EQ (air), de-esser, EQ (restore top), optional ducker; sends: filtered reverb, 1/8 delay, micro-shift doubler | [Gudwin](https://www.soundonsound.com/techniques/inside-track-dua-lipa-dont-start-now), [Lee](https://www.soundonsound.com/techniques/inside-track-twice-scientist?page=2) |
| Intimate / dry pop | Low cut EQ, light opto comp, de-esser, mid-cut EQ, console-style colour EQ, rider; no reverb; width via micro-shift only | [Eilish](https://www.soundonsound.com/techniques/inside-track-billie-eilish-bad-guy) |
| Soul / powerhouse | Colour EQ (small 100 Hz and 12 kHz lifts), fast FET, slow opto; narrow notches for chorus; two de-essers at different bands; fader rides | [Elmhirst](https://www.soundonsound.com/techniques/tom-elmhirst-recording-adele-rolling-deep) |
| Rock lead | Limiter/clipper in transfer for attitude, 1176-style 4:1 quick release, heavy fader riding; long hall on intro, room ~1 s after; 1/4 and 1/8 delays automated | [CLA](https://www.soundonsound.com/techniques/secrets-mix-engineers-chris-lord-alge) |
| Backing vocals | HP, FET comp, EQ, de-esser, group bus: cut lows, leveling opto, boost highs; one reverb send only; stereo-width tool on group | [Lee](https://www.soundonsound.com/techniques/inside-track-twice-scientist?page=2), [Weeknd](https://www.soundonsound.com/techniques/inside-track-weeknd) |
| Rap | Small EQ, comp; delay (ping-pong, filtered) preferred over reverb; one chain for verse and chorus so it reads as one performer | [Joshua](https://www.soundonsound.com/techniques/secrets-mix-engineers-jaycen-joshua) FACT, [Shebib](https://www.soundonsound.com/techniques/noah-40-shebib-recording-drakes-headlines) FACT |
| R&B / hip-hop ad-libs | Pitch correct, EQ, rider, de-esser, gate; parallel effect track feeding slap, long delay, delay+reverb | [Weeknd](https://www.soundonsound.com/techniques/inside-track-weeknd) FACT |
| EDM vocal chop (stock Ableton) | Sampler in slice mode, Complex Pro warp, formant 100%, up an octave; delay 1/8; reverb decay 2.89 s, dry/wet 67% (later >7 s); low-pass 1.35 kHz then 1.04 kHz | [Puremix](https://www.puremix.com/blog/creating-vocal-chops) FACT (one producer demo), VERIFIED |
| Pop chop (bridge) | Formant-down pitch tool, micro-shift width, light dotted-1/8 delay before saturator-as-compressor (delay swells when vocal stops), fast comp, de-esser, LFO-style transient soften | [Gudwin](https://www.soundonsound.com/techniques/inside-track-dua-lipa-dont-start-now) FACT, VERIFIED (order inferred by article) |

## 4. Documented named-record chains

| Record | Chain (as documented) | Source / status |
|--------|----------------------|-----------------|
| Dua Lipa "Don't Start Now" (Gudwin) | Sub cleaner (~30 Hz) -> light grit comp -> LA-3A-style opto -> resonance suppressor -> Pultec-style EQ (low cut a bit, +12 kHz air) -> de-esser -> EQ (restore top) -> LFO ducker (10% per kick, 40% in verses). Reverb: plate/hall -> OTT -> 1176 on reverb. Producer preferred ducker over sidechain. | [SOS](https://www.soundonsound.com/techniques/inside-track-dua-lipa-dont-start-now) FACT, VERIFIED |
| Adele "Rolling In The Deep" (Elmhirst) | Console insert: Pultec-style (boost ~100 Hz, 12k, little gain) -> blackface 1176 (fast/fast) -> CL1B (slow/slow). Plugins on chorus: notches 930 Hz (-18 dB), 1634 Hz (-18 dB), 3175 Hz (-12.1 dB), narrow Q; de-essers 5449 Hz and 11004 Hz. Space Echo track only lead effect in first chorus; spring reverbs on BVs. | [SOS](https://www.soundonsound.com/techniques/tom-elmhirst-recording-adele-rolling-deep) FACT, VERIFIED (all numbers match; the page notes other songs use different de-esser/notch freqs) |
| Billie Eilish "Bad Guy" (Kinelski) | Low-cut EQ -> 670-style comp -> de-esser 6557 Hz -> mid-cut EQ (200 Hz-2 kHz) -> console 1073-style EQ (engaged, colour) -> rider (1.5 dB). Group bus comp 4:1 stereo-linked. Width aux with micro-shift; no reverb. | [SOS](https://www.soundonsound.com/techniques/inside-track-billie-eilish-bad-guy) FACT, VERIFIED |
| TWICE "Scientist" (Lee) | Insert: CLA-76 (attack 3, release 5; usual 4 and 6) -> EQ with high shelf. Four sends: doubler (micro-shift), 480-style reverb, 2290-style delay, 1/8 delay. BVs one send only (to the reverb). Lead folder: inflator. | [SOS](https://www.soundonsound.com/techniques/inside-track-twice-scientist?page=2) FACT, VERIFIED |
| Pussycat Dolls "Beep" (Pensado) | Linear-phase EQ -> colour EQ -> multitap delay 149/298/587 ms (16th/8th/half) spread L to R, rising in level -> Doubler -> pitch-blender (cents) -> plate reverb with dip at 8k. "Buttons": 11.5 s reverb with low end rolled off from an aux; Metaflanger mix 21. Pensado: "I never liked compression." | [SOS](https://www.soundonsound.com/techniques/secrets-mix-engineers-david-pensado) FACT, VERIFIED |
| The Weeknd "The Hills" (Illangelo) | Verse inserts: Auto-Tune (subtle) -> de-esser -> EQ (lo-fi rolloff) -> rider -> API 560-style EQ -> multiband. Parallel: radiator + squashed 1176. Five sends (convolution reverb with pre-delay, slap, doubler -> micro-shift -> EQ, long filtered delay, second reverb). | [SOS](https://www.soundonsound.com/techniques/inside-track-weeknd) FACT, UNCONFIRMED-NUMBER (no numbers; order as listed) |
| St Vincent "Pay Your Way In Pain" (Riordan) | Multiband (midrange), CLA-76, API 550A, resonance suppressor, EQ; parallel distortion sends (amp sim, saturator) exposed harshness at 3.5 kHz and 7.5 kHz, removed at source. Room reverb on aux. | [SOS](https://www.soundonsound.com/techniques/inside-track-st-vincent-pay-your-way-pain) FACT, UNCONFIRMED-NUMBER; order not confirmed |
| MCR "Welcome To The Black Parade" (CLA) | Limiter in transfer -> blue-stripe 1176 4:1 quick release -> heavy riding. BVs: TSL3-style comp; de-esser dbx 263x. Hall 7 s on intro; room ~1 s. | [SOS](https://www.soundonsound.com/techniques/secrets-mix-engineers-chris-lord-alge) FACT, UNCONFIRMED-NUMBER (some attributions hedged "probably") |
| Kendrick "To Pimp A Butterfly" (Ali) | "These Walls": opto-style comp threshold at -18, console HP/LP, imager to widen, Distressor for grit, plate reverb on aux. Guests: Fairchild parallel comp. | [SOS](https://www.soundonsound.com/techniques/inside-track-kendrick-lamars-pimp-butterfly) FACT, UNCONFIRMED-NUMBER (-18 not re-opened); insert order unconfirmed |
| Drake "Headlines" (Shebib) | Light Auto-Tune, de-esser, comp, Pultec EQ, Smack!; vocal bus comp, EQ; four aux: reverb, delay, exciter, delay2. One chain for all lead sections. | [SOS](https://www.soundonsound.com/techniques/noah-40-shebib-recording-drakes-headlines) FACT, UNCONFIRMED-NUMBER; order not stated |
| Bieber "Baby" (Joshua) | Lead split across tracks with per-section EQ; comp; warmth processor; narrow-notch EQ; sends: convolution plate and hall; Ludacris: small EQ, long EQ'd ping-pong delay into reverb. | [SOS](https://www.soundonsound.com/techniques/secrets-mix-engineers-jaycen-joshua) FACT, UNCONFIRMED-NUMBER |

## 5. Conflicts between sources (not resolved)

- **EQ vs compressor order.** iZotope: EQ before comp (acknowledged as debated). Hanes (relay): "typically begins with compression followed by EQ" (VERIFIED), but low cut before comp. Pensado: EQ first, no comp. Elmhirst: colour EQ -> FET -> opto. Could differ by whether EQ is corrective (before) or tonal (after), and by tracking-chain colour.
- **De-esser position.** iZotope: after EQ before comp as "common advice", but first, last, or two all valid; basic-chain article places it after comp. Hanes, Eilish: after comp. Gudwin: after EQ, then EQ again to restore top. Scheps: start and often end (UNVERIFIED snippet).
- **Compression amount.** iZotope 3-7 dB; Ogan 3-6 dB; Hanes ~3 or ~10 dB; Elmhirst "control" (qualitative); Elmhirst "Hello" none (UNVERIFIED snippet); Pensado dislikes compression (VERIFIED). Likely depends on genre dynamics and number of stages (serial 1-2 dB each, forum snippet only).
- **Reverb on rap.** Joshua: "kiss of death on rap vocals" (UNCONFIRMED-NUMBER; delay used instead). Shebib: reverb aux on Drake. Ali: reverb aux. Possibly a genre/era split or a short vs long reverb distinction.
- **Reverb pre-delay.** Pensado 16th/32nd note (VERIFIED); blogs 20-60 ms; Harris 16th triplet. Same thing if converted by tempo; no named-record source gives ms.
- **LP on delay/reverb return.** Pensado ~5k/4k (reverb); Meshplugins 4-5 kHz (delay). Consistent; HP differs (300 Hz vs 400 Hz).

## 6. Uncertainty and gaps

- Hanes numbers are second-hand: a blog relaying a Gearspace Q&A; the original statement is UNVERIFIED. Page has affiliate links.
- Plugin order inside SOS lists for Riordan, Ali, Shebib is not explicitly stated by the articles.
- Never opened: Scheps vocal chain, Elmhirst "Hello" (SonicScoop), Winehouse "Rehab" chain, Marroquin, Brauer, Huart, Slate, Vargo, Moss, Weiss, Nail The Mix 1176->LA-2A, Pensado's Place, Tape Op, Mix, Mix With The Masters. Gearspace threads (ad-libs/doubles, serial compression, 1176/LA-2A order) were snippet-only (one was HTTP 403).
- Generic blog numbers (doubles 6-10 dB below lead, HP 150-200 Hz; BV HP 90-150 Hz, dip 200-400 Hz; plate 1-1.5 s with 20-30 ms pre-delay; slap 80-140 ms; ad-lib reverb 0.3-0.8 s; EDM chop sidechain 2-4 dB) seen only as snippets from commercial blogs; unreliable starting points.
- Harris send-based reverb/delay system (six sends, e.g. 1/8 delay into plate, 16th-triplet pre-delay, raise sends until audible then back off): OPINION, UNCONFIRMED-NUMBER, [source](https://mixandmastermysong.com/vocal-reverb-delay-chain/).
- No official manufacturer docs for specific plugins, and no Ableton-stock vocal chain from Ableton's own docs. R&B/rap numbers are thin; EDM chops rest on one producer demo.
- Pensado's Eventide settings are a stated general preference, not confirmed for the "Beep" vocal.

## 7. Sources

| Source | URL | Re-verified |
|--------|-----|-------------|
| SOS Pensado 2007 | https://www.soundonsound.com/techniques/secrets-mix-engineers-david-pensado | Yes |
| SOS St Vincent 2021 | https://www.soundonsound.com/techniques/inside-track-st-vincent-pay-your-way-pain | No |
| SOS Dua Lipa 2020 | https://www.soundonsound.com/techniques/inside-track-dua-lipa-dont-start-now | Yes |
| SOS Weeknd 2015 | https://www.soundonsound.com/techniques/inside-track-weeknd | No |
| SOS Billie Eilish 2019 | https://www.soundonsound.com/techniques/inside-track-billie-eilish-bad-guy | Yes |
| SOS TWICE 2022 | https://www.soundonsound.com/techniques/inside-track-twice-scientist?page=2 | Yes |
| SOS Chris Lord-Alge 2007 | https://www.soundonsound.com/techniques/secrets-mix-engineers-chris-lord-alge | No |
| Mix and Master My Song (Ghenea/Hanes) | https://mixandmastermysong.com/serban-ghenea-vocal-chain-revealed/ | Yes |
| SOS Kendrick 2015 | https://www.soundonsound.com/techniques/inside-track-kendrick-lamars-pimp-butterfly | No |
| SOS Drake "Headlines" 2012 | https://www.soundonsound.com/techniques/noah-40-shebib-recording-drakes-headlines | No |
| SOS Jaycen Joshua 2010 | https://www.soundonsound.com/techniques/secrets-mix-engineers-jaycen-joshua | No |
| SOS Elmhirst / Adele 2011 | https://www.soundonsound.com/techniques/tom-elmhirst-recording-adele-rolling-deep | Yes |
| iZotope basic vocal chain | https://www.izotope.com/en/learn/crafting-a-basic-vocal-chain | Yes |
| iZotope de-essing | https://www.izotope.com/community/blog/the-dos-and-donts-of-de-essing | No |
| Recording Magazine (Ogan) | https://www.recordingmag.com/resources/recording-info/mics-miking/vocal-sessions-la-style/ | Yes |
| Meshplugins vocal throw | https://shop.meshplugins.com/blogs/the-hidden-sauce/vocal-throw-delay | Yes |
| Harris reverb/delay chain | https://mixandmastermysong.com/vocal-reverb-delay-chain/ | No |
| Puremix vocal chops | https://www.puremix.com/blog/creating-vocal-chops | Yes |
| Gearspace threads (snippet only) | https://gearspace.com/board/rap-hip-hop-engineering-and-production/864436-hip-hop-ad-libs-vocal-doubles.html ; https://gearspace.com/threads/chris-lord-alge-parallel-distortion-on-bass-and-vocals.1023539/ | No |
