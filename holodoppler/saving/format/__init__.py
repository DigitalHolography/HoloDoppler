"""Data preparation layer for :mod:`holodoppler.saving`.

Everything in this package turns in-memory NumPy data into the representation a
writer needs (``uint8`` rasters, serializable metadata dictionaries, validated
video stacks).  Nothing here touches the filesystem or starts a process, so it
can be unit-tested without any output directory or encoder.

The groups are:

``normalize``
    Dataclass/NumPy -> JSON/YAML safe values, and float/16-bit rasters ->
    ``uint8``.
``image``
    Raster -> :class:`PIL.Image.Image`.
``video``
    Raster stacks -> encoder-ready ``uint8`` frame blocks.
"""

from __future__ import annotations

from .image import is_image, prepare_png_image
from .normalize import (
    cast_png_data,
    json_default,
    normalize_float_array_to_uint8,
    to_serializable,
)
from .video import (
    average_video,
    is_color_video,
    is_grayscale_video,
    is_video,
    make_dimensions_multiple_of,
    make_even_dimensions,
    prepare_ffmpeg_frames,
    prepare_video_frames,
    validate_video,
    video_to_uint8,
)

__all__ = [
    "average_video",
    "cast_png_data",
    "is_color_video",
    "is_grayscale_video",
    "is_image",
    "is_video",
    "json_default",
    "make_dimensions_multiple_of",
    "make_even_dimensions",
    "normalize_float_array_to_uint8",
    "prepare_ffmpeg_frames",
    "prepare_png_image",
    "prepare_video_frames",
    "to_serializable",
    "validate_video",
    "video_to_uint8",
]
