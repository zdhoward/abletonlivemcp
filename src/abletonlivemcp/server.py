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

import collections
import contextvars
import functools
import inspect
import json
import logging
import os
import secrets
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any

from mcp.server.elicitation import AcceptedElicitation, ElicitationResult
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.mcpserver.resolve import Elicit, Resolve
from mcp.types import ToolAnnotations
from mcp_types.version import is_version_at_least
from pydantic import BaseModel, Field, ValidationError

from . import chain
from .bridge import BridgeClient, BridgeError
from .chain import ChainError, Refusal
from .config import ConfigError, load_config
from .errors import Invalid
from .models import ResponseFormat
from .output_models import TOOL_OUTPUTS
from .permissions import DELETING, allowed_permissions, deletes, required_permissions

mcp = MCPServer("abletonlivemcp")
_bridge = BridgeClient()
_plans = chain.PlanStore()
_mutation_lock = threading.Lock()
LOCK_WAIT = 5.0
SETTLE_SECONDS = 0.3  # Live applies play/stop/launch a tick after the call returns
LEASE_TTL = 60.0
_lease: str | None = None  # held only inside live_build_chain; rides on every call meanwhile
_audit = logging.getLogger("abletonlivemcp.audit")
_log = logging.getLogger("abletonlivemcp")  # stderr only; never message text or arguments


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


class ToolsetError(Invalid):
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


def _withheld(exc: Exception, code: str) -> str:
    """An unexpected exception: its type and a stable code only. It may have come after a write,
    so the outcome is unknown."""
    return f"{type(exc).__name__}: {code} (outcome unknown; read the state back before retrying)"


def _writable(tool: str | None = None, args: dict | None = None) -> None:
    """Host policy, aligned with the bridge: writes only when the config says read_only: false.
    ``args`` (the call's arguments) matter for tools that delete only sometimes."""
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
        required = required_permissions(tool, args)
        missing = required - allowed_permissions(config)
        if missing:
            needed = ", ".join(sorted(missing))
            _audit.warning("permission_denied tool=%s permissions=%s", tool, needed)
            raise ToolFailure(
                f"permission_denied: {tool} requires local permission(s) {needed}; "
                "update permissions in the private bridge config (not applied)"
            )
        granted = ",".join(sorted(required)) or "-"
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
    tool = registered_tool(server, spec.name)
    # A property literally named "title" lives under "properties" and is never touched,
    # because pruning only looks at schema nodes, not at the property-name mapping.
    _prune_schema(tool.parameters)
    _drop_optional_null(tool.parameters)
    if tool.output_schema is not None:
        _prune_schema(tool.output_schema)


def registered_tool(server: MCPServer, name: str):
    """The SDK's registered tool, whose ``parameters`` / ``output_schema`` dicts list_tools
    serves. mcp 2.x has no public getter (add_tool returns None, list_tools returns copies), so
    this is the one place that touches the private tool manager; it fails loudly, and
    tests/test_client_server_install.py checks the edit reaches tools/list, if the SDK changes."""
    manager = getattr(server, "_tool_manager", None)
    tool = manager.get_tool(name) if manager is not None else None
    if not isinstance(getattr(tool, "parameters", None), dict):
        raise RuntimeError(f"mcp SDK changed: cannot reach the registered schema of {name!r}")
    return tool


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


def _drop_optional_null(schema: dict) -> None:
    """Input schemas only: an optional property whose default is None advertises just its real
    type, because omitting it means the same thing. ``X | None`` becomes ``X`` (``anyOf`` with a
    lone ``{"type": "null"}`` branch). Pydantic still validates calls, so an explicit null keeps
    working. Run after ``_prune_schema``, which has already removed ``"default": null``. Output
    schemas are never touched: a structured result may really contain null."""
    nodes = [schema, *(schema.get("$defs") or {}).values()]
    while nodes:
        node = nodes.pop()
        if not isinstance(node, dict):
            continue
        required = set(node.get("required") or ())
        for name, prop in (node.get("properties") or {}).items():
            if not isinstance(prop, dict):
                continue
            branches = prop.get("anyOf")
            if name not in required and "default" not in prop and isinstance(branches, list):
                rest = [b for b in branches if b != {"type": "null"}]
                if len(rest) < len(branches) and rest:
                    del prop["anyOf"]
                    if len(rest) == 1 and not (set(prop) & set(rest[0])):
                        prop.update(rest[0])
                    else:
                        prop["anyOf"] = rest
            nodes.append(prop)
        for key in ("items", "additionalProperties"):
            if isinstance(node.get(key), dict):
                nodes.append(node[key])
        for key in ("anyOf", "oneOf", "allOf"):
            nodes.extend(b for b in node.get(key) or () if isinstance(b, dict))


# ---- confirmation for DESTRUCTIVE tools (T-007) -----------------------------------------------
#
# Before a DESTRUCTIVE tool runs, the server asks the human, in form mode, to confirm the exact
# targets (with their expect_name). The question goes through the SDK resolver, so it rides a
# standalone elicitation/create request on <= 2025-11-25 and an InputRequiredResult round trip on
# >= 2026-07-28. The answer is injected by the server into a parameter the input schema never
# shows, so nothing the model sends can stand in for it; a tool may not declare its own confirm.

CONFIRM_PARAM = "confirmation"
_RESERVED_PARAMS = {"confirm", CONFIRM_PARAM, "confirmation_plan"}
_CTX_PARAM = "_abletonlivemcp_ctx"
_PLAN_PARAM = "confirmation_plan"  # the plan read for this request; injected, never sent
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


def _brief(value):
    """A long list (notes, for instance) is summarised in the confirmation text."""
    return f"<{len(value)} items>" if isinstance(value, list) and len(value) > 8 else value


@dataclass(frozen=True)
class Plan:
    """What a destructive call will delete, resolved in Live before the human is asked:
    ``lines`` describe the real objects (names, times, spans) for the question, ``data`` holds
    the references bound to exactly those objects. The write uses ``data``, so a Set changed
    while the form was open refuses at the bridge instead of deleting something else."""

    lines: list[str]
    data: dict


# tool name -> plan(arguments) for the deleting paths; filled by the tool modules.
PLANS: dict[str, Callable[[dict], Plan]] = {}
_confirmed_plan: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "abletonlivemcp_confirmed_plan", default=None
)

# An approval binds one question to the plan it shows. The plan is read in Live once, before
# the first question, and held here under a random single-use token printed in the question.
# On >= 2026-07-28 the resolvers re-run when the client resumes with the answer; the resume
# finds the approval whose rendered question the client was asked (the SDK's question digest
# in request_state) and reuses its plan instead of reading Live again, so a same-named
# replacement made while the form was open is refused by the bridge (stale_target), never
# deleted under the old answer. The tool call consumes the token (accepted, declined or
# cancelled alike); a token expires after APPROVAL_TTL and the store is bounded. A resume that
# finds no live approval reads a fresh plan under a new token: the question changes, so the
# SDK asks again instead of reusing the old answer.
APPROVAL_TTL = 600.0
MAX_APPROVALS = 64


@dataclass(frozen=True)
class Approval:
    token: str
    tool: str
    args: str  # canonical JSON of the call's arguments
    plan: Plan
    message: str  # the exact question text, rendered once
    expires: float


_approvals: collections.OrderedDict[str, Approval] = collections.OrderedDict()
_approvals_lock = threading.Lock()


def _args_key(args: dict) -> str:
    plain = {k: _plain(v) for k, v in args.items()}
    return json.dumps(plain, sort_keys=True, separators=(",", ":"), default=repr)


def _purge_approvals(now: float) -> None:
    for token in [t for t, a in _approvals.items() if a.expires <= now]:
        del _approvals[token]
    while len(_approvals) > MAX_APPROVALS:
        _approvals.popitem(last=False)


def _issue_approval(name: str, args: dict, plan: Plan) -> Approval:
    token = secrets.token_hex(4)
    label = f"{token} (single use, expires in {int(APPROVAL_TTL // 60)} min)"
    message = confirmation_message(name, args, plan, label)
    expires = time.monotonic() + APPROVAL_TTL
    approval = Approval(token, name, _args_key(args), plan, message, expires)
    with _approvals_lock:
        _approvals[token] = approval
        _purge_approvals(time.monotonic())
    return approval


def _take_approval(approval) -> Approval | None:
    """Consume ``approval``: the held record, or None when it expired, was evicted or used."""
    if not isinstance(approval, Approval):
        return None
    with _approvals_lock:
        _purge_approvals(time.monotonic())
        return _approvals.pop(approval.token, None)


def _asked_digests(ctx: Context) -> set[str] | None:
    """Digests of the questions a resumed call was asked, from the SDK's request_state; None
    if this SDK cannot say (then every candidate is offered: the SDK still accepts an answer
    only for the exact question it was given, so a wrong one is asked again, never applied)."""
    try:
        from mcp.server.mcpserver.resolve import _decode_state
    except ImportError:  # pragma: no cover - SDK drift; a test pins these helpers
        return None
    return set(_decode_state(ctx.request_state).asked.values())


def _question_digest(message: str) -> str | None:
    try:
        from mcp.server.mcpserver.resolve import _render_request, _request_digest
    except ImportError:  # pragma: no cover
        return None
    return _request_digest(_render_request(Elicit(message, Confirmation)))


def _shown_approval(ctx: Context, name: str, args: dict) -> Approval | None:
    """On a resume, the held approval whose question this call was asked; otherwise None."""
    if not ctx.request_state:
        return None
    asked = _asked_digests(ctx)
    key = _args_key(args)
    with _approvals_lock:
        _purge_approvals(time.monotonic())
        candidates = [a for a in reversed(_approvals.values()) if (a.tool, a.args) == (name, key)]
    for approval in candidates:
        if asked is None or _question_digest(approval.message) in asked:
            return approval
    return None


def planned(tool: str):
    """Register ``fn(arguments) -> Plan`` as the confirmation plan of ``tool``."""

    def register(fn):
        PLANS[tool] = fn
        return fn

    return register


def confirmed_plan() -> dict | None:
    """The plan data the human confirmed for the running call (None outside a confirmed call)."""
    return _confirmed_plan.get()


def _make_plan(name: str, args: dict) -> Plan:
    try:
        return PLANS[name](args)
    except ToolError:
        raise
    except (Invalid, ValidationError, BridgeError) as exc:
        raise ToolFailure(_explain(exc)) from exc


def confirmation_message(
    name: str, args: dict, plan: Plan | None = None, approval: str | None = None
) -> str:
    """What the human reads: the tool, the real objects this call deletes (from ``plan``, read
    in Live), every target, the other arguments. expect_name is shown only when given."""
    args = {k: _plain(v) for k, v in args.items() if v is not None}
    key = next((k for k in ("targets", "clips", "cues") if isinstance(args.get(k), list)), None)
    targets = args.pop(key) if key else None
    lines = [f"Confirm the destructive operation {_title(name)} ({name})."]
    if name in DELETING:
        lines.append(f"This call deletes: {DELETING[name][1]}.")
    if plan is not None:
        lines.append("Read from Live just now, this call deletes exactly:")
        lines += [f"- {line}" for line in plan.lines] or ["- nothing"]
        lines.append("If any of these changes before the write, nothing is applied.")
    if approval is not None:
        lines.append(f"Approval {approval}.")
    if isinstance(targets, list):
        lines.append(f"Targets ({len(targets)}):")
        for i, target in enumerate(targets, 1):
            if isinstance(target, dict):
                lines.append(
                    f"{i}. " + ", ".join(f"{k}={_brief(v)!r}" for k, v in target.items())
                )
            else:
                lines.append(f"{i}. {target!r}")
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


def _by_name(fn, name: str, params: list[inspect.Parameter], extra: str, hint) -> None:
    """Give a resolver every tool argument by name plus one injected keyword ``extra``."""
    kw = inspect.Parameter.KEYWORD_ONLY
    fn.__name__ = fn.__qualname__ = name
    fn.__signature__ = inspect.Signature(
        [p.replace(kind=kw, annotation=inspect.Parameter.empty) for p in params]
        + [inspect.Parameter(extra, kw, annotation=hint)]
    )
    fn.__annotations__ = {extra: hint}


def _confirmation_resolver(name: str, params: list[inspect.Parameter], plan_resolver):
    """The form question, built from this request's plan (resolved first, once per call)."""

    def ask(**kwargs):
        approval = kwargs.pop(_PLAN_PARAM)
        if name in DELETING and not deletes(name, kwargs):
            return None
        if isinstance(approval, Approval):  # the text rendered once for the held plan
            return Elicit(approval.message, Confirmation)
        return Elicit(confirmation_message(name, kwargs), Confirmation)

    _by_name(ask, f"confirm_{name}", params, _PLAN_PARAM, Annotated[Any, Resolve(plan_resolver)])
    return ask


def _plan_resolver(name: str, params: list[inspect.Parameter]):
    """Refuse before asking when nothing could be applied, then the approval: on a resume the
    held one whose question was asked, otherwise a plan read in Live now under a new token
    (None when the call deletes nothing or the tool has no plan). The SDK caches the value for
    the round and injects it into the question and the tool body alike."""

    def plan(**kwargs):
        ctx = kwargs.pop(_CTX_PARAM)
        if name in DELETING and not deletes(name, kwargs):
            return None  # this call deletes nothing: no question (the guard re-checks the args)
        # policy wins: never ask a human to approve a write that will refuse
        _writable(name, kwargs)
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
        if name not in PLANS:
            return None
        # bind the question to the objects it names: those already shown, or read now in Live
        shown = _shown_approval(ctx, name, kwargs)
        return shown or _issue_approval(name, kwargs, _make_plan(name, kwargs))

    _by_name(plan, f"plan_{name}", params, _CTX_PARAM, Context)
    return plan


def _check_confirmed(name: str, outcome) -> None:
    if not (
        isinstance(outcome, AcceptedElicitation)
        and isinstance(outcome.data, Confirmation)
        and outcome.data.confirm is True
    ):
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
    # DESTRUCTIVE tools are always confirmed; a tool in DELETING is confirmed for the calls
    # that delete (replace modes, cue delete), through the same form question.
    always = annotations == DESTRUCTIVE
    confirm = always or fn.__name__ in DELETING
    sig = inspect.signature(fn, eval_str=True)
    if confirm and _RESERVED_PARAMS & set(sig.parameters):
        raise RuntimeError(f"{fn.__name__}: a confirmed tool may not take a confirm argument")

    @functools.wraps(fn)
    def run(*args, **kwargs):
        token = None
        try:
            if confirm:
                outcome = kwargs.pop(CONFIRM_PARAM, None)
                # consumed whatever the answer: single use, nothing held after a decline
                approval = _take_approval(kwargs.pop(_PLAN_PARAM, None))
                if always or deletes(fn.__name__, kwargs):
                    _check_confirmed(fn.__name__, outcome)
                    if fn.__name__ in PLANS:
                        if approval is None:
                            raise ToolFailure(
                                _explain(
                                    Refusal(
                                        "confirmation_stale",
                                        "this call's approval expired or was already used; "
                                        "call again to be asked anew",
                                    )
                                )
                            )
                        token = _confirmed_plan.set(approval.plan.data)
            if not mutation:
                return fn(*args, **kwargs)
            _writable(fn.__name__, kwargs)
            if not _mutation_lock.acquire(timeout=LOCK_WAIT):
                raise ToolFailure("busy: another mutation is running; retry later (not applied)")
            try:
                return fn(*args, **kwargs)
            finally:
                _mutation_lock.release()
        except ToolError:
            raise
        # ChainError and Refusal are Invalid; a ValidationError checks the tool's own arguments
        except (Invalid, ValidationError, BridgeError) as exc:
            raise ToolFailure(_explain(exc)) from exc
        except ValueError as exc:  # not a deliberate refusal: its text may hold private data
            _log.warning("tool %s failed: %s", fn.__name__, type(exc).__name__)
            raise ToolFailure(_withheld(exc, "tool_failed")) from exc
        finally:
            if token is not None:
                _confirmed_plan.reset(token)

    # Publish the resolved signature (annotations evaluated in the tool's own module) so the MCP
    # library derives the input schema and, from the return annotation, the outputSchema.
    ret = TOOL_OUTPUTS.get(fn.__name__, _UNTYPED.get(sig.return_annotation, sig.return_annotation))
    run.__signature__ = sig.replace(return_annotation=ret)
    if confirm:
        # The confirmation is a resolved parameter: filled by the server, absent from the
        # input schema. Fresh annotations, so the wrapped function's own dict is untouched.
        params = list(sig.parameters.values())
        planner = _plan_resolver(fn.__name__, params)
        hint = Annotated[
            ElicitationResult[Confirmation],
            Resolve(_confirmation_resolver(fn.__name__, params, planner)),
        ]
        plan_hint = Annotated[Any, Resolve(planner)]
        kw = inspect.Parameter.KEYWORD_ONLY
        extra = [
            inspect.Parameter(CONFIRM_PARAM, kw, annotation=hint),
            inspect.Parameter(_PLAN_PARAM, kw, annotation=plan_hint),
        ]
        run.__signature__ = run.__signature__.replace(parameters=[*params, *extra])
        run.__annotations__ = {
            **{n: p.annotation for n, p in sig.parameters.items() if p.annotation is not p.empty},
            CONFIRM_PARAM: hint,
            _PLAN_PARAM: plan_hint,
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
        raise Invalid("response_format must be 'concise' or 'detailed'")
    return [{k: r[k] for k in concise if k in r} for r in rows]


def _untrusted(data):
    """Names and text from Live or the browser are data, never instructions."""
    return {"provenance": "live_object_text_untrusted", "data": data}


def _generation() -> int:
    return _call("session_info")["generation"]


def _row(method: str, index: int, what: str) -> dict:
    rows = _call(method)
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(rows):
        raise Invalid(f"{what} must be an index 0..{len(rows) - 1}")
    return rows[index]


def _slot(track: int, scene: int) -> dict:
    return _call("clip_slot", {"track": track, "scene": scene})


def _clip_ref(track: int, scene: int) -> str:
    slot = _slot(track, scene)
    if not slot["has_clip"]:
        raise Invalid("that clip slot is empty")
    return slot["clip"]


def _read_back(method: str, params: dict | None = None) -> tuple[Any, str | None]:
    """After a command succeeded: wait for Live to apply it, then read the real state. Returns
    ``(state, None)`` or ``(None, verification)``; a failed readback must never turn the
    command's success into "(not applied)", so it is reported beside the command's reply."""
    time.sleep(SETTLE_SECONDS)
    try:
        return _call(method, params), None
    except Refusal as exc:
        why = f"refused:{exc.code}: {exc.message}"
    except BridgeError as exc:
        why = f"{exc.kind}: {exc.message}"
    except Invalid as exc:
        why = f"invalid_reply: {exc}"
    except Exception as exc:  # noqa: BLE001 - never turn an applied command into a failure
        _log.warning("readback %s failed: %s", method, type(exc).__name__)
        why = f"{type(exc).__name__}: readback_failed"
    return None, f"the command was applied; reading the state back failed ({why})"


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
        raise Invalid("give at least one target")
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
            known = isinstance(exc, Invalid | BridgeError)
            # An unexpected exception's text may hold paths or user data: type and code only.
            stopped, error = i, _explain(exc) if known else f"{type(exc).__name__}: step_failed"
            if not known:
                _log.warning("step %s failed: %s", label, type(exc).__name__)
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
