"""Client for the Remote Script bridge (loopback TCP, newline-framed JSON)."""

from __future__ import annotations

import itertools
import json
import socket
from typing import Any

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9877


class BridgeError(Exception):
    """The bridge answered with an error, or could not be reached."""

    def __init__(self, kind: str, message: str):
        super().__init__(f"{kind}: {message}")
        self.kind = kind


class BridgeClient:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 15.0):
        self._addr = (host, port)
        self._timeout = timeout
        self._ids = itertools.count(1)

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        rid = next(self._ids)
        payload = {"id": rid, "method": method, "params": params or {}}
        try:
            with socket.create_connection(self._addr, timeout=self._timeout) as conn:
                conn.sendall(json.dumps(payload).encode("utf-8") + b"\n")
                buf = b""
                while b"\n" not in buf:
                    chunk = conn.recv(65536)
                    if not chunk:
                        raise BridgeError("ConnectionClosed", "bridge closed the connection")
                    buf += chunk
        except OSError as exc:
            raise BridgeError(
                "Unreachable",
                f"cannot reach Live bridge at {self._addr[0]}:{self._addr[1]} ({exc}). "
                "Is Live open with the AbletonLiveMCP control surface enabled?",
            ) from exc
        reply = json.loads(buf.split(b"\n", 1)[0])
        if reply.get("id") != rid:
            raise BridgeError("IdMismatch", f"sent {rid}, got {reply.get('id')}")
        if not reply.get("ok"):
            err = reply.get("error", {})
            # A timeout after start means the action may have run: surface it, never auto-retry.
            raise BridgeError(err.get("type", "Error"), err.get("message", ""))
        return reply.get("result")
