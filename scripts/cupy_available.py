
from __future__ import annotations

import numpy as np
import scipy.fft as np_fft
import scipy.ndimage as np_ndi
from scipy.ndimage import gaussian_filter as np_gaussian_filter
from scipy.ndimage import zoom as scipy_zoom
import scipy.linalg as np_linalg


# ---------------------------------------------------------------------------
# Optional CuPy import
# ---------------------------------------------------------------------------

try:
    import cupy as cp
    import cupyx.scipy.fft as cp_fft
    import cupyx.scipy.ndimage as cp_ndi
    from cupyx.scipy.ndimage import gaussian_filter as cp_gaussian_filter
    from cupyx.scipy.ndimage import zoom as cupy_zoom
    import cupy.linalg as cp_linalg
    _cupy_imported = True

except Exception:
    cp = None
    cp_fft = None
    cp_ndi = None
    cp_gaussian_filter = None
    cupy_zoom = None
    cp_linalg = None
    _cupy_imported = False


# ---------------------------------------------------------------------------
# CUDA usability test
# ---------------------------------------------------------------------------

def _cupy_usable() -> bool:
    """Return True only when CuPy can actually execute CUDA operations.

    Importing CuPy alone is not enough. This test detects cases such as:

        cudaErrorInsufficientDriver

    where CuPy is installed but the NVIDIA driver is missing, incompatible,
    or otherwise unable to execute the CUDA runtime.

    The test performs:
      1. A CUDA device query.
      2. A tiny GPU allocation.
      3. A tiny GPU operation.
      4. A synchronization.
      5. A transfer back to the CPU.

    Returns
    -------
    bool
        True if CuPy is actually usable, False otherwise.
    """
    if not _cupy_imported or cp is None:
        return False

    try:
        # Make sure at least one CUDA device is visible.
        if cp.cuda.runtime.getDeviceCount() < 1:
            return False

        # Actually allocate something on the GPU.
        x = cp.zeros(1, dtype=cp.float32)

        # Perform a real GPU operation.
        x += 1

        # Force CUDA to execute the operation now.
        cp.cuda.runtime.deviceSynchronize()

        # Force a device -> host transfer as a final sanity check.
        return float(x.get()[0]) == 1.0

    except Exception as exc:
        print(
            "CuPy detected but CUDA is not usable; "
            f"falling back to NumPy: {exc}"
        )
        return False


# Test CuPy once when this module is imported.
_cupy_available = _cupy_usable()