import h5py
import numpy as np

from holodoppler.pipelines.main_spectral_cube import (
    _save_endpoint_pngs,
    _write_cardiac_h5,
)
from holodoppler.spectral_cube import (
    CARDIAC_PULSE_NOT_DETECTED,
    aggregate_single_beat,
    cardiac_phase_analysis,
    cardiac_failure_message,
    cardiac_detection_signal,
    detect_cardiac_landmarks,
    detect_streaks,
    log_power_ratio,
    repair_streaks,
    resolve_cardiac_fc,
    resample_beats,
)


def test_cardiac_landmarks_are_positive_derivative_maxima_of_signed_high_f_power():
    t = np.linspace(0.0, 5.0, 501)
    f = np.array([-200.0, -50.0, 50.0, 200.0])
    waveform = 10.0 + np.sin(2.0 * np.pi * t)
    signal = np.zeros((t.size, f.size), dtype=np.float32)
    signal[:, 0] = 0.25 * waveform
    signal[:, 3] = 0.75 * waveform
    signal[:, 1:3] = 1000.0  # Must be excluded by abs(f) > fc.

    result = cardiac_detection_signal(
        signal,
        t,
        f,
        100.0,
        smoothing_s=0.0,
    )
    (
        landmarks,
        _resolved_prominence,
        _resolved_relative_height,
        _diagnostics,
    ) = (
        detect_cardiac_landmarks(
            result["dg_dt"],
            t,
            min_distance_s=0.7,
            prominence_mad=0.5,
            return_diagnostics=True,
        )
    )

    np.testing.assert_array_equal(
        result["high_frequency_mask"], [True, False, False, True]
    )
    np.testing.assert_allclose(result["g_sum"], waveform, rtol=1e-6)
    assert np.corrcoef(result["g"], waveform - np.mean(waveform))[0, 1] > 0.999
    np.testing.assert_array_equal(result["g"], result["g_smoothed"])
    assert result["median_window_samples"] == 1
    assert result["svd_explained_variance_fraction"] > 0.999
    np.testing.assert_allclose(t[landmarks], [1.0, 2.0, 3.0, 4.0], atol=0.02)
    assert np.all(result["dg_dt"][landmarks] > 0)


def test_cardiac_landmarks_apply_final_half_maximum_threshold():
    t = np.arange(7, dtype=np.float64)
    derivative = np.array([0.0, 10.0, 0.0, 4.0, 0.0, 5.1, 0.0])

    landmarks, _prominence, resolved_height, diagnostics = detect_cardiac_landmarks(
        derivative,
        t,
        min_distance_s=0.5,
        prominence_mad=0.0,
        relative_height=0.5,
        return_diagnostics=True,
    )

    np.testing.assert_array_equal(landmarks, [1, 5])
    assert resolved_height == 5.0
    assert np.all(derivative[landmarks] > 0.5 * np.max(derivative[landmarks]))
    np.testing.assert_array_equal(
        diagnostics["relative_height_rejected_indices"], [3]
    )


def test_cardiac_failure_message_reports_measured_common_causes():
    t = np.arange(5, dtype=np.float64) * 0.1
    f = np.array([-20_000.0, 0.0, 20_000.0])
    detection = {
        "dg_dt": np.array([0.0, 10.0, 0.0, 2.0, 0.0]),
        "high_frequency_mask": np.array([True, False, True]),
        "svd_explained_variance_fraction": 0.4,
    }
    diagnostics = {
        "pre_relative_landmark_indices": np.array([1, 3]),
        "relative_height_rejected_indices": np.array([3]),
    }
    parameters = {
        "spectral_endpoints_cardiac_fc_hz": 14_000.0,
        "spectral_endpoints_cardiac_fc_effective_hz": 14_000.0,
        "spectral_endpoints_peak_relative_height": 0.3,
        "spectral_endpoints_min_beat_duration_s": 0.25,
        "spectral_endpoints_max_beat_duration_s": 2.0,
    }
    no_interval = {
        "beat_periods": np.empty(0),
        "beat_accepted": np.empty(0, dtype=bool),
    }

    message = cardiac_failure_message(
        detection,
        diagnostics,
        np.array([1]),
        no_interval,
        t,
        f,
        parameters,
    )

    assert "configured fc=14000 Hz" in message
    assert "dominant motion-artifact" in message
    assert "Fewer than two maxima survived" in message
    assert "Beat-duration QC cannot run" in message
    assert "too few observable cardiac cycles" in message
    assert "Insufficient cardiac signal" in message

    invalid_intervals = {
        "beat_periods": np.array([0.1, 2.5]),
        "beat_accepted": np.array([False, False]),
    }
    message = cardiac_failure_message(
        detection,
        diagnostics,
        np.array([0, 1, 4]),
        invalid_intervals,
        t,
        f,
        parameters,
    )
    assert "Every surviving interval is outside [0.25, 2] s" in message


def test_cardiac_cutoff_is_capped_at_eighty_percent_nyquist():
    assert resolve_cardiac_fc(12_000, 8_000) == 3_200
    assert resolve_cardiac_fc(12_000, 50_000) == 12_000


def test_temporal_median_filter_removes_impulsive_cardiac_outlier():
    t = np.arange(101, dtype=np.float64) * 0.01
    f = np.array([-200.0, 200.0])
    waveform = 10.0 + np.sin(2.0 * np.pi * t)
    waveform[50] += 100.0
    signal = np.column_stack((0.5 * waveform, 0.5 * waveform)).astype(np.float32)

    result = cardiac_detection_signal(
        signal,
        t,
        f,
        100.0,
        median_window_s=0.05,
        smoothing_s=0.01,
    )

    assert result["median_window_samples"] == 5
    assert result["g_sum"][50] - result["g_sum_median_filtered"][50] > 90.0
    np.testing.assert_allclose(
        result["g_sum_median_filtered"][50], 10.0, atol=0.07
    )
    assert not np.array_equal(result["g"], result["g_smoothed"])


def test_dominant_svd_mode_is_selected_after_per_frequency_mean_removal():
    t = np.linspace(0.0, 4.0, 401)
    f = np.array([-300.0, -200.0, 0.0, 200.0, 300.0])
    dominant = np.sin(2.0 * np.pi * t)
    weaker = 0.2 * np.sin(4.0 * np.pi * t)
    signal = np.full((t.size, f.size), 20.0, dtype=np.float64)
    signal[:, 0] += dominant + weaker
    signal[:, 1] += 2.0 * dominant - weaker
    signal[:, 3] += 2.0 * dominant - weaker
    signal[:, 4] += dominant + weaker

    result = cardiac_detection_signal(
        signal,
        t,
        f,
        100.0,
        median_window_s=0.0,
        smoothing_s=0.0,
    )

    assert abs(np.mean(result["g"])) < 1e-12
    assert np.corrcoef(result["g"], dominant)[0, 1] > 0.999
    assert result["cardiac_singular_values"][0] > result[
        "cardiac_singular_values"
    ][1]
    np.testing.assert_array_equal(
        result["cardiac_frequency_mode"][[2]], [0.0]
    )


def test_phase_normalization_linearly_aligns_beats_of_different_durations():
    t = np.array([0, 0.25, 0.5, 0.75, 1.0, 1.375, 1.75, 2.125, 2.5])
    phase_in_beat = np.where(t <= 1.0, t, (t - 1.0) / 1.5)
    waveform = 2.0 + np.sin(2.0 * np.pi * phase_in_beat)
    signal = np.stack((waveform, 2.0 * waveform), axis=1).astype(np.float32)
    background = (0.5 * signal).astype(np.float32)

    result = resample_beats(
        signal,
        background,
        t,
        np.array([0, 4, 8]),
        phase_bins=4,
        min_duration_s=0.5,
        max_duration_s=1.6,
    )

    assert result["S_beats"].shape == (2, 4, 2)
    np.testing.assert_allclose(result["S_beats"][0], result["S_beats"][1])
    np.testing.assert_allclose(result["phase"], [0.0, 0.25, 0.5, 0.75])
    np.testing.assert_allclose(result["beat_periods"], [1.0, 1.5])
    assert np.all(result["beat_accepted"])


def test_streak_detection_and_repair_change_only_fundus_contaminated_row():
    signal_beats = np.empty((3, 16, 4), dtype=np.float32)
    signal_beats[0] = 1.0
    signal_beats[1] = 2.0
    signal_beats[2] = 4.0
    signal_beats[0, 6, :] = 101.0
    original = signal_beats.copy()
    background_beats = np.arange(3 * 16 * 4, dtype=np.float32).reshape(3, 16, 4)
    background_before = background_beats.copy()

    _trace, streak_mask, _peak_count = detect_streaks(
        signal_beats,
        prominence_mad=6.0,
        threshold_mad=6.0,
        min_width=1.0,
    )
    repaired, insufficient = repair_streaks(
        signal_beats,
        streak_mask,
        min_clean_beats=2,
    )

    assert streak_mask[0, 6]
    assert not np.any(streak_mask[1:])
    assert not np.any(insufficient)
    np.testing.assert_allclose(repaired[0, 6], 3.0)
    np.testing.assert_array_equal(repaired[0, :6], original[0, :6])
    np.testing.assert_array_equal(repaired[0, 7:], original[0, 7:])
    np.testing.assert_array_equal(background_beats, background_before)


def test_repair_flags_too_few_clean_beats_without_inserting_values():
    signal_beats = np.ones((3, 8, 2), dtype=np.float32)
    streak_mask = np.zeros((3, 8), dtype=bool)
    streak_mask[0, 3] = True
    repaired, insufficient = repair_streaks(
        signal_beats,
        streak_mask,
        min_clean_beats=3,
    )
    assert insufficient[0, 3]
    np.testing.assert_array_equal(repaired, signal_beats)


def test_aggregation_occurs_before_log_and_does_not_modify_s0_beats():
    repaired_signal = np.array([1.0, 10.0, 100.0], dtype=np.float32).reshape(3, 1, 1)
    background_beats = np.array([1.0, 100.0, 1.0], dtype=np.float32).reshape(3, 1, 1)
    background_before = background_beats.copy()

    signal, background, log_ratio = aggregate_single_beat(
        repaired_signal,
        background_beats,
    )
    median_of_beat_logs = np.median(
        log_power_ratio(np, repaired_signal, background_beats), axis=0
    )

    np.testing.assert_allclose(signal, [[10.0]])
    np.testing.assert_allclose(background, [[1.0]])
    np.testing.assert_allclose(log_ratio, np.log([[10.0]]))
    assert not np.allclose(log_ratio, median_of_beat_logs)
    np.testing.assert_array_equal(background_beats, background_before)


def test_missing_cardiac_pulse_keeps_longtimes_and_writes_failure_qc(tmp_path):
    t = np.arange(30, dtype=np.float64) * 0.1
    f = np.array([-200.0, 200.0])
    ramp = np.arange(t.size, dtype=np.float32)
    signal = np.column_stack((ramp, 2.0 * ramp)).astype(np.float32)
    background = np.ones_like(signal)
    parameters = {
        "sampling_freq": 1_000.0,
        "spectral_endpoints_cardiac_fc_hz": 100.0,
        "spectral_endpoints_cardiac_fc_effective_hz": 100.0,
        "spectral_endpoints_cardiac_median_window_s": 0.0,
        "spectral_endpoints_cardiac_smoothing_s": 0.0,
        "spectral_endpoints_peak_min_distance_s": 0.3,
        "spectral_endpoints_peak_prominence_mad": 1.0,
        "spectral_endpoints_peak_relative_height": 0.5,
        "spectral_endpoints_min_beat_duration_s": 10.0,
        "spectral_endpoints_max_beat_duration_s": 20.0,
        "spectral_endpoints_phase_bins": 8,
    }

    analysis = cardiac_phase_analysis(signal, background, t, f, parameters)

    assert analysis["pulse_detected"] is False
    assert analysis["pulse_detection_error"].startswith(CARDIAC_PULSE_NOT_DETECTED)
    assert "Measured cardiac-segmentation diagnostics" in analysis[
        "pulse_detection_error"
    ]
    assert analysis["S_beats"].shape == (0, 8, 2)

    path = tmp_path / "no-pulse.h5"
    with h5py.File(path, "w") as handle:
        spectrograms = handle.create_group("spectrograms")
        spectrograms.attrs["source_file"] = str(
            tmp_path / "no_pulse_recording.holo"
        )
        longtimes = spectrograms.create_group("longtimes")
        longtimes.create_dataset("S", data=signal)
        longtimes.create_dataset("S0", data=background)
        longtimes.create_dataset("L", data=np.zeros_like(signal))
        longtimes.create_dataset("t", data=t)
        longtimes.create_dataset("f", data=f)
        _write_cardiac_h5(spectrograms, analysis, parameters)

        assert "spectrograms/longtimes/g" in handle
        assert "spectrograms/singlebeat" in handle
        assert "spectrograms/singlebeat/S" not in handle
        assert not bool(handle["spectrograms/singlebeat"].attrs["pulse_detected"])
        assert handle["spectrograms/singlebeat"].attrs[
            "pulse_detection_error"
        ].startswith(
            CARDIAC_PULSE_NOT_DETECTED
        )

    _save_endpoint_pngs(path, tmp_path, {"contrast": False})
    png_names = {item.name for item in (tmp_path / "png").iterdir()}
    assert {
        "no_pulse_recording_longtimes_S.png",
        "no_pulse_recording_longtimes_S0.png",
        "no_pulse_recording_longtimes_L.png",
        "no_pulse_recording_cardiac_segmentation_qc.png",
    }.issubset(png_names)
    assert "no_pulse_recording_singlebeat_S.png" not in png_names


def test_grouped_hdf5_schema_contains_longtimes_singlebeat_and_qc(tmp_path):
    path = tmp_path / "endpoints.h5"
    t = np.arange(6, dtype=np.float64) * 0.1
    f = np.array([-2.0, 0.0, 2.0])
    phase = np.arange(4, dtype=np.float64) / 4
    analysis = {
        "g": np.arange(6, dtype=np.float64),
        "g_sum": np.arange(6, dtype=np.float64) + 10.0,
        "g_sum_median_filtered": np.arange(6, dtype=np.float64) + 9.0,
        "g_smoothed": np.arange(6, dtype=np.float64),
        "dg_dt": np.ones(6, dtype=np.float64),
        "high_frequency_mask": np.array([True, False, True]),
        "cardiac_singular_values": np.array([5.0, 1.0]),
        "cardiac_frequency_mode": np.array([0.5, 0.0, 0.5]),
        "svd_explained_variance_fraction": 25.0 / 26.0,
        "svd_sign": -1,
        "S": np.ones((4, 3), dtype=np.float32),
        "S0": np.full((4, 3), 0.5, dtype=np.float32),
        "L": np.full((4, 3), np.log(2.0), dtype=np.float32),
        "phase": phase,
        "beat_landmark_indices": np.array([0, 3, 5]),
        "beat_landmark_times": t[[0, 3, 5]],
        "beat_periods": np.array([0.3, 0.2]),
        "beat_accepted": np.array([True, False]),
        "accepted_beat_indices": np.array([0]),
        "rejected_beat_indices": np.array([1]),
        "streak_trace": np.ones((1, 4), dtype=np.float32),
        "streak_mask": np.array([[False, True, False, False]]),
        "streak_peak_count": np.array([1]),
        "streak_unrepaired_mask": np.zeros((1, 4), dtype=bool),
        "resolved_peak_prominence": 2.5,
        "resolved_peak_relative_height": 1.25,
        "median_window_samples": 5,
        "median_window_resolved_s": 0.5,
    }
    parameters = {
        "sampling_freq": 100.0,
        "spectral_endpoints_cardiac_fc_hz": 14_000.0,
        "spectral_endpoints_cardiac_fc_effective_hz": 40.0,
        "spectral_endpoints_cardiac_median_window_s": 0.035,
        "spectral_endpoints_cardiac_smoothing_s": 0.02,
        "spectral_endpoints_peak_relative_height": 0.3,
    }

    with h5py.File(path, "w") as handle:
        spectrograms = handle.create_group("spectrograms")
        spectrograms.attrs["source_file"] = str(
            tmp_path / "retina_sample.holo"
        )
        longtimes = spectrograms.create_group("longtimes")
        longtimes.create_dataset("S", data=np.ones((6, 3), dtype=np.float32))
        longtimes.create_dataset("S0", data=np.ones((6, 3), dtype=np.float32))
        longtimes.create_dataset("L", data=np.zeros((6, 3), dtype=np.float32))
        longtimes.create_dataset("t", data=t)
        longtimes.create_dataset("f", data=f)
        longtimes.create_dataset("frame_start", data=np.arange(6))
        _write_cardiac_h5(spectrograms, analysis, parameters)

        required_longtimes = {
            "S",
            "S0",
            "L",
            "t",
            "f",
            "frame_start",
            "g",
            "g_sum",
            "g_sum_median_filtered",
            "dg_dt",
            "cardiac_singular_values",
            "cardiac_frequency_mode",
        }
        required_singlebeat = {
            "S",
            "S0",
            "L",
            "phase",
            "f",
            "beat_landmark_indices",
            "beat_landmark_times",
            "beat_periods",
            "streak_mask",
            "streak_unrepaired_mask",
        }
        assert required_longtimes.issubset(spectrograms["longtimes"])
        assert required_singlebeat.issubset(spectrograms["singlebeat"])
        assert spectrograms["singlebeat/S"].shape == (4, 3)
        assert spectrograms["singlebeat/S0"].shape == (4, 3)
        assert spectrograms["singlebeat/L"].shape == (4, 3)
        assert spectrograms["singlebeat/phase"].shape == (4,)
        assert spectrograms["longtimes/g"].shape == spectrograms["longtimes/t"].shape
        assert spectrograms["longtimes/g_sum"].shape == spectrograms["longtimes/t"].shape
        assert spectrograms["longtimes/dg_dt"].shape == spectrograms["longtimes/t"].shape
        assert spectrograms["singlebeat/f"].id == spectrograms["longtimes/f"].id
        assert spectrograms["longtimes/g"].attrs["fc_hz"] == 40.0
        assert spectrograms["longtimes/g"].attrs["svd_mode_index"] == 0
        assert spectrograms["singlebeat"].attrs["resolved_peak_relative_height"] == 1.25

    _save_endpoint_pngs(path, tmp_path, {"contrast": False})
    expected_pngs = {
        "retina_sample_longtimes_S.png",
        "retina_sample_longtimes_S0.png",
        "retina_sample_longtimes_L.png",
        "retina_sample_singlebeat_S.png",
        "retina_sample_singlebeat_S0.png",
        "retina_sample_singlebeat_L.png",
        "retina_sample_cardiac_segmentation_qc.png",
        "retina_sample_singlebeat_streak_mask.png",
        "retina_sample_streak_qc_beat_0000.png",
    }
    assert expected_pngs.issubset(
        {item.name for item in (tmp_path / "png").iterdir()}
    )
