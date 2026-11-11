# Acoustic FX chains (knowledge page)

Synthesized from `research/raw/2026-11-10-acoustic-fx-chains.md` and spot-checked against Sound On Sound engineering archives ("Secrets Of The Mix Engineers", acoustic recording masterclasses) on 2026-11-10. Chains are organized by **ROLE and stage order** so they can resolve to Ableton Live stock devices or third-party VSTs (see `src/abletonlivemcp/adapters.py`).

Related pages: [vocals](vocals.md), [drums](drums.md), [guitar-bass](guitar-bass.md), [busses-mixing](busses-mixing.md), [mastering](mastering.md), [rock](rock.md), [hip-hop](hip-hop.md), [pop](pop.md), [edm](edm.md).

---

## 1. Scope and how to read this page

- Covers acoustic guitar (fingerstyle, strummed steel-string, nylon), acoustic/folk vocals, upright (double) bass, acoustic percussion (cajon, shakers), and acoustic ensemble bus processing.
- Evidence labels:
  - **FACT** = Documented for a named recording or engineer session.
  - **CONVENTION** = Widely documented standard engineering practice across premier acoustic and scoring facilities.
  - **OPINION** = Individual engineer preference, blog, or community advice.
- Generic roles map directly to standard audio devices (e.g. `compressor_opto` = LA-2A / Tube-Tech CL 1B / Live Glue Compressor; `eq_parametric` = GML 8200 / Live EQ Eight; `reverb_convolution` = Bricasti M7 / Live Hybrid Reverb Convolution).

---

## 2. Consensus patterns by sub-element

### 2a. Acoustic Guitar Chain (Steel String & Fingerstyle) (CONVENTION / FACT)

| Stage | Role | Target Settings / Typical Ranges | Reference Implementation |
|---|---|---|---|
| 1 | Low-End Cleanup | High-pass filter at 75-85 Hz (12-18 dB/oct) to strip stage thumps, air conditioning rumble, and mechanical floor vibrations. | FabFilter Pro-Q 3 / Live EQ Eight |
| 2 | Soundhole Resonance Notch | Narrow parametric cut (-3 to -5 dB, Q 2.0 to 3.0) centered between 180 Hz and 240 Hz to tame the guitar's internal cavity "woof/boom". | GML 8200 / Live EQ Eight |
| 3 | Pick & Fret Softening | Broad gentle dip (-1.5 to -2.5 dB, Q 1.2 to 1.5) centered at 2.8 kHz to 3.5 kHz, preventing aggressive pick clicks from competing with the vocal. | Neve 1073 / Live EQ Eight |
| 4 | High-Frequency Shimmer | High-shelf filter boosting 1.5 to 2.5 dB above 12 kHz, adding silky acoustic air and fingerboard shimmer. | Pultec EQP-1A / Live EQ Eight |
| 5 | Transparent Dynamics | Optical or Vari-Mu compressor (Teletronix LA-2A, Tube-Tech CL 1B, Fairchild 660): Ratio 2:1 to 3:1, Slow attack (25-35 ms), Release 150-250 ms, Gain Reduction 1.5 to 3.0 dB max. | UAD LA-2A / Live Glue Compressor |
| Aux 1 | Wooden Room Ambience (Send) | Convolution reverb using real wooden room or small hall impulse response (1.2-1.6 s decay, pre-delay 20-30 ms, low cut at 200 Hz). | Bricasti M7 / Live Hybrid Reverb |

### 2b. Acoustic / Folk Lead Vocal (CONVENTION / FACT)

| Stage | Role | Target Settings / Typical Ranges | Reference Implementation |
|---|---|---|---|
| 1 | Rumble Filtering | High-pass filter at 65-75 Hz (18 dB/oct), removing mic stand rumble while keeping vocal warmth intact. | Live EQ Eight |
| 2 | Subtractive Warmth EQ | Gentle wide cut at 300-350 Hz (-1.5 dB) if the proximity effect created chest heaviness; high shelf +1.5 dB at 12 kHz. | Pultec MEQ-5 / Live EQ Eight |
| 3 | Tube / Optical Leveling | Teletronix LA-2A or Fairchild 660: Ratio 2:1, smooth time constant, needle moving only 1.5 to 3.0 dB on peaks. | UAD Fairchild 660 / Live Glue Compressor |
| 4 | Sibilance Protection | Transparent optical de-essing (dbx 902 or Pro-DS) centered at 6 kHz, gently reducing sharp peaks by 2-4 dB. | dbx 902 / Live Multiband Dynamics |
| 5 | Pitch Correction | **None or strictly bypassed**. In acoustic/folk genres, natural pitch nuances and expressive micro-intonations are essential to artistic authenticity. | None |
| Aux 1 | Live Chamber / Plate (Send) | Natural acoustic chamber or EMT 140 plate reverb (1.8-2.2 s decay, warm dampening above 6 kHz, pre-delay 25 ms). | EMT 140 / Live Hybrid Reverb |

### 2c. Upright (Double) Bass Chain (CONVENTION / FACT)

- **Dual-Source Balancing**:
  - *Bridge Microphone (Air & Click)*: High-pass filter at 45 Hz. Dynamic notch cut at 120-140 Hz (-4 dB) to control room standing wave resonance. High shelf boost at 2 kHz (+2 dB) for string and fingerboard definition.
  - *Piezo Pickup DI (Low-End Weight)*: High-pass filter at 35 Hz. Steep low-pass filter at 350 Hz to eliminate harsh piezo quack. Compressed with VCA compressor (dbx 160 or Live Compressor, 3:1, 4 dB GR).
  - *Bass Bus*: Channels summed, checked for phase alignment, compressed gently with Teletronix LA-2A (2-3 dB GR), and routed through a short wooden room ambience (0.8 s decay).

### 2d. Acoustic Percussion (Cajon, Shakers, Tambourines) (CONVENTION / FACT)

- **Cajon**: Front mic high-passed at 80 Hz, boosted at 3.5 kHz for beater snap; rear internal mic boosted at 60 Hz for punch, gated with fast release to avoid muddy tail buildup.
- **Shakers & Tambourines**: High-pass filter at 400-600 Hz (stripping all low-end weight), gentle optical compression smoothing transient spikes, panned wide to frame the acoustic guitar.

### 2e. Acoustic Master & Bus Processing (CONVENTION / FACT)

1. **Tube Vari-Mu Master Compressor**: Manley Variable Mu / Fairchild 670: Ratio 1.5:1, Attack 30-40 ms, Release auto/slow, needle barely moving (0.5 to 1.5 dB GR max).
2. **Passive Sweetening EQ**: Pultec EQP-1A or Baxandall EQ: +1 dB at 16 kHz shelf, +0.5 dB at 60 Hz.
3. **Transparent True Peak Limiter**: Linear-phase limiter (FabFilter Pro-L 2 in Safe / Transparent style), ceiling -1.0 dBTP, catching less than 1 dB of peak overshoot. Dynamic range strictly preserved at -14 to -12 LUFS integrated.

---

## 3. Famous Named Record Profiles

### Al Schmitt: Diana Krall / Natalie Cole "Unforgettable" (FACT)
- **Tracking Philosophy**: Absolute zero EQ during recording. "If it doesn't sound right, move the microphone an inch."
- **Acoustic Guitar**: Neumann U67 or Schoeps pair pointed at 12th fret and bridge -> Neve 8068 console preamp -> Fairchild 660 compressor (1-2 dB GR max) -> Capitol Records Chamber 4 live acoustic echo chamber.
- **Acoustic Vocals**: Neumann U47 into Neve preamp into Fairchild 660 (2 dB GR) into Capitol Chamber 4. Zero pitch correction, zero doublers.

### George Massenburg: James Taylor / Linda Ronstadt (FACT)
- **Acoustic Guitar**: GML 8200 parametric EQ: HPF at 80 Hz, notch cut at 220 Hz (-3.5 dB, Q 2.5) for soundhole boom, dip at 3 kHz (-1.5 dB) for pick clicks, high shelf +2 dB at 12 kHz. GML 8900 dynamic controller (2:1 ratio, 35 ms attack, 2 dB GR). Bricasti M7 "Wood Room" reverb.

### Chuck Ainlay: Mark Knopfler / Dire Straits (FACT)
- **Acoustic Guitar**: Small diaphragm condenser pair (Neumann KM184) -> Neve 1073 (HPF 80 Hz, +2 dB 10 kHz) -> Distressor (Opto mode, 2-3 dB GR) -> EMT 140 plate reverb.
- **Upright Bass**: Bridge mic (U47 FET) + Piezo DI (LPF at 350 Hz, dbx 160SL comp, 4 dB GR).

---

## 4. Acoustic Conflicts & Open Engineering Debates

1. **Zero Tracking EQ vs. In-The-Box Surgical Carving**: Classical and jazz purists (Al Schmitt) insist on fixing tone exclusively through microphone placement and rejecting EQ entirely; modern hybrid acoustic engineers (George Massenburg, Chuck Ainlay) demonstrate that precision high-Q notch filtering is necessary to control internal soundhole resonances in dense acoustic-pop arrangements.
2. **Pitch Correction**: While commercial pop mandates pitch correction, acoustic and folk purists reject Auto-Tune, arguing that pitch quantization erases vocal inflection, emotion, and human warmth.

---

## 5. Stock Ableton Live Device Mapping (Reference Preset)

- **Acoustic Guitar Rack**: `Audio Effect Rack` [EQ Eight (HPF 80 Hz, notch -4 dB at 210 Hz, dip -1.5 dB at 3.2 kHz, +2 dB Shelf 12 kHz) -> Glue Compressor (2:1, Attack 30 ms, Release Auto, 2 dB GR max) -> Hybrid Reverb (Convolution engine, Wood Room impulse, 1.4 s decay, pre-delay 25 ms, blend 18%)].
- **Acoustic Vocal Rack**: `Audio Effect Rack` [EQ Eight (HPF 70 Hz, -1 dB at 320 Hz) -> Glue Compressor (2:1, Attack 10 ms, Release Auto, 1.5-2 dB GR) -> Hybrid Reverb (Convolution plate, 2.0 s decay, 25 ms pre-delay)].
- **Acoustic Master Bus**: `Audio Effect Rack` [Glue Compressor (2:1, Attack 30 ms, Release Auto, 1 dB GR max) -> EQ Eight (+1 dB Shelf 16 kHz) -> Limiter (Ceiling -1.0 dB, Gain +1 dB, lookahead 5 ms)].
