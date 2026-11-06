# Default pipeline saving investigation

Measured locally on 2026-11-06 with `scripts/profile_default_saving.py`, independently
of the existing benchmark.py. Production saving code was unchanged; experimental
layout and format changes apply only inside the benchmark process.

After this investigation, production saving was updated to use one-batch
chunks for appended HDF5 datasets and export `averaged_spectrogram` only to
HDF5. The measurements below describe the original code and experimental
comparisons; running the script now measures the updated defaults.

## Workload and measurements

- 25,600 independent synthetic random uint16 frames, shape 320 × 512, values
  0–4095, deterministic seeds. 100 batches of 256, plus the normal reference read.
  The nominal input is 7.8125 GiB; batches are generated on demand, without input
  disk reads or a resident full input array.
- Actual default processing and saving paths, including SVD, translation
  registration, autofocus, square resizing, Doppler images, spectrograms and
  the averaged spectrogram. Synthetic metadata substitutes: z=0.1 m,
  pixel_pitch=[20e-6,20e-6] m, sampling_freq=50,000 Hz.
- NVIDIA RTX 5090, 32 GiB VRAM; 40 logical CPUs; 255.5 GiB system RAM; Windows.
  `auto` selected CuPy. Default CPU processing worker count (16) is inactive
  on this backend; the GPU pipeline uses its own bounded prefetch depth of 4.
- Timed processing through completed saving/encoder close. CUDA context creation
  is outside the timer; reference preparation and input generation are inside.
  Per-operation wall and thread CPU times, process IO counters, and approximately
  0.5-second RAM/GPU/disk/child-process samples are retained as JSON.
- One completed run per configuration. Comparisons are diagnostic, not statistical
  performance guarantees. The first sandboxed attempt stalled before processing
  and was discarded; completed runs used normal CUDA/FFmpeg access.

## Results

| Configuration | Total seconds | Final close/drain seconds |
|---|---:|---:|
| Full saving, synchronous (0 workers) | 70.61 | 5.44 |
| Full saving, default 2 workers | 48.51 | 10.45 |
| Full saving, 8 workers | 42.85 | 11.52 |
| HDF5/CSV only, 2 workers | 33.86 | 0.40 |
| Saving disabled, processing retained | 20.35 | 0.00 |
| Full saving, 2 workers, experimental batch-aligned HDF5 chunks | 33.77 | 12.00 |
| Same aligned chunks, aggregate media disabled (aggregate HDF5 retained) | 27.49 | 5.77 |

Worker counts also change the default queue bound: 2 workers admit 4 outstanding
batches and 8 workers admit 16. These are comparisons of the normal configurations,
not isolated thread-count experiments.

## Main bottleneck: HDF5 layout and serialized CPU work

Default auto-chunking creates moment datasets with chunks `(32,32,32)` and
spectrogram chunks `(64,4,16,16)`. The writer appends one temporal batch, then
flushes the file, for each output name. Each new batch modifies chunks spanning
32 or 64 temporal batches, repeatedly reading and rewriting their other contents.
This also allocates storage for unused portions of the last temporal chunk.

For the default two-worker run:

- Final files occupy 1.70 GiB, including 1.50 GiB HDF5.
- Process counters report 45.56 GiB of writes and about 42.5 GiB of reads.
  These are OS IO requests, **not physical disk traffic**: the system cache
  absorbs much of the repeated HDF5 IO.
- HDF5 spectrogram appends alone take 14.03 accumulated wall seconds and
  13.14 thread CPU seconds. This points to CPU work in the saving path rather
  than waiting mainly for the storage device.
- Calls submitting batches take 12.53 seconds, mostly waiting for queue capacity.
- All HDF5 appends share one explicit writer lock. More saving workers cannot
  execute those writes concurrently.

The benchmark-only change uses `chunks=(1,*value.shape)` while retaining the
same append/resize/flush behavior. With all exports retained:

- Total runtime drops 48.51 → 33.77 seconds (30% shorter).
- Spectrogram HDF5 append time drops 14.03 → 0.60 seconds.
- Batch submission time drops 12.53 → 0.53 seconds.
- Process writes drop 45.56 → 2.78 GiB; final HDF5 size drops 1.50 → 1.23 GiB.
- The batch loop takes 19.05 seconds, versus 18.90 seconds without saving.

All eleven numerical datasets, including the full averaged spectrogram, match
exactly between the baseline and aligned-chunk runs (checked array by array).

This is strong evidence that append layout is the first optimization to make.
For production, choose one-batch chunks with spatial tiling where useful, and
consider flushing once per batch rather than once per dataset. The experiment
does not establish an optimal chunk layout for every downstream read pattern.

## Remaining media and finalization cost

The final `(256,512,512)` averaged spectrogram is interpreted as a video, with
frequency bins used as frames. In addition to HDF5, saving exports AVI, MP4,
and a PNG average. Its AVI takes 1.70 seconds and MP4 4.47 seconds in the baseline.
These static exports run sequentially within the aggregate's saving job.

After aligning chunks, suppressing only aggregate media reduces total runtime
33.77 → 27.49 seconds. Per-batch media still produces two encoders per image
stream (eight streams, sixteen encoders). Encoder closes and average PNG writes
are performed serially when the session closes; their accumulated baseline
MediaStream close time is about 5.65 seconds.

Media processing is on the CPU (`mjpeg` and `libx264`), not NVENC. GPU encoding
is not enabled by adding saving workers. Keep aggregate media if it is useful;
making those exports optional would avoid about six seconds in this workload.

## Resource limits

- **Disk:** a separate 1 GiB sequential write plus `fsync` to the same benchmark
  location takes 3.33 seconds (307 MiB/s). Default output size divided by runtime
  is only about 36 MiB/s. System-wide sampled physical-disk counters report
  2.45 GiB written during the baseline, far below the process's 45.56 GiB.
  Together with the chunk-layout control, this argues against physical disk
  bandwidth being the primary limit on this machine. OS caching and unrelated
  system traffic mean disk counters are supporting evidence, not a durability
  benchmark; normal HDF5 flush/close is not an `fsync` of all output files.
- **CPU:** the default parent process averages about 1.42 CPU cores. Sampled
  encoder CPU time adds at least 1.53 cores (short-lived children can be missed).
  Overall CPU capacity is plentiful; serialized saving work and queue
  backpressure are the issue. Eight saving workers improve runtime by 12%,
  substantially less than correcting chunking with two workers.
- **GPU:** baseline sampled utilization averages 8.2%, versus 15.6% without saving.
  GPU memory peaks near 6.7 GiB, well below capacity. Low sampled utilization
  alone does not identify every processing bottleneck, but the controls show
  that saving slows the GPU producer rather than saturating the GPU.
- **RAM:** baseline Python RSS peaks at 1.88 GiB; even with eight workers it peaks
  at 2.08 GiB. At least 230 GiB system memory remains available. Neither system
  RAM nor VRAM fills. RSS excludes some driver/cache allocations; available
  system memory and GPU memory were monitored separately.

## Reproduce

From the repository root, use the project virtual environment Python:

```powershell
.\.venv\Scripts\python.exe scripts/profile_default_saving.py --mode full --workers 2
.\.venv\Scripts\python.exe scripts/profile_default_saving.py --mode full --workers 0
.\.venv\Scripts\python.exe scripts/profile_default_saving.py --mode full --workers 8
.\.venv\Scripts\python.exe scripts/profile_default_saving.py --mode h5 --workers 2
.\.venv\Scripts\python.exe scripts/profile_default_saving.py --mode none --workers 2
.\.venv\Scripts\python.exe scripts/profile_default_saving.py --mode full --workers 2 --frame-chunks
.\.venv\Scripts\python.exe scripts/profile_default_saving.py --mode no-aggregate-media --workers 2 --frame-chunks
.\.venv\Scripts\python.exe scripts/profile_default_saving.py --disk-probe
.\.venv\Scripts\python.exe scripts/profile_default_saving.py --summarize
```

All generated files and JSON measurements are in the git-ignored
`profiling_default_saving/` directory. Re-running a configuration overwrites its
generated output names. The existing benchmark.py is never called.
