"""P-12: drum_pads, DrumPad mute/solo/delete_all_chains, copy_pad, DrumChain fields.

Stub (T-003). Implemented by the P-12 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-12"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
