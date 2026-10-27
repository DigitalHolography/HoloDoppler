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
numpy_num_workers: 8 # CPU workers; 0 or 1 runs sequentially
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
uv sync --all-extras
uv run build_installer.py
```

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
