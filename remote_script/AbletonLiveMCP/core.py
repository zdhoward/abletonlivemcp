"""Live-independent bridge core: loopback TCP server, newline-framed JSON, main-thread queue.

Socket threads only frame/validate JSON and enqueue work. All handler code runs inside
``BridgeServer.drain()``, which the Remote Script calls from Live's main thread. Nothing on
the main thread ever waits on a socket. Stdlib only (Live ships its own Python).
"""

import json
import queue
import socket
import threading

PROTOCOL_VERSION = 1
MAX_FRAME = 1024 * 1024  # bytes per request line
REQUEST_TIMEOUT = 10.0  # seconds a client waits for the main thread


class _Pending:
    __slots__ = ("request", "event", "response", "cancelled", "started")

    def __init__(self, request):
        self.request = request
        self.event = threading.Event()
        self.response = None
        self.cancelled = False
        self.started = False


class BridgeServer:
    def __init__(self, dispatch, host="127.0.0.1", port=9877, log=None):
        self._dispatch = dispatch  # (method, params) -> JSON-able result; raises on error
        self._host = host
        self._port = port
        self._log = log or (lambda msg: None)
        self._queue = queue.Queue()
        self._sock = None
        self._stop = threading.Event()

    @property
    def port(self):
        return self._port

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self._host, self._port))  # loopback only; never 0.0.0.0
        s.listen(4)
        s.settimeout(0.5)
        self._port = s.getsockname()[1]
        self._sock = s
        threading.Thread(target=self._accept_loop, name="almcp-accept", daemon=True).start()

    def stop(self):
        self._stop.set()
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass

    # -- main thread ---------------------------------------------------------------
    def drain(self, budget=8):
        """Run up to ``budget`` queued requests. Call from Live's main thread."""
        for _ in range(budget):
            try:
                pending = self._queue.get_nowait()
            except queue.Empty:
                return
            if pending.cancelled:  # client timed out before we started: skip, never run late
                continue
            pending.started = True
            pending.response = self._run(pending.request)
            pending.event.set()

    def _run(self, req):
        rid = req.get("id")
        try:
            result = self._dispatch(req["method"], req.get("params") or {})
            return {"id": rid, "ok": True, "result": result}
        except Exception as exc:  # noqa: BLE001 - report every handler failure to the client
            err = {"type": type(exc).__name__, "message": str(exc)}
            return {"id": rid, "ok": False, "error": err}

    # -- socket threads ------------------------------------------------------------
    def _accept_loop(self):
        while not self._stop.is_set():
            try:
                conn, _addr = self._sock.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            threading.Thread(target=self._client_loop, args=(conn,), daemon=True).start()

    def _client_loop(self, conn):
        buf = b""
        conn.settimeout(1.0)
        with conn:
            while not self._stop.is_set():
                try:
                    chunk = conn.recv(65536)
                except TimeoutError:
                    continue
                except OSError:
                    return
                if not chunk:
                    return
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if not self._handle_line(conn, line):
                        return
                if len(buf) > MAX_FRAME:
                    self._send(conn, _err(None, "FrameTooLarge", "request exceeds limit"))
                    return

    def _handle_line(self, conn, line):
        if not line.strip():
            return True
        try:
            req = json.loads(line.decode("utf-8"))
            if not isinstance(req, dict) or not isinstance(req.get("method"), str):
                raise ValueError("request must be an object with a string 'method'")
        except ValueError as exc:  # includes JSONDecodeError and UnicodeDecodeError
            return self._send(conn, _err(None, "BadRequest", str(exc)))
        pending = _Pending(req)
        self._queue.put(pending)
        if not pending.event.wait(REQUEST_TIMEOUT):
            pending.cancelled = True
            # If it already started, the mutation may have happened: say so, never retry.
            kind = "TimeoutAfterStart" if pending.started else "Timeout"
            return self._send(conn, _err(req.get("id"), kind, "main thread did not answer in time"))
        return self._send(conn, pending.response)

    def _send(self, conn, obj):
        try:
            conn.sendall(json.dumps(obj, separators=(",", ":")).encode("utf-8") + b"\n")
            return True
        except OSError:
            return False


def _err(rid, kind, message):
    return {"id": rid, "ok": False, "error": {"type": kind, "message": message}}
