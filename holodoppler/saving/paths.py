"""Output directory layout and output-rate helpers.

Pure path arithmetic: no array, image or video handling lives here.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def ensure_directory(path: Path) -> Path:
    """Create a directory if necessary and return it."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_directories(
    target_dir: Path,
    full: bool = True,
) -> None:
    """Create the output directory structure."""
    target_dir = Path(target_dir)

    subdirectories = [
        "png",
        "avi",
        "mp4",
        "json",
        "csv",
        "yaml",
    ]

    if full:
        subdirectories.append("h5")

    for directory in subdirectories:
        ensure_directory(target_dir / directory)


def is_csv_h5_output(name: str) -> bool:
    """Return True if an output must be saved to both CSV and HDF5."""
    name = name.lower()
    return "coefs" in name or "registration" in name


def get_default_output_path(
    file_path: str | Path,
    mode: int = 0,
) -> Path:
    """
    Generate the standard output directory.

    mode 0:
        {base_name}/{base_name}_HD

    mode 1:
        {base_name}_HD_{index}

    mode 2:
        {base_name}/{base_name}_HD_{index}
    """
    path = Path(file_path)
    base_name = path.stem

    if mode not in (0, 1, 2):
        raise ValueError("mode must be 0, 1, or 2")

    if mode == 0:
        return path.parent / base_name / f"{base_name}_HD"

    indices = []
    search_directories = [
        path.parent,
        path.parent / base_name,
    ]

    for directory in search_directories:
        if not directory.exists():
            continue

        for subdir in directory.iterdir():
            if not subdir.is_dir():
                continue

            match = re.search(
                rf"^{re.escape(base_name)}_HD_(\d+)$",
                subdir.name,
            )
            if match:
                indices.append(int(match.group(1)))

    new_index = max(indices) + 1 if indices else 0

    if mode == 1:
        return path.parent / f"{base_name}_HD_{new_index}"

    return path.parent / base_name / f"{base_name}_HD_{new_index}"


def calculate_fps(
    num_batch: int | None,
    end_frame: int | None,
    first_frame: int | None,
    parameters: dict[str, Any] | None,
    default_fps: float = 30.0,
    maximum_fps: float = 65.0,
) -> float:
    """Calculate output FPS with safe fallbacks."""
    if (
        num_batch is None
        or end_frame is None
        or first_frame is None
    ):
        return default_fps

    frame_range = end_frame - first_frame

    if frame_range <= 0:
        return default_fps

    parameters = parameters or {}
    sampling_freq = parameters.get("sampling_freq", 1000)

    fps = num_batch / frame_range * sampling_freq

    return min(float(fps), maximum_fps)
