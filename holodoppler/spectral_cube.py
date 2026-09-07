"""Array helpers for streamed Doppler spectral cubes."""

from __future__ import annotations

from functools import cache

import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.signal import find_peaks


CARDIAC_PULSE_NOT_DETECTED = (
    "No valid cardiac beats remain after landmark detection and duration QC"
)


def window_starts(
    first_frame: int,
    end_frame: int,
    batch_size: int,
    batch_stride: int,
) -> np.ndarray:
    """Return the first input frame of every complete temporal window."""
    values = {
        "first_frame": first_frame,
        "end_frame": end_frame,
        "batch_size": batch_size,
        "batch_stride": batch_stride,
    }
    for name, value in values.items():
        if not isinstance(value, (int, np.integer)):
            raise TypeError(f"{name} must be an integer, got {type(value).__name__}")

    if first_frame < 0:
        raise ValueError("first_frame must be non-negative")
    if end_frame <= first_frame:
        raise ValueError("end_frame must be greater than first_frame")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if batch_stride <= 0:
        raise ValueError("batch_stride must be positive")

    final_start = end_frame - batch_size
    if final_start < first_frame:
        return np.empty(0, dtype=np.int64)
    return np.arange(first_frame, final_start + 1, batch_stride, dtype=np.int64)


def mean_bin_axis(xp, values, target_bins: int, axis: int = 0):
    """Average contiguous samples into ``target_bins`` along one axis."""
    if not isinstance(target_bins, (int, np.integer)) or target_bins <= 0:
        raise ValueError("target_bins must be a positive integer")

    axis = axis % values.ndim
    source_bins = values.shape[axis]
    if target_bins > source_bins:
        raise ValueError(
            f"target_bins ({target_bins}) cannot exceed source bins ({source_bins})"
        )

    moved = xp.moveaxis(values, axis, 0)
    if source_bins % target_bins == 0:
        bin_width = source_bins // target_bins
        binned = moved.reshape(
            (target_bins, bin_width) + tuple(moved.shape[1:])
        ).mean(axis=1)
    else:
        # Unequal integer-width bins cover the complete source axis exactly.
        edges = np.linspace(0, source_bins, target_bins + 1, dtype=np.int64)
        binned = xp.stack(
            [
                moved[start:stop].mean(axis=0)
                for start, stop in zip(edges[:-1], edges[1:])
            ],
            axis=0,
        )

    return xp.moveaxis(binned, 0, axis)


def binned_fft_frequencies(
    sampling_frequency: float,
    batch_size: int,
    target_bins: int,
) -> np.ndarray:
    """Return averaged centers spanning the complete signed FFT frequency range."""
    if not np.isfinite(sampling_frequency) or sampling_frequency <= 0:
        raise ValueError("sampling_frequency must be a positive finite number")
    if not isinstance(batch_size, (int, np.integer)) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")

    frequencies = np.fft.fftshift(
        np.fft.fftfreq(batch_size, d=1.0 / float(sampling_frequency))
    )
    return np.asarray(
        mean_bin_axis(np, frequencies, target_bins, axis=0), dtype=np.float64
    )


@cache
def centered_ellipse_mask(
    xp,
    ny: int,
    nx: int,
    radius_y_factor: float,
    radius_x_factor: float,
):
    """Return pixels inside a centered ellipse."""
    radius_y_factor = float(radius_y_factor)
    radius_x_factor = float(radius_x_factor)
    if not np.isfinite(radius_y_factor) or radius_y_factor <= 0:
        raise ValueError("radius_y_factor must be a positive finite number")
    if not np.isfinite(radius_x_factor) or radius_x_factor <= 0:
        raise ValueError("radius_x_factor must be a positive finite number")

    radius_y = radius_y_factor * ny / 2.0
    radius_x = radius_x_factor * nx / 2.0
    center_y = (ny - 1) / 2.0
    center_x = (nx - 1) / 2.0
    yy, xx = xp.ogrid[:ny, :nx]
    inside = (
        ((yy - center_y) / radius_y) ** 2
        + ((xx - center_x) / radius_x) ** 2
        <= 1.0
    )
    if not bool(xp.any(inside)):
        raise ValueError(
            "The centered ellipse does not contain any pixels; increase one or "
            "both radius factors"
        )
    return inside


def ellipse_median_power(
    xp,
    spectrum,
    radius_y_factor: float,
    radius_x_factor: float,
    *,
    outside: bool = False,
):
    """Take the spatial median inside or outside an ellipse for every frequency."""
    if spectrum.ndim != 3:
        raise ValueError(f"Expected spectrum with shape (f,y,x), got {spectrum.shape}")
    ny, nx = spectrum.shape[-2:]
    inside = centered_ellipse_mask(
        xp,
        ny,
        nx,
        radius_y_factor=radius_y_factor,
        radius_x_factor=radius_x_factor,
    )
    region = ~inside if outside else inside
    if not bool(xp.any(region)):
        location = "outside" if outside else "inside"
        raise ValueError(
            f"The region {location} the centered ellipse contains no pixels"
        )
    frequency_planes = spectrum.reshape(spectrum.shape[0], -1)
    region_values = frequency_planes[:, region.reshape(-1)]
    return xp.median(region_values, axis=1).astype(xp.float32, copy=False)


def corner_ellipse_mask(
    xp,
    ny: int,
    nx: int,
    radius_y_factor: float = 1.2,
    radius_x_factor: float = 1.2,
):
    """Return pixels outside a centered ellipse as a corner-region mask."""
    return ~centered_ellipse_mask(
        xp,
        ny,
        nx,
        radius_y_factor,
        radius_x_factor,
    )


def corner_median_power(
    xp,
    spectrum,
    radius_y_factor: float = 1.2,
    radius_x_factor: float = 1.2,
):
    """Take the spatial median outside the configured centered ellipse."""
    return ellipse_median_power(
        xp,
        spectrum,
        radius_y_factor=radius_y_factor,
        radius_x_factor=radius_x_factor,
        outside=True,
    )


def estimated_endpoint_bytes(
    time_points: int,
    frequency_bins: int,
    *,
    endpoint_count: int = 3,
    bytes_per_value: int = 4,
) -> int:
    """Return the payload size of uncompressed S, S0, and L arrays."""
    dimensions = (time_points, frequency_bins, endpoint_count)
    if any(value < 0 for value in dimensions):
        raise ValueError("Endpoint dimensions must be non-negative")
    return int(np.prod(dimensions, dtype=np.int64)) * bytes_per_value


def log_power_ratio(xp, signal, background):
    """Return the natural log of signal/background with float32 zero protection."""
    if signal.shape != background.shape:
        raise ValueError(
            f"S and S0 must have identical shapes, got {signal.shape} and "
            f"{background.shape}"
        )
    numerical_floor = xp.asarray(np.finfo(np.float32).tiny, dtype=xp.float32)
    return xp.log(
        xp.maximum(signal, numerical_floor)
        / xp.maximum(background, numerical_floor)
    ).astype(xp.float32, copy=False)


def _robust_mad_scale(values: np.ndarray) -> float:
    """Return a MAD-based scale with only a numerical fallback for flat data."""
    values = np.asarray(values, dtype=np.float64)
    center = float(np.median(values))
    scale = 1.4826 * float(np.median(np.abs(values - center)))
    numerical = np.finfo(np.float64).eps * max(1.0, float(np.max(np.abs(values))))
    return max(scale, numerical)


def resolve_cardiac_fc(configured_fc_hz: float, sampling_frequency_hz: float) -> float:
    """Cap the configured cutoff at 80% of the temporal Nyquist frequency."""
    configured_fc_hz = float(configured_fc_hz)
    sampling_frequency_hz = float(sampling_frequency_hz)
    if not np.isfinite(configured_fc_hz) or configured_fc_hz < 0:
        raise ValueError("spectral_endpoints_cardiac_fc_hz must be non-negative")
    if not np.isfinite(sampling_frequency_hz) or sampling_frequency_hz <= 0:
        raise ValueError("sampling_freq must be a positive finite number")
    return min(configured_fc_hz, 0.8 * sampling_frequency_hz / 2.0)


def cardiac_detection_signal(
    signal: np.ndarray,
    t: np.ndarray,
    f: np.ndarray,
    fc_hz: float,
    *,
    median_window_s: float = 0.0,
    smoothing_s: float = 0.0,
):
    """Extract the dominant temporal SVD mode of median-filtered high-f S."""
    signal = np.asarray(signal)
    t = np.asarray(t, dtype=np.float64)
    f = np.asarray(f, dtype=np.float64)
    fc_hz = float(fc_hz)
    median_window_s = float(median_window_s)
    smoothing_s = float(smoothing_s)
    if signal.ndim != 2 or signal.shape != (t.size, f.size):
        raise ValueError(
            "S, t, and f must have compatible shapes (time,frequency); got "
            f"S{signal.shape}, t{t.shape}, f{f.shape}"
        )
    if t.size < 3:
        raise ValueError("At least three long-time samples are required")
    if not np.all(np.isfinite(t)) or not np.all(np.diff(t) > 0):
        raise ValueError("t must be finite and strictly increasing")
    if not np.isfinite(fc_hz) or fc_hz < 0:
        raise ValueError("spectral_endpoints_cardiac_fc_hz must be non-negative")
    if not np.isfinite(median_window_s) or median_window_s < 0:
        raise ValueError(
            "spectral_endpoints_cardiac_median_window_s must be non-negative"
        )
    if not np.isfinite(smoothing_s) or smoothing_s < 0:
        raise ValueError("spectral_endpoints_cardiac_smoothing_s must be non-negative")

    high_frequency = np.abs(f) > fc_hz
    if not np.any(high_frequency):
        raise ValueError(
            "No Doppler-frequency bins satisfy abs(f) > "
            f"spectral_endpoints_cardiac_fc_hz ({fc_hz:g} Hz)"
        )
    high_frequency_signal = np.asarray(
        signal[:, high_frequency], dtype=np.float64
    )
    if not np.all(np.isfinite(high_frequency_signal)):
        raise ValueError("Selected high-frequency S contains non-finite values")
    cardiac_sum = np.sum(high_frequency_signal, axis=1, dtype=np.float64)
    median_dt = float(np.median(np.diff(t)))
    median_samples = 1
    if median_window_s > 0:
        requested_samples = median_window_s / median_dt
        lower_odd = max(1, int(np.floor(requested_samples)))
        if lower_odd % 2 == 0:
            lower_odd -= 1
        upper_odd = lower_odd + 2
        median_samples = (
            lower_odd
            if requested_samples - lower_odd < upper_odd - requested_samples
            else upper_odd
        )
        if median_samples > t.size:
            raise ValueError(
                "Resolved cardiac median window exceeds the long-time signal length"
            )
    median_filtered_matrix = median_filter(
        high_frequency_signal,
        size=(median_samples, 1),
        mode="nearest",
    )
    median_filtered_sum = np.sum(
        median_filtered_matrix, axis=1, dtype=np.float64
    )
    centered = median_filtered_matrix - np.mean(
        median_filtered_matrix, axis=0, keepdims=True
    )
    temporal_modes, singular_values, frequency_modes = np.linalg.svd(
        centered,
        full_matrices=False,
    )
    if singular_values.size == 0 or singular_values[0] <= 0:
        raise ValueError(
            "The median-filtered high-frequency spectrum has no temporal variation"
        )

    cardiac_signal = singular_values[0] * temporal_modes[:, 0]
    frequency_mode = frequency_modes[0].copy()
    reference = cardiac_sum - np.mean(cardiac_sum)
    svd_sign = 1
    if float(np.dot(cardiac_signal, reference)) < 0:
        cardiac_signal = -cardiac_signal
        frequency_mode = -frequency_mode
        svd_sign = -1

    smoothed = cardiac_signal.copy()
    if smoothing_s > 0:
        smoothed = gaussian_filter1d(
            cardiac_signal,
            sigma=smoothing_s / median_dt,
            mode="nearest",
        )
    derivative = np.gradient(smoothed, t, edge_order=2)
    full_frequency_mode = np.zeros(f.size, dtype=np.float64)
    full_frequency_mode[high_frequency] = frequency_mode
    singular_power = np.square(singular_values)
    explained_fraction = float(singular_power[0] / np.sum(singular_power))
    return {
        "g": cardiac_signal,
        "g_sum": cardiac_sum,
        "g_sum_median_filtered": median_filtered_sum,
        "g_smoothed": smoothed,
        "dg_dt": derivative,
        "high_frequency_mask": high_frequency,
        "median_window_samples": median_samples,
        "median_window_resolved_s": median_samples * median_dt,
        "cardiac_singular_values": singular_values,
        "cardiac_frequency_mode": full_frequency_mode,
        "svd_explained_variance_fraction": explained_fraction,
        "svd_sign": svd_sign,
    }


def detect_cardiac_landmarks(
    derivative: np.ndarray,
    t: np.ndarray,
    *,
    min_distance_s: float,
    prominence_mad: float,
    relative_height: float = 0.3,
    return_diagnostics: bool = False,
):
    """Select positive dg/dt maxima using prominence, spacing, and height QC."""
    derivative = np.asarray(derivative, dtype=np.float64)
    t = np.asarray(t, dtype=np.float64)
    min_distance_s = float(min_distance_s)
    prominence_mad = float(prominence_mad)
    relative_height = float(relative_height)
    if derivative.shape != t.shape:
        raise ValueError("derivative and t must have identical shapes")
    if not np.isfinite(min_distance_s) or min_distance_s <= 0:
        raise ValueError("spectral_endpoints_peak_min_distance_s must be positive")
    if not np.isfinite(prominence_mad) or prominence_mad < 0:
        raise ValueError("spectral_endpoints_peak_prominence_mad must be non-negative")
    if not np.isfinite(relative_height) or not 0 <= relative_height <= 1:
        raise ValueError(
            "spectral_endpoints_peak_relative_height must be between 0 and 1"
        )

    resolved_prominence = prominence_mad * _robust_mad_scale(derivative)
    candidates, properties = find_peaks(
        derivative,
        prominence=resolved_prominence,
    )
    positive = derivative[candidates] > 0
    candidates = candidates[positive]
    prominences = properties["prominences"][positive]

    # Enforce separation using actual times. Stronger derivative events win when
    # two otherwise valid local maxima are too close.
    order = np.lexsort((-prominences, -derivative[candidates]))
    accepted = []
    for candidate in candidates[order]:
        if all(abs(t[candidate] - t[other]) >= min_distance_s for other in accepted):
            accepted.append(int(candidate))
    landmarks = np.asarray(sorted(accepted), dtype=np.int64)
    pre_relative_landmarks = landmarks.copy()
    resolved_relative_height = np.nan
    if landmarks.size:
        resolved_relative_height = relative_height * float(
            np.max(derivative[landmarks])
        )
        landmarks = landmarks[
            derivative[landmarks] > resolved_relative_height
        ]
    rejected_by_relative_height = np.setdiff1d(
        pre_relative_landmarks, landmarks, assume_unique=True
    )
    diagnostics = {
        "positive_candidate_count": int(candidates.size),
        "pre_relative_landmark_indices": pre_relative_landmarks,
        "relative_height_rejected_indices": rejected_by_relative_height,
    }
    result = (
        landmarks,
        float(resolved_prominence),
        resolved_relative_height,
    )
    if return_diagnostics:
        return (*result, diagnostics)
    return result


def cardiac_failure_message(
    detection,
    landmark_diagnostics,
    landmarks,
    beats,
    t,
    f,
    parameters,
):
    """Explain why landmark detection and beat-duration QC produced no beats."""
    t = np.asarray(t, dtype=np.float64)
    f = np.asarray(f, dtype=np.float64)
    landmarks = np.asarray(landmarks, dtype=np.int64)
    derivative = np.asarray(detection["dg_dt"], dtype=np.float64)
    preliminary = np.asarray(
        landmark_diagnostics["pre_relative_landmark_indices"], dtype=np.int64
    )
    rejected = np.asarray(
        landmark_diagnostics["relative_height_rejected_indices"], dtype=np.int64
    )
    periods = np.asarray(beats["beat_periods"], dtype=np.float64)
    accepted = np.asarray(beats["beat_accepted"], dtype=bool)
    recording_span = float(t[-1] - t[0])
    min_duration = float(parameters["spectral_endpoints_min_beat_duration_s"])
    max_duration = float(parameters["spectral_endpoints_max_beat_duration_s"])
    relative_fraction = float(
        parameters.get("spectral_endpoints_peak_relative_height", 0.3)
    )
    relative_threshold = (
        relative_fraction * float(np.max(derivative[preliminary]))
        if preliminary.size
        else np.nan
    )
    configured_fc = float(parameters["spectral_endpoints_cardiac_fc_hz"])
    effective_fc = float(
        parameters.get(
            "spectral_endpoints_cardiac_fc_effective_hz", configured_fc
        )
    )
    selected_bin_count = int(np.count_nonzero(detection["high_frequency_mask"]))
    explained = float(detection["svd_explained_variance_fraction"])

    def values_text(values):
        values = np.asarray(values)
        if values.size == 0:
            return "none"
        return np.array2string(values, precision=4, separator=", ")

    lines = [
        "No valid cardiac beats remain after landmark detection and duration QC.",
        "Measured cardiac-segmentation diagnostics:",
        f"- Recording: {recording_span:.4g} s across {t.size} long-time samples.",
        (
            "- High-frequency selection: "
            f"configured fc={configured_fc:g} Hz, effective fc={effective_fc:g} "
            f"Hz, selected bins={selected_bin_count}/{f.size}, leading-SVD "
            f"explained variance={explained:.2%}."
        ),
        (
            "- Derivative maxima after prominence and spacing: "
            f"{preliminary.size}; heights={values_text(derivative[preliminary])}."
        ),
        (
            f"- Relative-height QC: require > {relative_fraction:.0%} of the "
            f"strongest maximum (absolute threshold={relative_threshold:.6g}); "
            f"rejected={rejected.size}, surviving={landmarks.size}; "
            f"surviving heights={values_text(derivative[landmarks])}."
        ),
        (
            f"- Surviving landmark periods: {values_text(periods)} s; required "
            f"range=[{min_duration:g}, {max_duration:g}] s; "
            f"accepted={int(np.count_nonzero(accepted))}/{periods.size}."
        ),
        "Common-cause assessment:",
    ]
    if rejected.size:
        lines.append(
            "- A dominant motion-artifact dg/dt maximum may have caused genuine "
            "cardiac maxima to fall below the relative-height threshold."
        )
    else:
        lines.append(
            "- A dominant motion artifact was not demonstrated by relative-height "
            "rejection, but may still distort the derivative waveform."
        )
    if landmarks.size < 2:
        lines.append(
            f"- Fewer than two maxima survived ({landmarks.size}); no landmark "
            "interval can be formed."
        )
    else:
        lines.append(f"- {landmarks.size} maxima survived, enough to form intervals.")
    if periods.size and not np.any(accepted):
        lines.append(
            f"- Every surviving interval is outside [{min_duration:g}, "
            f"{max_duration:g}] s."
        )
    elif periods.size == 0:
        lines.append("- Beat-duration QC cannot run because no interval was formed.")
    if recording_span < min_duration:
        lines.append(
            "- The recording is shorter than the minimum permitted beat period, "
            "so it cannot contain two valid cardiac landmarks."
        )
    elif landmarks.size < 2:
        lines.append(
            "- The recording may contain too few observable cardiac cycles even "
            "though its total duration exceeds the minimum beat period."
        )
    lines.append(
        "- Insufficient cardiac signal in the configured high-frequency range may "
        "make the leading SVD mode noisy or unrelated to cardiac modulation; use "
        "the selected-bin count and explained variance above with the QC waveform "
        "to assess this possibility."
    )
    return "\n".join(lines)


def resample_beats(
    signal: np.ndarray,
    background: np.ndarray,
    t: np.ndarray,
    landmarks: np.ndarray,
    *,
    phase_bins: int,
    min_duration_s: float,
    max_duration_s: float,
):
    """Linearly resample valid landmark-to-landmark beats onto [0,1)."""
    signal = np.asarray(signal, dtype=np.float32)
    background = np.asarray(background, dtype=np.float32)
    t = np.asarray(t, dtype=np.float64)
    landmarks = np.asarray(landmarks, dtype=np.int64)
    phase_bins = int(phase_bins)
    min_duration_s = float(min_duration_s)
    max_duration_s = float(max_duration_s)
    if signal.shape != background.shape or signal.shape[0] != t.size:
        raise ValueError("S, S0, and t must have compatible shapes")
    if phase_bins < 2:
        raise ValueError("spectral_endpoints_phase_bins must be at least 2")
    if (
        not np.isfinite(min_duration_s)
        or not np.isfinite(max_duration_s)
        or min_duration_s <= 0
        or max_duration_s <= min_duration_s
    ):
        raise ValueError("Beat-duration bounds must satisfy 0 < min < max")
    if landmarks.size and (
        np.any(landmarks < 0)
        or np.any(landmarks >= t.size)
        or np.any(np.diff(landmarks) <= 0)
    ):
        raise ValueError("landmarks must be strictly increasing valid indices")

    phase = np.arange(phase_bins, dtype=np.float64) / phase_bins
    periods = np.diff(t[landmarks]) if landmarks.size >= 2 else np.empty(0)
    accepted = (periods >= min_duration_s) & (periods <= max_duration_s)
    accepted_indices = np.flatnonzero(accepted).astype(np.int64)
    rejected_indices = np.flatnonzero(~accepted).astype(np.int64)
    signal_beats = []
    background_beats = []
    for beat_index in accepted_indices:
        start = int(landmarks[beat_index])
        stop = int(landmarks[beat_index + 1])
        source_phase = (t[start : stop + 1] - t[start]) / (t[stop] - t[start])
        signal_segment = signal[start : stop + 1]
        background_segment = background[start : stop + 1]
        signal_beats.append(
            np.stack(
                [
                    np.interp(phase, source_phase, signal_segment[:, index])
                    for index in range(signal.shape[1])
                ],
                axis=1,
            ).astype(np.float32)
        )
        background_beats.append(
            np.stack(
                [
                    np.interp(phase, source_phase, background_segment[:, index])
                    for index in range(background.shape[1])
                ],
                axis=1,
            ).astype(np.float32)
        )

    empty_shape = (0, phase_bins, signal.shape[1])
    signal_beats = (
        np.stack(signal_beats) if signal_beats else np.empty(empty_shape, np.float32)
    )
    background_beats = (
        np.stack(background_beats)
        if background_beats
        else np.empty(empty_shape, np.float32)
    )
    return {
        "phase": phase,
        "S_beats": signal_beats,
        "S0_beats": background_beats,
        "beat_periods": periods.astype(np.float64),
        "beat_accepted": accepted,
        "accepted_beat_indices": accepted_indices,
        "rejected_beat_indices": rejected_indices,
    }


def detect_streaks(
    signal_beats: np.ndarray,
    *,
    prominence_mad: float,
    threshold_mad: float,
    min_width: float,
    padding_phase_bins: int = 0,
):
    """Detect beat-specific sharp positive broadband peaks over cardiac phase."""
    signal_beats = np.asarray(signal_beats, dtype=np.float32)
    if signal_beats.ndim != 3:
        raise ValueError("S_beats must have shape (beat,phase,frequency)")
    prominence_mad = float(prominence_mad)
    threshold_mad = float(threshold_mad)
    min_width = float(min_width)
    padding_phase_bins = int(padding_phase_bins)
    if prominence_mad < 0 or threshold_mad < 0 or min_width <= 0:
        raise ValueError(
            "Streak prominence/threshold must be non-negative and width positive"
        )
    if padding_phase_bins < 0:
        raise ValueError("Streak padding must be non-negative")

    traces = np.mean(signal_beats, axis=2, dtype=np.float64)
    mask = np.zeros(traces.shape, dtype=bool)
    peak_counts = np.zeros(traces.shape[0], dtype=np.int64)
    for beat_index, trace in enumerate(traces):
        center = float(np.median(trace))
        scale = _robust_mad_scale(trace)
        threshold = center + threshold_mad * scale
        peaks, _properties = find_peaks(
            trace,
            height=threshold,
            prominence=prominence_mad * scale,
            width=min_width,
        )
        peak_counts[beat_index] = len(peaks)
        for peak in peaks:
            left = int(peak)
            right = int(peak)
            while left > 0 and trace[left - 1] >= threshold:
                left -= 1
            while right + 1 < trace.size and trace[right + 1] >= threshold:
                right += 1
            left = max(0, left - padding_phase_bins)
            right = min(trace.size - 1, right + padding_phase_bins)
            mask[beat_index, left : right + 1] = True
    return traces.astype(np.float32), mask, peak_counts


def repair_streaks(
    signal_beats: np.ndarray,
    streak_mask: np.ndarray,
    *,
    min_clean_beats: int,
):
    """Repair only S from clean beats at the same phase; leave failures unchanged."""
    signal_beats = np.asarray(signal_beats, dtype=np.float32)
    streak_mask = np.asarray(streak_mask, dtype=bool)
    min_clean_beats = int(min_clean_beats)
    if signal_beats.ndim != 3 or streak_mask.shape != signal_beats.shape[:2]:
        raise ValueError("streak_mask must match the beat and phase axes of S_beats")
    if min_clean_beats < 1:
        raise ValueError("spectral_endpoints_min_clean_beats must be positive")

    repaired = signal_beats.copy()
    insufficient = np.zeros(streak_mask.shape, dtype=bool)
    for phase_index in range(signal_beats.shape[1]):
        dirty = np.flatnonzero(streak_mask[:, phase_index])
        if dirty.size == 0:
            continue
        clean = np.flatnonzero(~streak_mask[:, phase_index])
        if clean.size < min_clean_beats:
            insufficient[dirty, phase_index] = True
            continue
        replacement = np.mean(
            signal_beats[clean, phase_index, :],
            axis=0,
            dtype=np.float64,
        ).astype(np.float32)
        repaired[dirty, phase_index, :] = replacement
    return repaired, insufficient


def aggregate_single_beat(repaired_signal_beats, background_beats):
    """Median aggregate S and untouched S0, then compute log of their ratio."""
    repaired_signal_beats = np.asarray(repaired_signal_beats, dtype=np.float32)
    background_beats = np.asarray(background_beats, dtype=np.float32)
    if (
        repaired_signal_beats.ndim != 3
        or repaired_signal_beats.shape != background_beats.shape
        or repaired_signal_beats.shape[0] == 0
    ):
        raise ValueError("S_beats and S0_beats must be matching non-empty 3D arrays")
    signal = np.median(repaired_signal_beats, axis=0).astype(np.float32)
    background = np.median(background_beats, axis=0).astype(np.float32)
    log_ratio = log_power_ratio(np, signal, background)
    return signal, background, log_ratio


def cardiac_phase_analysis(signal, background, t, f, parameters):
    """Run segmentation, phase normalization, S-only repair, and aggregation."""
    detection = cardiac_detection_signal(
        signal,
        t,
        f,
        parameters.get(
            "spectral_endpoints_cardiac_fc_effective_hz",
            parameters["spectral_endpoints_cardiac_fc_hz"],
        ),
        median_window_s=parameters.get(
            "spectral_endpoints_cardiac_median_window_s", 0.035
        ),
        smoothing_s=parameters["spectral_endpoints_cardiac_smoothing_s"],
    )
    (
        landmarks,
        resolved_prominence,
        resolved_relative_height,
        landmark_diagnostics,
    ) = detect_cardiac_landmarks(
        detection["dg_dt"],
        t,
        min_distance_s=parameters["spectral_endpoints_peak_min_distance_s"],
        prominence_mad=parameters["spectral_endpoints_peak_prominence_mad"],
        relative_height=parameters.get(
            "spectral_endpoints_peak_relative_height", 0.3
        ),
        return_diagnostics=True,
    )
    beats = resample_beats(
        signal,
        background,
        t,
        landmarks,
        phase_bins=parameters["spectral_endpoints_phase_bins"],
        min_duration_s=parameters["spectral_endpoints_min_beat_duration_s"],
        max_duration_s=parameters["spectral_endpoints_max_beat_duration_s"],
    )
    if beats["S_beats"].shape[0] == 0:
        return {
            **beats,
            **detection,
            "beat_landmark_indices": landmarks,
            "beat_landmark_times": np.asarray(t, dtype=np.float64)[landmarks],
            "resolved_peak_prominence": resolved_prominence,
            "resolved_peak_relative_height": resolved_relative_height,
            "cardiac_fc_hz": parameters.get(
                "spectral_endpoints_cardiac_fc_effective_hz",
                parameters["spectral_endpoints_cardiac_fc_hz"],
            ),
            "pulse_detected": False,
            "pulse_detection_error": cardiac_failure_message(
                detection,
                landmark_diagnostics,
                landmarks,
                beats,
                t,
                f,
                parameters,
            ),
        }
    streak_trace, streak_mask, streak_peak_count = detect_streaks(
        beats["S_beats"],
        prominence_mad=parameters["spectral_endpoints_streak_prominence"],
        threshold_mad=parameters["spectral_endpoints_streak_threshold"],
        min_width=parameters["spectral_endpoints_streak_min_width"],
        padding_phase_bins=parameters["spectral_endpoints_streak_padding_phase_bins"],
    )
    repaired_signal, insufficient = repair_streaks(
        beats["S_beats"],
        streak_mask,
        min_clean_beats=parameters["spectral_endpoints_min_clean_beats"],
    )
    single_signal, single_background, single_log_ratio = aggregate_single_beat(
        repaired_signal,
        beats["S0_beats"],
    )
    return {
        **beats,
        **detection,
        "beat_landmark_indices": landmarks,
        "beat_landmark_times": np.asarray(t, dtype=np.float64)[landmarks],
        "resolved_peak_prominence": resolved_prominence,
        "resolved_peak_relative_height": resolved_relative_height,
        "cardiac_fc_hz": parameters.get(
            "spectral_endpoints_cardiac_fc_effective_hz",
            parameters["spectral_endpoints_cardiac_fc_hz"],
        ),
        "streak_trace": streak_trace,
        "streak_mask": streak_mask,
        "streak_peak_count": streak_peak_count,
        "streak_unrepaired_mask": insufficient,
        "repaired_S_beats": repaired_signal,
        "S": single_signal,
        "S0": single_background,
        "L": single_log_ratio,
        "pulse_detected": True,
        "pulse_detection_error": "",
    }
