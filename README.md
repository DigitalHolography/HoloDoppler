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

Both launch the dependency-light UI in `holodoppler/ui_simplest.py`. The full
Tkinter UI (advanced/minimal views, settings store, theming) is archived in
`old/ui/`; see `old/README.md`.

### Run a Batch of Files in CLI

```bash
holodoppler process --batch "path/to/files.txt" "./parameters/default_parameters_debug.json"
```

Give a `.txt` file with one `.holo` or `.cine` path per line.

## Output

Every run writes into `<input stem>/<input stem>_HD/`:

| directory | contents |
|---|---|
| `avi/` | one MJPEG AVI per video output (full-range 4:2:2) |
| `mp4/` | the same videos as H.264 with `yuv420p` |
| `png/` | images, and the temporal average of each video |
| `h5/` | numerical outputs, parameters and version stamps |
| `json/`, `csv/`, `yaml/` | metadata and tabular outputs |

The saving stage prints a single summary line, for example:

```
Saving completed in 12.3 seconds
  videos[avi]: 6 | videos[mp4]: 6 | pngs: 7 | csv: 1 | json: 3 | h5: 1
```

The installer build script now lives in `old/` and is not part of the normal
workflow (see `old/README.md`).
