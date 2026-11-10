# Keys and synths FX chains: raw evidence (collector output)

Collected 2026-11-10. Track: piano, electric piano, organ, pads, strings, plucks, leads, synth bass, supersaws, arps.
Labels: FACT = documented for a named recording/workflow; CONVENTION = author's general recommendation; OPINION = community/blog opinion.
Every URL below was opened with WebFetch unless marked UNVERIFIED. Settings are quoted from the fetched page; "no setting given" means the page has none.

IMPORTANT: No source found documents a chain for a NAMED famous recording in this track. Everything here is CONVENTION or OPINION, except the Ableton-device workflow in section 2 and the Spire patch in section 9, which are FACT only as "this author's documented workflow", not as a famous record.

## Summary of consistent patterns

1. Modulation before reverb: strings, pianos, supersaws all say chorus/widener first, reverb after (sections 1, 4, 8, 11).
2. Reverb belongs on a return/send, usually with HP/LP on the return: piano HP/LP unspecified (4); strings return HP 150-200 Hz (11); supersaw send HP 300-400 Hz, LP ~8 kHz (8); vocal-oriented return HP 200 Hz, LP 8-10 kHz (13, opinion, not keys-specific).
3. Pads: high-pass (150-300 Hz range), cut low-mid/presence rather than add reverb; width via chorus/flanger/M-S rather than reverb (2, 3, 7).
4. Sidechain ducking: two tiers. Subtle "breathing" pad (ratio ~2:1, attack 5-10 ms, release 250-400 ms, 3-5 dB) vs obvious pump (ratio 4:1+, fast attack, release synced to 1/8 note or 150-400 ms, 6-12 dB). Duck reverb/delay returns instead of the dry lead (7, 8).
5. Compression on keys is gentle: piano 3:1, 5-10 ms attack, ~5 dB or less (4, 5); strings 2:1, slow attack (11); synth bass 4:1+, attack 1-30 ms, and a low band only multiband at ~8:1 (6).
6. Low-end hygiene: only one layer owns sub (<100 Hz); HP other bass layers at ~100 Hz; HP wide supersaw layer 100-150 Hz; dip 200-400 Hz by 2-4 dB (6, 8, 9).
7. Electric piano in Live: Electric is mono; stereo effects (Auto Pan tremolo, L/R EQ) must follow it; Amp/Cabinet last in Dual mode (1).
8. Pads should be near inaudible and automated, filter highs out in verses (2, 3).

## 1. Rhodes Hog (Ableton Electric chain)
- Source: "Rhodes Hog", Len Sasso, Sound on Sound, January 2016. https://www.soundonsound.com/techniques/rhodes-hog
- Context: Ableton Live Electric instrument, effects and racks.
- Chain (order as described): 
  1. Electric (Piano & Keys presets MkI/MkII/Wurli). Mallet Stiffness and Force: avoid much below 50%.
  2. Auto Pan, Tremolo preset: amount to Mod Wheel, rate to a MIDI CC. No numeric values given. Purpose: Electric is mono, so this creates stereo.
  3. EQ Eight in L/R mode: cut highs on one side, lows on the other. No frequencies/gains given.
  4. Audio Effects Rack with parallel Chorus / Flanger / Phaser chains plus a dry chain, Chain Selector crossfade. No settings given.
  5. Optional rack: Tube / Overdrive / Saturator. No settings given.
  6. Amp then Cabinet, Dual mode, preferably last (Mono mode acceptable only if all stereo effects come after them).
- Layer ideas: Rhodes with Collision "Digital String" through a Gate with Attack at max to soften the attack; Wurly plus Analog "Mellow Brass".
- Evidence: FACT for the documented Live workflow (not a named recording). Confidence: high for ordering rules, nothing numeric. Note this is stock-Live specific and directly usable.

## 2. Pad It Out: 10 ways (Ableton)
- Source: Richard Veenstra, Ableton blog, 4 Aug 2020. https://www.ableton.com/en/blog/pad-it-out-10-ways-make-distinctive-pad-sounds/
- Chain/techniques: Wavetable detune oscillators ~1-10%, first oscillator near zero; vibrato with sine/triangle LFO at ~10% amount; medium-long amp attack and release; Classic unison for width plus low cut EQ, watch phase with a correlation meter; EQ automation (cut highs in verses, restore in choruses or drops); rhythmic pad via volume automation or noise gate sidechained to drums with the drum output muted; re-pitch trick (transpose +7 semitones, bounce, transpose -7 in clip); piano sample with attack removed plus long reverb/release blended into pad; degrade with saturation or bit crusher, Noise unison ~40%, Echo "Hiss Tape Mode" preset (modified).
- Evidence: CONVENTION (Ableton educator tutorial). Confidence: high on devices, medium on exact numbers (only detune %, LFO %, noise 40% are stated).

## 3. Pad processing (Synthesis Workshop)
- Source: "Creating & Using Synth Pad Sounds", Mike Senior, Sound on Sound, May 2010. https://www.soundonsound.com/techniques/creating-using-synth-pad-sounds
- Chain: EQ: cut 4-6 dB around 3-4 kHz (caption shows a narrow 5 dB cut); high-pass gently from ~300 Hz in caption (text says energy below ~200 Hz rarely useful), slope not given. Reverb: warm pads usually none; short reverb for bright pads needing width, decay/level not given. Widening: chorus/flanger/phaser with L/R out of phase, M/S boost, duplicate-mono-invert-blend trick, L/R-swap polarity-invert clone, independent L/R pitch shifts. Ping-pong delay for rhythmic pads (no times). Level: "if you can hear it, it's too loud!", automate down in thin sections and up for choruses.
- Evidence: CONVENTION by a named engineer. Conflict: HP at ~300 Hz (caption) vs "below about 200 Hz" (text).

## 4. Using Effects With Keyboards
- Source: Paul White, Sound on Sound, July 1994. https://www.soundonsound.com/techniques/using-effects-keyboards
- Strings: gentle stereo chorus and/or detune first, then reverb ~3 s (concert hall) used sparingly, especially for slow-release patches; detune example from the choir section 5-10 cents, 20-50 ms delays on the detuned copies, pre-delay 50-100 ms. No chorus rate/depth given.
- Pads: no echo/reverb (gaps already filled); gentle stereo chorus or flanging; slow auto-pan synced to a multiple of tempo (no rate).
- Synth bass: mostly dry; compression/limiting with attack 10-50 ms; centre pan; short delays for ADT, flanging for movement (no times).
- Piano, electric piano, organ, leads: no setting given (page has no sections on them).
- Evidence: CONVENTION, dated (1994 hardware-era). Confidence: high on order (modulation before reverb), low on modern relevance.

## 5. Piano chain: Music Guy Mixing
- Source: Music Guy Mixing, 22 Aug 2024. https://www.musicguymixing.com/mix-piano/
- Chain: EQ (cut a small amount 300-600 Hz; lift near 9 kHz, no gain given) -> compression 3:1, threshold at average level, attack 5 ms, release 50 ms, ~5 dB GR -> optional octave layering -> mono/near-mono in busy mixes -> chorus (e.g. Microshift) on a send, no numbers -> reverb on send, 100% wet, ~1.5 s decay, 20-30 ms pre-delay, filter lows and highs from the reverb.
- Evidence: OPINION (blog). Confidence: medium.

## 6. Piano chain: Sage Audio
- Source: Sage Audio, "How to Mix Piano Pt. 1" (author and date not stated on page). https://www.sageaudio.com/articles/mix-piano-pt-1
- Chain: EQ: HP near 200 Hz when heavy bass/kick; dip ~6 dB at 2-3 kHz to sit behind vocals. Compression: threshold ~-7 dB, 3:1, attack 10 ms, release ~1000 ms (gentler); aggressive variant 2:1 with lower threshold. Reverb/panning deferred to a next post (not covered).
- Evidence: OPINION. Conflict: release 50 ms (Music Guy) vs ~1000 ms (Sage); attack 5 vs 10 ms.

## 7. Mixing Bass (synth bass)
- Source: Mike Senior, Sound on Sound, September 2012. https://www.soundonsound.com/techniques/mixing-bass
- Chain/settings: one layer owns sub-100 Hz, HP the other layers ~100 Hz; sub layer a sine/triangle; low-pass a hidden non-sine sub fairly severely; boost ~1 kHz for cut-through, then LP ~2-3 kHz to control noise; HP 20-30 Hz with a low shelf boost; compression 4:1 or higher, attack 1-30 ms; multiband on lowest band only, ~8:1, attack ~5 ms, release ~80 ms, 8-12 dB GR, placed before the main bass compressor; duck bass 2-3 dB on each kick via sidechain; saturation to tame resonant sweeps; narrow peaking cut Q ~8 (from search summary, not re-verified in the fetched text).
- Evidence: CONVENTION by a named engineer. Confidence: high.

## 8. Supersaw anatomy
- Source: Serkan Cura, "Anatomy of the Supersaw", Sept 2026 (page shows 23 Sept and 18 Sept 2026; publish date unclear). https://www.serkancura.com/en/muzik-en/anatomy-of-the-supersaw/
- Chain: stack plus separate mono sub saw -> HP 100-150 Hz on wide layer -> LP with filter envelope (no values) -> saturation on the summed stack after unison -> EQ dip 2-4 dB at 200-400 Hz -> stereo imaging last. Detune: under 5 cents thickening, 8-20 cents classic trance, 25-40 deliberately detuned. Voices 5-7 leads, 3-5 pads. Keep content below ~300-500 Hz narrow; correlation 0 to +0.5. Reverb: mono send, stereo return, HP send 300-400 Hz, LP ~8 kHz. Lead sidechain 40-80 ms release, 2-4 dB. Delay: ping-pong or short stereo offset, HP the return, avoid dotted 8ths on 16th leads.
- Evidence: OPINION (single blog; cites no sources, refers only to unnamed "published analyses" of the JP-8000). Confidence: low-medium.

## 9. Syntorial supersaw trance lead
- Source: Joe Hanley, Syntorial/Audible Genius, 2019 (page also shows 2026 update). https://www.syntorial.com/tutorials/synth-quickie-supersaw-trance-lead/
- Patch/chain (Spire): 3 saw oscs 9-voice unison, widest; noise osc; HP filter 12 dB (cutoff just thins low end); low sustain, fast decay; then FX: distortion (clip, small amount) -> compression (Spire X-Comp ~half) -> reverb large, fairly wet, long decay, damped highs. No delay, no EQ.
- Evidence: FACT for this author's workflow (not a named record). Confidence: medium-high.

## 10. Trance sidechain by element
- Source: Myloops, "Sidechain Compression for Trance", 15 Sep 2026, no author named. https://www.myloops.net/sidechain-compression-techniques-for-trance
- Settings: pads HP 150-250 Hz, 2:1, attack 5-10 ms, release 250-400 ms, 3-5 dB, ghost-kick trigger, reverb after the compressor and widener/chorus before. Reverb return: 4:1, fastest attack, release 200-300 ms, 4-7 dB. Delay return: 3-5 dB, release ~150 ms. Leads/plucks: no dedicated settings (leads stay mostly untouched, returns are ducked; plucks use a volume shaper).
- Further numbers (search-result summaries only, pages not opened, UNVERIFIED in detail): Ramesh Music pad 2:1, 20-30 ms attack, 100-150 ms release https://rameshmusic.com/sidechain-compression-tutorial/ ; Producer's Bible house pad 6:1-10:1, 0.1-1 ms attack, 250-400 ms release https://musicproductionwiki.com/bible/sidechain-compression ; RingMod genre table (house 4:1, 4-8 dB; trance 4:1-8:1, 6-10 dB, 1/8-note release) https://ringmodsidechain.com/blog/sidechain-compression-settings
- Evidence: OPINION/CONVENTION. Conflict: release 100-150 ms (Ramesh) vs 250-400 ms (Myloops) for pads; subtle vs pumping tiers explain much of it.

## 11. Strings mixing chain
- Source: Music Production Wiki Team, updated May 2026. https://musicproductionwiki.com/articles/how-to-mix-strings
- Chain: strings group bus (peak -12 to -10 dBFS) -> HP 50-100 Hz -> harshness cut 2-4 kHz -2 to -5 dB, Q 2-4 -> optional warmth +2-3 dB at 200-300 Hz -> air shelf 8-12 kHz +2-3 dB -> compression sampled 2:1, attack 30-80 ms, release 150-300 ms -> reverb send: hall 2.5-4 s, 10-20 ms pre-delay, return HP 150-200 Hz (pop/trap: room or plate 0.8-1.5 s); reverb sidechain to kick attack 1-5 ms, release 80-150 ms, 4-6 dB.
- Evidence: OPINION (wiki, orchestral/sampled strings focus). Conflict with section 4: hall ~3 s agrees; HP 50-100 Hz vs pad HP 150-300 Hz is instrument-dependent.

## 12. Synthwave production
- Source: Simon Haven, EDMProd, 23 May 2025. https://www.edmprod.com/how-to-make-synthwave/
- Chain: pad/chords (OB-Xd, filter cut most highs, sidechain to kick and snare); bass sidechain via STFU; lead dry, add reverb and delay in mixer (no amounts); arp plucky, lows and highs filtered, sits back. Only numeric: snare/clap parallel reverb 100% wet with volume automation or sidechain gating; drum bus room reverb with mid removed, Wider 200%, lows EQ'd out; 140 BPM. No chorus settings given.
- Evidence: FACT for author's demo workflow, little keys-specific detail. Confidence: low for synths.

## 13. Piano and keys chain (MusicRadar) - partially verified
- Source: MusicRadar, "Save time with this solid piano & keys mixing chain". https://www.musicradar.com/how-to/save-time-with-this-solid-piano-and-keys-mixing-chain
- WebFetch returned only navigation (page truncated), so author/date/settings are UNVERIFIED. Search-result summary only: hardware-emulation EQ for high-frequency air, mix-bus-style compressor with medium attack, auto release, 2:1 or 4:1; tempo-synced stereo delay 1/4 left, 1/8 right, low wet, fairly high feedback.
- Also UNVERIFIED (truncated fetch): MusicRadar sidechain article https://www.musicradar.com/tuition/tech/how-to-create-classic-pumping-sidechain-compression-624915 . Only the search-summary claim that dropping the last kick in bars 2 and 4 lets the pad swell.

## 14. Generic Ableton melodic chain (arps/plucks)
- Sources: EDMProd, "Learn Ableton Live From Scratch" https://www.edmprod.com/learn-ableton-live-from-scratch/ and "Ableton Wavetable guide" https://www.edmprod.com/ableton-wavetable/ ; Splice https://splice.com/blog/how-to-use-ableton-wavetable/ . NOT opened, search summaries only, UNVERIFIED.
- Claimed: MIDI clip -> Arpeggiator -> instrument -> EQ -> Delay -> output; Arpeggiator before Wavetable, Reverb after, EQ after; pluck from filter envelope. No numbers.
- Vocal-oriented return settings (UNVERIFIED, not keys-specific): reverb decay 1.2-2.5 s, pre-delay 20-40 ms, high cut 6-8 kHz; delay 1/8 or 1/4 synced (tunedrip.com, search summary only).

## Gaps and uncertainties
- No named-recording chain for any keyboard/synth part was found (no Mix with the Masters, Secrets of the Mix Engineers, Attack Magazine, Valhalla DSP, FabFilter, Soundtoys, Native Instruments, Arturia article was retrieved). Searches for Attack Magazine supersaw and SOS Synth Secrets returned nothing usable.
- Organ/Leslie: only forum opinion in search results (Gearspace, Organ Forum); not opened and not recorded as facts. SOS "Synthesizing the Rest of the Hammond Organ" is about modelling the Leslie (800 Hz crossover per search summary, UNVERIFIED), not mixing.
- Electric piano: only the Ableton-device article (section 1) with no numeric settings. Classic Rhodes chain (suitcase tremolo -> chorus -> Space Echo) appeared only as a Gearspace guess; unverified opinion.
- Trap, ambient, pop keys chains: no documented source found. Synthwave source is thin.
- MusicRadar pages failed to render via fetch (truncated). Several Myloops/Serkan Cura/Music Production Wiki pages carry 2026 dates and are single-site blog content, so treat as OPINION.
- Conflicting numbers are noted per section; none resolved. Ableton Reference Manual (Auto Pan, Compressor sidechain) not consulted.
