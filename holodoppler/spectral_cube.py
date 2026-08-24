"""Array helpers for streamed Doppler spectral cubes."""

from __future__ import annotations

from functools import cache

import numpy as np


def window_starts(
    first_frame: int,
    end_frame: int,
    batch_size: int,
    batch_stride: int,
) -> np.ndarray:
    """Return the first input frame of every complete temporal window."""
    values = {
        "first_frame": first_frame,
        "end_frame": end_frame,
        "batch_size": batch_size,
        "batch_stride": batch_stride,
    }
    for name, value in values.items():
        if not isinstance(value, (int, np.integer)):
            raise TypeError(f"{name} must be an integer, got {type(value).__name__}")

    if first_frame < 0:
        raise ValueError("first_frame must be non-negative")
    if end_frame <= first_frame:
        raise ValueError("end_frame must be greater than first_frame")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if batch_stride <= 0:
        raise ValueError("batch_stride must be positive")

    final_start = end_frame - batch_size
    if final_start < first_frame:
        return np.empty(0, dtype=np.int64)
    return np.arange(first_frame, final_start + 1, batch_stride, dtype=np.int64)


def mean_bin_axis(xp, values, target_bins: int, axis: int = 0):
    """Average contiguous samples into ``target_bins`` along one axis."""
    if not isinstance(target_bins, (int, np.integer)) or target_bins <= 0:
        raise ValueError("target_bins must be a positive integer")

    axis = axis % values.ndim
    source_bins = values.shape[axis]
    if target_bins > source_bins:
        raise ValueError(
            f"target_bins ({target_bins}) cannot exceed source bins ({source_bins})"
        )

    moved = xp.moveaxis(values, axis, 0)
    if source_bins % target_bins == 0:
        bin_width = source_bins // target_bins
        binned = moved.reshape(
            (target_bins, bin_width) + tuple(moved.shape[1:])
        ).mean(axis=1)
    else:
        # Unequal integer-width bins cover the complete source axis exactly.
        edges = np.linspace(0, source_bins, target_bins + 1, dtype=np.int64)
        binned = xp.stack(
            [
                moved[start:stop].mean(axis=0)
                for start, stop in zip(edges[:-1], edges[1:])
            ],
            axis=0,
        )

    return xp.moveaxis(binned, 0, axis)


def binned_fft_frequencies(
    sampling_frequency: float,
    batch_size: int,
    target_bins: int,
) -> np.ndarray:
    """Return averaged centers spanning the complete signed FFT frequency range."""
    if not np.isfinite(sampling_frequency) or sampling_frequency <= 0:
        raise ValueError("sampling_frequency must be a positive finite number")
    if not isinstance(batch_size, (int, np.integer)) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")

    frequencies = np.fft.fftshift(
        np.fft.fftfreq(batch_size, d=1.0 / float(sampling_frequency))
    )
    return np.asarray(
        mean_bin_axis(np, frequencies, target_bins, axis=0), dtype=np.float64
    )


def spatial_block_mean(xp, values, ratio_y: int, ratio_x: int):
    """Downscale the last two axes by exact non-overlapping block averaging."""
    for name, value in (("ratio_y", ratio_y), ("ratio_x", ratio_x)):
        if not isinstance(value, (int, np.integer)) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")

    ny, nx = values.shape[-2:]
    if ny % ratio_y or nx % ratio_x:
        raise ValueError(
            "Spatial dimensions must be divisible by their binning ratios: "
            f"input=(y={ny}, x={nx}), ratios=(y={ratio_y}, x={ratio_x})"
        )

    output_shape = (
        tuple(values.shape[:-2])
        + (ny // ratio_y, ratio_y, nx // ratio_x, ratio_x)
    )
    return values.reshape(output_shape).mean(axis=(-3, -1))


@cache
def corner_ellipse_mask(
    xp,
    ny: int,
    nx: int,
    radius_y_factor: float = 1.2,
    radius_x_factor: float = 1.2,
):
    """Return pixels outside a centered ellipse as a corner-region mask."""
    radius_y_factor = float(radius_y_factor)
    radius_x_factor = float(radius_x_factor)
    if not np.isfinite(radius_y_factor) or radius_y_factor <= 0:
        raise ValueError("radius_y_factor must be a positive finite number")
    if not np.isfinite(radius_x_factor) or radius_x_factor <= 0:
        raise ValueError("radius_x_factor must be a positive finite number")

    radius_y = radius_y_factor * ny / 2.0
    radius_x = radius_x_factor * nx / 2.0
    center_y = (ny - 1) / 2.0
    center_x = (nx - 1) / 2.0
    yy, xx = xp.ogrid[:ny, :nx]
    inside = (
        ((yy - center_y) / radius_y) ** 2
        + ((xx - center_x) / radius_x) ** 2
        <= 1.0
    )
    corners = ~inside
    if not bool(xp.any(corners)):
        raise ValueError(
            "The corner ellipse covers the complete frame; reduce one or both "
            "radius factors"
        )
    return corners


def corner_mean_power(
    xp,
    spectrum,
    radius_y_factor: float = 1.2,
    radius_x_factor: float = 1.2,
):
    """Average every frequency plane outside the configured centered ellipse."""
    if spectrum.ndim != 3:
        raise ValueError(f"Expected spectrum with shape (f,y,x), got {spectrum.shape}")
    ny, nx = spectrum.shape[-2:]
    corners = corner_ellipse_mask(
        xp,
        ny,
        nx,
        radius_y_factor=radius_y_factor,
        radius_x_factor=radius_x_factor,
    )
    corners_float = corners.astype(xp.float32, copy=False)
    count = xp.sum(corners_float)
    return xp.sum(
        spectrum * corners_float[xp.newaxis, :, :],
        axis=(-2, -1),
        dtype=xp.float32,
    ) / count


def estimated_cube_bytes(
    time_points: int,
    frequency_bins: int,
    output_y: int,
    output_x: int,
    *,
    bytes_per_value: int = 4,
) -> int:
    """Return the payload size of an uncompressed spectral cube."""
    dimensions = (time_points, frequency_bins, output_y, output_x)
    if any(value < 0 for value in dimensions):
        raise ValueError("Cube dimensions must be non-negative")
    return int(np.prod(dimensions, dtype=np.int64)) * bytes_per_value
