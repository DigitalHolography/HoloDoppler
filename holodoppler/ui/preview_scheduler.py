"""Bounded, isolated preview jobs. No Tk calls are made outside the UI thread."""
from __future__ import annotations

import copy
import multiprocessing
import os
import queue
import threading
from collections import OrderedDict
from logging.handlers import QueueListener

from holodoppler.logging import configure_worker_logging, logger


def compute_preview(path, parameters):
    from holodoppler.cli import preview
    parameters = copy.deepcopy(parameters)
    parameters["numpy_num_workers"] = 0
    parameters["num_saving_workers"] = 0
    try:
        return preview(path, parameters, save_outputs=False)
    except Exception:
        logger.exception("Preview failed: %s", path)
        raise


def preview_worker_count(parameters, file_count):
    from holodoppler.backend import BackendManager
    gpu = BackendManager(parameters.get("backend", "auto")).is_gpu
    return min(file_count, 1 if gpu else min(2, os.cpu_count() or 1))


class PreviewScheduler:
    """One coordinator owns the pool; callers only enqueue commands.

    Only a worker-count-sized window is submitted, so obsolete queued work can
    be replaced without first computing an entire old batch.
    """
    def __init__(self, events):
        self.events = events
        self.commands = queue.Queue()
        self.closed = False
        self.thread = threading.Thread(target=self._run, name="PreviewScheduler", daemon=True)
        self.thread.start()

    def submit(self, tasks):
        self.commands.put(("submit", tasks))

    def retain(self, tokens):
        self.commands.put(("retain", set(tokens)))

    def pause(self):
        drained = threading.Event()
        self.commands.put(("pause", drained))
        return drained

    def resume(self):
        self.commands.put(("resume", None))

    def close(self):
        self.closed = True
        self.commands.put(("close", None))

    def _run(self):
        context = multiprocessing.get_context("spawn")
        pending = OrderedDict()
        active = {}
        pool = listener = log_queue = None
        pool_key = None
        paused = False
        drained = None
        closed = False

        def cleanup(terminate=False):
            nonlocal pool, listener, log_queue, pool_key
            if pool is not None:
                if terminate:
                    pool.terminate()
                else:
                    pool.close()
                pool.join()
                pool = None
            if listener is not None:
                listener.stop()
                listener = None
            if log_queue is not None:
                log_queue.close()
                log_queue.join_thread()
                log_queue = None
            pool_key = None

        try:
            while not closed and not self.closed:
                try:
                    kind, value = self.commands.get(timeout=.05)
                    if kind == "close":
                        closed = True
                        continue
                    if kind == "submit":
                        for token, path, parameters in value:
                            pending[token] = (path, parameters)
                    elif kind == "retain":
                        pending = OrderedDict((k, v) for k, v in pending.items() if k in value)
                    elif kind == "pause":
                        paused, drained = True, value
                    elif kind == "resume":
                        paused, drained = False, None
                except queue.Empty:
                    pass

                for token, (result, path) in list(active.items()):
                    if not result.ready():
                        continue
                    del active[token]
                    try:
                        image = result.get()
                        self.events.put(dict(kind="gallery_result", token=token, path=path, image=image))
                    except Exception as exc:
                        self.events.put(dict(kind="gallery_error", token=token, path=path, message=str(exc)))

                # A worker killed by native code never produces an AsyncResult.
                # Pool normally silently replaces it; fail this generation instead.
                if pool is not None and any(p.exitcode is not None for p in workers):
                    raise RuntimeError("A preview worker exited unexpectedly. Refresh previews to retry.")
                if paused:
                    if not active and drained is not None:
                        cleanup()
                        drained.set()
                    continue
                if not pending:
                    continue
                parameters = next(iter(pending.values()))[1]
                # Keep the CPU pool at two workers even for a single initial file,
                # allowing subsequently loaded files to overlap without a restart.
                count = preview_worker_count(parameters, 2)
                key = (parameters.get("backend", "auto"), count)
                if pool_key != key:
                    if active:
                        continue
                    cleanup()
                    log_queue = context.Queue()
                    listener = QueueListener(log_queue, *logger.handlers, respect_handler_level=True)
                    listener.start()
                    pool = context.Pool(count, initializer=configure_worker_logging, initargs=(log_queue,))
                    workers = list(pool._pool)
                    pool_key = key
                while pending and len(active) < count:
                    token, (path, parameters) = pending.popitem(last=False)
                    self.events.put(dict(kind="gallery_started", token=token, path=path))
                    active[token] = (pool.apply_async(compute_preview, (path, parameters)), path)
        except Exception as exc:
            self.closed = True
            logger.exception("Preview scheduler failed")
            for token, path in [(k, v[1]) for k, v in active.items()] + [(k, v[0]) for k, v in pending.items()]:
                self.events.put(dict(kind="gallery_error", token=token, path=path, message=str(exc)))
        finally:
            self.closed = True
            cleanup(terminate=True)
            if drained is not None:
                drained.set()
            self.events.put(dict(kind="gallery_scheduler_closed"))
