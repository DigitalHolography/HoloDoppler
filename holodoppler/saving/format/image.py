"""Image shape classification and PIL preparation."""

from __future__ import annotations

import numpy as np
from PIL import Image

from .normalize import cast_png_data


def prepare_png_image(data: np.ndarray) -> Image.Image:
    """
    Convert a 2-D grayscale or 3-D RGB/RGBA array into a PIL Image.
    """
    data = cast_png_data(data)

    if data.ndim == 2:
        if data.dtype == np.uint16:
            return Image.fromarray(data, mode="I;16")

        return Image.fromarray(data, mode="L")

    if data.ndim == 3:
        channels = data.shape[-1]

        if channels == 3:
            return Image.fromarray(data, mode="RGB")

        if channels == 4:
            return Image.fromarray(data, mode="RGBA")

    raise ValueError(
        f"Unsupported PNG shape {data.shape}. "
        "Expected (H, W), (H, W, 3), or (H, W, 4)."
    )


def is_image(data: np.ndarray) -> bool:
    """Return True for a 2-D grayscale or 3-D RGB/RGBA image."""
    if data.ndim == 2:
        # if data.shape[0] > 4 and data.shape[1] > 4 : # images should be more than 4 by 4 pixels (else they are simply)
        return True

    return data.ndim == 3 and data.shape[-1] in (3, 4)
