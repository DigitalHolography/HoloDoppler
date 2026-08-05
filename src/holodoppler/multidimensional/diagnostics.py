"""Optional diagnostic image export, deliberately separate from computation."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

import numpy as np

from ._backend import asnumpy


ImageComponent = Literal["magnitude", "phase", "real", "imaginary"]


def _image_component(array: Any, component: ImageComponent) -> np.ndarray:
    image = asnumpy(array)
    if image.ndim != 2:
        raise ValueError(f"Diagnostic images must be two-dimensional, got {image.shape}.")
    if component == "magnitude":
        return np.abs(image)
    if component == "phase":
        return np.angle(image)
    if component == "real":
        return np.real(image)
    if component == "imaginary":
        return np.imag(image)
    raise ValueError(f"Unsupported image component: {component!r}.")


def export_diagnostic_images(
    images: Mapping[str, Any],
    output_directory: str | Path,
    *,
    component: ImageComponent = "magnitude",
    percentiles: tuple[float, float] = (1.0, 99.0),
    cmap: str = "gray",
    overwrite: bool = False,
) -> list[Path]:
    """Export caller-selected 2-D arrays as compact PNG diagnostics.

    Existing images are protected unless ``overwrite=True`` is explicit.
    """

    from matplotlib import pyplot as plt

    low_percentile, high_percentile = percentiles
    if not (0 <= low_percentile < high_percentile <= 100):
        raise ValueError("percentiles must satisfy 0 <= low < high <= 100.")
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    planned_paths = {}
    for name in images:
        if not name or Path(name).name != name:
            raise ValueError(f"Diagnostic name must be a plain filename stem: {name!r}.")
        path = output_directory / f"{name}.png"
        if path.exists() and not overwrite:
            raise FileExistsError(f"Diagnostic image already exists: {path}")
        planned_paths[name] = path

    paths: list[Path] = []
    for name, value in images.items():
        path = planned_paths[name]
        image = _image_component(value, component)
        finite = image[np.isfinite(image)]
        if finite.size == 0:
            raise ValueError(f"Diagnostic image {name!r} has no finite values.")
        low, high = np.percentile(finite, [low_percentile, high_percentile])
        if high <= low:
            low, high = float(finite.min()), float(finite.max())
        plt.imsave(path, image, cmap=cmap, vmin=low, vmax=high)
        paths.append(path)
    return paths
