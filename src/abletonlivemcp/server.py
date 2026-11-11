"""MCP server (stdio) for the Live bridge: a small, honest core.

Only tools the Remote Script can execute safely are registered. Offline readers, the knowledge
base, gear lookup and the judge backends are not imported here. Every mutation runs under one
lock, only when the shared config says ``"read_only": false`` (the Remote Script enforces the
same policy itself), names its targets by references read from Live, and treats a refusal reply
from the bridge as an error: nothing was written.

Names and text that come from Live or from a browser are wrapped as untrusted data.

This module holds the shared helpers (registration, toolsets, bridge calls, settling, untrusted
wrapping, batch preflight, step receipts); the tools themselves live in ``tools/<domain>.py``.
``server.<tool name>`` (module ``__getattr__``) or ``server.tool(name)`` reaches any registered
tool; there is no static re-export list.

Toolsets: a tool belongs to the toolset named by its module (``tools/drums.py`` -> ``drums``;
the core domains -> ``core``). ``ABLETONLIVEMCP_TOOLSETS`` (comma-separated) or the config key
``toolsets`` picks them; ``core``, ``automation`` and ``arrangement`` are always on.
``all`` means every toolset but ``experimental``,
and an unknown name stops the server at startup. Read-only still wins: write tools stay listed
and refuse.
"""

from __future__ import annotations

import functools
import inspect
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass
from typing import Annotated, Any

from mcp.server.elicitation import AcceptedElicitation, ElicitationResult
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.mcpserver.resolve import Elicit, Resolve
from mcp.types import ToolAnnotations
from mcp_types.version import is_version_at_least
from pydantic import BaseModel, Field

from . import chain
from .bridge import BridgeClient, BridgeError
from .chain import ChainError, Refusal
from .config import ConfigError, load_config
from .models import ResponseFormat
from .output_models import TOOL_OUTPUTS
from .permissions import allowed_permissions, required_permissions

mcp = MCPServer("abletonlivemcp")
_bridge = BridgeClient()
_plans = chain.PlanStore()
_mutation_lock = threading.Lock()
LOCK_WAIT = 5.0
SETTLE_SECONDS = 0.3  # Live applies play/stop/launch a tick after the call returns
LEASE_TTL = 60.0
_lease: str | None = None  # held only inside live_build_chain; rides on every call meanwhile
_audit = logging.getLogger("abletonlivemcp.audit")


def _preset(read_only: bool, destructive: bool, idempotent: bool) -> ToolAnnotations:
    return ToolAnnotations(
        readOnlyHint=read_only,
        destructiveHint=destructive,
        idempotentHint=idempotent,
        openWorldHint=False,
    )


READ = _preset(True, False, True)
CREATE = _preset(False, False, False)
OVERWRITE = _preset(False, True, True)
CONTROL = _preset(False, False, False)  # audible state only (transport, launch, view)
DESTRUCTIVE = _preset(False, True, False)  # every call is confirmed by a human (elicitation)

# ---- toolsets ---------------------------------------------------------------------------------

CORE_MODULES = {"session", "tracks", "scenes", "clips", "notes", "devices", "browser", "chain"}
TOOLSETS = (
    "core",
    "drums",
    "racks",
    "organize",
    "als",
    "library",
    "arrangement",
    "automation",
    "recording",
    "editing",
    "song",
    "view",
    "devices-advanced",
    "files",
    "experimental",
)
TOOLSETS_ENV = "ABLETONLIVEMCP_TOOLSETS"
DEFAULT_TOOLSETS = frozenset({"core", "automation", "arrangement"})


class ToolsetError(ValueError):
    """An unknown toolset name; the server refuses to start rather than guess."""


def toolset_of(module: str) -> str:
    """``abletonlivemcp.tools.devices_advanced`` -> ``devices-advanced``; core domains -> core."""
    leaf = module.rsplit(".", 1)[-1]
    return "core" if leaf in CORE_MODULES else leaf.replace("_", "-")


def select_toolsets(requested: str | list | tuple | None) -> frozenset[str]:
    """Resolve a request; core, automation and arrangement are always on."""
    if requested is None:
        requested = ()
    if isinstance(requested, str):
        requested = requested.split(",")
    if not isinstance(requested, list | tuple) or not all(isinstance(n, str) for n in requested):
        raise ToolsetError("toolsets must be a comma-separated string or a list of names")
    names = {n.strip().lower() for n in requested if n.strip()}
    unknown = sorted(names - set(TOOLSETS) - {"all"})
    if unknown:
        raise ToolsetError(f"unknown toolset(s) {unknown}; known: {', '.join(TOOLSETS)}, all")
    if "all" in names:
        names = (names - {"all"}) | (set(TOOLSETS) - {"experimental"})
    return frozenset(names | DEFAULT_TOOLSETS)


def configured_toolsets() -> frozenset[str]:
    """The environment wins over the private config; neither means the defaults only."""
    requested = os.environ.get(TOOLSETS_ENV)
    if requested is None:
        try:
            requested = load_config().get("toolsets")
        except ConfigError:
            requested = None
    return select_toolsets(requested)


try:
    ENABLED = configured_toolsets()
    _toolset_error: ToolsetError | None = None
except ToolsetError as exc:  # reported by main(); importing for tests still works
    ENABLED, _toolset_error = frozenset({"core"}), exc


def toolsets() -> dict:
    """What live_hello reports: enabled and available toolsets."""
    return {
        "enabled": sorted(ENABLED),
        "available": list(TOOLSETS),
        "how_to_enable": f"{TOOLSETS_ENV} in the MCP client config, or \"toolsets\" in the "
        "bridge config; read once at server start, so start a new client session",
    }


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


def _writable(tool: str | None = None) -> None:
    """Host policy, aligned with the bridge: writes only when the config says read_only: false."""
    try:
        config = load_config()
        read_only = config.get("read_only") is not False
    except ConfigError:
        read_only = True
    if read_only:
        raise ToolFailure(
            "read_only: writes are disabled in the local bridge config; set read_only to false "
            "there to allow them; it is read on every call, no restart needed (not applied)"
        )
    if tool is not None:
        missing = required_permissions(tool) - allowed_permissions(config)
        if missing:
            needed = ", ".join(sorted(missing))
            _audit.warning("permission_denied tool=%s permissions=%s", tool, needed)
            raise ToolFailure(
                f"permission_denied: {tool} requires local permission(s) {needed}; "
                "update permissions in the private bridge config (not applied)"
            )
        granted = ",".join(sorted(required_permissions(tool))) or "-"
        _audit.info("allowed tool=%s permissions=%s", tool, granted)


@dataclass(frozen=True)
class ToolSpec:
    """Everything needed to list a tool; kept for every tool, enabled or not."""

    fn: Any  # the guarded wrapper
    name: str
    title: str
    toolset: str
    module: str
    annotations: ToolAnnotations


SPECS: dict[str, ToolSpec] = {}
_UNTYPED = {dict: dict[str, Any], list: list[Any]}  # bare annotations still get a schema


def _title(name: str) -> str:
    """``live_get_clip`` -> ``Get clip``."""
    words = name.removeprefix("live_").replace("_", " ")
    return words[:1].upper() + words[1:]


def install(server: MCPServer, enabled: frozenset[str]) -> None:
    """Add every recorded tool whose toolset is enabled (used for alternate surfaces, tests)."""
    for spec in SPECS.values():
        if spec.toolset in enabled:
            _add(server, spec)


def _add(server: MCPServer, spec: ToolSpec) -> None:
    if os.environ.get("ABLETONLIVEMCP_READ_ONLY_TOOLS") == "1" and spec.annotations != READ:
        return
    server.add_tool(spec.fn, name=spec.name, title=spec.title, annotations=spec.annotations)
    tool = server._tool_manager.get_tool(spec.name)
    if tool is not None:
        # A property literally named "title" lives under "properties" and is never touched,
        # because pruning only looks at schema nodes, not at the property-name mapping.
        _prune_schema(tool.parameters)
        if tool.output_schema is not None:
            _prune_schema(tool.output_schema)


def _prune_schema(schema: dict, *, top: bool = True) -> None:
    for sub in (schema.get("properties") or {}).values():
        _prune_schema(sub, top=False)
    for sub in (schema.get("$defs") or {}).values():
        sub.pop("description", None)  # class docstrings are noise to the model
        _prune_schema(sub, top=False)
    schema.pop("title", None)
    for sub in schema.get("anyOf", []) + schema.get("oneOf", []) + schema.get("allOf", []):
        if isinstance(sub, dict):
            _prune_schema(sub)
    if isinstance(schema.get("items"), dict):
        _prune_schema(schema["items"])
    if isinstance(schema.get("additionalProperties"), dict):
        _prune_schema(schema["additionalProperties"])
    if "default" in schema and schema["default"] is None:
        del schema["default"]


# ---- confirmation for DESTRUCTIVE tools (T-007) -----------------------------------------------
#
# Before a DESTRUCTIVE tool runs, the server asks the human, in form mode, to confirm the exact
# targets (with their expect_name). The question goes through the SDK resolver, so it rides a
# standalone elicitation/create request on <= 2025-11-25 and an InputRequiredResult round trip on
# >= 2026-07-28. The answer is injected by the server into a parameter the input schema never
# shows, so nothing the model sends can stand in for it; a tool may not declare its own confirm.

CONFIRM_PARAM = "confirmation"
_RESERVED_PARAMS = {"confirm", CONFIRM_PARAM}
_CTX_PARAM = "_abletonlivemcp_ctx"
_INPUT_REQUIRED_VERSION = "2026-07-28"  # first revision that elicits through InputRequiredResult


class Confirmation(BaseModel):
    """The form the human fills in: one box, unticked by default."""

    confirm: bool = Field(
        False, title="Apply", description="Tick to apply exactly the listed change"
    )


def _plain(value):
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, list | tuple):
        return [_plain(v) for v in value]
    return value


def confirmation_message(name: str, args: dict) -> str:
    """What the human reads: the tool, every target with its expect_name, the other arguments."""
    args = {k: _plain(v) for k, v in args.items() if v is not None}
    targets = args.pop("targets", None)
    lines = [f"Confirm the destructive operation {_title(name)} ({name})."]
    if isinstance(targets, list):
        lines.append(f"Targets ({len(targets)}):")
        for i, target in enumerate(targets, 1):
            if isinstance(target, dict):
                rest = ", ".join(f"{k}={v!r}" for k, v in target.items() if k != "expect_name")
                lines.append(f"{i}. {rest}; expect_name={target.get('expect_name')!r}")
            else:
                lines.append(f"{i}. {target!r}; expect_name=None")
    if args:
        lines.append("Arguments: " + ", ".join(f"{k}={v!r}" for k, v in sorted(args.items())))
    lines.append("Nothing is applied unless you tick Apply and accept.")
    return "\n".join(lines)


def _confirmation_unavailable(ctx: Context) -> bool:
    """True when this client cannot be asked: no form elicitation declared, or (before
    2026-07-28) no back-channel for the server's elicitation/create request."""
    caps = ctx.client_capabilities
    elicitation = caps.elicitation if caps is not None else None
    if elicitation is None or (elicitation.form is None and elicitation.url is not None):
        return True  # a bare `elicitation: {}` means form mode; url-only does not
    version = ctx.protocol_version
    if version is not None and is_version_at_least(version, _INPUT_REQUIRED_VERSION):
        return False
    return not ctx.session.can_send_request


def _confirmation_resolver(name: str, params: list[inspect.Parameter]):
    """A resolver that receives every tool argument by name plus the Context, and returns the
    form question (or refuses before asking when nothing could be applied anyway)."""

    def ask(**kwargs):
        ctx = kwargs.pop(_CTX_PARAM)
        _writable(name)  # policy wins: never ask a human to approve a write that will refuse
        if _confirmation_unavailable(ctx):
            raise ToolFailure(
                _explain(
                    Refusal(
                        "confirmation_unavailable",
                        f"{name} needs a human confirmation, but this client does not support "
                        "form elicitation",
                    )
                )
            )
        return Elicit(confirmation_message(name, kwargs), Confirmation)

    kw = inspect.Parameter.KEYWORD_ONLY
    ask.__name__ = f"confirm_{name}"
    ask.__signature__ = inspect.Signature(
        [p.replace(kind=kw, annotation=inspect.Parameter.empty) for p in params]
        + [inspect.Parameter(_CTX_PARAM, kw, annotation=Context)]
    )
    ask.__annotations__ = {_CTX_PARAM: Context}
    return ask


def _check_confirmed(name: str, outcome) -> None:
    if not (isinstance(outcome, AcceptedElicitation) and outcome.data.confirm is True):
        action = getattr(outcome, "action", "missing")
        detail = "accepted without ticking Apply" if action == "accept" else action
        raise ToolFailure(
            _explain(Refusal("not_confirmed", f"the human did not confirm {name} ({detail})"))
        )


def _register(fn, annotations: ToolAnnotations, mutation: bool):
    run = _guard(fn, annotations, mutation)
    if fn.__name__ in SPECS:
        raise RuntimeError(f"tool {fn.__name__} is registered twice")
    spec = ToolSpec(
        run, fn.__name__, _title(fn.__name__), toolset_of(fn.__module__), fn.__module__, annotations
    )
    SPECS[spec.name] = spec
    if spec.toolset in ENABLED:
        _add(mcp, spec)
    return run


def _guard(fn, annotations: ToolAnnotations, mutation: bool):
    """Wrap a tool body with the write policy, the mutation lock, refusal reporting and, for
    the DESTRUCTIVE preset, the human confirmation. Registers nothing."""
    confirm = annotations == DESTRUCTIVE
    sig = inspect.signature(fn, eval_str=True)
    if confirm and _RESERVED_PARAMS & set(sig.parameters):
        raise RuntimeError(f"{fn.__name__}: a DESTRUCTIVE tool may not take a confirm argument")

    @functools.wraps(fn)
    def run(*args, **kwargs):
        try:
            if confirm:
                _check_confirmed(fn.__name__, kwargs.pop(CONFIRM_PARAM, None))
            if not mutation:
                return fn(*args, **kwargs)
            _writable(fn.__name__)
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

    # Publish the resolved signature (annotations evaluated in the tool's own module) so the MCP
    # library derives the input schema and, from the return annotation, the outputSchema.
    ret = TOOL_OUTPUTS.get(fn.__name__, _UNTYPED.get(sig.return_annotation, sig.return_annotation))
    run.__signature__ = sig.replace(return_annotation=ret)
    if confirm:
        # The confirmation is a resolved parameter: filled by the server, absent from the
        # input schema. Fresh annotations, so the wrapped function's own dict is untouched.
        resolver = _confirmation_resolver(fn.__name__, list(sig.parameters.values()))
        hint = Annotated[ElicitationResult[Confirmation], Resolve(resolver)]
        extra = inspect.Parameter(CONFIRM_PARAM, inspect.Parameter.KEYWORD_ONLY, annotation=hint)
        run.__signature__ = run.__signature__.replace(parameters=[*sig.parameters.values(), extra])
        run.__annotations__ = {
            **{n: p.annotation for n, p in sig.parameters.items() if p.annotation is not p.empty},
            CONFIRM_PARAM: hint,
            "return": ret,
        }
    return run


def _read(fn):
    return _register(fn, READ, False)


def _create(fn):
    return _register(fn, CREATE, True)


def _overwrite(fn):
    return _register(fn, OVERWRITE, True)


def _control(fn):
    return _register(fn, CONTROL, True)


def _destructive(fn):
    return _register(fn, DESTRUCTIVE, True)


def _call(method: str, params: dict | None = None):
    """One bridge call; a refusal reply raises Refusal. While a lease is held every call carries
    it: writes need it and the bridge ignores it on reads, so no host-side write list can drift
    from the bridge's own classification."""
    if _lease is not None:
        params = {**(params or {}), "lease": _lease}
    return chain.checked(_bridge.call)(method, params)


def shape(rows: list[dict], response_format: ResponseFormat, concise: tuple[str, ...]) -> list:
    """`concise` keeps only the named keys of each row; `detailed` returns rows unchanged."""
    if response_format == "detailed":
        return rows
    if response_format != "concise":
        raise ValueError("response_format must be 'concise' or 'detailed'")
    return [{k: r[k] for k in concise if k in r} for r in rows]


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


# ---- shared tool helpers (v2 tool contract) -----------------------------------------------


def unsupported(what: str, reason: str) -> Refusal:
    """The bounded host refusal for an ability Live 12.2 lacks: ``refused:unsupported: ...``.
    Raise it only before any write began."""
    return Refusal("unsupported", f"{what}: {reason}")


def clip_selector(addr) -> dict:
    """A ClipRef (``{track, scene}`` or ``{track, arrangement[, take_lane]}``) -> a ``ref_issue``
    selector of kind ``clip`` or ``arr_clip``."""
    data = addr.model_dump(exclude_none=True) if isinstance(addr, BaseModel) else dict(addr)
    kind = "arr_clip" if data.get("arrangement") is not None else "clip"
    return {"kind": kind, **data}


def issue_refs(selectors: list[dict]) -> list[dict]:
    """Batch preflight: references for every selector (``{kind, ...index selectors,
    expect_name?}``; kinds as in the remote ``reference_nodes``) in as few ``ref_issue`` calls as
    possible (64 per call), then the exact-name check on every one. Raises (nothing applied)
    before any write when a selector is invalid or a name differs. Returns ``{kind, ref, name,
    expect_name}`` rows in input order; pass ``ref`` and ``expect_name`` on to the write, whose
    gate re-checks both."""
    from .models import MAX_TARGETS

    if not selectors:
        raise ValueError("give at least one target")
    rows: list[dict] = []
    for start in range(0, len(selectors), MAX_TARGETS):
        chunk = selectors[start : start + MAX_TARGETS]
        items = [{k: v for k, v in sel.items() if k != "expect_name"} for sel in chunk]
        rows += _call("ref_issue", {"targets": items})["refs"]
    out = []
    for i, (sel, row) in enumerate(zip(selectors, rows, strict=True)):
        expected = sel.get("expect_name")
        if expected is not None and expected != row.get("name"):
            raise Refusal(
                "name_mismatch",
                f"targets[{i}]: expected {expected!r} but the object is named {row.get('name')!r}",
            )
        out.append({**row, "expect_name": expected})
    return out


def run_steps(steps: list[tuple[str, Any]]) -> dict:
    """Run several write calls (``(label, zero-argument callable)``) as one tool call. A failure
    in the first step propagates (the gate's refusal text is then true). From the first success
    on, nothing raises: the reply is a receipt with ``status`` complete/partial and per-step
    ``outcome`` (applied, not_applied for a bridge refusal, unknown for anything that may have
    applied, not_attempted after a stop). It stops at the first failure; there is no rollback."""
    done: list[dict] = []
    stopped, error = None, None
    for i, (label, step) in enumerate(steps):
        if stopped is not None:
            done.append({"index": i, "label": label, "outcome": "not_attempted"})
            continue
        try:
            result = step()
        except Exception as exc:
            if not done:
                raise
            known = isinstance(exc, ValueError | BridgeError)
            stopped, error = i, _explain(exc) if known else f"{type(exc).__name__}: {exc}"
            # A bridge refusal is returned before that call's write; anything else may have
            # changed Live. _explain's "(not applied)" then describes this step only.
            refused = isinstance(exc, Refusal) or (
                isinstance(exc, BridgeError) and not exc.may_have_applied
            )
            outcome = "not_applied" if refused else "unknown"
            done.append({"index": i, "label": label, "outcome": outcome, "error": error})
            continue
        partial = isinstance(result, dict) and result.get("status") == "partial"
        done.append({"index": i, "label": label, "outcome": "applied", "result": result})
        if partial:
            stopped, error = i, "a step returned a partial receipt"
    status = "complete" if stopped is None else "partial"
    return {"status": status, "items": done, "stopped_at": stopped, "error": error}


def tool(name: str):
    """The registered (guarded) function of tool ``name``; KeyError when it is not registered.
    Tests and scripts call tools through this (or ``server.<name>``), never through re-exports."""
    return SPECS[name].fn


def __getattr__(name: str):
    """``server.live_<x>``: any registered tool, by name (no static re-export list to drift)."""
    spec = SPECS.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return spec.fn


# ---- tools, resources, prompts: registered by their modules (the helpers above exist first) --

from . import prompts as _prompts  # noqa: E402
from . import resources as _resources  # noqa: E402
from . import tools  # noqa: E402, F401 - registers every tool

_resources.register(sys.modules[__name__])
_prompts.register(sys.modules[__name__])


AUDIT_ENV = "ABLETONLIVEMCP_AUDIT"


def enable_audit_log() -> None:
    """ABLETONLIVEMCP_AUDIT=1 also logs every allowed write (tool and permissions, never
    arguments) to stderr; denials are always logged."""
    if os.environ.get(AUDIT_ENV) == "1" and not _audit.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
        _audit.addHandler(handler)
        _audit.setLevel(logging.INFO)


def main() -> None:
    if _toolset_error is not None:
        print(f"abletonlivemcp: {_toolset_error}", file=sys.stderr)
        sys.exit(2)
    enable_audit_log()
    mcp.run("stdio")


if __name__ == "__main__":
    # `python -m abletonlivemcp.server` runs this file as `__main__`, but the tool modules
    # register on the importable `abletonlivemcp.server`, so run that module's server.
    from abletonlivemcp import server as _server

    _server.main()
