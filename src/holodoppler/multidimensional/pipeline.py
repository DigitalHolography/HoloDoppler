"""Composable orchestration that does not mix computation with export."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .aperture import analyze_quadrant_spectra, apply_aperture_masks
from .decomposition import space_time_svd_filter
from .representations import build_field_representations
from .spectral import (
    representation_coupling,
    symmetric_frequency_band,
    temporal_spectral_estimates,
)
from .types import (
    AngularAnalysis,
    CouplingResult,
    FieldRepresentations,
    SpaceTimeSVDFilterResult,
    SpectralEstimates,
)


@dataclass(frozen=True)
class FieldAnalysis:
    """Selected complementary and angular analyses of one complex-field block."""

    representations: FieldRepresentations
    svd_filter: SpaceTimeSVDFilterResult | None
    spectra: dict[str, SpectralEstimates]
    amplitude_phase_coupling: CouplingResult
    aperture_fields: FieldRepresentations | None
    aperture_spectra: dict[str, SpectralEstimates] | None
    angular: dict[str, AngularAnalysis] | None


def analyze_field_block(
    H: Any,
    sampling_frequency: float,
    *,
    masks: Any | None = None,
    epsilon: float | None = None,
    amplitude_reference: float | None = None,
    threshold_fraction: float = 0.01,
    valid_mask: Any | None = None,
    power_threshold: float = 0.0,
    block_length: int = 32,
    overlap: int = 0,
    nfft: int | None = None,
    taper: str = "dpss",
    number_of_tapers: int = 4,
    dpss_time_bandwidth: float = 2.5,
    coupling_low_frequency_guard: float = 0.0,
    svd_remove_modes: int = 0,
    svd_center_rows: bool = False,
) -> FieldAnalysis:
    """Run the manuscript representations and optional quadrant analysis.

    When ``svd_remove_modes`` is positive, retinal-Doppler space-time SVD is
    applied before representations, aperture separation, and spectra.
    """

    spectral_options = dict(
        block_length=block_length,
        overlap=overlap,
        nfft=nfft,
        taper=taper,
        number_of_tapers=number_of_tapers,
        dpss_time_bandwidth=dpss_time_bandwidth,
    )
    svd_filter = None
    analysis_field = H
    if svd_remove_modes:
        svd_filter = space_time_svd_filter(
            H,
            svd_remove_modes,
            center_rows=svd_center_rows,
        )
        analysis_field = svd_filter.filtered_field

    representations = build_field_representations(
        analysis_field,
        epsilon=epsilon,
        amplitude_reference=amplitude_reference,
        threshold_fraction=threshold_fraction,
        valid_mask=valid_mask,
    )
    spectra = {
        "H": temporal_spectral_estimates(
            representations.H, sampling_frequency, **spectral_options
        ),
        "a": temporal_spectral_estimates(
            representations.log_amplitude, sampling_frequency, **spectral_options
        ),
        "phi": temporal_spectral_estimates(
            representations.phase_phasor, sampling_frequency, **spectral_options
        ),
    }
    coupling_frequency_mask = symmetric_frequency_band(
        spectra["a"].frequencies,
        coupling_low_frequency_guard,
    )
    coupling = representation_coupling(
        spectra["a"].SH,
        spectra["phi"].SH,
        power_threshold=power_threshold,
        frequency_mask=coupling_frequency_mask,
    )

    aperture_fields = None
    aperture_spectra = None
    angular = None
    if masks is not None:
        H_p = apply_aperture_masks(analysis_field, masks)
        aperture_fields = build_field_representations(
            H_p,
            epsilon=epsilon,
            amplitude_reference=amplitude_reference,
            threshold_fraction=threshold_fraction,
        )
        aperture_spectra = {
            "H": temporal_spectral_estimates(
                aperture_fields.H, sampling_frequency, **spectral_options
            ),
            "a": temporal_spectral_estimates(
                aperture_fields.log_amplitude,
                sampling_frequency,
                **spectral_options,
            ),
            "phi": temporal_spectral_estimates(
                aperture_fields.phase_phasor,
                sampling_frequency,
                **spectral_options,
            ),
        }
        angular = {
            name: analyze_quadrant_spectra(
                spectral.SH, power_threshold=power_threshold
            )
            for name, spectral in aperture_spectra.items()
        }

    return FieldAnalysis(
        representations=representations,
        svd_filter=svd_filter,
        spectra=spectra,
        amplitude_phase_coupling=coupling,
        aperture_fields=aperture_fields,
        aperture_spectra=aperture_spectra,
        angular=angular,
    )
