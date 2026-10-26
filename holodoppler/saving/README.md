# Saving package

Pipelines continue to import `OutputClass`, `save_outputs`, and standalone
save helpers from `holodoppler.saving`.

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

`MediaStream` owns encoder handles, first-frame display levels, and the
unquantized temporal sum used for the final PNG. `CsvStream` writes one
flattened row per temporal batch. Complete/static CSV arrays retain their
existing first-axis rows and flatten trailing dimensions into columns.

`OutputClass` validates submissions before dispatch. It waits for queued
writes before closing format writers, suppresses final averages on failure,
and propagates background errors. Queue capacity is acquired before input
snapshots are copied. Existing worker defaults and legacy video scheduling
are retained.

Tests patch dependencies in the module that owns them, for example
`holodoppler.saving.media.save_video` or `holodoppler.saving.data.get_git_version`.
