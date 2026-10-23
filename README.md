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

### Preview

```bash
holodoppler preview "D:\path\to\holo.holo" "./parameters/default_parameters_debug.json"
```

### Process

```bash
holodoppler process "D:\path\to\holo.holo" "./parameters/default_parameters_debug.json"
```

### Run the GUI

```bash
holodoppler
```

or explicitly:

```bash
holodoppler gui
```

### Application Logs

CLI, GUI, source runs, and the Windows executable use the same logger and log
format. All `DEBUG`, `INFO`, `WARNING`, and `ERROR` messages are saved to:

```text
%APPDATA%\holodopplerpython\<version>\logs\holodoppler.log
```

The file rotates at 5 MiB and keeps three backups. CLI runs also show the same
messages in the terminal. In the GUI, use **Logs** next to **Run** in minimal
mode or **Stop** in advanced mode to show or hide the log window at any time,
including while processing. Messages use gray for debug, blue for info, amber
for warnings, and red for errors. The latest 2,000 messages remain available
while the window is hidden; the log file retains history up to its rotation
limit. The processing `--debug`
option controls diagnostic outputs; all log levels are available without it.

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

No setup is needed inside processing functions: application entrypoints
configure the logger once. Standalone scripts can call
`from holodoppler.logging import configure_logging` followed by
`configure_logging()` before logging. `get_log_path()` from the same module
returns the active log path. Worker processes forward their messages to the
parent logger so they also appear in the GUI log window.

### Run a Batch of Files in CLI

```bash
holodoppler process --batch "path/to/files.txt" "./parameters/default_parameters_debug.json"
```

Give a `.txt` file with one `.holo` or `.cine` path per line.

### Saving workers in the default pipeline

```yaml
live_saving: true
num_saving_workers: 0
saving_queue_depth: null
```

Set `num_saving_workers` to a positive integer to overlap live saving with
processing. Zero keeps saving synchronous. `saving_queue_depth` limits outstanding
batches, including active writes; `null` uses twice the worker count. Processing
waits when the queue is full, and completion waits for all accepted writes.
The same worker count controls end-of-run saving when `live_saving: false` and
preview exports. ECC still buffers its inputs before saving corrected results.
Worker count controls saving threads; codec settings and output values stay the same.

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

## License

This project is licensed under the GNU General Public License v3.0 only. See [LICENSE](LICENSE).
