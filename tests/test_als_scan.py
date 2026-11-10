"""Synthetic sample/schema and fault-tolerant project scan coverage."""

import gzip
from pathlib import Path

import pytest

from abletonlivemcp.als import scan, scan_projects
from abletonlivemcp.als.reader import AlsError, SampleRefUse, parse_xml_bytes, read_set
from abletonlivemcp.als.usage import find_sets


def summary(content: str):
    return parse_xml_bytes(f"<Ableton><LiveSet>{content}</LiveSet></Ableton>".encode())


def sample(path="C:/samples/kick.wav"):
    return f'<SampleRef><FileRef><Path Value="{path}"/></FileRef></SampleRef>'


def midi(pitch=36, attributes="", disabled="false"):
    return f"""<MidiClip><Disabled Value="{disabled}"/><Notes><KeyTracks><KeyTrack>
      <MidiKey Value="{pitch}"/><Notes><MidiNoteEvent {attributes}/></Notes>
    </KeyTrack></KeyTracks></Notes></MidiClip>"""


def track(content, name="Drums"):
    return f'<MidiTrack><Name><EffectiveName Value="{name}"/></Name>{content}</MidiTrack>'


def device(content, tag="OriginalSimpler"):
    return f"<DeviceChain><Devices><{tag}>{content}</{tag}></Devices></DeviceChain>"


def write_set(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(f"<Ableton><LiveSet>{content}</LiveSet></Ableton>".encode()))
    return path


@pytest.mark.parametrize(
    ("file_ref", "expected", "relative", "size"),
    [
        ('<Path Value="D:/loop.wav"/>', "D:/loop.wav", None, None),
        (
            '<RelativePath Value="Samples/Imported"/><Name Value="loop.wav"/>',
            "Samples/Imported/loop.wav", "Samples/Imported/loop.wav", 4096,
        ),
        (
            '<RelativePath><RelativePathElement Id="0" Dir="Samples"/>'
            '<RelativePathElement Id="1" Dir="Imported"/></RelativePath>'
            '<Name Value="loop.wav"/>',
            "Samples/Imported/loop.wav", "Samples/Imported/loop.wav", 4096,
        ),
        (
            '<RelativePath Value="Samples/loop.wav"/><Name Value="loop.wav"/>',
            "Samples/loop.wav", "Samples/loop.wav", 4096,
        ),
    ],
)
def test_audio_clip_sample_paths_and_size(file_ref, expected, relative, size):
    size_xml = '<OriginalFileSize Value="4096"/>' if size else ""
    content = f"<AudioClip><SampleRef><FileRef>{file_ref}</FileRef>{size_xml}</SampleRef>"
    s = summary(track(content + "</AudioClip>", "Audio"))
    assert s.samples == [SampleRefUse(expected, relative, "Audio", None, "referenced", size)]


@pytest.mark.parametrize("tag", ["OriginalSimpler", "Simpler", "DrumCell", "MultiSampler"])
@pytest.mark.parametrize(
    ("clip", "classification"),
    [
        ("", "potentially_triggered"),
        (midi(), "referenced"),
        (midi(attributes='IsEnabled="false"'), "potentially_triggered"),
        (midi(attributes='Velocity="0"'), "potentially_triggered"),
        (midi(disabled="true"), "potentially_triggered"),
        (midi(pitch="invalid"), "potentially_triggered"),
    ],
)
def test_sampler_classification(tag, clip, classification):
    s = summary(track(device(sample(), tag) + clip))
    assert s.samples[0].classification == classification
    assert s.samples[0].device_class == tag


def test_drum_pad_notes_match_only_the_corresponding_pad_and_track():
    pads = "".join(
        f'<DrumBranch><ZoneSettings><ReceivingNote Value="{pitch}"/></ZoneSettings>'
        f'{device(sample(f"{pitch}.wav"), "DrumCell")}</DrumBranch>'
        for pitch in [36, 38]
    )
    rack = device(f"<Branches>{pads}</Branches>", "DrumGroupDevice")
    s = summary(track(rack + midi(36)) + track(device(sample()), "Other"))
    assert [(r.path, r.classification) for r in s.samples] == [
        ("36.wav", "referenced"), ("38.wav", "potentially_triggered"),
        ("C:/samples/kick.wav", "potentially_triggered"),
    ]
    assert [r.track for r in s.samples] == ["Drums", "Drums", "Other"]


def test_empty_slots_ignored_and_invalid_size_is_optional():
    s = summary(track(device(
        '<SampleRef><FileRef/></SampleRef><SampleRef/>'
        '<SampleRef><FileRef><Name Value="kick.wav"/>'
        '<OriginalFileSize Value="unknown"/></FileRef></SampleRef>'
    )))
    assert len(s.samples) == 1
    assert s.samples[0].path == "kick.wav"
    assert s.samples[0].original_file_size is None
    assert SampleRefUse("kick.wav", None, None, None).classification == "referenced"


def test_scan_aggregates_instances_projects_formats_and_errors(tmp_path, monkeypatch):
    plugin = """<PluginDevice><PluginDesc><Vst3PluginInfo>
      <Name Value="Synth"/></Vst3PluginInfo></PluginDesc></PluginDevice>"""
    devices = f"<Devices><Reverb/><Reverb/>{plugin}</Devices>"
    content = track(devices + device(sample()) + device(sample()))
    write_set(tmp_path / "a.als", content)
    write_set(tmp_path / "Samples" / "b.ALS", content)
    write_set(tmp_path / "Backup" / "nested" / "ignored.als", content)
    write_set(tmp_path / "backup" / "ignored.als", content)
    denied = write_set(tmp_path / "denied.als", content)
    (tmp_path / "corrupt.als").write_bytes(b"not gzip")
    (tmp_path / "xml.als").write_bytes(gzip.compress(b"<broken>"))
    original_open = gzip.open

    def open_set(path, *args, **kwargs):
        if Path(path) == denied:
            raise PermissionError("synthetic unreadable file")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(gzip, "open", open_set)
    idx = scan_projects(tmp_path)
    assert idx.sets_scanned == 2
    assert {p.name for p, _ in idx.errors} == {"corrupt.als", "xml.als", "denied.als"}
    assert all(message for _, message in idx.errors)
    assert {c.key: (c.projects, c.instances) for c in idx.devices} == {
        "Reverb": (2, 4), "PluginDevice": (2, 2), "OriginalSimpler": (2, 4),
    }
    assert [(c.key, c.projects, c.instances) for c in idx.plugins] == [("vst3:Synth", 2, 2)]
    assert [(c.key, c.projects, c.instances) for c in idx.samples] == [
        ("C:/samples/kick.wav", 2, 4),
    ]
    assert scan(tmp_path) == idx
    assert find_sets(tmp_path / "Backup") == []


def test_corrupt_deflate_is_reported_as_als_error(tmp_path):
    path = tmp_path / "deflate.als"
    path.write_bytes(bytes.fromhex("1f8b0800000000000003") + b"\x07" * 20)
    with pytest.raises(AlsError, match="cannot read"):
        read_set(path)
    assert scan_projects(tmp_path).sets_scanned == 0
    assert len(scan_projects(tmp_path).errors) == 1
