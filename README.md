# Getting Started

Follow the steps below to install dependencies and run the example.

## 1. Install the Project

```bash
python -m venv .venv
source ./.venv/Scripts/activate
python -m pip install -e .
```

## 2. Run the CLI Examples

### Preview

```bash
holodoppler preview "D:\path\to\holo.holo" "./parameters/default_parameters_debug.json"
```

### Process

```bash
holodoppler process "D:\path\to\holo.holo" "./parameters/default_parameters_debug.json"
```

### Debug And Profile

```bash
holodoppler process "D:\path\to\holo.holo" "./parameters/default_parameters_debug.json" --debug --tictoc
```

```bash
holodoppler preview "D:\path\to\holo.holo" "./parameters/default_parameters_debug.json" --debug --tictoc
```

The `--debug` provides more output visually and `--tictoc` provides information about processing time.

### Available Processing Presets

The GUI and installer include presets for:

- `simple`: GPU processing with optional 2D filtering and subpixel registration.
- `sliding`: sliding-window processing.
- `sliding_shack_hartmann`: accumulated Shack-Hartmann correction.
- `split_apertures`: split-aperture and quadrant correlations.
- `pca_accumulation`: PCA/FFT accumulation.
- `sh_avg`: Shack-Hartmann spectrum averaging.
- `simple_numpy`: CPU multiprocessing.
- `main`: the legacy backend-selectable moments pipeline.
- `spectral_cube`: streams spatially averaged full signed-frequency signal and
  background spectra to uncompressed HDF5 datasets ordered as `(t, f)`.

Select the matching preset in the GUI before changing its pipeline name; each
pipeline has its own required parameters.

Every non-preview processing run also launches `spectral_cube` by default after
the selected moments pipeline. Set `spectral_cube_enabled: false` to opt out.
The spectral pipeline starts from its bundled preset, inherits the acquisition
and optical settings of the selected profile, and accepts independent overrides
through the `spectral_cube_settings` object. The default `simple` profile exposes
these overrides in the GUI.

The `spectral_cube` preset uses `batch_size` and `batch_stride` as its rectangular
temporal FFT window and stride. It averages the full signed FFT range into
`f_bins` bins. For every `(t,f)`, `S` is the spatial median of non-registered data
inside a centered ellipse whose default semiaxes are `0.8 * Ny/2` and
`0.8 * Nx/2`. `S0` is the spatial median of the same non-registered data outside
a centered ellipse whose default semiaxes are `1.2 * Ny/2` and `1.2 * Nx/2`.
`L` is the natural logarithm `ln(S/S0)`, protected only against division by zero
by the smallest positive `float32` value. SVD filtering always removes exactly
the two strongest singular components without a separate temporal-DC
subtraction. Registration is not applied.

The run produces one HDF5 file named `<output-directory>.h5` (without the former
`_output` suffix). Moment and other pipeline datasets remain at its root. The
spectral results are appended to `spectrograms/longtimes` and
`spectrograms/singlebeat`; no separate `_spectral_endpoints.h5` file is created.
Their effective, filtered settings are stored in
`spectrograms/spectral_cube_parameters`. The main file's root metadata remains
the single source of HoloDoppler version information.

The HDF5 `spectrograms/longtimes` group contains the uncompressed
acquisition-time datasets `S(t,f)`, `S0(t,f)`, `L(t,f)`, `t`, `f`, and
`frame_start`. Cardiac segmentation
uses the bins satisfying `abs(f)>fc`, where the resolved cutoff is the minimum
of the configured cutoff (14 kHz by default) and `0.8 * Nyquist`. Each frequency
trace is temporally median-filtered (35 ms by default) and mean-centered. From
the resulting matrix SVD, `g(t) = sigma_1 * U[:,0]` is sign-oriented to correlate
positively with the original high-frequency sum. Positive local maxima of
`dg/dt`, computed on the actual `t` axis after 20 ms Gaussian smoothing by
default, delimit beats. As a final QC step, only maxima strictly above 30% of the
strongest selected positive maximum are retained; the fraction is configurable.
The unfiltered sum is retained as `spectrograms/longtimes/g_sum`. Valid beats are linearly
resampled onto `[0,1)`. Beat-specific broadband streaks are
detected from the frequency mean of each fundus beat and repaired only in `S`
from clean beats at the same phase. The `spectrograms/singlebeat` group contains the median
repaired `S(phase,f)`, independently median-aggregated `S0(phase,f)`, and
`L = ln(S/S0)`, along with phase, frequency, beat timing, streak masks, and QC
metadata.

If no beat survives landmark and duration QC, processing remains non-fatal: all
moment outputs, long-time spectrograms, and available cardiac diagnostics are
saved. The HDF5 status records `pulse_detected = false`; the GUI marks that input
red, continues the batch, and displays the affected-file list when the batch is
finished.

Percentile-adjusted maps are exported as `png/longtimes_S.png`,
`png/longtimes_S0.png`, `png/longtimes_L.png`, `png/singlebeat_S.png`,
`png/singlebeat_S0.png`, and `png/singlebeat_L.png`, with frequency vertical and
acquisition time or cardiac phase horizontal. Cardiac landmark and streak QC
plots are also written to the PNG directory.

### Run the GUI

```bash
holodoppler
```

or explicitly:

```bash
holodoppler gui
```

### Run a Batch of Files in CLI

```bash
holodoppler process --batch "path/to/files.txt" "./parameters/default_parameters_debug.json"
```

Give a `.txt` file with one `.holo` or `.cine` path per line.

### Build the Windows Installer

```bash
python -m pip install -e .[build]
python build_installer.py
```

The installer build script must run under Python 3.13 or newer.
The installer build uses the bundled UI defaults from
`holodoppler/ui/defaults/` and verifies they match `parameters/*.json`,
`parameters/*.yaml`, and `parameters/*.yml`.
Use `python build_installer.py --verify-installer` to run the installer smoke
verification when Inno Setup is available.
