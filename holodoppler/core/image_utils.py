from functools import cache


def gaussian_flatfield(
    array,
    gaussian_width,
    gaussian_filter_func,
):
    """Apply Gaussian flat-field correction, returning zero where background is zero.

    Parameters
    ----------
    array:
        Input array.
    gaussian_width:
        Gaussian filter width.
    gaussian_filter_func:
        Gaussian filtering callable for the supplied array type.
    """
    blurred = gaussian_filter_func(
        array,
        gaussian_width,
    )

    # Avoid evaluating division at zero denominators on either NumPy or CuPy.
    valid = blurred != 0
    return (array * valid) / (blurred + (~valid))


def temporal_gaussian_filter(
    xp,
    gaussian_filter_func,
    arr,
    sigma,
    axis=0,
):
    """Apply a temporal Gaussian filter using explicit array and filter dependencies.

    Parameters
    ----------
    xp:
        Array module.
    gaussian_filter_func:
        Gaussian filtering callable for the supplied array type.
    arr:
        Input array.
    sigma:
        Gaussian sigma.
    axis:
        Temporal axis. Defaults to 0.
    """
    if sigma == 0:
        return arr

    arr = xp.asarray(
        arr,
    )

    return xp.asarray(
        gaussian_filter_func(
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
    xp,
    ny,
    nx,
    radius_frac,
):
    """Create an elliptical boolean mask.

    Parameters
    ----------
    xp:
        Array module, included in the cache key.
    ny, nx:
        Mask dimensions.
    radius_frac:
        Fraction of the image radius occupied by the ellipse.

    Returns
    -------
    array
        Cached boolean mask on the supplied array backend. Treat as read-only.
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


# ============================================================================
# Central padding / cropping
# ============================================================================


def pad_array_centrally(
    xp,
    arr,
    new_shape,
):
    """Pad the final two dimensions centrally using the supplied array module.

    Parameters
    ----------
    xp:
        Array module.
    arr:
        Input array.
    new_shape:
        Integer or ``(height, width)`` tuple.

    Returns
    -------
    array
        Centrally padded array on the supplied array backend.
    """
    arr = xp.asarray(arr)

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

    return xp.pad(
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
    xp,
    zoom_func,
    video_frames,
    new_height,
    new_width,
    *,
    order=3,
):
    """Resize an image or stack on ``xp`` using ``zoom_func``.

    The returned array stays on the supplied array backend.

    Parameters
    ----------
    xp:
        Array module.
    zoom_func:
        Zoom callable for the supplied array type.
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

    video_frames = xp.asarray(video_frames)

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

    if (height, width) == (new_height, new_width):
        return video_frames[0] if was_2d else video_frames

    zoom_factors = (
        1.0,
        new_height / height,
        new_width / width,
    )

    resized = zoom_func(
        video_frames,
        zoom_factors,
        order=order,
    )

    if was_2d:
        return resized[0]

    return resized
