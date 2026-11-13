"""Batch 3 host tools: argument forwarding to the bridge, refusals before any call, and the MIDI
file codec and roots (no Live)."""

import inspect

import pytest
from mcp.server.elicitation import AcceptedElicitation
from pydantic import TypeAdapter

from abletonlivemcp import midi_file, server
from abletonlivemcp.tools import arrangement, automation, clips, editing, files, notes


class Bridge:
    def __init__(self, replies=None):
        self.calls, self.replies = [], replies or {}

    def call(self, method, params=None):
        self.calls.append((method, params))
        if method == "ref_issue":
            refs = [
                {"kind": t["kind"], "ref": f"R{i}", "name": "n"}
                for i, t in enumerate(params["targets"])
            ]  # noqa: E501
            return {"generation": 5, "refs": refs}
        if method == "session_info":
            return {"generation": 5, "tempo": 120.0, "signature": [4, 4]}
        reply = self.replies.get(method, {"status": "complete"})
        return reply(params) if callable(reply) else reply

    def last(self):
        return self.calls[-1]


def call_args(tool, **kwargs):
    """Validate keyword arguments like the MCP layer does."""
    params = inspect.signature(tool.__wrapped__, eval_str=True).parameters
    return {k: TypeAdapter(params[k].annotation).validate_python(v) for k, v in kwargs.items()}


def call(tool, **kwargs):
    """Validate keyword arguments like the MCP layer does, then run the guarded tool."""
    return tool(**call_args(tool, **kwargs))


@pytest.fixture
def bridge(monkeypatch):
    fake = Bridge()
    monkeypatch.setattr(server, "_bridge", fake)
    monkeypatch.setattr(server, "_writable", lambda *_args: None)
    return fake


def test_create_clips_issues_slot_refs_and_forwards_fields(bridge):
    call(
        clips.live_create_clips,
        clips=[
            {
                "track": 0,
                "scene": 1,
                "length": 8,
                "notes": [{"pitch": 60, "start_time": 0, "duration": 1}],
            }
        ],
    )  # noqa: E501
    method, params = bridge.last()
    assert method == "create_clips"
    (t,) = params["targets"]
    assert t["ref"] == "R0" and t["length"] == 8 and t["notes"][0]["velocity"] == 100


def test_set_clips_addresses_session_and_arrangement_clips(bridge):
    call(
        clips.live_set_clips,
        targets=[
            {"clip": {"track": 0, "scene": 0}, "name": "A"},
            {"clip": {"track": 1, "arrangement": 2}, "loop": [0, 4]},
        ],
    )
    sent = bridge.calls[0][1]["targets"]
    assert [s["kind"] for s in sent] == ["clip", "arr_clip"]
    assert [t["kind"] for t in bridge.last()[1]["targets"]] == ["clip", "arr_clip"]


def test_edit_notes_forwards_every_edit_kind(bridge):
    call(
        notes.live_edit_notes,
        clip={"track": 0, "scene": 0},
        remove_ids=[3],
        modify=[{"note_id": 1, "probability": 0.5}],
        quantize={"grid": 0.25},
    )
    method, params = bridge.last()
    assert method == "edit_notes" and params["remove_ids"] == [3]
    assert params["modify"] == [{"note_id": 1, "probability": 0.5}]
    assert params["quantize"] == {"grid": 0.25, "amount": 1.0}


def test_get_notes_concise_drops_extended_fields(bridge):
    row = {
        "note_id": 1,
        "pitch": 60,
        "start_time": 0,
        "duration": 1,
        "velocity": 100,
        "mute": False,
        "probability": 1,
        "velocity_deviation": 0,
        "release_velocity": 64,
    }
    bridge.replies["get_notes"] = {"notes": [row], "total": 1, "cursor": None}
    out = call(notes.live_get_notes, clip={"track": 0, "scene": 0}, response_format="concise")
    assert "probability" not in out["notes"][0] and out["notes"][0]["note_id"] == 1


def test_cue_points_add_carries_the_generation(bridge):
    call(
        arrangement.live_set_cue_points,
        cues=[{"cue": 0, "action": "rename", "name": "A"}],
        add=[{"time": 16}],
    )
    method, params = bridge.last()
    assert method == "set_cue_points" and params["generation"] == 5
    assert params["cues"] == [{"cue": "R0", "action": "rename", "name": "A"}]


def test_arrangement_automation_refuses_before_any_call(bridge):
    with pytest.raises(Exception, match="unsupported"):
        call(
            automation.live_set_automation,
            targets=[
                {
                    "clip": {"track": 0, "arrangement": 0},
                    "parameter": {"mixer": "volume"},
                    "clear": True,
                }
            ],
        )
    assert not [c for c in bridge.calls if c[0] != "session_info"]


def test_set_automation_issues_clip_and_param_refs(bridge):
    call(
        automation.live_set_automation,
        targets=[
            {
                "clip": {"track": 0, "scene": 0},
                "parameter": {"device": [0], "parameter": 2},
                "ramps": [{"start": 0, "end": 4, "from": 0, "to": 1}],
            }
        ],
    )
    sels = bridge.calls[0][1]["targets"]
    assert [s["kind"] for s in sels] == ["clip", "param"] and sels[1]["parameter"] == 2
    (t,) = bridge.last()[1]["targets"]
    assert t["param"] == "R1" and t["param_kind"] == "param" and t["ramps"][0]["from"] == 0


def test_create_clips_if_exists_skip_leaves_occupied_slots_alone(bridge):
    bridge.replies["get_clips"] = {
        "clips": [{"track": 0, "scene": 0, "name": "old"}, {"track": 1, "scene": 0, "empty": True}]
    }
    out = call(
        clips.live_create_clips,
        clips=[{"track": 0, "scene": 0}, {"track": 1, "scene": 0}],
        if_exists="skip",
    )
    method, params = bridge.last()
    assert method == "create_clips" and len(params["targets"]) == 1
    assert out["skipped"] == [{"track": 0, "scene": 0}]


def test_create_clips_replace_writes_against_the_confirmed_occupant(bridge, monkeypatch):
    """R3: the write reuses the references the confirmation showed; none are issued after."""
    bridge.replies["get_clips"] = {"clips": [{"track": 0, "scene": 0, "name": "n", "length": 4}]}
    args = call_args(clips.live_create_clips, clips=[{"track": 0, "scene": 0}], if_exists="replace")
    with pytest.raises(server.ToolFailure, match="not_confirmed"):  # replace deletes: confirm
        clips.live_create_clips(**args)
    yes = AcceptedElicitation(data=server.Confirmation(confirm=True))
    with pytest.raises(server.ToolFailure, match="confirmation_stale"):  # nothing was shown
        clips.live_create_clips(**args, confirmation=yes)
    plan = server.PLANS["live_create_clips"](args)  # what the resolver reads before asking
    assert plan.lines == ["Session clip 'n' (length None beats) at track 0, scene 0"]
    shown = len(bridge.calls)
    clips.live_create_clips(
        **args,
        confirmation=yes,
        confirmation_plan=server._issue_approval("live_create_clips", args, plan),
    )
    assert [m for m, _ in bridge.calls[shown:]] == ["create_clips"]  # no new refs, no delete
    (target,) = bridge.last()[1]["targets"]
    assert target["replace"] is True and target["expect_clip"] == "R0"


def test_replace_into_empty_destinations_plans_no_deletes_and_creates(bridge):
    """Regression: with every destination empty the plan asked issue_refs([]) and refused."""
    bridge.replies["get_clips"] = {"clips": [{"track": 0, "scene": 0, "empty": True}]}
    args = call_args(clips.live_create_clips, clips=[{"track": 0, "scene": 0}], if_exists="replace")
    plan = server.PLANS["live_create_clips"](args)
    assert plan.lines == [] and plan.data["occupants"] == {}
    yes = AcceptedElicitation(data=server.Confirmation(confirm=True))
    clips.live_create_clips(
        **args,
        confirmation=yes,
        confirmation_plan=server._issue_approval("live_create_clips", args, plan),
    )
    (target,) = bridge.last()[1]["targets"]
    assert bridge.last()[0] == "create_clips" and "expect_clip" not in target

    bridge.replies["get_clips"] = {"clips": [{"track": 0, "scene": 0, "length": 4}]}
    bridge.replies["get_arrangement"] = {"tracks": [{"track": 0, "clips": []}]}
    args = call_args(
        arrangement.live_create_arrangement_clips,
        clips=[{"track": 0, "kind": "from_session", "scene": 0, "start": 8, "replace": True}],
    )
    plan = server.PLANS["live_create_arrangement_clips"](args)
    assert plan.lines == [] and plan.data["expect"] == [[]]


def test_automation_parameter_by_name_resolves_to_its_index(bridge):
    bridge.replies["device_parameters"] = [
        {"index": 0, "name": "Device On"},
        {"index": 1, "name": "Frequency"},
    ]
    call(
        automation.live_get_automation,
        clip={"track": 0, "scene": 0},
        parameter={"device": [1], "parameter": "frequency"},
    )
    method, params = bridge.last()
    assert method == "get_automation" and params["parameter"]["parameter"] == 1


def test_edit_audio_clip_forwards_markers(bridge):
    call(
        editing.live_edit_audio_clip,
        clip={"track": 1, "scene": 0},
        gain=0.5,
        warp_markers=[{"action": "remove", "beat_time": 4}],
    )
    method, params = bridge.last()
    assert method == "edit_audio_clip" and params["gain"] == 0.5
    assert params["warp_markers"] == [{"action": "remove", "beat_time": 4.0}]


# ---- MIDI files --------------------------------------------------------------------------------


def test_midi_codec_round_trip():
    src = [
        {"pitch": 60, "start_time": 0, "duration": 1, "velocity": 100},
        {"pitch": 64, "start_time": 0.5, "duration": 0.25, "velocity": 80},
    ]
    data = midi_file.encode(src, tempo_bpm=128, time_signature=(3, 4))
    back = midi_file.parse(data)
    assert [(n.pitch, n.start_time, n.duration, n.velocity) for n in back.notes] == [
        (60, 0.0, 1.0, 100),
        (64, 0.5, 0.25, 80),
    ]
    assert back.tempo_bpm == 128 and back.time_signature == (3, 4)


def test_midi_parse_rejects_garbage_and_truncation():
    with pytest.raises(midi_file.MidiFileError):
        midi_file.parse(b"not midi")
    with pytest.raises(midi_file.MidiFileError):
        midi_file.parse(midi_file.encode([{"pitch": 1, "start_time": 0, "duration": 1}])[:-6])


def test_file_roots_confine_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("ABLETONLIVEMCP_FILE_ROOTS", str(tmp_path))
    assert files.confined(str(tmp_path / "a.mid")) == (tmp_path / "a.mid").resolve()
    for bad in ("rel.mid", str(tmp_path / ".." / "x.mid"), str(tmp_path / "a.txt")):
        with pytest.raises(ValueError):
            files.confined(bad)


def test_export_then_import_round_trip(bridge, monkeypatch, tmp_path):
    monkeypatch.setenv("ABLETONLIVEMCP_FILE_ROOTS", str(tmp_path))
    row = {
        "note_id": 1,
        "pitch": 62,
        "start_time": 1.0,
        "duration": 0.5,
        "velocity": 90.0,
        "mute": False,
    }
    bridge.replies["get_notes"] = {"notes": [row], "total": 1, "cursor": None}
    out = call(files.live_export_midi, clip={"track": 0, "scene": 0}, file=str(tmp_path / "x.mid"))
    assert out["notes"] == 1
    with pytest.raises(Exception, match="new files only"):
        call(files.live_export_midi, clip={"track": 0, "scene": 0}, file=str(tmp_path / "x.mid"))
    call(files.live_import_midi, file=str(tmp_path / "x.mid"), track=0, scene=1)
    method, params = bridge.last()
    (t,) = params["targets"]
    assert method == "create_clips" and t["length"] == 4.0
    assert t["notes"] == [{"pitch": 62, "start_time": 1.0, "duration": 0.5, "velocity": 90.0}]


@pytest.mark.parametrize("change", ["none", "replace", "edit"])
def test_export_refuses_a_clip_changed_between_pages(bridge, monkeypatch, tmp_path, change):
    """N4 (round 6): export paged by address + offset, so a clip replaced or edited between
    pages became a hybrid file reported as success. The host tool now runs against the real
    remote get_notes; a change after page 1 refuses and no file is written."""
    import sys
    import types
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tests.test_batch3_dom import Clip, Note, Song, midi_clip

    from AbletonLiveMCP import handlers
    from AbletonLiveMCP.safety import Safety

    monkeypatch.setenv("ABLETONLIVEMCP_FILE_ROOTS", str(tmp_path))
    song = Song()
    clip = midi_clip(song)
    clip.notes = [Note(i, 60 + i % 12, i * 0.25, 0.2) for i in range(1, 1201)]  # 3 pages
    dispatch = handlers.make_dispatch(
        lambda: song, types.SimpleNamespace(), Safety(lambda: song, policy=lambda: False)
    )
    pages = []

    def get_notes(params):
        if len(pages) == 1 and change == "replace":
            song.tracks[0].clip_slots[0].clip = other = Clip(4.0)
            other.notes = list(clip.notes)  # same notes, another clip object
        elif len(pages) == 1 and change == "edit":
            clip.notes[1100].pitch = 30  # lands on the last page's snapshot, not its read
        pages.append(dispatch("get_notes", params))
        return pages[-1]

    bridge.replies["get_notes"] = get_notes
    target = tmp_path / "x.mid"
    if change == "none":
        out = call(files.live_export_midi, clip={"track": 0, "scene": 0}, file=str(target))
        assert out["notes"] == 1200 and target.exists() and len(pages) == 3
        assert sum(len(p["notes"]) for p in pages) == 1200
        return
    with pytest.raises(Exception, match="stale_cursor"):
        call(files.live_export_midi, clip={"track": 0, "scene": 0}, file=str(target))
    assert not target.exists()


def test_concise_clips_keep_arrangement_span_fields(bridge):
    arr = {"track": 0, "arrangement": 0, "name": "A", "length": 4, "start": 8, "end": 24}
    arr |= {"arrangement_length": 16, "looping": True}
    bridge.replies["get_clips"] = {"clips": [arr, {"track": 0, "scene": 0, "is_playing": False}]}
    rows = call(clips.live_get_clips, track=0)["data"]["clips"]
    assert rows[0]["end"] == 24 and rows[0]["arrangement_length"] == 16 and "looping" not in rows[0]
    assert "end" not in rows[1] and rows[1]["is_playing"] is False


def test_device_parameters_carry_the_device_header_and_tidy_display(bridge):
    from abletonlivemcp.tools import devices

    rows = [{"index": 0, "ref": "R", "name": "Drive", "display": " 4.00dB dB "}]
    rows += [{"index": 1, "name": "Rate", "display": "1/4 x"}]
    head = {"name": "Sat", "class_name": "Saturator", "type": "audio_effect"}
    bridge.replies["device_parameters"] = {"device": head, "parameters": rows}
    out = call(devices.live_get_device_parameters, track=0, path=[0])["data"]
    assert out["device"] == head and bridge.last()[1]["with_device"] is True
    assert [p["display"] for p in out["parameters"]] == ["4.00dB", "1/4 x"]
    assert devices.tidy_display("65.87% %") == "65.87%" and devices.tidy_display("x x") == "x x"
    bridge.replies["device_parameters"] = rows  # a Remote Script without with_device
    assert "device" not in call(devices.live_get_device_parameters, track=0, path=[0])["data"]
