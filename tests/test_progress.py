from concurrent.futures import Future
from threading import Event

import numpy as np
import pytest

from holodoppler.core.progress import (
    ProcessingCancelled, ProgressReporter, check_cancelled,
)


def test_reporter_preserves_callback_contract_and_checks_after_reporting():
    stop = Event()
    calls = []

    def callback(*args):
        calls.append(args)
        stop.set()

    reporter = ProgressReporter(callback, stop)
    with pytest.raises(ProcessingCancelled):
        reporter(2, 5, "Batch 2/5")
    assert calls == [(2, 5, "Batch 2/5")]
    with pytest.raises(ProcessingCancelled):
        reporter(3, 5)
    assert len(calls) == 1
    check_cancelled(None)
    check_cancelled(lambda *args: None)


def test_ecc_cancellation_bounds_submissions_and_cancels_pending(monkeypatch):
    from holodoppler.core import registration

    stop = Event()
    submitted = []
    futures = []

    class Executor:
        def __init__(self, max_workers):
            self.max_workers = max_workers

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def submit(self, callback, job):
            submitted.append(job[0])
            future = Future()
            if len(submitted) == 1:
                future.set_result((job[0], np.zeros(12)))
            futures.append(future)
            return future

    monkeypatch.setattr(registration, "ProcessPoolExecutor", Executor)
    monkeypatch.setattr(registration.os, "cpu_count", lambda: 8)

    def report(completed, total, message):
        if completed == 2:
            stop.set()

    with pytest.raises(ProcessingCancelled):
        registration.register_with_ecc(
            np.ones((20, 4, 4), dtype=np.float32), n_workers=2,
            progress_callback=ProgressReporter(report, stop),
        )
    assert submitted == [1, 2]
    assert futures[1].cancelled()
