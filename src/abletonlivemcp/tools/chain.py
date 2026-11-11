"""Chain tools: plan a device chain (or an FX-rack wrap), then build exactly that plan."""

from __future__ import annotations

from .. import chain, server
from ..chain import ChainError
from ..models import DevicePath, TrackSel
from ..models_devices import FxRack
from ..preferences import load_preferences
from ..resolve import plan_chain
from ..server import _call, _create, _read


def _preferences(preferences: dict | None) -> dict:
    return {**load_preferences(), **{k.lower(): v for k, v in (preferences or {}).items()}}


@_read
def live_plan_chain(
    track: TrackSel,
    stages: list[dict] | None = None,
    chain_path: DevicePath | None = None,
    append: bool = False,
    rack: dict | None = None,
    preferences: dict | None = None,
) -> dict:
    """Dry run. Target: track, return, master or a chain/pad (chain_path); occupied needs
    append. Stage: {"role": eq|compressor|saturation|reverb, "intent"} or {"device", "params",
    "root"?, "path"?}; instruments first, empty MIDI target only. Value "-18 dB" or {"raw": x}.
    rack {"groups": [{macro, label?, value?, targets: [{device, parameter, min?, max?}]}]}
    wraps the existing effects in an Audio Effect Rack (manual mapping steps)."""
    if rack is not None:
        if stages or chain_path or append:
            raise ChainError("rack mode wraps the existing devices: no stages/chain_path/append")
        groups = [g.model_dump() for g in FxRack.model_validate(rack).groups]
        plan = chain.make_rack_plan(_call, track, (), groups)
    else:
        plan = chain.make_plan(
            _call, stages or [], track, _preferences(preferences), plan_chain,
            tuple(chain_path or ()), append,
        )  # fmt: skip
    server._plans.add(plan)
    return plan.model_dump(mode="json")


def run_plan(plan_id: str, accept_omissions: bool, modes: tuple[str, ...]) -> dict:
    """Build a stored plan once under the bridge lease (shared by the chain and drum builders)."""
    plans = server._plans
    peek = plans.peek(plan_id)
    if peek is not None and peek.mode not in modes:
        raise ChainError(f"that is a {peek.mode} plan; build it with its own build tool")
    mode, value = plans.claim(plan_id)
    if mode == "receipt":
        return {**value.model_dump(mode="json"), "already_built": True}
    plan = value
    started = False
    try:
        if not plan.intent_complete and not accept_omissions:
            raise ChainError("the plan omits intent; review `omitted` and pass accept_omissions")
        ref = chain.verify_target(_call, plan)
        # The lease lives on the server module: server._call attaches it to every write.
        lease = chain.checked(server._bridge.call)("lease_acquire", {"ttl": server.LEASE_TTL})
        server._lease = lease["lease"]
        started = True
        receipt = chain.execute(_call, plan, ref)
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


@_create
def live_build_chain(plan_id: str, accept_omissions: bool = False) -> dict:
    """Build a live_plan_chain plan exactly once after re-checking the Set and target. Stops at
    the first stage not fully applied and exact; receipt: status, intent_fulfilled, per-stage
    originals/actuals, stopped_at, omitted, unknown, manual_steps. Never deletes, undoes,
    retries or substitutes. Reusing a plan returns its receipt."""
    return run_plan(plan_id, accept_omissions, ("chain", "fx_rack"))
