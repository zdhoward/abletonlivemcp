"""P-11: rack macros, add/remove_macro, variations, randomize_macros, Chain.mixer_device.

Stub (T-003). Implemented by the P-11 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-11"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
