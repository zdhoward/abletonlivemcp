"""Tests use small SYNTHETIC XML mirroring the structure described in docs/research-deep-review.md.
Real Live files are needed to confirm the schema; see docs/validation.md."""

import gzip
from pathlib import Path

import pytest

from abletonlivemcp.als import AlsError, read_set, scan
from abletonlivemcp.als.reader import parse_xml_bytes

SET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Ableton MajorVersion="5" MinorVersion="12.0_12300" Creator="Ableton Live 12.4">
  <LiveSet>
    <Tracks>
      <MidiTrack>
        <Name><EffectiveName Value="Drums"/><UserName Value="Drums"/></Name>
        <DeviceChain><DeviceChain><Devices>
          <DrumGroupDevice>
            <Branches><DrumBranch><DeviceChain><DeviceChain><Devices>
              <OriginalSimpler>
                <Player><MultiSampleMap><SampleParts><MultiSamplePart>
                  <SampleRef><FileRef>
                    <RelativePath Value="Samples/kick.wav"/>
                    <Path Value="C:/lib/kick.wav"/>
                  </FileRef></SampleRef>
                </MultiSamplePart></SampleParts></MultiSampleMap></Player>
              </OriginalSimpler>
            </Devices></DeviceChain></DeviceChain></DrumBranch></Branches>
          </DrumGroupDevice>
        </Devices></DeviceChain></DeviceChain>
      </MidiTrack>
      <AudioTrack>
        <Name><EffectiveName Value="Vox"/><UserName Value=""/></Name>
        <DeviceChain><DeviceChain><Devices>
          <Reverb/>
          <PluginDevice><PluginDesc>
            <Vst3PluginInfo><Name Value="Pro-Q 3"/></Vst3PluginInfo>
          </PluginDesc></PluginDevice>
          <PluginDevice><PluginDesc>
            <VstPluginInfo><PlugName Value="Old Comp"/></VstPluginInfo>
          </PluginDesc></PluginDevice>
        </Devices></DeviceChain></DeviceChain>
      </AudioTrack>
    </Tracks>
  </LiveSet>
</Ableton>
"""


def write_set(path: Path, xml: str = SET_XML) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as fh:
        fh.write(xml.encode())
    return path


def test_reads_tracks_devices_plugins_samples(tmp_path):
    s = read_set(write_set(tmp_path / "a.als"))
    assert s.creator == "Ableton Live 12.4"
    assert s.tracks == ["Drums", "Vox"]
    classes = [d.device_class for d in s.devices]
    assert "DrumGroupDevice" in classes and "OriginalSimpler" in classes and "Reverb" in classes
    plugins = {(d.plugin_format, d.plugin_name) for d in s.devices if d.plugin_name}
    assert plugins == {("vst3", "Pro-Q 3"), ("vst2", "Old Comp")}
    assert len(s.samples) == 1
    sample = s.samples[0]
    assert sample.path == "C:/lib/kick.wav" and sample.track == "Drums"
    assert sample.device_class == "OriginalSimpler"


def test_rejects_entities():
    bad = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><Ableton><LiveSet/></Ableton>'
    with pytest.raises(AlsError):
        parse_xml_bytes(bad)


def test_rejects_non_set_and_non_gzip(tmp_path):
    with pytest.raises(AlsError):
        parse_xml_bytes(b"<Other/>")
    junk = tmp_path / "junk.als"
    junk.write_bytes(b"not gzip")
    with pytest.raises(AlsError):
        read_set(junk)


def test_scan_counts_projects_and_skips_backup(tmp_path):
    write_set(tmp_path / "one" / "one.als")
    write_set(tmp_path / "two" / "two.als")
    write_set(tmp_path / "two" / "Backup" / "two [2026-01-01].als")
    (tmp_path / "bad.als").write_bytes(b"nope")
    idx = scan(tmp_path)
    assert idx.sets_scanned == 2
    assert len(idx.errors) == 1
    reverb = next(c for c in idx.devices if c.key == "Reverb")
    assert (reverb.projects, reverb.instances) == (2, 2)
    assert idx.plugins[0].key.startswith(("vst3:", "vst2:"))
    assert idx.samples[0].key == "C:/lib/kick.wav"
