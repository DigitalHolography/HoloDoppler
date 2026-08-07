"""Sliding-window multidimensional maps for diagnostic video export."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from ._backend import (
    array_namespace,
    asnumpy,
    complex_dtype,
    real_dtype,
    scalar_float,
)
from .aperture import HADAMARD, MODE_NAMES, apply_aperture_masks, quadrant_masks
from .decomposition import space_time_svd_filter
from .representations import build_field_representations
from .spectral import (
    energy_normalized_tapers,
    representation_coupling,
    spectral_estimate_shape,
)
from .types import SpectralEstimates


DEFAULT_VIDEO_BANDS: dict[str, tuple[float, float]] = {
    "total_0250_4000": (250.0, 4000.0),
    "low_0250_1000": (250.0, 1000.0),
    "mid_1000_3000": (1000.0, 3000.0),
    "high_3000_4000": (3000.0, 4000.0),
}


@dataclass(frozen=True)
class SlidingWindowAnalysis:
    """Reduced maps and checks for one complex-field analysis window."""

    maps: dict[str, Any]
    singular_values: Any
    removed_mode_count: int
    removed_singular_energy_fraction: float
    filtered_projection_relative_norm: float
    energy_closure_relative_error: float
    representation_valid_fraction: float
    number_of_spectral_estimates: int
    spectral_frequencies: Any
    aperture_pixel_counts: tuple[int, int, int, int]
    delay_identity_max_abs_error: float


def sliding_window_starts(
    frame_count: int,
    *,
    window_length: int = 64,
    stride: int = 64,
    include_last: bool = True,
) -> tuple[int, ...]:
    """Return deterministic starts, optionally adding a final tail-covering window."""

    frame_count = int(frame_count)
    window_length = int(window_length)
    stride = int(stride)
    if frame_count < 1:
        raise ValueError("frame_count must be positive.")
    if window_length < 32 or window_length > frame_count:
        raise ValueError("window_length must lie between 32 and frame_count.")
    if stride < 1:
        raise ValueError("stride must be positive.")

    starts = list(range(0, frame_count - window_length + 1, stride))
    final_start = frame_count - window_length
    if include_last and starts[-1] != final_start:
        starts.append(final_start)
    return tuple(starts)


def _frequency_band_mask(frequencies: Any, bounds: tuple[float, float]):
    xp = array_namespace(frequencies)
    absolute = xp.abs(frequencies)
    low_frequency, high_frequency = map(float, bounds)
    if low_frequency < 0 or high_frequency <= low_frequency:
        raise ValueError(f"Invalid frequency band: {bounds}.")
    lower = absolute >= low_frequency
    upper = (
        absolute <= high_frequency
        if high_frequency >= scalar_float(xp.max(absolute))
        else absolute < high_frequency
    )
    return lower & upper


def _reduce_coupling(
    maps: dict[str, Any],
    coupling: Any,
    frequencies: Any,
    bands: Mapping[str, tuple[float, float]],
) -> None:
    xp = array_namespace(coupling.cross_spectrum)
    for name, bounds in bands.items():
        mask = _frequency_band_mask(frequencies, bounds)
        valid = coupling.valid_mask[mask]
        cross = xp.sum(
            xp.where(valid, coupling.cross_spectrum[mask], 0), axis=0
        )
        power_a = xp.sum(xp.where(valid, coupling.power_a[mask], 0), axis=0)
        power_b = xp.sum(xp.where(valid, coupling.power_b[mask], 0), axis=0)
        denominator = xp.sqrt(power_a * power_b)
        band_valid = xp.isfinite(denominator) & (denominator > 0)
        coherence = xp.where(
            band_valid,
            cross / xp.where(band_valid, denominator, 1),
            0,
        )
        maps[f"coupling_cross_{name}"] = xp.abs(cross)
        maps[f"coupling_coherence2_{name}"] = xp.clip(
            xp.abs(coherence) ** 2, 0, 1
        )
        maps[f"coupling_phase_{name}"] = xp.angle(coherence)


def _bounded_temporal_spectral_estimates(
    H: Any,
    sampling_frequency: float,
    *,
    block_length: int,
    overlap: int,
    nfft: int,
    taper: str,
    number_of_tapers: int,
    dpss_time_bandwidth: float,
) -> SpectralEstimates:
    """Fill the retained spectrum directly, avoiding list-and-stack duplication."""

    if taper != "dpss":
        raise ValueError("The bounded sliding estimator currently requires DPSS.")
    output_shape = spectral_estimate_shape(
        tuple(map(int, H.shape)),
        block_length=block_length,
        overlap=overlap,
        nfft=nfft,
        taper=taper,
        number_of_tapers=number_of_tapers,
    )
    windows = energy_normalized_tapers(
        block_length,
        taper=taper,
        number_of_tapers=number_of_tapers,
        dpss_time_bandwidth=dpss_time_bandwidth,
    )
    xp = array_namespace(H)
    windows_backend = xp.asarray(windows, dtype=real_dtype(H.dtype))
    estimates = xp.empty(output_shape, dtype=complex_dtype(H.dtype))
    step = block_length - overlap
    block_starts = np.arange(
        0, H.shape[0] - block_length + 1, step, dtype=np.int64
    )
    reshape = (block_length,) + (1,) * (H.ndim - 1)
    estimate_index = 0
    for start in block_starts:
        block = H[int(start) : int(start) + block_length]
        for window in windows_backend:
            tapered = block * window.reshape(reshape)
            estimates[estimate_index] = xp.fft.fft(
                tapered, n=nfft, axis=0, norm="ortho"
            )
            estimate_index += 1
            del tapered
    frequencies = xp.fft.fftfreq(nfft, d=1.0 / sampling_frequency)
    return SpectralEstimates(
        SH=estimates,
        frequencies=frequencies,
        block_starts=block_starts,
        sampling_frequency=float(sampling_frequency),
        block_length=int(block_length),
        overlap=int(overlap),
        nfft=int(nfft),
        taper=taper,
        number_of_tapers=int(windows.shape[0]),
    )


def _release_unused_memory(xp: Any) -> None:
    """Return unused CuPy pool blocks between memory-heavy analysis stages."""

    if xp.__name__ == "cupy":  # pragma: no branch - production GPU path
        xp.get_default_memory_pool().free_all_blocks()


def _bounded_delayed_power(
    aperture_spectra: Any,
    frequencies: Any,
    sampling_frequency: float,
    mode: str,
    polarity: str,
):
    """Compute one delayed power without materializing a 4-aperture product."""

    if mode not in MODE_NAMES[1:]:
        raise ValueError("mode must be one of 'x', 'y', or 'xy'.")
    if polarity not in ("plus", "minus"):
        raise ValueError("polarity must be 'plus' or 'minus'.")
    xp = array_namespace(aperture_spectra, frequencies)
    signs = xp.asarray(HADAMARD[MODE_NAMES.index(mode)])
    delayed_sign = signs > 0 if polarity == "plus" else signs < 0
    delays = xp.where(delayed_sign, 1.0 / sampling_frequency, 0.0)
    phase = xp.exp(-2j * xp.pi * frequencies[:, None] * delays[None, :])
    phase = phase.astype(aperture_spectra.dtype, copy=False)

    delayed = xp.zeros(
        (
            aperture_spectra.shape[0],
            aperture_spectra.shape[1],
            *aperture_spectra.shape[-2:],
        ),
        dtype=aperture_spectra.dtype,
    )
    working = xp.empty_like(delayed)
    for aperture_index in range(4):
        xp.multiply(
            aperture_spectra[:, :, aperture_index],
            phase[None, :, aperture_index, None, None],
            out=working,
        )
        delayed += working
    del working, phase
    _release_unused_memory(xp)

    magnitude_squared = xp.empty(delayed.shape, dtype=real_dtype(delayed.dtype))
    xp.absolute(delayed, out=magnitude_squared)
    xp.square(magnitude_squared, out=magnitude_squared)
    power = xp.mean(magnitude_squared, axis=0)
    del delayed, magnitude_squared
    _release_unused_memory(xp)
    return power


def analyze_sliding_window(
    H: Any,
    sampling_frequency: float,
    *,
    svd_remove_modes: int = 4,
    spectral_block_length: int = 32,
    spectral_overlap: int = 0,
    spectral_nfft: int = 32,
    number_of_tapers: int = 4,
    dpss_time_bandwidth: float = 2.5,
    bands: Mapping[str, tuple[float, float]] = DEFAULT_VIDEO_BANDS,
    masks: Any | None = None,
    delay_modes: Sequence[str] = ("x", "y", "xy"),
) -> SlidingWindowAnalysis:
    """Compute the reduced map set used by sliding diagnostic videos.

    The numerical result stays on the input backend. Persistent encoding and
    display scaling are deliberately handled by :mod:`.video`.
    """

    if getattr(H, "ndim", 0) != 3:
        raise ValueError("H must have shape (N_t, N_y, N_x).")
    if np.dtype(H.dtype) != np.dtype(np.complex64):
        raise TypeError("H must use complex64 for bounded production memory.")
    if sampling_frequency <= 0:
        raise ValueError("sampling_frequency must be positive.")
    if not bands:
        raise ValueError("bands cannot be empty.")

    xp = array_namespace(H)
    spectral_options = {
        "block_length": int(spectral_block_length),
        "overlap": int(spectral_overlap),
        "nfft": int(spectral_nfft),
        "taper": "dpss",
        "number_of_tapers": int(number_of_tapers),
        "dpss_time_bandwidth": float(dpss_time_bandwidth),
    }
    maps: dict[str, Any] = {
        "unfiltered_amplitude": xp.mean(xp.abs(H), axis=0),
    }
    original_energy = xp.sum(xp.abs(H) ** 2, dtype=xp.float64)

    decomposition = space_time_svd_filter(H, svd_remove_modes)
    filtered = decomposition.filtered_field
    maps["filtered_amplitude"] = xp.mean(xp.abs(filtered), axis=0)
    removed = H - filtered
    maps["removed_power"] = xp.mean(xp.abs(removed) ** 2, axis=0)
    removed_energy = xp.sum(xp.abs(removed) ** 2, dtype=xp.float64)
    filtered_energy = xp.sum(xp.abs(filtered) ** 2, dtype=xp.float64)
    rejected = decomposition.temporal_modes[:, :svd_remove_modes]
    projection = filtered.reshape(filtered.shape[0], -1).T @ rejected
    projection_relative_norm = scalar_float(
        xp.linalg.norm(projection) / xp.linalg.norm(filtered)
    )
    del projection, rejected, removed

    singular_energy = decomposition.singular_values.astype(xp.float64) ** 2
    removed_fraction = scalar_float(
        xp.sum(singular_energy[:svd_remove_modes]) / xp.sum(singular_energy)
    )
    energy_closure_error = scalar_float(
        xp.abs(original_energy - removed_energy - filtered_energy) / original_energy
    )

    simple_spectrum = xp.fft.fft(filtered, axis=0, norm="ortho")
    simple_power = xp.abs(simple_spectrum) ** 2
    simple_frequencies = xp.fft.fftfreq(
        filtered.shape[0], d=1.0 / sampling_frequency
    )
    for name, bounds in bands.items():
        maps[f"doppler_{name}"] = xp.sum(
            simple_power[_frequency_band_mask(simple_frequencies, bounds)], axis=0
        )
    del simple_spectrum, simple_power, simple_frequencies

    representations = build_field_representations(filtered)
    representation_valid_fraction = scalar_float(
        xp.mean(representations.valid_mask)
    )
    amplitude_spectral = _bounded_temporal_spectral_estimates(
        representations.log_amplitude,
        sampling_frequency,
        **spectral_options,
    )
    phase_spectral = _bounded_temporal_spectral_estimates(
        representations.phase_phasor,
        sampling_frequency,
        **spectral_options,
    )
    coupling = representation_coupling(
        amplitude_spectral.SH,
        phase_spectral.SH,
    )
    _reduce_coupling(maps, coupling, amplitude_spectral.frequencies, bands)
    spectral_frequencies = amplitude_spectral.frequencies.copy()
    number_of_estimates = int(amplitude_spectral.SH.shape[0])
    del coupling, amplitude_spectral, phase_spectral, representations
    _release_unused_memory(xp)

    spatial_shape = tuple(map(int, H.shape[-2:]))
    if masks is None:
        masks = quadrant_masks(spatial_shape)
    mask_array = asnumpy(masks).astype(bool, copy=False)
    if mask_array.shape != (4, *spatial_shape):
        raise ValueError(f"masks must have shape {(4, *spatial_shape)}.")
    mask_counts = tuple(
        int(value) for value in mask_array.reshape(4, -1).sum(axis=1)
    )

    aperture_shape = spectral_estimate_shape(
        (H.shape[0], 4, *spatial_shape),
        block_length=spectral_block_length,
        overlap=spectral_overlap,
        nfft=spectral_nfft,
        taper="dpss",
        number_of_tapers=number_of_tapers,
    )
    aperture_spectra = xp.empty(aperture_shape, dtype=xp.complex64)
    aperture_frequencies = None
    for aperture_index in range(4):
        aperture_field = apply_aperture_masks(
            filtered, mask_array[aperture_index : aperture_index + 1]
        )[:, 0]
        estimate = _bounded_temporal_spectral_estimates(
            aperture_field,
            sampling_frequency,
            **spectral_options,
        )
        aperture_spectra[:, :, aperture_index] = estimate.SH
        if aperture_frequencies is None:
            aperture_frequencies = estimate.frequencies.copy()
        del estimate, aperture_field
        _release_unused_memory(xp)
    if aperture_frequencies is None:
        raise RuntimeError("No aperture spectra were produced.")
    singular_values = decomposition.singular_values.copy()
    del decomposition, filtered
    _release_unused_memory(xp)

    identity_error = 0.0
    for mode in delay_modes:
        power_plus = _bounded_delayed_power(
            aperture_spectra,
            aperture_frequencies,
            sampling_frequency,
            mode,
            "plus",
        )
        power_minus = _bounded_delayed_power(
            aperture_spectra,
            aperture_frequencies,
            sampling_frequency,
            mode,
            "minus",
        )
        difference = power_plus - power_minus
        identity_error = max(
            identity_error,
            scalar_float(xp.max(xp.abs(difference - (power_plus - power_minus)))),
        )
        for name, bounds in bands.items():
            mask = _frequency_band_mask(aperture_frequencies, bounds)
            band_plus = xp.sum(power_plus[mask], axis=0)
            band_minus = xp.sum(power_minus[mask], axis=0)
            band_difference = xp.sum(difference[mask], axis=0)
            denominator = band_plus + band_minus
            valid = xp.isfinite(denominator) & (denominator > 0)
            contrast = xp.where(
                valid,
                band_difference / xp.where(valid, denominator, 1),
                0,
            )
            maps[f"delay_{mode}_contrast_{name}"] = xp.clip(contrast, -1, 1)
            if name == "total_0250_4000":
                maps[f"delay_{mode}_plus_total"] = band_plus
                maps[f"delay_{mode}_minus_total"] = band_minus
        del power_plus, power_minus, difference
        _release_unused_memory(xp)

    del aperture_spectra
    _release_unused_memory(xp)

    return SlidingWindowAnalysis(
        maps=maps,
        singular_values=singular_values,
        removed_mode_count=int(svd_remove_modes),
        removed_singular_energy_fraction=removed_fraction,
        filtered_projection_relative_norm=projection_relative_norm,
        energy_closure_relative_error=energy_closure_error,
        representation_valid_fraction=representation_valid_fraction,
        number_of_spectral_estimates=number_of_estimates,
        spectral_frequencies=spectral_frequencies,
        aperture_pixel_counts=mask_counts,
        delay_identity_max_abs_error=identity_error,
    )
