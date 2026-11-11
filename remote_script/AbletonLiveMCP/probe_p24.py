"""P-24: Song.view selection, select_device, rack view selected chain/drum pad.

Stub (T-003). Implemented by the P-24 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-24"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
