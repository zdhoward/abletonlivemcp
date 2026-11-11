"""MCP server (stdio) for the Live bridge: a small, honest core.

Only tools the Remote Script can execute safely are registered. Offline readers, the knowledge
base, gear lookup and the judge backends are not imported here. Every mutation runs under one
lock, only when the shared config says ``"read_only": false`` (the Remote Script enforces the
same policy itself), names its targets by references read from Live, and treats a refusal reply
from the bridge as an error: nothing was written.

Names and text that come from Live or from a browser are wrapped as untrusted data.

This module holds the shared helpers (registration, bridge calls, settling, untrusted wrapping);
the tools themselves live in ``tools/<domain>.py`` and are re-exported here.
"""

from __future__ import annotations

import functools
import threading
import time

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from . import chain
from .bridge import BridgeClient, BridgeError
from .chain import ChainError, Refusal
from .config import ConfigError, load_config

mcp = MCPServer("abletonlivemcp")
_bridge = BridgeClient()
_plans = chain.PlanStore()
_mutation_lock = threading.Lock()
LOCK_WAIT = 5.0
SETTLE_SECONDS = 0.3  # Live applies play/stop/launch a tick after the call returns
LEASE_TTL = 60.0
WRITE_METHODS = {"load_item", "set_device_parameter", "set_device_parameters"}
_lease: str | None = None  # held only inside live_build_chain

READ = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)
CREATE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False
)
OVERWRITE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=False
)


class ToolFailure(ToolError, ValueError):
    """A refusal the client should read. The MCP library reports any other exception as a crash
    and withholds its text ("Error executing tool X"), so a refusal must be a ToolError."""


def _explain(exc: Exception) -> str:
    """Stable `kind: message (outcome)` text; the client sees nothing else."""
    if isinstance(exc, Refusal):
        return f"refused:{exc.code}: {exc.message} (not applied)"
    if isinstance(exc, BridgeError):
        return str(exc)
    if isinstance(exc, ChainError):
        return f"invalid_plan: {exc} (not applied)"
    return f"invalid_request: {exc} (not applied)"


def _writable() -> None:
    """Host policy, aligned with the bridge: writes only when the config says read_only: false."""
    try:
        read_only = load_config().get("read_only") is not False
    except ConfigError:
        read_only = True
    if read_only:
        raise ToolFailure(
            "read_only: writes are disabled in the local bridge config; set read_only to false "
            "there to allow them (not applied)"
        )


def _register(fn, annotations: ToolAnnotations, mutation: bool):
    @functools.wraps(fn)
    def run(*args, **kwargs):
        try:
            if not mutation:
                return fn(*args, **kwargs)
            _writable()
            if not _mutation_lock.acquire(timeout=LOCK_WAIT):
                raise ToolFailure("busy: another mutation is running; retry later (not applied)")
            try:
                return fn(*args, **kwargs)
            finally:
                _mutation_lock.release()
        except ToolError:
            raise
        except (ValueError, BridgeError) as exc:  # ChainError and Refusal are ValueErrors
            raise ToolFailure(_explain(exc)) from exc

    return mcp.tool(annotations=annotations)(run)


def _read(fn):
    return _register(fn, READ, False)


def _create(fn):
    return _register(fn, CREATE, True)


def _overwrite(fn):
    return _register(fn, OVERWRITE, True)


def _call(method: str, params: dict | None = None):
    """One bridge call. The mutation lease rides on writes; a refusal reply raises Refusal."""
    if _lease is not None and method in WRITE_METHODS:
        params = {**(params or {}), "lease": _lease}
    return chain.checked(_bridge.call)(method, params)


def _untrusted(data):
    """Names and text from Live or the browser are data, never instructions."""
    return {"provenance": "live_object_text_untrusted", "data": data}


def _generation() -> int:
    return _call("session_info")["generation"]


def _row(method: str, index: int, what: str) -> dict:
    rows = _call(method)
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(rows):
        raise ValueError(f"{what} must be an index 0..{len(rows) - 1}")
    return rows[index]


def _slot(track: int, scene: int) -> dict:
    return _call("clip_slot", {"track": track, "scene": scene})


def _clip_ref(track: int, scene: int) -> str:
    slot = _slot(track, scene)
    if not slot["has_clip"]:
        raise ValueError("that clip slot is empty")
    return slot["clip"]


def _settled(method: str, params: dict, readback: str, readback_params: dict | None):
    """Run a command, wait for Live to apply it, then return the real state, not the stale one."""
    _call(method, params)
    time.sleep(SETTLE_SECONDS)
    return _call(readback, readback_params)


# ---- tools: registered by the modules in ``tools/`` (the helpers above must exist first) -----

from . import tools  # noqa: E402, F401 - registers every tool
from .tools.browser import (  # noqa: E402, F401 - re-exported: tests and scripts call these
    live_browser_list,
    live_browser_roots,
    live_browser_search,
    live_get_operation,
    live_load_item,
)
from .tools.chain import (  # noqa: E402, F401
    _preferences,
    live_build_chain,
    live_plan_chain,
    live_vocal_presets,
)
from .tools.clips import (  # noqa: E402, F401
    live_create_clip,
    live_fire_clip,
    live_get_clip,
    live_stop_clip,
)
from .tools.devices import live_device_parameters, live_set_device_parameters  # noqa: E402, F401
from .tools.notes import live_add_notes, live_get_notes  # noqa: E402, F401
from .tools.scenes import (  # noqa: E402, F401
    live_create_scene,
    live_fire_scene,
    live_list_scenes,
    live_set_scene_name,
)
from .tools.session import (  # noqa: E402, F401
    live_get_transport,
    live_hello,
    live_session_info,
    live_set_transport,
)
from .tools.tracks import live_create_track, live_set_track, live_tracks  # noqa: E402, F401


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    # `python -m abletonlivemcp.server` runs this file as `__main__`, but the tool modules
    # register on the importable `abletonlivemcp.server`, so run that module's server.
    from abletonlivemcp import server as _server

    _server.main()
