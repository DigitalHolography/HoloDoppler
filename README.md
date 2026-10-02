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

### Run the GUI

```bash
holodoppler
```

or explicitly:

```bash
holodoppler gui
```

The GUI reads and writes presets directly in `parameters/` (the `parameters/`
folder beside the installed executable in packaged builds). Presets may use
`.yaml`, `.yml`, or `.json`. Individual values and newly added parameters also
accept YAML/JSON syntax, so values such as `0.5`, `true`, and `[1, 2]` keep
their numeric, boolean, and list types.

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
The installer packages presets from `parameters/`. It also verifies that the
corresponding fallback files in `holodoppler/ui/defaults/` remain in sync.
Use `python build_installer.py --verify-installer` to run the installer smoke
verification when Inno Setup is available.
