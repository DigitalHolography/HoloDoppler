import numpy as np
import pytest
import h5py

import holodoppler.saving as saving
from holodoppler.saving import (
    _power_to_relative_db,
    _spectral_cube_frequency_indices,
    _time_average_spectral_cube,
)
from holodoppler.spectral_cube import (
    binned_fft_frequencies,
    corner_ellipse_mask,
    corner_mean_power,
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


def test_spectral_cube_frequency_indices_support_all_and_deduplication():
    assert _spectral_cube_frequency_indices("all", 3) == [0, 1, 2]
    assert _spectral_cube_frequency_indices([2, 0, 2], 3) == [2, 0]


def test_spectral_cube_frequency_indices_validate_bounds():
    with pytest.raises(ValueError, match="outside"):
        _spectral_cube_frequency_indices([3], 3)


def test_time_average_spectral_cube_uses_t_axis(tmp_path):
    h5_path = tmp_path / "cube.h5"
    cube = np.arange(3 * 2 * 4 * 5, dtype=np.float32).reshape(3, 2, 4, 5)
    with h5py.File(h5_path, "w") as handle:
        dataset = handle.create_dataset("S", data=cube)
        result = _time_average_spectral_cube(dataset, chunk_size=2)
    np.testing.assert_allclose(result, np.mean(cube, axis=0))


def test_power_to_relative_db_uses_power_decibels_and_floor():
    result = _power_to_relative_db(np.array([1.0, 0.1, 0.0]), floor_db=-20)
    np.testing.assert_allclose(result, [0.0, -10.0, -20.0])


def test_power_to_relative_db_accepts_per_frequency_floor():
    power = np.array([[[10.0, 1.0]], [[10.0, 1.0]]], dtype=np.float32)
    result = _power_to_relative_db(power, floor_power=np.array([1.0, 5.0]))
    np.testing.assert_allclose(result[0], [[0.0, -10.0]])
    np.testing.assert_allclose(result[1], [[0.0, 10 * np.log10(0.5)]])


def test_save_spectral_cube_avi_exports_frequency_axis(tmp_path, monkeypatch):
    h5_path = tmp_path / "cube.h5"
    target_dir = tmp_path / "output"
    cube = np.arange(3 * 2 * 4 * 5, dtype=np.float32).reshape(3, 2, 4, 5)
    with h5py.File(h5_path, "w") as handle:
        handle.create_dataset("S", data=cube)
        handle.create_dataset("f", data=[-100.0, 100.0])
        handle.create_dataset(
            "corner_average_power",
            data=np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]),
        )

    writes = []

    def record_write(path, frames, fps, **kwargs):
        writes.append((path, np.asarray(frames), fps, kwargs))

    monkeypatch.setattr(saving, "_write_video_fast", record_write)
    path = saving.save_spectral_cube_avi(
        h5_path,
        target_dir,
        {
            "spectral_cube_avi": True,
            "spectral_cube_avi_frequency_indices": [1],
            "spectral_cube_avi_fps": 12,
            "spectral_cube_avi_time_chunk": 2,
            "contrast": False,
        },
    )

    assert path.name == "spectral_cube_time_average_log_f.avi"
    assert writes[0][1].shape == (1, 4, 5)
    assert writes[0][1].dtype == np.uint8
    assert writes[0][2] == 12.0
    assert writes[0][3] == {"codec": "mjpeg", "quality": 8}
    frequency_csv = target_dir / "avi" / "spectral_cube_time_average_log_f_frequency_hz.csv"
    assert frequency_csv.is_file()
    assert "0,1,100,4" in frequency_csv.read_text()
