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

or 

```bash
uv sync --all-extras
uv run build_installer.py
```

## License

This project is licensed under the GNU General Public License v3.0 only. See [LICENSE](LICENSE).

### Default profiles and logging

Both the CLI and UI seed editable parameter profiles from `parameters/` on first
use. Missing profiles are copied without overwriting existing files. The default
profile is `default_parameters_default.yaml`; an explicit CLI configuration takes
precedence. The UI also remembers its selected profile and working edits.

User data lives in `%APPDATA%/HoloDoppler/<version>` on Windows and
`$XDG_DATA_HOME/HoloDoppler/<version>` on Linux (by default,
`~/.local/share/HoloDoppler/<version>`). Existing `holodopplerpython` data is
copied when the new directory does not exist.

Execution and default-pipeline console messages use `HH:MM:SS [info] message`,
with `[warning]` and `[error]` levels and indented parameter/metadata fields.
Pass `--tracebacks` to `process` or `preview` to include exception tracebacks.
Batch processing continues after failed files and returns a failure exit code
if any file failed. UI Stop takes effect after the current file.
