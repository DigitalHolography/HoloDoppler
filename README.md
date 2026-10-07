# Getting Started

Follow the steps below to install dependencies and run the example.

## 1. Install the Project

```bash
python -m venv .venv
source ./.venv/Scripts/activate
python -m pip install -e '.[gui,gpu]'
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

### Run a Batch of Files in CLI

```bash
holodoppler process --batch "path/to/files.txt" "./parameters/default_parameters_debug.json"
```

Give a `.txt` file with one `.holo` or `.cine` path per line.

### Build the Windows Installer

```bash
python -m pip install -e '.[gui,gpu,build]'
python build_installer.py
```

The installer build script must run under Python 3.13 or newer.
The installer build uses the bundled UI defaults from
`holodoppler/ui/defaults/` and verifies they match `parameters/*.json`,
`parameters/*.yaml`, and `parameters/*.yml`.
Use `python build_installer.py --verify-installer` to run the installer smoke
verification when Inno Setup is available.

### Docker CLI on Windows or Linux

The [CLI starter](docker/README.md) includes `input/`,
`config/parameters.yaml`, and `output/`. Put recordings in `docker/input/`,
edit the settings if needed, and run:

```powershell
.\docker\run-cpu.cmd -Build
# Or, with an NVIDIA GPU:
.\docker\run-gpu.cmd -Build
```

`-Build` builds from this source checkout. Once the images are built or
published, run without `-Build`. On Linux / WSL, use
`sh docker/run.sh --build` or `sh docker/run.sh --build --gpu`.

See [the Docker guide](docs/docker.md) for CPU and NVIDIA GPU images with CLI or
GUI targets, display and data mounts, and the image release workflow.
