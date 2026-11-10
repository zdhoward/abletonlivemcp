# Mastering: chain order, M/S, loudness and delivery

Source: `research/raw/2026-11-10-mastering.md`, curated 2026-11-10. Sibling pages: [vocals](vocals.md), [drums](drums.md), [busses-mixing](busses-mixing.md), [guitar-bass](guitar-bass.md), [keys-synths](keys-synths.md).

## 1. Scope and how to read this page

Mastering-stage FX chains for the MCP server, organized by ROLE and stage order (corrective EQ, compressor, tonal EQ, saturation, stereo/M-S, multiband, limiter, dither), not by brand.

Labels:
- FACT: stated by an engineer, platform or standards body in their own words.
- CONVENTION: repeated across third-party guides, not authoritative.
- OPINION: one author's view.

Verification tags: RE-VERIFIED (page re-opened in this synthesis pass, 2026-11-10), COLLECTOR-FETCHED (opened by the collector only), SECOND-HAND (relayed via other sites), UNVERIFIED, UNCONFIRMED-NUMBER.

## 2. Loudness and delivery targets

| Platform / standard | Number | Source page | Status |
|---|---|---|---|
| Spotify normalization | -14 LUFS integrated (ITU 1770) | support.spotify.com/us/artists/article/loudness-normalization/ | FACT, RE-VERIFIED |
| Spotify master advice | Master at -14 LUFS integrated; keep true peak below -1 dBTP | same | FACT, RE-VERIFIED |
| Spotify, masters louder than -14 | Keep true peak below -2 dBTP | same | FACT, RE-VERIFIED |
| Spotify Premium listener levels | Loud -11, Normal -14, Quiet -19 LUFS | same | FACT, RE-VERIFIED |
| Spotify Loud-mode limiter | -1 dB, 5 ms attack, 100 ms decay | same | FACT, RE-VERIFIED |
| Spotify quiet tracks | Raised, but limited by peak headroom (example: -20 LUFS / -5 dBFS TP lifted only to -16 LUFS) | same | FACT, RE-VERIFIED |
| AES TD1004 (v1.0, 19 Oct 2015) target loudness | Not above -16 LUFS, not below -20 LUFS | aes.org/wp-content/uploads/2024/01/AESTD1004_1_15_10.pdf | FACT, RE-VERIFIED (PDF text) |
| AES TD1004 peak | Max -1.0 dB TP; safety limiter at -1.0 dB TP before encoding; true-peak metering at least 4x oversampling | same | FACT, RE-VERIFIED |
| AES TD1008 (2021) music | Track normalization -16 LUFS; album normalization about -14 LUFS for loudest track; speech/assorted -18 LUFS | productionadvice.co.uk/td1008/ (aes.org page 403, aes.org PDF link 404) | SECOND-HAND, existence confirmed in search listing of the AES page |
| AES TD1008 true peak | not found | n/a | UNCONFIRMED-NUMBER |
| Apple Music, Apple's own PDF | "Leave at least 1 dB of headroom"; no LUFS number | apple.com/apple-music/apple-digital-masters/docs/apple-digital-masters.pdf | FACT, COLLECTOR-FETCHED |
| Apple Music "-16 LUFS / -1 dBTP" | -16 LUFS, -1 dBTP | e.g. masteringthemix.com/blogs/learn/producing-music-for-apple-music (not opened) | SECOND-HAND, not in Apple's PDF |
| Apple Sound Check tolerance | +/-2 LU vs +/-1 LU (sources disagree) | search snippets | UNCONFIRMED-NUMBER |
| YouTube | About -14 LUFS; reportedly never boosts quiet audio | third-party only (frame.io, Mastering The Mix, Production Advice) | UNVERIFIED; no official page found (answer/7050148 404; search found none) |
| YouTube per Katz | -13 dB | Tape Op #116 | conflict, see section 7 |
| Tidal | -18 LUFS (Katz: "sensible") | Tape Op #116 | Katz's statement only; platform page not checked |
| Amazon, Deezer, club, CD | none | n/a | NOT FOUND |

Notes:
- TD1004 explicitly aims at streamers, with the -16 to -20 window for quality and mobile audibility. Productionadvice relays that TD1008 renamed "Target Loudness" to "Distribution Loudness" because it was mistaken for a mastering target, and says creators may master at any loudness (SECOND-HAND). Spotify's own page describes -14 as the level it adjusts to. Treat all figures as normalization references, not required mastering levels.
- Platforms now sit outside TD1004's window (Spotify -14). TD1004 is 2015.
- TD1008 exists (confirmed via AES page listing: AESTD1008 "Recommendations for Loudness of Internet Audio Streaming and On-Demand Distribution"; PDF v3.13 dated 2021-09-24 in its filename). Its content here is second-hand only.

## 3. Consensus chain order and typical ranges

Katz says there is no typical order (FACT, Dynaudio 2017: "there is no typical way"; Digido K-1 console lets gear insert "in virtually any order"). The order below is CONVENTION (Mastering The Mix, Born Creative, SOS Paul White, Ozone guides). Limiter last is the one point no source disputes.

| Stage | Role | Typical range | Source / label |
|---|---|---|---|
| 1 | Corrective EQ | HPF 20-30 Hz, 12 dB/oct; narrow cuts 2-4 dB, often 200-400 Hz | Born Creative (OPINION/CONVENTION) |
| 1 alt | "Smile" cut | cut about 200 Hz-1 kHz by a few dB | Paul White, SOS 2003 (FACT for author) |
| 2 | Compressor (glue) | 2:1, attack 10 or 30 ms, release Auto, about 1-2 dB GR | Born Creative (OPINION/CONVENTION) |
| 2 alt | Overall compression | 1.1:1-1.2:1, 3-4 dB GR, attack 5 ms, release start 50 ms | Paul White (FACT for author) |
| 3 | Tonal EQ | moves under about 1.5 dB (e.g. +0.5 dB shelf above 8 kHz) | Born Creative (OPINION) |
| 4 | Multiband | low crossover about 120 Hz, slow attack, 1-2 dB on low band | Born Creative (OPINION) |
| 5 | Stereo / M-S | width 100% up to 110%; mono below about 120 Hz | Born Creative (OPINION); Mastering The Mix narrows below about 250 Hz (CONVENTION, vendor) |
| 6 | Saturation | Soft Sine, drive 1-3 dB, output compensated | Born Creative (OPINION); Paul White: placement flexible |
| 7 | Limiter | ceiling -1.0 dB (others cite -0.3 or -1; UNVERIFIED); 2-3 dB GR (Born Creative), at most about 6 dB (Paul White) | CONVENTION |
| 8 | Dither | last, only on bit-depth reduction | Ozone summary, UNVERIFIED; no authoritative source |

Additional documented points:
- AES TD1004: a maximum of 1 dB of limiting before final encoding is a starting point; limiting more than about 1 dB may produce more audible artifacts than letting occasional transients clip; use the ear as final judge. A lower target is preferred to heavy peak limiting.
- Katz: EQ "most often before compression" (Gearspace snippet, UNVERIFIED). Parallel compression blended in about 1 dB steps; API 2500 parallel blend at -7.5 dB in one example (FACT, own site).
- FabFilter Pro-L 2 help (vendor, FACT for product): enable True Peak limiting; set output level to the standard's maximum (example -1.0 dBTP); 4x oversampling with lookahead of 0.1 ms or more keeps inter-sample peaks within about 0.1 dB.
- Paul White: do not normalize before other processing; clipped bursts under 1 ms. Pre-LUFS article.
- Order contexts: Mastering The Mix places stereo before EQ and compression (cleanup, stereo, broadband EQ, bus comp, limiter). Born Creative Ableton chain places stereo after multiband. See section 7.

## 4. Named-engineer content

| Engineer | Documented | Source |
|---|---|---|
| Bob Katz | No typical order. M/S "powerful but also screws up the mix if overused". More compression dulls highs. Serial plus parallel compression. K-System: 0 = 83 dB SPL per channel. Over-compression since about 1995 "needlessly over-processed". Gear list is snippet-only. | Dynaudio 2017, Tape Op #116, Digido (FACT) |
| Bob Ludwig | Prefers subtractive EQ, boosting common on dull tracks. Analog path after D/A. No dB figures, no ordered chain. "3 dB is already a lot" and Audeze gear list are snippet-only (UNVERIFIED). | Massenburg DesignWorks page |
| Emily Lazar | Uses multiband, Fairchild-type limiters, Neve 1073, Pultec, SSL bus comp, mostly stem mastering; EQ directly before multiband compressor; "more of a scalpel than a hatchet". No settings. | UAD interview |

NO chain found: Greg Calbi, Dave Kutch, Randy Merrill, Matt Colton, Bernie Grundman. Do not attribute chains to them.

Do not cite the SOS review of Katz's book as Katz settings; it has no numbers.

## 5. M/S, stereo, vinyl, CD, club

- M/S (Barry Watson, SOS 2012, FACT for method): Mid gets high shelf for lead vocal, high-mid peak, gentle low-mid scoop, 1-2 dB compression at low ratio. Sides get HPF; +3 dB on sides as a widening example. Linear-phase EQ preferred. Compare to unprocessed often; too much side boost masks mid.
- Sage Audio (OPINION/CONVENTION): side HPF to mono the lows; side high shelf to widen; more mid compression widens the image, more side compression narrows it; M/S limiter hits mid harder; cut side near 2 kHz to focus vocal.
- Vinyl (WEAK sourcing, one unnamed-author site, not cutting-engineer documentation): mono below about 150-200 Hz, about -14 to -12 dBFS RMS, sides under 22 min, de-ess harder, consult the cutting engineer. Conflict: other blogs give 100-200 Hz for the mono cutoff. UNCONFIRMED-NUMBER.
- CD: no numeric source. Katz cites Californication at about -5 LUFS (PLR 5 dB) as the loudness-war extreme.
- Club: NOT FOUND.

## 6. What not to do

- Hypercompression and clipping: Vickers (AES 129th Convention, 2010, FACT, peer-reviewed): pop CD average levels rose almost 20 dB in 20 years vs about 4 dB for LP over 40 years; Death Magnetic DR 3 dB; clipping, inter-sample clipping and aliasing listed as artifacts; recommends loudness normalization.
- Apple's brief: tracks mastered loud are played back lower and "can make tracks actually sound weaker"; check clipping (afclip); inter-sample clipping risk at 0 dBFS.
- AES TD1004: heavy peak limiting for loudness is worse than a lower target.
- Paul White: do not judge by flat waveform; do not process out impact; listen for pumping and dulling.
- Katz: pop "point of no return" about -14 LUFS (opinion); loud masters on normalized media have tradeoffs.
- Do not boost side signal excessively; do not boost low-end width (lows should stay centered).

## 7. Conflicts between sources

| Topic | Positions | Handling |
|---|---|---|
| Imager before or after Dynamics | Calvin West (Ozone): EQ, Imager, Dynamics, Tape, Maximizer. Born Creative (Ozone): Imager after tone EQ and Low End Focus. Mastering The Mix: stereo before comp. Born Creative Ableton: stereo after multiband. | Snippet-only for Ozone orders; make order configurable, default stereo after dynamics |
| YouTube -13 vs -14 | Katz (Tape Op): -13. Third-party: -14. | No official page; both unverified |
| Spotify and quiet tracks | Many sites say Spotify only turns loud tracks down. Spotify's page: softer masters get positive gain, limited by peak. | Spotify page wins (RE-VERIFIED) |
| Apple LUFS | Third-party -16 LUFS; Apple's PDF has none. | Keep SECOND-HAND |
| Vinyl mono cutoff | 100-200 Hz vs 150-200 Hz | Unresolved |
| Limiter ceiling | -0.3 dB, -1 dB (Pro-L 2 examples -0.1, -0.3, -1.0) | Default -1.0 dBTP for streaming (TD1004, Spotify) |
| Katz on Spotify | Katz says Spotify target too high and adds peak limiting; Spotify's page differs. | Opinion vs platform doc |

## 8. Uncertainty and gaps

- YouTube, Tidal, Amazon, Deezer official numbers not verified.
- Apple LUFS and tolerance unconfirmed; TD1008 true-peak figure not read from the document.
- No authoritative source for dither, multiband settings, club and CD targets.
- iZotope guide (403), Ableton official mastering guidance, FabFilter Pro-Q and Pro-C docs not collected.
- SOS articles are 2003 and 2012 (pre-streaming-LUFS). Born Creative and Mastering The Mix pages are vendor/blog content with 2026 dates the collector could not cross-check.
- Spotify page undated and may change.

## 9. Sources

| Source | URL | Status |
|---|---|---|
| Spotify loudness normalization | https://support.spotify.com/us/artists/article/loudness-normalization/ | RE-VERIFIED |
| AES TD1004 | https://aes.org/wp-content/uploads/2024/01/AESTD1004_1_15_10.pdf | RE-VERIFIED (PDF text) |
| AES TD1008 page | https://aes.org/community/technical-council/technical-document-aestd1008/ | exists per search; fetch 403 |
| AES TD1008 PDF | https://aes.org/wp-content/uploads/2024/01/20210924_TD1008_v3.13.pdf | fetch 404 |
| Production Advice TD1008 summary | https://productionadvice.co.uk/td1008/ | opened; SECOND-HAND |
| Production Expert TD1008 | https://www.production-expert.com/production-expert-1/aes-update-loudness-recommendations-for-audio-only-streaming | SECOND-HAND |
| Apple Digital Masters PDF | https://www.apple.com/apple-music/apple-digital-masters/docs/apple-digital-masters.pdf | COLLECTOR-FETCHED |
| Mastering The Mix, Apple | https://www.masteringthemix.com/blogs/learn/producing-music-for-apple-music | not opened |
| YouTube (third-party) | https://workflow.frame.io/guide/loudness-for-youtube ; https://productionadvice.co.uk/stats-for-nerds/ | not opened as authoritative; no official page |
| SOS Paul White | https://www.soundonsound.com/techniques/maximising-loudness-your-masters | COLLECTOR-FETCHED |
| SOS Barry Watson | https://www.soundonsound.com/techniques/ms-mastery | COLLECTOR-FETCHED |
| Tape Op #116 Katz | https://tapeop.com/interviews/116/bob-katz-bonus | COLLECTOR-FETCHED |
| Dynaudio Katz | https://dynaudio.com/magazine/2017/august/bob-katz-part-2 | COLLECTOR-FETCHED |
| Digido K-1 | https://www.digido.com/k-1-mastering-transfer-console/ | COLLECTOR-FETCHED |
| Gearspace Katz chain | https://gearspace.com/board/mastering-forum/179025-what-your-mastering-chain.html | 403, UNVERIFIED |
| SOS Katz book review | https://www.soundonsound.com/reviews/bob-katz-mastering-audio | COLLECTOR-FETCHED |
| Ludwig, Massenburg | https://massenburgdesignworks.com/bob-ludwig/ | COLLECTOR-FETCHED |
| Audeze Ludwig | https://www.audeze.com/blogs/audeze-artists/audeze-talks-with-legendary-mastering-engineer-bob-ludwig | snippet-only |
| Lazar, UAD | https://www.uaudio.com/blogs/ua/emily-lazar | COLLECTOR-FETCHED |
| Mastering The Mix chain | https://www.masteringthemix.com/blogs/learn/where-every-mastering-plugin-sits-in-the-chain | COLLECTOR-FETCHED |
| Born Creative Ableton | https://borncreativeaudio.com/blog/ableton-mastering-chain | COLLECTOR-FETCHED |
| Born Creative Ozone | https://borncreativeaudio.com/blog/ozone-mastering-chain | snippet-only |
| Calvin West Ozone | https://calvinwest.com/blog/mastering-with-ozone-produce-a-full-sound/ | snippet-only |
| FabFilter Pro-L 2 | https://www.fabfilter.com/help/pro-l/using/recommendedworkflow | COLLECTOR-FETCHED |
| Sage Audio M/S | https://www.sageaudio.com/articles/how-to-mid-side-process-your-master | COLLECTOR-FETCHED |
| Vickers, AES 129 | https://www.sfxmachine.com/docs/loudnesswar/loudness_war.pdf | COLLECTOR-FETCHED |
| Critical Listening Lab vinyl | https://www.criticallisteninglab.com/en/learn/delivery-formats/vinyl | COLLECTOR-FETCHED, weak |
