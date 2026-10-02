"""Video shape classification and encoder-ready frame preparation."""

from __future__ import annotations

import warnings

import numpy as np

from .normalize import cast_png_data, normalize_float_array_to_uint8


def is_grayscale_video(data: np.ndarray) -> bool:
    """Return True for a video represented as (T, H, W)."""
    return data.ndim == 3


def is_color_video(data: np.ndarray) -> bool:
    """Return True for a video represented as (T, H, W, C)."""
    return data.ndim == 4 and data.shape[-1] in (3, 4)


def is_video(data: np.ndarray) -> bool:
    """
    Determine whether an array represents a video.

    Convention:
        (T, H, W)       -> grayscale video
        (T, H, W, 3)    -> RGB video
        (T, H, W, 4)    -> RGBA video

    A 3-D array whose final dimension is 3 or 4 is interpreted as an image.
    """
    return is_grayscale_video(data) or is_color_video(data)


def validate_video(data: np.ndarray) -> np.ndarray:
    """
    Validate and prepare video data.

    Accepted:
        (T, H, W)
        (T, H, W, 3)
        (T, H, W, 4)
    """
    data = np.asarray(data)

    if not is_video(data):
        raise ValueError(
            f"Invalid video shape {data.shape}. "
            "Expected (T,H,W), (T,H,W,3), or (T,H,W,4)."
        )

    if data.shape[0] == 0:
        raise ValueError("Cannot save a video with zero frames.")

    return data


def video_to_uint8(data: np.ndarray) -> np.ndarray:
    """Convert a complete video to uint8 for the encoder."""
    data = validate_video(data)
    return normalize_float_array_to_uint8(data)


def average_video(data: np.ndarray) -> np.ndarray:
    """
    Compute the temporal average of a video.

    For floating-point videos:
        mean is computed while still floating point,
        then the result is converted to uint8.

    This intentionally avoids converting every frame to uint8 before
    calculating the average. The conversion keeps the long-standing
    ``cast_png_data`` behaviour (per-image min/max), which is what the shipped
    outputs are built around; the video path itself uses one range for the whole
    ``(T, H, W)`` block, see :func:`prepare_video_frames`.
    """
    data = validate_video(data)

    average = np.mean(data, axis=0)

    return cast_png_data(average)


def make_even_dimensions(frames: np.ndarray) -> np.ndarray:
    """
    Pad video dimensions to even values.

    This is useful for codecs/pixel formats requiring even dimensions.
    """
    return make_dimensions_multiple_of(frames, 2)


def make_dimensions_multiple_of(frames: np.ndarray, multiple: int) -> np.ndarray:
    """
    Pad the spatial dimensions up to a multiple of ``multiple``.

    H.264 with ``yuv420p`` refuses a height or width that is not divisible by
    two, and most codecs prefer dimensions aligned to 16. The originals are
    copied into the top-left corner and the padding is black.

    A ``multiple`` of 1 is a no-op.
    """
    if multiple <= 1:
        return frames

    height = frames.shape[1]
    width = frames.shape[2]

    new_height = ((height + multiple - 1) // multiple) * multiple
    new_width = ((width + multiple - 1) // multiple) * multiple

    if new_height == height and new_width == width:
        return frames

    if frames.ndim == 3:
        padded = np.zeros(
            (frames.shape[0], new_height, new_width),
            dtype=frames.dtype,
        )
    else:
        padded = np.zeros(
            (frames.shape[0], new_height, new_width, frames.shape[3]),
            dtype=frames.dtype,
        )

    padded[:, :height, :width, ...] = frames

    return padded


def prepare_video_frames(data: np.ndarray) -> np.ndarray:
    """
    Convert an arbitrary numerical video into encoder-ready ``uint8`` frames.

    The returned block is contiguous, even-sized and either ``(T, H, W)``
    (grayscale) or ``(T, H, W, 3)`` (RGB).  Alpha channels are dropped.

    The pixel format is deliberately *not* chosen here: the imageio FFMPEG
    writer derives its input format from the frame rank (``gray`` for 2-D,
    ``rgb24`` for RGB) and the caller selects the output format.
    """
    frames = video_to_uint8(data)
    frames = make_even_dimensions(frames)

    if frames.ndim == 3:
        return np.ascontiguousarray(frames)

    channels = frames.shape[-1]

    if channels == 4:
        frames = frames[..., :3]
        channels = 3

    if channels != 3:
        raise ValueError(
            f"Unsupported number of video channels: {channels}. "
            "Expected 3 or 4."
        )

    return np.ascontiguousarray(frames)


def prepare_ffmpeg_frames(data: np.ndarray) -> np.ndarray:
    """Deprecated alias of :func:`prepare_video_frames`."""
    warnings.warn(
        "prepare_ffmpeg_frames() is deprecated; use prepare_video_frames(). "
        "It now returns the frame block only, without pixel formats.",
        DeprecationWarning,
        stacklevel=2,
    )
    return prepare_video_frames(data)
