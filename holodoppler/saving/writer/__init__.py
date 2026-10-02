"""I/O layer for :mod:`holodoppler.saving`.

Each writer takes prepared data (see :mod:`holodoppler.saving.format`) and puts
it on disk:

``image``
    PNG rasters.
``video``
    AVI video through the imageio FFMPEG plugin.
``table``
    text / CSV / JSON / YAML.
``hdf5``
    numerical datasets.
``metadata``
    reader headers plus the version stamps.
"""

from __future__ import annotations

from .hdf5 import save_h5
from .image import (
    save_image_png,
    save_png,
    save_pngs,
    save_video_average_png,
)
from .metadata import save_metadata
from .table import (
    save_csv,
    save_csv_outputs,
    save_json,
    save_txt,
    save_yaml,
)
from .video import (
    DEFAULT_OUTPUT_FORMATS,
    DEFAULT_PIXELFORMATS,
    DEFAULT_VIDEO_FORMATS,
    VideoFormat,
    find_ffmpeg,
    resolve_video_format,
    save_video,
    save_videos,
    write_video,
    write_videos,
)

__all__ = [
    "DEFAULT_OUTPUT_FORMATS",
    "DEFAULT_PIXELFORMATS",
    "DEFAULT_VIDEO_FORMATS",
    "VideoFormat",
    "find_ffmpeg",
    "resolve_video_format",
    "save_csv",
    "save_csv_outputs",
    "save_h5",
    "save_image_png",
    "save_json",
    "save_metadata",
    "save_png",
    "save_pngs",
    "save_txt",
    "save_video",
    "save_video_average_png",
    "save_videos",
    "save_yaml",
    "write_video",
    "write_videos",
]
