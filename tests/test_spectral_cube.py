import numpy as np
import pytest

from holodoppler.spectral_cube import (
    binned_fft_frequencies,
    estimated_cube_bytes,
    mean_bin_axis,
    spatial_block_mean,
    window_starts,
)


def test_window_starts_uses_only_complete_windows():
    starts = window_starts(10, 31, batch_size=8, batch_stride=5)
    np.testing.assert_array_equal(starts, [10, 15, 20])


def test_window_starts_rejects_incomplete_range():
    assert window_starts(10, 17, batch_size=8, batch_stride=2).size == 0


def test_mean_bin_axis_averages_contiguous_bins():
    values = np.arange(24, dtype=np.float32).reshape(8, 3)
    result = mean_bin_axis(np, values, target_bins=4, axis=0)
    expected = values.reshape(4, 2, 3).mean(axis=1)
    np.testing.assert_allclose(result, expected)


def test_mean_bin_axis_covers_nondivisible_source():
    values = np.arange(10, dtype=np.float32)
    result = mean_bin_axis(np, values, target_bins=4)
    np.testing.assert_allclose(result, [0.5, 3.0, 5.5, 8.0])


def test_binned_fft_frequencies_cover_full_signed_range():
    result = binned_fft_frequencies(8.0, batch_size=8, target_bins=4)
    np.testing.assert_allclose(result, [-3.5, -1.5, 0.5, 2.5])


def test_spatial_block_mean_preserves_independent_axis_ratios():
    values = np.arange(2 * 4 * 6, dtype=np.float32).reshape(2, 4, 6)
    result = spatial_block_mean(np, values, ratio_y=2, ratio_x=3)
    expected = values.reshape(2, 2, 2, 2, 3).mean(axis=(2, 4))
    np.testing.assert_allclose(result, expected)
    assert result.shape == (2, 2, 2)


def test_spatial_block_mean_requires_exact_divisibility():
    with pytest.raises(ValueError, match="divisible"):
        spatial_block_mean(np, np.zeros((2, 5, 8)), ratio_y=2, ratio_x=4)


def test_estimated_cube_bytes_uses_float32_by_default():
    assert estimated_cube_bytes(2, 3, 4, 5) == 2 * 3 * 4 * 5 * 4
