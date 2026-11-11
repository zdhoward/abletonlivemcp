# Knowledge base: FX chains, songwriting, production, drum programming, MIDI FX, studio organization, mixing troubleshooting, and VST plugins

Built by `/study` on 2026-11-10 for the Ableton Live MCP server. Each page organizes chains by **role and stage order**, not by brand, so a chain can resolve to whatever plugins or stock devices a user owns (see `src/abletonlivemcp/adapters.py`). Raw collector notes with citations are in `research/raw/`.

## Using and extending this folder

**Reading.** Use the MCP tools `knowledge_list`, `knowledge_search` (by words, returns sections) and `knowledge_read` (a page, or one section by heading). They rescan this folder on every call, so a page added a minute ago is found at once.

**Adding a page** (several threads and agents write here at the same time):
- Drop any `.md` file in this folder. Subfolders are fine (for example `knowledge/gemini/`, `knowledge/plugins/`). The page name is its path without `.md`.
- Start with a `# Title` line and use `##` headings for sections, so a section can be read by itself. Nothing else is required: no frontmatter, no registration.
- Label evidence as FACT (documented for a named recording or workflow), CONVENTION or OPINION, link the source URL, and tag numbers you could not confirm against the original page with `UNCONFIRMED-NUMBER`, `UNVERIFIED`, `SECOND-HAND` or `LOW CONFIDENCE`. `knowledge_list` counts these tags per page.
- Do **not** add your page to the table below to register it; listing is automatic. The table is a hand-written overview and can lag behind. Editing the same file from two threads causes merge conflicts.
- Commit only your own files (`git add knowledge/<your files>`), and keep raw collector notes in `research/raw/`, not here.

### Instrument & Stage Knowledge Pages

| Page | Covers | Strength of sourcing |
|---|---|---|
| [vocals](vocals.md) | Lead, backing, rap, R&B, EDM chops; named-record chains (Adele, Billie Eilish, Dua Lipa, The Weeknd, Drake, Kendrick Lamar, TWICE) | Best of the set: many Sound on Sound engineer write-ups. Rap/R&B list plugins but few numbers. |
| [drums](drums.md) | Per-drum chains, drum bus, parallel compression, kick/bass ducking, "In the Air Tonight" | Good for acoustic and parallel compression. No gate, snare-reverb or transient-shaper settings found. Trap/808 is snippet-level only. |
| [busses-mixing](busses-mixing.md) | Bus and group processing, sends/returns, gain staging, EQ/compressor order | Good, but most documented examples are 2007-2010 analogue-hybrid mixes. |
| [guitar-bass](guitar-bass.md) | Pedal order, amp-sim chains, DI + amp bass, parallel distortion | Good for bass and amp-sim; many numbers re-verified. Acoustic guitar is blog-snippet level. |
| [keys-synths](keys-synths.md) | Piano, electric piano, pads, strings, supersaw, synth bass, sidechain tiers | Weak. **No chain tied to a famous recording was found**; almost all of it is convention or opinion. |
| [mastering](mastering.md) | Chain order, loudness targets, M/S, what not to do | Strong on Spotify and AES TD1004 (checked against their own pages). YouTube, Apple and TD1008 numbers are second-hand or unverified. |

### Genre-Specific FX Chain Knowledge Pages

| Page | Covers | Strength of sourcing |
|---|---|---|
| [rock](rock.md) | Classic/modern rock lead vocals, high-gain rhythm guitars, bass parallel clean/dirty split, drum crush bus, rock mix bus (Chris Lord-Alge, Andy Wallace, Butch Vig, Jens Bogren) | Strong: primary engineer interviews and named multi-track breakdown articles from Sound On Sound and Mix Magazine. |
| [hip-hop](hip-hop.md) | Modern trap/boom-bap lead vocals, 808 harmonic generation and mono sub locking, soft-clipping transients, rolling hi-hats, vocal ad-libs (MixedByAli, Mike Dean, Jaycen Joshua, Alex Tumay) | Strong: detailed mix breakdowns from named Grammy-winning engineers and documented masterclasses. |
| [pop](pop.md) | Pristine hyper-compressed lead vocals, stacked vocal walls, rhythmic sidechain pumping, ducked vocal spaces, high-gloss master bus (Serban Ghenea, John Hanes, Max Martin, Tom Elmhirst, Manny Marroquin) | Exceptional: detailed In-The-Box routing, plugin chains, and frequency specifics from industry leaders. |
| [acoustic](acoustic.md) | Steel-string and fingerstyle acoustic guitars, natural acoustic vocals, upright double bass, acoustic percussion, subtle master glue (Al Schmitt, George Massenburg, Chuck Ainlay) | High: authoritative accounts from acoustic engineering pioneers and GML/Capitol Records documentation. |
| [edm](edm.md) | Supersaw leads, bass sound design (OTT upward/downward compression), kick/sub volume envelope ducking, build-up washouts, drop stereo collapse, club loudness (Luca Pretolesi, Mick Guzauski, Skrillex, Steve Duda) | Strong: documented producer workflows, Xfer OTT architecture, and commercial master bus clippers. |

### Genre Songwriting, Melody, Rhythm & Production Knowledge Pages

| Page | Covers | Strength of sourcing |
|---|---|---|
| [rock-songwriting-production](rock-songwriting-production.md) | Minor pentatonic & blues scale, Mixolydian/Dorian modes, riff-as-hook, Bonham behind-the-beat snare drag vs. punk rush, loud-quiet-loud dynamics, quad-tracking guitars, amp pairing, room mic compression (Andy Wallace, Rick Rubin, Butch Vig, Brendan O'Brien) | Strong: documented multi-track analyses, Berklee songwriting literature, and Sound On Sound producer retrospectives. |
| [hip-hop-songwriting-production](hip-hop-songwriting-production.md) | Aeolian/Phrygian darkness, harmonic minor drill melodies, flow cadence as melody, Migos triplet flow, half-time trap grid (snare on beat 3), MPC swing & J Dilla unquantized timing, circular non-resolving loops, 808 saturation and sidechain carving (Metro Boomin, Mike Dean, MixedByAli, Jaycen Joshua) | Exceptional: masterclass breakdowns, producer interviews, and musicological analyses of rap cadence and sample manipulation. |
| [pop-songwriting-production](pop-songwriting-production.md) | Max Martin "melodic math" (leap followed by step, vowel formant targeting), sectional contrast (verse vs. pre vs. chorus), four-on-the-floor with funk bass syncopation, "Axis of Awesome" four chords, borrowed minor iv heartbreak, massive vocal stacking, 7-second rule, ear candy (Max Martin, Shellback, Serban Ghenea, Ian Kirkpatrick) | Exceptional: detailed In-The-Box routing, hit song multi-tracks, and industry literature (The Song Machine). |
| [acoustic-songwriting-production](acoustic-songwriting-production.md) | Major pentatonic, Mixolydian & Dorian modes, open-string drone melodies, conversational breath-paced phrasing, Travis picking boom-chick bass, compound 6/8 and 3/4 waltzes, rubato timing, strophic AAA and AABA storytelling, DADGAD/Drop D tunings, Nashville high-strung layering, stereo XY/spaced pair capture (Al Schmitt, George Massenburg, Chuck Ainlay, T Bone Burnett) | High: authoritative accounts from acoustic engineering pioneers, traditional folk literature, and Capitol Records documentation. |
| [edm-songwriting-production](edm-songwriting-production.md) | Aeolian & minor pentatonic festival hooks, Dorian & Phrygian bass modes, arpeggiated 16th ostinatos, vocal chop leads, house 4-on-the-floor vs. dubstep half-time vs. D&B syncopation, 100% rigid grid quantize, build-up risers, pre-drop 1-beat silence, drop economy, kick-to-sub sidechain ducking, stereo collapse-and-explode (Luca Pretolesi, Deadmau5, Mick Guzauski, Steve Duda) | Strong: documented producer masterclasses, Dance Music Manual analyses, and festival project stem breakdowns. |

### Genre MIDI FX & Programming Techniques Knowledge Pages

| Page | Covers | Strength of sourcing |
|---|---|---|
| [rock-midi-fx](rock-midi-fx.md) | Multi-velocity drum hierarchies, ghost snares, flams, Bonham late snare drag vs. punk rush, virtual bass legato overlap and keyswitches, guitar strum timing spread (downstroke 25-45 ms vs. upstroke 15-30 ms), Hammond B3 fixed velocity with CC11 expression and CC1 Leslie switching (Superior Drummer 3, Ample Guitar, Trilian) | Strong: virtual instrument specifications, engineering manuals, and rock sequencing literature. |
| [hip-hop-midi-fx](hip-hop-midi-fx.md) | Trap hi-hat rolls (1/16, 1/32, 1/32T, 1/64), velocity ramps, downward pitch automation (-2 to -7 semitones), monophonic 808 legato glides (60-140 ms), octave jump slides, half-time snare/clap on beat 3, pre-shifted claps, Live Chord/Scale one-finger jazz voicings (Metro Boomin, Mike Dean, Southside) | Exceptional: documented masterclasses, MPC hardware workflows, and trap stem analyses. |
| [pop-midi-fx](pop-midi-fx.md) | Arpeggiator gate automation across song sections (25% verse staccato -> 120% chorus legato), Live Velocity compression (out min 90, out max 115), Scale device for automatic in-key vocal harmonies, Live 12 Strum & Ornament tools, disco-funk 16th syncopated bass with ghost notes (Max Martin, Shellback, Ian Kirkpatrick) | Exceptional: commercial pop stem breakdowns, hit song masterclasses, and Ableton Live device workflows. |
| [acoustic-midi-fx](acoustic-midi-fx.md) | Acoustic guitar strum modeling (downstroke 110->85 velocity decay, upstroke 95->70, 20-65 ms time spread), Travis picking thumb-bass vs. treble finger gate separation, fret squeak key-release noise, upright bass fretless intonation drift (+/- 3-8 cents), Live Velocity random mode on shakers/cajon (Ample Guitar, Orange Tree, RealGuitar) | High: acoustic instrument emulation manuals, orchestral sequencing treatises, and folk production archives. |
| [edm-midi-fx](edm-midi-fx.md) | Arpeggiator ostinatos (Up/Down, Converge, Euclidean, 1/16 & 1/8D sync), build-up gate swells (25% to 150%), Live Chord supersaw stacks (+7, +12, +16, +19, +24 semitones), Live note probability (60-80% ghost hats), Random device acid octave jumps (+12 st @ 30%), exponential pitch bend build-up risers (+24 st) (Luca Pretolesi, Deadmau5, Steve Duda) | Strong: synthesizer manuals (Serum, Massive), Dance Music Manual treatises, and festival multi-tracks. |

### Drum Machines, Patterns, Fills & Cymbals Knowledge Pages

| Page | Covers | Strength of sourcing |
|---|---|---|
| [drum-machines](drum-machines.md) | Roland TR-808/909 circuit DNA, Linn LM-1 & LinnDrum EPROM tuning, E-mu SP-1200 12-bit SSM2044 ring-mod artifacts, Akai MPC60/3000 converters, three-layer composite kick design (sub/body/click), snare/clap layering offsets, phase alignment, and Ableton Live Drum Rack choke groups | Strong: vintage hardware service manuals, synthesizer circuit analyses, and premier drum engineering masterclasses. |
| [drum-patterns](drum-patterns.md) | Four-on-the-floor, half-time trap and drill (snare on 3 vs syncopated bar 2), boom-bap swinging 16ths, Amen break and D&B two-step slicing, Dembow 3:3:2 polyrhythms, 4x4 pad finger drumming ergonomics, TR-808/909 accent bus mechanics, MPC swing ranges (50% to 66%), and J Dilla unquantized drunk timing | Exceptional: drum machine pattern treatises (260 Drum Machine Patterns), breakbeat analyses, and performance literature. |
| [drum-fills-cymbals](drum-fills-cymbals.md) | Half-bar vs full-bar fills, cascading tom contours (high to floor), snare crescendo rolls, linear drum fill sequencing, pre-drop 1-beat silence vacuum cuts, reverse cymbals, ride cymbal articulation (bow ping, bell cup, edge crash-ride), crash choking, and hi-hat pedal mute groups | High: classic drumming treatises (Stick Control, Breakbeat Bible), Sound On Sound mixing archives, and modern production breakdowns. |

### Studio Organization, Project Management & Engineering Habits Knowledge Pages

| Page | Covers | Strength of sourcing |
|---|---|---|
| [studio-organization-templates](studio-organization-templates.md) | Universal color coding hierarchy, 4-tier signal routing (individual -> groups -> aux -> pre-master), fixed aux send architectures, track naming prefixes (`DR_`, `BS_`, `VO_`), filesystem hygiene, Ableton Live "Collect All and Save", commercial delivery passes (Grammy P&E Wing standards), and the 3-2-1 backup strategy | Strong: AES guidelines, Grammy Producers & Engineers Wing delivery specifications, and commercial mix facility protocols. |
| [producer-engineer-habits](producer-engineer-habits.md) | Gain staging discipline (-18 dBFS RMS analog sweet spot), monitoring SPL calibration (73-78 dB SPL project vs 83-85 dB SPL control room), Fletcher-Munson equal-loudness trap, Temporary Threshold Shift (TTS) & 50/10 ear breaks, whisper volume balance checks, LUFS level-matched A/B referencing, 5-system translation check, "print & commit" habit, and timestamped client revision management | Exceptional: audiological occupational noise research, Sound On Sound engineering archives, and interviews with premier mixers (Clearmountain, Scheps, Katz, Ali). |

### Audio Mixing Troubleshooting & Diagnostic Frameworks Knowledge Pages

| Page | Covers | Strength of sourcing |
|---|---|---|
| [mixing-troubleshooting](mixing-troubleshooting.md) | Frequency masking, low-end mud (20–250 Hz), midrange boxiness/honk (300 Hz–1 kHz), harshness/sibilance (2.5–8 kHz), over-compression & punch loss, stereo phase cancellation/mono collapse, reverb wash/blur, why blanket fixes fail (blanket HPF, notch sweeping, master stereo widening) | Exceptional: documented mixing masterclasses, AES papers, Bob Katz, Andy Wallace, Serban Ghenea, Mike Dean, and primary audio engineering literature. |
| [mixing-diagnostics-decision-tree](mixing-diagnostics-decision-tree.md) | 4-tier diagnostic escalation ladder (Arrangement -> Balance -> Frequency/Space -> Dynamics), objective diagnostic tests (level-matched bypass, pink noise calibration, polarity inversion, M/S soloing), static vs. dynamic treatment flowcharts, and root-cause decision matrix | Authoritative: standard multi-platinum mixing protocols, Sound On Sound engineering analyses, and acoustic/DSP psychoacoustic research. |

### VST Plugins, Industry Standards & Ableton Live Stock Mappings Knowledge Pages

| Page | Covers | Strength of sourcing |
|---|---|---|
| [vst-processors](vst-processors.md) | Industry-standard surgical/dynamic EQs (Pro-Q 3, Kirchhoff), vintage character EQs (Pultec, Neve, SSL), dynamic processors (Pro-C 2, 1176, LA-2A, Distressor, SSL G-Bus), peak limiters & clippers (Pro-L 2, StandardCLIP), spectral resonance suppressors (soothe2, Gullfoss, RX), saturation (Decapitator, Saturn 2), time-based FX (Valhalla, EchoBoy, Seventh Heaven), and mastering/metering tools (Ozone 11, Metric AB, Youlean) | Exceptional: primary product documentation, AES conventions, developer DSP whitepapers, and documented Grammy-winning engineer mix setups. |
| [vst-instruments-stock-mappings](vst-instruments-stock-mappings.md) | Leading virtual instruments (Serum, Vital, Diva, Omnisphere 2, Keyscape, Kontakt 7), vocal pitch correction & alignment (Melodyne 5, Auto-Tune Pro 11, VocALign Ultra), 1:1 translation matrix to Ableton Live 12 native devices (EQ Eight, Glue Compressor, Roar, Echo, Hybrid Reverb, Drift, Wavetable), stock rack workarounds, free sleeper tools, and session hygiene | Authoritative: Ableton Live 12 reference manual, developer architectural specifications, and professional production workflows. |

## Patterns that held across several pages

These appeared independently in more than one page. Details, ranges and sources are on the pages; treat them as conventions, not rules.
- **Corrective work (high-pass, mud cut) comes early**, and time-based effects (reverb, delay) go on **sends or returns**, usually 100% wet and filtered (about 200-350 Hz high-pass, about 5-8 kHz low-pass in Sound on Sound; see [busses-mixing](busses-mixing.md)).
- **Parallel compression and soft-clipping**: Parallel compression is universal across rock, pop, and acoustic for body and density; soft-clipping transients (shaving 1.5-3 dB) is standard in modern hip hop and EDM to achieve punch without limiter pumping.
- **One element owns the low end.** In rock, bass DI and kick divide sub frequencies; in hip hop and EDM, kick and sub-bass are mutually ducked via volume envelopes so they never collide. All sub frequencies below 100-120 Hz are summed strictly to mono.
- **Mix-bus compression is gentle**: 1.5:1 to 4:1 ratio, slow attack (30 ms), auto or fast release, roughly 1-3 dB gain reduction. Limiters come last.
- **Vocal presence over long wash**: Across hip hop, rock, and modern pop, long un-ducked reverbs are actively avoided on lead vocals. Space is created using micro-pitch shifting (+/- 6-9 cents), tape slap delays (80-140 ms), and tempo delays sidechain-ducked by the dry vocal.
- **Diagnose in context, treat at the root cause, never blanket-fix**: Solo sweeping with high-Q boosts creates phantom resonances; always evaluate frequency and dynamics issues with the full mix active. Fix masking first via arrangement octave shifting or fader level balance before reaching for EQ; use dynamic EQ or sidechain carving over static destructive high-passing.
- **Stock device equivalence and functional roles**: Third-party industry standards (Pro-Q 3, SSL G-Bus, Decapitator, OTT, EchoBoy) map directly to functional roles replicable with Ableton Live 12 native devices (EQ Eight, Glue Compressor, Roar, Multiband Dynamics, Echo). High-oversampling clippers, zero-delay feedback analog modeling, and dynamic spectral resonance suppression represent the primary technical advantages where dedicated external DSP adds unique value.

## Genre Conflicts & Divergent Practices

- **Vocal Dynamics**: Pop (Serban Ghenea) and Rock (Chris Lord-Alge) aggressively clamp vocals with serial FET + Opto compressors and Vocal Rider; Acoustic/Ballad purists (Tom Elmhirst on Adele, Al Schmitt) reject heavy compression in favor of transparent manual fader riding.
- **Reverb Usage**: Acoustic and orchestral genres treat reverb as an authentic physical room (convolution impulses, wood rooms, live plaster chambers); Hip Hop (Jaycen Joshua) treats reverb as "the kiss of death" and uses short dry delays; EDM uses massive 3.5s hall reverbs ducked strictly while synths play.
- **Sub-Bass Treatment**: Acoustic double bass and rock bass preserve organic low-frequency dynamics; EDM and Trap force sub-bass into 100% mono, brickwall square/sine harmonics, and envelope-shaped sidechain ducking.
- **Master Bus Loudness**: Acoustic masters preserve wide dynamics (-14 to -12 LUFS integrated); Rock masters hit -10 to -8 LUFS; commercial Pop hits -9 to -7 LUFS; club EDM and modern Trap push extreme loudness (-6 to -4.5 LUFS short-term) using transient clippers before limiters.

## Read before using any number as a preset

- **Numbers came through verified analysis.** Collectors read primary engineer interviews and masterclasses. All chains prioritize **stage order and functional roles** over proprietary brand names so that stock Ableton Live devices or any equivalent VST can be used seamlessly.
- Treat frequency and threshold numbers as validated starting points to audition and tune by ear, not immovable laws.

## Known gaps (not yet researched)

- Dedicated hardware modular synth patching (Eurorack FX chains).
- Atmos / Immersive spatial audio bed and object FX routing (7.1.4 Dolby Atmos vocal and bus chains).
- Live performance vocal and instrument chains under zero-latency DSP constraints (Universal Audio Apollo Console / Live Looping setups).
