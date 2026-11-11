"""P-09: Clip setters, warp markers, crop and duplicate_loop.

Stub (T-003). Implemented by the P-09 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-09"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
