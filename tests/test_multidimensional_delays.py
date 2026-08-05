import numpy as np

from holodoppler.multidimensional import (
    analyze_quadrant_spectra,
    one_frame_reciprocal_analysis,
)


def test_direct_one_frame_difference_matches_modal_identity():
    rng = np.random.default_rng(5)
    SH_p = (
        rng.standard_normal((9, 32, 4, 2, 3))
        + 1j * rng.standard_normal((9, 32, 4, 2, 3))
    ).astype(np.complex64)
    sampling_frequency = 32_000.0
    frequencies = np.fft.fftfreq(32, 1 / sampling_frequency)
    angular = analyze_quadrant_spectra(SH_p)

    for mode in ("x", "y", "xy"):
        result = one_frame_reciprocal_analysis(
            SH_p,
            frequencies,
            sampling_frequency,
            mode,
            modal_cross_spectral_matrix=angular.modal_cross_spectral_matrix,
        )
        assert result.difference.dtype == np.float32
        assert result.modal_formula_difference.dtype == np.float32
        np.testing.assert_allclose(
            result.difference,
            result.modal_formula_difference,
            atol=2e-4,
            rtol=2e-5,
        )
