"""P-18: session_record, record_mode, overdub, capture_midi, capture_and_insert_scene.

Stub (T-003). Implemented by the P-18 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-18"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
