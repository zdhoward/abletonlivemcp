# EDM MIDI FX and Programming Techniques: raw evidence (collector track)

Collected 2026-11-10. Sourced from electronic dance music sequencing manuals (Rick Snoman's Dance Music Manual), Sound On Sound EDM producer masterclasses, and synth sequencing documentation (Xfer Serum, Native Instruments Massive, Ableton Live 11/12 MIDI Tools).
Evidence labels:
- **FACT** = Documented for a specific synthesizer, sequencer manual, or technical masterclass.
- **CONVENTION** = Universally accepted electronic dance music sequencing standard.
- **OPINION** = Individual producer philosophy or personal production preference.

---

## 1. Arpeggiator Ostinatos and Synth Sequence Generation

### 1a. Arpeggiator Modes and Patterns (CONVENTION / FACT)
- **Pattern Types**:
  - Up / Down: Classic progressive house and trance (Deadmau5 "Strobe").
  - Converge / Diverge: Alternating outside notes moving inward towards the center.
  - Random / Euclidean: Tech-house and melodic techno generative lines.
- **Rate and Division**:
  - Straight 1/16th: Festival progressive house, trance, techno.
  - 1/16 Triplet (1/24) / Dotted 8th (1/8D): Psytrance rolling basslines and melodic techno.
- **Retrigger Modes**:
  - "Sync to Song Position": Ensures arpeggios stay locked to project bars regardless of when a key is pressed.
  - "Restart on Note": Restarts the arpeggio sequence from step 1 on every chord change for predictable impact.

### 1b. Note Length and Gate Automation in Build-Ups (FACT)
- **Gate Sweep**: Automating the Gate length parameter in Live's Arpeggiator:
  - Breakdown: 25% (short, percussive plucks with low filter cutoff).
  - Build-up (8 bars): Automated from 25% steadily up to 150% (swelling into continuous sustained wall of sound).
  - Pre-Drop Fill: Muted to 0%.
  - Drop: Snappy 75% gate.

---

## 2. Chord Stacking, Voicings, and Inversions

### 2a. Live Chord Device Stacking
- **Supersaw Chord Stacking**: Placing Live Chord MIDI FX before multi-oscillator detuned saw synths:
  - Shift 1: +7 semitones (5th)
  - Shift 2: +12 semitones (Octave)
  - Shift 3: +16 semitones (Major 3rd + Octave)
  - Shift 4: +19 semitones (5th + Octave)
  - Shift 5: +24 semitones (Double Octave)
- **Live 12 Invert & Span MIDI Transformers**: Dynamically spreading close-position chords across 3 to 4 octaves and cycling inversions in real-time.

---

## 3. Probability, Randomization, and Generative Techniques

### 3a. Live Note Probability and Chance (FACT)
- **Generative Hi-Hats and Percussion**: Assigning 65-80% probability to ghost hi-hats and percussion stabs, creating evolving non-repeating drum loops over 16-32 bar club arrangements.
- **Velocity Chance**: Assigning a velocity deviation range (e.g. 70 +/- 30) so each trigger possesses distinct velocity and filter envelope response.
- **Random MIDI Device for Acid / Techno Lead Lines**:
  - Setting Live Random effect to: Chance 30%, Choices 3, Scale +12 semitones. Generates sporadic, unexpected octave jumps during continuous 16th-note acid sequences (TB-303 style).

---

## 4. Pitch Automation, Risers, and Drop Fills

### 4a. Pitch Bend Automation for Build-Up Risers (CONVENTION / FACT)
- **Pitch Bend Range Configuration**: Adjusting synth pitch bend range to **+12 or +24 semitones**.
- **The Exponential Pitch Riser Curve**: Automating pitch bend from 0 up to +24 semitones across an 8-bar or 16-bar build-up, using an exponential upward curve where pitch acceleration matches accelerating snare roll subdivisions.
- **Portamento / Monophonic Glide on Bass Drops**: Setting glide time to 60 - 100 ms to create sliding drop riffs in bass house and future bass.
