# Hip Hop MIDI FX and Programming Techniques (knowledge page)

Synthesized from `research/raw/2026-11-10-hip-hop-midi-fx.md` and verified against modern trap production masterclasses (Metro Boomin, Mike Dean, Southside), MPC sequencing archives, and FL Studio/Ableton Live beatmaking workflows.

Related pages: [hip-hop](hip-hop.md), [hip-hop-songwriting-production](hip-hop-songwriting-production.md), [drums](drums.md), [vocals](vocals.md).

---

## 1. Scope and how to read this page

- Covers trap hi-hat rolls/ratchets, 808 legato glides and pitch slides, half-time snare/clap placement, chord triggering devices, and scale-locking workflows for boom-bap, modern trap, and UK/NY drill.
- Evidence labels:
  - **FACT** = Documented for a specific DAW device, sampler specification, or technical masterclass.
  - **CONVENTION** = Universally accepted hip hop and trap MIDI sequencing standard.
  - **OPINION** = Individual producer philosophy or personal production preference.

---

## 2. Trap Hi-Hat Sequencing, Rolls, and Ratchets

### 2a. Subdivision Switching and Micro-Grid Ratchets (CONVENTION / FACT)
- **Base Grid**: Continuous straight 8th or 16th notes at moderate velocity (85 - 100).
- **Subdivision Bursts**:
  - 1/32 Notes: Standard rhythmic roll leading into beats 2 and 4.
  - 1/32 Triplets (1/48 Notes): High-speed stutter roll.
  - 1/64 Notes: Hyper-speed drill and modern trap machine-gun burst.
- **Ableton Live 12 Tools**: Use the **Slice** and **Ornament** MIDI Tools to subdivide single sustained notes into geometric ratchets and pitch-gliding ornaments.

### 2b. Pitch Automation and Velocity Ramps
- **Downward Pitch Glides**: Automate pitch downward across a roll by 2 to 7 semitones (or use Live's Pitch device). Creates a falling sweep that directs the ear into the snare hit.
- **Velocity Ramping Profiles**:
  - Decrescendo Roll: Starts at velocity 115, decaying smoothly to 40.
  - Swell Roll (Crescendo): Starts at velocity 35, rising aggressively to 120 directly before beat 3.
  - Alternating Accent: Downbeat 100, offbeat 70.
- **Stereo Panning Rolls**: Automate MIDI Pan or use Live's Note Expression to sweep hi-hat rolls across the stereo field (40% L to 40% R).

---

## 3. 808 Bass MIDI Programming and Pitch Slides

### 3a. Monophonic Legato and Portamento Glides (FACT / CONVENTION)
- **Monophonic Voice Limit**: Set 808 sampler voice allocation strictly to **1 Voice** to prevent low-end phase cancellations and muddy frequency collisions.
- **Glide / Portamento Time**: Set to 60 - 140 ms in Legato mode.
- **Overlapping Notes for Slides**: Extending Note A so it overlaps the beginning of Note B by 15-30 ms causes the pitch to glide smoothly from Note A to Note B without retriggering the transient click.

### 3b. Drill and Trap Octave Jumps and Slide Fills (FACT)
- **Root-to-Octave Jump**: Play the sub-bass root note (e.g. C1 @ 32.7 Hz), followed by a short overlapping 16th note an octave higher (C2 @ 65.4 Hz) or a fifth higher (G1), creating a sliding siren effect.
- **Syncopated End-of-Bar Slides**: In UK and NY Drill, 808 slides are placed on the syncopated offbeats of bars 2 and 4 (the "and" of beat 4), sweeping up to semitones +12, +14, or +19.

---

## 4. Snare, Clap, and Percussion MIDI Techniques

### 4a. The Half-Time Backbeat (Beat 3)
- In modern trap (130 - 160 BPM DAW tempo), the primary snare or clap lands strictly on **Beat 3** (the half-time backbeat).
- **Pre-Shifted Claps**: Nudge the MIDI clap note 10 to 20 ms *ahead* of the grid (early) or layer a pre-shifted ghost clap to create a relaxed, wide impact.
- **Pitch-Dropping Trap Snare Fills**: Sequence a 3-to-5 hit snare roll at the end of every 8 bars where each hit drops 1-2 semitones in pitch and scales downward in velocity.

---

## 5. Harmonic MIDI Tools: Chord, Scale, and Random

### 5a. Ableton Live Chord Device for One-Finger Jazz Chords (FACT)
- Insert Live Chord MIDI device before a vintage electric piano or synth pad:
  - Shift 1: +3 semitones (Minor 3rd)
  - Shift 2: +7 semitones (Perfect 5th)
  - Shift 3: +10 semitones (Minor 7th)
  - Shift 4: +14 semitones (Major 9th)
- Playing a single root key triggers full, soulful neo-soul / boom-bap chord voicings.

### 5b. Scale Device Locking
- Set Live Scale device to **Phrygian**, **Minor Pentatonic**, or **Harmonic Minor** to guarantee that every MIDI pad or generated melody conforms strictly to dark trap tonalities.

---

## 6. Hip Hop MIDI Implementation Matrix

| Element | MIDI Devices / Tools | Velocity Strategy | Subdivision / Timing | Pitch / Modulation |
|---|---|---|---|---|
| **Trap Hi-Hats** | Live 12 Slice / Note Length | Dynamic ramps (40 to 120) | 1/16, 1/32, 1/32T, 1/64 rolls | Pitch drop -2 to -7 semitones |
| **808 Bass** | Simpler (1 Voice, Legato Glide) | Constant high velocity (115-127)| Straight syncopated 8ths | Portamento slide (60-140 ms) |
| **Trap Clap/Snare**| Velocity (Fixed @ 120) | Velocity 120-125 | Strictly Beat 3 (half-time) | Nudged 10-15 ms early |
| **Chords/Samples**| Live Chord + Scale Device | Velocity 80-95 | 2-bar or 4-bar sustained loops| Pitch-shifted down 2-5 st |
| **Boom-Bap Drums**| Live Groove Pool (MPC 58% Swing)| Varied dynamics (60 to 115) | 16th swing + unquantized drift | Subtle pitch tuning per pad |
