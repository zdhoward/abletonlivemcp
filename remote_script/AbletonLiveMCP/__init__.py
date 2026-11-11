"""AbletonLiveMCP Remote Script entry point (Live loads this folder as a Control Surface)."""

import traceback

try:  # present only inside Live; absent when tests import this package
    from _Framework.ControlSurface import ControlSurface
except ImportError:  # pragma: no cover
    ControlSurface = object

from .core import BridgeServer
from .handlers import make_dispatch

PORT = 9877


class AbletonLiveMCP(ControlSurface):
    def __init__(self, c_instance):
        super().__init__(c_instance)
        self._server = None
        self._dispatch = None
        try:
            import Live

            # Pass the supplier, not a captured Song: the Set can be replaced while we run.
            dispatch = make_dispatch(self.song, Live.Application.get_application())
            self._dispatch = dispatch
            self._server = BridgeServer(dispatch, port=PORT, log=self.log_message)
            self._server.start()
            self.log_message(f"AbletonLiveMCP: listening on 127.0.0.1:{self._server.port}")
        except Exception:  # noqa: BLE001 - never let a failure here break Live's startup
            self.log_message("AbletonLiveMCP: failed to start\n" + traceback.format_exc())

    def update_display(self):  # called by Live ~every 100 ms on the main thread
        super().update_display()
        if self._server is not None:
            self._server.drain()

    def disconnect(self):
        if self._dispatch is not None:
            self._dispatch.safety.invalidate()  # drop references and any lease
        if self._server is not None:
            self._server.stop()
        super().disconnect()


def create_instance(c_instance):
    return AbletonLiveMCP(c_instance)
