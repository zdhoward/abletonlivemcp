"""MCP server (stdio). Read-only tools only in v0.1."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from .als import read_set, scan_projects
from .bridge import BridgeClient

mcp = MCPServer("abletonlivemcp")
_bridge = BridgeClient()


@mcp.tool()
def live_hello() -> dict:
    """Handshake with Live: protocol version, Live version, and which APIs this Live supports."""
    return _bridge.call("hello")


@mcp.tool()
def live_session_info() -> dict:
    """Tempo, play state, time signature and track/return/scene counts of the open Set."""
    return _bridge.call("session_info")


@mcp.tool()
def live_tracks() -> list:
    """Every track in the open Set with its devices."""
    return _bridge.call("tracks")


@mcp.tool()
def live_browser_roots() -> list:
    """Browser categories available in this Live (instruments, audio_effects, drums, ...)."""
    return _bridge.call("browser_roots")


@mcp.tool()
def live_browser_list(root: str, path: list[str] | None = None) -> dict:
    """List the children of a browser folder. `path` is the folder names under `root`."""
    return _bridge.call("browser_list", {"root": root, "path": path or []})


@mcp.tool()
def live_browser_search(root: str, query: str, limit: int = 25) -> dict:
    """Search a browser category by name (bounded walk; check `budget_exhausted`)."""
    return _bridge.call("browser_search", {"root": root, "query": query, "limit": limit})


@mcp.tool()
def live_load_item(track: int, root: str, path: list[str]) -> dict:
    """Load a browser item onto a track. `path` must resolve to exactly one loadable item."""
    return _bridge.call("load_item", {"track": track, "root": root, "path": path})


@mcp.tool()
def live_device_parameters(track: int, device: int) -> list:
    """Name, value, range and display text of each parameter of a device."""
    return _bridge.call("device_parameters", {"track": track, "device": device})


@mcp.tool()
def live_set_device_parameter(track: int, device: int, parameter: int, value: float) -> dict:
    """Set one device parameter (value in the parameter's own min..max). Returns the readback."""
    return _bridge.call(
        "set_device_parameter",
        {"track": track, "device": device, "parameter": parameter, "value": value},
    )


@mcp.tool()
def live_create_track(kind: str, index: int = -1) -> dict:
    """Create a 'midi' or 'audio' track at `index` (-1 = end)."""
    return _bridge.call("create_track", {"kind": kind, "index": index})


@mcp.tool()
def live_set_track_name(track: int, name: str) -> dict:
    """Rename a track."""
    return _bridge.call("set_track_name", {"track": track, "name": name})


@mcp.tool()
def live_set_track_color(track: int, color_index: int) -> dict:
    """Set a track's color by Live palette index."""
    return _bridge.call("set_track_color", {"track": track, "color_index": color_index})


@mcp.tool()
def live_set_tempo(bpm: float) -> dict:
    """Set the Set's tempo (20..999 BPM)."""
    return _bridge.call("set_tempo", {"bpm": bpm})


@mcp.tool()
def als_summary(path: str) -> dict:
    """Read a saved .als file offline (Live need not be running) and list tracks and devices."""
    s = read_set(path)
    return {
        "creator": s.creator,
        "tracks": s.tracks,
        "devices": [vars(d) for d in s.devices],
        "samples": [str(x) for x in s.samples],
    }


@mcp.tool()
def als_usage_index(root: str) -> dict:
    """Scan every saved Set under `root` (skipping Backup folders) and count device, plugin and
    sample usage across projects. Read-only; Live need not be running."""
    return asdict(scan_projects(Path(root)))


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
