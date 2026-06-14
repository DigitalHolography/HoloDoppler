# HoloDoppler

HoloDoppler provides a Qt desktop UI and command-line tools for previewing and
processing `.holo`, `.cine`, and text file lists.

## Install with uv

```bash
uv sync
```

Launch the UI through the managed environment:

```bash
uv run holodoppler
```

To build the Windows app installer dependencies too:

```bash
uv sync --extra build
```

## Install with pip

```bash
python -m venv .venv
source ./.venv/Scripts/activate
python -m pip install -e .
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

The desktop UI uses PySide6 and pyqtgraph. They are installed by the project
dependencies.

## Desktop UI

Launch the application without command-line arguments:

```bash
uv run holodoppler
```

The UI supports:

- selecting `.holo`, `.cine`, or `.txt` input lists;
- drag and drop of supported inputs anywhere on the window;
- selecting a JSON parameter file;
- previewing the first input with pyqtgraph;
- running or stopping processing after the current file.

## Command Line

### Preview

```bash
uv run holodoppler preview "D:\path\to\holo.holo" ".\parameters\default_parameters_debug.json"
```

### Process

```bash
uv run holodoppler process "D:\path\to\holo.holo" ".\parameters\default_parameters_debug.json"
```

## Building app

```bash
uv sync --extra build
uv run python build_installer.py
```
