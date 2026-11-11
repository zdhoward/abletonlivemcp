# Mixing Diagnostics and Decision Frameworks (knowledge page)

Synthesized from `research/raw/2026-11-10-mixing-diagnostics-decision-frameworks.md` and verified against critical listening curricula, Sound On Sound "Mix Rescue" diagnostic methodologies, and masterclass protocols from premier mixing engineers (Bob Katz, Andrew Scheps, Sylvia Massy, Derek Ali).

Related pages: [busses-mixing](busses-mixing.md), [mastering](mastering.md), [producer-engineer-habits](producer-engineer-habits.md), [mixing-troubleshooting](mixing-troubleshooting.md).

---

## 1. Scope and how to read this page

- Provides a systematic, evidence-based diagnostic framework for analyzing audio mix problems objectively.
- Guides the mixer through the 4-tier escalation hierarchy (Arrangement -> Balance -> Frequency/Space -> Dynamics), preventing reflex "blanket fixes" and ensuring problems are resolved at the true root cause.
- Evidence labels:
  - **FACT** = Documented for a psychoacoustic law, acoustic measurement protocol, or verified diagnostic procedure.
  - **CONVENTION** = Universally accepted professional diagnostic framework.
  - **OPINION** = Individual mixer philosophy or personal listening habit.

---

## 2. The 4-Tier Diagnostic Escalation Hierarchy

### 2a. The "Root-Cause First" Escalation Ladder (CONVENTION / FACT)
When a mix problem is identified (e.g. "the lead vocal gets buried in the chorus"), inexperienced mixers reflexively reach for EQ or compression plugins. Professional diagnostic hierarchy resolves problems at the lowest possible tier before introducing signal processing:

```text
[ Tier 1: Arrangement & Composition ]
              │
              ▼ (If arrangement is clean, proceed to...)
[ Tier 2: Balance & Fader Levels ]
              │
              ▼ (If level adjustments alone cannot resolve, proceed to...)
[ Tier 3: Frequency & Space (EQ & Panning) ]
              │
              ▼ (If static separation still leaves dynamic inconsistency, proceed to...)
[ Tier 4: Dynamics & Nonlinear Processing (Compression / Saturation) ]
```

1. **Tier 1: Arrangement & Composition**: Is another instrument playing the same notes in the identical octave at the same instant?
   - *Action*: Mute competing layers, transpose keyboard voicings up an octave, or stagger rhythmic syncopation. Resolving conflicts in the arrangement fixes 80% of mix problems with zero audio degradation.
2. **Tier 2: Balance & Fader Levels**: Is the element simply 1.5 - 3 dB too quiet or too loud?
   - *Action*: Adjust the fader or draw volume automation. Never reach for an EQ or compressor to fix a level balance problem.
3. **Tier 3: Frequency & Space (EQ & Panning)**: Are two instruments sharing identical frequency space and panning position?
   - *Action*: Apply complementary EQ cuts (cutting the competing instrument, not boosting the desired one) and pan contrasting instruments away from each other.
4. **Tier 4: Dynamics & Nonlinear Processing (Compression / Saturation)**: Does the instrument have excessive dynamic range, causing it to disappear during quiet phrases and poke out during loud phrases?
   - *Action*: Apply fader riding, gentle optical leveling (LA-2A), parallel compression, or split-band de-essing.

---

## 3. Objective Diagnostic Testing Protocols

### 3a. The Level-Matched Bypass Test (The A/B Verification) (FACT)
- **The Loudness Illusion**: The human ear perceives louder audio as having superior punch, greater clarity, and crisper highs. If a plugin adds 1.0 dB of output gain, the mixer will instinctively believe the processing "improved" the sound, even if the plugin damaged the dynamics or introduced harsh distortion.
- **The Protocol**: Before declaring any processing step successful, match the plugin's output level so that toggling the bypass switch produces **zero difference in perceived volume**. If the processed signal does not sound clearly superior when level-matched, bypass and delete the plugin.

### 3b. The "In-Context" vs. "Solo" Diagnostic Rule (CONVENTION)
- **The Solo Trap**: EQing an acoustic guitar, bass, or snare drum in solo to make it sound "huge, warm, and massive" invariably creates an instrument that overloads the 200-500 Hz region and clashes with the rest of the mix.
- **The Protocol**: Make 90% of EQ, compression, and saturation adjustments **with the entire mix playing**. Solo should only be engaged for 5-10 seconds to locate clicks, pops, headphone bleed, or ground hum.

### 3c. Static vs. Dynamic Frequency Diagnosis
- **The Critical Question**: Is the frequency defect present **continuously** or **only during specific musical moments**?
  - *Static Problem*: Guitar cabinet speaker whistle (constant tone whenever notes sound); 60 Hz hum; microphone capsule resonance peak. -> **Treat with a narrow Static EQ notch or shelf**.
  - *Dynamic Problem*: Vocal proximity boom (occurs only when the singer leans into the mic on low notes); snare sibilance on crash hits; bass resonance on specific notes. -> **Treat with Dynamic EQ, Multiband Compression, or Automation**. (Applying a static EQ cut to a dynamic problem leaves the instrument hollow and thin when the problem note is not playing).

---

## 4. Common Blanket Fix Traps and What to Do Instead

### 4a. The Blanket High-Pass Filtering Trap (CONVENTION / FACT)
- **The Blanket Fix**: Automatically applying steep 24 dB/octave high-pass filters at 100 Hz across every channel in the session.
- **Why It Fails**: Steep minimum-phase filters introduce phase shift, group delay, and low-end ringing. Applying this across 40 tracks hollows out the 150-300 Hz region, leaving the mix sterile, thin, and brittle.
- **Targeted Alternative**: Use gentle 6 dB or 12 dB/octave filters only where unwanted sub-rumble exists (< 30 Hz on vocals, piano, acoustic guitars). Leave electric guitars and bass with their natural low-mid body intact.

### 4b. The High-Q Resonance Sweep Hunting Trap
- **The Blanket Fix**: Boosting a narrow parametric bell by +15 dB with high Q and sweeping across the spectrum hunting for "harsh" frequencies, then cutting wherever it sounds painful.
- **Why It Fails**: Boosting *any* frequency by +15 dB with a high Q creates an artificial resonant ringing artifact that was not originally audible. Cutting 6 to 8 notches across a track turns the EQ into a comb filter, destroying the instrument's natural harmonic structure.
- **Targeted Alternative**: Listen to the mix first without boosting. If a harsh frequency is genuinely offensive, identify it by ear, then apply a subtle, moderate-Q cut (-2 to -4 dB, Q 2.0 to 4.0).

---

## 5. Step-by-Step Diagnostic Decision Flowchart

```text
Step 1: Identify the Defect
  └── Example: "The lead vocal sounds buried during the chorus."
        │
Step 2: Isolate the Clashing Pair
  └── Mute instruments one by one until vocal clarity returns.
  └── Result: The rhythm electric guitars are masking the vocal.
        │
Step 3: Test Tier 1 (Arrangement)
  └── Can rhythm guitars play higher voicings or drop during vocal lines?
  └── If yes -> Problem solved with zero audio processing.
  └── If no -> Proceed to Step 4.
        │
Step 4: Test Tier 2 (Fader & Balance)
  └── Lower the rhythm guitar bus fader by 1.5 dB. Does the mix balance hold?
  └── If guitars now feel too quiet overall -> Proceed to Step 5.
        │
Step 5: Test Tier 3 (Frequency Slotting)
  └── Vocal body lives at 350-450 Hz, presence at 3 kHz.
  └── Cut 400 Hz by 2 dB and 3 kHz by 2 dB on rhythm guitars.
  └── Does the vocal sit cleanly now?
  └── If yes -> Verify with Level-Matched Bypass. Done.
  └── If conflict only occurs dynamically -> Proceed to Step 6.
        │
Step 6: Test Tier 4 (Dynamic Carving)
  └── Insert Dynamic EQ on guitar bus, sidechained to lead vocal.
  └── Duck 1-3 kHz by 2 dB only when vocal sings.
  └── Verify in Mono and Stereo. Problem solved surgically.
```

---

## 6. Diagnostic Decision Matrix

| Problem Identified | Tier 1 (Arrangement) | Tier 2 (Balance) | Tier 3 (Frequency/Space) | Tier 4 (Dynamics/Processing) |
|---|---|---|---|---|
| **Vocal masked by guitars** | Mute guitars during lines | Drop guitar fader -1.5 dB | Cut 400 Hz & 3 kHz on guitars | Dynamic EQ ducking guitars via vocal |
| **Kick and bass collision** | Transpose bass line octave | Adjust kick/bass relative faders| Slot frequencies (Kick 55 vs Bass 95)| Sidechain duck bass fundamental 3 dB |
| **Harsh cymbals & vocal** | Re-track with darker mic | Lower overhead faders | Cut 4-6 kHz on overheads | Pre-compression split-band de-esser |
| **Mix sounds muddy / boxy** | Thin out chord voicings | Lower pad / keyboard levels | Cut 300-500 Hz on rhythm bus | Dynamic EQ on low-mid buildup |
| **Loss of punch on drums** | Simplify kick/snare pattern | Raise drum bus fader | Boost transient click @ 3-5 kHz | Slow compressor attack to 30 ms; parallel crush |
| **Hollow in mono** | Pan contrasting parts | Center main elements | Narrow side frequencies below 120 Hz| Time-align multi-mic zero crossings |
