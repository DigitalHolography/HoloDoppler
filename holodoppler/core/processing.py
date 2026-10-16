"""Ordered batch execution with bounded CPU and asynchronous GPU pipelines."""

import os
import sys
import logging
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from numbers import Integral
from time import perf_counter

import numpy as np
from tqdm import tqdm

from holodoppler import backend
from holodoppler.logger import get_logger

logger = get_logger(__name__)


@contextmanager
def _processing_progress(file_reader, total, batch_size, workers, cupy_async, depth):
    """Keep start/end summaries outside the progress bar, including on failure."""
    file_path = getattr(file_reader, "file_path", "unknown")
    backend_name = backend.get_backend_name()
    logger.info(
        "Starting batch processing: file=%s, backend=%s, batches=%s, batch_size=%s, "
        "workers=%s, cupy_async=%s, prefetch_depth=%s",
        file_path, backend_name, total, batch_size, workers,
        cupy_async if backend.is_gpu else False, depth if backend.is_gpu and cupy_async else 0,
    )
    started = perf_counter()
    failed = True
    progress = None
    try:
        with tqdm(total=total, desc=f"Processing ({backend_name})") as progress:
            yield progress
        failed = False
    finally:
        completed = progress.n if progress is not None else 0
        elapsed = perf_counter() - started
        logger.log(
            logging.ERROR if failed else logging.INFO,
            "Batch processing %s: file=%s, backend=%s, completed=%s/%s, elapsed=%.3fs, %.2f batches/s",
            "failed" if failed else "complete", file_path, backend_name,
            completed, total, elapsed, completed / elapsed if elapsed else 0,
        )


def _worker_count(workers):
    if workers is None:
        workers = 8
    return min(max(0, int(workers)), max(1, (os.cpu_count() or 1) // 2))


def _pinned_array(shape, dtype):
    """Allocate a NumPy array whose owner retains CUDA pinned memory."""
    dtype = np.dtype(dtype)
    memory = backend.xp.cuda.alloc_pinned_memory(int(np.prod(shape)) * dtype.itemsize)
    return np.ndarray(shape, dtype=dtype, buffer=memory)


def _run_cupy_batches(
    file_reader, batch_indices, batch_size, process_batch, consume,
    registration_ref, prepare_result, depth,
):
    """Bound all admitted batches, including queued reads, by ``depth``.

    Only the reader thread touches file IO; all CUDA calls and consumption run
    on the caller. Slots retain transfer sources until every download finishes.
    """
    xp = backend.xp
    upload = xp.cuda.Stream(non_blocking=True)
    compute = xp.cuda.Stream(non_blocking=True)
    download = xp.cuda.Stream(non_blocking=True)
    initial = xp.cuda.Event()
    initial.record(xp.cuda.get_current_stream())
    compute.wait_event(initial)
    slots = deque()
    starts = iter(enumerate(batch_indices))
    executor = ThreadPoolExecutor(max_workers=1)

    def admit():
        item = next(starts, None)
        if item is None:
            return False
        index, start = item
        slots.append({
            "index": index,
            "read": executor.submit(
                file_reader.read_frames, first_frame=start, batch_size=batch_size
            ),
        })
        return True

    def schedule(slot, reference):
        frames = slot["read"].result()
        if frames.ndim == 2:
            frames = frames[None, ...]
        host = slot["input_host"] = _pinned_array(frames.shape, frames.dtype)
        np.copyto(host, frames)
        del frames
        slot.pop("read")
        with upload:
            device = slot["input_device"] = xp.empty(host.shape, dtype=host.dtype)
            device.set(host, stream=upload)
            uploaded = xp.cuda.Event()
            uploaded.record(upload)
        compute.wait_event(uploaded)
        slot["uploaded"] = uploaded
        with compute:
            result, reference = process_batch(device, reference)
            slot["raw_result"] = result
            if prepare_result is not None:
                result = prepare_result(result)
            slot["device_result"] = result
            computed = xp.cuda.Event()
            computed.record(compute)
        slot["computed"] = computed
        download.wait_event(computed)
        host_result = slot["host_result"] = {}
        with download:
            for key, value in result.items():
                if isinstance(value, xp.ndarray):
                    target = host_result[key] = _pinned_array(value.shape, value.dtype)
                    value.get(out=target, stream=download, blocking=False)
                else:
                    host_result[key] = value
            done = xp.cuda.Event()
            done.record(download)
            slot["done"] = done
        return reference

    try:
        for _ in range(min(depth, len(batch_indices))):
            admit()
        while slots:
            # Schedule each admitted batch once, without waiting for GPU work.
            for slot in slots:
                if "done" in slot:
                    continue
                registration_ref = schedule(slot, registration_ref)
            oldest = slots[0]
            oldest["done"].synchronize()
            consume(oldest["index"], oldest["host_result"])
            slots.popleft()
            # Drop all aliases before admitting a replacement batch.
            del oldest, slot
            admit()
    finally:
        failing = sys.exc_info()[0] is not None
        for slot in slots:
            if "read" in slot:
                slot["read"].cancel()
        executor.shutdown(wait=True, cancel_futures=True)
        cleanup_error = None
        for stream in (upload, compute, download):
            try:
                stream.synchronize()
            except Exception as exc:
                if cleanup_error is None:
                    cleanup_error = exc
        slots.clear()
        if cleanup_error is not None and not failing:
            raise cleanup_error
    return registration_ref


def run_batches(
    file_reader,
    batch_indices,
    batch_size,
    process_batch,
    consume_result,
    *,
    registration_ref=None,
    registration_enabled=False,
    workers=0,
    progress_callback=None,
    cupy_async=True,
    cupy_prefetch_depth=4,
    prepare_result=None,
):
    """Process complete batches and consume results in input order.

    ``process_batch(frames, registration_ref)`` returns ``(result, reference)``.
    CPU workers share a fixed reference and must treat it as read-only.
    ``consume_result(index, result)`` runs on the calling thread. GPU execution
    uses three streams when ``cupy_async`` is true. ``cupy_prefetch_depth``
    bounds all admitted GPU batches, including queued reads. ``prepare_result``
    runs on the compute stream before download (or inline on CPU/sequential GPU).
    Asynchronous GPU results passed to the consumer are NumPy arrays.
    """
    if not isinstance(cupy_async, bool):
        raise TypeError("cupy_async must be a boolean")
    if isinstance(cupy_prefetch_depth, bool) or not isinstance(cupy_prefetch_depth, Integral):
        raise TypeError("cupy_prefetch_depth must be an integer")
    if cupy_prefetch_depth < 1:
        raise ValueError("cupy_prefetch_depth must be at least one")
    total = len(batch_indices)
    if not total:
        logger.info("No complete batches to process: file=%s, batch_size=%s",
                    getattr(file_reader, "file_path", "unknown"), batch_size)
        return registration_ref
    workers = 0 if backend.is_gpu else _worker_count(workers)
    starts = iter(batch_indices)

    def execute(start, reference):
        frames = file_reader.read_frames(first_frame=start, batch_size=batch_size)
        if frames.ndim == 2:
            frames = frames[None, ...]
        frames = backend.to_backend(frames)
        if not backend.is_gpu:
            frames = frames.astype(backend.xp.float32, copy=False)
        try:
            result, reference = process_batch(frames, reference)
            if prepare_result is not None:
                result = prepare_result(result)
            return result, reference
        finally:
            # Complete device work before results are consumed or inputs released.
            if backend.is_gpu:
                backend.xp.cuda.get_current_stream().synchronize()

    with _processing_progress(file_reader, total, batch_size, workers, cupy_async, cupy_prefetch_depth) as progress:
        def consume(index, result):
            consume_result(index, result)
            progress.update(1)
            if progress_callback is not None:
                completed = index + 1
                progress_callback(completed, total, f"Batch {completed}/{total}")

        if backend.is_gpu and cupy_async:
            return _run_cupy_batches(
                file_reader, batch_indices, batch_size, process_batch, consume,
                registration_ref, prepare_result, cupy_prefetch_depth,
            )

        completed = 0
        if workers > 1 and registration_enabled and registration_ref is None:
            result, registration_ref = execute(next(starts), None)
            if registration_ref is None:
                raise ValueError("Registration enabled but first batch produced no reference")
            consume(0, result)
            del result
            completed = 1

        if workers <= 1:
            for index, start in enumerate(starts):
                result, registration_ref = execute(start, registration_ref)
                consume(index, result)
                del result
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                pending = deque()
                try:
                    for _ in range(min(workers, total - completed)):
                        pending.append(executor.submit(execute, next(starts), registration_ref))
                    while pending:
                        future = pending.popleft()
                        try:
                            result, _ = future.result()
                            consume(completed, result)
                            del result
                        finally:
                            del future
                        completed += 1
                        start = next(starts, None)
                        if start is not None:
                            pending.append(executor.submit(execute, start, registration_ref))
                finally:
                    for future in pending:
                        future.cancel()
                    pending.clear()
    return registration_ref
