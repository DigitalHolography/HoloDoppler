"""PNG writers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import numpy as np

from holodoppler.saving.format.image import is_image, prepare_png_image
from holodoppler.saving.format.video import average_video, is_video
from holodoppler.saving.paths import ensure_directory
from holodoppler.saving.report import WriteTally


def save_png(path: Path, data: np.ndarray) -> None:
    """Save one image using PIL."""
    path = Path(path)
    ensure_directory(path.parent)

    image = prepare_png_image(data)
    image.save(path)


def save_video_average_png(path: Path, video: np.ndarray) -> None:
    """
    Save the temporal average of a video as PNG.

    The average is calculated first in the original numerical representation,
    then converted to a PNG-compatible integer representation.
    """
    average = average_video(video)
    save_png(path, average)


def save_image_png(path: Path, image: np.ndarray) -> None:
    """Save an image directly as PNG."""
    if not is_image(image):
        raise ValueError(f"Invalid image shape: {image.shape}")

    save_png(path, image)


def save_pngs(
    target_dir: Path,
    data_map: dict[str, Any],
    png_keys: Iterable[str] | None = None,
    tally: WriteTally | None = None,
) -> None:
    """
    Save images and temporal-average PNGs.

    Failures are counted in ``tally`` instead of being printed; the caller
    reports them once at the end of the run.
    """
    png_dir = ensure_directory(target_dir / "png")
    selected_keys = None if png_keys is None else set(png_keys)

    for name, data in data_map.items():
        if data is None or not isinstance(data, np.ndarray):
            continue

        if selected_keys is not None and name not in selected_keys:
            continue

        try:
            path = png_dir / f"{name}.png"

            if is_image(data):
                save_image_png(path, data)

            elif is_video(data):
                save_video_average_png(path, data)

            else:
                continue

            if tally is not None:
                tally.record_png()

        except Exception:
            if tally is not None:
                tally.record_failure()
