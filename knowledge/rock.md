# Rock FX chains (knowledge page)

Synthesized from `research/raw/2026-11-10-rock-fx-chains.md` and spot-checked against Sound On Sound engineering archives ("Secrets Of The Mix Engineers", "Inside Track") on 2026-11-10. Chains are organized by **ROLE and stage order** so they can resolve to Ableton Live stock devices or third-party VSTs (see `src/abletonlivemcp/adapters.py`).

Related pages: [vocals](vocals.md), [drums](drums.md), [guitar-bass](guitar-bass.md), [busses-mixing](busses-mixing.md), [mastering](mastering.md), [hip-hop](hip-hop.md), [pop](pop.md), [acoustic](acoustic.md), [edm](edm.md).

---

## 1. Scope and how to read this page

- Covers classic rock, hard rock, modern alternative, and heavy metal FX chains across lead vocals, rhythm/lead guitars, rock bass, acoustic/rock drum kits, parallel busses, and the rock mix bus.
- Evidence labels:
  - **FACT** = Documented for a named recording or engineer session.
  - **CONVENTION** = Widely documented standard engineering practice across multiple premier rock facilities.
  - **OPINION** = Individual engineer preference, blog, or community analysis.
- Generic roles map directly to standard audio devices (e.g. `compressor_fet` = Urei 1176 / Ableton Compressor in Peak mode; `compressor_opto` = Teletronix LA-2A/LA-3A; `vca_bus_comp` = SSL G-Master Bus / Ableton Glue Compressor; `saturation_tape` = Studer A800 / Ableton Saturator).

---

## 2. Consensus patterns by sub-element

### 2a. Rock Lead Vocal Chain (CONVENTION / FACT)

| Stage | Role | Target Settings / Typical Ranges | Reference Implementation |
|---|---|---|---|
| 1 | Corrective EQ | HPF 80-100 Hz (18 dB/oct); dynamic notch cut 250-400 Hz (proximity mud); narrow dip 2.8-3.5 kHz if harsh. | FabFilter Pro-Q 3 / Ableton EQ Eight |
| 2 | Peak Limiting / Catching | Fast FET compression (Urei 1176 Blue Stripe or Blackface): Ratio 4:1, Attack 3 (medium-fast, ~400 µs), Release 7 (fastest, ~50 ms). Shaving 4-8 dB GR on vocal peaks. | Waves CLA-76 / UAD 1176LN / Live Compressor (Peak) |
| 3 | Optical Leveling | Smooth optical compressor (Teletronix LA-2A or LA-3A): 2-4 dB gentle leveling, smooth decay. | UAD LA-2A / Waves CLA-2A |
| 4 | Presence / Air EQ | Console or tube EQ: High shelf +4 to +6 dB at 8-10 kHz; broad midrange presence peak at 3.5 kHz (+2 dB). | Pultec EQP-1A / SSL 4000 E Channel EQ |
| 5 | De-Esser | Split-band de-essing centered at 5.5-7.5 kHz, 4-6 dB reduction on sibilant consonants. | dbx 902 / FabFilter Pro-DS |
| 6 | Fader Automation | Hand automation or fader rider (+/- 3 dB) keeping vocal anchored on top of heavy guitars. | Waves Vocal Rider / Live Automation |
| Aux 1 | Slap Delay (Send) | Analog tape slap delay: 100-140 ms (or 15 ips tape emulation), single repeat, rolled off below 300 Hz and above 4 kHz. | Soundtoys EchoBoy / Live Delay (Tape mode) |
| Aux 2 | Tempo Delay (Send) | 1/8th note or dotted 1/8th note, ducked by 3-4 dB via sidechain compressor keyed to dry vocal. | Waves H-Delay / Live Delay |
| Aux 3 | Tight Room Reverb (Send) | Short ambient room (0.8 - 1.2 s decay), pre-delay 15-25 ms, low cut 300 Hz, high cut 5 kHz. (Long halls shut off during rock sections). | Lexicon 300 / Sony DRE2000 / Live Hybrid Reverb |

### 2b. High-Gain & Crunch Rhythm Guitars (CONVENTION / FACT)

| Stage | Role | Target Settings / Typical Ranges | Reference Implementation |
|---|---|---|---|
| 1 | Pre-Distortion Tightening | Overdrive pedal ahead of amplifier: Drive 0, Tone 5.5-6.0, Level 10. Strips sub-100 Hz mud before clipping. | Ibanez TS9 / Maxon OD808 / Live Pedal (OD) |
| 2 | High-Gain Amplifier | Tube amplifier (Peavey 5150, Mesa Dual Rectifier, Marshall JCM800). Preamp gain 4.5-6.0 (avoiding oversaturation). | Neural DSP / Softube / Live Amp (Lead/Heavy) |
| 3 | Cabinet & Microphones | 4x12 cab with Celestion V30 speakers; dual SM57 and Royer 121 ribbon mics blended. | Cab IR / Live Cabinet |
| 4 | Post-Amp High/Low Cut | High-pass filter at 80-90 Hz (24 dB/oct); Low-pass filter at 10-12 kHz (removing abrasive fizz). | Ableton EQ Eight |
| 5 | Surgical Resonance Notch | High-Q narrow parametric notches (-3 to -6 dB, Q 6.0-10.0) on cabinet whistle frequencies (2.8 to 4.2 kHz). | FabFilter Pro-Q 3 / Ableton EQ Eight |
| 6 | Presence Shelf EQ | SSL E-series console EQ: High shelf +4 to +8 dB at 8 kHz. Mid frequencies explicitly preserved (no scooping). | Waves SSL EV2 / Live EQ Eight |
| 7 | Dynamics (Optional) | Discrete optical/VCA compressor (Teletronix LA-3A): 2-3 dB GR max. Often kept completely uncompressed. | UAD LA-3A / Live Compressor |
| Aux | Spatial Reverb | **100% Dry**. Top rock mixers (CLA, Wallace) explicitly leave rhythm guitars completely dry. | None |

### 2c. Rock Bass (Clean Sub + Dirty Parallel Bite) (CONVENTION / FACT)

- **Architecture**: Bass is split into two parallel channels (or dual-band crossover split at 200-250 Hz).
- **Channel 1 (Clean Low-End DI)**:
  - Low-pass filter at 200 Hz. High-pass filter at 30 Hz (18 dB/oct).
  - Brickwall limiting or heavy VCA/FET compression (8:1 or 4:1 ratio, 8-12 dB GR) holding sub frequencies rock-solid.
- **Channel 2 (Dirty Mid/High Growl)**:
  - High-pass filter at 200 Hz. Low-pass filter at 3 kHz.
  - Overdriven through SansAmp Bass Driver DI, Darkglass B7K, or Ampeg SVT tube head.
  - EQ: Scooped at 500 Hz (-6 dB), boosted at 1.5-2.5 kHz (+4 dB) for pick clank and string cut.
- **Summing**: Channels blended 50/50, phase-aligned with drum kick, summed to mono below 100 Hz.

### 2d. Rock Drum Bus & Parallel Crush (CONVENTION / FACT)

| Element | Signal Path & Settings | Reference Equipment |
|---|---|---|
| Kick Close Mic | HPF 30 Hz, cut -4 dB at 350 Hz (boxiness), boost +3 dB at 60 Hz (weight) and +4 dB at 3.5 kHz (beater click). Gated with 1.5 kHz sidechain filter. | Neve 1073 / SSL Channel / Live EQ Eight |
| Snare Close Mic | HPF 80 Hz, dip at 400 Hz, boost +3 dB at 200 Hz (body) and +4 dB at 5-7 kHz (snap). dbx 160 compressor (4:1, 4-6 dB GR). | dbx 160 / Live Compressor |
| Drum Parallel Crush Bus | Parallel send from all acoustic drums: Urei 1176 "All-Buttons-In" (British mode, 20:1 ratio, fastest attack, fastest release, 15-25 dB GR) or Empirical Labs Distressor (1:1 Nuke). Blended -14 dB under clean kit. | UAD 1176 / Distressor / Live Glue Compressor |
| Room Mics | Coles 4038 ribbon or Neumann U87 room pair smashed with Gates Sta-Level or Fairchild 670 (10-15 dB GR) for ambient explosive decay. | Gates Sta-Level / Live Compressor |
| Drum Sub-Bus Glue | SSL Quad / Live Glue Compressor: Ratio 4:1, Attack 10-30 ms, Release 0.1 s, 3-5 dB GR. High-pass sidechain filter set at 80 Hz to prevent kick pumping. | SSL G-Master / Live Glue Compressor |

### 2e. Rock Mix Bus (CONVENTION / FACT)

1. **VCA Bus Compressor**: SSL 4000 G-series Master Bus Compressor / Live Glue Compressor.
   - Settings: Ratio 4:1 (or 2:1), Attack 30 ms (slow, letting drum transients punch), Release Auto or 0.1 s, Gain Reduction 2-3 dB on loud chorus hits. Sidechain HPF at 80-100 Hz.
2. **Analog Tape Saturation**: Studer A800 or Ampex ATR-102 (15 ips or 30 ips, +3 to +6 dB hot input drive).
3. **True Peak Limiting**: Clean digital limiter (FabFilter Pro-L 2 in Dynamic/Punchy mode), ceiling -1.0 dBTP, catching 1-2 dB on highest peaks.

---

## 3. Famous Named Record Profiles

### Chris Lord-Alge: My Chemical Romance "Welcome To The Black Parade" (FACT)
- **Lead Vocal**: Waves L1 limiter on input for bite -> Blue-stripe 1176 (4:1, attack 3, fastest release 7) -> dbx 263x de-esser -> Roland SDE-3000 (1/4 & 1/8 note delays) -> Marshall Tape Emulator (15 ips slap) -> Lexicon 300 (7s hall in intro, muted to 1s room in rock sections).
- **Rhythm Guitars**: 3 mics per amp summed -> Teletronix LA-3A (2-3 dB GR) -> SSL E-Channel EQ (+6 to +8 dB at 8 kHz shelf, no mid-scoop) -> 100% dry (no reverb).
- **Bass**: Blackface Urei 1176LN (4:1, 7 dB GR) -> Heavy high-frequency console EQ boost for cut against wall of guitars.

### Andy Wallace: Nirvana "Nevermind" / Linkin Park "Hybrid Theory" (FACT)
- **Console & Glue**: SSL 4000 G-series console. SSL Master Bus Compressor (4:1, 30 ms attack, auto release, 2-4 dB GR).
- **Drums**: Custom Yamaha snare sample triggered at -8 dB behind Grohl's acoustic snare. Kick dipped at 350 Hz, boosted at 60 Hz and 3.5 kHz.
- **Vocals**: Butch Vig tape doubles mixed through SSL with 1176 (4:1, medium attack, fast release) into Pultec EQP-1A (+3 dB at 10 kHz). Eventide H3000 pitch microshift (+9 cents L, -9 cents R, 20 ms delay) blended at -18 dB for stereo width.

### Butch Vig: Smashing Pumpkins "Siamese Dream" (FACT)
- **Guitar Wall**: Up to 24 tracks of Billy Corgan's EHX Op-Amp Big Muff into 100W Marshall JCM800. High-passed at 90 Hz, low-passed at 10 kHz, surgical notch cuts removing 3.2 kHz harsh whistling resonances.

---

## 4. Rock Conflicts & Open Engineering Debates

1. **The Guitar Mid-Scoop Myth**: Bedroom guitarists often scoop 500-800 Hz on amplifiers; however, every documented rock mixing engineer (CLA, Wallace, Vig, Bogren) explicitly avoids mid-scooping, noting that electric guitars live between 400 Hz and 3 kHz and scooping causes them to vanish in a dense mix.
2. **Reverb vs. Dry Guitars**: While amateur mixes often drench rhythm guitars in reverb, professional rock mixers maintain rhythm guitars 100% dry, using room ambience only on drums and intros.
3. **Sample Blending vs. Pure Acoustic Drums**: Andy Wallace and CLA champion triggering drum samples behind live kits for consistency through dense guitars; Steve Albini and vintage purists reject drum replacement outright.

---

## 5. Stock Ableton Live Device Mapping (Reference Preset)

- **Lead Vocal**: `Audio Effect Rack` [EQ Eight (HPF 85 Hz, -3 dB at 320 Hz) -> Compressor (FET Peak, 4:1, Attack 0.5 ms, Release 50 ms) -> Glue Compressor (Opto style, 2:1, Soft Clip) -> EQ Eight (+4 dB High Shelf 9 kHz) -> De-Esser / Multiband Dynamics].
- **Heavy Guitar**: `Audio Effect Rack` [Pedal (OD mode, Gain 0, Output 10) -> Amp (Heavy/Lead) -> Cabinet (4x12) -> EQ Eight (HPF 85 Hz, LPF 11 kHz, notch 3.5 kHz, +5 dB Shelf 8 kHz)].
- **Drum Parallel Smash**: Aux Track [Glue Compressor (Ratio 10:1, Attack 0.1 ms, Release 0.1 s, Range full, Drive +6 dB, Peak GR 15-20 dB) -> EQ Eight (HPF 60 Hz, LPF 8 kHz)].
