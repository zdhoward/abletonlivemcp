# EDM MIDI FX and Programming Techniques (knowledge page)

Synthesized from `research/raw/2026-11-10-edm-midi-fx.md` and verified against electronic dance music sequencing treatises (Dance Music Manual by Rick Snoman), Sound On Sound EDM masterclasses (Luca Pretolesi, Deadmau5, Steve Duda), and festival project stem breakdowns.

Related pages: [edm](edm.md), [edm-songwriting-production](edm-songwriting-production.md), [keys-synths](keys-synths.md), [drums](drums.md).

---

## 1. Scope and how to read this page

- Covers arpeggiator ostinatos, chord stacking and inversions, probability and generative tools, build-up pitch bend risers, portamento glides, and Live 12 MIDI Transformers across House, Techno, Dubstep, Trance, and Drum & Bass.
- Evidence labels:
  - **FACT** = Documented for a specific synthesizer, sequencer manual, or technical masterclass.
  - **CONVENTION** = Universally accepted electronic dance music sequencing standard.
  - **OPINION** = Individual producer philosophy or personal production preference.

---

## 2. Arpeggiator Ostinatos and Synth Sequence Generation

### 2a. Arpeggiator Modes and Patterns (CONVENTION / FACT)
- **Pattern Types**:
  - Up / Down: Classic progressive house and trance (Deadmau5 "Strobe").
  - Converge / Diverge: Outside notes moving progressively towards the center.
  - Random / Euclidean: Generative melodic techno and tech-house lines.
- **Rate and Division**:
  - Straight 1/16th: Festival progressive house, trance, techno.
  - 1/16 Triplet (1/24) / Dotted 8th (1/8D): Psytrance rolling basslines and melodic techno.
- **Retrigger Modes**:
  - "Sync to Song Position": Keeps the arpeggio locked to absolute project bars regardless of key trigger timing.
  - "Restart on Note": Restarts the sequence from step 1 on every chord change for punchy downbeat impact.

### 2b. Gate Length Automation in Build-Ups (FACT)
- Automate the Gate parameter in Live's Arpeggiator:
  - Breakdown: 25% (short, percussive plucks with low filter cutoff).
  - Build-up (8-16 bars): Automated smoothly from 25% up to 150% (swelling into continuous sustained wall of sound).
  - Pre-Drop Fill: Muted to 0%.
  - Drop: Snappy 75% gate.

---

## 3. Chord Stacking, Voicings, and Inversions

### 3a. Live Chord Device for Massive Supersaws (FACT)
- Place Live Chord MIDI FX before multi-oscillator detuned saw synths:
  - Shift 1: +7 semitones (Perfect 5th)
  - Shift 2: +12 semitones (Octave)
  - Shift 3: +16 semitones (Major 3rd + Octave)
  - Shift 4: +19 semitones (Perfect 5th + Octave)
  - Shift 5: +24 semitones (Double Octave)
- Playing a single root note triggers a full, 6-voice concert-grade supersaw chord across two octaves.

### 3b. Live 12 MIDI Transformers: Invert, Span, and Connect
- **Invert Tool**: Rotate chord inversions dynamically across bars while keeping root bass notes anchored.
- **Span Tool**: Spread close-position 3-note chords across 3 to 4 octaves to create sprawling trance pads.

---

## 4. Probability, Randomization, and Generative Techniques

### 4a. Live Note Probability and Chance (FACT)
- **Generative Hi-Hats & Percussion**: Assign 60% - 80% probability to ghost hi-hats, percussive bongo hits, and synth clicks to produce non-repeating evolving loops across 32-bar club sections.
- **Velocity Chance**: Assign a velocity deviation range (e.g. 80 +/- 25) so each trigger drives subtle variations in filter cutoff and envelope attack.
- **Random MIDI Device for Acid Lines (TB-303 Style)**:
  - Setting Live Random effect to: Chance 30%, Choices 3, Scale +12 semitones. Generates sporadic, unexpected octave jumps during continuous 16th-note acid sequences.

---

## 5. Pitch Automation, Risers, and Drop Fills

### 5a. Exponential Pitch Bend Automation (CONVENTION / FACT)
- **Pitch Bend Range**: Set synth pitch bend range to **+12 or +24 semitones**.
- **Exponential Riser Curve**: Automate pitch bend from 0 up to +24 semitones across an 8-bar or 16-bar build-up, using an upward exponential curve where pitch acceleration matches accelerating snare roll subdivisions.
- **Portamento / Monophonic Glide on Bass Drops**: Set synth glide time to 60 - 100 ms to create sliding drop riffs in bass house and future bass.

---

## 6. EDM MIDI Implementation Matrix

| Element | MIDI Devices / Tools | Velocity Strategy | Timing / Quantization | Pitch / Modulation |
|---|---|---|---|---|
| **Supersaw Leads** | Live Chord (+7, +12, +16, +19, +24)| Fixed velocity (115-125) | 100% rigid grid | Live 12 Span tool for spread |
| **Arp Sequences** | Live Arpeggiator (Gate Auto) | Constant 100 | Straight 1/16th or 1/8D | Gate automated 25% -> 150% |
| **Acid 303 Lines** | Live Random (+12 st @ 30%) | Accented notes 127, rest 85 | Continuous 16ths | Legato portamento glide |
| **Build-Up Risers**| Note Length + Pitch Automation| Rising crescendo (40 to 127) | Accelerating 1/4 -> 1/32 | Exponential pitch bend +24 st |
| **Club Percussion**| Live Note Probability (65-80%) | Velocity Chance +/- 20 | Micro-quantize / 56% swing | Subtle sample pitch transpose |
