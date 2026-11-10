# Guitar and Bass FX chains: raw evidence (collector: guitar/bass track)

Date collected: 2026-11-10. Labels: FACT = documented for a named recording/workflow; CONVENTION = widely repeated technique; OPINION = community/blog. "Fetched" = page opened and read via WebFetch. "Search-only" = only a search snippet seen, marked UNVERIFIED.

## Summary of most consistent patterns

1. Pedal order (CONVENTION, Premier Guitar, Guitar World, BOSS agree; PG says it is taste, not law): tuner, (wah), compressor, drive (OD/dist/fuzz), modulation, delay, reverb, amp. Delay/reverb (and often modulation) move to the amp FX loop with high-gain amps.
2. Amp-sim guitar in the box (CONVENTION, Nail The Mix, Sound on Sound EQ guide): record clean DI at -18 to -10 dBFS peaks, optional tight boost pedal sim before amp, amp sim, cab/IR, high-pass 80-100 Hz, low-pass 10-12 kHz, narrow cuts 2-5 kHz, gate. Cab/IR is where most fizz/thinness comes from.
3. Tube Screamer-style boost before a high-gain amp is used to tighten, not add gain: Drive 0, Tone ~6, Level 10, amp gain lowered (Nail The Mix, fetched). Forum sources agree (OPINION).
4. Bass: DI plus amp/amp-sim blended, distortion only in parallel with low end removed (below ~100 Hz pre-distortion, above 2 kHz post), compression 2:1 to 4:1 plus parallel compression, keep one low-end owner (Sound on Sound, Lockwood and Senior).
5. Delay time: dotted eighth = 45000/BPM ms (documented math in Tim Darling's study; the "Edge uses it" is Darling's analysis, not Edge's statement).
6. Compressor placement: before EQ for bright/wiry, after EQ for smooth (Paul White, SOS 1996).

---

## 1. Mixing DI Bass Guitar (Sound on Sound)
- Source: "Mixing DI Bass Guitar", Dave Lockwood, Sound On Sound, August 2022. https://www.soundonsound.com/techniques/mixing-di-bass-guitar (fetched)
- Context: DI bass in a DAW mix, genre-agnostic workflow.
- Chain (ordered):
  1. Edit/cleanup: fix uneven notes by region gain, not by compressor; mute gaps. No setting given.
  2. Remedial EQ: high-pass 30 Hz, 12 or 18 dB/oct.
  3. EQ in context: -8 dB at 500 Hz Q 0.2; high shelf -3 dB from ~3 kHz; +4 dB bump Q ~0.3 centred 100-120 Hz (sweep 90-150); optional -4 dB at 1 kHz; optional +3 dB at 4-5 kHz Q 0.7.
  4. Main compressor: 2:1, threshold for ~4-5 dB max gain reduction, attack 10-20 ms, release auto or ~100 ms, RMS preferred.
  5. Parallel compression (aux): 6:1 or 8:1, ~10 dB GR, fast attack/release (no numbers).
  6. Parallel distortion only: cut below ~100 Hz before, above 2 kHz after; optional pre-distortion compressor 4:1, 6-10 dB GR.
  7. Parallel phaser/chorus with lows removed from return; main bass stays mono. No rates given.
  8. Optional two-band split: Lows = 30 Hz HPF + 24 dB/oct LPF at 300 Hz; Highs = 24 dB/oct HPF at 400 Hz; distortion/modulation fed only from Highs.
  9. Amp/cab plug-in on DI or via aux; if blending DI with amp sim+IR use DI with -6 dB at ~1 kHz Q 0.3 and 18 dB/oct roll-off at 30 Hz, blend lowest audible.
- Evidence label: FACT for this author's workflow (not a named recording); CONVENTION where echoed elsewhere.
- Confidence: high on numbers (read from page). Caveat: the extraction tool paraphrased; verify exact wording before quoting.

## 2. Mixing Bass (Sound on Sound)
- Source: "Mixing Bass", Mike Senior, Sound On Sound, September 2012. https://www.soundonsound.com/techniques/mixing-bass (fetched)
- Context: bass in a small-studio mix, includes synth/sub handling.
- Chain / rules:
  1. Polarity/timing alignment of DI and mic layers first; re-check phase after EQ on one layer or on a parallel distortion return.
  2. High-pass: 20-30 Hz safety; secondary bass parts ~100 Hz; acoustic bass from ~35 Hz.
  3. Sub-100 Hz EQ: narrow cuts starting Q 8 for resonances; bass low E fundamental 41 Hz; room 40-80 Hz.
  4. Presence: boost around 1 kHz; if heavy, low-pass 2-3 kHz; avoid 3-6 kHz harshness.
  5. Sub synth: single oscillator, sine or triangle, no detune, avoid fast attack/release; only one layer carries sub-100 Hz.
  6. Parallel distortion, heavily EQ'd, cuts only.
  7. Compression: 4:1 or higher hard knee for chart styles; attack 1-30 ms; acoustic bass max 9 dB GR.
  8. Multiband salvage on lowest band: ~8:1, ~5 ms attack, ~80 ms release, 8-12 dB GR, before main compressor.
  9. Kick-triggered ducking of bass 2-3 dB per hit (sidechain or group).
  10. Effect returns high-passed; short stereo reverb or chorus.
- Evidence label: CONVENTION/author workflow.
- Confidence: high. Note a mild difference with Lockwood: Senior says 4:1+ for chart styles, Lockwood uses 2:1 main plus parallel 6:1-8:1. Recorded as a conflict of approach, not resolved.

## 3. Sound on Sound "Using EQ" Guitars & Basses
- Source: "Using EQ", Mike Senior and Paul White, SOS, August 2001. https://www.soundonsound.com/techniques/using-eq (fetched)
- Context: EQ start points for acoustic, electric, bass.
- Chain: single-stage EQ guidance.
  - Acoustic: 80-120 Hz weight; 200-300 Hz boom; 1-1.5 kHz nasal; 2-5 kHz clarity; 5-10 kHz sparkle.
  - Electric: high-pass below ~80 Hz; 125-250 Hz warmth; 3-5 kHz attack (cabinets roll off steeply above 4 kHz); above 4-5 kHz boosting mostly adds noise.
  - Bass: 80-100 Hz weight; 100-300 Hz warmth; 500-1500 Hz attack/boxy; 2-5 kHz string/fret noise.
  - Rolling a little top off rhythm guitar focuses it; no specific low-pass given.
- Evidence: CONVENTION. Confidence: high on page content.

## 4. Producing & Recording Electric Guitar Styles
- Source: Paul White, SOS, November 1996. https://www.soundonsound.com/techniques/producing-recording-electric-guitar-styles (fetched)
- Context: per-style tracking and processing (jazz, country, funk, Knopfler/Rea/Gilmour clean, blues, R&B, heavy rock, metal).
- Chain highlights:
  - Clean (jazz): clean combo, close dynamic, compression after EQ with slower attack, spring or plate reverb with top rolled off.
  - Country: compression before EQ; reverb 2-3 s or spring; slapback 80-100 ms single repeat.
  - Funk: bright clean, condenser, compression before EQ, release about 0.5 s or less, boost 3-6 kHz.
  - "Keep it clean" (Knopfler, Rea, Gilmour named by the author as style references): light compression for sustain; for "Floyd-like" sound stereo echo with different delay time per side plus phaser (times not given).
  - Acoustic-style from electric: boost ~150 Hz, cut 500 Hz-1 kHz heavily, peak 4-6 kHz.
  - Blues/R&B: small valve combo; author uses SansAmp XXL pedal into small Fender valve amp for R&B.
  - Metal: overdrive pedal into overdriven amp; compression after preamp with short release; double-track and pan L/R; British sounds scooped-mid.
  - Compression before EQ = bright/wiry; after EQ = smooth.
- Evidence: CONVENTION (author advice), 1996 so dated gear. Confidence: medium-high; many "no setting given" (ratio, threshold, decay).

## 5. Guitar Amp Recording: Pro Techniques Put To The Test
- Source: Mike Senior, SOS, August 2007; read via reprint https://solodallas.com/blogs/blog/guitar-amp-recording-from-sound-on-sound (fetched; reprint dated 21 Oct 2010 crediting the original SOS article). Reprint, not the SOS URL: confirm against SOS before citing.
- Context: compilation of producer/engineer techniques.
- Documented per-person techniques (FACT as attributed by the article, relayed through reprint):
  - Joe Barresi: SM57 and MD421 at speaker edge (dead centre for brighter); dedicated splitter (Little Labs PCP or Systematic Systems); check phase as each mic is added.
  - Mike Hedges: three tracks (clean, half-driven, fully driven) faded through the song.
  - Hugh Padgham: MD421 on each of the two 12-in speakers of a Roland JC120, panned L/R, chorus on.
  - John Leckie: SM58 plus U67, U67 usually 10-15 dB down.
  - Jack Douglas "phase EQ": SM57 and MD421 in a triangle plus condenser with 10 dB pad ~1 ft away; check they add, flip polarity if not.
  - Distances: Albini 10-12 in start; Parsons ~1 ft up to 4 ft; Al Schmitt room mic 15-20 ft.
- Confidence: medium-high. No EQ/compression settings beyond the above.

## 6. Nail The Mix: How to Record a Guitar DI for Metal
- Source: Nail The Mix Staff, 11 July 2025. https://www.nailthemix.com/how-to-record-a-guitar-di (fetched)
- Context: metal DI tracking and re-amp.
- Chain: guitar/good cable; DI box (Radial ProDI passive, J48 active; Red Eye 3D or Torpedo Reload for DI/re-amp); record peaks -12 to -10 dBFS with no EQ or compression; DI edit (tighten timing, gate or hand-edit noise, high-pass 80-100 Hz, slight fast-attack compression for inconsistent players); then re-amp, load box, or amp sim (5150, Neural DSP named); cab/IR or Fredman two-SM57 technique. Gate values, compression values, amp gain: no setting given.
- Evidence: CONVENTION. Confidence: high for stated numbers. Note differing level target vs source 7 (-12 to -10 here, -18 to -12 there): conflict recorded, not resolved.

## 7. Nail The Mix: Amp Sim FAQs
- Source: Nail The Mix Staff, 17 Sept 2025. https://www.nailthemix.com/amp-sim-faqs (fetched)
- Context: modern metal amp-sim chain.
- Chain: Hi-Z input or DI box; Tube Screamer-style boost before sim (Drive 0, Tone ~6, Level 10) with amp gain reduced to ~5-6 to tighten, important for drop-F# and lower; amp sim then cab/IR (cab usually the source of fizz/thinness; third-party IRs optional); post-EQ low-pass ~10-12 kHz, high-pass ~80-100 Hz, narrow cuts of a few dB in 2-5 kHz; aggressive gate; guitar bus with light saturation/compression. DI peaks -18 to -12 dBFS; buffer 64 or 128 samples. The article does not spell out the order; the fetched summary assembled it from separate tips.
- Evidence: CONVENTION. Confidence: medium-high.

## 8. Premier Guitar: Tone Tips, Echo and the Dirty Amp
- Source: Pete Thorn, Premier Guitar, 3 Oct 2016. https://www.premierguitar.com/tone-tips-echo-and-the-dirty-amp (fetched)
- Context: delay placement and settings.
- Chain: drive then delay generally; use FX loop on preamp/master amps because time effects can get "out of control and muddy" before distortion; exception, echo into a dirty amp responds dynamically. Eddie Van Halen example per the article: 1960s Marshall Super Lead at 10 with Echoplex EP-3, 300 ms with one repeat ("Ain't Talkin' 'Bout Love"). Delay mix start "just above minimum"; repeats should roll off treble. Joe Walsh "The Bomber" Echoplex into front of amp, regeneration no number.
- Evidence: FACT for the EVH/Walsh examples as stated by the author; CONVENTION for placement. Confidence: medium-high.

## 9. Premier Guitar and Guitar World / BOSS pedal order guides
- Sources: PG explains (no date seen) https://www.premierguitar.com/explains/pedals-effects ; Guitar World https://www.guitarworld.com/gear/where-to-place-your-effect-pedals-in-your-signal-chain ; BOSS https://articles.boss.info/the-ultimate-guide-to-guitar-effects-pedal-order-and-signal-chain/ ; PG "State of the Stomp" https://premierguitar.com/articles/21915-state-of-the-stomp-a-solid-case-for-doing-it-wrong. All SEARCH-ONLY (UNVERIFIED by direct fetch; summary via search tool).
- Chain: tuner, wah/filter, compressor, drive, (pitch), modulation, delay, reverb, looper; delay before reverb; reverb usually in FX loop unless very clean amp; compressor not after drive (amplifies noise) per Guitar World; PG says order is taste and wah/drive swaps are common.
- Evidence: CONVENTION. Confidence: medium (not fetched). Conflict: compressor before vs after drive is "single most debated" per aggregator results.

## 10. BOSS: Order of Operation, Bass Effects Signal Chain
- Source: Lee Glynn, BOSS Articles, no date shown. https://articles.boss.info/order-of-operation-a-guide-to-bass-effects-signal-chain/ (fetched)
- Chain: bass, tuner, compression, wah/filter, octaves, OD/dist/fuzz, noise suppressor, EQ (restore low end drained by distortion), modulation, volume, delay, reverb, amp. Katana Bass chain 2 adds a Blend (low-pass on dry path, high-pass on wet path). No knob values given.
- Evidence: CONVENTION plus manufacturer product description. Confidence: high for order.

## 11. Premier Guitar: Using Pedals to Enhance Your Recordings
- Source: Bryan Clark, Premier Guitar Recording Dojo, 21 Mar 2023. https://www.premierguitar.com/diy/recording-dojo/using-pedals-to-enhance-tracks (fetched)
- Context: re-amping tracks through pedals from a DAW.
- Chain: duplicate track, send via interface line outs to pedals, record return; if weak, switch input from line to mic; his flow overdrive, modulation, time-based, looper; use aux sends for mod/time plugins and aux buses for compressors. No numeric settings given.
- Evidence: CONVENTION/workflow. Confidence: medium.

## 12. Edge delay study (U2)
- Source: Tim Darling, "A Study of The Edge's (U2) Guitar Delay", last updated May 2006. https://www.amnesta.net/edge_delay/ (fetched first ~100k of ~225k characters)
- Context: delay timings measured from recordings; fan analysis, not Edge-stated.
- Chain: guitar into modulated delay(s) (Memory Man Deluxe on Boy/October, Korg SDD-3000 later, two TC 2290 from Joshua Tree on per the page) feeding Vox AC30s; split into two delays/two amps. Dotted eighth 3/16 = 45,000/BPM ms (450 ms at 100 BPM). Darling estimates: With or Without You ~410 ms, Still Haven't Found 450 (left)+150 (right), Bad 467+221, Streets 350+525. Mostly 1-2 audible repeats. Mod "audible but not overpowering" (no number).
- Evidence: OPINION/analysis (measured estimates), with interview quotes about approach separate. Confidence: medium; commenters dispute some songs (recorded by the page).

## 13. Shoegaze reverse-reverb (Red Panda) and Kevin Shields context
- Sources: Red Panda support article, Curt Malouin, modified 23 Nov 2021, https://support.redpandalab.com/support/solutions/articles/43000644553-shoegaze-reverse-reverb (fetched); Happy Mag, Anthony Sfirse, 22 Apr 2021, https://happymag.tv/engineering-the-sound-my-bloody-valentines-loveless/ (fetched).
- Context: My Bloody Valentine, Loveless era, shoegaze.
- Documented about the record (Happy Mag, attributes to Moulder/Shields): guitars sent through Yamaha SPX90 on reverse reverb; Roger Meyers Active Fuzz plus Octave Fuzz (gating effect when Octave Fuzz driven); tremolo arm "glide" technique; two amps facing each other with different tremolo and mics between them (one song); album recorded mainly in mono. Article gives no pedal order or settings.
- Red Panda (manufacturer, NOT a recording chain): guitar, Context 2 (reverse mode; blend 2:00, predelay 11:15, decay 10:30 kept short, high 3:00, low ~1:30, mod 3:00-5:00), fuzz, clean amp; reverse "fairly short", placed before fuzz/overdriven amp. Delay time ~11:15, feedback ~11:00. Clock positions, not units. Page never names Shields in text; the settings are "a starting point" for the sound, not a replica.
- Evidence: FACT (SPX90, fuzzes, two-amp trick per Happy Mag) vs OPINION/manufacturer (Red Panda settings). Confidence: medium. Caveat: Wikipedia/GuitarGangsters claims seen in search (Guitar World 1992 quote "just two amps facing each other, with tremolo") were not opened; UNVERIFIED.

## 14. Alan Moulder on Nine Inch Nails and Smashing Pumpkins
- Source: Richard Buskin, SOS, May 2000. https://www.soundonsound.com/people/alan-moulder-recording-nine-inch-nails-smashing-pumpkins (fetched)
- Context: The Fragile, ambient/mangled guitar textures.
- Chain: guitar to amp, DI, or both together; console send to Eventide DSP4000 using sample-card loop with overlay, build up loops, capture to DAT, chop into arrangements; sympathetic acoustic guitars tuned to a chord, compressor pedal, recorded DI. Moulder home rig lists Eventide DSP4000, Watkins Copicat, Roland RE201, Lovetone pedals. No amp models or settings for guitar.
- Evidence: FACT (named album workflow). Confidence: high; low detail.

## 15. Bass blends: Tim Commerford, Justin Chancellor, Chris Wolstenholme
- Sources (all SEARCH-ONLY, UNVERIFIED): Guitar World Wolstenholme feature https://www.guitarworld.com/features/too-much-is-never-enough-muses-chris-wolstenholme-reinvents-art-rock-bass-for-the-21st-century (page fetch returned title only, body unavailable); TalkBass threads https://www.talkbass.com/threads/tim-commerford.265221/ and https://www.talkbass.com/threads/justin-chancellors-signal-path-check-it-out.347041/ (forum paraphrases of Bass Player, OPINION).
- Claims seen in search results (not verified): Wolstenholme keeps one amp clean and puts distortion on a split path, studio same as live plus a clean DI for re-amping; Commerford runs clean, overdrive and in-between amps blended; Chancellor keeps a clean path via splitter. No settings.
- Evidence: OPINION/secondhand. Do not use as FACT until Bass Player or Guitar World text is read.

## 16. DI plus amp bass blend (community and blog, OPINION)
- Sources (search-snippet only, UNVERIFIED): https://forum.cockos.com/showthread.php?t=240483 (DI HPF ~60-70 Hz, distortion/amp track HPF ~300 Hz, LPF ~5k); https://theproaudiofiles.com/mixing-bass-guitar/ (align DI and mic phase, compress DI hard, amp more dynamic); https://www.hollyland.com/blog/topics/record-bass-guitar (60-70% DI to 30-40% amp starting blend).
- Consistent with Senior and Lockwood on phase and parallel distortion. Treat numbers as opinion.

## 17. Acoustic guitar starting points (OPINION)
- Sources (search-only, UNVERIFIED): https://www.musicguymixing.com/eqing-acoustic-guitar/ (HPF start 70 Hz; threshold 5-10 dB below average); https://danmurtagh.com/acoustic-guitar-eq (80 Hz solo, 150 Hz in full mix); https://tonyosomusic.com/thoughts-tidbits-and-tips/blog/7600785/acoustic-guitar-eq-cheat-sheet-the-settings-i-actually-use (90 Hz HPF, -2 to -3 dB at 250 Hz); https://www.lewitt-audio.com/blog/how-to-mix-acoustic-guitar (HPF ~80 Hz, attack 15-30 ms, release 60-100 ms); Johnny Copland (4-8 dB GR) https://johnnycopland.com/how-to-make-acoustic-guitar-sound-better-in-your-mixes/ .
- Agreement: HPF 70-150 Hz depending on role, cut ~250 Hz mud, boost 3 kHz presence, 10 kHz shelf for air, gentle compression 4-8 dB GR. Blog-grade, no engineer attribution.

---

## Gaps and uncertainties
- No Neural DSP, Positive Grid, Kemper, Line 6, UA or Fractal manufacturer article was found/read; searches returned third-party guides only. Not verified.
- No Mix with the Masters, Tape Op, or Bass Player primary text was read; Bass Player claims are relayed only through TalkBass forum threads (UNVERIFIED).
- Wolstenholme Guitar World page body would not load; chain details unverified.
- Ambient/shoegaze: only Happy Mag (and Red Panda manufacturer settings) read; no engineer interview with reverb decay times or pedal order. Guitar World 1992 Shields interview not opened.
- High-gain metal: no named-engineer chain with numbers (Barresi miking exists, but no EQ/compression values). Andy Wallace: nothing technique-specific found.
- Clean/crunch with named recordings: only Paul White's style guide (1996), no per-recording chains.
- Pedal-order guides from PG/Guitar World/BOSS (item 9) were summarised by search only; PG itself states the order is taste.
- Conflicts left open: DI record target (-12 to -10 vs -18 to -12 dBFS); bass compression ratio (2:1 + parallel vs 4:1+); compressor before vs after drive.
- Reverb decay times and delay times for ambient guitar were rarely stated; only slapback 80-100 ms, EVH 300 ms, and Darling's Edge estimates.
- Extraction was done by a summarising fetch tool; numbers should be spot-checked against the pages before being coded into presets.
