"""Protocol-only sockets: private temporary config, port=0, inert recording dispatch."""

import csv
import importlib.util
import io
import json
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "bridge_core", Path(__file__).resolve().parents[1] / "remote_script/AbletonLiveMCP/core.py"
)
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)  # never imports the Remote Script entry point or Live
_client_spec = importlib.util.spec_from_file_location(
    "bridge_client", Path(__file__).resolve().parents[1] / "src/abletonlivemcp/bridge.py"
)
bridge = importlib.util.module_from_spec(_client_spec)
_client_spec.loader.exec_module(bridge)  # always this worktree, never an installed checkout


class PrivateConfig:
    def __init__(self, path, secret):
        self.path, self.secret = path, secret

    def __iter__(self):
        return iter((self.path, self.secret))

    def __repr__(self):
        return "<private temporary config; secret redacted>"


@pytest.fixture
def private_config(tmp_path, monkeypatch):
    if os.name == "nt":
        identity = subprocess.run(
            ["whoami", "/user", "/fo", "csv", "/nh"],
            check=True,
            capture_output=True,
            text=True,
        )
        sid = next(csv.reader(io.StringIO(identity.stdout.strip())))[1]
        subprocess.run(
            ["icacls", str(tmp_path), "/inheritance:r", "/grant:r", f"*{sid}:(OI)(CI)F"],
            check=True,
            capture_output=True,
        )
    else:
        tmp_path.chmod(0o700)
    home = tmp_path / "isolated-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    config = tmp_path / "bridge.json"
    secret = secrets.token_bytes(32)
    config.write_text(json.dumps({"secret": secret.hex(), "read_only": True}), encoding="utf-8")
    config.chmod(0o600)
    default = home / ".abletonlivemcp" / "bridge.json"
    default.parent.mkdir()
    default.write_bytes(config.read_bytes())
    default.chmod(0o600)
    if os.name == "nt":
        subprocess.run(
            ["icacls", str(tmp_path), "/setowner", f"*{sid}", "/T"],
            check=True,
            capture_output=True,
        )
    monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", str(config))
    return PrivateConfig(config, secret)


def eventually(predicate):
    end = time.monotonic() + 2
    while not predicate():
        assert time.monotonic() < end, "bounded synchronization wait expired"
        time.sleep(0.002)


class Job:
    def __init__(self, fn):
        self.value = None
        self.error = None

        def run():
            try:
                self.value = fn()
            except Exception as exc:
                self.error = exc

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def finish(self):
        self.thread.join(2)
        assert not self.thread.is_alive()
        return self.error if self.error is not None else self.value


@contextmanager
def running(dispatch, pump=True):
    server = core.BridgeServer(dispatch, host="127.0.0.1", port=0)
    server.start()
    assert server.port != 9877 and server.port > 0
    assert server._sock.getsockname()[0] == "127.0.0.1"
    stop = threading.Event()

    def drain():
        while not stop.is_set():
            server.drain()
            stop.wait(0.002)

    worker = Job(drain) if pump else None
    try:
        yield server
    finally:
        stop.set()
        server.stop()
        if worker:
            assert worker.finish() is None
        assert not server._workers and not server._connections and not server._queue


def dial(server):
    assert server.port != 9877
    return socket.create_connection(("127.0.0.1", server.port), timeout=2)


def closed(conn):
    raw = b""
    while True:
        try:
            data = conn.recv(65536)
        except ConnectionResetError:
            break
        if not data:
            break
        raw += data
        assert len(raw) <= core.MAX_FRAME + 1
    return raw


def authenticated(server, secret):
    conn = dial(server)
    wire = bridge._Wire(conn, time.monotonic() + 2)
    context = bridge.BridgeClient(port=server.port)._authenticate(wire, secret)
    return conn, wire, context


def request(secret, context, **changes):
    body = {"type": "request", "protocol": 2, "id": 1, "method": "record", "params": {}}
    body.update(changes)
    return bridge._signed(secret, "request", context, body)


def test_config_is_private_and_fails_closed(private_config, monkeypatch):
    config, secret = private_config
    agree = core._load_secret() == bridge._load_secret() == secret
    assert agree
    monkeypatch.delenv("ABLETONLIVEMCP_CONFIG")
    agree = core._load_secret() == bridge._load_secret() == secret
    assert agree
    monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", str(config))
    for path in ("relative.json", str(config.parent / "absent.json"), ""):
        monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", path)
        with pytest.raises((ValueError, OSError)):
            core._load_secret()
        with pytest.raises(bridge.BridgeError) as error:
            bridge.BridgeClient(port=1).call("record")  # config fails before opening any socket
        assert error.value.kind == "ConfigError" and not error.value.may_have_applied
        server = core.BridgeServer(lambda *_: pytest.fail("dispatch"), port=0)
        with pytest.raises(ValueError, match="private bridge config"):
            server.start()
        assert server._sock is None
    monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", str(config))
    config.write_text('{"secret":"invalid"}', encoding="utf-8")
    for reader in (core._load_secret, bridge._load_secret):
        with pytest.raises(ValueError):
            reader()
    config.write_text(json.dumps({"secret": secret.hex()}), encoding="utf-8")
    if os.name == "nt":
        subprocess.run(
            ["icacls", str(config), "/grant", "*S-1-1-0:R"],
            check=True,
            capture_output=True,
        )
    else:
        config.chmod(0o644)
    for reader in (core._load_secret, bridge._load_secret):
        with pytest.raises(ValueError):
            reader()
    print(
        "config: temporary config/home; readers agree=True; missing/relative/empty/"
        "invalid-secret/insecure=closed; fallback=False; dispatch=0"
    )


def _without_ctypes(monkeypatch, path="bridge_core_noctypes"):
    for name in ("ctypes", "ctypes.wintypes", "msvcrt"):
        monkeypatch.setitem(sys.modules, name, None)  # import raises ImportError
    spec = importlib.util.spec_from_file_location(path, core.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_config_check_falls_back_when_ctypes_is_missing(private_config, monkeypatch, tmp_path):
    config, secret = private_config
    assert core.strict_acl_available() and "ctypes=yes" in core.module_diagnostic()
    assert core._load_secret() == secret  # ctypes-present path unchanged
    nc = _without_ctypes(monkeypatch)  # module still imports without ctypes/msvcrt
    assert nc.strict_acl_available() == (os.name != "nt")
    assert "ctypes=no" in nc.module_diagnostic() and secret.hex() not in nc.module_diagnostic()
    assert nc._load_secret() == secret
    original = config.read_bytes()
    bad = {
        "invalid-secret": b'{"secret":"zz"}',
        "duplicate-key": b'{"secret":"%s","secret":"%s"}' % ((secret.hex().encode(),) * 2),
        "oversized": b'{"secret":"%s","pad":"%s"}' % (secret.hex().encode(), b"x" * 9000),
    }
    for data in bad.values():
        config.write_bytes(data)
        with pytest.raises(ValueError):
            nc._load_secret()
    config.write_bytes(original)
    link = tmp_path / "link.json"
    try:
        link.symlink_to(config)
    except (OSError, NotImplementedError):
        link = None  # no symlink privilege on this host
    if link is not None:
        monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", str(link))
        with pytest.raises(ValueError):
            nc._load_secret()
        monkeypatch.setenv("ABLETONLIVEMCP_CONFIG", str(config))
    # Location rule: outside the profile and with no explicit override it is refused.
    with open(config, "rb") as stream:
        nc._windows_private(stream.fileno(), str(config))  # explicit override, unlinked parent
        monkeypatch.delenv("ABLETONLIVEMCP_CONFIG")
        with pytest.raises(ValueError):
            nc._windows_private(stream.fileno(), str(config))
        nc._windows_private(stream.fileno(), os.path.join(os.path.expanduser("~"), "x.json"))


def test_remote_script_imports_without_ctypes_or_msvcrt(monkeypatch):
    root = str(Path(__file__).resolve().parents[1] / "remote_script")
    saved = {k: v for k, v in sys.modules.items() if k.split(".")[0] == "AbletonLiveMCP"}
    for key in saved:
        del sys.modules[key]
    monkeypatch.syspath_prepend(root)
    for name in ("ctypes", "ctypes.wintypes", "msvcrt"):
        monkeypatch.setitem(sys.modules, name, None)
    try:
        for part in ("core", "safety", "operations", "handlers"):
            importlib.import_module("AbletonLiveMCP." + part)
    finally:
        for key in [k for k in sys.modules if k.split(".")[0] == "AbletonLiveMCP"]:
            del sys.modules[key]
        sys.modules.update(saved)


def test_mutual_authentication_envelopes_and_replay(private_config):
    _, secret = private_config
    calls = []
    with running(lambda m, p: calls.append((m, p)) or {"recorded": m}) as server:
        client = bridge.BridgeClient(port=server.port)
        assert client.call("record", {"finite": 1.25}) == {"recorded": "record"}
        assert client.status["protocol"] == 2
        assert client.status["capabilities"] == core.CAPABILITIES
        print(
            f"auth: mutual=ok protocol=2 port={server.port} ephemeral=True "
            "config/home=temporary secret/nonces/MACs=[redacted]"
        )
        calls.clear()
        with dial(server) as conn:
            wire = bridge._Wire(conn, time.monotonic() + 2)
            with pytest.raises(ValueError):
                client._authenticate(wire, secrets.token_bytes(32))
        eventually(lambda: not server._connections)
        assert calls == []
        invalid = [
            b'{"id":1,"method":"record"}\n',  # missing key/auth and protocol 1
            b'{"type":"client_hello","protocol":1,"nonce":"unused"}\n',
            b"GET / HTTP/1.1\r\n",
            b"not json\n",
            b"[]\n",
            b"\n",
            b'{"a":1,"a":2}\n',
            b'{"x":NaN}\n',
            b'{"x":1e999}\n',
        ]
        for first_line in invalid:
            with dial(server) as conn:
                conn.sendall(first_line)
                closed(conn)
        assert calls == []
        conn, wire, context = authenticated(server, secret)
        with conn:
            old_auth = bridge._signed(
                secret, "client_auth", context, {"type": "client_auth", "protocol": 2}
            )
            replay = request(secret, context)
            wire.send(replay)
            reply = bridge._verify(secret, "response", context, wire.read())
            assert reply["ok"]
            closed(conn)
        assert len(calls) == 1
        calls.clear()
        conn, wire, _ = authenticated(server, secret)
        with conn:
            wire.send(replay)
            assert closed(conn) == b""
        with dial(server) as conn:
            wire = bridge._Wire(conn, time.monotonic() + 2)
            wire.send({"type": "client_hello", "protocol": 2, "nonce": secrets.token_hex(32)})
            wire.read()
            wire.send(old_auth)
            assert closed(conn) == b""
        for changes in (
            {"id": True},
            {"id": 0},
            {"id": "1"},
            {"protocol": 1},
            {"protocol": 2.0},
            {"method": "x" * 129},
            {"params": []},
            {"extra": True},
        ):
            conn, wire, context = authenticated(server, secret)
            with conn:
                wire.send(request(secret, context, **changes))
                assert closed(conn) == b""
        conn, wire, context = authenticated(server, secret)
        with conn:
            tampered = request(secret, context)
            tampered["method"] = "tampered"
            wire.send(tampered)
            assert closed(conn) == b""
        assert calls == []
        print(
            "reject: wrong-key/missing-key/v1/auth-replay/request-replay/tamper/"
            "invalid-envelope/nonfinite/duplicate-key/malformed/HTTP=closed; dispatch=0"
        )


def test_bounds_deadlines_shutdown_and_atomic_cancellation(private_config, monkeypatch):
    _, secret = private_config
    print(
        f"defaults: connections={core.MAX_CONNECTIONS} queue={core.MAX_QUEUE} "
        f"request/reply={core.MAX_FRAME} idle/frame={core.FRAME_TIMEOUT}s "
        f"overall={core.EXCHANGE_TIMEOUT}s wait={core.REQUEST_TIMEOUT}s"
    )
    calls = []
    # Prove the byte bound independently of TCP close semantics. Windows may reset a
    # connection closed with unread inbound bytes, discarding the diagnostic reply.
    for suffix in (b"", b"\n"):
        wire = core._Wire(None, time.monotonic() + 2)
        wire.buf = b" " * (core.MAX_FRAME + 1) + suffix
        with pytest.raises(core._FrameError) as oversized:
            wire.read()
        assert oversized.value.kind == "FrameTooLarge"
    with running(lambda m, p: calls.append(m) or "x" * core.MAX_FRAME) as server:
        with dial(server) as conn:
            try:
                conn.sendall(b" " * (core.MAX_FRAME + 1) + b"\n")
            except ConnectionResetError:
                pass
            diagnostic = closed(conn)
            if diagnostic:
                assert json.loads(diagnostic.split(b"\n")[0])["error"] == "FrameTooLarge"
        assert calls == []
        with pytest.raises(bridge.BridgeError) as error:
            bridge.BridgeClient(port=server.port).call("large")
        assert error.value.kind == "ReplyTooLarge" and error.value.may_have_applied
        assert calls == ["large"]
    print(
        "bounds: 1048577-byte request=FrameTooLarge dispatch=0; "
        "oversize reply=ReplyTooLarge may_have_applied=True dispatch=1"
    )
    calls.clear()
    with running(lambda m, p: calls.append(m), pump=False) as server:
        peers = [dial(server) for _ in range(core.MAX_CONNECTIONS)]
        try:
            eventually(lambda: len(server._connections) == 4)
            with dial(server) as extra:
                assert json.loads(closed(extra))["error"] == "Busy"
            server.stop()
            assert not server._connections and not server._workers
            assert all(server._slots.acquire(blocking=False) for _ in range(4))
            for _ in range(4):
                server._slots.release()
        finally:
            for peer in peers:
                peer.close()
    print("capacity: active=4 fifth=Busy; stop sockets=0 workers=0 slots-released=4 dispatch=0")
    monkeypatch.setattr(core, "FRAME_TIMEOUT", 0.2)
    monkeypatch.setattr(core, "EXCHANGE_TIMEOUT", 1.0)
    monkeypatch.setattr(core, "REQUEST_TIMEOUT", 0.25)
    with running(lambda m, p: calls.append(m), pump=False) as server:
        with dial(server) as conn:
            began = time.monotonic()
            assert json.loads(closed(conn))["error"] == "FrameTimeout"
            idle = time.monotonic() - began
            assert 0.15 <= idle < 0.7
        with dial(server) as conn:
            began = time.monotonic()

            def trickle():
                for _ in range(8):
                    try:
                        conn.sendall(b" ")
                    except OSError:
                        return
                    time.sleep(0.05)

            sender = Job(trickle)
            assert json.loads(closed(conn))["error"] == "FrameTimeout"
            elapsed = time.monotonic() - began
            assert 0.15 <= elapsed < 0.7
            assert sender.finish() is None
    print(f"deadline: test idle/frame=0.2s idle={idle:.3f}s trickle={elapsed:.3f}s dispatch=0")
    monkeypatch.setattr(core, "MAX_QUEUE", 1)
    with running(lambda m, p: calls.append(m), pump=False) as server:
        waiting = Job(lambda: bridge.BridgeClient(port=server.port).call("cancel"))
        eventually(lambda: len(server._queue) == 1)
        with server._lock:
            pending = server._queue[0]
            assert pending.state == "queued"
        with pytest.raises(bridge.BridgeError) as error:
            bridge.BridgeClient(port=server.port).call("overflow")
        assert error.value.kind == "Busy" and not error.value.may_have_applied
        timeout = waiting.finish()
        assert isinstance(timeout, bridge.BridgeError)
        assert timeout.kind == "Timeout" and not timeout.may_have_applied and not timeout.retryable
        assert pending.state == "cancelled" and not server._queue
        server.drain()
        assert calls == []
        print(
            "queue: test limit=1 observed=1 overflow=Busy may_have_applied=False; "
            "trace queued->cancelled->drain-skipped dispatch=0 Timeout retryable=False"
        )
        waiting = Job(lambda: bridge.BridgeClient(port=server.port).call("shutdown"))
        eventually(lambda: len(server._queue) == 1)
        pending = server._queue[0]
        server.stop()
        shutdown = waiting.finish()
        assert isinstance(shutdown, bridge.BridgeError)
        assert pending.event.is_set() and pending.state == "cancelled"
        assert not server._pending and not server._queue and not server._connections
        assert calls == []
    print("shutdown: queued->cancelled waiter=woken queue=0 pending=0 sockets=0 dispatch=0")
    entered, release = threading.Event(), threading.Event()

    def record_only(method, params):
        calls.append(method)
        entered.set()
        assert release.wait(1)
        return {"recorded": method}

    with running(record_only) as server:
        waiting = Job(lambda: bridge.BridgeClient(port=server.port).call("started"))
        try:
            assert entered.wait(1)
            pending = next(iter(server._pending))
            assert pending.state == "started"
            timeout = waiting.finish()
            assert isinstance(timeout, bridge.BridgeError)
            assert timeout.kind == "TimeoutAfterStart"
            assert timeout.may_have_applied and not timeout.retryable
        finally:
            release.set()
        eventually(lambda: pending.state == "completed")
        assert calls == ["started"]
    print(
        "trace: queued->started->TimeoutAfterStart->completed dispatch=1 "
        "may_have_applied=True retryable=False"
    )
    calls.clear()
    monkeypatch.setattr(core, "FRAME_TIMEOUT", 0.5)
    monkeypatch.setattr(core, "EXCHANGE_TIMEOUT", 0.2)
    monkeypatch.setattr(core, "REQUEST_TIMEOUT", 1)
    with running(lambda m, p: calls.append(m), pump=False) as server:
        began = time.monotonic()
        with pytest.raises(bridge.BridgeError) as error:
            bridge.BridgeClient(port=server.port).call("overall")
        elapsed = time.monotonic() - began
        assert error.value.may_have_applied and not error.value.retryable
        assert 0.15 <= elapsed < 0.7
        eventually(lambda: not server._pending and not server._connections)
        server.drain()
        assert calls == []
    print(
        f"overall: test limit=0.2s observed={elapsed:.3f}s response-loss "
        "may_have_applied=True dispatch=0"
    )


def test_client_rejects_impersonation_spoofed_and_unbounded_replies(private_config, monkeypatch):
    _, secret = private_config
    received = []

    def exchange(mode):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(2)
        port = listener.getsockname()[1]
        assert port != 9877

        def peer():
            with listener:
                conn, _ = listener.accept()
                with conn:
                    wire = core._Wire(conn, time.monotonic() + 2)
                    hello = wire.read()
                    status = {
                        "protocol": 2,
                        "component_version": "0.0.9",
                        "build": "inert-test",
                        "session": secrets.token_hex(32),
                        "methods": [],
                        "capabilities": dict(core.CAPABILITIES),
                    }
                    if mode == "capability":
                        status["capabilities"]["atomic_cancellation"] = False
                    context = {
                        "client_nonce": hello["nonce"],
                        "server_nonce": secrets.token_hex(32),
                        "status": status,
                    }
                    envelope = core._signed(
                        secret,
                        "server_hello",
                        {},
                        {"type": "server_hello", "protocol": 2, "context": context},
                    )
                    if mode == "impersonator":
                        envelope["mac"] = "0" * 64
                    wire.send(envelope)
                    if mode in {"impersonator", "capability"}:
                        assert closed(conn) == b""  # no auth proof or command to an untrusted peer
                        return
                    core._verify(secret, "client_auth", context, wire.read())
                    wire.send(
                        core._signed(
                            secret,
                            "authenticated",
                            context,
                            {"type": "authenticated", "protocol": 2},
                        )
                    )
                    req = core._verify(secret, "request", context, wire.read())
                    received.append(mode)
                    reply = {
                        "type": "response",
                        "protocol": 2,
                        "id": req["id"],
                        "ok": True,
                        "result": "inert",
                    }
                    if mode == "wrong-id":
                        reply["id"] += 1
                    signed = core._signed(secret, "response", context, reply)
                    if mode == "spoof":
                        signed["mac"] = "0" * 64
                    if mode in {"oversize-line", "oversize-partial"}:
                        try:
                            conn.sendall(
                                b" " * (core.MAX_FRAME + 1)
                                + (b"\n" if mode == "oversize-line" else b"")
                            )
                        except OSError:
                            pass
                    elif mode == "idle-reply":
                        assert closed(conn) == b""
                    else:
                        wire.send(signed)

        job = Job(peer)
        try:
            client = bridge.BridgeClient(port=port)
            if mode == "compatible-patch":
                assert client.call("record") == "inert"
                return
            with pytest.raises(bridge.BridgeError) as error:
                client.call("record")
            if mode in {"impersonator", "capability"}:
                assert not error.value.may_have_applied and not client.status
            else:
                assert error.value.may_have_applied and not error.value.retryable
                if mode.startswith("oversize"):
                    assert error.value.kind == "FrameTooLarge"
                elif mode == "idle-reply":
                    assert error.value.kind == "FrameTimeout"
                else:
                    assert error.value.kind == "ProtocolError"
        finally:
            assert job.finish() is None

    monkeypatch.setattr(bridge, "FRAME_TIMEOUT", 0.2)
    for mode in (
        "impersonator",
        "capability",
        "spoof",
        "wrong-id",
        "oversize-line",
        "oversize-partial",
        "idle-reply",
        "compatible-patch",
    ):
        exchange(mode)
    assert received == [
        "spoof",
        "wrong-id",
        "oversize-line",
        "oversize-partial",
        "idle-reply",
        "compatible-patch",
    ]
    print(
        "client: impersonator/missing-capability commands=0; spoof/wrong-id=ProtocolError; "
        "reply line/partial >1048576=FrameTooLarge; idle-reply=FrameTimeout; "
        "post-transmit errors may_have_applied=True retryable=False; compatible-patch=ok"
    )


def test_review_fixes_outcome_text_refusals_auth_deadline_and_busy(private_config, monkeypatch):
    applied = str(bridge.BridgeError("ExchangeTimeout", "bridge deadline expired", True))
    refused = str(bridge.BridgeError("Busy", "x", False))
    assert applied.endswith("(may have been applied; read back state before retrying)")
    assert refused.endswith("(not applied)")

    def dispatch(method, params):
        if method == "refuse":
            raise ValueError("'scene' must be an integer")
        raise RuntimeError("secret-token-123")

    with running(dispatch) as server:
        with pytest.raises(bridge.BridgeError) as error:
            bridge.BridgeClient(port=server.port).call("refuse")
        assert error.value.kind == "ValueError" and not error.value.may_have_applied
        assert "'scene' must be an integer" in str(error.value)
        with pytest.raises(bridge.BridgeError) as error:
            bridge.BridgeClient(port=server.port).call("boom")
        assert error.value.kind == "HandlerError" and error.value.may_have_applied
        assert "secret-token-123" not in str(error.value)
    monkeypatch.setattr(core, "AUTH_TIMEOUT", 0.3)
    with running(lambda m, p: None, pump=False) as server:
        with dial(server) as conn:
            began = time.monotonic()
            reply = closed(conn)  # keyless peer is dropped; deadline races may send an error.
            assert reply == b"" or json.loads(reply).get("error") == "FrameTimeout"
            assert 0.2 <= time.monotonic() - began < 1.5
    with running(lambda m, p: None, pump=False) as server:
        peers = [dial(server) for _ in range(core.MAX_CONNECTIONS)]
        try:
            eventually(lambda: len(server._connections) == core.MAX_CONNECTIONS)
            with pytest.raises(bridge.BridgeError) as error:
                bridge.BridgeClient(port=server.port).call("busy")
            assert error.value.kind == "BridgeBusy" and not error.value.may_have_applied
            assert "bridge busy; try again shortly" in str(error.value)
        finally:
            for peer in peers:
                peer.close()
    print(
        "review: str() carries outcome; ValueError readable/not applied; other=HandlerError "
        "no text; auth deadline 0.3s; unsigned Busy=BridgeBusy not applied"
    )
