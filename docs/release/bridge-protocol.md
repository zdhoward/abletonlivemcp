# Bridge protocol 2 — M1a-02 steps 1–3

This is the standalone transport contract. M1a-01 installer/config reconciliation,
artifact checks and the combined closing batch (ticket step 4) have not run.
There is no protocol-1 fallback. The Remote Script implementation is stdlib only.

## Shared configuration assumed for reconciliation

Both readers use the absolute file named by `ABLETONLIVEMCP_CONFIG`, if set;
otherwise `~/.abletonlivemcp/bridge.json`. An empty, relative or invalid explicit
override fails closed without consulting the default. The file must already exist.
Neither reader creates, modifies, repairs or prints it.

The only consumed JSON field is `secret`: exactly 64 lowercase hexadecimal
characters encoding 32 random bytes, decoded to bytes before HMAC. Unknown fields
are allowed. In particular, `read_only` is reserved for M1a-01/M1b policy integration;
this transport does not consume or enforce it. There is no required config version,
port, host or protocol field. Config is at most 8192 bytes; malformed, duplicate-key
or non-finite JSON is rejected.

Readers live independently in `remote_script/AbletonLiveMCP/core.py` and
`src/abletonlivemcp/bridge.py`; neither imports `src/abletonlivemcp/config.py`.
Keep their wire/config helpers identical when reconciling M1a-01.

Both check the opened regular file and reject links/reparse points and replacement
between lstat/open. POSIX requires current-user ownership and no group/other mode
bits. Windows uses ctypes/GetSecurityInfo on the opened handle: owner must be the
process user, DACL must exist, and allow ACEs may grant access only to that user
(including OWNER RIGHTS, which resolves to that checked owner), LocalSystem or
BUILTIN Administrators. Deny ACEs are harmless; unsupported ACE
types and inspection failures are rejected. The installer must also protect the
containing directory from replacement by other users; parent-directory ACL/mode
auditing is not implemented here. Same-user secret readers and OS administrators
remain outside this boundary. Windows ACL behavior is tested on this worktree;
POSIX behavior still needs a POSIX run.

The server loads once before binding and the client loads on every call. Rotation
requires a bridge restart; mixed keys fail closed. No config bytes, exception
details, keys, nonces or MAC values are logged or included in tool outcomes.

## Framing and authentication

IPv4 loopback only (`127.0.0.1`); one authenticated request per connection.
Each frame is one UTF-8 JSON object terminated by LF, at most 1 MiB excluding LF.
Parsing rejects duplicate keys, non-finite floats (including exponent overflow),
depth over 32, over 16384 JSON nodes, integers outside ±(2^53−1), and strings over
floor(MAX_FRAME/6) characters. The string restriction bounds worst-case escaped
JSON allocation even when a handler returns a large scalar. Invalid first input,
including blank/HTTP input, closes the connection. Pipelined buffered request
suffixes are rejected. No HTTP or CORS protocol exists.

Canonical bytes are Python JSON with sorted keys, ASCII escaping,
`separators=(",", ":")`, `allow_nan=False`. A MAC is lowercase hex HMAC-SHA256:

`HMAC(secret_bytes, b"AbletonLiveMCP/v2/" + domain_ascii + NUL + canonical(context) + NUL + canonical(body))`

The envelope adds `mac` to body; verification removes it, checks its exact hex shape,
and uses `hmac.compare_digest`. Domain names below are distinct. This is a
Python-to-Python protocol; it does not claim arbitrary-language JSON canonicalization.

1. Client sends exactly `{type:"client_hello", protocol:2, nonce:C}`, where C is
   32 fresh random bytes as lowercase hex.
2. Server sends body `{type:"server_hello", protocol:2, context:T}`, signed with
   domain `server_hello` and empty context `{}`.
   T is exactly `{client_nonce:C, server_nonce:S, status:STATUS}`; S is fresh for
   each connection. STATUS includes protocol 2, component_version, build, session,
   methods, capabilities. Session is a fresh 32-byte hex value per server start.
3. Client verifies the server MAC, nonce binding, protocol and required capabilities
   **before sending an auth proof or application command**. It sends
   `{type:"client_auth", protocol:2}` signed with domain `client_auth`, context T.
4. Server verifies it before queueing any work, then returns
   `{type:"authenticated", protocol:2}`, domain `authenticated`, context T.
5. Client sends exactly `{type:"request", protocol:2, id:I, method:M, params:P}`,
   domain `request`, context T. I is a positive integer ≤2^53−1 (bool is invalid);
   M matches `[A-Za-z][A-Za-z0-9_.]{0,127}`; P is an object.
6. Server sends one signed response, domain `response`, context T, then closes.
   Success body: `{type:"response", protocol:2, id:I, ok:true, result:R}`.
   Error body: `{type:"response", protocol:2, id:I, ok:false, error:E}`.
   E is exactly `{type:string, message:string, may_have_applied:bool}`.

Different domains, C/S/session and I bind both directions and prevent cross-connection
auth/request/reply replay. Closing after the single request prevents within-connection
request replay. Unknown/extra envelope keys and invalid versions are rejected.

STATUS currently advertises component version `0.0.1`, build label
`source-protocol-2` (not an artifact hash), an empty application `methods` inventory,
and capabilities `authenticated_envelopes`, `bounded_io`, `atomic_cancellation`.
Application inventory/classification requires the later entry-point/handler boundary
integration, outside these allowed edits. Do not interpret these transport capabilities
as permission to write or as proof of Live mutation safety.

The client validates protocol/capabilities on every call, with no cross-connection
cache, and optionally requires additional capabilities through its constructor's
`required_capabilities`. Compatible component patch versions need not match exactly.
Unverifiable/incompatible handshakes instruct reinstalling the script and restarting
Live. Host policy and method-specific write checks remain later integration work.

## Bounds, lifecycle and outcomes

Defaults: 4 active socket workers, queue 16, 1 MiB request/reply, 5-second absolute
frame/read/send deadline, 15-second overall connection/exchange deadline, and an
additional 10-second main-thread wait. Incoming bytes do not reset frame deadlines.
The overall deadline includes authentication and pending work; no response is
promised after the overall deadline. Since there is one request per connection,
the effective pending queue cannot exceed four with default connection capacity.
Tests temporarily lower the queue limit to one to exercise the separate queue gate.
Read buffers are bounded to MAX_FRAME+1; parsing/serialization have the additional
depth/node/scalar limits above. Listening backlog and OS socket buffers are OS-owned.

Connection saturation returns a tiny untrusted `{type:"error",protocol:2,error:"Busy"}`
and closes without a new worker. Its send budget is at most 50 ms. Malformed frame,
oversize frame and frame timeout may similarly send an untrusted diagnostic
`BadFrame`, `FrameTooLarge` or `FrameTimeout` before closing if time remains.
Pre-auth diagnostics are never accepted by the client as authenticated outcomes.
Authenticated queue saturation returns signed Busy with may_have_applied=false.
Any spoof, invalid reply, connection loss or timeout after attempted request send
is uncertain at the host, regardless of any unauthenticated diagnostic.

One lock protects the deque and each pending job's
`queued -> started -> completed` or `queued -> cancelled` transition.
Timeout while queued removes it immediately and returns signed Timeout with
may_have_applied=false. drain() also checks the absolute deadline under that lock;
expired work never starts, even if the socket worker has not yet cancelled it.
Timeout after started returns signed TimeoutAfterStart with may_have_applied=true.
A running handler cannot be preempted; its late result is discarded, and completion
releases tracking. Handler exceptions return generic HandlerError with
may_have_applied=true, without copying exception messages. Oversize/nonserializable
handler results return bounded ReplyTooLarge with may_have_applied=true.

stop() cancels queued jobs, wakes all waiters, clears the queue, closes active sockets,
and joins transport threads with a one-second total budget. A shutdown racing with
an already-started handler is uncertain; shutdown does not kill Live's main thread.
Only drain() calls application handlers. Result validation, serialization and socket
I/O happen on the socket worker, outside the state lock.

BridgeError exposes `kind`, `may_have_applied`, and `retryable=False`. Request
transmission is marked uncertain before sendall, because a send failure can follow
full delivery. A verified signed error can establish non-application; lost or
unverified responses cannot. There are no automatic mutation or transport retries.
Deadlines bound transport responses/resources, not execution time of an already
started application handler. This is the explicit cancellation guarantee.

## Standalone verification

`python -m pytest -q -s tests/test_bridge.py`

Only ephemeral loopback listeners, recording inert dispatch, temporary private config
and isolated home discovery are used. Tests print redacted handshake/rejection,
capacity, deadlines and deterministic cancellation/start traces for the ticket ledger.
They do not import the Remote Script entry point, use Live/fake Live, connect to
9877, or run installer/artifact checks. The coordinator must reconcile config fields
and run the ticket's merged closing batch after M1a-01.
