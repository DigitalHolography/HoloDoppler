"""Shared output selection and array shape classification."""
from __future__ import annotations

import numpy as np


def is_grayscale_video(data: np.ndarray) -> bool:
    """Return True for a video represented as (T, H, W)."""
    return data.ndim == 3


def is_color_video(data: np.ndarray) -> bool:
    """Return True for a video represented as (T, H, W, C)."""
    return data.ndim == 4 and data.shape[-1] in (3, 4)


def is_image(data: np.ndarray) -> bool:
    """Return True for a 2-D grayscale or 3-D RGB/RGBA image."""
    if data.ndim == 2:
        return True

    return data.ndim == 3 and data.shape[-1] in (3, 4)


def is_video(data: np.ndarray) -> bool:
    """
    Determine whether an array represents a video.

    Convention:
        (T, H, W)       -> grayscale video
        (T, H, W, 3)    -> RGB video
        (T, H, W, 4)    -> RGBA video

    A 3-D array whose final dimension is 3 or 4 is interpreted as an image.
    """
    return not is_image(data) and (is_grayscale_video(data) or is_color_video(data))


def is_csv_output(name: str) -> bool:
    """Return True if an output must be saved to both CSV and HDF5."""
    name = name.lower()
    return "coefs" in name or "registration" in name or name.endswith("shack_hartmann_shifts")


def save_to_hdf5(name: str) -> bool:
    """Select numerical outputs; Doppler images and per-range moments stay in media exports."""
    return (name in {"moment0ff", "moment0", "moment1", "moment2",
                    "spectrum_line", "sh_psd", "averaged_spectrogram",
                    "spectrograms", "PROJ", "PROJff", "QSum_M0", "J0_M0"}
            or name.startswith(("NW_", "NE_", "SW_", "SE_", "NWxSE_", "NExSW_"))
            or name.endswith("_flow_index") or "band_" in name or is_csv_output(name))


def output_formats(name: str, value: np.ndarray, *, temporal: bool = False) -> frozenset[str]:
    """Resolve formats once for a static array or one temporal batch result.

    CSV outputs are numerical even when their shape resembles an image.
    Temporal results are individual frames, whereas static arrays may be videos.
    """
    formats = {"h5"} if save_to_hdf5(name) else set()
    if is_csv_output(name):
        formats.add("csv")
    elif temporal:
        if is_image(value) and not np.iscomplexobj(value):
            formats.update(("avi", "mp4", "png"))
    elif is_image(value):
        formats.add("png")
    elif is_video(value):
        formats.update(("avi", "mp4", "png"))
    return frozenset(formats)
