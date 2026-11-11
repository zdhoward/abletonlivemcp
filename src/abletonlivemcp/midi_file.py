"""Bounded Standard MIDI File codec (pure Python): read notes from SMF 0/1, write SMF 0.

Only what clip import/export needs: note on/off pairs, tempo and time signature meta events.
Every size is bounded (file bytes, tracks, events, notes) so a hostile file costs little.
Times are in beats (quarter notes); velocity 1..127.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

MAX_BYTES = 4 * 1024 * 1024
MAX_TRACKS = 64
MAX_EVENTS = 200_000
MAX_NOTES = 2000
DEFAULT_PPQ = 480


class MidiFileError(ValueError):
    pass


@dataclass
class MidiNote:
    pitch: int
    start_time: float
    duration: float
    velocity: int
    channel: int = 0


@dataclass
class MidiContent:
    ppq: int
    notes: list[MidiNote]
    tempo_bpm: float | None = None
    time_signature: tuple[int, int] | None = None
    tracks: int = 1
    format: int = 0
    truncated: bool = False


def _vlq(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    for _ in range(4):
        if pos >= len(data):
            raise MidiFileError("truncated variable-length value")
        b = data[pos]
        pos += 1
        value = (value << 7) | (b & 0x7F)
        if not b & 0x80:
            return value, pos
    raise MidiFileError("variable-length value longer than 4 bytes")


def _write_vlq(value: int) -> bytes:
    if not 0 <= value <= 0x0FFFFFFF:
        raise MidiFileError(f"delta time {value} out of range")
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.append(0x80 | (value & 0x7F))
        value >>= 7
    return bytes(reversed(out))


def _chunks(data: bytes):
    pos = 0
    while pos + 8 <= len(data):
        kind, size = data[pos : pos + 4], struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        if pos + size > len(data):
            raise MidiFileError(f"chunk {kind!r} runs past the end of the file")
        yield kind, data[pos : pos + size]
        pos += size


def parse(data: bytes) -> MidiContent:
    """Notes (sorted by time, pitch) from an SMF 0 or 1 byte string. Raises MidiFileError."""
    if len(data) > MAX_BYTES:
        raise MidiFileError(f"file larger than {MAX_BYTES} bytes")
    chunks = list(_chunks(data))
    if not chunks or chunks[0][0] != b"MThd" or len(chunks[0][1]) < 6:
        raise MidiFileError("not a Standard MIDI File (no MThd header)")
    fmt, ntracks, division = struct.unpack(">HHH", chunks[0][1][:6])
    if fmt not in (0, 1):
        raise MidiFileError(f"SMF format {fmt} is not supported (0 or 1 only)")
    if division & 0x8000 or division == 0:
        raise MidiFileError("SMPTE time division is not supported")
    tracks = [body for kind, body in chunks[1:] if kind == b"MTrk"]
    if len(tracks) > MAX_TRACKS:
        raise MidiFileError(f"more than {MAX_TRACKS} tracks")
    content = MidiContent(ppq=division, notes=[], tracks=len(tracks), format=fmt)
    events = 0
    for body in tracks:
        events = _parse_track(body, content, events)
    content.notes.sort(key=lambda n: (n.start_time, n.pitch))
    if len(content.notes) > MAX_NOTES:
        content.notes, content.truncated = content.notes[:MAX_NOTES], True
    return content


def _parse_track(body: bytes, content: MidiContent, events: int) -> int:
    pos, tick, status = 0, 0, 0
    open_notes: dict[tuple[int, int], list[tuple[int, int]]] = {}
    ppq = content.ppq
    while pos < len(body):
        events += 1
        if events > MAX_EVENTS:
            raise MidiFileError(f"more than {MAX_EVENTS} events")
        delta, pos = _vlq(body, pos)
        tick += delta
        if pos >= len(body):
            raise MidiFileError("truncated event")
        byte = body[pos]
        if byte == 0xFF:  # meta
            if pos + 2 > len(body):
                raise MidiFileError("truncated meta event")
            mtype = body[pos + 1]
            size, pos = _vlq(body, pos + 2)
            payload = body[pos : pos + size]
            pos += size
            if mtype == 0x51 and len(payload) == 3 and content.tempo_bpm is None:
                content.tempo_bpm = round(60_000_000 / int.from_bytes(payload, "big"), 6)
            elif mtype == 0x58 and len(payload) >= 2 and content.time_signature is None:
                content.time_signature = (payload[0], 2 ** payload[1])
            elif mtype == 0x2F:
                break
            continue
        if byte in (0xF0, 0xF7):  # sysex
            size, pos = _vlq(body, pos + 1)
            pos += size
            continue
        if byte & 0x80:
            status, pos = byte, pos + 1
        elif not status:
            raise MidiFileError("running status without a previous status byte")
        kind, channel = status & 0xF0, status & 0x0F
        width = 1 if kind in (0xC0, 0xD0) else 2
        if pos + width > len(body):
            raise MidiFileError("truncated channel event")
        args = body[pos : pos + width]
        pos += width
        if kind == 0x90 and args[1] > 0:
            open_notes.setdefault((channel, args[0]), []).append((tick, args[1]))
        elif kind == 0x80 or (kind == 0x90 and args[1] == 0):
            stack = open_notes.get((channel, args[0]))
            if stack:
                start, vel = stack.pop(0)
                if tick > start:
                    content.notes.append(
                        MidiNote(args[0], start / ppq, (tick - start) / ppq, vel, channel)
                    )
    return events


def encode(
    notes: list[MidiNote] | list[dict],
    ppq: int = DEFAULT_PPQ,
    tempo_bpm: float | None = None,
    time_signature: tuple[int, int] | None = None,
) -> bytes:
    """An SMF 0 file holding ``notes`` (dicts or MidiNote; start_time/duration in beats)."""
    if len(notes) > MAX_NOTES:
        raise MidiFileError(f"at most {MAX_NOTES} notes")
    if not 24 <= ppq <= 9600:
        raise MidiFileError("ppq must be 24..9600")
    timed: list[tuple[int, int, bytes]] = []  # (tick, order, bytes): offs sort before ons
    for n in notes:
        n = n if isinstance(n, MidiNote) else _note(n)
        if not 0 <= n.pitch <= 127 or n.start_time < 0 or n.duration <= 0:
            raise MidiFileError(f"invalid note {n}")
        ch = n.channel & 0x0F
        vel = max(1, min(127, round(n.velocity)))
        on = round(n.start_time * ppq)
        off = max(on + 1, round((n.start_time + n.duration) * ppq))
        timed.append((on, 1, bytes((0x90 | ch, n.pitch, vel))))
        timed.append((off, 0, bytes((0x80 | ch, n.pitch, 0))))
    timed.sort(key=lambda e: (e[0], e[1]))
    body = bytearray()
    if tempo_bpm:
        if not 1 <= tempo_bpm <= 999:
            raise MidiFileError("tempo_bpm must be 1..999")
        body += b"\x00\xff\x51\x03" + round(60_000_000 / tempo_bpm).to_bytes(3, "big")
    if time_signature:
        num, den = time_signature
        if not 1 <= num <= 99 or den not in (1, 2, 4, 8, 16, 32):
            raise MidiFileError("time_signature must be [1..99, power of two]")
        body += b"\x00\xff\x58\x04" + bytes((num, den.bit_length() - 1, 24, 8))
    last = 0
    for tick, _order, event in timed:
        body += _write_vlq(tick - last) + event
        last = tick
    body += b"\x00\xff\x2f\x00"
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, ppq)
    return header + b"MTrk" + struct.pack(">I", len(body)) + bytes(body)


def _note(d: dict) -> MidiNote:
    try:
        return MidiNote(
            int(d["pitch"]),
            float(d["start_time"]),
            float(d["duration"]),
            int(round(float(d.get("velocity", 100)))),
            int(d.get("channel", 0)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise MidiFileError(f"invalid note {d!r}: {exc}") from exc
