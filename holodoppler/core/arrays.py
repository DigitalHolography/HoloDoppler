"""Array, mask and padding helpers on the active backend.

Every function here operates on whichever array module the active
:class:`~holodoppler.execution.context.ExecutionContext` carries, so this
module never reads the process-global backend directly.

Cached functions take ``xp`` explicitly, which keeps backend identity part of
the cache key.
"""

from __future__ import annotations

from functools import cache

import numpy as np

from holodoppler.execution.context import ExecutionContext


def _active() -> ExecutionContext:
    """The execution context for the currently selected backend."""
    return ExecutionContext.current()


def to_backend(data):
    """Convert data to the currently selected numerical backend."""
    return _active().to_backend(data)



def to_numpy(data):
    """Convert data to a NumPy array."""
    return _active().to_numpy(data)



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

    return _active().zoom(
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

    video_frames = _active().to_backend(video_frames)

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

    resized = _active().zoom(
        video_frames,
        zoom_factors,
        order=order,
    )

    resized = _active().to_numpy(resized)

    if was_2d:
        return resized[0]

    return resized



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
    data = _active().to_numpy(data)

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

    flat = _active().to_backend(data).ravel()

    return (
        _active().xp.percentile(
            flat,
            low_percent,
        ),
        _active().xp.percentile(
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
    data = _active().to_backend(data)

    adjusted = (
        _active().xp.clip(data, low, high) - low
    ) / (
        high - low + 1e-12
    )

    if gamma != 1.0:
        adjusted = _active().xp.power(
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
        gaussian_filter_func = _active().gaussian_filter

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

    arr = _active().to_backend(
        arr,
    )

    return _active().xp.asarray(
        _active().gaussian_filter(
            arr,
            sigma=[
                sigma if i == axis else 0
                for i in range(arr.ndim)
            ],
        )
    )



@cache
def _elliptical_mask_cached(
    xp,
    ny,
    nx,
    radius_frac,
):
    """Build an elliptical boolean mask for a specific array module.

    ``xp`` participates in the cache key, so a mask built for the CPU is never
    reused for the GPU (or the other way round).
    """
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



def _clear_elliptical_mask_cache() -> None:
    """Drop every cached elliptical mask."""
    _elliptical_mask_cached.cache_clear()



def elliptical_mask(
    ny,
    nx,
    radius_frac,
    xp=None,
):
    """Create an elliptical boolean mask.

    The result is generated using the requested array module, or the currently
    selected backend when ``xp`` is omitted.

    Parameters
    ----------
    ny, nx:
        Mask dimensions.
    radius_frac:
        Fraction of the image radius occupied by the ellipse.
    xp:
        Optional array module to use. Defaults to the active backend.

    Returns
    -------
    array
        Boolean mask on the active backend.

    Notes
    -----
    The result is cached per array module, so switching the backend can never
    return a mask created by the previous backend. For long-running
    applications that need to drop the cached masks, call:

        elliptical_mask.cache_clear()
    """
    if xp is None:
        xp = _active().xp

    return _elliptical_mask_cached(
        xp,
        ny,
        nx,
        radius_frac,
    )



elliptical_mask.cache_clear = _clear_elliptical_mask_cache  # type: ignore[attr-defined]



def pad_array_centrally(
    arr,
    new_shape,
    xp=None,
):
    """Pad the final two dimensions centrally.

    Parameters
    ----------
    arr:
        Input array.
    new_shape:
        Integer or ``(height, width)`` tuple.
    xp:
        Accepted for call-site compatibility with the propagation kernels.
        The padding is performed on the active backend by this module, so the
        argument is intentionally ignored.

    Returns
    -------
    array
        Centrally padded array on the active backend.
    """
    arr = _active().to_backend(arr)

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

    return _active().xp.pad(
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