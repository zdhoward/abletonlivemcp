# Audio Mixing Problems, Root Causes, and Targeted Solutions: raw evidence (collector track)

Collected 2026-11-10. Sourced from mixing engineering literature (Mixing Secrets for the Small Studio by Mike Senior, The Mixing Engineer's Handbook by Bobby Owsinski), Sound On Sound troubleshooting archives, and masterclass retrospectives from premier mixing engineers (Bob Power, Andy Wallace, Tchad Blake, Michael Brauer).
Evidence labels:
- **FACT** = Documented for a specific acoustic/psychoacoustic phenomenon, hardware circuit, or verified technical protocol.
- **CONVENTION** = Universally accepted standard across commercial mixing facilities.
- **OPINION** = Individual mixer philosophy or personal troubleshooting approach.

---

## 1. Low-End Masking, Mud, and Phase Conflict (20 Hz - 250 Hz)

### 1a. Kick and Bass Collision and Mud Buildup (CONVENTION / FACT)
- **Problem Symptoms**: Boomy, flabby low-end; kick drum lacks punch; bassline pitch is undefined; master bus headroom is eaten up without perceived loudness; sub-woofers distort.
- **Root Causes**:
  - Overlapping fundamental frequencies (e.g. both kick and bass peaking at 55 Hz).
  - Destructive phase cancellation at the zero-crossing between kick transient and bass waveform.
  - Sub-rumble buildup below 30 Hz from non-bass instruments (guitars, piano, vocal plosives, room rumble).
  - Uncontrolled low-frequency buildup on stereo reverb/delay tails.
- **The Destructive Blanket Fix (What NOT to do)**:
  - Applying steep 24 dB/octave high-pass filters at 100 Hz across every instrument track. Steep minimum-phase filters introduce severe phase rotation, ringing, and group delay, stripping the mix of its warm, acoustic body and causing low-mid hollowness.
- **Targeted Diagnostic & Treatment**:
  - *Assign Low-End Dominance*: Determine which element owns the sub-bass (30 - 65 Hz) and which owns the punch/chest (70 - 130 Hz). If 808/sub owns 35-55 Hz, tune kick punch to 65-90 Hz with high-pass on kick at 40 Hz.
  - *Dynamic EQ / Sidechain Carving*: Duck the bass fundamental by 2 to 4 dB *only* when the kick strikes, releasing within 50-100 ms so the bass body returns instantly.
  - *Abbey Road Reverb Filter*: High-pass all reverb and delay sends at 300 to 600 Hz to prevent low-end wash.

---

## 2. Midrange Boxiness, Congestion, and Masking (300 Hz - 1 kHz)

### 2a. The "Cardboard" Buildup and Vocal Drowning
- **Problem Symptoms**: Mix sounds congested, boxy, honky, and "cheap"; lead vocal struggles to stay on top of rhythm guitars and keyboards; muddy accumulation around 400 - 600 Hz.
- **Root Causes**:
  - Proximity effect on directional microphones (acoustic guitars, snare bottom, close vocal mics).
  - Multiple polyphonic chordal instruments (distorted rhythm guitars, electric piano, acoustic strums, synth pads) playing full-voiced triads in the same octave (C3 - C5).
  - Room reflections in untreated project studios accumulating between 300 and 700 Hz.
- **The Destructive Blanket Fix**:
  - Scooping out a massive wide notch at 500 Hz on every track. Stripping 500 Hz leaves the mix thin, weak, gutless, and fatiguing.
- **Targeted Diagnostic & Treatment**:
  - *Arrangement Pruning*: Mute or simplify rhythm guitar voicings during lead vocal phrases; transpose synth chords up an octave.
  - *Complementary Frequency Slotting*: If the lead vocal's body lives at 350-450 Hz, dip 400 Hz by 2-3 dB on rhythm guitars and piano; if acoustic guitar provides warmth at 250 Hz, leave it there and high-pass synth pads.
  - *Dynamic EQ on Busses*: Using a dynamic EQ on the rhythm instruments sidechained to the lead vocal, cutting 300-800 Hz by 1.5 - 3 dB only while the vocal is singing.

---

## 3. Harshness, Sibilance, and Ear Fatigue (2.5 kHz - 8 kHz)

### 3a. Brittle Highs, Vocal Spikes, and Distortion Fizz
- **Problem Symptoms**: Mix cannot be turned up without causing listener ear fatigue; vocal "S", "T", and "CH" consonants sting the ear; cymbals sound like harsh white noise; electric guitars have a persistent buzz/whistle.
- **Root Causes**:
  - Cheap condenser microphones with hyped capsule resonance peaks (+4 to +6 dB at 6-8 kHz).
  - Aggressive clipping or saturation applied after top-end EQ boosts.
  - Uncontrolled guitar amplifier speaker resonances (cabinet whistle between 2.8 and 4.2 kHz).
  - Vocal compression without prior de-essing: clamping a vocal pulls quiet sibilant tails up in level.
- **The Destructive Blanket Fix**:
  - Low-passing all high frequencies above 8 kHz (kills sparkle and air), or scooping 3 kHz broadly across the mix bus (destroys vocal intelligibility and snare snap).
- **Targeted Diagnostic & Treatment**:
  - *Pre-Compression De-Essing*: Place a split-band de-esser *before* heavy vocal compressors so consonants do not trigger aggressive gain reduction.
  - *Surgical Resonance Notching*: Use a high-Q parametric bell (Q 8 - 12) with a deep narrow cut (-4 to -6 dB) locked onto static cabinet whistle frequencies.
  - *Tape Emulation / Soft Clipping*: Analog tape saturation (e.g. Studer A800 / Live Saturator in Tape mode) naturally rounds off jagged high-frequency transients into warm, musical harmonics.

---

## 4. Lack of Punch, Flatness, and Over-Compression

### 4a. The Lifeless, Pumping Mix
- **Problem Symptoms**: Mix feels small, squashed, and flat; drum hits have no punch or initial impact; turn up the volume and the mix collapses into a wall of noise; unnatural breathing/pumping artifacts.
- **Root Causes**:
  - Compressor attack times set too fast (< 10 ms), instantly grabbing and crushing the drum's initial acoustic transient.
  - Stacking multiple aggressive compressors on individual tracks, subgroups, and master bus without monitoring total cumulative gain reduction.
  - Master bus limiter shaving off 6+ dB of dynamic crest factor.
- **The Destructive Blanket Fix**:
  - Slapping multiband compressors or more limiters onto the master bus to "glue" or fix the lack of energy.
- **Targeted Diagnostic & Treatment**:
  - *Slowing Down Attack Times*: Set compressor attack to 30 milliseconds on kick, snare, and drum bus to let the transient punch pass through unhindered before compression engages.
  - *Parallel Compression (The NYC Trick)*: Keep the dry drum tracks uncompressed or lightly controlled for maximum transient snap; blend in a heavily crushed parallel bus (1176 in All-Buttons mode or SSL Bus comp @ 10:1 ratio) 8-12 dB lower to add sustain and body without damaging the punch.
  - *Clip Gain Automation*: Manually automate clip gain or vocal faders on phrases before hitting the compressor, reducing the dynamic work the compressor must perform.

---

## 5. Stereo Smearing, Phase Cancellation, and Weak Center Image

### 5a. The "Hollow in Mono" Syndrome (FACT)
- **Problem Symptoms**: Mix sounds wide and exciting in stereo headphones, but when collapsed to mono or played on a smartphone/Bluetooth speaker, instruments disappear, vocals thin out, and the low-end vanishes.
- **Root Causes**:
  - Overuse of Haas-effect delays (< 30 ms delay between L and R channels) on mono sources.
  - Out-of-phase stereo widening plugins (micro-pitch shift, artificial phase inverters).
  - Multi-mic phase cancellation between drum overheads, snare top/bottom, and dual guitar mics.
- **The Destructive Blanket Fix**:
  - Applying stereo wideners to the master bus or panning sub-bass instruments wide.
- **Targeted Diagnostic & Treatment**:
  - *Mono Low-End Rule*: Force all audio below 100-120 Hz strictly to mono using utility plugins. Low frequencies have long wavelengths that cancel rapidly when out of phase.
  - *Sample-Level Time Alignment*: Zoom into multi-mic waveforms in the DAW audio editor and align transient peaks to within 0.1 milliseconds.
  - *Arrangement Panning*: Achieve wide stereo width by panning contrasting musical elements hard left and right (e.g. rhythm guitar 100% L, acoustic guitar/piano 100% R) rather than processing single mono tracks through phase wideners.
