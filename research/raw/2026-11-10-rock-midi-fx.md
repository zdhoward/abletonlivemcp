# Rock MIDI FX and Programming Techniques: raw evidence (collector track)

Collected 2026-11-10. Sourced from virtual instrument programming manuals (Superior Drummer 3, Steven Slate Drums, Ample Guitar, Scarbee Bass), Sound On Sound MIDI sequencing archives, and rock producer masterclasses.
Evidence labels:
- **FACT** = Documented for a specific plugin specification, sampler engine, or verified score analysis.
- **CONVENTION** = Universally accepted standard across rock MIDI programming and mockups.
- **OPINION** = Individual producer philosophy or personal sequencing tip.

---

## 1. Drum Programming and Humanization Techniques

### 1a. Velocity Dynamics and Layering (CONVENTION / FACT)
- **Multi-Velocity Sample Switching**: Acoustic rock drum samplers (Superior Drummer 3, BFD3, Live Drum Rack with multi-velocity zones) feature up to 16-32 velocity layers. Static velocities (e.g. constant velocity 127) trigger the machine-gun effect.
- **Velocity Hierarchy by Drum Element**:
  - Downbeat Kick: Velocity 105 - 120. Weak beat kicks: Velocity 80 - 95. Ghost kicks: Velocity 45 - 65.
  - Primary Backbeat Snare (Beats 2 & 4): Velocity 110 - 125.
  - Ghost Snares: Velocity 30 - 55. Placed on sixteenth-note offbeats right before or after the main hit.
  - Snare Flams: Two hits separated by 15 - 30 milliseconds; primary hit at velocity 115, secondary lead hit at velocity 75 - 85.
  - Hi-Hat Accents: 8th-note pulse alternates strong/weak (e.g. 100 on the downbeat, 70-80 on the upbeat).
  - Open Hi-Hat Foot Chokes: High note duration cutoff or dedicated pedal choke note (MIDI note 44 foot close choked against open hat on note 46).
- **Ableton Live Velocity Device Configuration**:
  - Mode: Random. Random value: +/- 8 to 15. Range: 40 to 127.
  - Compand: Parabolic curve to expand or compress player dynamics.

### 1b. Micro-Timing and Pocket Offsets
- **Human Timing Drift vs. Hard Quantize (CONVENTION)**: 100% hard grid quantization strips rock feel. Applying 10-25% Groove Pool quantize or manual humanization with +/- 5 to 15 millisecond randomized timing offsets.
- **The Snare Drag**: Moving all backbeat snares 8 to 18 ms *late* relative to the kick drum downbeat to emulate heavy classic rock pocket (John Bonham feel).
- **The Punk / Metal Snare Rush**: Nudging snare hits 4 to 10 ms *early* ahead of the grid to impart adrenaline and forward drive.

---

## 2. Bass and Guitar MIDI Simulation

### 2a. Rock Bass Sequencing (CONVENTION / FACT)
- **Monophonic Legato and Note Overlap**: Overlapping bass MIDI notes by 5 to 20 ms to trigger legato slide and hammer-on/pull-off transitions in virtual bass engines (Trilian, Scarbee Pre-Bass, MODO Bass).
- **Keyswitch Articulations**:
  - Low MIDI keyswitches (C-1 to B-1) trigger finger vs. pick attack, palm mutes, dead notes, and fret slides.
  - Pitch Wheel slides: Full-step or octave pitch wheel automation simulating slides into root notes.

### 2b. Rock Rhythm Guitar Strumming and Voicings
- **Strum Timing Offset (The Strum Spread) (FACT)**: When a plectrum hits 6 strings, they do not sound simultaneously. A realistic downstroke spreads the 6 notes across 20 to 45 ms from low string to high string. An upstroke spreads notes in reverse order across 15 to 30 ms.
- **Ableton Live 12 Strum MIDI Tool**: Configured with positive slope for downstrokes (arpeggiating from low note to high note) and negative slope for upstrokes, with humanized velocity decay across the sweep.
- **Power Chord Voicing (Root - 5th - Octave)**: In rock MIDI sequencing, full 6-string barre chords through high-gain amp sims sound muddy. Sequencing simple 3-note power chord voicings (E2 - B2 - E3) preserves clarity and transient punch.

---

## 3. Keyboard, Organ, and Synth MIDI Techniques

### 3a. Hammond B3 Organ Emulation
- **Zero Velocity Sensitivity (FACT)**: Authentic tone-wheel organs (Hammond B3) are physically non-velocity sensitive. Velocity on organ tracks should be fixed (e.g. constant 100 or 127). Dynamics are controlled strictly via Volume / Expression Pedal (MIDI CC11).
- **Leslie Speed Switching**: Automating MIDI CC1 (Modulation Wheel) or CC64 (Sustain Pedal) between values 0 (Chorale / Slow) and 127 (Tremolo / Fast). Switching to fast right before chorus climaxes or during sustained chords.

### 3b. Piano Voicings and Sustain Pedal (CC64)
- **Sustain Pedal Automation (CC64)**: Clearing and retriggering CC64 on chord changes to prevent muddy acoustic resonance bleed.
- **Tenth Intervals in the Left Hand**: Sequencing wide tenths (Root + tenth / octave + 3rd) rather than dense root-position triads in the lower register.
