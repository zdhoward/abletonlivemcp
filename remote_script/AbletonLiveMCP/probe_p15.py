"""P-15: PluginDevice.get_parameter_names, presets, selected_preset_index.

Stub (T-003). Implemented by the P-15 ticket (plan section 4).
Behavioural probe (write): touch only objects created through ``scratch``.
"""

from .dom_common import WRITE

PROBE_ID = "P-15"
KIND = WRITE


def run(ctx, scratch):
    return {"verdict": "not_implemented"}
