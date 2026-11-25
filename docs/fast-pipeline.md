# Fast pipeline

```bash
holodoppler process recording.holo parameters/default_parameters_fast.yaml --accu=3
holodoppler preview recording.holo parameters/default_parameters_fast.yaml --mode=pca
```

Fast reads contiguous, nonoverlapping windows of `time_window` frames. It averages
`accu` windows into one image and drops incomplete trailing groups. Preview uses
the first complete group. The output rate is `sampling_freq / (time_window * accu)`.
The preset resolves optical parameters from a Holo recording. For other
recordings, supply the distance, pixel pitch, and sampling frequency explicitly.

FFT mode exports `moment0`, `moment1`, `moment2`, and `moment0ff`. The moments
use power weighted by signed frequencies in Hz to the corresponding order.
`frequency_ranges` takes a union of zero-based half-open ranges in raw FFT order.
With 64 frames, `[[4, 31], [33, 60]]` retains bins 4–30 and 33–59. Set these
ranges to fit any changed window size. A positive `svd_filter` rejects the
largest modes, a negative value rejects the smallest, and zero bypasses SVD.
Explicit DC subtraction is disabled. PCA mode exports `pca_sum` and its flatfielded counterpart `pca_sum_ff`. Component
magnitudes are summed over `pca_index_range` in ascending eigenvalue order.

Optional autofocus averages the first group's Fresnel subaperture images before
estimating shifts and fitting one phase mask. Optional registration uses the
first completed group's flatfielded image as its fixed translation reference.

Saving starts after compute. Output buffers require about
`4 × height × width × number of output groups × number of maps` bytes of RAM,
plus working buffers. Use a shorter frame range or increase `accu` to reduce RAM
use. The optional `outputs` mapping selects formats. The default export is
uncompressed HDF5.

To evaluate the disk throughput target, time a read-only pass over the same
windows using the file reader and record bytes per second. Compare with Fast's
logged compute rate in source frames per second multiplied by on-disk frame size.
Log export time separately and record whether each run uses a warm OS page cache.
Repeat in FFT and PCA modes, with SVD, autofocus, and registration measured in
separate runs as applicable.
