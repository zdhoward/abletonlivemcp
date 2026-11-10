"""Compare RuleJudge and JevJudge on synthetic names. Labels were written by hand (see below).

Needs OPENROUTER_API_KEY. Makes one request per item (40 total). Prints only names and labels.
"""

from abletonlivemcp.judge import JudgeError
from abletonlivemcp.judge.jev import JevJudge
from abletonlivemcp.judge.rules import RuleJudge

# (file name, folders, one_shot expected, drum type expected or None)
SAMPLES = [
    ("Kick_Heavy_01.wav", ["Drums", "Kicks"], "yes", "kick"),
    ("BD 808 Long.wav", ["808s"], "yes", "kick"),
    ("Thump_03.wav", ["Kicks"], "yes", "kick"),
    ("SNR 03.wav", ["Snares"], "yes", "snare"),
    ("Rimshot Tight.wav", ["Drums"], "yes", "percussion"),
    ("Clap_Layered_02.wav", ["Claps"], "yes", "clap"),
    ("HH_Closed_07.wav", ["Hats"], "yes", "hat_closed"),
    ("OpenHat_12.wav", ["Hats"], "yes", "hat_open"),
    ("Tick_05.wav", ["Hats", "Closed"], "yes", "hat_closed"),
    ("Floor Tom 2.wav", ["Toms"], "yes", "tom"),
    ("Crash_Big.wav", ["Cymbals"], "yes", "cymbal"),
    ("Shaker_Loop_100bpm.wav", ["Percussion"], "no", None),
    ("Break 90bpm.wav", ["Breaks"], "no", None),
    ("Drum Loop 120 BPM.wav", ["Loops"], "no", None),
    ("Top_Loop_Dusty_128.wav", ["Loops"], "no", None),
    ("Pad_Warm_Cm.wav", ["Pads"], "yes", None),
    ("Bass_Reese_F.wav", ["Bass"], "yes", None),
    ("Vocal_Chop_Hey.wav", ["Vocals"], "yes", None),
    ("Riser_8bars.wav", ["FX"], "no", None),
    ("Texture_Rain.wav", ["Atmos"], "no", None),
    ("Fill_Snare_Roll.wav", ["Fills"], "no", None),
    ("random_texture.wav", [], "no", None),
    ("Perc_Bongo_Hi.wav", ["Percussion"], "yes", "percussion"),
    ("Kick Loop 4x4 124.wav", ["Loops"], "no", None),
    ("Sub_Drop_Impact.wav", ["FX"], "yes", None),
]
PLUGINS = [
    ("FabFilter Pro-Q 3", "eq"),
    ("Compressor", "compressor"),
    ("ValhallaVintageVerb", "reverb"),
    ("Nexus", "synth"),
    ("Limiter", "limiter"),
    ("Delay", "delay"),
    ("Reverb", "reverb"),
    ("Soundtoys Decapitator", "saturation"),
    ("Serum", "synth"),
    ("Kontakt", "sampler"),
    ("Pro-L 2", "limiter"),
    ("ShaperBox 3", "modulation"),
    ("Utility", "utility"),
    ("Kickstart 2", "compressor"),
    ("Mystery Box", None),
]


def run(judge):
    shot = drum = shot_n = drum_n = plug = fails = 0
    wrong = []
    for name, folders, e_shot, e_drum in SAMPLES:
        try:
            j = judge.classify_sample(name, folders)
        except JudgeError as exc:
            fails += 1
            wrong.append((name, f"ERROR {exc}"))
            continue
        shot_n += 1
        shot += j.one_shot == e_shot
        drum_n += 1
        drum += j.drum_type == e_drum
        if j.one_shot != e_shot or j.drum_type != e_drum:
            wrong.append((name, f"got {j.one_shot}/{j.drum_type} want {e_shot}/{e_drum}"))
    for name, e_cat in PLUGINS:
        try:
            p = judge.classify_plugin(name, "vst3")
        except JudgeError as exc:
            fails += 1
            wrong.append((name, f"ERROR {exc}"))
            continue
        plug += p.category == e_cat
        if p.category != e_cat:
            wrong.append((name, f"got {p.category} want {e_cat}"))
    print(
        f"{judge.name}: one_shot {shot}/{shot_n}, drum_type {drum}/{drum_n}, "
        f"plugin {plug}/{len(PLUGINS)}, errors {fails}"
    )
    for item in wrong:
        print("   miss:", *item)


run(RuleJudge())
run(JevJudge())
