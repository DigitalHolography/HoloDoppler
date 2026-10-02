"""Output saving: format preparation plus writers.

The package is split in two stages:

``holodoppler.saving.format``
    Pure data preparation.  NumPy rasters and Python objects become the
    ``uint8`` frame blocks / serializable dictionaries the writers need.  No
    filesystem or process access, therefore unit-testable on its own.
``holodoppler.saving.writer``
    Everything that touches disk: PNG, AVI (through the imageio FFMPEG plugin),
    CSV/JSON/YAML, HDF5 and metadata.

``holodoppler.saving.bundle`` sits on top and writes a complete output
directory in one call, which is what the pipelines use through
:func:`save_outputs`.

Every public helper from the former ``holodoppler/saving.py`` module is
re-exported here, so ``from holodoppler.saving import save_outputs`` (and the
other historical imports) keep working.
"""

from __future__ import annotations

from .bundle import save_bundle, save_outputs
from .format import (
    average_video,
    cast_png_data,
    is_color_video,
    is_grayscale_video,
    is_image,
    is_video,
    json_default,
    make_even_dimensions,
    normalize_float_array_to_uint8,
    prepare_ffmpeg_frames,
    prepare_png_image,
    prepare_video_frames,
    to_serializable,
    validate_video,
    video_to_uint8,
)
from .paths import (
    calculate_fps,
    create_directories,
    ensure_directory,
    get_default_output_path,
    is_csv_h5_output,
)
from .version import get_git_version, save_version_files
from .writer import (
    DEFAULT_OUTPUT_FORMATS,
    DEFAULT_PIXELFORMATS,
    DEFAULT_VIDEO_FORMATS,
    VideoFormat,
    find_ffmpeg,
    resolve_video_format,
    save_csv,
    save_csv_outputs,
    save_h5,
    save_image_png,
    save_json,
    save_metadata,
    save_png,
    save_pngs,
    save_txt,
    save_video,
    save_video_average_png,
    save_videos,
    save_yaml,
    write_video,
    write_videos,
)
from .report import WriteTally
from .writer.video import quality_from_q_v

__all__ = [
    "DEFAULT_OUTPUT_FORMATS",
    "DEFAULT_PIXELFORMATS",
    "DEFAULT_VIDEO_FORMATS",
    "VideoFormat",
    "WriteTally",
    "average_video",
    "calculate_fps",
    "cast_png_data",
    "create_directories",
    "ensure_directory",
    "find_ffmpeg",
    "get_default_output_path",
    "get_git_version",
    "is_color_video",
    "is_csv_h5_output",
    "is_grayscale_video",
    "is_image",
    "is_video",
    "json_default",
    "make_even_dimensions",
    "normalize_float_array_to_uint8",
    "prepare_ffmpeg_frames",
    "prepare_png_image",
    "prepare_video_frames",
    "quality_from_q_v",
    "resolve_video_format",
    "save_bundle",
    "save_csv",
    "save_csv_outputs",
    "save_h5",
    "save_image_png",
    "save_json",
    "save_metadata",
    "save_outputs",
    "save_png",
    "save_pngs",
    "save_txt",
    "save_video",
    "save_video_average_png",
    "save_videos",
    "save_version_files",
    "save_yaml",
    "to_serializable",
    "validate_video",
    "video_to_uint8",
    "write_video",
    "write_videos",
]
