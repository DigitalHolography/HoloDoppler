"""Complex-field, log-amplitude, and phase-phasor representations."""

from __future__ import annotations

from typing import Any

from ._backend import array_namespace, scalar_float
from .types import FieldRepresentations


def _validate_field(H: Any) -> None:
    if getattr(H, "ndim", 0) < 3:
        raise ValueError("H must have shape (N_t, ..., N_y, N_x).")
    if H.shape[0] < 1 or H.shape[-2] < 1 or H.shape[-1] < 1:
        raise ValueError("H cannot contain an empty time or spatial axis.")


def phase_validity_mask(
    H: Any,
    *,
    threshold_fraction: float = 0.01,
    valid_mask: Any | None = None,
):
    """Return the fixed spatial mask used for phase-sensitive observables.

    The default threshold is one percent of the spatial median of the
    time-averaged field power. A supplied mask is intersected with it.
    """

    _validate_field(H)
    if threshold_fraction < 0:
        raise ValueError("threshold_fraction must be nonnegative.")

    xp = array_namespace(H)
    power = xp.mean(xp.abs(H) ** 2, axis=0)
    finite_positive = xp.isfinite(power) & (power > 0)
    if not bool(scalar_float(xp.any(finite_positive))):
        raise ValueError("H has no finite nonzero time-averaged power.")
    reference_power = xp.median(power[finite_positive])
    threshold = threshold_fraction * reference_power
    mask = xp.isfinite(power) & (power > threshold)
    if valid_mask is not None:
        candidate = xp.asarray(valid_mask, dtype=bool)
        if candidate.shape != H.shape[1:]:
            raise ValueError(
                f"valid_mask must have shape {H.shape[1:]}, got {candidate.shape}."
            )
        mask &= candidate
    return mask, scalar_float(threshold)


def build_field_representations(
    H: Any,
    *,
    epsilon: float | None = None,
    amplitude_reference: float | None = None,
    threshold_fraction: float = 0.01,
    valid_mask: Any | None = None,
) -> FieldRepresentations:
    """Build the three representations specified by the manuscript.

    ``H`` keeps its established ``(time, ..., y, x)`` layout. Log amplitude is
    temporally centered. The phase phasor is not centered and is set to zero
    outside the fixed validity mask so invalid pixels do not poison FFTs.
    """

    _validate_field(H)
    xp = array_namespace(H)
    mask, power_threshold = phase_validity_mask(
        H,
        threshold_fraction=threshold_fraction,
        valid_mask=valid_mask,
    )

    amplitude = xp.abs(H)
    expanded_mask = mask[xp.newaxis, ...]
    valid_amplitudes = amplitude[xp.broadcast_to(expanded_mask, amplitude.shape)]
    valid_amplitudes = valid_amplitudes[
        xp.isfinite(valid_amplitudes) & (valid_amplitudes > 0)
    ]
    if not bool(scalar_float(valid_amplitudes.size > 0)):
        raise ValueError("The validity mask contains no finite nonzero amplitudes.")

    robust_amplitude = xp.median(valid_amplitudes)
    if amplitude_reference is None:
        amplitude_reference = scalar_float(robust_amplitude)
    if amplitude_reference <= 0:
        raise ValueError("amplitude_reference must be positive.")

    if epsilon is None:
        epsilon = 1e-6 * scalar_float(robust_amplitude)
    if epsilon <= 0:
        raise ValueError("epsilon must be positive.")

    ell = xp.log((amplitude + epsilon) / amplitude_reference)
    log_amplitude = ell - xp.mean(ell, axis=0, keepdims=True)
    log_amplitude = xp.where(expanded_mask, log_amplitude, 0)

    safe_amplitude = xp.where(amplitude > epsilon, amplitude, 1)
    phase_phasor = H / safe_amplitude
    phase_phasor = xp.where(expanded_mask & (amplitude > epsilon), phase_phasor, 0)

    return FieldRepresentations(
        H=H,
        log_amplitude=log_amplitude,
        phase_phasor=phase_phasor,
        valid_mask=mask,
        epsilon=float(epsilon),
        amplitude_reference=float(amplitude_reference),
        power_threshold=float(power_threshold),
    )
