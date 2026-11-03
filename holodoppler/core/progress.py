"""Cooperative cancellation carried by an optional progress callback."""


class ProcessingCancelled(Exception):
    """The user requested that processing stop at a safe checkpoint."""


def check_cancelled(progress_callback):
    """Support cancellable reporters while accepting ordinary callbacks."""
    check = getattr(progress_callback, "check_cancelled", None)
    if check is not None:
        check()


class ProgressReporter:
    """A callable progress callback sharing a thread-safe cancellation event."""

    def __init__(self, callback, stop_event):
        self.callback = callback
        self.stop_event = stop_event

    def check_cancelled(self):
        if self.stop_event.is_set():
            raise ProcessingCancelled()

    def __call__(self, completed, total, message=""):
        self.check_cancelled()
        self.callback(completed, total, message)
        self.check_cancelled()
