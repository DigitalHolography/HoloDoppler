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
- `spectral_cube`: streams a registered, reduced-resolution full signed-frequency
  PSD cube to an uncompressed HDF5 dataset ordered as `(t, f, y, x)`.

Select the matching preset in the GUI before changing its pipeline name; each
pipeline has its own required parameters.

The `spectral_cube` preset uses `batch_size` and `batch_stride` as its rectangular
temporal FFT window and stride. It averages the full signed FFT range into
`f_bins` bins, applies one fixed-subpixel translation per temporal window to all
frequency planes at full spatial resolution, and only then performs exact block
averaging by `ratio_y` and `ratio_x`. Its HDF5 file contains `S`, `t`, `f`, `y`,
`x`, `frame_start`, `registration`, and processing metadata. SVD filtering is
controlled by `svd_filter`; only the selected filtered or unfiltered cube is
written. When `spectral_cube_avi` is enabled, every selected `f` bin is also
exported as a time-resolved grayscale MJPEG AVI under `avi/spectral_cube/`.
`spectral_cube_avi_frequency_indices` may be set to `all`, one index, or a list
of indices to control the number of generated videos.

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
