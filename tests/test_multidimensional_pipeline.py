import numpy as np

from holodoppler.multidimensional import analyze_field_block, quadrant_masks


def test_field_pipeline_composes_representations_coupling_and_quadrants():
    rng = np.random.default_rng(12)
    H = (
        2
        + 0.1 * rng.standard_normal((32, 4, 4))
        + 0.1j * rng.standard_normal((32, 4, 4))
    ).astype(np.complex64)

    result = analyze_field_block(
        H,
        32_000.0,
        masks=quadrant_masks((4, 4)),
        block_length=32,
        number_of_tapers=2,
    )

    assert result.representations.H.shape == (32, 4, 4)
    assert result.spectra["H"].SH.shape == (2, 32, 4, 4)
    assert result.spectra["H"].SH.dtype == np.complex64
    assert np.all(np.isnan(result.amplitude_phase_coupling.coherence[0]))
    assert result.aperture_fields.H.shape == (32, 4, 4, 4)
    assert result.aperture_spectra["H"].SH.shape == (2, 32, 4, 4, 4)
    assert result.angular["H"].cross_spectral_matrix.shape == (32, 4, 4, 4, 4)
