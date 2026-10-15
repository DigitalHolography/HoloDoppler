"""Ordered batch execution with bounded CPU concurrency."""

import os
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm

from holodoppler import backend


def _worker_count(workers):
    if workers is None:
        workers = 8
    return min(max(0, int(workers)), max(1, (os.cpu_count() or 1) // 2))


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
):
    """Process complete batches and consume results in input order.

    ``process_batch(frames, registration_ref)`` returns ``(result, reference)``.
    CPU workers share a fixed reference and must treat it as read-only.
    ``consume_result(index, result)`` runs on the calling thread. GPU execution
    is sequential. At most one worker's worth of futures is retained per worker.
    """
    total = len(batch_indices)
    if not total:
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
            return process_batch(frames, reference)
        finally:
            # Complete device work before results are consumed or inputs released.
            if backend.is_gpu:
                backend.xp.cuda.get_current_stream().synchronize()

    with tqdm(total=total, desc=f"Processing ({backend.get_backend_name()})") as progress:
        def consume(index, result):
            consume_result(index, result)
            progress.update(1)
            if progress_callback is not None:
                completed = index + 1
                progress_callback(completed, total, f"Batch {completed}/{total}")

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
