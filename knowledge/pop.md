# Pop FX chains (knowledge page)

Synthesized from `research/raw/2026-11-10-pop-fx-chains.md` and spot-checked against Sound On Sound engineering archives ("Inside Track", "Secrets Of The Mix Engineers") on 2026-11-10. Chains are organized by **ROLE and stage order** so they can resolve to Ableton Live stock devices or third-party VSTs (see `src/abletonlivemcp/adapters.py`).

Related pages: [vocals](vocals.md), [drums](drums.md), [busses-mixing](busses-mixing.md), [mastering](mastering.md), [rock](rock.md), [hip-hop](hip-hop.md), [acoustic](acoustic.md), [edm](edm.md).

---

## 1. Scope and how to read this page

- Covers modern commercial chart pop, dance-pop, vocal ballads, and K-pop across hyper-polished lead vocals, massive backing vocal stacks, sidechained synth/pad layers, and the high-gloss pop mix bus.
- Evidence labels:
  - **FACT** = Documented for a named recording or engineer session.
  - **CONVENTION** = Widely documented standard engineering practice across premier commercial pop facilities.
  - **OPINION** = Individual engineer preference, blog, or community advice.
- Generic roles map directly to standard audio devices (e.g. `pitch_corrector` = Melodyne / Auto-Tune; `compressor_fet` = Urei 1176 / Live Compressor; `compressor_opto` = CL 1B / LA-2A; `vca_bus_comp` = SSL G-Master Bus / Live Glue Compressor).

---

## 2. Consensus patterns by sub-element

### 2a. Pristine Modern Pop Lead Vocal (CONVENTION / FACT)

| Stage | Role | Target Settings / Typical Ranges | Reference Implementation |
|---|---|---|---|
| 1 | Transparent Pitch & Timing | Celemony Melodyne note-by-note manual intonation and timing alignment, into Antares Auto-Tune Pro (Retune Speed 25-40 ms) for subtle real-time centering. | Melodyne + Auto-Tune Pro / Live PitchDrop |
| 2 | Subtractive Surgical EQ | HPF 85-95 Hz (18 dB/oct); narrow parametric notches (-2 to -4 dB) on boxy mid buildup (300-450 Hz) and harsh mic resonances (2.8 kHz and 4.2 kHz). | FabFilter Pro-Q 3 / Live EQ Eight |
| 3 | Fast FET Peak Compression | Urei 1176LN (Blackface or Blue Stripe): Ratio 4:1, Attack 3 (medium-fast ~400 µs), Release 7 (fastest ~50 ms). Shaving 2-4 dB off transient peaks. | Waves CLA-76 / Live Compressor (Peak) |
| 4 | Smooth Optical Leveling | Tube-Tech CL 1B or Teletronix LA-2A: Ratio 3:1 to 4:1, Attack 20 ms, Release 120 ms, pulling 3-5 dB smooth musical leveling. | Tube-Tech CL 1B / Live Glue Compressor |
| 5 | High-Frequency Sheen EQ | Maag EQ4 Air Band (+3 to +4 dB at 20 kHz) or GML 8200 / Pultec EQP-1A (+2 to +3 dB at 12-16 kHz high shelf). | Maag EQ4 / Live EQ Eight |
| 6 | Dual-Stage De-Essing | Two de-essers in series: De-esser 1 at 5.5-6.5 kHz (catching dental "s" consonants); De-esser 2 at 10-12 kHz (taming top-end sizzle). | FabFilter Pro-DS / Live Multiband Dynamics |
| 7 | Harshness Suppression | Oeksound Soothe2: Depth 1.5 to 2.5, smoothing upper-mid harshness introduced by serial compression. | Oeksound Soothe2 / Live Multiband |
| 8 | Fader Smoothing | Waves Vocal Rider holding the performance inside a strict 1.5 dB dynamic window. | Waves Vocal Rider / Live Automation |
| Aux 1 | Stereo Micro-Shift (Send) | Micro-pitch shift (+6 cents L, -6 cents R, 15 ms / 22 ms delay, high frequencies rolled off above 8 kHz), blended at -20 dB. | Soundtoys MicroShift / Live Delay |
| Aux 2 | Ducked Tempo Delay (Send) | 1/8th note or dotted 1/8th note delay. Filtered (HPF 300 Hz, LPF 5 kHz) and ducked by 4 dB using sidechain compression keyed to lead vocal. | Waves H-Delay / Live Delay |
| Aux 3 | Expansive Plate Reverb (Send) | Bricasti M7 or Lexicon 480 Large Plate (2.0-2.5 s decay, pre-delay 30-45 ms, HPF 250 Hz, LPF 7 kHz). Pre-delay preserves lead transient clarity. | Lexicon 480 / Live Hybrid Reverb |

### 2b. Stacked Backing Vocals & Harmonies (CONVENTION / FACT)

- **Arrangement**: Typically 10 to 40+ vocal stems panned across the stereo spectrum (tight doubles 100% L/R, high harmonies 70% L/R, mid harmonies 40% L/R).
- **Sub-Bus Processing**:
  - Band-pass filtering: High-pass filter at 160-200 Hz (clearing room for lead vocal body); Low-pass filter at 8-10 kHz.
  - Aggressive Compression: Fairchild 670 or VCA compressor (8:1 or 10:1 ratio, 6-10 dB GR) squashing dynamics into a cohesive, pad-like vocal wall.
  - Stereo Spread: Waves S1 Stereo Imager or subtle chorus widening the background image.
  - Dedicated Darker Reverb: Routed to a separate, darker hall/plate reverb so backing vocals sit noticeably behind the dry, bright lead.

### 2c. Rhythmic Sidechain Pumping / Ducking (CONVENTION / FACT)

- Rhythmic volume ducking on synths, bass, and pads synced to kick drum hits.
- Standard modern implementation: Dedicated volume envelope shapers (LFO Tool, Kickstart 2, Cableguys VolumeShaper) synced to 1/4 note downbeats, dropping signal 80-100% on transient strike and recovering smoothly before the next 8th note. Producer Ian Kirkpatrick and Serban Ghenea favor envelope shapers over traditional compressors for precise recovery control.

### 2d. High-Gloss Pop Mix Bus (CONVENTION / FACT)

1. **VCA Bus Compressor**: SSL 4000 G-Master Bus / Live Glue Compressor: Ratio 4:1 (or 2:1), Attack 30 ms (slow, preserving punch), Release Auto, Gain Reduction 1.5 to 2.5 dB.
2. **Pultec Air & Weight**: Pultec EQP-1A: +1.5 dB boost at 30 Hz (weight) and +2 dB boost at 16 kHz (glossy top sheen).
3. **Multi-Band Tape Warmth**: Studer A800 or FabFilter Saturn 2 (subtle clean tape mode, 1-2 dB drive).
4. **Dynamic High-Mid Control**: Oeksound Soothe2 on mix bus (very mild depth 0.8-1.2) preventing digital fatigue at 3-5 kHz across loud playback systems.
5. **True Peak Limiting**: FabFilter Pro-L 2 in Modern style, ceiling -1.0 dBTP, targeting commercial streaming pre-master loudness (-9 to -7 LUFS).

---

## 3. Famous Named Record Profiles

### Serban Ghenea & John Hanes: Taylor Swift / The Weeknd "Blinding Lights" (FACT)
- **Vocal Chain**: Melodyne manual prep -> Auto-Tune (retune 30) -> Pro-Q 3 -> CLA-76 (4:1, 4-6 dB GR) -> Tube-Tech CL 1B (3 dB GR) -> Maag EQ4 (+3 dB 20 kHz Air Band) -> Dual de-essers (5.8 kHz and 11 kHz) -> Soothe2 -> Vocal Rider.
- **Mix Bus**: SSL G-Master Bus Compressor (4:1, 30 ms attack, auto release, 2 dB GR) into Pro-L 2 (-1.0 dBTP ceiling).

### Tom Elmhirst: Adele "Hello" (FACT)
- **Vocal Architecture**: Unconventional minimal compression to preserve emotional vocal dynamics; replaced heavy compression with meticulous manual fader automation (+/- 6 dB).
- **De-Essing**: Two Waves DeEssers dialed into exact frequencies: 5,449 Hz and 11,004 Hz.
- **Tone**: Neve VR console EQ, Pultec EQP-1A, EMT 140 plate reverb.

### Josh Gudwin & Ian Kirkpatrick: Dua Lipa "Don't Start Now" (FACT)
- **Vocal Chain**: Pro-Q 3, CLA-76, CL 1B, Maag EQ4, Pro-DS, Soothe.
- **Reverb Innovation**: Valhalla VintageVerb aux return feeding Xfer OTT (multiband compressor expanding ambient detail) into LFO Tool sidechain ducking.
- **Bridge Vocal Chop**: Little AlterBoy (formant shift down) -> MicroShift -> Waves H-Delay (dotted 8th) placed ahead of FabFilter Saturn (acting as dynamic compressor) -> Waves C1 -> Pro-DS -> LFO Tool.

---

## 4. Pop Conflicts & Open Engineering Debates

1. **Extreme Compression vs. Meticulous Fader Riding**: Standard commercial pop (Serban Ghenea) clamps vocals through dual compressors plus Vocal Rider; acoustic/ballad pop mixers (Tom Elmhirst on Adele) argue heavy compression squashes emotional connection, favoring manual automation and gentle leveling.
2. **LFO Volume Shaper vs. Sidechain Compressor**: Modern electronic pop producers (Ian Kirkpatrick, Josh Gudwin) reject audio-triggered sidechain compressors because erratic kick transients produce inconsistent pump; they mandate dedicated LFO volume shapers (LFO Tool, Kickstart) for mathematically repeatable groove.

---

## 5. Stock Ableton Live Device Mapping (Reference Preset)

- **Pop Lead Vocal Rack**: `Audio Effect Rack` [EQ Eight (HPF 90 Hz, -3 dB at 350 Hz) -> Compressor (Peak, 4:1, Attack 0.4 ms, Release 50 ms) -> Glue Compressor (Opto, Soft Clip ON) -> EQ Eight (+3.5 dB Shelf 12 kHz) -> Multiband Dynamics (De-Essing split) -> Utility (Gain automation)].
- **Backing Vocal Wall**: `Audio Effect Rack` [EQ Eight (HPF 180 Hz, LPF 9 kHz) -> Glue Compressor (Ratio 10:1, Attack 1 ms, Release 0.2 s, 8 dB GR) -> Utility (Stereo Width 135%)].
- **Pop Mix Bus Glue**: `Audio Effect Rack` [Glue Compressor (4:1, Attack 30 ms, Release Auto, 2 dB GR) -> EQ Eight (+1.5 dB Shelf 16 kHz, +1 dB Peak 50 Hz) -> Saturator (Soft Sine, Drive +1 dB, Output -1 dB)].
