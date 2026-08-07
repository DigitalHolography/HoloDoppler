import numpy as np

from holodoppler.multidimensional import (
    analyze_axial_gouy,
    axial_mode_svd,
    band_limited_svd,
    depth_time_svd,
    matrix_svd,
    space_time_svd,
    space_time_svd_filter,
    unfold_depth_aperture_time,
    unfold_depth_time,
    unfold_space_time,
)


def test_exact_complex_svd_reconstructs_matrix():
    rng = np.random.default_rng(6)
    X = (
        rng.standard_normal((30, 12)) + 1j * rng.standard_normal((30, 12))
    ).astype(np.complex64)
    result = matrix_svd(X)

    assert result.singular_values.dtype == np.float32
    np.testing.assert_allclose(result.reconstruct(), X, atol=2e-5, rtol=2e-5)


def test_rank_truncation_is_optional():
    rng = np.random.default_rng(7)
    X = rng.standard_normal((20, 10)).astype(np.float32)

    full = matrix_svd(X)
    truncated = matrix_svd(X, rank=3)

    assert full.rank == 10
    assert truncated.rank == 3
    np.testing.assert_allclose(truncated.singular_values, full.singular_values[:3])


def test_current_and_joint_unfolding_axes():
    H = np.arange(2 * 3 * 4).reshape(2, 3, 4)
    np.testing.assert_array_equal(unfold_space_time(H), H.reshape(2, -1).T)

    H_z = np.arange(2 * 5 * 3 * 4).reshape(2, 5, 3, 4)
    np.testing.assert_array_equal(unfold_depth_time(H_z), H_z.reshape(2, -1).T)

    H_zp = np.arange(2 * 5 * 4 * 3 * 4).reshape(2, 5, 4, 3, 4)
    np.testing.assert_array_equal(
        unfold_depth_aperture_time(H_zp), H_zp.reshape(2, -1).T
    )


def test_fixed_sample_selection_and_weighting_precede_svd():
    H = np.arange(4 * 2 * 3, dtype=np.float32).reshape(4, 2, 3)
    mask = np.asarray([[True, False, True], [False, True, False]])
    weights = np.asarray([[1, 0, 2], [0, -1, 0]], dtype=np.float32)

    unfolded = unfold_space_time(H, sample_mask=mask, sample_weights=weights)
    expected = H.reshape(4, -1).T[mask.reshape(-1)]
    expected *= weights.reshape(-1)[mask.reshape(-1), None]

    np.testing.assert_array_equal(unfolded, expected)


def test_complete_depth_stack_scales_singular_values_by_sqrt_nz():
    rng = np.random.default_rng(8)
    H = (
        rng.standard_normal((16, 3, 4)) + 1j * rng.standard_normal((16, 3, 4))
    ).astype(np.complex64)
    phases = np.exp(1j * np.asarray([0.0, 0.7, 1.4], dtype=np.float32))
    H_z = H[:, None, :, :] * phases[None, :, None, None]

    base = space_time_svd(H)
    stacked = depth_time_svd(H_z)

    np.testing.assert_allclose(
        stacked.singular_values[: base.rank],
        np.sqrt(3) * base.singular_values,
        atol=3e-5,
        rtol=3e-5,
    )
    np.testing.assert_allclose(stacked.singular_values[base.rank :], 0, atol=5e-3)


def test_full_temporal_fourier_transform_preserves_singular_values():
    rng = np.random.default_rng(9)
    H = (
        rng.standard_normal((16, 3, 4)) + 1j * rng.standard_normal((16, 3, 4))
    ).astype(np.complex64)
    base = space_time_svd(H)
    transformed = band_limited_svd(H, np.ones(16, dtype=bool))

    np.testing.assert_allclose(
        transformed.singular_values,
        base.singular_values,
        atol=3e-5,
        rtol=3e-5,
    )


def test_space_time_svd_filter_projects_out_largest_temporal_modes():
    rng = np.random.default_rng(19)
    H = (
        rng.standard_normal((16, 5, 6)) + 1j * rng.standard_normal((16, 5, 6))
    ).astype(np.complex64)

    result = space_time_svd_filter(H, 3)
    original = unfold_space_time(H)
    rejected = result.temporal_modes[:, :3]
    expected = original - (original @ rejected) @ rejected.conj().T
    filtered = unfold_space_time(result.filtered_field)

    assert result.filtered_field.shape == H.shape
    assert result.filtered_field.dtype == np.complex64
    assert result.singular_values.dtype == np.float32
    assert result.removed_mode_count == 3
    assert np.all(np.diff(result.singular_values) <= 0)
    np.testing.assert_allclose(filtered, expected, atol=2e-5, rtol=2e-5)
    np.testing.assert_allclose(filtered @ rejected, 0, atol=3e-5)


def test_space_time_svd_filter_validates_mode_count():
    H = np.ones((4, 2, 3), dtype=np.complex64)

    for invalid in (-1, 5, 1.5):
        with np.testing.assert_raises(ValueError):
            space_time_svd_filter(H, invalid)


def test_axial_svd_shapes_and_gouy_candidate_ranking():
    rng = np.random.default_rng(10)
    H_z = (
        rng.standard_normal((8, 9, 2, 3)) + 1j * rng.standard_normal((8, 9, 2, 3))
    ).astype(np.complex64)
    axial = axial_mode_svd(H_z, rank=3)

    assert axial.spatiotemporal_modes.shape == (3, 8, 2, 3)
    assert axial.axial_modes.shape == (9, 3)

    mode = np.ones((9, 1), dtype=np.complex64)
    mode[5:] = -1
    result = analyze_axial_gouy(
        mode,
        half_width=2,
        depths=np.arange(9, dtype=np.float32),
        top_k=2,
    )
    np.testing.assert_allclose(result.correlation[4, 0], -1 + 0j, atol=1e-7)
    assert set(result.candidate_indices[0]) == {4, 5}
    assert set(result.candidate_depths[0]) == {4, 5}
