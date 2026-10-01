"""The execution context: the sanctioned bridge to the numerical backend.

``core/`` modules must not read the process-global backend directly. They
either receive an explicit array module, or obtain one from the active
:class:`ExecutionContext`. That keeps a single documented seam, and lets the
array module be passed in explicitly as the pipelines are migrated.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Callable, Literal

from holodoppler.backend import get_backend, set_backend


if TYPE_CHECKING:  # pragma: no cover - typing only
    from holodoppler.backend import BackendManager


#: Which entry point is running. ``preview`` processes a single reference batch.
ExecutionMode = Literal["preview", "process"]

ProgressCallback = Callable[..., Any]


@dataclass(frozen=True)
class ExecutionContext:
    """Everything numerical code needs in order to do work.

    Attributes
    ----------
    backend:
        The resolved backend manager. Its ``requested`` field records what the
        user asked for and its ``actual`` field records what is really in use.
    mode:
        ``"process"`` for a full run, ``"preview"`` for a reference batch.
    progress_callback:
        Optional ``(current, total, text)`` progress reporter.

    Examples
    --------
    >>> context = ExecutionContext.from_backend("cpu")
    >>> context.array_module.__name__
    'numpy'
    """

    backend: "BackendManager"
    mode: ExecutionMode = "process"
    progress_callback: ProgressCallback | None = None

    # ------------------------------------------------------------------
    # Backend identity
    # ------------------------------------------------------------------

    @property
    def backend_name(self) -> str:
        """``"numpy"`` or ``"cupy"`` for the active backend."""
        return self.backend.actual

    @property
    def requested_mode(self) -> str:
        """The backend mode the user asked for: ``"cpu"``, ``"gpu"`` or ``"auto"``."""
        return self.backend.requested.value

    @property
    def is_gpu(self) -> bool:
        """True when CuPy is the active backend."""
        return self.backend.is_gpu

    # ------------------------------------------------------------------
    # Array modules
    # ------------------------------------------------------------------

    @property
    def array_module(self) -> Any:
        """The array module in use (``numpy`` or ``cupy``)."""
        return self.backend.xp

    @property
    def xp(self) -> Any:
        """Alias for :attr:`array_module`."""
        return self.backend.xp

    @property
    def fft(self) -> Any:
        """The FFT module matching :attr:`array_module`."""
        return self.backend.fft

    @property
    def ndi(self) -> Any:
        """The ``scipy.ndimage`` equivalent matching :attr:`array_module`."""
        return self.backend.ndi

    @property
    def gaussian_filter(self) -> Any:
        """The Gaussian filter matching :attr:`array_module`."""
        return self.backend.gaussian_filter

    @property
    def zoom(self) -> Any:
        """The interpolation/zoom function matching :attr:`array_module`."""
        return self.backend.zoom

    @property
    def linalg(self) -> Any:
        """The linear algebra module matching :attr:`array_module`."""
        return self.backend.linalg

    # ------------------------------------------------------------------
    # Array conversion
    # ------------------------------------------------------------------

    def to_backend(self, value: Any) -> Any:
        """Move ``value`` to the active backend."""
        return self.backend.to_backend(value)

    def to_numpy(self, value: Any) -> Any:
        """Move ``value`` to NumPy."""
        return self.backend.to_numpy(value)

    def clear_gpu_memory(self, synchronize: bool = True) -> None:
        """Release GPU memory pools; a no-op on the CPU backend."""
        self.backend.clear_gpu_memory(synchronize=synchronize)

    # ------------------------------------------------------------------
    # Derivation
    # ------------------------------------------------------------------

    def with_mode(self, mode: ExecutionMode) -> "ExecutionContext":
        """Return a copy of this context running in ``mode``."""
        return replace(self, mode=mode)

    @classmethod
    def from_backend(cls, name: Any = None, **kwargs: Any) -> "ExecutionContext":
        """Select ``name`` as the process backend and build a context for it.

        ``name`` accepts the same values as
        :func:`holodoppler.backend.set_backend`: ``"cpu"``, ``"gpu"``,
        ``"auto"``, ``None`` (meaning ``"auto"``) and the legacy aliases.

        Raises
        ------
        BackendNotAvailableError
            When ``"gpu"`` is requested and CuPy/CUDA is not usable.
        """
        return cls(backend=set_backend(name), **kwargs)

    @classmethod
    def current(cls, **kwargs: Any) -> "ExecutionContext":
        """Build a context for the currently selected backend."""
        return cls(backend=get_backend(), **kwargs)
