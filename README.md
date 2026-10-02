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

### Run a Batch of Files in CLI

```bash
holodoppler process --batch "path/to/files.txt" "./parameters/default_parameters_debug.json"
```

Give a `.txt` file with one `.holo` or `.cine` path per line.

## Output

Every run from `<input stem>.<input extension>` writes into `<input stem>/<input stem>_HD/`:

| directory | contents |
|---|---|
| `avi/` | one MJPEG AVI per video output (full-range 4:2:2) |
| `mp4/` | the same videos as H.264 with `yuv420p` |
| `png/` | images, and the temporal average of each video |
| `h5/` | numerical outputs, parameters and version stamps |
| `json/`, `csv/`, `yaml/` | metadata and tabular outputs |
