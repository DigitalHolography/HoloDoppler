"""Ordering, bounded memory, failure handling, and output parity for saving workers."""
from pathlib import Path
from threading import Event, Thread, current_thread
from types import SimpleNamespace
from unittest.mock import Mock

import h5py
import imageio.v2 as imageio
import numpy as np
from PIL import Image
import pytest

from holodoppler import saving
from holodoppler.config import validate_main_parameters


@pytest.mark.parametrize("key,value,error", [
    ("num_saving_workers", -1, ValueError),
    ("num_saving_workers", True, TypeError),
    ("num_saving_workers", 1.5, TypeError),
    ("num_saving_workers", "2", TypeError),
    ("num_saving_workers", None, TypeError),
    ("saving_queue_depth", 0, ValueError),
    ("saving_queue_depth", -1, ValueError),
    ("saving_queue_depth", False, TypeError),
    ("saving_queue_depth", 2.5, TypeError),
])
def test_worker_options_rejected_before_creating_outputs(tmp_path, key, value, error):
    with pytest.raises(error, match=key):
        validate_main_parameters({key: value})
    with pytest.raises(error, match=key):
        saving.OutputClass(SimpleNamespace(file_path=tmp_path / "input.raw"), {key: value})
    assert not list(tmp_path.iterdir())


def test_queue_defaults():
    assert saving._saving_options(0, None) == (0, 1)
    assert saving._saving_options(3, None) == (3, 6)
    assert saving._saving_options(3, 1) == (3, 1)


def test_worker_settings_in_all_default_templates():
    import yaml

    root = Path(__file__).resolve().parents[1]
    for name in ("default_parameters_default.yaml", "default_parameters_default_offline.yaml"):
        params = yaml.safe_load((root / "parameters" / name).read_text())
        assert params["num_saving_workers"] == 0
        assert params["saving_queue_depth"] is None


def test_workers_overlap_and_capacity_precedes_copying():
    release = Event()
    started = [Event(), Event()]
    copying = Event()
    attempting = Event()
    errors = []
    scheduler = saving._SavingScheduler(2, 1)

    def job(index):
        started[index].set()
        assert release.wait(5)

    def submit_next():
        attempting.set()
        try:
            scheduler.submit(lambda: (copying.set() or [("a", lambda: None, ())]))
        except BaseException as exc:
            errors.append(exc)

    producer = Thread(target=submit_next)
    try:
        scheduler.submit(lambda: [("a", job, (0,)), ("b", job, (1,))])
        assert all(event.wait(5) for event in started)
        producer.start()
        assert attempting.wait(5)
        assert not copying.wait(0.05)
        assert scheduler.peak_pending == 1
    finally:
        release.set()
        if producer.ident is not None:
            producer.join(5)
        scheduler.close()
    assert copying.is_set() and not errors
    assert all(not thread.is_alive() for thread in scheduler._threads)


def test_snapshot_order_validation_and_static_outputs(tmp_path, monkeypatch):
    release, started = Event(), Event()
    original = saving.OutputClass._write_add
    writes = []

    def delayed(self, name, value, t):
        started.set()
        assert release.wait(5)
        writes.append((name, t, current_thread().name))
        original(self, name, value, t)

    monkeypatch.setattr(saving.OutputClass, "_write_add", delayed)
    output = saving.OutputClass(SimpleNamespace(file_path=tmp_path / "input.raw"),
                               {"num_saving_workers": 2, "saving_queue_depth": 3})
    value = np.arange(8, dtype=np.float32)
    expected = value.copy()
    try:
        output.add("spectrum_line", value, 0)
        assert started.wait(5)
        value[:] = 99
        output.add("spectrum_line", value, 1)
        with pytest.raises(ValueError, match="expected batch index"):
            output.add("spectrum_line", value, 1)
        with pytest.raises(ValueError, match="shape or dtype"):
            output.add("spectrum_line", np.ones(9, np.float32), 2)
        static = np.array([4., 5.])
        output.write_static("shack_hartmann_autofocus_zernike_coefs", static)
        static[:] = -1
        with pytest.raises(ValueError, match="already"):
            output.write_static("spectrum_line", value)
    finally:
        release.set()
        output.close()
    output.close()
    assert [t for _, t, _ in writes] == [0, 1]
    assert len({thread for _, _, thread in writes}) == 1
    assert writes[0][2].startswith("Saving-")
    with h5py.File(output.target_dir / "h5" / f"{output.target_dir.name}_output.h5") as h5:
        np.testing.assert_equal(h5["spectrum_line"][:], [expected, np.full(8, 99)])
        np.testing.assert_equal(h5["shack_hartmann_autofocus_zernike_coefs"][:], [4., 5.])


def test_worker_failure_wakes_blocked_producer_and_closes_resources(tmp_path, monkeypatch):
    started, release, attempting = Event(), Event(), Event()
    failure = OSError("disk full")
    producer_errors = []
    original = saving.OutputClass._write_add
    output = saving.OutputClass(SimpleNamespace(file_path=tmp_path / "input.raw"),
                               {"num_saving_workers": 1, "saving_queue_depth": 1})

    def fail_after_open(self, name, value, t):
        original(self, name, value, t)
        started.set()
        assert release.wait(5)
        raise failure

    monkeypatch.setattr(saving.OutputClass, "_write_add", fail_after_open)

    def submit_next():
        attempting.set()
        try:
            output.add("registration", np.ones(2), 1)
        except BaseException as exc:
            producer_errors.append(exc)

    producer = Thread(target=submit_next)
    try:
        output.add("registration", np.zeros(2), 0)
        assert started.wait(5)
        csv_handle = output._streams["registration"]["csv"]
        producer.start()
        assert attempting.wait(5)
    finally:
        release.set()
        if producer.ident is not None:
            producer.join(5)
        output.close(finalize=False)
    assert not producer.is_alive()
    assert producer_errors == [failure]
    assert csv_handle.closed and not output._h5.id.valid
    assert all(not thread.is_alive() for thread in output._scheduler._threads)


def test_close_propagates_worker_failure(tmp_path, monkeypatch):
    failure = OSError("encoder failed")
    monkeypatch.setattr(saving.OutputClass, "_write_add", Mock(side_effect=failure))
    output = saving.OutputClass(SimpleNamespace(file_path=tmp_path / "input.raw"),
                               {"num_saving_workers": 1})
    output.add("spectrum_line", np.ones(8), 0)
    with pytest.raises(OSError, match="encoder failed") as raised:
        output.close()
    assert raised.value is failure
    assert not output._h5.id.valid
    output.close()


def test_processing_failure_cancels_queue_without_masking_error(tmp_path, monkeypatch):
    output = saving.OutputClass(SimpleNamespace(file_path=tmp_path / "input.raw"),
                               {"num_saving_workers": 1, "saving_queue_depth": 3})
    started, release, cancelled = Event(), Event(), Event()
    writes = []
    original_write = saving.OutputClass._write_add
    original_close = output._scheduler.close

    def write(self, name, value, t):
        writes.append(t)
        started.set()
        assert release.wait(5)
        original_write(self, name, value, t)
        raise OSError("worker also failed")

    # Signal once cancellation is set, before joining the active worker.
    def close(*, cancel=False):
        with output._scheduler._condition:
            output._scheduler._cancelled = cancel
            cancelled.set()
        original_close(cancel=cancel)

    monkeypatch.setattr(saving.OutputClass, "_write_add", write)
    monkeypatch.setattr(output._scheduler, "close", close)
    caught = []

    def processing():
        try:
            with output:
                output.add("spectrum_line", np.ones(8), 0)
                assert started.wait(5)
                output.add("spectrum_line", np.ones(8), 1)
                raise ValueError("processing failed")
        except BaseException as exc:
            caught.append(exc)

    producer = Thread(target=processing)
    producer.start()
    try:
        assert cancelled.wait(5)
    finally:
        release.set()
        producer.join(5)
        output.close(finalize=False)
    assert not producer.is_alive()
    assert len(caught) == 1 and str(caught[0]) == "processing failed"
    assert writes == [0]
    assert not output._h5.id.valid


def _assert_equal_bundles(first, second):
    files = lambda root: {path.relative_to(root) for path in root.rglob("*") if path.is_file()}
    assert files(first) == files(second)
    for relative in files(first):
        a, b = first / relative, second / relative
        if a.suffix == ".h5":
            with h5py.File(a) as left, h5py.File(b) as right:
                assert set(left) == set(right)
                for name in left:
                    if name != "HD_parameters":
                        np.testing.assert_equal(left[name][()], right[name][()])
        elif a.suffix == ".png":
            with Image.open(a) as left, Image.open(b) as right:
                np.testing.assert_equal(np.array(left), np.array(right))
        elif a.suffix in {".avi", ".mp4"}:
            with imageio.get_reader(str(a)) as left, imageio.get_reader(str(b)) as right:
                left_frames = list(left.iter_data())
                right_frames = list(right.iter_data())
            np.testing.assert_equal(left_frames, right_frames)
        elif a.suffix == ".csv":
            assert a.read_bytes() == b.read_bytes()


@pytest.mark.parametrize("workers", [1, 3])
@pytest.mark.parametrize("live", [True, False])
def test_real_outputs_equal_synchronous_saving(tmp_path, monkeypatch, workers, live):
    monkeypatch.setattr(saving, "get_git_version", lambda: "test")
    # Avoid comparing per-run parameter metadata files; HDF5 metadata is checked above.
    monkeypatch.setattr(saving, "save_metadata", lambda *args, **kwargs: None)
    reader = SimpleNamespace(file_path=tmp_path / "input.raw")
    video = np.arange(3 * 17 * 19, dtype=np.float32).reshape(3, 17, 19)
    video[1, 0, :3] = [np.nan, np.inf, -np.inf]
    registration = np.arange(6, dtype=np.float32).reshape(3, 2)
    spectrum = np.arange(21, dtype=np.float32).reshape(3, 7)
    target = []
    for count in (0, workers):
        directory = tmp_path / str(count) / "output"
        params = {"num_saving_workers": count, "saving_queue_depth": 2}
        static = np.arange(8, dtype=np.float32)
        if live:
            with saving.OutputClass(reader, params, custom_path=directory) as output:
                for t in range(3):
                    output.add_batch({"moment0": video[t], "registration": registration[t],
                                      "spectrum_line": spectrum[t]}, t)
                output.write_static("shack_hartmann_autofocus_zernike_coefs", static)
        else:
            saving.save_outputs(reader, {"moment0": video, "registration": registration,
                "spectrum_line": spectrum, "shack_hartmann_autofocus_zernike_coefs": static},
                params, custom_path=directory, num_saving_workers=count, saving_queue_depth=2)
        target.append(directory)
    _assert_equal_bundles(*target)


@pytest.mark.parametrize("workers", [0, 2])
def test_bundle_jobs_obey_worker_count_and_failure(workers):
    caller = current_thread().name
    threads = []

    def job():
        threads.append(current_thread().name)

    saving._run_saving_jobs(((job, (), {}) for _ in range(5)), workers, 2)
    assert len(threads) == 5
    if workers == 0:
        assert set(threads) == {caller}
    else:
        assert all(name.startswith("SavingBundle") for name in threads)
        assert len(set(threads)) <= workers
    failure = OSError("write failed")
    with pytest.raises(OSError, match="write failed"):
        saving._run_saving_jobs([(Mock(side_effect=failure), (), {})], workers, 1)
