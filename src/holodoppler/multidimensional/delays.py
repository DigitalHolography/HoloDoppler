"""Frequency-domain aperture delays and reciprocal one-frame contrasts."""

from __future__ import annotations

from typing import Any

from ._backend import array_namespace, real_dtype
from .aperture import HADAMARD, MODE_NAMES
from .types import OneFrameDelayResult


def delayed_recombination_spectra(
    SH_p: Any,
    frequencies: Any,
    delays: Any,
):
    """Return delayed spectra from ``SH_p[e, f, p, y, x]``.

    Positive delay selects the earlier signal ``t - tau`` and therefore uses
    the factor ``exp(-i 2 pi f tau)``.
    """

    if getattr(SH_p, "ndim", 0) != 5:
        raise ValueError("SH_p must have shape (N_e, N_f, N_p, N_y, N_x).")
    xp = array_namespace(SH_p, frequencies, delays)
    frequencies = xp.asarray(frequencies)
    delays = xp.asarray(delays)
    if frequencies.shape != (SH_p.shape[1],):
        raise ValueError("frequencies must match the frequency axis of SH_p.")
    if delays.shape != (SH_p.shape[2],):
        raise ValueError("delays must contain one value per aperture.")
    phase = xp.exp(-2j * xp.pi * frequencies[:, None] * delays[None, :])
    phase = phase.astype(SH_p.dtype, copy=False)
    return xp.sum(SH_p * phase[None, :, :, None, None], axis=2)


def delayed_recombination_power(SH_p: Any, frequencies: Any, delays: Any):
    """Return average delayed power ``S_tau[f, y, x]``."""

    xp = array_namespace(SH_p, frequencies, delays)
    delayed = delayed_recombination_spectra(SH_p, frequencies, delays)
    return xp.mean(xp.abs(delayed) ** 2, axis=0)


def modal_one_frame_difference(
    modal_cross_spectral_matrix: Any,
    frequencies: Any,
    sampling_frequency: float,
    mode: str,
):
    """Evaluate ``-2 sin(2 pi f/fs) Im(R_0mu)``."""

    if mode not in MODE_NAMES[1:]:
        raise ValueError("mode must be one of 'x', 'y', or 'xy'.")
    if modal_cross_spectral_matrix.shape[-2:] != (4, 4):
        raise ValueError("Modal cross-spectral matrix must end in (4, 4).")
    if sampling_frequency <= 0:
        raise ValueError("sampling_frequency must be positive.")
    xp = array_namespace(modal_cross_spectral_matrix, frequencies)
    frequencies = xp.asarray(frequencies)
    if frequencies.shape != (modal_cross_spectral_matrix.shape[0],):
        raise ValueError("frequencies must match the first matrix axis.")
    mode_index = MODE_NAMES.index(mode)
    weighting = -2 * xp.sin(2 * xp.pi * frequencies / sampling_frequency)
    weighting = weighting.astype(
        real_dtype(modal_cross_spectral_matrix.dtype), copy=False
    )
    return weighting[:, None, None] * xp.imag(
        modal_cross_spectral_matrix[..., 0, mode_index]
    )


def one_frame_reciprocal_analysis(
    SH_p: Any,
    frequencies: Any,
    sampling_frequency: float,
    mode: str,
    *,
    modal_cross_spectral_matrix: Any | None = None,
) -> OneFrameDelayResult:
    """Compute reciprocal one-frame powers directly and optionally by modal identity."""

    if SH_p.shape[2] != 4:
        raise ValueError("One-frame quadrant analysis requires four apertures.")
    if mode not in MODE_NAMES[1:]:
        raise ValueError("mode must be one of 'x', 'y', or 'xy'.")
    xp = array_namespace(SH_p, frequencies)
    signs = xp.asarray(HADAMARD[MODE_NAMES.index(mode)])
    tau = 1.0 / sampling_frequency
    delays_plus = xp.where(signs > 0, tau, 0.0)
    delays_minus = xp.where(signs < 0, tau, 0.0)
    power_plus = delayed_recombination_power(SH_p, frequencies, delays_plus)
    power_minus = delayed_recombination_power(SH_p, frequencies, delays_minus)
    difference = power_plus - power_minus
    formula = None
    if modal_cross_spectral_matrix is not None:
        formula = modal_one_frame_difference(
            modal_cross_spectral_matrix,
            frequencies,
            sampling_frequency,
            mode,
        )
    return OneFrameDelayResult(
        power_plus=power_plus,
        power_minus=power_minus,
        difference=difference,
        modal_formula_difference=formula,
    )
