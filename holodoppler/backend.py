"""Backend management for NumPy/CuPy selection.

HoloDoppler supports three explicit backend modes:

``cpu``
    Always use NumPy. CuPy is never imported for numerical execution.
``gpu``
    Use CuPy. If CuPy or the CUDA runtime is not usable, backend
    initialization fails with :class:`BackendNotAvailableError` instead of
    silently falling back to NumPy.
``auto``
    Use CuPy when it is actually usable, otherwise NumPy. This is the only
    mode in which a GPU -> CPU fallback is allowed.

The *requested* mode and the *actual* backend are separate values and can be
inspected through :meth:`BackendManager.mode` and
:meth:`BackendManager.actual`.

Consumers must use this module instead of importing CuPy directly. The active
backend is available through::

    backend.xp
    backend.fft
    backend.gaussian_filter
    backend.ndi
    backend.zoom
    backend.linalg
    backend.is_gpu
    backend.to_backend()
    backend.to_numpy()

The module-level names above resolve lazily, so they always reflect the
currently selected backend. CuPy is imported lazily as well: importing
HoloDoppler never requires CuPy to be installed.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from enum import Enum
from functools import cache
from typing import Any, Literal

import numpy as np
import scipy.fft as np_fft
import scipy.ndimage as np_ndi
import scipy.linalg as np_linalg
from scipy.ndimage import gaussian_filter as np_gaussian_filter
from scipy.ndimage import zoom as scipy_zoom


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

class BackendMode(str, Enum):
    """Explicitly requested numerical backend."""

    CPU = "cpu"
    GPU = "gpu"
    AUTO = "auto"


ActualBackend = Literal["numpy", "cupy"]


class BackendError(RuntimeError):
    """Base class for backend selection errors."""


class BackendNotAvailableError(BackendError):
    """Raised when the GPU backend is requested but cannot be used."""


GPU_UNAVAILABLE_MESSAGE = (
    "GPU backend requested but CuPy/CUDA could not be initialized.\n"
    "Use --backend cpu or --backend auto if CPU execution is intended."
)


# Legacy parameter values are still accepted so that existing parameter files
# keep working. They are resolved *strictly*: ``cupyRAM`` means "use the GPU",
# so it fails loudly when no usable GPU is present rather than falling back.
_MODE_ALIASES: dict[str, BackendMode] = {
    "cpu": BackendMode.CPU,
    "numpy": BackendMode.CPU,
    "np": BackendMode.CPU,
    "gpu": BackendMode.GPU,
    "cupy": BackendMode.GPU,
    "cp": BackendMode.GPU,
    "cupyram": BackendMode.GPU,
    "auto": BackendMode.AUTO,
}


def resolve_mode(value: Any = None) -> BackendMode:
    """Resolve a user-supplied backend value to a :class:`BackendMode`.

    Parameters
    ----------
    value:
        ``None``, a :class:`BackendMode`, or a string. ``None`` resolves to
        :attr:`BackendMode.AUTO`. Legacy names such as ``"cupyRAM"`` are
        accepted.

    Raises
    ------
    ValueError
        When the value is not a recognised backend name.
    """
    if value is None:
        return BackendMode.AUTO

    if isinstance(value, BackendMode):
        return value

    try:
        key = str(value).strip().lower()
    except Exception:  # pragma: no cover - defensive
        key = ""

    try:
        return _MODE_ALIASES[key]
    except KeyError:
        raise ValueError(
            f"Unknown backend {value!r}. Use 'cpu', 'gpu' or 'auto'."
        ) from None


# ---------------------------------------------------------------------------
# Lazy CuPy access
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _CupyModules:
    """The CuPy modules used by the GPU backend."""

    cp: Any
    fft: Any
    ndi: Any
    gaussian_filter: Any
    zoom: Any
    linalg: Any


def _cupy_installed() -> bool:
    """Return True when CuPy appears to be installed.

    A broken or hostile import hook must not make the package unusable, so
    every failure mode is reported as "not installed".
    """
    try:
        return importlib.util.find_spec("cupy") is not None
    except Exception:
        return False


@cache
def _cupy_modules() -> _CupyModules | None:
    """Import and bundle the CuPy modules, or return ``None``.

    CuPy is imported here rather than at module import time so that importing
    HoloDoppler never requires CuPy.
    """
    try:
        from pathlib import Path
        import os

        cache = Path(".cupy_cache") # force the cupy cache to be local.
        cache.mkdir(parents=True, exist_ok=True)
        os.environ["CUPY_CACHE_DIR"] = str(cache.resolve())
        import cupy as cp
        import cupy.linalg as cp_linalg
        import cupyx.scipy.fft as cp_fft
        import cupyx.scipy.ndimage as cp_ndi
        from cupyx.scipy.ndimage import gaussian_filter as cp_gaussian_filter
        from cupyx.scipy.ndimage import zoom as cp_zoom

    except Exception:
        return None

    return _CupyModules(
        cp=cp,
        fft=cp_fft,
        ndi=cp_ndi,
        gaussian_filter=cp_gaussian_filter,
        zoom=cp_zoom,
        linalg=cp_linalg,
    )


@cache
def _cupy_report() -> tuple[str, str | None]:
    """Return ``(state, detail)`` for the local CuPy installation.

    ``state`` is one of:

    ``"absent"``
        CuPy is not installed.
    ``"unusable"``
        CuPy is installed but CUDA cannot execute work.
    ``"usable"``
        CuPy can actually execute CUDA work.

    The result is cached: the CUDA probe performs a real allocation and is
    therefore only executed once per process.
    """
    if not _cupy_installed():
        return "absent", None

    modules = _cupy_modules()
    if modules is None:
        return "unusable", "CuPy could not be imported"

    cp = modules.cp

    try:
        # Make sure at least one CUDA device is visible.
        if cp.cuda.runtime.getDeviceCount() < 1:
            return "unusable", "no CUDA device is visible"

        # Actually allocate something on the GPU.
        x = cp.zeros(1, dtype=cp.float32)

        # Perform a real GPU operation and force CUDA to execute it now.
        x += 1
        cp.cuda.runtime.deviceSynchronize()

        # A device -> host transfer is the final sanity check.
        if float(x.get()[0]) != 1.0:
            return "unusable", "CUDA sanity check returned an unexpected value"

        return "usable", None

    except Exception as exc:  # noqa: BLE001 - any CUDA failure means unusable
        return "unusable", str(exc)


def _cupy_state() -> str:
    """Return ``"absent"``, ``"unusable"`` or ``"usable"``."""
    return _cupy_report()[0]


def _warn_auto_fallback() -> None:
    """Explain an ``auto`` fallback that was caused by a broken CUDA setup.

    ``auto`` with CuPy absent is the normal CPU installation, so it stays
    silent. A degraded CUDA runtime is worth a single notice.
    """
    state, detail = _cupy_report()

    if state != "unusable":
        return

    message = "CuPy is installed but CUDA is not usable; using the NumPy backend"
    if detail:
        message = f"{message}: {detail}"

    print(message, file=sys.stderr)


# ---------------------------------------------------------------------------
# Backend state
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BackendState:
    """Resolved backend: what was requested and what is actually in use."""

    requested: BackendMode
    actual: ActualBackend
    xp: Any
    fft: Any
    ndi: Any
    gaussian_filter: Any
    zoom: Any
    linalg: Any


def _numpy_state(requested: BackendMode) -> BackendState:
    """Build the NumPy state for the given requested mode."""
    return BackendState(
        requested=requested,
        actual="numpy",
        xp=np,
        fft=np_fft,
        ndi=np_ndi,
        gaussian_filter=np_gaussian_filter,
        zoom=scipy_zoom,
        linalg=np_linalg,
    )


def _cupy_state_for(requested: BackendMode) -> BackendState:
    """Build the CuPy state for the given requested mode."""
    modules = _cupy_modules()

    if modules is None:  # pragma: no cover - guarded by _cupy_state()
        raise BackendNotAvailableError(GPU_UNAVAILABLE_MESSAGE)

    return BackendState(
        requested=requested,
        actual="cupy",
        xp=modules.cp,
        fft=modules.fft,
        ndi=modules.ndi,
        gaussian_filter=modules.gaussian_filter,
        zoom=modules.zoom,
        linalg=modules.linalg,
    )


def _resolve_state(mode: BackendMode) -> BackendState:
    """Resolve ``mode`` into a concrete :class:`BackendState`.

    ``cpu`` never touches CuPy. ``gpu`` requires a usable GPU. ``auto`` is the
    only mode allowed to fall back to NumPy.
    """
    if mode is BackendMode.CPU:
        return _numpy_state(mode)

    if mode is BackendMode.GPU:
        if _cupy_state() != "usable":
            raise BackendNotAvailableError(GPU_UNAVAILABLE_MESSAGE)
        return _cupy_state_for(mode)

    # BackendMode.AUTO
    if _cupy_state() == "usable":
        return _cupy_state_for(mode)

    _warn_auto_fallback()
    return _numpy_state(mode)


# ---------------------------------------------------------------------------
# Backend manager
# ---------------------------------------------------------------------------

class BackendManager:
    """Manage NumPy/CuPy backend selection.

    Parameters
    ----------
    mode:
        ``"cpu"``, ``"gpu"``, ``"auto"`` or a legacy alias such as
        ``"cupyRAM"``.

    Attributes
    ----------
    state:
        The resolved :class:`BackendState`. Its ``requested`` field records
        what the caller asked for and its ``actual`` field records what is
        really in use.
    """

    def __init__(self, mode: BackendMode | str = BackendMode.AUTO) -> None:
        self.state = _resolve_state(resolve_mode(mode))

    # ------------------------------------------------------------------
    # State introspection
    # ------------------------------------------------------------------

    @property
    def mode(self) -> BackendMode:
        """The requested backend mode."""
        return self.state.requested

    @property
    def requested(self) -> BackendMode:
        """The requested backend mode."""
        return self.state.requested

    @property
    def actual(self) -> ActualBackend:
        """The backend that is actually in use."""
        return self.state.actual

    @property
    def backend_name(self) -> ActualBackend:
        """Legacy alias for :attr:`actual`."""
        return self.state.actual

    @property
    def array_module(self) -> Any:
        """The array module currently in use."""
        return self.state.xp

    @property
    def xp(self) -> Any:
        return self.state.xp

    @property
    def fft(self) -> Any:
        return self.state.fft

    @property
    def ndi(self) -> Any:
        return self.state.ndi

    @property
    def gaussian_filter(self) -> Any:
        return self.state.gaussian_filter

    @property
    def zoom(self) -> Any:
        return self.state.zoom

    @property
    def linalg(self) -> Any:
        return self.state.linalg

    @property
    def is_gpu(self) -> bool:
        """True when CuPy is the active backend."""
        return self.state.actual == "cupy"

    @property
    def is_numpy(self) -> bool:
        """True when NumPy is the active backend."""
        return self.state.actual == "numpy"

    def __repr__(self) -> str:
        return (
            f"BackendManager(requested={self.state.requested.value!r}, "
            f"actual={self.state.actual!r})"
        )

    # ------------------------------------------------------------------
    # Array conversion
    # ------------------------------------------------------------------

    def to_backend(self, arr):
        """Convert/move an array to the active backend."""
        if self.state.actual == "cupy":
            modules = _cupy_modules()
            if modules is not None:
                return modules.cp.asarray(arr)

        return np.asarray(arr)

    def to_numpy(self, arr):
        """Convert an array to NumPy."""
        if self.state.actual == "cupy":
            modules = _cupy_modules()
            if modules is not None and isinstance(arr, modules.cp.ndarray):
                return modules.cp.asnumpy(arr)

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

        cp = self.state.xp

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

        free_bytes, total_bytes = self.state.xp.cuda.runtime.memGetInfo()
        used_bytes = total_bytes - free_bytes

        print(f"Used GPU memory: {used_bytes / 1e6:.1f} MB")

    def synchronize(self) -> None:
        """Synchronize the GPU.

        This is a no-op when NumPy is active.
        """
        if self.is_gpu:
            self.state.xp.cuda.Device().synchronize()


# ---------------------------------------------------------------------------
# Process-wide backend
# ---------------------------------------------------------------------------

_backend: BackendManager | None = None


def get_backend() -> BackendManager:
    """Return the process-wide backend, initializing it on first use.

    The default mode is :attr:`BackendMode.AUTO`, matching HoloDoppler's
    historical behaviour of preferring the GPU and falling back to the CPU.
    """
    global _backend

    if _backend is None:
        _backend = BackendManager(BackendMode.AUTO)

    return _backend


def set_backend(name: Any = None) -> BackendManager:
    """Select the process-wide backend.

    Parameters
    ----------
    name:
        ``"cpu"``, ``"gpu"``, ``"auto"`` or a legacy alias. ``None`` means
        ``"auto"``.

    Returns
    -------
    BackendManager
        The newly selected backend manager.

    Raises
    ------
    BackendNotAvailableError
        When ``"gpu"`` is requested and CuPy/CUDA is not usable.
    ValueError
        When the name is not a recognised backend.

    Notes
    -----
    Re-selecting the current mode is a no-op: the CUDA probe is not repeated.
    """
    global _backend

    mode = resolve_mode(name)

    if _backend is not None and _backend.mode is mode:
        return _backend

    _backend = BackendManager(mode)

    return _backend


def reset_backend(*, clear_probe: bool = False) -> None:
    """Forget the process-wide backend.

    Parameters
    ----------
    clear_probe:
        Also discard the cached CuPy/CUDA probe result. Intended for tests
        that need to observe probing again.

    Notes
    -----
    Backend-dependent caches elsewhere in HoloDoppler are keyed on the active
    array module, so they do not need to be cleared when the backend changes.
    """
    global _backend

    _backend = None

    if clear_probe:
        _cupy_modules.cache_clear()
        _cupy_report.cache_clear()


# ---------------------------------------------------------------------------
# Module-level aliases
# ---------------------------------------------------------------------------
#
# These names are resolved lazily through PEP 562 so that ``backend.xp`` and
# friends always report the backend that is currently selected. Defining them
# as plain globals would freeze them at ``set_backend`` time.

_BACKEND_ATTRIBUTES = (
    "xp",
    "fft",
    "ndi",
    "gaussian_filter",
    "zoom",
    "linalg",
    "is_gpu",
)


def __getattr__(name: str) -> Any:
    if name in _BACKEND_ATTRIBUTES:
        return getattr(get_backend(), name)

    if name == "cupy_available":
        return _cupy_state() == "usable"

    if name == "backend":
        return get_backend()

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def to_backend(arr):
    """Convert an array to the currently selected backend."""
    return get_backend().to_backend(arr)


def to_numpy(arr):
    """Convert an array to NumPy."""
    return get_backend().to_numpy(arr)


def clear_gpu_memory(synchronize: bool = True):
    """Clear GPU memory when CuPy is active."""
    return get_backend().clear_gpu_memory(synchronize=synchronize)


def print_gpu_used_memory():
    """Print GPU memory usage when CuPy is active."""
    return get_backend().print_gpu_used_memory()


def get_backend_name() -> ActualBackend:
    """Return ``"numpy"`` or ``"cupy"`` for the active backend."""
    return get_backend().actual


def synchronize():
    """Synchronize GPU when CuPy is active."""
    return get_backend().synchronize()
