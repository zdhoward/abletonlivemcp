# Drum Machines, Hardware Architectures, and Sound Selection: raw evidence (collector track)

Collected 2026-11-10. Sourced from hardware service manuals, synthesizer architecture treatises (Roland, Linn, E-mu, Akai), Sound On Sound historical retrospectives, and engineer masterclasses.
Evidence labels:
- **FACT** = Documented for a specific hardware circuit, EPROM format, or verified engineer session.
- **CONVENTION** = Universally accepted standard across electronic drum programming.
- **OPINION** = Individual producer philosophy or personal sound design aesthetic.

---

## 1. Iconic Hardware Drum Machines and Circuit DNA

### 1a. Roland TR-808 (1980) – The Analog Transistor Masterpiece (FACT)
- **Circuit Architecture**: 100% discrete analog circuitry. No samples or microprocessors for audio generation. Uses bridged T-network resonant filters and transistor noise generators.
- **The Bass Drum (808 Kick)**: Bridged T-network oscillator generating a pure damped sine wave (fundamental frequency range: 45 - 65 Hz). Decay knob modifies the resistance in the feedback loop, extending the tail from a tight 200 ms thud to a 2 - 4 second booming sub-bass drone.
- **The Snare Drum**: Dual bridged T-network filters tuned to 180 Hz and 330 Hz (body) mixed with a filtered white noise generator (snappy sizzle).
- **The Hi-Hats & Cymbals**: Six Schmitt-trigger square wave oscillators running at non-harmonically related frequencies (creating dissonant pseudo-metallic noise) passed through a bandpass filter (centered ~10 kHz) and gated by a transistor VCA.
- **The Handclap**: Four rapid noise bursts spaced 10 - 15 ms apart (simulating multiple humans clapping at slightly different times) followed by a longer reverberant noise decay.
- **The Accent Circuit**: TR-808 features an Accent bus that boosts both the trigger voltage and the filter resonance on accented steps, giving accented hits a brighter, punchier timbre beyond mere volume boost.

### 1b. Roland TR-909 (1983) – The Hybrid House/Techno Engine (FACT)
- **Hybrid Architecture**: Analog sound generators for Kick, Snare, Toms, and Clap; 6-bit uncompressed digital PCM samples stored on ROM chips for Crash, Ride, and Hi-Hats (clocked at 32 kHz).
- **The 909 Kick**: Tuned triangle-to-sine wave oscillator driven by a pitch envelope generator. Tune knob changes pitch; Attack knob adds a high-frequency click transient; Decay controls low-end tail length. Cuts through dense club sound systems.
- **The 909 Snare**: Dual analog tone oscillators with adjustable Tune and Tone (noise amount), delivering a snappy, aggressive crack.
- **909 Hi-Hats**: 6-bit PCM samples with exclusive choking between open and closed hats. Distinctive gritty high-end presence that defines Chicago House and Detroit Techno.

### 1c. Linn LM-1 & LinnDrum (1980 / 1982) – The Digital EPROM Revolution (FACT)
- **Architecture**: 8-bit / 12-bit companded PCM samples recorded from acoustic drums, stored on interchangeable EPROM chips. Clocked at ~28 kHz (LM-1) and ~35 kHz (LinnDrum).
- **Individual Voice Tuning (LM-1)**: Every voice on the LM-1 had an individual hardware pitch knob on the back panel, altering the sample playback clock speed. Pitching down the Linn cross-stick/rim and cowbell created Prince's signature 1980s Minneapolis sound ("When Doves Cry", "1999").
- **Linn Swing Algorithm**: Roger Linn's pioneering 16th-note swing engine (54% to 70%), shifting every second 16th note late in the clock cycle.

### 1d. E-mu SP-12 & SP-1200 (1985 / 1987) – The Golden Age Boom-Bap Sampler (FACT)
- **Architecture**: 12-bit linear sampling at 26.04 kHz. 10 seconds total sampling time (SP-1200: 4 banks of 2.5 seconds).
- **Analog SSM2044 Filter Chips**: Outputs 1 and 2 feature hardwired SSM2044 dynamic low-pass filters; outputs 3-8 feature fixed low-pass reconstruction filters.
- **Pitch Transposition Artifacts (The +8 Pitch Trick)**: Due to lack of anti-aliasing interpolation, sampling vinyl records at 45 RPM (+8% pitch) and then pitching them down in the SP-1200 to restore original speed generated gritty, warm ring-modulation distortion and aliasing sidebands that defined 90s hip hop (DJ Premier, Pete Rock, RZA).

### 1e. Akai MPC60 & MPC3000 (1988 / 1994) (FACT)
- **MPC60**: 12-bit non-linear at 40 kHz, designed by Roger Linn. Signature heavy, punchy converter sound and unshakeable timing clock.
- **MPC3000**: 16-bit linear at 44.1 kHz with resonant low-pass filters. Masterpiece of hip hop sequencing (J Dilla, Dr. Dre).

---

## 2. Sound Selection and Sample Layering Methodology

### 2a. The Anatomy of a Modern Kick Drum (CONVENTION / FACT)
- **Three-Layer Composite Kick Architecture**:
  1. *Sub Layer (30 - 65 Hz)*: Pure sine wave or pitched 808 tail carrying clean sub-bass energy.
  2. *Body / Chest Punch (90 - 180 Hz)*: Acoustic kick mic or punchy 909 kick providing the low-mid "thud" felt in the chest.
  3. *Click / Top Transient (1.5 - 5 kHz)*: Beater click, vinyl snap, or typewriter/wood click ensuring the kick cuts through small mobile phone and laptop speakers.
- **Phase Alignment**: When layering kicks, align the initial zero-crossing transients in the DAW sample editor. Inverted polarity or a 2 ms offset will cause severe comb filtering and destructive low-end phase cancellation.
- **Tuning to the Song Key**: Tuning the kick's fundamental frequency to either the root (tonic) or fifth of the track's key prevents low-end harmonic dissonance.

### 2b. Snare and Clap Curation and Stacking
- **The Layered Pop/Hip-Hop Snare**:
  - *Core Body (180 - 250 Hz)*: Wood acoustic snare body.
  - *Crack / Snap (2 - 4 kHz)*: 808/909 snare or rimshot.
  - *Stereo Width / Tail*: 808 clap or layered handclap spread slightly in the stereo field with 10-15 ms pre-delay.
- **Offsetting Stacked Layers**: Nudging secondary clap/snare layers 5 to 15 milliseconds *early* or *late* creates perceived acoustic width and physical impact without phase cancellation.

### 2c. Hi-Hat and Cymbal Selection
- **Role Alignment**:
  - Main Driving Hat: Crisp, clean, mid-focused (e.g. 909 or tight 14" acoustic hat).
  - Syncopated Offbeat / Ghost Hats: Darker, pitched down, or lo-fi sampled hats (e.g. 808 or vinyl breakbeat hats).
  - Open Hat Sizzle: Metallic 909 open hat on the upbeat to drive four-on-the-floor momentum.
