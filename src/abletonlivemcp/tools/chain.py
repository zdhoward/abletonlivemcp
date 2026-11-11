"""Chain tools: plan a chain, then build exactly that plan; vocal starting points."""

from __future__ import annotations

from .. import chain, server
from ..chain import ChainError
from ..chain_presets import PRESETS
from ..preferences import load_preferences
from ..resolve import plan_chain
from ..server import _call, _create, _read


def _preferences(preferences: dict | None) -> dict:
    return {**load_preferences(), **{k.lower(): v for k, v in (preferences or {}).items()}}


@_read
def live_plan_chain(track: int, stages: list[dict], preferences: dict | None = None) -> dict:
    """Dry run for an EMPTY regular audio track: resolve stages to the devices this user has,
    without loading anything. A stage is {"role": "compressor", "intent": {...}} (roles: eq,
    compressor, saturation, reverb) or an exact {"device": "Compressor", "params": {...}} with
    optional "root" ('audio_effects' or 'plugins') and "path". A param value is a display target
    ("-18 dB") or {"raw": 0.3}. Returns an immutable plan with `plan_id`, the resolved devices,
    omitted intent (visible, never silent) and the target it was planned against. Plugin controls
    are `unverified_until_loaded`. The plan is review content, not approval: pass `plan_id` to
    live_build_chain."""
    plan = chain.make_plan(_call, stages, track, _preferences(preferences), plan_chain)
    server._plans.add(plan)
    return plan.model_dump(mode="json")


@_create
def live_build_chain(plan_id: str, accept_omissions: bool = False) -> dict:
    """Build a plan from live_plan_chain exactly once, after re-checking that the Set and target
    track are unchanged. Stops at the first stage that is not fully applied and exact and returns
    a receipt: `status` (complete/partial/failed/pending), `intent_fulfilled` (false if anything
    was omitted or off target), per-stage originals/actuals, `stopped_at`, `omitted` and
    `unknown`. It never deletes devices, undoes, retries, or loads a substitute. A plan with
    omitted intent builds only with accept_omissions=true. Using a plan again returns its
    receipt; an expired or changed plan is refused."""
    plans = server._plans
    mode, value = plans.claim(plan_id)
    if mode == "receipt":
        return {**value.model_dump(mode="json"), "already_built": True}
    plan = value
    started = False
    try:
        if not plan.intent_complete and not accept_omissions:
            raise ChainError("the plan omits intent; review `omitted` and pass accept_omissions")
        track_ref = chain.verify_target(_call, plan)
        # The lease lives on the server module: server._call attaches it to every write.
        lease = chain.checked(server._bridge.call)("lease_acquire", {"ttl": server.LEASE_TTL})
        server._lease = lease["lease"]
        started = True
        receipt = chain.execute(_call, plan, track_ref)
    except BaseException:
        if not started:
            plans.release(plan_id)  # nothing began: the plan may be tried again
        raise
    finally:
        token, server._lease = server._lease, None
        if token is not None:
            try:
                chain.checked(server._bridge.call)("lease_release", {"lease": token})
            except Exception:  # noqa: BLE001 - it expires on its own; never mask the receipt
                pass
    plans.finish(plan_id, receipt)
    return receipt.model_dump(mode="json")


@_read
def live_vocal_presets() -> dict:
    """List the starting-point vocal chains as role stages (values from general mixing practice,
    not judged by ear), ready to pass to live_plan_chain."""
    return PRESETS
