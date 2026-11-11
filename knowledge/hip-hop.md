# Hip Hop FX chains (knowledge page)

Synthesized from `research/raw/2026-11-10-hip-hop-fx-chains.md` and spot-checked against Sound On Sound engineering archives ("Inside Track", "Secrets Of The Mix Engineers") and professional urban masterclasses on 2026-11-10. Chains are organized by **ROLE and stage order** so they can resolve to Ableton Live stock devices or third-party VSTs (see `src/abletonlivemcp/adapters.py`).

Related pages: [vocals](vocals.md), [drums](drums.md), [busses-mixing](busses-mixing.md), [mastering](mastering.md), [rock](rock.md), [pop](pop.md), [acoustic](acoustic.md), [edm](edm.md).

---

## 1. Scope and how to read this page

- Covers modern commercial trap, boom-bap, melodic 808 rap, and alternative hip hop across lead vocals, ad-libs, 808 sub-bass, trap drums, hi-hat rolls, and mix bus processing.
- Evidence labels:
  - **FACT** = Documented for a named recording or engineer session.
  - **CONVENTION** = Widely documented standard engineering practice across modern urban production studios.
  - **OPINION** = Individual engineer preference, blog, or community advice.
- Generic roles map directly to standard audio devices (e.g. `pitch_corrector` = Antares Auto-Tune / Melodyne; `saturation_tape` = Decapitator / Live Saturator; `clipper_soft` = StandardCLIP / Live Saturator soft-clip mode; `compressor_opto` = Tube-Tech CL 1B / LA-2A).

---

## 2. Consensus patterns by sub-element

### 2a. Modern Rap Lead Vocal Chain (CONVENTION / FACT)

| Stage | Role | Target Settings / Typical Ranges | Reference Implementation |
|---|---|---|---|
| 1 | Pitch Correction | Antares Auto-Tune Pro: Hard trap tuning = Retune Speed 0-8 ms; natural/lyrical rap = Retune Speed 20-35 ms. | Antares Auto-Tune / Live PitchDrop/Tuner |
| 2 | Subtractive Cleanup EQ | HPF 85-95 Hz (18 dB/oct); dynamic dip 250-400 Hz (proximity resonance); high-Q notch at 2.8-3.5 kHz harshness. | FabFilter Pro-Q 3 / Live EQ Eight |
| 3 | Fast FET Peak Catching | Fast compressor (Urei 1176LN or Waves RVox): Ratio 4:1, Attack 3 (~400 µs), Release 7 (fastest ~50 ms). Shaving 3-6 dB GR. | Waves CLA-76 / RVox / Live Compressor |
| 4 | Smooth Tube/Opto Leveling | Tube-Tech CL 1B or LA-2A: Ratio 3:1 to 4:1, Attack 15 ms, Release 120 ms, pulling 2-4 dB smooth leveling. | Softube Tube-Tech CL 1B / Live Glue Compressor |
| 5 | High-Frequency Sheen EQ | Pultec EQP-1A or Maag EQ4: +3 to +4 dB boost at 10 kHz shelf or 20 kHz Air Band. | Maag EQ4 / Live EQ Eight |
| 6 | Split-Band De-Essing | De-esser centered between 5.5 kHz and 7.5 kHz, pulling 4-6 dB on sharp consonants. | FabFilter Pro-DS / Live Multiband Dynamics |
| 7 | Dynamic Resonance Taming | Oeksound Soothe2: Depth 1.8 to 2.5, taming harsh upper-mid buildup from compression. | Oeksound Soothe2 / Live Multiband |
| 8 | Fader Smoothing | Waves Vocal Rider holding vocal tightly inside a 1.5 dB window. | Waves Vocal Rider / Live Automation |
| Aux 1 | Stereo Micro-Pitch (Send) | MicroShift detuner (+6 cents L, -6 cents R, 12 ms / 20 ms delay, high cut at 7 kHz), blended at -20 dB for width. | Soundtoys MicroShift / Live Delay |
| Aux 2 | Ducked Tempo Delay (Send) | 1/8th note or dotted 1/8th note, ducked 3-4 dB by lead vocal via sidechain compressor. Low cut 350 Hz, high cut 4.5 kHz. | Soundtoys EchoBoy / Live Delay |
| Aux 3 | Spatial Ambience (Send) | **Kept dry or strictly minimal**. Small room or dark plate (1.2-1.8 s decay, HPF 300 Hz, LPF 5 kHz), blended below -20 dB. | Bricasti M7 / Live Hybrid Reverb |

### 2b. 808 Sub-Bass & Low-End Integration (CONVENTION / FACT)

| Stage | Role | Target Settings / Typical Ranges | Reference Implementation |
|---|---|---|---|
| 1 | Sub Filtering | High-pass filter at 28-32 Hz (24 dB/oct) to strip sub-audible infrasound and maximize amplifier headroom. | FabFilter Pro-Q 3 / Live EQ Eight |
| 2 | Harmonic Saturation | Overdrive/saturation generating 2nd and 3rd harmonics (120-600 Hz) for earbud and mobile speaker audibility. | Soundtoys Decapitator / Live Saturator |
| 3 | Low-End Mono Summing | 100% Mono summing for all frequencies below 100-120 Hz. Eliminates club system phase cancellation. | Brainworx bx_digital / Live Utility (Bass Mono) |
| 4 | Kick Sidechain Ducking | Sidechain compressor or volume shaper ducking 808 by 2.5-4.5 dB during kick hit. Fast attack (1 ms), release 40-70 ms. | FabFilter Pro-C 2 / Kickstart 2 / Live Compressor |

### 2c. Trap Drums & Rolling Hi-Hats (CONVENTION / FACT)

- **Transient Soft-Clipping**: Rather than compressing drums, trap mixers run kicks, 808s, and the drum bus into a dedicated soft clipper (StandardCLIP, T-RackS Clipper, or Ableton Saturator in Soft Clip mode). Shaving off 2-3 dB of transient peaks achieves explosive punch without triggering limiter pump.
- **Rolling Hi-Hats (1/16, 1/32, 1/64 rolls)**:
  - High-pass filter at 350-500 Hz (stripping low-mid clutter).
  - Dynamic EQ or tape saturation dipping harsh 4-6 kHz clicks.
  - Subtle auto-panning (Soundtoys PanMan or Live Auto Pan) and pitch/velocity modulation across rapid rolls.

### 2d. Ad-libs & Vocal Chops (CONVENTION / FACT)

- **Telephone / Radio Filter**: High-pass filter at 350-450 Hz, low-pass filter at 3.5-4.5 kHz, driven with tape saturation.
- **Formant & Pitch Shift**: Soundtoys Little AlterBoy (formant shifted -2 or +2 semitones, pitch unaltered) creating alien or demon vocal doubles.
- **Ping-Pong Delay**: Wide 1/4 note stereo delay repeats panned hard left and right.

### 2e. Modern Hip Hop Mix Bus (CONVENTION / FACT)

1. **VCA Glue Compressor**: SSL 4000 G-Master Bus / Live Glue Compressor: 2:1 or 4:1 ratio, 30 ms attack, auto release, 1.5 to 2.5 dB GR max. High-pass sidechain at 100 Hz so the 808 doesn't choke the compressor.
2. **Low-End Weight EQ**: Pultec EQP-1A: +2 dB boost at 30 Hz or 60 Hz.
3. **Soft Clipper**: Shaving 1.5-2.5 dB of drum transients before the limiter.
4. **True Peak Limiter**: Transparent digital limiter (FabFilter Pro-L 2 in Aggressive mode), ceiling -1.0 dBTP, targeting competitive commercial loudness (-8 to -6 LUFS).

---

## 3. Famous Named Record Profiles

### Derek "MixedByAli" Ali: Kendrick Lamar "DAMN." / SZA "SOS" (FACT)
- **Vocal Chain**: Sony C800G -> Neve 1073 -> CL 1B -> Pro-Q 3 (subtractive 90 Hz HPF, -3 dB at 300 Hz) -> Waves RVox (3-4 dB GR) -> Maag EQ4 (+3 dB at 20 kHz Air Band) -> Pro-DS (5.8 kHz) -> Soothe2 -> Vocal Rider.
- **Space**: MicroShift doubler aux (-20 dB), EchoBoy 1/8d delay ducked by vocal, Bricasti M7 plate (-22 dB).
- **808**: FabFilter Saturn (Clean Tube) generating harmonics at 200 Hz; Pro-Q 3 mono-locking sub below 100 Hz; sidechain ducked 3 dB from kick.

### Mike Dean: Travis Scott "Astroworld" / Kanye West (FACT)
- **Vocal Chain**: Auto-Tune Pro (retune speed 0) -> Soundtoys Decapitator (Style T, Drive 2.5) -> CLA-76 (fast attack/release, 6-10 dB GR) -> Pultec EQP-1A (+3 dB at 10 kHz) -> Eventide H3000 pitch widener -> Roland Space Echo RE-201 delays.
- **808**: Analog TR-808 through overdriven Neve console channel and ProCo Rat pedal, boosted at 50 Hz, clipped on analog summing bus.

### Jaycen Joshua: Modern Commercial Urban & "Clip-To-Zero" (FACT)
- **Vocal Philosophy**: Strict avoidance of reverb. Dual slap delays (mono 16th center + stereo 32nd wide) creating presence without masking.
- **Drums**: Soft clipping on every individual kick and 808 stem before drum bus, shaving 2 dB off peaks to achieve -6 LUFS without limiter pumping.

### Alex Tumay: Young Thug "Barter 6" / 21 Savage (FACT)
- **Vocal Chain**: Sony C800G -> Avalon 737 -> Auto-Tune (retune 8-15) -> Pro-Q 3 -> Tube-Tech CL 1B (4:1, 4-6 dB GR) -> Decapitator (Style E) -> Pro-DS -> Waves H-Delay (dotted 8th ping-pong, ducked 4 dB).

---

## 4. Hip Hop Conflicts & Open Engineering Debates

1. **Reverb vs. Upfront Dryness**: While older 90s boom-bap used plate reverbs on rap vocals, modern trap mixers (Joshua, Ali, Tumay) view long reverbs as destructive to vocal intelligibility, relying almost exclusively on micro-shifts, slap delays, and ducked tempo delays.
2. **Kick Sub vs. 808 Sub Dominance**: Engineers disagree on which element owns the lowest fundamental:
   - *Camp A (808 Dominant)*: 808 sits at 35-60 Hz; kick is high-passed at 55 Hz and serves as transient click.
   - *Camp B (Kick Dominant)*: Kick owns 45-65 Hz punch; 808 is sidechain-ducked on downbeats.
3. **Soft-Clipping vs. Heavy Brickwall Limiting**: Purists argue soft-clipping introduces distortion; modern urban mixers demonstrate that soft-clipping maintains punchy transients far better than limiters when targeting -7 to -5 LUFS.

---

## 5. Stock Ableton Live Device Mapping (Reference Preset)

- **Trap Lead Vocal**: `Audio Effect Rack` [EQ Eight (HPF 90 Hz, -3 dB at 320 Hz) -> Compressor (Peak mode, 4:1, Attack 0.5 ms, Release 50 ms) -> Glue Compressor (Opto, Soft Clip ON) -> EQ Eight (+3 dB High Shelf 10 kHz) -> Multiband Dynamics (De-Essing preset)].
- **808 Processor**: `Audio Effect Rack` [EQ Eight (HPF 30 Hz) -> Saturator (Soft Sine / Analog Clip, Drive +3 dB) -> Utility (Bass Mono ON, Freq 110 Hz) -> Compressor (Sidechain enabled, keyed to Kick, Attack 1 ms, Release 50 ms, GR 3 dB)].
- **Trap Drum Bus**: `Audio Effect Rack` [EQ Eight (HPF 25 Hz) -> Saturator (Digital Clip / Soft Clip, Output -0.5 dB, Drive +2 dB) -> Glue Compressor (2:1, Attack 30 ms, Release Auto, 1-2 dB GR)].
