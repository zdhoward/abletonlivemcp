# Hip Hop MIDI FX and Programming Techniques: raw evidence (collector track)

Collected 2026-11-10. Sourced from MPC sequencing literature, FL Studio trap workflow archives, Sound On Sound producer interviews (Metro Boomin, Mike Dean, Southside), and modern beatmaking documentation.
Evidence labels:
- **FACT** = Documented for a specific hardware sampler, DAW device, or technical masterclass.
- **CONVENTION** = Universally accepted hip hop and trap MIDI programming convention.
- **OPINION** = Individual producer philosophy or personal production preference.

---

## 1. Trap Hi-Hat Sequencing, Rolls, and Ratchets

### 1a. Subdivision Switching and Pitch Automation (CONVENTION / FACT)
- **Repeating Subdivisions**: The basic trap hi-hat line runs on continuous straight 8th or 16th notes, punctuated by sudden bursts of micro-subdivisions:
  - 1/32 notes (standard roll)
  - 1/32 triplets (1/48 notes - fast stutter)
  - 1/64 notes (high-speed machine-gun drill roll)
- **Pitch Glide Automation**: Automating pitch of the hi-hat roll downward by 2 to 7 semitones (or using Live's Pitch MIDI FX / note transpose) across the roll, creating a falling sweep into the snare hit.
- **Velocity Ramping**: Automating velocity curves:
  - Decaying roll: Starting at velocity 110 and fading down to 40.
  - Crescendo roll: Swelling from velocity 30 up to 120 directly before beat 3.
  - Alternating accent: Velocity 100 on on-beat, 65 on off-beat.
- **Live 12 Slice & Ornament MIDI Tools**: Automatically segmenting sustained notes into geometric ratchets and pitch-gliding ornaments.

---

## 2. 808 Bass MIDI Programming and Pitch Slides

### 2a. Monophonic Legato and Portamento Glides (FACT / CONVENTION)
- **Monophonic Voice Mode**: 808 samplers (Live Simpler in 1-voice mode) must have polyphony set strictly to **1 Voice** to prevent muddy low-frequency overlapping notes.
- **Glide / Portamento Time**: Set to 50 - 150 ms (or Glide Mode set to Legato).
- **Overlapping Notes for Slides**: When note B overlaps note A, the pitch smoothly glides from note A to note B without retriggering the transient click.
- **Octave Jumps and Slide Fills (UK/NY Drill & Trap)**:
  - Playing the root sub-note in the low octave (C1 @ 32.7 Hz), then placing a short overlapping 16th note an octave higher (C2 @ 65.4 Hz) or 19 semitones higher (G2), with portamento creating a sweeping siren glide.
  - Drill 808 pitch slides frequently sweep up to the 5th, 7th, or octave on syncopated offbeats ("and" of beat 4).

---

## 3. Snare, Clap, and Percussion MIDI Techniques

### 3a. Snare Fills and Pitch Drops
- **The Half-Time Backbeat**: Snare or clap locked strictly on **Beat 3** (in 140 BPM DAW tempo).
- **Pitch-Dropping Trap Snare Fills**: A 3-to-5 hit snare roll at the end of every 8 bars where each hit drops 1-2 semitones in pitch and lowers in velocity, clearing the frequency spectrum for the return of the hook.
- **Pre-Shifted Claps**: Nudging the MIDI clap note 10 to 20 ms ahead of the grid (or layering a pre-shifted ghost clap) to create a relaxed, wide impact.

---

## 4. Melodic MIDI Tools: Chord, Scale, and Random

### 4a. Ableton Live Chord and Scale Device Workflows
- **One-Finger Jazz Chords**: Inserting the Live Chord device before a rhodes or synth pad:
  - Shift 1: +3 semitones (minor 3rd)
  - Shift 2: +7 semitones (perfect 5th)
  - Shift 3: +10 semitones (minor 7th)
  - Shift 4: +14 semitones (major 9th)
- **Scale Device Locking**: Setting Live Scale device to Minor Pentatonic, Phrygian, or Harmonic Minor so every incoming key triggers in-key menacing trap melodies.
- **MPC 16-Levels Emulation**: Pitching a single vocal chop or drum sample across 16 velocity or pitch increments.
