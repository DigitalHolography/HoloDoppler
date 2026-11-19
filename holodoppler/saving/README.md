# Saving package

Pipelines continue to import `OutputClass`, `save_outputs`, and standalone
save helpers from `holodoppler.saving`.

Before erasing or archiving existing results, `check_output_access(path)` checks
the entire tree without modifying it. Windows delete-sharing conflicts raise
`PermissionError` naming the blocked path. Links and junctions are not traversed.
Other platforms check directory permissions. This is best effort: another
application can change access after the check, so replacement is not atomic.

| Module | Owns |
| --- | --- |
| `policy` | Shape classification and shared output-format selection |
| `data` | HDF5/CSV writers, numerical conversion, metadata, and serialization |
| `media` | Display conversion, encoders, streaming averages, and media export jobs |
| `scheduler` | Ordered workers, bounded submissions, and legacy bundle/video scheduling |
| `session` | Destination preparation, validation, submission, and resource lifecycle |
| `__init__` | Compatibility exports for existing callers |

To change which formats receive an output, edit `policy.output_formats`
and `policy.save_to_hdf5`. Streaming, static, and buffered orchestration
use these shared decisions. Standalone `save_h5` remains an explicit
low-level export: its optional selection list controls which arrays it writes.

`Hdf5Writer` owns the file, lock, metadata initialization, and append/static
writes. Numerical exports preserve NaNs and infinities; floating arrays use
float32 HDF5 storage. Rendered color and directional Doppler outputs remain
excluded from pipeline HDF5 exports. Shift arrays go to CSV and HDF5.
Appended datasets use one-batch chunks `(1, *batch_shape)` so each append
avoids rewriting earlier batches. `averaged_spectrogram` is exported only
to HDF5, with no AVI, MP4, or PNG exports.
For the default pipeline, `h5compression: 0` disables HDF5 compression (the
default); levels 1–9 enable gzip for numerical array datasets, including
`averaged_spectrogram`. Metadata and scalar datasets remain uncompressed.

`MediaStream` owns encoder handles, first-frame display levels, and the
unquantized temporal sum used for the final PNG. `CsvStream` writes one
flattened row per temporal batch. Complete/static CSV arrays retain their
existing first-axis rows and flatten trailing dimensions into columns.

Set `video_temporal_sigma: 1.0` in the processing YAML for smoother AVI and
MP4 exports. The value is the Gaussian standard deviation in output frames;
`0` (the default) disables it. Filtering affects only display frames, after
display scaling, and never changes HDF5, CSV, PNG averages, or processing
results. Spatial pixels and color channels are not mixed. Both streaming and
buffered exports use a centered Gaussian truncated at four sigma, repeating
the nearest frame at the ends. Streaming waits for that many future frames
and keeps at most a window of `2 * int(4 * sigma + 0.5) + 1` frames per video;
finalization flushes the remaining frames without changing the frame count
or playback rate.

`OutputClass` validates submissions before dispatch. It waits for queued
writes before closing format writers, suppresses final averages on failure,
and propagates background errors. Queue capacity is acquired before input
snapshots are copied. Existing worker defaults and legacy video scheduling
are retained.

Tests patch dependencies in the module that owns them, for example
`holodoppler.saving.media.save_video` or `holodoppler.saving.data.get_git_version`.
