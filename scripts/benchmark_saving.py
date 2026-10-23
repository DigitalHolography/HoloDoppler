"""Compare saving workers using identical frames and simulated processing time.

Run from the repository root, for example:
    python scripts/benchmark_saving.py --workers 0 1 4 --frames 32 --size 256

Uses real AVI/MP4 encoders and HDF5. Timings include initialization and shutdown;
processing_seconds includes simulated computation, submissions, and backpressure.
This measures saving overlap, rather than the optical processing pipeline.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from holodoppler.saving import OutputClass


def benchmark(root, workers, frames, size, processing_delay, queue_depth):
    params = {"num_saving_workers": workers, "saving_queue_depth": queue_depth}
    # A fresh run directory keeps previous measurements available.
    directory = root / f"workers-{workers}"
    reader = SimpleNamespace(file_path=root / "benchmark.raw")
    base = np.random.default_rng(7).random((size, size)).astype(np.float32)
    start = time.perf_counter()
    output = OutputClass(reader, params, custom_path=directory)
    loop_start = time.perf_counter()
    with output:
        for t in range(frames):
            time.sleep(processing_delay)
            image = base + np.float32(t / frames)
            output.add_batch({f"moment{index}": image * (index + 1)
                              for index in range(3)}, t)
        drain_start = time.perf_counter()
    end = time.perf_counter()
    return dict(workers=workers, queue_depth=output.saving_queue_depth,
                initialization_seconds=loop_start - start,
                processing_seconds=drain_start - loop_start,
                final_drain_seconds=end - drain_start, total_seconds=end - start,
                batches_per_second=frames / (end - start),
                peak_queued_batches=output._scheduler.peak_pending if output._scheduler else 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", nargs="+", type=int, default=[0, 1, 4])
    parser.add_argument("--frames", type=int, default=32)
    parser.add_argument("--size", type=int, default=256)
    parser.add_argument("--processing-delay", type=float, default=0.02)
    parser.add_argument("--queue-depth", type=int, default=None)
    parser.add_argument("--output", type=Path, default=Path(".local/saving-benchmark"))
    args = parser.parse_args()
    if (args.frames < 1 or args.size < 2 or args.processing_delay < 0
            or any(count < 0 for count in args.workers)
            or (args.queue_depth is not None and args.queue_depth < 1)):
        parser.error("Frames, size, and queue depth must be positive; workers and delay nonnegative.")
    root = args.output.resolve() / time.strftime("%Y%m%d-%H%M%S")
    for count in args.workers:
        result = benchmark(root, count, args.frames, args.size,
                           args.processing_delay, args.queue_depth)
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
