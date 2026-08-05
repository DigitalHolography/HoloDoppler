"""Energy-normalized temporal spectra and representation coupling."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
from scipy.signal.windows import dpss

from ._backend import array_namespace, complex_dtype, real_dtype
from .types import CouplingResult, SpectralEstimates


TaperName = Literal["dpss", "hann", "boxcar"]


def spectral_estimate_shape(
    field_shape: tuple[int, ...],
    *,
    block_length: int = 32,
    overlap: int = 0,
    nfft: int | None = None,
    taper: TaperName = "dpss",
    number_of_tapers: int = 4,
) -> tuple[int, ...]:
    """Return ``(N_e, N_f, ..., N_y, N_x)`` before allocating spectra."""

    if len(field_shape) < 3 or any(int(size) < 1 for size in field_shape):
        raise ValueError("field_shape must describe (N_t, ..., N_y, N_x).")
    if block_length < 32:
        raise ValueError("block_length must be at least 32 samples.")
    if number_of_tapers < 1:
        raise ValueError("number_of_tapers must be positive.")
    if overlap < 0 or overlap >= block_length:
        raise ValueError("overlap must satisfy 0 <= overlap < block_length.")
    if field_shape[0] < block_length:
        raise ValueError("The time dimension is shorter than block_length.")
    if nfft is None:
        nfft = block_length
    if nfft < block_length:
        raise ValueError("nfft cannot be smaller than block_length.")
    if taper == "dpss":
        tapers_per_block = number_of_tapers
    elif taper in ("hann", "boxcar"):
        tapers_per_block = 1
    else:
        raise ValueError(f"Unsupported taper: {taper!r}.")
    step = block_length - overlap
    number_of_blocks = 1 + (int(field_shape[0]) - block_length) // step
    return (
        number_of_blocks * tapers_per_block,
        int(nfft),
        *(int(size) for size in field_shape[1:]),
    )


def spectral_estimate_nbytes(
    field_shape: tuple[int, ...],
    *,
    dtype: Any = np.complex64,
    **spectral_options: Any,
) -> int:
    """Estimate retained spectral-array storage before a GPU allocation."""

    shape = spectral_estimate_shape(field_shape, **spectral_options)
    return int(np.prod(shape, dtype=np.int64) * np.dtype(dtype).itemsize)


def energy_normalized_tapers(
    block_length: int,
    *,
    taper: TaperName = "dpss",
    number_of_tapers: int = 4,
    dpss_time_bandwidth: float = 2.5,
) -> np.ndarray:
    """Return tapers with unit discrete energy, shaped ``(N_taper, N_block)``."""

    if block_length < 32:
        raise ValueError("block_length must be at least 32 samples.")
    if number_of_tapers < 1:
        raise ValueError("number_of_tapers must be positive.")

    if taper == "dpss":
        windows = dpss(
            block_length,
            NW=dpss_time_bandwidth,
            Kmax=number_of_tapers,
            sym=False,
            norm=2,
        )
    elif taper == "hann":
        windows = np.hanning(block_length)[None, :]
    elif taper == "boxcar":
        windows = np.ones((1, block_length), dtype=np.float64)
    else:
        raise ValueError(f"Unsupported taper: {taper!r}.")

    windows = np.atleast_2d(np.asarray(windows, dtype=np.float64))
    energies = np.sqrt(np.sum(np.abs(windows) ** 2, axis=1, keepdims=True))
    if np.any(energies == 0):
        raise ValueError("A temporal taper has zero energy.")
    return windows / energies


def temporal_spectral_estimates(
    H: Any,
    sampling_frequency: float,
    *,
    block_length: int = 32,
    overlap: int = 0,
    nfft: int | None = None,
    taper: TaperName = "dpss",
    number_of_tapers: int = 4,
    dpss_time_bandwidth: float = 2.5,
) -> SpectralEstimates:
    """Compute spectral estimates while preserving the existing FFT convention.

    Input uses ``H[t, ..., y, x]``. Output uses
    ``SH[estimate, frequency, ..., y, x]``. Frequencies are unshifted, matching
    the existing ``_fourier_time_transform`` and ``fftfreq`` behavior.
    """

    if getattr(H, "ndim", 0) < 3:
        raise ValueError("H must have shape (N_t, ..., N_y, N_x).")
    if np.dtype(H.dtype).kind not in "fc":
        raise TypeError("H must have a floating-point or complex dtype.")
    if sampling_frequency <= 0:
        raise ValueError("sampling_frequency must be positive.")
    if overlap < 0 or overlap >= block_length:
        raise ValueError("overlap must satisfy 0 <= overlap < block_length.")
    if H.shape[0] < block_length:
        raise ValueError(
            f"H contains {H.shape[0]} samples, fewer than block_length={block_length}."
        )
    if nfft is None:
        nfft = block_length
    if nfft < block_length:
        raise ValueError("nfft cannot be smaller than block_length.")

    output_shape = spectral_estimate_shape(
        tuple(int(size) for size in H.shape),
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
    spectrum_dtype = complex_dtype(H.dtype)
    step = block_length - overlap
    block_starts = np.arange(0, H.shape[0] - block_length + 1, step, dtype=np.int64)
    reshape = (block_length,) + (1,) * (H.ndim - 1)

    estimates = []
    for start in block_starts:
        block = H[int(start) : int(start) + block_length]
        for window in windows_backend:
            tapered = block * window.reshape(reshape)
            spectrum = xp.fft.fft(tapered, n=nfft, axis=0, norm="ortho")
            estimates.append(spectrum.astype(spectrum_dtype, copy=False))

    SH = xp.stack(estimates, axis=0)
    if SH.shape != output_shape:
        raise RuntimeError(
            f"Unexpected spectral estimate shape {SH.shape}; expected {output_shape}."
        )
    frequencies = xp.fft.fftfreq(nfft, d=1.0 / sampling_frequency)
    return SpectralEstimates(
        SH=SH,
        frequencies=frequencies,
        block_starts=block_starts,
        sampling_frequency=float(sampling_frequency),
        block_length=int(block_length),
        overlap=int(overlap),
        nfft=int(nfft),
        taper=str(taper),
        number_of_tapers=int(windows.shape[0]),
    )


def average_power_spectrum(SH: Any):
    """Average ``|SH|^2`` over the leading estimate axis."""

    if getattr(SH, "ndim", 0) < 4:
        raise ValueError("SH must include estimate, frequency, y, and x axes.")
    xp = array_namespace(SH)
    return xp.mean(xp.abs(SH) ** 2, axis=0)


def cross_spectrum(SH_a: Any, SH_b: Any):
    """Average ``SH_a * conj(SH_b)`` over the estimate axis."""

    if SH_a.shape != SH_b.shape:
        raise ValueError(f"Spectral estimate shapes differ: {SH_a.shape} and {SH_b.shape}.")
    xp = array_namespace(SH_a, SH_b)
    return xp.mean(SH_a * xp.conj(SH_b), axis=0)


def normalized_coherence(
    cross: Any,
    power_a: Any,
    power_b: Any,
    *,
    number_of_estimates: int,
    power_threshold: float = 0.0,
):
    """Normalize a cross-spectrum, returning NaN outside valid power support."""

    if number_of_estimates < 2:
        raise ValueError("Coherence requires at least two spectral estimates.")
    if cross.shape != power_a.shape or cross.shape != power_b.shape:
        raise ValueError("cross, power_a, and power_b must have identical shapes.")
    xp = array_namespace(cross, power_a, power_b)
    denominator = xp.sqrt(power_a * power_b)
    valid = (
        xp.isfinite(denominator)
        & (power_a > power_threshold)
        & (power_b > power_threshold)
        & (denominator > 0)
    )
    safe_denominator = xp.where(valid, denominator, 1)
    coherence = cross / safe_denominator
    nan_value = xp.asarray(complex(float("nan"), float("nan")), dtype=coherence.dtype)
    return xp.where(valid, coherence, nan_value), valid


def representation_coupling(
    SH_a: Any,
    SH_b: Any,
    *,
    power_threshold: float = 0.0,
    frequency_mask: Any | None = None,
) -> CouplingResult:
    """Return marginal powers, cross-spectrum, and normalized coherence."""

    if SH_a.shape != SH_b.shape:
        raise ValueError(f"Spectral estimate shapes differ: {SH_a.shape} and {SH_b.shape}.")
    number_of_estimates = int(SH_a.shape[0])
    power_a = average_power_spectrum(SH_a)
    power_b = average_power_spectrum(SH_b)
    cross = cross_spectrum(SH_a, SH_b)
    coherence, valid = normalized_coherence(
        cross,
        power_a,
        power_b,
        number_of_estimates=number_of_estimates,
        power_threshold=power_threshold,
    )
    if frequency_mask is not None:
        xp = array_namespace(coherence, frequency_mask)
        frequency_mask = xp.asarray(frequency_mask, dtype=bool)
        if frequency_mask.shape != (SH_a.shape[1],):
            raise ValueError("frequency_mask must match the frequency axis.")
        frequency_valid = frequency_mask.reshape(
            (frequency_mask.shape[0],) + (1,) * (coherence.ndim - 1)
        )
        valid &= frequency_valid
        nan_value = xp.asarray(
            complex(float("nan"), float("nan")), dtype=coherence.dtype
        )
        coherence = xp.where(valid, coherence, nan_value)
    return CouplingResult(
        cross_spectrum=cross,
        coherence=coherence,
        power_a=power_a,
        power_b=power_b,
        valid_mask=valid,
        number_of_estimates=number_of_estimates,
    )


def symmetric_frequency_band(
    frequencies: Any,
    low_frequency: float,
    high_frequency: float | None = None,
):
    """Return the existing absolute-frequency band mask without reordering bins."""

    if low_frequency < 0:
        raise ValueError("low_frequency must be nonnegative.")
    if high_frequency is not None and high_frequency <= low_frequency:
        raise ValueError("high_frequency must exceed low_frequency.")
    xp = array_namespace(frequencies)
    absolute = xp.abs(frequencies)
    if high_frequency is None:
        return absolute > low_frequency
    return (absolute > low_frequency) & (absolute < high_frequency)


def sum_frequency_band(array: Any, frequency_mask: Any, *, axis: int = 0):
    """Sum selected unshifted frequency bins along an explicit frequency axis."""

    xp = array_namespace(array, frequency_mask)
    mask = xp.asarray(frequency_mask, dtype=bool)
    if mask.ndim != 1 or mask.shape[0] != array.shape[axis]:
        raise ValueError("frequency_mask must match the selected frequency axis.")
    selected = xp.compress(mask, array, axis=axis)
    return xp.sum(selected, axis=axis)
