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
    assert result.svd_filter is None
    assert result.spectra["H"].SH.shape == (2, 32, 4, 4)
    assert result.spectra["H"].SH.dtype == np.complex64
    assert np.all(np.isnan(result.amplitude_phase_coupling.coherence[0]))
    assert result.aperture_fields.H.shape == (32, 4, 4, 4)
    assert result.aperture_spectra["H"].SH.shape == (2, 32, 4, 4, 4)
    assert result.angular["H"].cross_spectral_matrix.shape == (32, 4, 4, 4, 4)


def test_field_pipeline_applies_space_time_svd_before_spectra():
    rng = np.random.default_rng(21)
    H = (
        rng.standard_normal((32, 4, 5)) + 1j * rng.standard_normal((32, 4, 5))
    ).astype(np.complex64)

    result = analyze_field_block(
        H,
        8_000.0,
        block_length=32,
        number_of_tapers=2,
        svd_remove_modes=2,
    )

    assert result.svd_filter is not None
    assert result.svd_filter.removed_mode_count == 2
    np.testing.assert_array_equal(
        result.representations.H,
        result.svd_filter.filtered_field,
    )
    filtered = result.representations.H.reshape(32, -1).T
    rejected = result.svd_filter.temporal_modes[:, :2]
    np.testing.assert_allclose(filtered @ rejected, 0, atol=3e-5)
