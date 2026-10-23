# Getting Started

Follow the steps below to install dependencies and run the example.

## 1. Install the Project

```bash
python -m venv .venv
source ./.venv/Scripts/activate
python -m pip install -e .
```

or 

```bash
uv sync
```

or (if cuda is not installed separately)

```bash
uv sync --all-extras
```

## 2. Run the CLI Examples

### Processing pipelines

Available pipeline names are `default`, `lsci`, `pca_accumulation`,
`sliding_shack_hartmann`, and `split_apertures`. Each supports preview and
processing with the profiles in `parameters/`.

For Laser Doppler Holography rendering keep using the `default` pipeline.

### Preview

```bash
holodoppler preview "D:\path\to\holo.holo" "./parameters/default_parameters_default.yaml"
```

### Process

```bash
holodoppler process "D:\path\to\holo.holo" "./parameters/default_parameters_default.yaml"
```

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

### Processing and saving workers in the default pipeline

The processing backend management options should be tuned for your computer specifications.

```yaml
force_numpy: false # force the use of numpy (cpu cores only)
use_parallel: true # use parallel workers cores or not (numpy)
numpy_num_workers: 8 # the number of parallel workers to be used (numpy)
cupy_async: true # GPU pipeline: overlap reading, uploads, computation, and downloads. (cupy)
cupy_prefetch_depth: 4 # Maximum admitted batches; >= 1. Larger values use more RAM/VRAM. (cupy)
```



```yaml
live_saving: true
num_saving_workers: 0
saving_queue_depth: null
```

Compare worker counts on your machine using real encoders and simulated processing:

```bash
python scripts/benchmark_saving.py --workers 0 1 4 --frames 32 --size 256
```

The benchmark reports processing/submission time, final drain time, total time,
and peak queued batches. More workers can increase contention; compare total time.

### Build the Windows Installer

```bash
python -m pip install -e .[build]
python build_installer.py
```

or 

```bash
uv sync --extra build
uv run build_installer.py
```

The build uses PyInstaller's package hooks to include runtime dependencies and
plugins without collecting entire scientific test suites. CUDA libraries,
CuPy kernels/headers, FFmpeg, all processing pipelines, and GUI resources remain
bundled, so users do not need a separate CUDA toolkit installation. A compatible
NVIDIA driver is required for GPU processing.

The installer uses solid LZMA2 `ultra64` compression. This takes more time and
memory to build (about 742 MB for compression, 64 MB for decompression), but the
installed app runs from normal, uncompressed files. Each build writes a
`dist/HoloDoppler-setup-<version>.size.json` report with package sizes and build
dependency versions.

Verify the frozen app's CPU/GPU operations, plotting, GUI resources, HDF5, images,
and video encoding before packaging it:

```bash
uv run build_installer.py --verify-payload
```

Use `--verify-installer` to silently install the generated installer, run those
checks on the installed app, check seeded parameter presets, and uninstall the
test installation. If the same version is already installed, use
`--verify-payload`; installer verification stops before touching that installation.
GPU checks run when a compatible GPU/driver is available;
missing CUDA DLLs or failed kernel compilation fail verification. Reports are
written to `dist/payload-verification.json` and `dist/release-self-test.json`.
For an additional preview/process check on a recording, pass both
`--smoke-holo <file.holo>` and `--smoke-parameters <preset.yaml>`.

### Application Logs

CLI, GUI, source runs, and the Windows executable use the same logger and log
format. All `DEBUG`, `INFO`, `WARNING`, and `ERROR` messages are saved to:

```text
%APPDATA%\HoloDoppler\<version>\logs\holodoppler.log
```

To add messages to any processing file, import the shared logger and call the
method that matches the message:

```python
from holodoppler.logging import logger

logger.debug("Batch size: %s", batch_size)  # Technical details
logger.info("Processing started")         # Normal progress
logger.warning("Some frames were skipped")
logger.error("The input file is missing")

try:
    save_results()
except Exception:
    logger.exception("Could not save results")  # Includes the traceback
    raise
```

## License

This project is licensed under the GNU General Public License v3.0 only. See [LICENSE](LICENSE).
