# Raw Collector Research: Popular & Best-in-Class VST Processors
**Date**: 2026-11-10
**Topic**: Industry-standard and best-in-class VST audio processors for mixing and mastering
**Coverage**: Parametric/Dynamic EQs, Dynamics (Compressors, Limiters, Clippers), Spectral Resonance, Saturation/Color, Spatial/Time-based, Mastering & Metering suites

---

## 1. Equalizers: Surgical, Dynamic, and Analog-Modeled

### FabFilter Pro-Q 3
- **Classification**: Digital Parametric & Dynamic Equalizer (Industry Reference Standard).
- **Architecture**:
  - Up to 24 independent EQ bands.
  - Phase Modes:
    - **Zero Latency**: Minimum phase with 0 samples latency, ideal for tracking and CPU conservation.
    - **Natural Phase**: Matches analog magnitude and phase response accurately without phase warping near Nyquist, avoiding pre-ring while preserving phase linearity where it counts.
    - **Linear Phase**: Perfectly maintains phase coherence across all frequencies at the cost of fixed latency and potential low-frequency pre-ringing; selectable resolutions (Low, Medium, High, Very High, Maximum).
  - Dynamic EQ Mode: Any band (bell or shelf) can be switched to dynamic operation with continuous upward/downward processing, internal threshold or external sidechain triggering, and auto-gain calculation.
  - Filter Slopes: 6 dB/oct up to 96 dB/oct, plus Brickwall HPF/LPF slopes.
  - Stereo Modes: Left/Right, Mid/Side, or Stereo per band.
  - Analytical Features: Spectrum Grab, Multi-track spectrum collision detection (visualizing frequency masking between multiple Pro-Q 3 instances across tracks), EQ Match (curves matched against a reference audio file or sidechain).
- **Authority/Use Case**: Found across top studios worldwide (Serban Ghenea, Dave Pensado, Mick Guzauski, Luca Pretolesi). Used as the default surgical utility and sidechain dynamic unmasker.

### Three-Body Technology Kirchhoff-EQ
- **Classification**: High-Precision Parametric/Dynamic EQ.
- **Key Technical Distinctions**:
  - 64-bit internal processing with 117-bit double-doubled precision filters to eliminate digital rounding noise and cramping near Nyquist.
  - 32 vintage analog EQ curve topologies modeled accurately (Pultec, Neve, SSL, API curves selectable per band).
  - Dynamic EQ with customizable attack and release envelopes, plus continuous proportional-Q behaviors.

### Analog-Modeled Vintage EQ Standards
- **Pultec EQP-1A (Universal Audio, Waves, Softube, Tube-Tech PE 1C)**:
  - *Circuit*: Passive tube/transformer equalizer.
  - *The "Pultec Low-End Trick"*: Simultaneous Boost and Attenuate at the same nominal bass frequency (typically 30 Hz or 60 Hz). Because the boost and cut curves have slightly different centers and Q factors, boosting and cutting together creates a solid sub boost coupled with a dip in the muddy 200–300 Hz region, firming kick drums and bass guitars without mud.
  - *High Shelf / Boost*: 3 kHz to 16 kHz broadband inductor boost with broad bandwidth adds smooth silky top-end without harsh sibilance.
- **Neve 1073 (Universal Audio, Waves Scheps 73, Arturia 1973)**:
  - *Circuit*: Discrete Class-A transistor preamp and inductor equalizer.
  - *Sound Characteristics*: Rich transformer harmonics, gentle high-shelf fixed at 12 kHz ("Neve air"), selectable mid-band frequencies (360 Hz, 700 Hz, 1.6 kHz, 3.2 kHz, 4.8 kHz, 7.2 kHz) with musical inductor saturation when pushed.
- **SSL 4000 Series Channel Strip EQ (SSL Native, Universal Audio, Waves, Brainworx bx_console SSL)**:
  - *Topologies*:
    - **E-Series "Black Knob" (242)**: Steeper 18 dB/oct high-pass filter, tighter Q, aggressive bite and punch, ideal for rock drums, snare snap, and rhythm guitars.
    - **E-Series "Brown Knob" (02)**: Wider musical curves, softer musical tone.
    - **G-Series (292)**: Proportional-Q design (Q narrows as boost/cut depth increases), smoother broad tone shaping for bus and vocal work.

---

## 2. Dynamic Processors: Compressors, Limiters, and Clippers

### Clean & Versatile VCA/Digital Compressors
- **FabFilter Pro-C 2**:
  - *Algorithms*: 8 distinct styles:
    1. *Clean*: Transparent, low distortion, feed-forward VCA style.
    2. *Classic*: Vintage feedback VCA style with musical warmth.
    3. *Opto*: Emulates slow, non-linear optical release curves (LA-2A style).
    4. *Vocal*: Tailored auto-gain and smooth leveling for lead vocal control.
    5. *Mastering*: Ultra-clean transparent bus compression with gentle attack/release.
    6. *Bus*: Snappy glue compression for drum and mix busses.
    7. *Punch*: Deliberately emphasizes transients for drums and percussion.
    8. *Pumping*: Aggressive dance/electronic sidechain pumping.
  - *Controls*: Lookahead (up to 20 ms), oversampling (up to 4x), sidechain EQ (tilt, bell, HPF, LPF), variable knee (0 to 40 dB), and animated level display.

### Vintage Analog Compressors (The Big Four)
1. **Universal Audio / Waves 1176 Classic Limiting Amplifier (FET)**:
   - *Attack*: 20 to 800 microseconds (extremely fast). Note that knob position 1 is slowest, position 7 is fastest.
   - *Release*: 50 to 1100 milliseconds (knob 1 slowest, knob 7 fastest).
   - *Ratios*: 4:1, 8:1 (moderate compression), 12:1, 20:1 (limiting).
   - *"All-Buttons-In" / British Mode*: Depressing all ratio buttons simultaneously alters the bias point, creating extreme non-linear FET distortion, unique lag time before release, and an explosive drum room or vocal crush sound.
2. **Teletronix LA-2A Leveling Amplifier (Optical / Tube)**:
   - *Gain Element*: T4 electro-luminescent optical attenuator cell paired with vacuum tubes.
   - *Operation*: Program-dependent 2-stage release. The initial 50% release occurs in ~60 ms; the remaining 50% releases gradually over 1 to 5 seconds depending on signal history.
   - *Controls*: Simple two-knob workflow: Gain (output makeup) and Peak Reduction. Ideal for smooth vocal tracking, acoustic bass, and string leveling.
3. **Empirical Labs Distressor EL8 / EL8-X (VCA)**:
   - *Circuit*: Digitally controlled analog VCA compressor designed by Dave Derr.
   - *Features*:
     - Ratios from 1:1 up to "Nuke" (brickwall limiter curve).
     - Distortion Modes: *Dist 2* (emphasizes 2nd harmonic tube warmth) and *Dist 3* (emphasizes 3rd harmonic tape-style saturation and transient rounding).
     - Sidechain detector HPF (at 170 Hz) and Band Emphasis (at 6 kHz) to prevent bass pumping and tame vocal sibilance.
4. **SSL G-Master Bus Compressor (VCA Quad Bus)**:
   - *Industry Standard Glue*: Attack 30 ms (lets initial transient through), Auto Release (adapts to song tempo and dynamics), 2:1 or 4:1 ratio, pulling 1 to 3 dB of gain reduction.

### Peak Limiters & Mastering Clippers
- **FabFilter Pro-L 2**:
  - *Algorithms*: Transparent, Allround, Dynamic, Modern, Hard, Aggressive, Bus, Safe.
  - *Mastering Features*: True Peak detection, up to 32x linear-phase oversampling, comprehensive EBU R128, ITU-R BS.1770-4, and ATSC A/85 loudness metering, DC offset filtering, and surround/Atmos channel linking.
- **Specialized Hard/Soft Clippers (StandardCLIP by SIR Audio Tools, Kazrog KClip 3)**:
  - Used before final peak limiters to shave off 1.5–3 dB of micro-transient spikes (snare hits, kick attacks) via zero-attack soft clipping. Prevents the final limiter from pumping and generates clean loudness without squashing program dynamics.

---

## 3. Spectral Processing & Resonance Suppression

### oeksound soothe2
- **Concept**: Dynamic spectral resonance suppressor.
- **Mechanism**: Continuously analyzes the incoming frequency spectrum in real time, detecting sharp resonant peaks (whistles, harshness, boxiness, mud), and applies narrow dynamic notch cuts only when and where resonances exceed the dynamic envelope.
- **Key Parameters**:
  - *Depth*: Overall intensity of resonance reduction.
  - *Sharpness*: Selectivity of cut notches (higher = surgical, lower = broadband smoothing).
  - *Selectivity*: Sensitivity to peaks vs background program material.
  - *Quality*: Latency and oversampling modes (Eco, Normal, High, Ultra).
  - *Delta Audition*: Listens exclusively to what is being removed from the signal.
  - *Sidechain Input*: Carves resonances dynamically based on an external mask (e.g. ducking vocal frequencies out of guitar/synth stems).

### Soundtheory Gullfoss
- **Concept**: Intelligent real-time equalization using computational auditory perception models.
- **Mechanism**: Models how the human ear perceives frequency masking, identifying masked frequencies (inaudible clutter) and over-dominant peaks.
- **Parameters**:
  - *Recover*: Boosts frequencies that are masked and inaudible.
  - *Tame*: Cuts frequencies that dominate and mask other elements.
  - *Bias*: Shifts balance toward Recovery or Taming.
  - *Brighten*: Enhances upper-frequency perceived clarity.

### iZotope RX Advanced (Audio Restoration Reference)
- Modules: Spectral De-noise, Voice De-noise, De-click, Mouth De-click, De-clip (reconstructs truncated analog/digital waveforms), Spectral Repair (replaces background artifacts using frequency interpolation), Dialogue Isolate, Guitar De-squeak.

---

## 4. Saturation, Tape, and Harmonic Coloration

### Soundtoys Decapitator
- **Concept**: Analog saturation and distortion modeler.
- **Models**:
  - *A*: Ampex 350 tape drive preamp (smooth tube saturation).
  - *E*: Chandler/EMI TG12345 console channel (punchy transistor drive with bite).
  - *N*: Neve 1057 discrete Germanium transistor input (warm, fat low-end roundness).
  - *T*: Thermionic Culture Vulture triode setting (even-order musical harmonics).
  - *P*: Thermionic Culture Vulture pentode setting (odd-order aggressive biting harmonics).
- **Punish Button**: Injects +20 dB of analog gain for extreme crunch and parallel drum crushing.

### FabFilter Saturn 2
- **Concept**: Multiband saturation and creative distortion workstation.
- **Capabilities**: Up to 6 split bands, 28 distinct models (gentle tube, warm tape, clean transformer, vintage guitar amps, bit-crushing, foldback distortion).
- **Modulation Engine**: 50-slot modulation matrix with XLFOs, Envelope Generators, Envelope Followers, and MIDI sources.

### Tape Emulations
- **Slate Digital VTM (Virtual Tape Machines)**: Studer A800 (16-track 2-inch tape machine for individual tracks) and Ampex ATR-102 (1/2-inch 2-track master tape for mix bus). Selectable tape speeds (15 ips for fat bass and head-bump warmth; 30 ips for flatter response and crisp treble) and tape formulations (456 vs GP9).
- **u-he Satin**: Continuous tape speed, bias, azimuth, compander, and tape delay modeling.

---

## 5. Spatial, Delay, and Reverb Processors

### ValhallaDSP (Sean Costello)
- **Valhalla VintageVerb**:
  - Recreates algorithmic digital reverbs of the 1970s and 1980s.
  - Color Modes: *1970s* (reduced bandwidth, 10 kHz roll-off, lower internal sample rate), *1980s* (full bandwidth, authentic digital noise floor), *NOW* (modern 24/96 pristine clean interpolation).
  - Top Algorithms: Concert Hall, Plate, Sanctuary, Smooth Room, Shimmer.
- **Valhalla Delay**:
  - Tape, BBD (Bucket Brigade Device), Digital, HiFi, Pitch, Ghost (frequency shifted), and Diffusion modes.
- **Valhalla Supermassive**: Free high-density delay/reverb unit based on feedback delay networks (FDNs) for ambient clouds and sound design.

### Soundtoys Time-Based Classics
- **EchoBoy**: Emulates classic hardware delays (Echoplex EP-2/EP-3 tape, Space Echo RE-201, Memory Man BBD, Tel-Ray oil can, Korg SDD-3000). Includes dedicated Groove, Feel, and Accent parameters for rhythmic push/drag.
- **MicroShift**: Algorithmic stereo pitch widening replicating Eventide H910 / H949 and AMS DMX 15-80S micro-pitch shifting (+/- 6 to 9 cents detuning with 10-30 ms cross-delays) without center mono phase cancellation.

### LiquidSonics Seventh Heaven
- **Concept**: Convolution/algorithmic hybrid emulation of the legendary Bricasti M7 hardware reverb.
- **Technology**: Fusion-IR captures multi-sampled modulated early reflections and non-linear late decay tails, eliminating the static metallic ringing of standard impulse responses.

---

## 6. Mastering & Referencing Suites

### iZotope Ozone 11 Advanced
- **Key Modules**:
  - *Maximizer*: Intelligent Release Control (IRC I to IV) and integrated soft clipping.
  - *Clarity*: Adaptive psychoacoustic spectral balance processor.
  - *Low End Focus*: Contrast processor targeting kick and sub-bass transients without altering spectral tilt.
  - *Stabilizer*: Adaptive spectral shaping EQ that prevents mix harshness and mud dynamically.
  - *Master Rebalance*: Neural network source separation allowing real-time fader adjustment of Vocals, Drums, or Bass within a bounced stereo master (+/- 8 dB).

### Metering & Referencing Tools
- **Audiowerkstat Metric AB**: A/B referencing plugin supporting up to 16 reference tracks, automated LUFS loudness matching (preventing "louder sounds better" bias), 5-band frequency crossovers, stereo correlation, and dynamic range graphs.
- **Youlean Loudness Meter 2**: Industry-standard loudness compliance meter (Integrated LUFS, Short-Term, Momentary, True Peak, Loudness Range LRA) with official presets for Spotify (-14 LUFS), Apple Music (-16 LUFS), YouTube (-14 LUFS), and Netflix/AES broadcast standards.
- **Voxengo SPAN**: Free FFT spectrum analyzer with flexible slope settings (4.5 dB/oct standard for modern balanced mixes), mid/side spectrum overlay, and RMS/peak level readouts.
