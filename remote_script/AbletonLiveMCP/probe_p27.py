"""P-27: DeviceParameter display_value write, value_items, default_value, automation_state.

Stub (T-003). Implemented by the P-27 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-27"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
