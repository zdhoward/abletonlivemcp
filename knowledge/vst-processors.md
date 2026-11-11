# Best-in-Class & Industry Standard Audio Processing Plugins (knowledge page)

Curated guide to premier third-party VST/AU audio processing plugins across mixing, sound design, and mastering. Focuses on architectural strengths, exact technical capabilities, circuit topologies, and operational workflows.

## 1. Industry-Standard Equalizers: Surgical, Dynamic, and Analog Topologies

### FabFilter Pro-Q 3 (Parametric & Dynamic Standard)
- **Phase Modes**:
  - **Zero Latency**: **FACT** Introduces zero samples of latency; best for low-latency recording and CPU-constrained tracking sessions.
  - **Natural Phase**: **FACT** Faithfully reproduces the magnitude and phase response of analog gear without cramping or phase warping near the Nyquist frequency, avoiding pre-ringing while maintaining natural phase coherence.
  - **Linear Phase**: **FACT** Delivers 100% linear phase response without phase shift at any frequency. Tradeoff: Introduces fixed algorithmic latency and potential low-frequency pre-ringing artifacts on sharp transients (e.g., kick drums).
- **Dynamic EQ Processing**: **CONVENTION** Any band (bell, shelf, notch) can be turned into a dynamic band with continuous threshold detection or external sidechain routing. Common practice: ducking guitar or synth mud bands (250–500 Hz) only when the lead vocal sings.
- **Spectrum Masking & Collision Detection**: **FACT** Highlights real-time frequency collisions between multiple Pro-Q 3 instances across different tracks in red, locating masking instantly in the session.
- **Filter Slopes**: **FACT** Supports slopes from 6 dB/octave up to 96 dB/octave, plus Brickwall low-pass and high-pass filtering.

### Three-Body Technology Kirchhoff-EQ
- **High-Precision Architecture**: **FACT** Uses 64-bit internal processing and 117-bit double-doubled precision filter math to eliminate digital rounding noise.
- **Vintage Topologies**: **FACT** Includes 32 modeled vintage curves (Pultec, Neve, SSL, API) selectable per band with independent envelope attack and release controls.

### Analog-Modeled Character Equalizers
- **Pultec EQP-1A (Universal Audio, Waves, Softube, Tube-Tech PE 1C)**:
  - **The Pultec Low-End Trick**: **CONVENTION** Setting both the Boost and Attenuate knobs to nominal amounts at 30 Hz or 60 Hz simultaneously. Because the filter curves have slightly offset center frequencies and bandwidths, this creates a tight sub-bass boost combined with a musical dip in the 200–350 Hz mud region.
  - **High-End Sheen**: **CONVENTION** Broad inductor boost between 8 kHz and 16 kHz introduces smooth high-frequency air without sounding brittle or harsh.
- **Neve 1073 (Universal Audio, Waves Scheps 73, Arturia 1973)**:
  - **Class-A Inductor Sound**: **FACT** Transformer-coupled discrete circuitry that adds rich second- and third-order harmonics as input gain is driven.
  - **Key Bands**: **CONVENTION** Fixed 12 kHz high-shelf for "Neve air"; switchable mid-band (360 Hz, 700 Hz, 1.6 kHz, 3.2 kHz, 4.8 kHz, 7.2 kHz) adds punch and body to drums, vocals, and electric guitars.
- **SSL 4000 Channel Strip EQs**:
  - **E-Series "Black Knob" (0242)**: **FACT** Steeper 18 dB/oct HPF and tighter Q for aggressive punch, bite, and attack on rock snares, kicks, and distorted guitars.
  - **G-Series (0292)**: **FACT** Proportional-Q design where bandwidth narrows as boost or cut depth increases; ideal for gentle bus balancing and vocal shaping.

---

## 2. Dynamic Processors: VCA, FET, Opto, and Bus Standards

### FabFilter Pro-C 2 (Versatile Digital Workhorse)
- **8 Dedicated Compression Styles**: **FACT**
  1. *Clean*: Low-distortion feed-forward VCA mode.
  2. *Classic*: Vintage feedback VCA style with musical warmth.
  3. *Opto*: Slow, non-linear multi-stage optical release curve.
  4. *Vocal*: Level-matched auto-gain compression tailored for vocal control.
  5. *Mastering*: Transparent bus compression designed for minimal harmonic distortion.
  6. *Bus*: Snappy glue compression for drum and instrument busses.
  7. *Punch*: Emphasizes initial transient attacks.
  8. *Pumping*: Aggressive electronic/dance pumping envelope.
- **Analytical Controls**: **FACT** Visual knee display (0 to 40 dB), sidechain tilt/filter EQ, lookahead up to 20 ms, and up to 4x oversampling.

### The Vintage Compression Archetypes
1. **1176 Classic Limiting Amplifier (FET)**:
   - **Ultra-Fast Transients**: **FACT** Attack times range from 20 to 800 microseconds; release times range from 50 to 1100 milliseconds. Note: On hardware and authentic emulations, clockwise (position 7) is fastest; counter-clockwise (position 1) is slowest.
   - **All-Buttons-In ("British Mode")**: **CONVENTION** Depressing ratios 4, 8, 12, and 20 simultaneously distorts the FET bias, causing severe non-linear saturation, unique attack/release lags, and aggressive explosive character on drum room mics and parallel vocal crush busses.
2. **Teletronix LA-2A (Optical / Tube)**:
   - **Two-Stage Program-Dependent Release**: **FACT** The T4 optical attenuator cell releases the first 50% of gain reduction in ~60 ms, while the remaining 50% releases over 1 to 5 seconds depending on prior signal history.
   - **Vocal & Bass Smoothing**: **CONVENTION** Universal two-knob standard (Gain and Peak Reduction) for transparent vocal leveling and round upright/electric bass body.
3. **Empirical Labs Distressor EL8 (Digitally Controlled VCA)**:
   - **Nonlinear Coloration**: **FACT** Features switchable harmonic distortion circuits: *Dist 2* (tube-style 2nd harmonics) and *Dist 3* (tape-style 3rd harmonics), detector HPF (170 Hz), and detector band emphasis (6 kHz).
   - **Ratios**: **FACT** Ratios from 1:1 through 20:1 up to "Nuke" (brickwall limiting).
4. **SSL G-Master Bus Compressor (VCA Bus Glue)**:
   - **Industry Standard Mix Bus Setting**: **CONVENTION** Attack: 30 ms (preserves drum transients), Release: Auto (adapts dynamically to track tempo and transients), Ratio: 2:1 or 4:1, Gain Reduction: 1 to 3 dB.

---

## 3. Mastering Peak Limiters & Specialized Clippers

### FabFilter Pro-L 2 (Mastering Limiter Standard)
- **Limiting Algorithms**: **FACT** 8 styles (Transparent, Allround, Dynamic, Modern, Hard, Aggressive, Bus, Safe) offering distinct transient preservation and release curves.
- **Compliance & Metering**: **FACT** Features true peak limiting (inter-sample peak prevention), up to 32x linear-phase oversampling, and integrated EBU R128, ITU-R BS.1770-4, and ATSC A/85 loudness meters.

### Dedicated Mastering Clippers (StandardCLIP, KClip 3)
- **Function**: **FACT** Applied immediately before the final peak limiter to truncate micro-transient spikes by 1.5 to 3 dB via zero-attack soft clipping.
- **Workflow Benefit**: **CONVENTION** Shaving off transient peaks with a high-oversampling clipper prevents the downstream limiter from being forced into heavy pumping, yielding louder and punchier masters with higher dynamic integrity.

---

## 4. Resonance Suppression, Spectral Shaping & Audio Restoration

### oeksound soothe2 (Dynamic Spectral Resonance Suppressor)
- **Operating Mechanism**: **FACT** Analyzes frequency spectrum in real time and automatically applies narrow dynamic notch cuts to offending resonant spikes.
- **Core Parameters**:
  - *Depth*: Overall reduction amount.
  - *Sharpness*: Selectivity of cut notches (high values target narrow whistling peaks; low values smooth broadband harshness).
  - *Selectivity*: Discriminates between resonant spikes and broadband musical tone.
  - *Delta Audition*: **CONVENTION** Crucial monitoring mode that isolates the exact audio being removed to verify musical information is not being hollowed out.
  - *Sidechain Carving*: Duck resonances in guitars, synths, or cymbals triggered by the lead vocal.

### Soundtheory Gullfoss (Auditory Perception EQ)
- **Computational Auditory Model**: **FACT** Changes frequency curves hundreds of times per second based on human hearing perception models.
- **Parameters**: **FACT** *Recover* (boosts frequencies masked by louder elements), *Tame* (attenuates over-dominant masking frequencies), *Bias* (shifts balance between Recover and Tame).

### iZotope RX Advanced (Audio Restoration Standard)
- **Spectral Repair**: **FACT** Visual spectrogram audio painting to remove coughs, chair squeaks, and extraneous noises via frequency interpolation.
- **De-Click & Mouth De-Click**: **FACT** Eliminates digital clicks, vinyl thumps, and vocal saliva clicks without dulling high-end transients.
- **Voice / Spectral De-Noise**: **FACT** Learns noise profiles to strip room hum, HVAC noise, and tape hiss cleanly.

---

## 5. Saturation, Tape Emulation, and Harmonic Exciters

### Soundtoys Decapitator (Analog Saturation)
- **5 Circuit Models**: **FACT**
  - *A*: Ampex 350 tape drive preamp (smooth tube saturation).
  - *E*: Chandler / EMI TG console channel (punchy transistor drive with bite).
  - *N*: Neve 1057 Germanium transistor input (rich low-end weight).
  - *T*: Thermionic Culture Vulture Triode setting (even-order harmonics).
  - *P*: Thermionic Culture Vulture Pentode setting (odd-order biting harmonics).
- **Punish Mode**: **FACT** Injects a fixed +20 dB analog gain boost for aggressive distortion and parallel drum crushing.

### FabFilter Saturn 2 (Multiband Saturation Workstation)
- **Multiband Routing**: **FACT** Up to 6 independent frequency bands with 28 saturation styles (tubes, tapes, vintage guitar amps, transformers, bit-crushing).
- **Modulation**: **FACT** 50-slot modulation matrix with LFOs, envelope followers, and MIDI velocity tracking to create dynamic, tempo-synced distortion sweeps.

### Tape Machine Emulations (Slate VTM, u-he Satin, UAD Ampex/Studer)
- **15 ips vs 30 ips**: **CONVENTION** 15 inches per second (ips) boosts head-bump bass resonance around 50–100 Hz, adding fatness to drums and bass; 30 ips provides a flatter frequency response and extended high-end fidelity.

---

## 6. Time-Based Effects: Algorithmic Reverbs, Hybrid Convolution, and Vintage Delays

### ValhallaDSP (Sean Costello)
- **Valhalla VintageVerb**: **CONVENTION** The modern standard for algorithmic digital reverb. Modes: *1970s* (10 kHz low-pass roll-off, vintage hardware sample rate), *1980s* (full bandwidth with vintage algorithmic character), *NOW* (pristine clean 24/96 modern response). Concert Hall and Plate algorithms are industry standards on vocals, snares, and synths.
- **Valhalla Delay**: **FACT** Models classic delay technologies: Tape, Bucket Brigade (BBD), Digital, Hi-Fi, Pitch, and Ghost (frequency shifted).
- **Valhalla Supermassive**: **OPINION** Considered the premier free sound-design and ambient cloud reverb/delay tool.

### Soundtoys Time-Based Plugins
- **EchoBoy**: **CONVENTION** The definitive multi-style delay plugin. Features over 30 hardware delay styles (Space Echo, Echoplex, Memory Man, Tel-Ray) with customizable groove, swing, and input saturation drive.
- **MicroShift**: **CONVENTION** Stereo pitch-widening tool modeling the Eventide H910/H949 and AMS DMX 15-80S. Adds +/- 6 to 9 cents micro-pitch detuning and 10–30 ms delays to thicken lead vocals and guitars without center mono phase cancellation.

### LiquidSonics Seventh Heaven (Bricasti M7 Emulation)
- **Fusion-IR Technology**: **FACT** Combines multi-sampled impulse responses with algorithmic modulation, faithfully capturing the authentic depth, early reflections, and late decay of the Bricasti M7 hardware reverb.

---

## 7. Mastering Suites, Metering & Referencing Tools

### iZotope Ozone 11 Advanced
- **Maximizer**: **FACT** Includes IRC (Intelligent Release Control) I through IV algorithms with integrated soft clipping.
- **Stabilizer & Clarity**: **FACT** Dynamic spectral shaping modules that smooth harsh high-mid build-up and increase clarity in muddy mixes.
- **Master Rebalance**: **FACT** Neural-network stem separation allowing independent level adjustments of Vocals, Bass, or Drums by up to +/- 8 dB directly on a stereo master file.

### Metering & Referencing Standards
- **Audiowerkstat Metric AB**: **CONVENTION** Industry reference plugin supporting up to 16 reference tracks, automated loudness matching (LUFS/RMS), 5-band frequency soloing, and stereo correlation monitoring to eliminate volume bias.
- **Youlean Loudness Meter 2**: **FACT** Compliant with ITU-R BS.1770-4 and EBU R128; provides presets for streaming delivery (Spotify -14 LUFS, Apple Music -16 LUFS, YouTube -14 LUFS).
- **Voxengo SPAN**: **CONVENTION** Free FFT spectrum analyzer. Standard mixing convention: set display slope to 4.5 dB/octave to evaluate tonal tilt across modern balanced mixes.

---

## 8. Functional Plugin Selection Matrix

| Mixing Task / Need | Primary Industry Standard | Alternative / Specialist VST | Free / Budget Champion |
|---|---|---|---|
| **Surgical & Dynamic EQ** | FabFilter Pro-Q 3 | Three-Body Kirchhoff-EQ | Tokyo Dawn TDR Nova |
| **Vintage Character EQ** | Universal Audio Pultec EQP-1A / Neve 1073 | Waves Scheps 73 / Softube Tube-Tech | Tokyo Dawn TDR SlickEQ |
| **All-Round Channel Compression** | FabFilter Pro-C 2 | Universal Audio 1176 / LA-2A | Klanghelm DC1A |
| **Mix Bus Glue Compression** | SSL Native Bus Compressor | Cytomic The Glue / Slate FG-Grey | Tokyo Dawn TDR Kotelnikov |
| **Resonance & Harshness Taming** | oeksound soothe2 | Soundtheory Gullfoss / Baby Audio Smooth Operator | Tokyo Dawn TDR Nova (Dynamic mode) |
| **Saturation & Analog Drive** | Soundtoys Decapitator | FabFilter Saturn 2 / Vertigo VSM-3 | Klevgrand FreeAMP |
| **Time-Based Algorithmic Reverb** | Valhalla VintageVerb | LiquidSonics Seventh Heaven | Valhalla Supermassive |
| **Character & Vintage Delay** | Soundtoys EchoBoy | Valhalla Delay / Soundtoys PrimalTap | TAL-Dub-2 / Baby Audio Comeback Kid |
| **Stereo Widening & Thickening** | Soundtoys MicroShift | Eventide H910 / Waves Doubler | Polyverse Wider |
| **Final Peak Limiting & Loudness** | FabFilter Pro-L 2 | Sonnox Oxford Limiter / iZotope Maximizer | VladG Limiter No6 / Kilohearts Limiter |
