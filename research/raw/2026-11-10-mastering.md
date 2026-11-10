# Mastering track: chain order, M/S, loudness targets (collector notes)

Collected 2026-11-10. Evidence labels: FACT (documented by engineer or platform/standards body), CONVENTION (repeated across third-party guides, not authoritative), OPINION (one author's view). "Fetched" means the page or PDF was opened and read in this session. "Search-snippet only" means a web search summary showed it but the page was not opened (treat as UNVERIFIED).

## Summary of consistent patterns

1. Order (CONVENTION, repeated across Mastering The Mix, Born Creative, SOS Paul White, Ozone guides): corrective EQ (optional HPF at 20-30 Hz) -> compression/glue -> tonal EQ -> saturation/exciter -> stereo/M-S -> (multiband / low-end control) -> limiter LAST. Limiter last is the one point no source disputes. Placement of imager vs dynamics varies (Calvin West: Imager before Dynamics; Born Creative Ozone: Imager after tone EQ). Katz himself says there is no typical order (FACT, Dynaudio).
2. Compression amounts are small. Glue: ~1-2 dB GR at 2:1 (Born Creative Ableton, OPINION/CONVENTION). Overall mastering compression 3-4 dB GR at 1.1-1.2:1 (Paul White SOS 2003, FACT for that author). Limiter: <= ~6 dB GR (Paul White); 2-3 dB (Born Creative); AES TD1004 warns limiting >~1 dB at the codec stage can be worse than occasional clipping.
3. EQ: subtract rather than add (Ludwig, FACT). Moves are fractions of a dB to ~1.5 dB for tonal EQ (Born Creative, OPINION).
4. M/S: use for mono-ing lows (side HPF), widening highs, de-harshing; Katz calls it "powerful but also screws up the mix if overused" (Tape Op, FACT). Heavier mid compression/limiting widens image (Sage Audio).
5. Loudness: Spotify official -14 LUFS integrated, TP <= -1 dBTP (<= -2 dBTP if louder than -14). AES TD1004 official -16 to -20 LUFS, TP <= -1.0 dBTP. Apple's own PDF gives NO LUFS number; only "leave at least 1 dB headroom".
6. Anti-pattern: hypercompression/clipping (Vickers AES paper; Apple tech brief; Katz; AES TD1004 prefers a lower target over heavy peak limiting).

---

## 1. Spotify for Artists: Loudness normalization (platform, FACT)
- Source: "Loudness normalization", Spotify support. URL: https://support.spotify.com/us/artists/article/loudness-normalization/ (fetched; undated page).
- Context: official delivery guidance.
- Numbers (as relayed by the fetch; quoted from page):
  - "We adjust tracks to -14 dB LUFS, according to the ITU 1770 standard."
  - Recommend master at -14 dB integrated LUFS, "keep it below -1dB TP max". For masters louder than -14 LUFS keep TP below -2 dB.
  - Premium listener settings: Loud -11 LUFS, Normal -14 LUFS, Quiet -19 LUFS. Loud mode applies a limiter "at -1 dB (sample values), with a 5 ms attack time and a 100 ms decay time".
  - Softer masters are turned up but limited by peak (example: -20 LUFS with -5 dBFS TP lifted only to -16 LUFS). Louder masters are turned down with no added distortion.
- Confidence: high. Caveat: a search snippet via bd-en regional URL matched; I fetched the US page.
- Conflict: many third-party sites claim Spotify only turns loud tracks down; Spotify's page says softer ones are raised.

## 2. AES TD1004.1.15-10 (standards body, FACT)
- Source: "Recommendation for Loudness of Audio Streaming and Network File Playback", AES Technical Document, Version 1.0 dated 19 October 2015. URL: https://aes.org/wp-content/uploads/2024/01/AESTD1004_1_15_10.pdf (fetched, text extracted locally).
- Stated:
  - Target loudness should not exceed -16 LUFS ("to avoid excessive peak limiting") and not be lower than -20 LUFS (mobile audibility). Window -20 to -16 LUFS.
  - Max peak not to exceed -1.0 dB TP "to prevent clipping when using lossy encoders". Recommends a safety limiter at -1.0 dB TP before encoding.
  - Users may choose lower, e.g. -18 LUFS, to allow more peak-to-loudness ratio without excessive limiting.
  - "Use the ear as the final judge, since limiting more than about 1 dB may produce more audible artifacts than simply letting the program clip on occasional transients." Suggests a -1 dB TP limiter with 1 dB lower target rather than 2 dB of peak limiting.
  - True-peak metering needs at least 4x oversampling.
- Related (SECOND-HAND, search snippet only, not opened): TD1008 (2021) windows of -14 LUFS (loudest album track) to -18 LUFS; via Production Expert and Melbourne AES presentation (https://www.production-expert.com/production-expert-1/aes-update-loudness-recommendations-for-audio-only-streaming). UNVERIFIED.

## 3. Apple Digital Masters technology brief (platform, FACT, but no LUFS)
- Source: "Apple Digital Masters: Music as the Artist and Sound Engineer Intended". URL: https://www.apple.com/apple-music/apple-digital-masters/docs/apple-digital-masters.pdf (fetched, text extracted locally; undated).
- Stated: "leave at least 1 dB of headroom" because 4x oversampling on playback can clip data at 0 dBFS. Sound Check measures loudness, stores it in metadata, raises or lowers each track; "songs that have been mastered loud will be played back at a lower volume which can make tracks actually sound weaker". Provides afclip clipping checker and a CAF/Sound Check workflow. Loudness wars described neutrally ("louder is better" is a creative choice).
- No LUFS or LKFS figure appears in the text I extracted. The widely quoted "-16 LUFS / -1 dBTP for Apple" is SECOND-HAND (search summaries citing Production Expert, Mastering The Mix; e.g. https://www.masteringthemix.com/blogs/learn/producing-music-for-apple-music, not opened). Tolerance conflict: one source says +/-2 LU, RTW says +/-1 LU (snippets, UNVERIFIED).

## 4. YouTube (UNVERIFIED)
- Official YouTube help page was not retrievable (support.google.com/youtube/answer/7050148 returned 404). All "-14 LUFS, never boosts quiet audio" claims are third-party search snippets (e.g. https://workflow.frame.io/guide/loudness-for-youtube, https://www.masteringthemix.com/blogs/learn/76296773-mastering-audio-for-soundcloud-itunes-spotify-and-youtube). Not opened.
- Conflict: Bob Katz in Tape Op says YouTube normalizes to "-13 dB" and Tidal to -18 LUFS (Section 7), a different number than -14.

## 5. Sound On Sound, Paul White, "Maximising The Loudness Of Your Masters" (Mar 2003) (FACT for author's advice)
- URL: https://www.soundonsound.com/techniques/maximising-loudness-your-masters (fetched).
- Chain: smile EQ (cut ~200 Hz-1 kHz by a few dB) -> compression -> saturation -> limiting; saturation placement flexible; do not normalize before other processing.
- Settings: overall compression ratio 1.1:1-1.2:1, threshold for 3-4 dB GR, attack 5 ms, release 50 ms start; limiter no more than ~6 dB GR; clipped bursts under 1 ms (about 44 samples at 44.1 kHz). Drum limiting: fast attack, 10-50 ms release, >10:1, 3-6 dB GR.
- Don'ts: do not judge by flat waveform, do not process out impact, avoid clipping on acoustic music (common in dance), listen for pumping and dulling. Note: Pre-LUFS era article; targets are old.

## 6. Sound On Sound, Barry Watson, "M/S Mastery" (Apr 2012) (FACT for author's method)
- URL: https://www.soundonsound.com/techniques/ms-mastery (fetched).
- Reaper + Voxengo MSED split into Mid / Sides tracks. Mid: high shelf for lead vocal, high-mid peak, gentle low-mid scoop; low-ratio compression about 1-2 dB GR. Sides: HPF to remove low energy; example Sides +3 dB to widen. Linear-phase EQ preferred. Cut Source 1-2 dB if headroom lost. Caution: excessive Sides boost makes the mix too wide / masks Mid; compare to unprocessed regularly.

## 7. Tape Op #116 bonus interview, Bob Katz (Nov/Dec 2016) (FACT, engineer's words)
- URL: https://tapeop.com/interviews/116/bob-katz-bonus (fetched).
- Stated: M/S "powerful but also screws up the mix if overused". More compression dulls highs because transients soften. Tidal -18 LUFS "sensible", YouTube "-13 dB" too high, pop "point of no return" around -14 LUFS. Spotify "uses too high a target and adds peak limiting". Californication about -5 LUFS, PLR 5 dB. K-System: 0 dB monitor position = 83 dB SPL per speaker (pink noise, RMS); K-14 for music, K-20 for film (6 dB lower).
- No chain order, no compressor settings given.

## 8. Dynaudio Magazine, Bob Katz & M5P (Aug 2017) (FACT)
- URL: https://dynaudio.com/magazine/2017/august/bob-katz-part-2 (fetched).
- Stated: no typical order ("there is no typical way"). Parallel compression via analog blender in 1 dB steps with Pendulum ES-8 tube limiter; heavy compression blended low; may combine series downward compression with parallel to avoid clamping. K-System: 0 = 83 dB SPL per channel, -20 dBFS RMS pink noise; pop/rock typically monitored at -9 to -11. Over-compression since ~1995 "needlessly over-processed"; will do loud masters if client insists but explains tradeoffs on normalized media.

## 9. Digido, K-1 Mastering Transfer Console (Katz's own site, FACT)
- URL: https://www.digido.com/k-1-mastering-transfer-console/ (fetched).
- Analog gear insertable "in virtually any order"; processing stereo or M/S; compressors serial or parallel. Example: API 2500 in parallel with compressed signal mixed at -7.5 dB ("fairly strong"). Gives no ratio/threshold/EQ settings.
- Katz's gear list in a Gearspace thread (Maselec, Manley Vari Mu, Massive Passive, Focusrite Blue 230, Crane Song HEDD, Z-Sys EQ, Waves L2; "EQ most often before compression"): https://gearspace.com/board/mastering-forum/179025-what-your-mastering-chain.html. Page returned 403; claim is search-snippet only, UNVERIFIED.

## 10. SOS review of Katz "Mastering Audio" (Hugh Robjohns, Oct 2003)
- URL: https://www.soundonsound.com/reviews/bob-katz-mastering-audio (the fetched URL was soundonsound.com/sos/oct03/articles/bobkatz.htm, same review).
- Says the book has a section on importance of processor order but gives none; mentions M&S EQ and compression, macro/microdynamics, K-System. Quote: "It's not how loud you make it. It's how you make it loud". No numbers. Do not cite as Katz settings. Book chapter/page figures not found: UNVERIFIED.

## 11. Bob Ludwig, "EQ in the Mastering Process" (Massenburg DesignWorks; undated) (FACT)
- URL: https://massenburgdesignworks.com/bob-ludwig/ (fetched).
- Stated: EQ, level and compression are the core tools. Subtractive EQ preferred, but boosting common on dull tracks. No dB figures (only a Q of 25 notch for de-hissing). Gear: analog path after high-quality D/A (Manley Massive Passive, Sontec, Massenburg MDW EQ, SPL PQ), some analog compression. No ordered chain. (Audeze 2022-23 gear list "6 channels MDW EQ, 6 Massive Passive, Manley MU compressor" is search-snippet only: https://www.audeze.com/blogs/audeze-artists/audeze-talks-with-legendary-mastering-engineer-bob-ludwig, UNVERIFIED. The claim "3 dB is already a lot" is also snippet-only.)

## 12. Emily Lazar (UAD interview; undated) (FACT, but thin)
- URL: https://www.uaudio.com/blogs/ua/emily-lazar (fetched).
- Names UAD Precision Multiband, Fairchild limiter collection, Neve 1073, Pultec, SSL G bus comp; mostly for stem mastering. Only ordering: EQ directly before the multiband compressor. No settings. "More of a scalpel than a hatchet".
- No documented chains found for Greg Calbi, Dave Kutch, Randy Merrill, Matt Colton, Bernie Grundman: NOT FOUND. Do not attribute chains to them.

## 13. Mastering The Mix, Tom Frampton, "Where Every Mastering Plugin Sits in the Chain" (Jun 1, 2026) (CONVENTION, vendor)
- URL: https://www.masteringthemix.com/blogs/learn/where-every-mastering-plugin-sits-in-the-chain (fetched).
- Order: cleanup (RESO) -> stereo image (STEREOVAULT; keep low end centred, narrow below ~250 Hz, cut rather than boost width) -> broadband EQ (MIXVAULT) -> comp/limit (FASTER MASTER); reference and QC (EXPOSE 2 for streaming loudness, true peak, codec preview) outside the path. General order stated: cleanup -> stereo -> broadband EQ -> bus compression -> limiter last. Gives no dB/ratio/LUFS values. Vendor plugins; note the stereo-before-dynamics placement differs from other guides.

## 14. Born Creative Audio, Charlie Crown, "Ableton Mastering Chain" (Sep 2, 2026) (OPINION/CONVENTION, stock devices)
- URL: https://borncreativeaudio.com/blog/ableton-mastering-chain (fetched; the page promotes a paid rack).
- Chain: EQ Eight (HPF 20-30 Hz, 12 dB/oct; narrow cuts 2-4 dB, often 200-400 Hz) -> Glue Compressor (2:1, attack 10 or 30 ms, release Auto, 1-2 dB GR) -> EQ Eight 2 (moves under 1.5 dB, e.g. +0.5 dB shelf above 8 kHz, ~1 dB at 60 Hz, -0.5 dB near 250 Hz) -> Multiband Dynamics (low crossover ~120 Hz, slow attack, 1-2 dB on low band) -> Utility (width 100%, up to 110%; mono below ~120 Hz; check mono) -> Saturator (Soft Sine, drive 1-3 dB, output compensated) -> Limiter (ceiling -1.0 dB, 2-3 dB GR).
- Search snippets of other Ableton guides (audeobox, violetrecording; not opened) agree on order and give limiter ceilings of -0.3 dB or -1 dB: UNVERIFIED. No official ableton.com mastering page found.

## 15. FabFilter Pro-L 2 Help, Recommended workflow (vendor, FACT for the product)
- URL: https://www.fabfilter.com/help/pro-l/using/recommendedworkflow (fetched). Also https://www.fabfilter.com/help/pro-l/using/outputoptions (snippet only).
- Stated: start from default preset, raise Gain; enable True Peak Limiting and metering; set Output Level to the max your standard allows (example -1.0 dBTP for EBU R128; example values -0.1, -0.3, -1.0 dB); 4x oversampling with lookahead >= 0.1 ms keeps inter-sample peaks within about 0.1 dB; lookahead below 0.1 ms approximates hard clipping. Styles: Modern default; Aggressive for EDM/rock/pop (snippet). No gain figure.

## 16. Sage Audio, "How to Mid-Side Process Your Master" (undated) (OPINION/CONVENTION)
- URL: https://www.sageaudio.com/articles/how-to-mid-side-process-your-master (fetched).
- Side HPF to mono the lows; cut side near 2 kHz to focus vocal; side high shelf to widen; compress mid more = wider image, side more = narrower; M/S limiter mode hits mid harder; multiband expansion of side highs and ~400 Hz low-mids. Meters show mid left, side right.

## 17. iZotope Ozone (UNVERIFIED for first-party content)
- iZotope's Mastering with Ozone PDF returned 403 (https://c3.zzounds.com/media/OzoneMasteringGuide-8ed8210b36b1a3dc6a02d407b53b9ea2.PDF). Claims "no single correct order; Maximizer and Dither last" are from a search summary only.
- Third-party orders (search-snippet only): Born Creative (https://borncreativeaudio.com/blog/ozone-mastering-chain): EQ -> Dynamics -> tone EQ/Stabilizer -> Low End Focus -> Imager -> Exciter -> Maximizer; Calvin West (https://calvinwest.com/blog/mastering-with-ozone-produce-a-full-sound/): EQ -> Imager -> Dynamics -> Vintage Tape -> Maximizer. Conflict on Imager vs Dynamics.

## 18. Vickers, "The Loudness War: Background, Speculation and Recommendations", AES 129th Convention, Nov 2010 (FACT: peer-reviewed convention paper)
- URL: https://www.sfxmachine.com/docs/loudnesswar/loudness_war.pdf (fetched, text extracted locally).
- Stated: pop CD average levels rose almost 20 dB in 20 years vs ~4 dB for LP over 40 years; Death Magnetic DR = 3 dB vs 15 dB for a 1909 cylinder; Robert Dennis quoted: crest factor 10 dB reasonable, modern mastering reduces to as low as 6 dB; clipping, inter-sample clipping, aliasing listed as artifacts; recommends loudness normalization (Katz quoted to the same effect) and negative consumer reviews as pressure.

## 19. Vinyl / club / CD differences (CONVENTION; no authoritative source reached)
- Critical Listening Lab (no named author): https://www.criticallisteninglab.com/en/learn/delivery-formats/vinyl (fetched): mono below about 150-200 Hz, about -14 to -12 dBFS RMS, sides under 22 min, de-ess harder, talk to cutting engineer. Other blogs vary on the mono cutoff (100-200 Hz); Major Mixing is internally inconsistent per search summary. Not cutting-engineer documentation.
- CD / club: no numeric source found. Katz (Tape Op) says CDs like Californication at about -5 LUFS are the loudness-war extreme. Club targets: NOT FOUND.

---

## Gaps and uncertainties
- YouTube official loudness page not retrieved (404); YouTube -14 LUFS is second-hand. Tidal, Amazon, Deezer figures not verified from platform pages.
- Apple LUFS target (-16) and -1 dBTP are not in Apple's own brief; only "at least 1 dB headroom" is.
- No documented chains for Calbi, Kutch, Merrill, Colton, Grundman. Ludwig and Lazar give gear/principles, not ordered chains with settings. Katz gives no fixed order. Katz's book chapter and page numbers not accessed.
- iZotope first-party guide and Ozone docs not readable (403); FabFilter Pro-Q and Pro-C docs not collected. Ableton official mastering guidance not found.
- Sound on Sound hits are 2003 and 2012 era (pre-streaming-LUFS). Born Creative and Mastering The Mix pages are vendor/blog content with dates in 2026 that I could not cross-check.
- Dither and multiband specifics lack authoritative sources beyond Apple's definitions and a Born Creative low-band suggestion.
- Spotify page may change; TD1004 is 2015 and platforms now sit outside its window (-14 LUFS).
