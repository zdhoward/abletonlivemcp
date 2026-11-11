"""P-05: delete/duplicate calls for tracks, returns, scenes, clips and devices.

Stub (T-003). Implemented by the P-05 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-05"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
