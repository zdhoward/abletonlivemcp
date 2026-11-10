# Busses and general mixing: collected evidence (2026-11-10)

Track: bus/group processing, sends/returns, mix-bus compression, workflow and signal-flow order, gain staging.
Labels: FACT = documented by a named source for a named engineer/record. CONVENTION = widely repeated teaching or manufacturer guidance. OPINION = community/blog view.
"Fetched" = page opened with WebFetch this session. "Snippet only" = seen only in search-result summaries (treat as UNVERIFIED).
Note: WebFetch returns model-summarised page text, not raw text. Quotes below are as returned; verify any number before shipping it as a hard default.

## Summary of consistent patterns

1. Mix-bus "glue" compression is gentle: ratio 1.5:1 to 2:1 (4:1 sometimes), medium/slow attack (10-50 ms), auto or medium release, about 1-3 dB gain reduction (Waves says 2-4; SOS says 1-3). Sources 1, 2, 3, 12.
2. Insert the bus compressor early and mix into it, rather than adding it at the end (SOS Will Haas; Waves FAQ). Opposing practice exists: Scheps uses no bus compression; Pensado reportedly avoids it (see 6, 14).
3. Drum bus gets stronger compression than the master: about 4:1, 10 ms, fast release, 4-6 dB (Waves, convention). Documented pros use 2:1-4:1 with 4-5 dB movement per drum channel (CLA). Sources 2, 3.
4. Sends are 100% wet returns with a shared reverb/delay; HPF about 200 Hz and LPF about 10 kHz on the reverb return (SOS Paul White, Matt Houghton). Depth: more send/less pre-delay = further back. Sources 4, 5, 11.
5. Parallel compression is done on a duplicate/aux of the bus, heavily compressed, blended under the dry signal (Sweetwater snippet; Joshua documented on kick/snare; Brauer multi-bus; Scheps rear bus). Sources 6, 7, 8, 9.
6. Named engineers frequently build per-family buses (drums, music, vocals) with their own processing before the stereo sum (Joshua 3 groups, Brauer ABCD, Odeholm, Blake). Sources 7, 8, 9, 10.
7. Gain staging: about -18 dBFS average per track (iZotope), peaks about -10 dBFS (Paul White) and mix-bus peaks roughly -6 dBFS (community convention, no manufacturer source found). Sources 13, 17.
8. EQ vs compression order has no consensus; "fix before, enhance after" and the EQ-comp-EQ sandwich is the common compromise (opinion). Source 15.
9. HPF is a habit, not a rule: Senior supports systematic HPF in small studios; Exeter uses none (shelves instead). Sources 16, 4, 1b.

---

## 1. Scheps rear bus (multi-stage compression)
- Source: "Multi-stage Compression", Sound On Sound (author/date not shown by fetch). https://www.soundonsound.com/techniques/multi-stage-compression (Fetched)
- Context: Andrew Scheps' "rear bus" technique, named after the rear bus on his Neve 8068; now recreated in the DAW.
- Chain/routing (ordered):
  1. All tracks go to the stereo bus as normal.
  2. Parallel send from nearly everything EXCEPT drums ("basically everything in the mix except the drums") to a rear bus.
  3. Rear bus: multi-mono (unlinked) 1176-style compressor; ratio low, attack slow, release fast. NO numeric settings given.
  4. Stereo bus may still carry a touch of its own compression ("just tickling the meters").
- Purpose: leads trigger most of the compression instead of drums, giving a glued, punchy, energetic mix (rock/grunge).
- Same article: vocal 1176 before LA-2A, 1176 fast, about 8:1 to all-buttons-in, about 3-4 dB off peaks, faster compressor with higher threshold first. Brauer "Brauerizing": four compressed buses (A-D) plus a clean bus, each "no more than a couple of dB", L/R unlinked.
- Label: FACT for Scheps (routing); numbers absent. Confidence: high on routing, none on settings. Note the 1176 specifics (8:1, 3-4 dB) appear in a general section, not clearly attributed to Scheps.

## 1b. Scheps, "In Solitude" and other producers (Mynett)
- Source: "Masters Of The Art Of Mixing", Mark Mynett, Sound On Sound, Aug 2024. https://www.soundonsound.com/techniques/masters-art-mixing (Fetched)
- Context: multiple producers each mixed the same song.
- Scheps: no samples; snare aux reverb Revibe II 835 ms; tom aux reverb Revibe II 876 ms; global drum reverb Seventh Heaven 750 ms routed straight to the mix bus; Scheps Omni Channel saturation on kick/snare/tom aux buses; global drums aux with Devil-Loc Deluxe (subtle) at insert 1 whose sends feed global reverb, a "drums dirt" channel (iZotope Trash), a second Devil-Loc, UAD dbx 160 and Fatso Jr. Master bus: NO bus compression; Eventide reverb at 15% mix.
- Odeholm: kick sidechains almost everything through one multiband band, usually below 120 Hz. Instrument pre-master bus (all but orchestra/vocals): EQ, compression, multiband, stacked tape distortion (Saturn). Orchestra/vocals pre-master bus: no processing. Master: tone-match EQ, Gullfoss, tape emulation, limiting.
- Getgood: bass and guitar buses mirror-EQ'd (bass boosts near 900 Hz and 2k, 80 Hz boost, 1.4k cut; guitar cut around 80 Hz, boost near 1.1k).
- Exeter: NO high-pass filters, uses shelves; bx_console 4000G across 14 submixes.
- Bogren: vocal chain UA 1176, LA-2, Distressor, C4, de-esser, Decapitator; vocal sidechains the rhythm guitar bus (ducks guitars); vocal delay return ducked; delay preferred to reverb.
- Label: FACT (named engineers, one metal record, 2024). Heavy-metal context; do not generalise to pop. Most bus settings not given.

## 2. Waves SSL buss compressor guide
- Source: "How to Use an SSL Buss Compressor: Complete Guide to the Classic Mix Glue", Waves blog, no author, 30 Sep 2025. https://www.waves.com/how-to-use-ssl-bus-compressor-classic-mix-glue (Fetched)
- Chain/settings table:
  - Mix buss: 2:1, 30 ms attack, Auto release, 2-4 dB GR ("glue").
  - Drum buss: 4:1, 10 ms, release 0.1-0.3 (as listed), 4-6 dB GR ("punch").
  - Vocal group: 2:1, 3 ms, Auto, 1-2 dB. Mastering: 2:1, 30 ms, Auto, 1-2 dB.
- Order of operation: pick ratio, lower threshold until GR, then make-up gain to match bypass. Can go on master, drum bus or submixes. Top-down mixing = insert on master first. "More than 4-5 dB on the mix buss usually sounds over-compressed."
- Internal inconsistency: elsewhere gives "30 ms attack, 0.1 release, 2:1" for the mix bus (table says Auto).
- Label: CONVENTION (manufacturer teaching). Confidence: medium-high; table summarised by fetch tool.

## 3. SOS Guide To Mix Compression
- Source: Will Haas (with Peter Moore quotes), Sound On Sound, May 2008. https://www.soundonsound.com/techniques/sos-guide-mix-compression (Fetched)
- Chain/settings: ratio 1.5:1 or 2:1; medium attack (Moore about 50 ms); release medium (about 250 ms), tuned to groove, or auto; threshold for about 1-3 dB GR; make-up to match bypass; stereo link matters; sidechain filter to avoid kick pumping; no multiband on the mix bus.
- Order: insert from the start, mix through it, leave settings alone; do not slap one on right before printing; no brick-wall for loudness.
- Label: CONVENTION (expert magazine guidance). Confidence: high.

## 4. Mixing Essentials (workflow order)
- Source: Paul White, Sound On Sound, Oct 2006. https://www.soundonsound.com/techniques/mixing-essentials (Fetched)
- Workflow order: prep, rough balance (rhythm up, then vocals), group buses (aim for eight main faders or fewer), headroom (track peaks around -10 dB), reference, EQ/comp only with purpose (cut rather than boost, wide gentle boosts, narrower deeper cuts), high-pass (reverb returns about 200 Hz, overheads, bass below 50 Hz), pan after balance (bass and lead vocal centre; kits and piano moderate width; spread backings/doubles), reverb after balance (start about 20% wet, back off 3-4 dB), mono check.
- Pro tips: Spike Stent SSL quad compressor across the stereo bus at 2:1 with GML EQ lifting above 10k (FACT per this article, no GR figure); Alan Parsons "never" compresses/limits a mix.
- No strict EQ/comp order prescribed.
- Label: CONVENTION plus two FACT tips. Confidence: high. Date is 2006; plug-in-era applicability may differ.

## 5. Using Reverb & Delay (send/return)
- Source: Matt Houghton, Sound On Sound, Oct 2007 (Cubase focus). https://www.soundonsound.com/techniques/using-reverb-delay (Fetched)
- Routing: reverb/delay as send FX at 100% wet so channels share a space; 3-6 FX channels as template (author uses six: short ambience, mid, long reverb, plus delays: very short/no feedback, noticeable with a touch of feedback, long). Sends post-fader by default; pre-fader if the source is compressed but you want livelier reverb. Pan the send separately, avoid hard-panning reverb; harder panning suits delays. Compressor after reverb to duck.
- Settings: pre-delay set so reverb is "just distinct" from the snare; reverb time so the tail dies before the next hit; delays tempo-synced unless very short. Cut lows into the reverb; cut highs to push sounds back.
- Label: CONVENTION. Confidence: high; no dBFS/ms figures.

## 6. How To Optimise Your Reverb Treatments
- Source: Paul White, Sound On Sound, Nov 2020. https://www.soundonsound.com/techniques/how-optimise-your-reverb-treatments (Fetched)
- Chain: return EQ before or after reverb: HPF about 200 Hz at 12 or 18 dB/oct; LPF about 10 kHz at 12 or 18 dB/oct ("Abbey Road reverb" trick). Ducking: compressor/gate after the reverb with the dry source (e.g. lead vocal) on the external sidechain; reverb swells in gaps. Delay feeding a reverb: filter about 300 Hz lows and above about 1.2 kHz highs. No pre-delay times given.
- Label: CONVENTION. Confidence: high.

## 7. Jaycen Joshua, "Baby" (Justin Bieber)
- Source: Paul Tingen, Sound On Sound, Aug 2010. https://www.soundonsound.com/techniques/secrets-mix-engineers-jaycen-joshua (Fetched)
- Routing: Pro Tools stems out to Neve 1073/1084 returned via SSL insert returns. Three groups (rhythm, music, vocals), each to an SSL sub bus returning on two faders. Drum submix: SSL G384 compressor plus GML 8200 EQ. Music submix: untouched. Vocal submix: Avalon 2055 EQ for air. About 1 dB subgroup lifts for chorus/outro. Parallel: kick via dbx 160x into Pultec EQP1A blended with original (a Bob Powers chain "passed on by Pensado"); snare via 160x into API 550A, parallel. Crash: Medium Delay 21 ms, original 100% left, delay 100% right, deliberately not tempo-synced. Vocal FX: sent to effects tracks, TL Space convolution reverbs. Backing vocals widened with Waves Center.
- No stereo bus compressor or headroom numbers given.
- Label: FACT. Confidence: high; analogue console hybrid, 2010 pop/R&B.

## 8. Michael Brauer, Coldplay "Violet Hill"
- Source: Paul Tingen, Sound On Sound, Nov 2008. https://www.soundonsound.com/techniques/secrets-mix-engineers-michael-brauer (Fetched)
- Routing: four stereo buses A-D into the SSL centre section, then to the summing amp:
  - A: Neve 33609 then Pultec P1A3S (keys, backing vocals);
  - B: Distressor then Avalon E55 EQ (bass and drums);
  - C: Pendulum ES8 tube limiter (guitars);
  - D: Inward Connection stereo tube limiter (backing vocals).
  - Lead vocal kept off the multibus. Final stereo compressor "barely acts". "Eighty percent of my compressors are used strictly for tone."
- Sends: lead vocal Distressor insert, then sends to five more compressors, each returning on its own channel. Reverb on vocals only ("if you send only one thing to reverb, it'll be huge"). Six aux sends (two Neve 1176s, Lexicon 200, PCM81, variable effect, Bricasti M7/DRE777, DRE777). Mastering chain before tape: ADL 670 then Chandler Curve Bender.
- Label: FACT. Confidence: high on routing; almost no numeric settings.

## 9. Chris Lord-Alge, "Welcome To The Black Parade" (MCR)
- Source: Paul Tingen, Sound On Sound, May 2007. https://www.soundonsound.com/techniques/secrets-mix-engineers-chris-lord-alge (Fetched)
- Routing: SSL 4056 E, no dedicated drum bus described; drums processed per channel: Urei 1178 4:1 and Neve 33264 2:1, slow attack, quick release, roughly 4-5 dB movement; Sony DRE2000 one-second short room. Returns: channels 1-4 delays, 49-52 stereo reverbs; long Lexicon 300 giant hall, 7 s decay, used on orchestra/piano/lead vocal intro and big fills, switched off for the rock sections; one-second room for band sections. Delays tempo-set to quarter/eighth notes (dotted eighths in the bridge), automated spills. Bass: 1176 4:1 about 7 dB GR. Guitars: LA3 2-5 dB.
- Stereo bus compression: not documented. He says compression and limiting are done before printing.
- Label: FACT. Confidence: high. Single 2007 rock mix.

## 10. Manny Marroquin, "Stronger" (Kanye West)
- Source: Paul Tingen, Sound On Sound, Dec 2007. https://www.soundonsound.com/techniques/secrets-mix-engineers-manny-marroquin (Fetched)
- Routing: stereo submixes/stems, printed with effects. Mix bus: Manley Passive across the stereo bus on the SSL, cutting 2-3 dB at 3k. Kick buses: Neve 1073 (+4 dB at 220 Hz, +2 dB at 12k) then Avalon 2044 (5:1). Keyboards: pair of Pultec EQP1A then Neve 33609 3:1 fast release. Lead vocal: Neve 32264 3:1 fast recovery on bus insert, second fader with Tube-Tech CL1B 4:1 medium attack, Avalon 2055, dbx 902 de-esser. Echo Farm delay 577 ms on selected words. Hook vocals: Lexicon PCM42 slaps about 80 ms set far back. SSL side-chain de-esser with +12 dB narrow boost 6-7k on the sidechain channel.
- Separate profile (search snippet only, UNVERIFIED): https://www.soundonsound.com/people/manny-marroquin says hip-hop uses short reverb, EQ'd returns, and he compresses stems rather than the stereo mix.
- Label: FACT. Confidence: high for "Stronger"; no parallel compression documented.

## 11. Dave Pensado, "Beep" / "Buttons"
- Source: Paul Tingen, Sound On Sound, Jan 2007. https://www.soundonsound.com/techniques/secrets-mix-engineers-david-pensado (Fetched)
- Routing: effects normally on a separate aux fed by a send, not inserted. Reverb One 11.5 s with low end rolled off feeding a Metaflanger (one section). Eventide 2016 stereo room: 16th/32nd-note pre-delay, top rolled off about 5k (sometimes 4k), bottom from 300 Hz. Supertap delays 149/298/587 ms (16th/eighth/half). Pensado says he has never liked compression and prefers wide dynamics.
- Bus structure, mix-bus processing and send levels: not given.
- Search-snippet claim (UNVERIFIED, forum): a Gearspace thread says Pensado used three parallel compression submixes instead of 2-bus compression. https://gearspace.com/board/so-much-gear-so-little-time/21633-dave-pensado-i-think-i-figured-out-how-you-get-away-without-mixbus-compression.html (not fetched; labeled OPINION)
- Label: FACT for the SOS article. Confidence: high.

## 12. Tchad Blake
- Source: "I Turn Knobs, Until It Sounds Good - Mixing With Tchad Blake", Adam Burucs, Envato Tuts+, 25 May 2017. https://music.tutsplus.com/i-turn-knobs-until-it-sounds-good-mixing-with-tchad-blake--cms-28866a (Fetched)
- Chain: master bus plugins Slate VTM, Crane Song Phoenix, Chandler Curve Bender, McDSP ML4000, Oxford Inflator; ML4000 limiter on from the start of the mix and removed before sending to mastering; historically "only 1-2 dB compression on the master bus". Drum bus: C4 multiband plus SSL compressor (sometimes two). Sends: Echoboy and Altiverb; Devil-Loc on drums via sends. SansAmp on guitar/snares/bass; Omnipressor on overheads. Sidechain rarely used.
- Caveat: secondhand summary by the author, "not direct quotes from Blake", with typos. Label: FACT-ish (secondary); confidence medium.
- Other Blake pages seen only as snippets (UNVERIFIED): SonicScoop https://sonicscoop.com/mix-masters-the-secrets-of-tchad-blakes-sound-analog-tones-with-digital-tools/ and SOS https://www.soundonsound.com/people/tchad-blake-binaural-excitement. No SOS "Secrets of the Mix Engineers" article on Blake was found.

## 13. iZotope gain staging
- Source: Nick Messitte, iZotope Learn, page shows 9 Oct 2026 (as returned; date looks like a refresh). https://www.izotope.com/en/learn/gain-staging-what-it-is-and-how-to-do-it.html (Fetched)
- Targets: tracks about -18 dBFS at unity (0 VU model for analog-emulating plug-ins), sometimes -20 for extra headroom; submix outputs -14 dBFS (specific to his analog-summing setup); master "doesn't hit 0 dBFS". No numeric master-bus headroom beyond that. Fixing an overloaded drum bus: lower the bus fader or a Utility after the compressor rather than changing drive.
- Label: CONVENTION. Confidence: high for -18; -14 is gear-specific. The "-6 dBFS mix-bus peak" figure comes only from small blogs (see 17).

## 14. Parallel compression (Sweetwater)
- Source: Sweetwater InSync, "Parallel Compression Explained" https://www.sweetwater.com/insync/parallel-compression-explained/ and "Compression Tricks to Give Your Drums Instant Punch" https://www.sweetwater.com/insync/compression-tricks-give-drums-instant-punch/ . BOTH returned HTTP 403 to fetch. Content below from search-result summary only: UNVERIFIED.
- Claimed: duplicate the drum aux return and compress the duplicate with threshold so quiet parts are untouched and ratio at least 20:1; or bus compressor with higher threshold and low ratio reducing peaks only a dB or two.
- Label: CONVENTION, UNVERIFIED. Other snippet-only sources (Sage Audio, Reverb.com) say aux send at unity to a heavily compressed aux, blend under dry.

## 15. EQ before or after compression
- Source: Marco Sebastiano Alessi, Boris FX blog, 12 Dec 2025. https://borisfx.com/blog/eq-before-or-after-compression-best-for-mix/ (Fetched)
- Positions: (a) EQ first (subtractive/corrective): smoother compression, resonances don't trigger the compressor. (b) Compressor first, EQ after (additive): compressor unaffected by EQ boosts, EQ can repair artifacts. (c) Sandwich: EQ, comp, EQ; for drums subtractive EQ then compression then additive EQ.
- Conflict: Paul White (source 4) says use EQ/comp only with purpose and cut rather than boost; neither prescribes an order. Gearspace posters (snippet only, UNVERIFIED, https://gearspace.com/board/so-much-gear-so-little-time/172417-eq-before-after-compression.html) argue a boosted band can trigger the compressor, and that hardware insert points precede the channel EQ.
- No named engineer or session cited. Label: OPINION. Confidence: high that no consensus exists.

## 16. High-pass filtering
- Source: Mike Senior, "Q. Do mixes benefit from low-pass filtering at mixdown?", Sound On Sound, Jan 2012. https://www.soundonsound.com/sound-advice/q-do-mixes-benefit-low-pass-filtering-mixdown (Fetched)
- Position: systematic HPF worthwhile in small studios with questionable low-frequency monitoring; broad LPF less beneficial (harmonics); prefers peaking/shelving cuts for masking; LPF acceptable on amped instruments (top two octaves). No Hz values given.
- Conflict: Exeter in source 1b uses no high-pass filters. Paul White (source 4) gives about 200 Hz for reverb returns, bass below 50 Hz.
- Label: CONVENTION/OPINION by a named expert. Confidence: high.

## 17. Community headroom, width and masking guidance (all OPINION, search snippets only)
- Gain staging blogs (KAN Samples https://kansamples.com/blogs/learn/gain-staging-routing-mix ; Audiospectra https://audiospectra.net/gain-staging/ ): mix-bus peaks about -6 dBFS (some say -6 to -3), subgroups peak about -10 dBFS. Conflict: KAN says master fader to -6 dB; others keep master at unity and pull channels. UNVERIFIED (not fetched). Paul White's -10 dB track peaks (source 4) is the only fetched peak figure.
- Panning/width (https://www.masteringthemix.com/blogs/learn/guide-to-panning-and-stereo-width and others): kick, snare, bass, lead vocal centre; guitars/pads/backings wide; keep content below about 100-150 Hz centred or mono (thresholds quoted vary 100/120/200 Hz). UNVERIFIED.
- Kick/bass masking around 60-100 Hz; fixes: carve and sidechain. UNVERIFIED.

## 18. Ableton-specific (for Live implementation)
- Official: Ableton Live 12 manual, Glue Compressor. https://www.ableton.com/en/manual/live-audio-effect-reference/ . Per search summary (not fetched): Glue is mainly meant for the Main track or Group tracks; sidechain can use any internal routing point including return tracks; sidechain EQ available; sidechain is trigger only. Status: UNVERIFIED by fetch.
- Community (labeled OPINION; search summary only): Born Creative Audio drum bus chain https://borncreativeaudio.com/blog/ableton-drum-bus-chain (Utility with Bass Mono, EQ Eight low cut 20-30 Hz, Drum Buss, Glue at ratio 4 for 2-4 dB GR, optional soft clip; if kick drives compression, HPF Glue's sidechain 80-100 Hz). Return guide https://www.audeobox.com/learn/ableton/return-tracks-guide/ (Reverb Dry/Wet 100% on return, HPF 300 Hz/LPF 8 kHz, EQ after reverb). Vector DSP https://vector-dsp.com/blog/eq-on-return-track/ (HPF 100-200 Hz, LPF 6-10 kHz). The 300 Hz vs 200 Hz HPF difference is a conflict with SOS about 200 Hz.

---

## Gaps and uncertainties

- No Sound on Sound "Secrets of the Mix Engineers" article was found for Serban Ghenea or Tchad Blake. Ghenea: only secondary claims (mixes into his 2-bus chain from the start; Gearspace/Luis Cancion blog, not fetched, UNVERIFIED). Do not attribute specific Ghenea plug-ins/settings.
- Scheps' rear-bus compressor settings: no numbers in SOS. The audiospectra.net "Scheps mix bus chain" (FabFilter Pro-Q, EQ Match, bx_digital V3, Elevate) is a third-party breakdown, UNVERIFIED and not fetched.
- Pensado's own mix-bus/parallel routing is not documented in the SOS article; the three-parallel-submix claim is forum-only. Pensado's Place episodes were not opened.
- Marroquin and Joshua: SOS gives routing but no send levels; Joshua gives no stereo bus compressor.
- Sweetwater pages blocked (403); manual page for Ableton not fetched directly. No manufacturer source gives the -6 dBFS mix-bus peak figure; SSL, UAD, FabFilter, Mix with the Masters not reached.
- No source found giving send levels in dB for any named engineer; only blogs give hints (e.g. about 20% wet start in Paul White).
- Documented engineer examples are analogue-hybrid, 2007-2010 mostly; the 2024 metal piece is a different genre. Treat numbers as examples, not defaults.
- WebFetch summarises pages via a small model; numbers occasionally could be mis-transcribed. Spot-check against the page before locking constants.
- Date oddity: iZotope page shows 9 Oct 2026 as the publication date; may be a refresh date.
