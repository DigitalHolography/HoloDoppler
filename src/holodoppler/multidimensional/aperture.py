"""Quadrant aperture construction and angular cross-spectral analysis."""

from __future__ import annotations

from typing import Any

import numpy as np

from ._backend import array_namespace, complex_dtype
from .types import AngularAnalysis


QUADRANT_NAMES = ("NW", "NE", "SW", "SE")
MODE_NAMES = ("0", "x", "y", "xy")

HADAMARD = np.asarray(
    [
        [1, 1, 1, 1],
        [-1, 1, -1, 1],
        [1, 1, -1, -1],
        [-1, 1, 1, -1],
    ],
    dtype=np.float32,
)


def quadrant_masks(
    shape: tuple[int, int],
    *,
    center: tuple[float, float] | None = None,
    radius: float | None = None,
    support_mask: Any | None = None,
    require_balanced: bool = True,
) -> np.ndarray:
    """Build nonoverlapping masks ordered ``[NW, NE, SW, SE]``.

    The default center lies between the central pixels for even dimensions.
    For odd dimensions, the central row and column are excluded. No pupil
    center is inferred from signal content.
    """

    ny, nx = map(int, shape)
    if ny < 2 or nx < 2:
        raise ValueError("Quadrant masks require at least a 2 x 2 array.")
    if center is None:
        center = ((ny - 1) / 2.0, (nx - 1) / 2.0)
    cy, cx = map(float, center)
    if not (0 <= cy <= ny - 1 and 0 <= cx <= nx - 1):
        raise ValueError("center must lie inside the reciprocal-plane array.")
    if radius is not None and radius <= 0:
        raise ValueError("radius must be positive.")

    yy, xx = np.ogrid[:ny, :nx]
    upper = yy < cy
    lower = yy > cy
    left = xx < cx
    right = xx > cx
    masks = np.stack(
        [upper & left, upper & right, lower & left, lower & right],
        axis=0,
    )

    support = np.ones((ny, nx), dtype=bool)
    if radius is not None:
        support &= (yy - cy) ** 2 + (xx - cx) ** 2 <= radius**2
    if support_mask is not None:
        supplied = np.asarray(support_mask, dtype=bool)
        if supplied.shape != (ny, nx):
            raise ValueError(
                f"support_mask must have shape {(ny, nx)}, got {supplied.shape}."
            )
        support &= supplied
    masks &= support[None, ...]

    counts = masks.reshape(4, -1).sum(axis=1)
    if np.any(counts == 0):
        raise ValueError("Every quadrant must contain at least one usable sample.")
    if require_balanced and not np.all(counts == counts[0]):
        raise ValueError(
            "Quadrant support is not balanced: "
            + ", ".join(f"{name}={count}" for name, count in zip(QUADRANT_NAMES, counts))
        )
    if np.any(masks.sum(axis=0) > 1):
        raise RuntimeError("Quadrant masks unexpectedly overlap.")
    return masks


def apply_aperture_masks(H: Any, masks: Any):
    """Return aperture-resolved fields as ``H_p[t, p, y, x]``.

    Masks are defined in the centered reciprocal plane. Spatial FFTs are
    orthonormal, and the time axis remains first.
    """

    if getattr(H, "ndim", 0) != 3:
        raise ValueError("H must have shape (N_t, N_y, N_x).")
    if getattr(masks, "ndim", 0) != 3 or masks.shape[1:] != H.shape[-2:]:
        raise ValueError(
            f"masks must have shape (N_p, {H.shape[-2]}, {H.shape[-1]})."
        )
    xp = array_namespace(H, masks)
    masks_backend = xp.asarray(masks)
    reciprocal = xp.fft.fftshift(
        xp.fft.fft2(H, axes=(-2, -1), norm="ortho"), axes=(-2, -1)
    )
    selected = reciprocal[:, xp.newaxis, :, :] * masks_backend[xp.newaxis, :, :, :]
    fields = xp.fft.ifft2(
        xp.fft.ifftshift(selected, axes=(-2, -1)),
        axes=(-2, -1),
        norm="ortho",
    )
    return fields.astype(complex_dtype(H.dtype), copy=False)


def _mode_transform(values: Any, aperture_axis: int):
    if values.shape[aperture_axis] != 4:
        raise ValueError("The aperture axis must contain [NW, NE, SW, SE].")
    xp = array_namespace(values)
    matrix = xp.asarray(HADAMARD, dtype=values.dtype)
    values_last = xp.moveaxis(values, aperture_axis, -1)
    modes_last = xp.einsum("mp,...p->...m", matrix, values_last)
    return xp.moveaxis(modes_last, -1, aperture_axis)


def power_asymmetries(
    quadrant_powers: Any,
    *,
    aperture_axis: int,
    power_threshold: float = 0.0,
):
    """Return Hadamard power modes and normalized ``[A_x, A_y, A_xy]``."""

    xp = array_namespace(quadrant_powers)
    modes = _mode_transform(quadrant_powers, aperture_axis)
    total = xp.take(modes, 0, axis=aperture_axis)
    directional = xp.take(modes, [1, 2, 3], axis=aperture_axis)
    denominator = xp.expand_dims(total, aperture_axis)
    valid = xp.isfinite(denominator) & (xp.abs(denominator) > power_threshold)
    safe = xp.where(valid, denominator, 1)
    normalized = directional / safe
    nan_value = xp.asarray(float("nan"), dtype=normalized.dtype)
    return modes, xp.where(valid, normalized, nan_value)


def quadrant_cross_spectral_matrix(SH_p: Any):
    """Return ``C[f, y, x, p, q]`` from ``SH_p[e, f, p, y, x]``."""

    if getattr(SH_p, "ndim", 0) != 5 or SH_p.shape[2] != 4:
        raise ValueError("SH_p must have shape (N_e, N_f, 4, N_y, N_x).")
    xp = array_namespace(SH_p)
    return xp.einsum(
        "efpyx,efqyx->fyxpq",
        SH_p,
        xp.conj(SH_p),
        optimize=True,
    ) / SH_p.shape[0]


def modal_cross_spectral_matrix(cross_spectral_matrix: Any):
    """Return ``R = H C H^T`` with matrix axes kept last."""

    if cross_spectral_matrix.shape[-2:] != (4, 4):
        raise ValueError("Cross-spectral matrix axes must both have length four.")
    xp = array_namespace(cross_spectral_matrix)
    matrix = xp.asarray(HADAMARD, dtype=cross_spectral_matrix.dtype)
    return xp.einsum(
        "mp,...pq,nq->...mn",
        matrix,
        cross_spectral_matrix,
        matrix,
        optimize=True,
    )


def _coherence_from_cross_spectral(
    cross_spectral_matrix: Any,
    *,
    number_of_estimates: int,
    power_threshold: float,
):
    xp = array_namespace(cross_spectral_matrix)
    powers_last = xp.real(
        xp.diagonal(cross_spectral_matrix, axis1=-2, axis2=-1)
    )
    denominator = xp.sqrt(powers_last[..., :, None] * powers_last[..., None, :])
    valid = (
        (number_of_estimates >= 2)
        & xp.isfinite(denominator)
        & (powers_last[..., :, None] > power_threshold)
        & (powers_last[..., None, :] > power_threshold)
        & (denominator > 0)
    )
    safe = xp.where(valid, denominator, 1)
    coherence = cross_spectral_matrix / safe
    nan_value = xp.asarray(complex(float("nan"), float("nan")), dtype=coherence.dtype)
    return xp.where(valid, coherence, nan_value), powers_last


def analyze_cross_spectral_matrix(
    cross_spectral_matrix: Any,
    *,
    number_of_estimates: int,
    power_threshold: float = 0.0,
) -> AngularAnalysis:
    """Compute all fixed angular quantities from a cross-spectral matrix."""

    xp = array_namespace(cross_spectral_matrix)
    coherence, powers_last = _coherence_from_cross_spectral(
        cross_spectral_matrix,
        number_of_estimates=number_of_estimates,
        power_threshold=power_threshold,
    )
    quadrant_powers = xp.moveaxis(powers_last, -1, -3)
    power_modes, normalized = power_asymmetries(
        quadrant_powers,
        aperture_axis=-3,
        power_threshold=power_threshold,
    )

    modal = modal_cross_spectral_matrix(cross_spectral_matrix)
    modal_powers_last = xp.real(xp.diagonal(modal, axis1=-2, axis2=-1))
    modal_powers = xp.moveaxis(modal_powers_last, -1, -3)
    incoherent_total = xp.take(power_modes, 0, axis=-3)
    denominator = modal_powers + xp.expand_dims(incoherent_total, -3)
    valid = xp.isfinite(denominator) & (xp.abs(denominator) > power_threshold)
    contrasts = (modal_powers - xp.expand_dims(incoherent_total, -3)) / xp.where(
        valid, denominator, 1
    )
    contrasts = xp.where(valid, contrasts, xp.asarray(float("nan"), contrasts.dtype))

    return AngularAnalysis(
        quadrant_powers=quadrant_powers,
        power_modes=power_modes,
        normalized_power_asymmetries=normalized,
        cross_spectral_matrix=cross_spectral_matrix,
        quadrant_coherence=coherence,
        modal_cross_spectral_matrix=modal,
        modal_powers=modal_powers,
        interference_contrasts=contrasts,
        number_of_estimates=int(number_of_estimates),
    )


def analyze_quadrant_spectra(
    SH_p: Any,
    *,
    power_threshold: float = 0.0,
) -> AngularAnalysis:
    """Compute all frequency-resolved quadrant quantities from spectral estimates."""

    cross = quadrant_cross_spectral_matrix(SH_p)
    return analyze_cross_spectral_matrix(
        cross,
        number_of_estimates=int(SH_p.shape[0]),
        power_threshold=power_threshold,
    )


def band_angular_analysis(
    cross_spectral_matrix: Any,
    frequency_mask: Any,
    *,
    number_of_estimates: int,
    power_threshold: float = 0.0,
) -> AngularAnalysis:
    """Sum ``C(f)`` over a band before normalization, as prescribed."""

    if cross_spectral_matrix.ndim != 5:
        raise ValueError("Expected C with shape (N_f, N_y, N_x, 4, 4).")
    xp = array_namespace(cross_spectral_matrix, frequency_mask)
    mask = xp.asarray(frequency_mask, dtype=bool)
    if mask.shape != (cross_spectral_matrix.shape[0],):
        raise ValueError("frequency_mask does not match the frequency axis.")
    band_cross = xp.sum(cross_spectral_matrix[mask], axis=0)
    return analyze_cross_spectral_matrix(
        band_cross,
        number_of_estimates=number_of_estimates,
        power_threshold=power_threshold,
    )
