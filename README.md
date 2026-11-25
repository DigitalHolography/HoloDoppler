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

Available pipeline names are `default`, `fast`, `lsci`, `pca_accumulation`,
`sliding_shack_hartmann`, and `split_apertures`. Each supports preview and
processing with the profiles in `parameters/`.

Use `fast` for contiguous Fresnel processing with FFT moments or PCA maps,
grouped accumulation, and deferred saving. [Fast pipeline guide](docs/fast-pipeline.md).

See [How the main pipeline works](docs/main-pipeline.md) for the processing
stages, data flow, execution modes, and remaining design concerns. 

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

During processing, click **Stop** in either UI mode to cancel the current file
and skip the remaining inputs. The UI shows **Stopping...** while active work
finishes and resources close, then **Stopped**. Completed files are kept;
the cancelled file is not finalized as a partial result.

The Advanced **Inputs & Preview** panel automatically computes a preview for each
loaded file.

For the default pipeline, display-only previews compute just the configured
`registration_image` and its dependencies. Autofocus fitting, correction, and
acceptance checks are preserved, while unused output images and diagnostic plots
are skipped. When registration is enabled, previews use
`registration_ref_first_frame` and `registration_ref_batch_size`; otherwise they
use the first processing batch. The returned image is the raw registration
reference before shifts or square resizing. The gallery retains it after
processing. Saved previews still produce their full first-batch output bundle,
but return the registration-reference image too.

### Run a Batch of Files in CLI

```bash
holodoppler process --batch "path/to/files.txt" "./parameters/default_parameters_debug.json"
```

Give a `.txt` file with one `.holo` or `.cine` path per line.
You can also give a folder to process all `.holo` and `.cine` files directly
inside it, without searching subfolders:

```bash
holodoppler process --batch "path/to/recordings" "./parameters/default_parameters_debug.json"
```

### Processing and saving workers in the default pipeline

The processing backend management options should be tuned for your computer specifications.

```yaml
backend: "auto" # auto, numpy (CPU), or cupy (GPU)
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

### Paint manual artery, vein, and optic-disc masks

```powershell
python scripts/h5_mask_painter.py "path/to/sample.holo"
```

You can also pass the `sample` run folder, `sample_HD`, its `h5` folder,
or an HDF5 file directly. With no argument, use **Open file** or **Open run folder**.
For a recording, the app opens the alphabetically first HDF5 in
`sample/sample_HD/h5/`. It displays the time average of `moment0ff`, falling
back to `moment0`, including datasets inside groups. Arrays remain in native
`(NT, NY, NX)` order; masks are `(NY, NX)` without transposing or flipping.
The mean is computed in batches. Display contrast uses the 1st–99th percentiles;
gamma and overlay opacity affect only the display.

Paint **Artery**, then **Next mask** for **Vein**, then **Optic disc**.
Left-drag paints, right-drag erases; adjust radius in pixels. Use the toolbar
for zoom/pan, and deactivate its tool to resume painting. Undo/redo retains up
to 30 edits. Layers are independent, allowing artery/vein crossings.
**Soft value [0,1]** paints probabilities (sometimes called logits by DopplerView).
Binary masks use `value > 0.5`; fractional layers are also saved for further editing.

**Save** writes the EyeFlow companion
`sample/sample_DV/h5/sample_DV.h5`; `--output PATH` or **Save as** changes it.
Existing masks at that destination are reopened automatically. Saving updates
the DopplerView paths `segmentation/Retina/{artery_mask,vein_mask,vessel_mask,
vessel_segmentation_logits}` and `segmentation/OpticDisc/{mask,center,width,height}`.
Vessel support is the union of artery and vein. Optic-disc center is `(x,y)`
and dimensions come from the painted bounding box; empty discs have no geometry.
Fractional layers use a `_probability` suffix alongside each painted mask.
EyeFlow thresholds `vessel_segmentation_logits` at `> 0.1`, so low-confidence
soft pixels can enter its vessel support even when excluded from binary masks.

The output has `provenance/manual = true`, `annotation_method = manual_brush`,
source HDF5/background names, and a UTC timestamp. Mask datasets also carry
manual annotation attributes. Saving is atomic and retains unrelated existing
DV fields, but removes old retinal topology labels because painting invalidates
them. Previously computed DV analyses are not recalculated. This supplies manual
segmentation inputs; it does not generate DopplerView topology or analysis results.
The original HD file is never modified.

## License

This project is licensed under the GNU General Public License v3.0 only. See [LICENSE](LICENSE).
