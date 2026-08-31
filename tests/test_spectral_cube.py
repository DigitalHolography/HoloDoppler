import numpy as np

from holodoppler.spectral_cube import (
    binned_fft_frequencies,
    centered_ellipse_mask,
    corner_ellipse_mask,
    corner_mean_power,
    estimated_endpoint_bytes,
    ellipse_mean_power,
    log_power_ratio,
    mean_bin_axis,
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


def test_corner_ellipse_mask_selects_only_outer_corners():
    mask = corner_ellipse_mask(np, 10, 12, 1.2, 1.2)
    assert mask[0, 0]
    assert mask[-1, -1]
    assert not mask[5, 6]


def test_corner_mean_power_is_frequency_resolved():
    mask = corner_ellipse_mask(np, 10, 12, 1.2, 1.2)
    spectrum = np.zeros((2, 10, 12), dtype=np.float32)
    spectrum[0, mask] = 3.0
    spectrum[1, mask] = 7.0
    np.testing.assert_allclose(corner_mean_power(np, spectrum), [3.0, 7.0])


def test_signal_ellipse_mean_power_is_frequency_resolved():
    mask = centered_ellipse_mask(np, 10, 12, 0.8, 0.8)
    spectrum = np.zeros((2, 10, 12), dtype=np.float32)
    spectrum[0, mask] = 5.0
    spectrum[1, mask] = 11.0
    np.testing.assert_allclose(
        ellipse_mean_power(np, spectrum, 0.8, 0.8),
        [5.0, 11.0],
    )


def test_estimated_endpoint_bytes_counts_s_s0_and_l():
    assert estimated_endpoint_bytes(2, 3) == 2 * 3 * 3 * 4


def test_log_power_ratio_uses_natural_log_and_float32_output():
    signal = np.array([1.0, np.e**2, 0.0], dtype=np.float32)
    background = np.array([1.0, 1.0, 0.0], dtype=np.float32)
    result = log_power_ratio(np, signal, background)
    np.testing.assert_allclose(result, [0.0, 2.0, 0.0], rtol=1e-6)
    assert result.dtype == np.float32
