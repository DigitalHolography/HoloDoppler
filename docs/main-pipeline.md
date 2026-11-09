# How the main HoloDoppler pipeline works

This documents the `default` Laser Doppler Holography pipeline as implemented in
[`main_default.py`](../holodoppler/pipelines/main_default.py). It describes current
behavior, including surprising details; proposed improvements are listed separately.
The other registered pipelines (`lsci`, `pca_accumulation`,
`sliding_shack_hartmann`, `split_apertures`) are outside this walkthrough.

## Entry points and ownership

```bash
holodoppler preview path/to/recording.holo parameters/default_parameters_default.yaml
holodoppler process path/to/recording.holo parameters/default_parameters_default.yaml
```

To override the profile's backend for one run:

```bash
holodoppler process path/to/recording.holo parameters/default_parameters_default.yaml --backend numpy
```

The current profile uses these controls (excerpt, not a complete configuration):

```yaml
pipeline_name: default
backend: auto # auto, numpy, or cupy
save_averaged_spectrogram: true
directional_Doppler_image: true
```

There is no temporal-transform selector. The default pipeline always computes
the temporal FFT, and uses `moment0`, `moment0ff`, `moment1`, and `moment2`
throughout computation, registration, rendering, and saving.

The CLI loads YAML/JSON, applies overrides, and dispatches using `pipeline_name`.
The lazy registry maps `default` to `main_default.process` and `preview_default`
to `main_default.preview`. The registry forwards callbacks only when the called
function accepts them.

| Code | Responsibility |
| --- | --- |
| [CLI](../holodoppler/cli/command.py), [registry](../holodoppler/pipelines/__init__.py) | Configuration loading and pipeline dispatch |
| [Configuration](../holodoppler/config/) | Resolve metadata placeholders and validate parameters |
| [File readers](../holodoppler/file_reader/file_reader.py) | Read `.holo` or `.cine` frame batches |
| [Default pipeline](../holodoppler/pipelines/main_default.py) | References, optical processing, outputs, finalization |
| [Batch runner](../holodoppler/core/processing.py) | Ordered CPU/GPU execution and progress |
| [Filtering](../holodoppler/core/filtering.py), [propagation](../holodoppler/core/propagation.py), [moments](../holodoppler/core/moments.py) | Numerical operations |
| [Saving](../holodoppler/saving/README.md) | Output selection, bounded saving jobs, media and numerical exports |

## Overall flow

```mermaid
flowchart TD
    A[Input recording and parameters] --> B[Resolve metadata and validate]
    B --> V[Validate registration and autofocus reference bounds]
    V --> C[Select complete batches]
    C --> D[Optional fixed Shack-Hartmann autofocus]
    D --> E[Optional registration reference]
    E --> F[Read next batch]
    F --> G[Optional spatial high-pass filter]
    G --> H[Optional per-batch wavefront estimate]
    H --> I[Spatial propagation with phase correction]
    I --> J[SVD clutter rejection]
    J --> K[Temporal FFT]
    K --> L[Power spectrum, moments and band maps]
    L --> M[Optional translation registration]
    M --> N{ECC enabled?}
    N -->|No| O[Resize scalar maps and render Doppler colors]
    O --> P[Stream outputs or retain in RAM]
    N -->|Yes| Q[Retain all batches in RAM]
    Q --> R[ECC registration after all batches]
    R --> S[Resize, render colors and save]
    P --> T[Save static diagnostics and close writers]
    S --> T
```

The temporal FFT always runs; it is part of the spectral pipeline, not a setting.

## 1. Setup and batch selection

The backend initially prefers CuPy if an actual CUDA operation succeeds;
otherwise it uses NumPy/SciPy. Each run selects `backend: auto`, `numpy`, or
`cupy`; the CLI can override it with `--backend`. Selecting `cupy` falls back
to NumPy if CUDA is unavailable.

The reader supplies file metadata. Values marked `use_holovibes` are resolved
from the `.holo` footer; supported `.cine` values marked `use_metadata` are
resolved from its header. Explicit numerical values remain unchanged. The
default pipeline passes its parameter mapping to resolvers that mutate it.
Validation happens once after resolution in shared preview/process setup. Enabled
registration and autofocus reference bounds are checked next, before processing
batch indices are calculated or output writers are opened. Preview retains its
first-batch behavior without translation registration or ECC. The registration
reference receives the fixed autofocus correction when autofocus is enabled.

[`calculate_batch_indices`](../holodoppler/core/batching.py) schedules only complete
batches. Let `N = batch_size`, `s = skip_every` (1 when omitted), and `b` be a
batch's starting source-frame index. The batch reads:

```text
b, b+s, b+2s, ..., b+(N-1)s
```

Starts advance by `batch_stride` source frames. `end_frame` is exclusive;
zero or a negative value means the end of the file. A batch fits when its last
selected frame is below that limit. Incomplete trailing batches are dropped.
If there are no complete batches, `process()` returns without producing outputs.

For example, `batch_size=256`, `skip_every=2`, `batch_stride=256` reads
`0,2,...,510`, then `256,258,...,766`: the batches overlap. Increasing
`skip_every` does not automatically increase the stride.

Batch arrays use `(N, H, W)`. The effective sampling frequency for frequency
calculations is `sampling_freq / s`, and FFT-bin spacing is that rate divided
by `N`. Batch cadence is instead `sampling_freq / batch_stride`.

## 2. Wavefront correction and registration references

### Fixed Shack-Hartmann autofocus

When enabled, `_get_autofocus_phase_term()` reads a reference starting at
`registration_ref_first_frame`, with `shack_hartmann_autofocus_batch_size`
selected frames (falling back to `batch_size`). This happens even if translation
registration is disabled. The reference receives the optional 2-D filter.

`_process_shack_hartmann()` constructs subaperture images using Fresnel or angular
spectrum propagation and estimates their displacements. It uses either the
graph-Laplacian or the alternative displacement method, then fits the selected
Zernike modes. The correction is `exp(-1j * phase)`.

Autofocus rejects missing/nonfinite coefficients, absence of mode 4, excessive
absolute Z4, or a missing/nonfinite phase. Rejection logs a warning and continues
without correction; it does **not** fall back to per-batch Shack-Hartmann.
Coefficients and diagnostics can still be saved after rejection.

An accepted correction is reused for every batch. For Fresnel propagation,
`_fixed_fresnel_kernel()` combines it with the input kernel once before scheduling.
Matching autofocus and explicit registration references reuse the raw frame read.

### Translation reference

When `image_registration` is enabled, full processing uses the configured
`registration_ref_first_frame` and `registration_ref_batch_size`. If these match
the first processing batch, its `moment0ff` becomes the reference. Otherwise a separate
reference batch is processed through filtering, wavefront correction, propagation,
SVD, and the zeroth moment; unrelated outputs are skipped.

When autofocus is disabled and `shack_hartmann` is enabled, a fresh phase correction
is estimated per processing batch, and for a separately processed reference.

## 3. Processing one batch

`_process_one_batch()` wraps `_process_batch()` and translation registration.

1. **Optional spatial filtering:** `filter_2d()` applies a spatial FFT, removes
   a central elliptical low-frequency region, and transforms back.
2. **Optional live wavefront estimate:** used only when fixed autofocus is
   disabled and `shack_hartmann` is enabled.
3. **Spatial propagation:** Fresnel or angular spectrum reconstructs complex
   holograms, applying the supplied phase correction when present.
4. **SVD clutter rejection:** holograms are cast to complex64. The implementation
   forms an `N × N` temporal covariance, eigendecomposes it, and projects away
   selected dominant modes. `number_of_values` removes the leading count;
   `amplitude_threshold` selects covariance eigenvalues above the threshold.
   `svd_remove_dc` subtracts the temporal mean first. A negative SVD threshold
   bypasses the entire filter, including mean removal. Pixel blocks limit
   intermediate work arrays, not total memory.
5. **Temporal FFT:** `fft(..., axis=0, norm="ortho")` always produces the complex
   spectrum. By default no temporal window is applied. With `welch_enabled: true`,
   complete segments of `welch_batch_size` selected frames (default 32) start every
   `welch_stride` selected frames (default 32); incomplete trailing segments are
   discarded. Both sizes must be positive integers; neither accepts null.
   `welch_windowing: null` applies no taper; a name such as `hann` or `hamming`
   selects a SciPy periodic taper. No additional detrending is performed.
6. **Power spectrum:** `P = abs(spectrum)**2`, optionally followed by corner
   compensation. Welch averages segment powers, normalized by the taper's mean
   squared weight when present, using one segment at a time. Frequency bins use
   the segment FFT length; all moments, Doppler maps and saved spectra use this
   averaged spectrum. Registration reference images use the same Welch settings
   and must contain at least one complete segment. Shack-Hartmann wavefront
   estimation is unchanged. Input `batch_size`, `batch_stride`, and output cadence
   remain unchanged; strides larger than the segment length leave gaps.
7. **Directional intermediates:** optional positive/negative maps are zeroth
   moments (sums of power) over directional PSD bins, with energy-preserving
   flat-field normalization. The existing inclusive directional bin intervals
   are preserved; they differ from the strict moment-band mask below.
8. **Moments and bands:** reduce selected frequency bins into spatial maps.
9. **Flat-field correction:** `moment0ff = moment0 / gaussian_filter(moment0, sigma)`,
   returning zero wherever the blurred denominator is zero (also for extra ranges).
10. **Translation registration:** estimate `(shift_y, shift_x)` against reference
    `moment0ff` and apply it to the selected scalar maps, Doppler intermediates, and
    retained PSD. Save the shift as `registration`.

The main frequency mask uses **strict** bounds:
`low_freq < abs(f) < high_freq`; omitting `high_freq` removes the upper bound.
Frequencies retain their signs in the moment calculation:

```text
moment0(y,x) = sum P(f,y,x)
moment1(y,x) = sum f * P(f,y,x)
moment2(y,x) = sum f² * P(f,y,x)
```

These are raw discrete sums: there is no division by `moment0` or multiplication by
frequency-bin width. `moment1` can cancel between positive and negative frequencies;
it is not a mean speed. Interpreting these as physical flow quantities requires
additional calibration and conventions outside this function.

## 4. Outputs and finalization

| Saved name | Meaning / shape before saving |
| --- | --- |
| `moment0`, `moment1`, `moment2` | Canonical names throughout processing; one `(H,W)` map per batch |
| `moment0ff` | Gaussian flat-field-normalized `moment0` |
| `spectrum_line` | Spatial mean of the full PSD; `(N,)` per batch |
| `band_k_low_high` | Mean PSD over the selected symmetric band; NaN if empty |
| `moment0_range_*`, `moment1_range_*`, `moment0ff_range_*` | Optional additional range moments and normalized power |
| `spectrograms` | Spatially resized, frequency-selected and frequency-binned PSD per batch |
| `averaged_spectrogram` | Full PSD averaged over the number of completed batches |
| `registration`, `registration_ecc` | Translation shifts and optional ECC transformations |
| `color_Doppler_image` | RGB composite from Gaussian-normalized low/high positive-frequency magnitude bands |
| `directional_Doppler_image` | HSV-derived RGB encoding of positive/negative spectrum maps |
| `shack_hartmann_*` | Optional wavefront, subaperture, coefficient and shift diagnostics |

With ECC disabled, `_finalize_spatial_result()` optionally resizes scalar maps
to `(max(H,W), max(H,W))`, then renders color/directional composites and removes
their internal intermediates. This stretches rectangular maps; it is not padding.
The default color mode decorrelation-stretches `[high, low, low]`; an alternative
uses Lab color with `moment0` lightness.
Each color band sums spectral magnitudes over MATLAB-style bins
`round(low*N/fs)+1:round(high*N/fs)`, clamped to `1:ceil(N/2)`.
Its Gaussian background uses `max(registration_flatfield_gw, 20)` with
replicate padding; zero backgrounds produce zero. With Welch enabled,
magnitudes are obtained from the square root of the Welch power spectrum.

ECC runs after all batches on the CPU, using the first computed `moment0ff` as
reference. It can follow translation registration if both are enabled. It warps
selected maps and Doppler intermediates, then finalizes each batch individually.
The full averaged PSD does not receive ECC correction.

### Execution and memory

Profiles group the workspace limits and subaperture execution mode under
`# backend management`:

```yaml
svd_block_size_mib: 8
registration_block_size_mib: 8
shack_hartmann_sub_aps_process: sequential # sequential or parallel
```

Both MiB settings accept a positive finite number or `null`. A numeric value
targets the size of an individual work array, not total RAM/VRAM consumption.
`svd_block_size_mib: null` processes all pixels in one block, including each
subaperture in sequential Shack-Hartmann processing.
`registration_block_size_mib: null` transforms the entire stack at once.
Omitting either setting keeps the 8 MiB default.

The subaperture mode is independent of these limits: `sequential` processes
subapertures one at a time; `parallel` uses batched SVD/FFTs and does not use the
SVD pixel-block limit. Choosing `null` removes workspace limiting; it does not
automatically change the execution mode or check available memory.

The shared `run_batches()` always delivers results in input order:

- **CPU:** 0 or 1 worker runs sequentially; larger counts use a bounded thread
  pool, capped at `max(1, cpu_count - 2)`. If needed, the first batch establishes
  a registration reference before parallel processing starts.
- **Synchronous GPU:** sequential batches, synchronized before consumption.
- **Asynchronous GPU:** one reader thread plus upload, compute, and download
  CUDA streams. Events enforce dependencies; compute remains ordered on a
  single stream. Pinned host buffers support transfers. `cupy_prefetch_depth`
  bounds all admitted batches, including pending reads. Consumption waits for
  the oldest result's download.

With `live_saving: true` and ECC disabled, results go straight to `OutputClass`.
With live saving disabled, temporal outputs are allocated after the first result
and retained for all batches. **ECC forces this buffering even with live saving
enabled.** On GPU, the full-PSD aggregate stays on device until finalization;
on CPU it is accumulated by the consumer. Both paths divide the accumulated PSD
by the number of completed batches once, before saving.
`averaged_spectrogram` is written to HDF5 only once at finalization; batch
updates modify the in-memory accumulator, never an HDF5 dataset.
The aggregate is exported only to HDF5; it produces no AVI, MP4, or PNG.
Streaming HDF5 datasets use one-batch chunks to avoid rewriting previous batches.
`h5compression` defaults to `0` (uncompressed); levels `1`–`9` enable gzip
for numerical HDF5 arrays, including the final averaged spectrogram, in both
live and buffered saving. Higher levels trade saving CPU time for smaller files.

For `B` completed batches, the saved aggregate is:

```text
averaged_spectrogram(f,y,x) = (1/B) * sum_b PSD_b(f,y,x)
```

Each batch contributes equally, including overlapping batches. Translation
registration is applied to each retained PSD before accumulation when enabled;
ECC is not applied to this aggregate. Frequency binning for the per-batch
`spectrograms` output does not change the full frequency axis of this average.

Saving workers are separate from processing workers. Their bounded queue applies
backpressure, propagates errors, and drains before writers close. Media averages
use unquantized values before final PNG generation. Numerical HDF5 exports follow
an explicit name policy; rendered Doppler images and extra range moments are
excluded. Coefficients and registration data also receive CSV exports.

The normal destination is `<input parent>/<stem>/<stem>_HD/`, with preview in
its `preview` subdirectory. Overwrite policy can change destination handling.
Video playback defaults to 30 FPS unless `output_fps` is explicitly supplied;
it is not automatically the acquisition-derived batch cadence.

### Preview differs from full processing

Preview reads one batch at `first_frame`, optionally computes fixed autofocus,
processes and finalizes that batch, saves a preview bundle, and returns the NumPy
`moment0ff` image. Full `process()` saves outputs and returns `None`.

Preview uses its own `moment0ff` as the translation reference, ignoring a separately
configured registration reference. It does not run ECC or the normal spectrogram
preparation/aggregation path; retained PSD is saved as `sh_psd`. It also does not
use the full run's precombined Fresnel kernel optimization. A preview therefore
does not exercise every behavior of a full run.

## Review: remaining design concerns

The changes above resolve the original sum/average mismatch, backend selection,
zero-denominator flat-field division, configurable temporal FFT, amplitude-based
directional power, and internal moment-name translation. Remaining observations
come from code review, not scientific validation against experimental recordings.

1. **Directional bin boundaries differ from moment bands.** Directional maps now
   sum the same PSD as the moments, including optional corner compensation, but
   retain inclusive, one-based-derived bin intervals. These can include DC at low
   cutoffs, whereas moment masks use strict `fftfreq` bounds. Agree on the scientific
   binning convention before changing these boundaries.
2. **Moments are raw sums.** Signed `moment1` cancellation, unnormalized `moment2`,
   and the distinction between band means and moment sums need to remain explicit
   in the output contract and metadata.
3. **There are two orchestration implementations.** `core/pipeline.py` provides
   setup, accumulation, ECC and saving for other pipelines. The default pipeline
   still owns its own orchestration for GPU aggregation and delayed color rendering.
   Default preview and process share local setup and validation helpers without
   importing `core.pipeline`.
4. **Output meaning is encoded in strings and dimensions.** Registration, resizing
   and saving independently infer semantics from keys and shapes. An output
   specification with axes, spatial/temporal role, registration policy and export
   formats would make additions safer. Generic saving shape inference can confuse
   a grayscale stack of width 3 or 4 with a color image.
5. **Preview and full processing offer different guarantees.** Preview does not
   verify explicit-reference alignment, ECC, or spectrogram binning. Shared setup
   and finalization with an explicit preview policy would reduce drift.
6. **Configuration is mutable and inconsistently defaulted.** Metadata resolution
   can change the caller's dictionary. Validation sometimes checks a default
   without inserting it, while processing later indexes the key directly. Build a
   complete resolved configuration once. Legacy spellings such as
   `Fresnel_use_ouput_kernel` and `save_spectograms` also remain.
7. **Memory and time behavior can surprise users.** ECC buffers all outputs even
   with live saving; video playback FPS is independent of acquisition cadence.
   Both should be visible before a run, with buffering estimates and distinct
   timing metadata.
8. **`_process_to_output()` has many responsibilities.** It owns reference setup,
   GPU aggregation, callbacks, ECC, and static/temporal saving. Explicit run state
   and finalization functions could clarify ownership and failure cleanup.

### Registration image and PCA flatfield

`registration_image` defaults to `moment0ff` and selects the computed scalar image
used for translation and ECC, including separately computed references. Examples
are `pca_sum`, `pca_sum_ff`, and `band_0_3000_6000`. Enable the corresponding
computation first; unavailable keys log a warning and fall back to `moment0ff`.
With `pca_compute: true`, setting `pca_flatfield: true` applies Gaussian flatfield
correction using `registration_flatfield_gw` and emits only `pca_sum_ff` instead
of `pca_sum`. Both PCA variants support numerical and media exports.

The `pca_accumulation` pipeline always emits both `pca_sum` and `pca_sum_ff`.
Each output averages PCA magnitude sums from `accumulation` consecutive
`batch_size`-frame packets, using the `pca_range` component slice. Flatfield
correction is applied after averaging. Output starts advance by `batch_stride`
source frames, independently of accumulation; only full accumulation groups are
processed. With `skip_every`, packet sizes count sampled frames.
Live registration uses the first accumulated `pca_sum_ff` as a fixed reference
and shifts both accumulated outputs. Optional ECC runs on the completed
`pca_sum_ff` sequence and transforms both outputs before square resizing.
Preview returns the first accumulated `pca_sum_ff`. This pipeline does not run
Doppler moments, spectral filtering, or Shack-Hartmann correction.
Saved metadata retains the packet `batch_size` and `accumulation`, with
`output_frame_stride` equal to `batch_stride`. Unless explicitly configured,
video FPS is `sampling_freq / batch_stride` when sampling frequency is available.


Gaussian spectral width is enabled by `compute_gaussian_width: true`. The output
`gaussian_width` is intrinsic Gaussian FWHM in Hz, using the magnitude of the
post-SVD PSD in double precision (Welch when enabled), before corner compensation
and moment cutoffs. At least five FFT bins are required.
The estimator always uses every FFT bin of the complete spectrum.
For effective sampling frequency fs (accounting for frame skipping), define
Hk = sum abs(PSD(f)) exp(-i 2 pi k f/fs).
Then sigma = fs/(pi*sqrt(6)) * sqrt(log(abs(H1))-log(abs(H2))) and
FWHM = 2*sqrt(2*log(2))*sigma. No flat-field correction is applied.
An estimate is valid only for finite positive spectral sums, finite harmonic
magnitudes exceeding 100*double-epsilon*sum(abs(PSD)), and abs(H1)>abs(H2).
Invalid estimates return zero, matching the MATLAB implementation (despite its
comment promising NaN). Outputs are registered and saved alongside other scalar
maps, including numerical HDF5 data.

### Global and Local block SVD

The global SVD also provides `pc_sum_static` and `pc_sum_dynamic`: real images
summing absolute temporal PC coefficients over removed and retained components,
respectively. These use the input after optional temporal DC subtraction, before
local SVD or spectral processing. They sum amplitudes, rather than powers.
`svd_eigenvalues` contains descending, unnormalized covariance eigenvalues;
HDF5 and CSV use shape `(batches, temporal_components)`, with one batch per row.
The default and offline profiles enable these exports. Existing explicit `outputs`
configurations must select the new names, for example:

```yaml
outputs:
  pc_sum_static: [avi]
  pc_sum_static_time_projection: [png]
  pc_sum_dynamic: [avi]
  pc_sum_dynamic_time_projection: [png]
  svd_eigenvalues: [h5, csv]
```

The `_time_projection` PNGs average the component-sum images across batches.
Negative `svd_threshold` still disables filtering; requested diagnostics then use
uncentered input, with zero static projection and all components in dynamic.

Adaptive global SVD modes can replace `number_of_values`:

- `svd_filter_mode: effective_rank` removes
  `ceil(svd_effective_rank_multiplier * exp(-sum(p * log(p))))` components,
  capped at the temporal dimension. The multiplier defaults to `1.0` and must
  be finite and nonnegative.
- `svd_filter_mode: participation_ratio` removes
  `ceil(svd_participation_ratio_multiplier / sum(p**2))` leading components,
  capped at the temporal dimension. This rank equals `(sum(lambda)**2) / sum(lambda**2)`.
  The multiplier defaults to `1.0` and must be finite and nonnegative; zero removes no modes.
- `svd_filter_mode: energy_fraction` removes the smallest leading count reaching
  `svd_energy_fraction` of total covariance energy (default `0.9`, range `(0, 1]`).

Here `p` is the normalized nonnegative eigenvalue spectrum; zero entries do not
contribute to entropy. Numerical negative eigenvalues are clipped only for rank
selection; exported values remain raw. Zero-energy input removes zero modes.
All three modes ignore a nonnegative `svd_threshold`. The shared filter supports these
modes in other pipelines too; the new saved summaries belong to the default pipeline.

Set `svd_filter_by_bloc: true` to apply local SVD after global SVD in the default pipeline.
`svd_filter_by_bloc_window_size` is the square window side in pixels (default 5);
`svd_filter_by_bloc_window_stride` sets the window step along both spatial axes (default 1).
Increase it to run fewer local SVDs. It must be an integer between 1 and the
window size. Overlapping estimates are averaged, and final windows align with
the image edges so every pixel is covered. Windows must fit the image.
`svd_filter_by_bloc_threshold` counts leading singular components to remove
(default 0, disabling SVD). This count is independent of `svd_filter_mode`.
In both modes, `svd_remove_dc` subtracts each pixel's temporal mean before SVD,
including at threshold zero. The existing negative global threshold bypass remains unchanged.

Local block filtering uses spatial covariance `M?M` with `M` shaped
`(time, window_size?)`, removing the largest eigenvalue modes via projection.
`svd_filter_by_bloc_parallel: true` processes all windows in one batched solve.
The default `false` uses vectorized batches controlled by
`svd_filter_by_bloc_mib_block_size` (default 8 MiB; null processes all windows).
This is an estimated temporary-memory target, excluding input/output arrays
and eigensolver workspace; at least one window is processed per batch.
Parallel mode ignores this memory target and can require substantial RAM/VRAM.


## Explicit default output configuration

The default profiles use `DefaultOutput` and an `outputs` mapping. For example:

```yaml
outputs:
  moment0: [h5, avi]
  moment0_time_projection: [h5, png]
  "band_*": [h5, mp4]
  "band_*_time_projection": [png]
  spectrum_line: [h5, csv]
  spectrograms: [h5]
  averaged_spectrogram: [h5]
```

Exact names override glob rules, including an empty list to disable a dataset.
Otherwise the last matching glob wins. Omitted datasets are not exported.
Format lists accept `h5`, `avi`, `mp4`, `csv`, and `png`; paths retain the usual
format subdirectories and shared HDF5 file. Invalid configuration fails before
processing. Unknown or unavailable exact output names warn at finalization.

Selecting an optional output enables its computation regardless of its legacy
compute/save flag. This includes Gaussian width, PCA, Doppler colors, live
Shack-Hartmann diagnostics, and spectra. Algorithm settings still configure the
computation: for example `pca_flatfield` determines whether PCA produces `pca_sum`
or `pca_sum_ff`. Autofocus and registration remain controlled by their processing
flags, and registration dependencies are retained even when not exported.

Every temporal output can have an independently selected `_time_projection`
dataset: an arithmetic mean over completed output batches, after registration,
resizing, and rendering. Projection-only selection does not save the source
stack. Streaming accumulates a running sum; buffered and ECC processing use the
same writer after correction. There are no implicit average PNGs. Cancellation
and writer failures do not finalize projections. `resize_averaged_images` applies
to projection PNGs. The existing full-spectrum temporal mean retains its name
`averaged_spectrogram`; no automatic renamed alias is generated. Explicitly
selecting `spectrograms_time_projection` averages the cropped/binned spectrograms,
which differ from the full-spectrum aggregate.

HDF5 accepts numerical datasets. AVI/MP4 accept temporal grayscale or RGB/RGBA
images; PNG accepts static images and image projections. CSV accepts scalar,
vector, and table datasets, including spectrum lines and registration traces;
spatial images and spectral cubes are not flattened into CSV. A spectral cube
cannot become a video merely because its last axis happens to have length 3 or 4.
Incompatible dataset/format pairs warn once with their name, shape, and reason,
while compatible exports continue. Actual encoder and filesystem failures raise.

YAML without `outputs` retains the legacy saving behavior. Other pipelines keep
their existing interfaces. The default pipeline uses the new selection in saved
previews as well as streaming and buffered processing; display-only previews
continue computing only their registration reference.
