"""Bounded saving workers and legacy independent video scheduling."""
from __future__ import annotations

import os
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from numbers import Integral
from pathlib import Path
from queue import Queue
from threading import Condition, Thread
from typing import Any, Iterable

import numpy as np

from holodoppler.logging import logger
from . import data, media, policy
from .media import VideoWriter


def _saving_options(num_saving_workers, saving_queue_depth):
    if isinstance(num_saving_workers, bool) or not isinstance(num_saving_workers, Integral):
        raise TypeError("Parameter 'num_saving_workers' must be an integer.")
    if num_saving_workers < 0:
        raise ValueError("Parameter 'num_saving_workers' must be nonnegative.")
    if saving_queue_depth is not None:
        if isinstance(saving_queue_depth, bool) or not isinstance(saving_queue_depth, Integral):
            raise TypeError("Parameter 'saving_queue_depth' must be an integer or null.")
        if saving_queue_depth < 1:
            raise ValueError("Parameter 'saving_queue_depth' must be positive.")
    return num_saving_workers, saving_queue_depth or max(1, 2 * num_saving_workers)


class _SavingScheduler:
    """Bound whole submissions and keep each output on a single FIFO worker.

    Producers submit factories so capacity is acquired before arrays are copied.
    Workers never wait for other workers or close the resources they share.
    """

    def __init__(self, workers, depth):
        self._condition = Condition()
        self._queues = [Queue() for _ in range(workers)]
        self._lanes = {}
        self._pending = 0
        self.peak_pending = 0
        self.depth = depth
        self._error = None
        self._stopping = False
        self._cancelled = False
        self._threads = []
        try:
            for index, queue in enumerate(self._queues):
                thread = Thread(target=self._work, args=(queue,), name=f"Saving-{index}")
                thread.start()
                self._threads.append(thread)
        except BaseException:
            self.close(cancel=True)
            raise

    def _check(self):
        if self._error is not None:
            raise self._error
        if self._stopping:
            raise RuntimeError("Saving scheduler is closed")

    def submit(self, make_jobs):
        with self._condition:
            while self._pending >= self.depth:
                self._check()
                self._condition.wait()
            self._check()
            self._pending += 1
            try:
                jobs = make_jobs()
                groups = {}
                for name, callback, args in jobs:
                    if name not in self._lanes:
                        self._lanes[name] = len(self._lanes) % len(self._queues)
                    groups.setdefault(self._lanes[name], []).append((callback, args))
                if not groups:
                    self._pending -= 1
                    self._condition.notify_all()
                    return
                packet = {"remaining": len(groups)}
                self.peak_pending = max(self.peak_pending, self._pending)
                for lane, tasks in groups.items():
                    self._queues[lane].put((packet, tasks))
            except BaseException:
                self._pending -= 1
                self._condition.notify_all()
                raise

    def _work(self, queue):
        while True:
            item = queue.get()
            if item is None:
                return
            packet, tasks = item
            try:
                for callback, args in tasks:
                    with self._condition:
                        skip = self._cancelled or self._error is not None
                    if skip:
                        break
                    callback(*args)
            except BaseException as exc:
                with self._condition:
                    if self._error is None:
                        self._error = exc
                    self._condition.notify_all()
            finally:
                # Do not retain the previous batch while waiting for the next one.
                del item, tasks
                callback = args = None
                with self._condition:
                    packet["remaining"] -= 1
                    if packet["remaining"] == 0:
                        self._pending -= 1
                        self._condition.notify_all()
                del packet

    def close(self, *, cancel=False):
        with self._condition:
            if not self._stopping:
                self._stopping = True
                self._cancelled = cancel
                for queue in self._queues:
                    queue.put(None)
                self._condition.notify_all()
        for thread in self._threads:
            thread.join()
        if self._error is not None:
            raise self._error


def _run_saving_jobs(jobs, workers, depth):
    """Run bundle jobs without nested pools or an unbounded future list."""
    if workers == 0:
        for callback, args, kwargs in jobs:
            callback(*args, **kwargs)
        return
    pending = deque()
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="SavingBundle") as executor:
        try:
            for callback, args, kwargs in jobs:
                if len(pending) >= depth:
                    pending.popleft().result()
                pending.append(executor.submit(callback, *args, **kwargs))
            while pending:
                pending.popleft().result()
        finally:
            for future in pending:
                future.cancel()


def save_videos_parallel(
    target_dir: Path,
    data_map: dict[str, Any],
    fps: float,
    video_keys: Iterable[str] | None = None,
    video_formats: Iterable[str] = ("avi",),
    writer: VideoWriter = "cmd",
    max_workers: int = 8,
) -> None:
    """
    Save selected videos as AVI and/or MP4 in parallel.

    AVI: MJPEG
    MP4: H.264 (libx264)

    Each worker runs one independent video encoding job.
    """

    target_dir = Path(target_dir)

    avi_dir = data.ensure_directory(target_dir / "avi")
    mp4_dir = data.ensure_directory(target_dir / "mp4")

    selected = None if video_keys is None else set(video_keys)
    formats = {fmt.lower().lstrip(".") for fmt in video_formats}

    unsupported = formats - {"avi", "mp4"}
    if unsupported:
        raise ValueError(f"Unsupported video formats: {unsupported}")

    if max_workers < 1:
        raise ValueError("max_workers must be >= 1")

    cpu_count = os.cpu_count() or 1
    max_workers = max(min(max_workers, cpu_count // 2),1)

    ffmpeg = media.find_ffmpeg() if writer == "cmd" else None

    if ffmpeg:
        logger.debug(f"Using FFmpeg: {ffmpeg}")

    def save_one_video(
        name: str,
        value: np.ndarray,
        fmt: str,
    ) -> tuple[Path, float]:

        directory = avi_dir if fmt == "avi" else mp4_dir
        path = directory / f"{name}.{fmt}"

        codec = "mjpeg" if fmt == "avi" else "libx264"

        start = time.perf_counter()

        media.save_video(
            path,
            value,
            fps=fps,
            ffmpeg=ffmpeg,
            codec=codec,
            writer=writer,
        )

        elapsed = time.perf_counter() - start
        return path, elapsed

    # Build encoding jobs without duplicating NumPy arrays.
    jobs = []

    for name, value in data_map.items():
        if value is None or not isinstance(value, np.ndarray):
            continue

        if not {"avi", "mp4"}.intersection(policy.output_formats(name, value)):
            continue

        if selected is not None and name not in selected:
            continue

        for fmt in sorted(formats):
            jobs.append((name, value, fmt))

    if not jobs:
        logger.info("No videos to save.")
        return

    logger.info(
        "Saving %s video(s) using %s workers...",
        len(jobs), min(max_workers, len(jobs)),
    )

    start_total = time.perf_counter()
    errors = []

    with ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="VideoEncoder",
    ) as executor:

        futures = {
            executor.submit(save_one_video, name, value, fmt):
                (name, fmt)
            for name, value, fmt in jobs
        }

        for future in as_completed(futures):
            name, fmt = futures[future]

            try:
                path, elapsed = future.result()

                logger.info("Saved video: %s (%.1fs)", path, elapsed)

            except Exception as exc:
                errors.append((name, fmt, exc))
                logger.exception(f"Failed to save {name}.{fmt}: {exc}")

    elapsed_total = time.perf_counter() - start_total

    logger.info(
        "Video saving completed in %.1fs (%s/%s successful)",
        elapsed_total, len(jobs) - len(errors), len(jobs),
    )

    if errors:
        raise RuntimeError(
            f"{len(errors)} video encoding job(s) failed."
        ) from errors[0][2]
