"""P-14: Browser.load_item onto a MIDI track, drum pad or rack chain; hotswap; preview.

Stub (T-003). Implemented by the P-14 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-14"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
