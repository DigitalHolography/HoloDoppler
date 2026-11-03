"""Preview IO, scheduling, spawn and gallery integration regressions."""
import copy
from importlib import import_module
from pathlib import Path
import queue
import subprocess
import sys
import textwrap
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from holodoppler.cli import preview
from holodoppler.core import pipeline
from holodoppler.ui import preview_scheduler as scheduler_module
from test_pipeline_migration import parameters, reader_for


@pytest.fixture(scope="module", autouse=True)
def isolated_preview_log(tmp_path_factory):
    from holodoppler.logging import configure_logging
    configure_logging(log_path=tmp_path_factory.mktemp("preview_logs") / "preview.log")


@pytest.mark.parametrize("name", ["default", "lsci", "pca_accumulation", "sliding_shack_hartmann", "split_apertures"])
def test_display_only_preview_does_not_save(tmp_path, monkeypatch, name):
    frames = np.random.default_rng(42).uniform(10, 100, (16, 8, 10)).astype(np.float32)
    reader, _ = reader_for(tmp_path, frames)
    module = import_module("holodoppler.pipelines.main_" + ("sliding_shack_hart" if name == "sliding_shack_hartmann" else name))
    monkeypatch.setattr(pipeline, "get_reader", lambda _: reader)
    if name == "default":
        monkeypatch.setattr(module, "get_reader", lambda _: reader)
    save = Mock(return_value=tmp_path)
    monkeypatch.setattr(module if name == "default" else pipeline, "save_outputs", save)
    monkeypatch.setattr(pipeline, "OutputClass", Mock(side_effect=AssertionError("must not open outputs")))
    p = parameters(name, numpy_num_workers=0, compute_gaussian_width=False, lsci_resize_factor=1, lsci_nbh_s=3,
                   lsci_enable_spatial=True, lsci_enable_temporal=False, lsci_enable_spatiotemporal=False)
    result = preview(reader.file_path, copy.deepcopy(p), save_outputs=False)
    assert result.ndim == 2 and np.isfinite(result).all()
    save.assert_not_called()
    assert list(tmp_path.iterdir()) == []
    preview(reader.file_path, copy.deepcopy(p))
    save.assert_called_once()


def wait_until(predicate, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.01)
    raise AssertionError("Timed out waiting for preview work")


@pytest.mark.parametrize("gpu,cores,expected", [(False, 8, 2), (False, 1, 1), (True, 8, 1)])
def test_preview_worker_limits(monkeypatch, gpu, cores, expected):
    import holodoppler.backend as backend
    monkeypatch.setattr(backend, "BackendManager", lambda name: SimpleNamespace(is_gpu=gpu))
    monkeypatch.setattr(scheduler_module.os, "cpu_count", lambda: cores)
    assert scheduler_module.preview_worker_count({"backend": "auto"}, 10) == expected
    assert scheduler_module.preview_worker_count({"backend": "auto"}, 1) == 1


def test_scheduler_bounds_parallelism_drops_pending_and_drains(monkeypatch):
    from multiprocessing.pool import ThreadPool
    import multiprocessing
    context = multiprocessing.get_context("spawn")
    class Pool:
        def __init__(self, count, **kwargs):
            self.pool = ThreadPool(count)
            self._pool = []
        def apply_async(self, *args):
            return self.pool.apply_async(*args)
        def close(self): self.pool.close()
        def terminate(self): self.pool.terminate()
        def join(self): self.pool.join()
    monkeypatch.setattr(scheduler_module.multiprocessing, "get_context", lambda _: SimpleNamespace(Queue=context.Queue, Pool=Pool))
    monkeypatch.setattr(scheduler_module, "preview_worker_count", lambda p, n: 2)
    entered = []
    release = threading.Event()
    def compute(path, parameters):
        entered.append(path)
        assert release.wait(10)
        if path == "bad":
            raise ValueError("bad preview")
        return path
    monkeypatch.setattr(scheduler_module, "compute_preview", compute)
    events = queue.Queue()
    scheduler = scheduler_module.PreviewScheduler(events)
    try:
        scheduler.submit([(1, "first", {}), (2, "bad", {}), (3, "obsolete", {})])
        wait_until(lambda: len(entered) == 2)
        assert set(entered) == {"first", "bad"}
        scheduler.retain([1, 2])
        drained = scheduler.pause()
        assert not drained.wait(.2)
        release.set()
        assert drained.wait(10)
        assert "obsolete" not in entered
        results = []
        while not events.empty(): results.append(events.get_nowait())
        assert any(e["kind"] == "gallery_result" and e["token"] == 1 for e in results)
        assert any(e["kind"] == "gallery_error" and e["token"] == 2 for e in results)
        scheduler.resume()
        scheduler.submit([(4, "new", {})])
        wait_until(lambda: "new" in entered)
    finally:
        release.set()
        scheduler.close()
        scheduler.thread.join(10)
        assert not scheduler.thread.is_alive()


def test_scheduler_startup_failure_reports_each_card(monkeypatch):
    def fail(*args):
        raise RuntimeError("Cannot initialize preview workers")
    monkeypatch.setattr(scheduler_module, "preview_worker_count", fail)
    events = queue.Queue()
    scheduler = scheduler_module.PreviewScheduler(events)
    scheduler.submit([(1, "one", {}), (2, "two", {})])
    scheduler.thread.join(10)
    assert not scheduler.thread.is_alive() and scheduler.closed
    errors = []
    while not events.empty():
        event = events.get_nowait()
        if event["kind"] == "gallery_error": errors.append(event)
    assert {event["token"] for event in errors} == {1, 2}
    assert all("Cannot initialize" in event["message"] for event in errors)


def write_holo(path):
    import struct
    frames = np.random.default_rng(4).integers(1, 255, (8, 8, 10), dtype=np.uint8)
    header = struct.pack("<4sHHIIIQB", b"HOLO", 1, 8, 10, 8, 8, frames.size, 0).ljust(64, b"\0")
    path.write_bytes(header + frames.tobytes())


def test_spawn_preview_workers_and_cleanup(tmp_path):
    paths = [tmp_path / "one.holo", tmp_path / "two.holo"]
    for path in paths: write_holo(path)
    events = queue.Queue()
    scheduler = scheduler_module.PreviewScheduler(events)
    try:
        scheduler.submit([(i, p, parameters("default", numpy_num_workers=0, compute_gaussian_width=False)) for i, p in enumerate(paths)])
        completed = []
        deadline = time.monotonic() + 40
        while len(completed) < 2 and time.monotonic() < deadline:
            event = events.get(timeout=40)
            if event["kind"] in {"gallery_error", "gallery_result"}: completed.append(event)
        assert len(completed) == 2
        assert all(e["kind"] == "gallery_result" for e in completed), completed
        assert all(e["image"].shape == (8, 10) for e in completed)
        assert sorted(p.name for p in tmp_path.iterdir()) == ["one.holo", "two.holo"]
    finally:
        scheduler.close()
        scheduler.thread.join(15)
        assert not scheduler.thread.is_alive()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_gallery_controller_selection_refresh_and_processing(tmp_path, theme):
    script = textwrap.dedent('''
        import os, sys, threading, time
        from pathlib import Path
        from types import SimpleNamespace
        import tkinter as tk
        import numpy as np
        task_dir = Path(sys.argv[1])
        os.environ['APPDATA'] = str(task_dir)
        os.environ['XDG_CONFIG_HOME'] = str(task_dir)
        from holodoppler.logging import configure_logging
        configure_logging(log_path=task_dir / 'ui.log')
        from holodoppler.ui import app
        from holodoppler.ui.preview_gallery import PreviewGallery
        class Scheduler:
            def __init__(self):
                self.thread = SimpleNamespace(is_alive=lambda: True)
                self.tasks = []
                self.drained = threading.Event()
            def submit(self, tasks): self.tasks.extend(tasks)
            def retain(self, tokens): pass
            def pause(self): return self.drained
            def resume(self): pass
            def close(self): pass
        try:
            ui = app.UI()
        except tk.TclError as exc:
            print('TK_UNAVAILABLE:', exc)
            raise SystemExit(77)
        fake = Scheduler()
        ui.preview_scheduler = fake
        try:
            # Exercise real gallery widgets in each theme.
            old = ui.advanced.gallery
            old.destroy()
            gallery = PreviewGallery(ui.advanced.preview_frame, theme=sys.argv[2],
                on_select=ui.advanced.select_preview, on_retry=ui.preview_path)
            gallery.grid(row=0, column=0, sticky='nsew')
            ui.advanced.gallery = gallery
            paths = [task_dir / str(i) / 'same.holo' for i in range(6)]
            for p in paths:
                p.parent.mkdir()
                p.touch()
            ui.set_input_paths(paths)
            assert len(fake.tasks) == 6 and len(gallery.cards) == 6
            assert not ui._busy()
            first_token = ui.preview_tokens[paths[0]]
            ui._handle_event(dict(kind='gallery_started', path=paths[0], token=first_token))
            assert gallery.cards[paths[0]]['state'] == 'computing'
            ui._handle_event(dict(kind='gallery_result', path=paths[0], token=first_token, image=np.ones((8, 10))))
            image = gallery.cards[paths[0]]['image']
            assert image is not None
            ui._sync_views()
            assert gallery.cards[paths[0]]['image'] is image
            ui.advanced.select_preview(paths[3])
            assert gallery.selected_path == paths[3]
            assert ui.advanced.input_list.curselection() == (3,)
            assert gallery.cards[paths[3]]['frame'].cget('highlightbackground') == '#3b91e8'
            ui.advanced.input_list.selection_clear(0, 'end')
            ui.advanced.input_list.selection_set(1)
            ui.advanced._sync_preview_selection_from_list(None)
            assert gallery.selected_path == paths[1]
            gallery._show_tooltip(paths[1])
            assert gallery.tooltip.winfo_children()[0].cget('text') == str(paths[1])
            gallery._hide_tooltip()
            ui.geometry('1250x800')
            ui.update()
            assert gallery.columns >= 2
            assert gallery.cards[paths[2]]['frame'].grid_info()['row'] > 0
            assert float(gallery.canvas.cget('scrollregion').split()[3]) > gallery.canvas.winfo_height()
            ui.refresh_previews()
            new_token = ui.preview_tokens[paths[0]]
            assert new_token != first_token
            ui._handle_event(dict(kind='gallery_result', path=paths[0], token=first_token, image=np.ones((8, 10))))
            assert gallery.cards[paths[0]]['state'] == 'queued'
            ui._handle_event(dict(kind='gallery_error', path=paths[0], token=new_token, message='failure'))
            assert gallery.cards[paths[0]]['state'] == 'error'
            gallery.cards[paths[0]]['retry'].invoke()
            assert ui.preview_tokens[paths[0]] != new_token
            count = len(fake.tasks)
            ui._settings_changed()
            ui._settings_changed()
            deadline = time.monotonic() + .5
            while time.monotonic() < deadline:
                ui.update()
                time.sleep(.01)
            assert len(fake.tasks) == count + 6
            ui.run_processing()
            assert ui._busy()
            assert ui.minimal.status_var.get().startswith('Waiting for previews')
            ui.stop_processing()
            ui.worker.join(5)
            while not ui.events.empty(): ui._handle_event(ui.events.get_nowait())
            assert not ui._busy()
            assert ui.minimal.status_var.get() == 'Stopped'
            calls = []
            def process(path, parameters, **kwargs):
                calls.append(path)
                return {'moment0': np.full((1, 8, 10), len(calls), dtype=float)}
            app.process = process
            ui.run_processing()
            time.sleep(.1)
            assert not calls, 'processing must wait for active previews'
            fake.drained.set()
            ui.worker.join(5)
            assert not ui._busy()
            while not ui.events.empty(): ui._handle_event(ui.events.get_nowait())
            assert len(calls) == len(paths)
            assert all(c['state'] == 'ready' for c in gallery.cards.values())
            assert ui.minimal.status_var.get() == 'Processing complete'
            ui.clear_inputs()
            assert not gallery.cards and not ui.preview_tokens
            ui._handle_event(dict(kind='gallery_result', path=paths[0], token=first_token, image=np.ones((8, 10))))
            assert not gallery.cards
        finally:
            ui._on_close()
    ''')
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path), theme], capture_output=True, text=True, timeout=30)
    if result.returncode == 77: pytest.skip(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
