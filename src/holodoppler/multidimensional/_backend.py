"""Small NumPy/CuPy compatibility helpers.

NumPy is the reference-test backend. CuPy with CUDA 13 is the production
backend. Importing this module never requires a CUDA installation.
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:  # pragma: no cover - exercised on production GPU systems
    import cupy as cp
except Exception:  # pragma: no cover - expected in CPU-only test environments
    cp = None


def array_namespace(*arrays: Any):
    """Return CuPy when any argument is a CuPy array, otherwise NumPy."""

    if cp is not None and any(isinstance(array, cp.ndarray) for array in arrays):
        return cp
    return np


def asnumpy(array: Any) -> np.ndarray:
    """Copy an array to NumPy only when it currently resides on the GPU."""

    if cp is not None and isinstance(array, cp.ndarray):
        return cp.asnumpy(array)
    return np.asarray(array)


def real_dtype(dtype: Any):
    """Return the real component dtype associated with a real/complex dtype."""

    dtype = np.dtype(dtype)
    if dtype == np.dtype(np.complex64):
        return np.dtype(np.float32)
    if dtype == np.dtype(np.complex128):
        return np.dtype(np.float64)
    return dtype


def complex_dtype(dtype: Any):
    """Return the matching complex dtype without promoting 32-bit input."""

    dtype = np.dtype(dtype)
    if dtype in (np.dtype(np.float32), np.dtype(np.complex64)):
        return np.dtype(np.complex64)
    return np.dtype(np.complex128)


def scalar_float(value: Any) -> float:
    """Convert a NumPy/CuPy scalar to a Python float."""

    if cp is not None and isinstance(value, cp.ndarray):
        return float(value.get())
    return float(value)
