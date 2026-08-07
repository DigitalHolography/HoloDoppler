"""Typed result containers for multidimensional HoloDoppler analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldRepresentations:
    """Complex field and its complementary manuscript-defined observables."""

    H: Any
    log_amplitude: Any
    phase_phasor: Any
    valid_mask: Any
    epsilon: float
    amplitude_reference: float
    power_threshold: float


@dataclass(frozen=True)
class SpectralEstimates:
    """Energy-normalized temporal spectral estimates.

    ``SH`` has shape ``(N_e, N_f, ..., N_y, N_x)``. The frequency axis keeps
    the existing unshifted FFT order.
    """

    SH: Any
    frequencies: Any
    block_starts: Any
    sampling_frequency: float
    block_length: int
    overlap: int
    nfft: int
    taper: str
    number_of_tapers: int

    @property
    def number_of_estimates(self) -> int:
        return int(self.SH.shape[0])

    @property
    def number_of_frequencies(self) -> int:
        return int(self.SH.shape[1])


@dataclass(frozen=True)
class CouplingResult:
    """Cross-spectrum and normalized coherence between two representations."""

    cross_spectrum: Any
    coherence: Any
    power_a: Any
    power_b: Any
    valid_mask: Any
    number_of_estimates: int


@dataclass(frozen=True)
class AngularAnalysis:
    """Complete frequency- or band-resolved quadrant analysis."""

    quadrant_powers: Any
    power_modes: Any
    normalized_power_asymmetries: Any
    cross_spectral_matrix: Any
    quadrant_coherence: Any
    modal_cross_spectral_matrix: Any
    modal_powers: Any
    interference_contrasts: Any
    number_of_estimates: int


@dataclass(frozen=True)
class OneFrameDelayResult:
    """Reciprocal one-frame recombination powers and their odd difference."""

    power_plus: Any
    power_minus: Any
    difference: Any
    modal_formula_difference: Any | None


@dataclass(frozen=True)
class SVDResult:
    """Thin or rank-truncated singular-value decomposition."""

    left_modes: Any
    singular_values: Any
    right_modes_h: Any
    matrix_shape: tuple[int, int]
    centered_rows: bool
    method: str

    @property
    def rank(self) -> int:
        return int(self.singular_values.shape[0])

    def reconstruct(self):
        return (self.left_modes * self.singular_values[None, :]) @ self.right_modes_h


@dataclass(frozen=True)
class SpaceTimeSVDFilterResult:
    """Retinal-Doppler space-time SVD filtering of ``H[t, y, x]``.

    ``temporal_modes`` are ordered from the largest to the smallest singular
    value. ``filtered_field`` is reconstructed after projecting out the first
    ``removed_mode_count`` modes.
    """

    filtered_field: Any
    singular_values: Any
    temporal_modes: Any
    removed_mode_count: int
    input_shape: tuple[int, int, int]
    centered_rows: bool


@dataclass(frozen=True)
class AxialSVDResult:
    """Axial-mode SVD of ``H[t, z, y, x]``."""

    decomposition: SVDResult
    spatiotemporal_modes: Any
    axial_modes: Any
    input_shape: tuple[int, int, int, int]


@dataclass(frozen=True)
class GouyCorrelationResult:
    """Raw symmetric-depth correlations and ranked Gouy candidates."""

    correlation: Any
    score: Any
    candidate_indices: Any
    candidate_scores: Any
    candidate_depths: Any | None
    half_width: int
