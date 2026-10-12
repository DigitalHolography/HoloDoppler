import json
from functools import cache
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml

import holodoppler.backend as backend

def gaussian_flatfield(
    array,
    gaussian_width,
    gaussian_filter_func=None,
):
    """Apply Gaussian flat-field correction.

    Parameters
    ----------
    array:
        Input array.
    gaussian_width:
        Gaussian filter width.
    gaussian_filter_func:
        Optional filtering function. If omitted, the active backend's
        Gaussian filter is used.
    """
    if gaussian_filter_func is None:
        gaussian_filter_func = backend.gaussian_filter

    blurred = gaussian_filter_func(
        array,
        gaussian_width,
    )

    return array / blurred


def temporal_gaussian_filter(
    arr,
    sigma,
    axis=0,
):
    """Apply a 1D Gaussian filter along the temporal axis.

    Parameters
    ----------
    arr:
        Input array.
    sigma:
        Gaussian sigma.
    axis:
        Temporal axis. Defaults to 0.
    """
    if sigma == 0:
        return arr

    arr = backend.to_backend(
        arr,
    )

    return backend.xp.asarray(
        backend.gaussian_filter(
            arr,
            sigma=[
                sigma if i == axis else 0
                for i in range(arr.ndim)
            ],
        )
    )


# ============================================================================
# Masks
# ============================================================================


@cache
def elliptical_mask(
    ny,
    nx,
    radius_frac,
    xp = None
):
    """Create an elliptical boolean mask.

    The result is generated using the currently selected backend.

    Parameters
    ----------
    ny, nx:
        Mask dimensions.
    radius_frac:
        Fraction of the image radius occupied by the ellipse.
    xp: 
        Optional module to use, default is backend.

    Returns
    -------
    array
        Boolean mask on the active backend.

    Notes
    -----
    The result is cached. Changing the backend after a mask has been
    generated can therefore return a mask created by the previous backend.

    For long-running applications that switch backend dynamically, call:

        elliptical_mask.cache_clear()
    """

    if xp is None:
        xp = backend.xp
        
    radius_frac = max(
        0.0,
        min(1.0, float(radius_frac)),
    )

    if radius_frac == 0:
        return xp.zeros(
            (ny, nx),
            dtype=bool,
        )

    a = (nx / 2.0) * radius_frac
    b = (ny / 2.0) * radius_frac

    y, x = xp.ogrid[
        :ny,
        :nx,
    ]

    cy = ny / 2.0
    cx = nx / 2.0

    mask = (
        ((x - cx) / a) ** 2
        + ((y - cy) / b) ** 2
        <= 1.0
    )

    return mask


# ============================================================================
# Central padding / cropping
# ============================================================================


def pad_array_centrally(
    arr,
    new_shape,
):
    """Pad the final two dimensions centrally.

    Parameters
    ----------
    arr:
        Input array.
    new_shape:
        Integer or ``(height, width)`` tuple.

    Returns
    -------
    array
        Centrally padded array on the active backend.
    """
    arr = backend.to_backend(arr)

    if isinstance(new_shape, int):
        new_shape = (
            new_shape,
            new_shape,
        )

    if len(new_shape) != 2:
        raise ValueError(
            "new_shape must contain exactly two dimensions."
        )

    ny, nx = arr.shape[-2:]
    new_ny, new_nx = new_shape

    if new_ny < ny or new_nx < nx:
        raise ValueError(
            "new_shape must be >= current shape."
        )

    pad_y0 = (new_ny - ny) // 2
    pad_y1 = new_ny - ny - pad_y0

    pad_x0 = (new_nx - nx) // 2
    pad_x1 = new_nx - nx - pad_x0

    pad_width = [
        (0, 0)
        for _ in range(arr.ndim)
    ]

    pad_width[-2] = (
        pad_y0,
        pad_y1,
    )

    pad_width[-1] = (
        pad_x0,
        pad_x1,
    )

    return backend.xp.pad(
        arr,
        pad_width,
        mode="constant",
    )


def crop_array_centrally(
    arr,
    target_shape,
):
    """Crop the final two dimensions centrally.

    Parameters
    ----------
    arr:
        Input array.
    target_shape:
        Integer or ``(height, width)`` tuple.

    Returns
    -------
    array
        Centrally cropped array.
    """
    if isinstance(target_shape, int):
        target_shape = (
            target_shape,
            target_shape,
        )

    if len(target_shape) != 2:
        raise ValueError(
            "target_shape must contain exactly two dimensions."
        )

    ny, nx = arr.shape[-2:]
    target_ny, target_nx = target_shape

    if target_ny > ny or target_nx > nx:
        raise ValueError(
            "target_shape must be <= current shape."
        )

    crop_y0 = (ny - target_ny) // 2
    crop_x0 = (nx - target_nx) // 2

    slices = [
        slice(None)
        for _ in range(arr.ndim)
    ]

    slices[-2] = slice(
        crop_y0,
        crop_y0 + target_ny,
    )

    slices[-1] = slice(
        crop_x0,
        crop_x0 + target_nx,
    )

    return arr[
        tuple(slices)
    ]

def resize_frames(
    video_frames,
    new_height,
    new_width,
    *,
    order=3,
):
    """Resize an image or stack of images.

    Parameters
    ----------
    video_frames:
        Image with shape ``(height, width)`` or a stack of images
        with shape ``(n_frames, height, width)``.

    new_height:
        Target height.

    new_width:
        Target width.

    order:
        Interpolation order passed to the backend.

    Returns
    -------
    array
        Resized image with shape ``(height, width)`` if the input was
        2D, otherwise a frame stack with shape
        ``(n_frames, height, width)``.
    """

    video_frames = backend.to_backend(video_frames)

    was_2d = video_frames.ndim == 2

    if was_2d:
        video_frames = video_frames[None, ...]

    elif video_frames.ndim != 3:
        raise ValueError(
            "video_frames must have shape "
            "(height, width) or "
            "(n_frames, height, width)"
        )

    _, height, width = video_frames.shape

    zoom_factors = (
        1.0,
        new_height / height,
        new_width / width,
    )

    resized = backend.zoom(
        video_frames,
        zoom_factors,
        order=order,
    )

    resized = backend.to_numpy(resized)

    if was_2d:
        return resized[0]

    return resized



def subpixel_parabola(
    vm,
    v0,
    vp,
):
    """Refine a peak location using a parabolic fit.

    Returns the subpixel offset relative to ``v0``.
    """
    denominator = (
        vm
        - 2.0 * v0
        + vp
    )

    if abs(float(denominator)) < 1e-12:
        return 0.0

    return (
        0.5
        * float(vm - vp)
        / float(denominator)
    )


def signed_peak(
    ky,
    kx,
    ny,
    nx,
):
    """Convert FFT peak indices into signed shifts."""
    if ky > ny // 2:
        ky -= ny

    if kx > nx // 2:
        kx -= nx

    return (
        float(ky),
        float(kx),
    )