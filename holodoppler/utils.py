"""Utility functions for array operations.

Numerical array operations are delegated to the project's backend module,
which transparently selects NumPy or CuPy.

The active backend is available through:

    backend.xp
    backend.fft
    backend.gaussian_filter
    backend.zoom
    backend.to_backend()
    backend.to_numpy()

This module should therefore not import or use CuPy directly.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml

import holodoppler.backend as backend


# ============================================================================
# Array / backend helpers
# ============================================================================


def to_backend(data):
    """Convert data to the currently selected numerical backend."""
    return backend.to_backend(data)


def to_numpy(data):
    """Convert data to a NumPy array."""
    return backend.to_numpy(data)


# ============================================================================
# Resizing
# ============================================================================


def square_cupy(
    video_frames,
    newy=None,
    newx=None,
):
    """Resize a stack of images to a square or requested size.

    Despite the historical function name, this function now uses the
    currently selected backend and therefore works with either NumPy or CuPy.

    Parameters
    ----------
    video_frames:
        Array with shape ``(n_frames, height, width)``.
    newy, newx:
        Target height and width. If either is ``None``, both dimensions are
        set to the maximum input dimension.

    Returns
    -------
    array
        Resized array on the active backend.
    """
    if video_frames.ndim != 3:
        raise ValueError(
            "video_frames must have shape "
            "(n_frames, height, width)"
        )

    _, height, width = video_frames.shape

    if newy is None or newx is None:
        target_height = target_width = max(height, width)
    else:
        target_height = int(newy)
        target_width = int(newx)

    zoom_factors = (
        1.0,
        target_height / height,
        target_width / width,
    )

    return backend.zoom(
        video_frames,
        zoom_factors,
        order=3,
    )

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

    if was_2d:
        return resized[0]

    return resized



# ============================================================================
# Contrast / intensity adjustment
# ============================================================================


def stretchlim(
    data,
    low_percent=1,
    high_percent=99,
):
    """Calculate intensity limits using percentiles.

    For a 4D array, percentiles are calculated independently for the final
    dimension. This preserves the behavior of the original implementation.

    Parameters
    ----------
    data:
        Input array.
    low_percent:
        Lower percentile.
    high_percent:
        Upper percentile.

    Returns
    -------
    low, high
        Percentile limits.
    """
    if not 0 <= low_percent <= 100:
        raise ValueError(
            "low_percent must be between 0 and 100."
        )

    if not 0 <= high_percent <= 100:
        raise ValueError(
            "high_percent must be between 0 and 100."
        )

    if low_percent >= high_percent:
        raise ValueError(
            "low_percent must be smaller than high_percent."
        )

    # Percentile calculation in the original implementation was NumPy
    # based. Keep this operation CPU-side.
    data = backend.to_numpy(data)

    if data.ndim == 4:
        flat = data.reshape(-1, data.shape[-1])

        low = np.nanpercentile(
            flat,
            low_percent,
            axis=0,
        )

        high = np.nanpercentile(
            flat,
            high_percent,
            axis=0,
        )
    else:
        flat = data.ravel()

        low = np.nanpercentile(
            flat,
            low_percent,
        )

        high = np.nanpercentile(
            flat,
            high_percent,
        )

    return low, high


def stretchlimcp(
    data,
    low_percent=1,
    high_percent=99,
):
    """Calculate intensity limits on the active backend.

    The historical ``cp`` suffix is retained for compatibility, but the
    implementation now follows the active backend.
    """
    if not 0 <= low_percent <= 100:
        raise ValueError(
            "low_percent must be between 0 and 100."
        )

    if not 0 <= high_percent <= 100:
        raise ValueError(
            "high_percent must be between 0 and 100."
        )

    if low_percent >= high_percent:
        raise ValueError(
            "low_percent must be smaller than high_percent."
        )

    flat = data.ravel()

    return (
        backend.xp.percentile(
            flat,
            low_percent,
        ),
        backend.xp.percentile(
            flat,
            high_percent,
        ),
    )


def imadjust(
    data,
    low,
    high,
    gamma=1.0,
):
    """Adjust image intensity using the active backend.

    The input is converted to the active backend before processing.
    """
    data = backend.to_backend(data)

    adjusted = (
        backend.xp.clip(data, low, high) - low
    ) / (
        high - low + 1e-12
    )

    if gamma != 1.0:
        adjusted = backend.xp.power(
            adjusted,
            gamma,
        )

    return adjusted


def imadjust_cupy(
    data,
    low,
    high,
    gamma=1.0,
):
    """Backend-compatible version of :func:`imadjust`.

    The original function name is retained for API compatibility.
    """
    return imadjust(
        data,
        low,
        high,
        gamma=gamma,
    )


def scaling(
    data,
    low,
    high,
):
    """Scale values from ``low`` to ``high``."""
    return (
        data - low
    ) / (
        high - low + 1e-12
    )


# ============================================================================
# Sharpening / projection
# ============================================================================


def unsharp_projection(
    bm,
    imgs_arr,
    output_shape,
    radius=2.0,
    amount=2.0,
    dtype=np.float32,
):
    """Create an unsharp-mask projection from a stack of images.

    Parameters
    ----------
    bm:
        Backend manager. This argument is retained for compatibility with
        the existing code. It should normally be the project's global
        ``backend`` module or a compatible backend object.
    imgs_arr:
        Array with shape ``(n_images, height, width)``.
    output_shape:
        Target ``(height, width)``.
    radius:
        Gaussian blur sigma.
    amount:
        Sharpening strength.
    dtype:
        Working dtype.

    Returns
    -------
    numpy.ndarray
        Projection transferred back to CPU memory.
    """
    imgs_arr = bm.to_backend(imgs_arr)

    if imgs_arr.ndim != 3:
        raise ValueError(
            "imgs_arr must have shape "
            "(nt, nx, ny)"
        )

    nt, nx, ny = imgs_arr.shape

    if nt == 0:
        raise ValueError(
            "imgs_arr must contain at least one image."
        )

    out_nx, out_ny = output_shape

    zoom_factors = (
        out_nx / nx,
        out_ny / ny,
    )

    xp = bm.xp

    accumulator = xp.zeros(
        output_shape,
        dtype=xp.float32,
    )

    for image in imgs_arr:
        blurred = bm.gaussian_filter(
            image,
            sigma=radius,
        )

        sharpened = (
            image
            + amount * (image - blurred)
        )

        sharpened_resized = bm.zoom(
            sharpened,
            zoom_factors,
            order=3,
        )

        accumulator += sharpened_resized

    projection = accumulator / nt

    return bm.to_numpy(projection)


# ============================================================================
# Gaussian filtering / flat-field correction
# ============================================================================


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


# ============================================================================
# Configuration
# ============================================================================


def load_config(
    config_path,
):
    """Load a YAML or JSON configuration.

    Lists are recursively converted to tuples.

    Parameters
    ----------
    config_path:
        Path to a YAML/JSON configuration file or an existing dictionary.

    Returns
    -------
    dict
        Configuration dictionary with lists converted to tuples.
    """
    if isinstance(config_path, Mapping):
        config = dict(config_path)

    else:
        config_path = Path(
            config_path
        )

        with config_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            suffix = config_path.suffix.lower()

            if suffix in {".yaml", ".yml"}:
                config = yaml.safe_load(file)

            elif suffix == ".json":
                config = json.load(file)

            else:
                raise ValueError(
                    f"Unsupported configuration format: "
                    f"{config_path.suffix!r}. "
                    "Expected .json, .yaml or .yml."
                )

    def list_to_tuple(value):
        if isinstance(value, dict):
            return {
                key: list_to_tuple(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return tuple(
                list_to_tuple(item)
                for item in value
            )

        return value

    return list_to_tuple(config)


# ============================================================================
# HoloVibes footer
# ============================================================================


def update_from_holo_footer(
    parameters,
    holofooter,
):
    """Update processing parameters using a HoloVibes footer.

    Parameters whose value is ``"use_holovibes"`` are replaced with the
    corresponding values found in the HoloVibes metadata.

    The original function name is retained for compatibility.
    """
    if holofooter is None:
        return parameters

    try:
        compute_settings = holofooter[
            "compute_settings"
        ]

        image_rendering = compute_settings[
            "image_rendering"
        ]

        info = holofooter[
            "info"
        ]

        # ------------------------------------------------------------------
        # Wavelength
        # ------------------------------------------------------------------

        if parameters.get(
            "wavelength"
        ) == "use_holovibes":
            parameters["wavelength"] = (
                image_rendering["lambda"]
            )

        # ------------------------------------------------------------------
        # Spatial propagation
        # ------------------------------------------------------------------

        if parameters.get(
            "spatial_propagation"
        ) == "use_holovibes":

            holovibes_transform = image_rendering[
                "space_transformation"
            ]

            if holovibes_transform == "FRESNELTR":
                parameters[
                    "spatial_propagation"
                ] = "Fresnel"

            elif holovibes_transform == "ANGULARTR":
                parameters[
                    "spatial_propagation"
                ] = "AngularSpectrum"

            else:
                print(
                    "Couldn't parse spatial transform name "
                    "in HoloVibes footer "
                    f"({holovibes_transform!r}); "
                    "using Fresnel."
                )

                parameters[
                    "spatial_propagation"
                ] = "Fresnel"

        # ------------------------------------------------------------------
        # Propagation distance
        # ------------------------------------------------------------------

        if parameters.get(
            "z"
        ) == "use_holovibes":
            parameters["z"] = image_rendering[
                "propagation_distance"
            ]

        # ------------------------------------------------------------------
        # Pixel pitch
        # ------------------------------------------------------------------

        if parameters.get(
            "pixel_pitch"
        ) == "use_holovibes":

            pixel_pitch = info[
                "pixel_pitch"
            ]

            parameters["pixel_pitch"] = (
                pixel_pitch["y"] * 1e-6,
                pixel_pitch["x"] * 1e-6,
            )

        # ------------------------------------------------------------------
        # Sampling frequency
        # ------------------------------------------------------------------

        if parameters.get(
            "sampling_freq"
        ) == "use_holovibes":

            parameters[
                "sampling_freq"
            ] = info["camera_fps"]

        # ------------------------------------------------------------------
        # High frequency
        # ------------------------------------------------------------------

        if parameters.get(
            "high_freq"
        ) == "use_holovibes":

            parameters[
                "high_freq"
            ] = info["camera_fps"] / 2

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(
            f"Issue from HoloVibes footer: {exc}"
        )

    return parameters


# ============================================================================
# Registration
# ============================================================================


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