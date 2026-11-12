"""AbletonLiveMCP Remote Script entry point (Live loads this folder as a Control Surface)."""

try:  # present only inside Live; absent when tests import this package
    from _Framework.ControlSurface import ControlSurface
except ImportError:  # pragma: no cover
    ControlSurface = object

from .core import BridgeServer, log_failure, module_diagnostic, strict_acl_available
from .handlers import make_dispatch

PORT = 9877


class AbletonLiveMCP(ControlSurface):
    def __init__(self, c_instance):
        super().__init__(c_instance)
        self._server = None
        self._dispatch = None
        try:
            self.log_message(module_diagnostic())
            if not strict_acl_available():
                self.log_message(
                    "AbletonLiveMCP: strict config permission check unavailable in this Python "
                    "(no ctypes); using weaker location/link checks, ACL not verified"
                )
            import Live

            # Pass the supplier, not a captured Song: the Set can be replaced while we run.
            dispatch = make_dispatch(self.song, Live.Application.get_application())
            self._dispatch = dispatch
            self._server = BridgeServer(dispatch, port=PORT, log=self.log_message)
            self._server.start()
            self.log_message(f"AbletonLiveMCP: listening on 127.0.0.1:{self._server.port}")
        except Exception as exc:  # noqa: BLE001 - never let a failure here break Live's startup
            # type and code locations only: a message can hold paths or other private data
            log_failure("start", exc, self.log_message)

    def update_display(self):  # called by Live ~every 100 ms on the main thread
        super().update_display()
        if self._server is not None:
            self._server.drain()
        if self._dispatch is not None:
            try:  # advance pending loads even when no request arrived; never break Live's tick
                self._dispatch.operations.tick()
            except Exception as exc:  # noqa: BLE001
                log_failure("operations tick", exc, self.log_message)

    def disconnect(self):
        if self._dispatch is not None:
            self._dispatch.operations.invalidate()  # pending loads become unknown; ticks stop
            self._dispatch.safety.invalidate()  # drop references and any lease
        if self._server is not None:
            self._server.stop()
        super().disconnect()


def create_instance(c_instance):
    return AbletonLiveMCP(c_instance)
