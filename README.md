# HoloDoppler

## Install

HoloDoppler requires Python 3.13. The production backend is CuPy built for
CUDA 13; NumPy is retained as a reference backend for synthetic tests.

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Verify the CUDA production environment and run the synthetic suite:

```bash
python -c "import cupy as cp; cp.show_config()"
pytest
```

Keep recordings and generated results outside the repository. Start real-data
validation with one short temporal block and check its memory estimate before
increasing the frame or spatial dimensions.

## Command line

### Preview

```bash
holodoppler preview "D:\path\to\recording.holo" "./parameters/default_parameters.json"
```

### Process

```bash
holodoppler process "D:\path\to\recording.holo" "./parameters/default_parameters.json"
```

## Multidimensional analysis

The compatibility boundary is `H[t, y, x]`. Temporal spectra retain the
existing unshifted FFT order and are returned as
`SH[estimate, frequency, ..., y, x]`. A minimal CUDA example is:

```python
import cupy as cp

from holodoppler.Holodoppler import Holodoppler
from holodoppler.multidimensional import (
    analyze_field_block,
    quadrant_masks,
    spectral_estimate_nbytes,
)

processor = Holodoppler(backend="cupy", pipeline_version="latest")
processor.load_file(r"D:\data\recording.holo")

# `parameters` is loaded from the recording-specific JSON configuration.
frames = processor.read_frames(parameters["first_frame"], 32)
H = processor.render_holograms(parameters, frames=frames)["H"]

bytes_per_spectrum = spectral_estimate_nbytes(H.shape, block_length=32)
print(f"one retained complex spectrum set: {bytes_per_spectrum / 2**30:.2f} GiB")

masks = cp.asarray(quadrant_masks(H.shape[-2:]))
result = analyze_field_block(
    H,
    parameters["sampling_freq"],
    masks=masks,
    block_length=32,
)
```

See [the multidimensional processing guide](docs/multidimensional_processing.md)
for the complete axis contract, API mapping, SVD options, and selective export.

## Building the app

```bash
python -m pip install -e .[build]
python build_installer.py
```

## License

This project is licensed under the GNU General Public License v3.0 only. See [LICENSE](LICENSE).
