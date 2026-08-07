import cv2
import numpy as np

from holodoppler.multidimensional import (
    SlidingAnalysisAVIWriter,
    analyze_sliding_window,
    sliding_window_starts,
)


def test_sliding_window_starts_cover_a_nondivisible_tail():
    assert sliding_window_starts(160, window_length=64, stride=64) == (0, 64, 96)
    assert sliding_window_starts(
        160, window_length=64, stride=64, include_last=False
    ) == (0, 64)


def test_sliding_analysis_returns_finite_reduced_maps():
    rng = np.random.default_rng(33)
    H = (
        rng.standard_normal((32, 4, 4))
        + 1j * rng.standard_normal((32, 4, 4))
    ).astype(np.complex64)

    result = analyze_sliding_window(
        H,
        8_000.0,
        svd_remove_modes=2,
        spectral_block_length=32,
        spectral_nfft=32,
        number_of_tapers=2,
    )

    required = {
        "filtered_amplitude",
        "doppler_total_0250_4000",
        "coupling_coherence2_total_0250_4000",
        "delay_x_contrast_total_0250_4000",
        "delay_y_contrast_mid_1000_3000",
        "delay_xy_plus_total",
    }
    assert required <= result.maps.keys()
    for values in result.maps.values():
        assert values.shape == (4, 4)
        assert np.all(np.isfinite(values))
    assert result.number_of_spectral_estimates == 2
    assert result.aperture_pixel_counts == (4, 4, 4, 4)
    assert result.delay_identity_max_abs_error == 0


def _video_maps(shape=(8, 10)):
    rng = np.random.default_rng(34)
    positive = np.abs(rng.standard_normal(shape)).astype(np.float32) + 0.1
    signed = (0.1 * rng.standard_normal(shape)).astype(np.float32)
    maps = {
        "raw_mean": positive,
        "unfiltered_amplitude": positive,
        "removed_power": positive,
        "filtered_amplitude": positive,
    }
    for name in (
        "total_0250_4000",
        "low_0250_1000",
        "mid_1000_3000",
        "high_3000_4000",
    ):
        maps[f"doppler_{name}"] = positive
        maps[f"coupling_cross_{name}"] = positive
        maps[f"coupling_coherence2_{name}"] = np.clip(positive / 3, 0, 1)
        maps[f"coupling_phase_{name}"] = signed
        for mode in ("x", "y", "xy"):
            maps[f"delay_{mode}_contrast_{name}"] = signed
    for mode in ("x", "y", "xy"):
        maps[f"delay_{mode}_plus_total"] = positive
        maps[f"delay_{mode}_minus_total"] = positive
    return maps


def test_avi_writer_creates_readable_overview_streams(tmp_path):
    output = tmp_path / "videos"
    writer = SlidingAnalysisAVIWriter(
        output,
        playback_fps=10,
        source_shape=(8, 10),
        panel_width=80,
    )
    writer.write(_video_maps(), "synthetic window")
    writer.close()

    assert writer.frame_count == 1
    for path in writer.paths.values():
        assert path.is_file() and path.stat().st_size > 0
        capture = cv2.VideoCapture(str(path))
        ok, frame = capture.read()
        capture.release()
        assert ok
        assert frame.ndim == 3 and frame.shape[-1] == 3
