"""Numerical normalization into writer-friendly representations."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import numpy as np


def json_default(value: Any) -> Any:
    """Convert common scientific Python objects into JSON-compatible values."""
    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        return asdict(value)

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def to_serializable(value: Any) -> Any:
    """Recursively convert Python/NumPy objects into json/yaml savable objects."""
    if isinstance(value, dict):
        return {str(k): to_serializable(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [to_serializable(v) for v in value]

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        return to_serializable(asdict(value))

    return value


def normalize_float_array_to_uint8(data: np.ndarray) -> np.ndarray:
    """
    Normalize arbitrary numerical data to uint8.

    NaN and Inf are handled before normalization.
    """
    data = np.asarray(data)

    if data.dtype == np.uint8:
        return data

    if data.dtype == np.uint16:
        return (data.astype(np.float32) / 65535.0 * 255.0).astype(np.uint8)

    data = np.nan_to_num(
        data,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    ).astype(np.float32, copy=False)

    if data.size == 0:
        return np.zeros_like(data, dtype=np.uint8)

    minimum = float(data.min())
    maximum = float(data.max())

    if maximum <= minimum:
        return np.zeros_like(data, dtype=np.uint8)

    normalized = (data - minimum) / (maximum - minimum)
    return np.clip(normalized * 255.0, 0, 255).astype(np.uint8)


def cast_png_data(data: np.ndarray) -> np.ndarray:
    """
    Convert image data to a PIL-compatible integer array.

    Important:
        If the input is floating point, normalization happens before
        the final uint8 cast.
    """
    data = np.asarray(data)

    if data.dtype == np.uint8:
        return data

    if data.dtype == np.uint16:
        return data

    if np.issubdtype(data.dtype, np.floating):
        return normalize_float_array_to_uint8(data)

    if np.issubdtype(data.dtype, np.integer):
        if data.min() >= 0 and data.max() <= 255:
            return data.astype(np.uint8)

        if data.min() >= 0 and data.max() <= 65535:
            return data.astype(np.uint16)

    return normalize_float_array_to_uint8(data)
