import numpy as np

from holodoppler.multidimensional import (
    analyze_cross_spectral_matrix,
    analyze_quadrant_spectra,
    apply_aperture_masks,
    quadrant_cross_spectral_matrix,
    quadrant_masks,
)


def test_even_quadrants_form_balanced_complete_partition():
    masks = quadrant_masks((8, 10))
    assert masks.shape == (4, 8, 10)
    np.testing.assert_array_equal(masks.reshape(4, -1).sum(axis=1), 20)
    np.testing.assert_array_equal(masks.sum(axis=0), 1)


def test_odd_quadrants_exclude_central_axes_and_remain_balanced():
    masks = quadrant_masks((9, 11))
    np.testing.assert_array_equal(masks.reshape(4, -1).sum(axis=1), 20)
    assert np.all(masks[:, 4, :] == 0)
    assert np.all(masks[:, :, 5] == 0)


def test_aperture_fields_sum_to_original_for_complete_partition():
    rng = np.random.default_rng(3)
    H = (
        rng.standard_normal((32, 8, 10))
        + 1j * rng.standard_normal((32, 8, 10))
    ).astype(np.complex64)
    H_p = apply_aperture_masks(H, quadrant_masks((8, 10)))

    assert H_p.shape == (32, 4, 8, 10)
    assert H_p.dtype == np.complex64
    np.testing.assert_allclose(H_p.sum(axis=1), H, atol=2e-6)


def test_cross_spectral_matrix_is_hermitian_positive_semidefinite():
    rng = np.random.default_rng(4)
    SH_p = (
        rng.standard_normal((7, 6, 4, 2, 3))
        + 1j * rng.standard_normal((7, 6, 4, 2, 3))
    ).astype(np.complex64)
    cross = quadrant_cross_spectral_matrix(SH_p)

    np.testing.assert_allclose(cross, np.swapaxes(cross.conj(), -1, -2), atol=2e-6)
    eigenvalues = np.linalg.eigvalsh(cross.reshape(-1, 4, 4))
    assert eigenvalues.min() > -2e-5


def test_diagonal_cross_spectra_have_zero_interference_contrasts():
    powers = np.asarray([1, 2, 3, 4], dtype=np.float32)
    cross = np.zeros((1, 2, 3, 4, 4), dtype=np.complex64)
    indices = np.arange(4)
    cross[..., indices, indices] = powers

    result = analyze_cross_spectral_matrix(cross, number_of_estimates=4)

    expected_modes = np.asarray([10, 2, -4, 0], dtype=np.float32)
    np.testing.assert_allclose(result.power_modes[0, :, 0, 0], expected_modes)
    np.testing.assert_allclose(result.interference_contrasts, 0, atol=1e-7)


def test_quadrant_analysis_shapes_follow_frequency_first_convention():
    SH_p = np.ones((4, 8, 4, 3, 5), dtype=np.complex64)
    result = analyze_quadrant_spectra(SH_p)

    assert result.quadrant_powers.shape == (8, 4, 3, 5)
    assert result.cross_spectral_matrix.shape == (8, 3, 5, 4, 4)
    assert result.modal_powers.shape == (8, 4, 3, 5)
