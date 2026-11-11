"""T-005: one check of the new reference kinds (the proof is scripts/live_refs_test.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))

from AbletonLiveMCP.dom_common import Refused, reference_nodes  # noqa: E402
from AbletonLiveMCP.safety import Safety  # noqa: E402


class Obj:  # identity equality, unlike SimpleNamespace
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _mixer(sends):
    return Obj(sends=sends, volume=Obj(name="Volume"), panning=Obj(name="Pan"))


def test_new_kinds_validate_then_refuse_after_reorder_delete_and_set_change():
    sim = Obj(class_name="OriginalSimpler", name="Kick", parameters=[])
    pad_chain = Obj(devices=[sim], mixer_device=_mixer([]))
    pad = Obj(note=36, chains=[pad_chain])
    pads = [Obj(note=35, chains=[]), pad]
    kit = Obj(class_name="DrumGroupDevice", can_have_drum_pads=True, drum_pads=pads)
    track = Obj(
        devices=[kit], take_lanes=[Obj(arrangement_clips=[])], mixer_device=_mixer([Obj(), Obj()])
    )
    returns = [Obj(mixer_device=_mixer([])), Obj(mixer_device=_mixer([]))]
    song = Obj(tracks=[track], return_tracks=returns, master_track=Obj(), scenes=[], cue_points=[])
    safe = Safety(lambda: song, policy=lambda: False)

    def ref(**sel):
        return safe.issue(*reference_nodes(song, sel))

    def ok(kind, r):
        try:
            safe.resolve(kind, r, song)
            return True
        except Refused:
            return False

    refs = {
        "device": ref(kind="device", track=0, path=[0, "pad:36", 0]),
        "drum_pad": ref(kind="drum_pad", track=0, path=[0, "pad:36"]),
        "mixer_param": ref(kind="mixer_param", track=0, role="send", send=1),
        "return_track": ref(kind="return_track", track="return:1"),
        "master": ref(kind="master", track="master"),
        "take_lane": ref(kind="take_lane", track=0, take_lane=0),
    }
    assert all(ok(k, r) for k, r in refs.items())
    assert not ok("track", refs["master"])  # wrong kind

    pad_chain.devices.insert(0, Obj(class_name="Reverb"))  # reorder inside the pad's chain
    pad.chains.append(Obj())  # pad layout changed
    del returns[0], track.mixer_device.sends[0]  # a return deleted: sends shift
    assert not any(ok(k, refs[k]) for k in ("device", "drum_pad", "mixer_param", "return_track"))

    safe.invalidate()  # Set change
    assert not ok("master", refs["master"]) and not ok("take_lane", refs["take_lane"])
