"""Backend management for NumPy/CuPy switching.

CuPy is preferred when available. If CuPy is installed but the CUDA runtime
is not actually usable, the backend automatically falls back to NumPy.
"""

from __future__ import annotations

import numpy as np
import scipy.fft as np_fft
import scipy.ndimage as np_ndi
from scipy.ndimage import gaussian_filter as np_gaussian_filter
from scipy.ndimage import zoom as scipy_zoom


# ---------------------------------------------------------------------------
# Optional CuPy import
# ---------------------------------------------------------------------------

try:
    import cupy as cp
    import cupyx.scipy.fft as cp_fft
    import cupyx.scipy.ndimage as cp_ndi
    from cupyx.scipy.ndimage import gaussian_filter as cp_gaussian_filter
    from cupyx.scipy.ndimage import zoom as cupy_zoom

    _cupy_imported = True

except Exception:
    cp = None
    cp_fft = None
    cp_ndi = None
    cp_gaussian_filter = None
    cupy_zoom = None
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


# ---------------------------------------------------------------------------
# Backend manager
# ---------------------------------------------------------------------------

class BackendManager:
    """Manage NumPy/CuPy backend selection.

    Parameters
    ----------
    backend:
        Accepted values:

        - ``"auto"``  : use CuPy if actually usable, otherwise NumPy.
        - ``"numpy"`` : force NumPy.
        - ``"np"``    : alias for NumPy.
        - ``"cpu"``   : alias for NumPy.
        - ``"cupy"``  : request CuPy; falls back to NumPy if unusable.
        - ``"cp"``    : alias for CuPy.
        - ``"gpu"``   : alias for CuPy.
    """

    def __init__(self, backend: str = "auto"):
        self.backend_name = backend.lower()

        self.xp = None
        self.fft = None
        self.gaussian_filter = None
        self.ndi = None
        self.zoom = None

        self._init_backend()

    # ------------------------------------------------------------------
    # Backend initialization
    # ------------------------------------------------------------------

    def _init_backend(self) -> None:

        # --------------------------------------------------------------
        # Explicit NumPy
        # --------------------------------------------------------------

        if self.backend_name in {"numpy", "np", "cpu"}:
            self.backend_name = "numpy"

            self.xp = np
            self.fft = np_fft
            self.gaussian_filter = np_gaussian_filter
            self.ndi = np_ndi
            self.zoom = scipy_zoom

            return

        # --------------------------------------------------------------
        # CuPy / auto
        # --------------------------------------------------------------

        if self.backend_name in {"cupy", "cp", "gpu", "auto"}:

            if _cupy_available:
                self.backend_name = "cupy"

                self.xp = cp
                self.fft = cp_fft
                self.gaussian_filter = cp_gaussian_filter
                self.ndi = cp_ndi
                self.zoom = cupy_zoom

                return

            # CuPy is not usable -> NumPy fallback
            self.backend_name = "numpy"

            self.xp = np
            self.fft = np_fft
            self.gaussian_filter = np_gaussian_filter
            self.ndi = np_ndi
            self.zoom = scipy_zoom

            return

        # --------------------------------------------------------------
        # Unknown backend
        # --------------------------------------------------------------

        raise ValueError(
            f"Unknown backend {self.backend_name!r}. "
            "Use 'auto', 'numpy' or 'cupy'."
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_gpu(self) -> bool:
        """True when CuPy is the active backend."""
        return self.backend_name == "cupy" and self.xp is cp

    @property
    def is_numpy(self) -> bool:
        """True when NumPy is the active backend."""
        return self.backend_name == "numpy"

    # ------------------------------------------------------------------
    # Array conversion
    # ------------------------------------------------------------------

    def to_backend(self, arr):
        """Convert/move an array to the active backend."""
        if self.is_gpu:
            return cp.asarray(arr)

        return np.asarray(arr)

    def to_numpy(self, arr):
        """Convert an array to NumPy."""
        if self.is_gpu and isinstance(arr, cp.ndarray):
            return cp.asnumpy(arr)

        return np.asarray(arr)

    # ------------------------------------------------------------------
    # GPU utilities
    # ------------------------------------------------------------------

    def clear_gpu_memory(self, synchronize: bool = True) -> None:
        """Clear CuPy memory pools.

        This is a no-op when NumPy is active.
        """
        if not self.is_gpu:
            return

        if synchronize:
            cp.cuda.Device().synchronize()

        cp.get_default_memory_pool().free_all_blocks()
        cp.get_default_pinned_memory_pool().free_all_blocks()

    def print_gpu_used_memory(self) -> None:
        """Print current GPU memory usage.

        This is a no-op when NumPy is active.
        """
        if not self.is_gpu:
            return

        free_bytes, total_bytes = cp.cuda.runtime.memGetInfo()
        used_bytes = total_bytes - free_bytes

        print(f"Used GPU memory: {used_bytes / 1e6:.1f} MB")

    def synchronize(self) -> None:
        """Synchronize the GPU.

        This is a no-op for NumPy.
        """
        if self.is_gpu:
            cp.cuda.Device().synchronize()


# ---------------------------------------------------------------------------
# Process-wide default backend
# ---------------------------------------------------------------------------

# Automatically select CuPy when CUDA is really usable,
# otherwise use NumPy.
backend = BackendManager("auto")


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------

def set_backend(name: str = "auto") -> BackendManager:
    """Select the process-wide backend.

    Parameters
    ----------
    name:
        ``"auto"``, ``"numpy"`` or ``"cupy"``.

    Returns
    -------
    BackendManager
        The newly selected backend manager.

    Examples
    --------
    Force CPU:

    >>> import holodoppler.backend as backend
    >>> backend.set_backend("numpy")

    Request GPU:

    >>> backend.set_backend("cupy")

    Automatic selection:

    >>> backend.set_backend("auto")
    """
    global _backend
    global backend
    global xp
    global fft
    global gaussian_filter
    global ndi
    global zoom
    global is_gpu
    global cupy_available

    backend = BackendManager(name)

    _backend = backend

    xp = _backend.xp
    fft = _backend.fft
    gaussian_filter = _backend.gaussian_filter
    ndi = _backend.ndi
    zoom = _backend.zoom
    is_gpu = _backend.is_gpu

    cupy_available = _cupy_available

    return _backend


# ---------------------------------------------------------------------------
# Module-level aliases
# ---------------------------------------------------------------------------

_backend = backend

xp = _backend.xp
fft = _backend.fft
gaussian_filter = _backend.gaussian_filter
ndi = _backend.ndi
zoom = _backend.zoom
is_gpu = _backend.is_gpu

cupy_available = _cupy_available


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def to_backend(arr):
    """Convert an array to the currently selected backend."""
    return _backend.to_backend(arr)


def to_numpy(arr):
    """Convert an array to NumPy."""
    return _backend.to_numpy(arr)


def clear_gpu_memory(synchronize: bool = True):
    """Clear GPU memory when CuPy is active."""
    return _backend.clear_gpu_memory(synchronize=synchronize)


def print_gpu_used_memory():
    """Print GPU memory usage when CuPy is active."""
    return _backend.print_gpu_used_memory()


def synchronize():
    """Synchronize GPU when CuPy is active."""
    return _backend.synchronize()