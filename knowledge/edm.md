# EDM FX chains (knowledge page)

Synthesized from `research/raw/2026-11-10-edm-fx-chains.md` and spot-checked against Sound On Sound engineering archives ("Inside Track", electronic production series) and masterclasses on 2026-11-10. Chains are organized by **ROLE and stage order** so they can resolve to Ableton Live stock devices or third-party VSTs (see `src/abletonlivemcp/adapters.py`).

Related pages: [keys-synths](keys-synths.md), [drums](drums.md), [busses-mixing](busses-mixing.md), [mastering](mastering.md), [rock](rock.md), [hip-hop](hip-hop.md), [pop](pop.md), [acoustic](acoustic.md).

---

## 1. Scope and how to read this page

- Covers festival EDM, modern big room, future bass, dubstep/bass house, and electronic club mixing across supersaw lead chords, bass sound design, sub-bass mono architecture, drop tension/build-up transitions, and extreme loudness master bus processing.
- Evidence labels:
  - **FACT** = Documented for a named recording or engineer session.
  - **CONVENTION** = Widely documented standard engineering practice across premier electronic music production.
  - **OPINION** = Individual engineer preference, blog, or community advice.
- Generic roles map directly to standard audio devices (e.g. `multiband_ott` = Xfer OTT / Ableton Multiband Dynamics "OTT"; `envelope_shaper` = Kickstart 2 / LFO Tool; `clipper_soft` = StandardCLIP / Ableton Saturator; `utility_mono` = Ableton Utility Bass Mono).

---

## 2. Consensus patterns by sub-element

### 2a. Supersaw Lead & Synth Chord Stacks (CONVENTION / FACT)

| Stage | Role | Target Settings / Typical Ranges | Reference Implementation |
|---|---|---|---|
| 1 | Subtractive Pre-EQ | High-pass filter at 150-180 Hz (24 dB/oct) to prevent chord pads from colliding with the kick drum and sub-bass; notch cut at 400-500 Hz (-2.5 dB) for midrange clarity. | FabFilter Pro-Q 3 / Live EQ Eight |
| 2 | Multiband OTT Dynamics | Xfer OTT / Ableton Multiband Dynamics: Depth 25-40%, Time 100%. Low band muted or bypassed; Mid and High bands apply simultaneous downward peak compression and +15 to +20 dB upward expansion. | Xfer OTT / Live Multiband Dynamics (OTT) |
| 3 | Harmonic Saturation | Multi-band tape/tube distortion: FabFilter Saturn 2 or Soundtoys Decapitator adding aggressive 2nd and 3rd harmonics in the 1-5 kHz range. | FabFilter Saturn 2 / Live Saturator |
| 4 | Stereo Dimension Widening | Haas delay or dimension expansion widening Side frequencies above 1 kHz. Mid channel remains tight and centered. | Brainworx bx_digital / Live Utility (130% Width) |
| 5 | Rhythmic Sidechain Ducking | Volume envelope shaper (Nicky Romero Kickstart 2 / LFO Tool / Cableguys VolumeShaper): 1/4 note curve, 100% ducking on kick strikes, resetting smoothly. | Kickstart 2 / Live Compressor (Sidechain) |
| Aux 1 | Sidechained Reverb Bloom (Send) | Huge stereo hall reverb (Valhalla VintageVerb or Lexicon 480): 3.0-4.0 s decay, 100% wet, high-passed at 300 Hz. **Crucial**: The reverb return is ducked 3-4 dB by the dry synth signal so the tail blooms into wide space only when chords release. | Valhalla VintageVerb / Live Hybrid Reverb |

### 2b. Sub-Bass & Kick Architecture (CONVENTION / FACT)

| Stage | Role | Target Settings / Typical Ranges | Reference Implementation |
|---|---|---|---|
| 1 | Infrasound High-Pass | High-pass filter at 28-30 Hz (steep 24 dB/oct) stripping subsonic energy and protecting subwoofer excursion. | FabFilter Pro-Q 3 / Live EQ Eight |
| 2 | Absolute Mono Locking | 100% Mono summing below 100-120 Hz. Crucial for club system playback to eliminate destructive acoustic phase cancellation across subwoofers. | Live Utility (Bass Mono enabled, 110 Hz) |
| 3 | Harmonic Generation | Parallel saturation or mild tube drive generating harmonics at 120-300 Hz so the sub-bass is easily audible on consumer phone speakers and small earbuds. | Soundtoys Decapitator / Live Saturator |
| 4 | Envelope Shaper Ducking | Dedicated volume envelope ducking sub-bass to -inf (total silence) during the initial 40-70 ms transient strike of the kick drum, avoiding phase smear and bass collisions. | Nicky Romero Kickstart 2 / Live Utility |

### 2c. Aggressive Bass & Dubstep Growls (CONVENTION / FACT)

- **Signal Path**: Wavetable FM synthesis (Serum / Massive) -> Multi-stage distortion (CamelCrusher or Ableton Saturator) -> Multiband OTT (Depth 50-70%, extreme upward compression bringing out metallic breath details) -> Post-filter surgical notch cuts taming ear-fatiguing whistles at 2.5-4 kHz.
- **Sub Isolation**: Sub-bass is completely filtered off the aggressive growl track below 90 Hz; a dedicated clean sine wave on a separate channel handles the 30-80 Hz sub foundation.

### 2d. Build-up & Transition FX (The Tension Engine) (CONVENTION / FACT)

1. **Automated DJ Filter Sweep**: Automated high-pass filter (FabFilter Volcano or Ableton Auto Filter) sweeping from 20 Hz up to 800-1200 Hz over the 8 or 16-bar riser, starving the track of bass before the drop.
2. **Washout Reverb/Delay**: 100% wet reverb and ping-pong delay return. Automation ramps send levels from -inf to 100% wet, followed by an abrupt, total silence cut 1 beat before the drop hits.
3. **Stereo Field Collapse**: Automated stereo imager narrowing the stereo field from 100% wide down to 25-30% (almost mono) in the final 2 bars of the build-up; when the drop strikes in full wide stereo, it hits with exponential perceived width and impact.

### 2e. EDM Master Bus & Club Loudness (-6 to -4 LUFS) (CONVENTION / FACT)

1. **Mid/Side Equalization**: Dangerous BAX EQ or Pro-Q 3: Low-pass the Side channel below 100 Hz (mono sub); boost Side channel at 10 kHz for stereo air; boost Mid channel at 50 Hz and 3 kHz for kick and vocal punch.
2. **VCA Glue Compressor**: SSL G-Master Bus / Live Glue Compressor: 2:1 ratio, 30 ms attack, auto release, 1 dB GR max (avoiding pumping).
3. **Transient Soft-Clipping**: Hard/soft clipper (StandardCLIP, Flatline, or T-RackS Clipper) shaving 1.5 to 3.0 dB off drum transient peaks. Shaving transients with a clipper preserves dynamic punch far better than limiters when driving tracks to extreme loudness.
4. **Aggressive True Peak Limiter**: FabFilter Pro-L 2 in Aggressive or Modern style (Lookahead 0.5 ms, attack fast), pushing integrated drop loudness to -6.0 to -4.5 LUFS while keeping true-peak ceiling at -0.5 dBTP.

---

## 3. Famous Named Record Profiles

### Luca Pretolesi: Major Lazer "Lean On" / Diplo / Steve Aoki (FACT)
- **Vocal & Lead Processing**: Pro-Q 3 (HPF at 160 Hz, notch at 400 Hz) -> Xfer OTT (Depth 30%, Time 100%) -> Saturn 2 (Warm Tube mid, Clean Tape high) -> bx_digital M/S widening -> VolumeShaper kick ducking.
- **Master Bus**: Dangerous BAX EQ -> Bettermaker Mastering Compressor (1.5:1, 1 dB GR) -> StandardCLIP (2 dB clipping on drop kicks) -> FabFilter Pro-L 2 (Modern style, -5.5 LUFS drop target).

### Mick Guzauski: Daft Punk "Random Access Memories" (FACT)
- **Vocoder & Synths**: Sennheiser VSM201 vocoder into Neve 88R console -> Urei 1176 (4:1, fast attack/release, 4-6 dB GR) -> GML 8200 EQ (+3 dB at 10 kHz) -> EMT 140 plate reverb.
- **Kick & Bass Fusion**: Acoustic kick drum blended with analog Minimoog sub-bass; sub-bass dynamic EQ dipped at 65 Hz during kick hit; bass locked strictly in mono.

### Skrillex & Steve Duda: The OTT Paradigm (FACT)
- **Sound Design Revolution**: Steve Duda and Skrillex established Xfer OTT (and its Ableton Multiband Dynamics parent preset) as the defining sound of modern electronic bass music, using heavy upward compression to extract high-frequency harmonics from heavily distorted wavetables.

### Martin Garrix: Festival Big Room Supersaws (FACT)
- **Chords Architecture**: Layered Sylenth1 / Serum supersaw oscillators -> HPF at 160 Hz -> Xfer OTT (30% Depth) -> Kickstart 2 sidechain ducking -> Valhalla VintageVerb (3.5 s decay, ducked 3 dB by dry chords).

---

## 4. EDM Conflicts & Open Engineering Debates

1. **Analog Sidechain Compression vs. Dedicated Volume Envelope Shaper**: Older producers used sidechain compressors triggered by the kick; modern EDM producers (Pretolesi, Garrix, Duda) universally reject audio-triggered sidechain compressors due to inconsistent transient response and lag, mandating mathematically exact volume envelope tools (Kickstart, VolumeShaper, LFO Tool).
2. **Streaming Loudness Penalties vs. Club System Realities**: Streaming services normalize music to -14 LUFS; however, commercial EDM producers continue mastering to -6 to -4 LUFS. In DJ sets and festivals, quiet tracks sound lifeless and thin compared to competitively loud productions; club systems rely on pre-master density.

---

## 5. Stock Ableton Live Device Mapping (Reference Preset)

- **EDM Supersaw Lead Rack**: `Audio Effect Rack` [EQ Eight (HPF 160 Hz, -3 dB at 450 Hz) -> Multiband Dynamics (Preset: OTT, Amount 35%) -> Saturator (Soft Sine, Drive +2 dB) -> Utility (Width 130%) -> Compressor (Sidechain enabled, keyed to Kick, Attack 0.5 ms, Release 60 ms) -> Delay (1/8d ping-pong)].
- **Club Sub-Bass Processor**: `Audio Effect Rack` [EQ Eight (HPF 28 Hz, LPF 100 Hz) -> Saturator (Warm Tube, Drive +2.5 dB, Output -2.5 dB) -> Utility (Bass Mono ON, Freq 115 Hz) -> Utility (Volume automated -inf on kick strikes)].
- **Tension Build-Up Washout**: Send Track [Auto Filter (HPF sweeping 20 Hz to 900 Hz) -> Hybrid Reverb (Hall, 4.0 s decay, 100% wet) -> Delay (Ping-Pong, 1/4 note, feedback 60%)].
- **EDM Master Bus**: `Audio Effect Rack` [Glue Compressor (2:1, Attack 30 ms, Release Auto, 1 dB GR) -> Saturator (Digital Clip, Output -0.3 dB, Drive +2 dB) -> Limiter (Gain +4 dB, Ceiling -0.5 dB)].
