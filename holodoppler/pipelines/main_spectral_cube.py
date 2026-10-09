"""Stream a registered, reduced-resolution Doppler spectrum to HDF5."""

from __future__ import annotations

import json
from pathlib import Path
import time

import cupy as cp
import h5py
import imageio as iio
import numpy as np
from tqdm import tqdm

from holodoppler.file_reader import FileReaderFactory
from holodoppler.filtering import (
    corner_compensation,
    filter_2d,
    fourier_time_transform,
    svd_filter,
)
from holodoppler.propagation import (
    angular_spectrum_transform,
    angular_spectrum_transform_with_phase,
    fresnel_transform,
    fresnel_transform_with_phase,
)
from holodoppler.saving import (
    H5_OUTPUT_PATH_PARAMETER,
    _create_directories,
    _get_default_output_path,
    _get_h5_output_path,
    _save_metadata,
    apply_contrast_adjustment,
    normalize_to_uint8,
    save_preview_images,
)
from holodoppler.spectral_cube import (
    CARDIAC_PULSE_NOT_DETECTED,
    binned_fft_frequencies,
    cardiac_phase_analysis,
    centered_ellipse_mask,
    ellipse_median_power,
    estimated_endpoint_bytes,
    log_power_ratio,
    mean_bin_axis,
    resolve_cardiac_fc,
    window_starts,
)
from holodoppler.utils import update_from_footer


_SPECTRAL_CUBE_SHARED_PARAMETER_NAMES = {
    "batch_size",
    "first_frame",
    "batch_stride",
    "end_frame",
    "spatial_propagation",
    "z",
    "wavelength",
    "pixel_pitch",
    "Fresnel_use_ouput_kernel",
    "filter2d",
    "filter2d_low",
    "sampling_freq",
    "f_bins",
    "corner_compensation",
    "contrast",
    "contrast_low_max_percent",
    "contrast_gamma",
}
_SPECTRAL_CUBE_METADATA_EXCLUSIONS = {
    "spectral_cube_enabled",
    "spectral_cube_settings",
    "spectral_cube_filename",
    "spectral_endpoints_filename",
}


def _spectral_cube_parameters_for_h5(parameters):
    """Return only settings used to compute or render the spectral products."""
    return {
        name: value
        for name, value in parameters.items()
        if name not in _SPECTRAL_CUBE_METADATA_EXCLUSIONS
        and (
            name in _SPECTRAL_CUBE_SHARED_PARAMETER_NAMES
            or name.startswith("spectral_cube_")
            or name.startswith("spectral_endpoints_")
            or name.startswith("shack_hartmann")
        )
    }


def _propagate(parameters, frames, phase_term=None):
    propagation = parameters["spatial_propagation"]
    common = (
        cp,
        cp.fft,
        frames,
        parameters["z"],
        parameters["pixel_pitch"],
        parameters["wavelength"],
    )

    if propagation == "Fresnel":
        if phase_term is None:
            return fresnel_transform(
                *common,
                use_output_kernel=parameters.get("Fresnel_use_ouput_kernel", False),
            )
        return fresnel_transform_with_phase(
            *common,
            phase_term,
            use_output_kernel=parameters.get("Fresnel_use_ouput_kernel", False),
        )

    if propagation == "AngularSpectrum":
        if phase_term is None:
            return angular_spectrum_transform(*common)
        return angular_spectrum_transform_with_phase(*common, phase_term)

    raise ValueError(
        "spatial_propagation must be 'Fresnel' or 'AngularSpectrum', "
        f"got {propagation!r}"
    )


def _process_spectral_window(parameters, frames, phase_term=None):
    """Return frequency-binned, non-registered PSD planes."""
    holograms = _propagate(parameters, frames, phase_term=phase_term)
    del frames

    holograms = svd_filter(
        cp,
        holograms,
        2,
        filter_mode="number_of_values",
        remove_dc=False,
    )

    spectrum = fourier_time_transform(cp, cp.fft, holograms)
    del holograms
    psd = cp.square(cp.abs(spectrum)).astype(cp.float32, copy=False)
    del spectrum

    if parameters.get("corner_compensation", False):
        psd = corner_compensation(cp, psd).astype(cp.float32, copy=False)

    psd = cp.fft.fftshift(psd, axes=0)
    psd = mean_bin_axis(cp, psd, parameters["f_bins"], axis=0)
    return psd.astype(cp.float32, copy=False)


def _phase_term(parameters, frames):
    if not parameters.get("shack_hartmann", False):
        return None

    # Reuse the correction path from the simple pipeline without duplicating it.
    from holodoppler.pipelines.main_simple import _process_shack_hartmann

    return _process_shack_hartmann(parameters, frames)


def _endpoint_spectra_window(parameters, frames):
    phase_term = _phase_term(parameters, frames)
    psd = _process_spectral_window(
        parameters,
        frames,
        phase_term=phase_term,
    )
    del phase_term

    background_power = ellipse_median_power(
        cp,
        psd,
        radius_y_factor=parameters.get(
            "spectral_cube_corner_ellipse_radius_y_factor", 1.2
        ),
        radius_x_factor=parameters.get(
            "spectral_cube_corner_ellipse_radius_x_factor", 1.2
        ),
        outside=True,
    ).astype(cp.float32, copy=False)

    signal_power = ellipse_median_power(
        cp,
        psd,
        radius_y_factor=parameters.get(
            "spectral_cube_signal_ellipse_radius_y_factor", 0.8
        ),
        radius_x_factor=parameters.get(
            "spectral_cube_signal_ellipse_radius_x_factor", 0.8
        ),
        outside=False,
    ).astype(cp.float32, copy=False)
    return signal_power, background_power


def _total_frames(file_reader) -> int:
    if file_reader.ext == ".holo":
        return int(file_reader.file_header.num_frames)
    return int(file_reader.TotalImageCount)


def _prepare(file_path, parameters):
    file_reader = FileReaderFactory.create(file_path)
    parameters = dict(parameters)
    if file_reader.ext == ".holo":
        parameters = update_from_footer(parameters, file_reader.file_footer)

    total_frames = _total_frames(file_reader)
    first_frame = int(parameters.get("first_frame", 0))
    requested_end = int(parameters.get("end_frame", -1))
    end_frame = total_frames if requested_end <= 0 else min(requested_end, total_frames)
    batch_size = int(parameters["batch_size"])
    batch_stride = int(parameters["batch_stride"])
    starts = window_starts(first_frame, end_frame, batch_size, batch_stride)
    if starts.size == 0:
        raise ValueError(
            "The selected frame range does not contain one complete temporal window"
        )

    try:
        sampling_frequency = float(parameters["sampling_freq"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "sampling_freq must resolve to a numeric value; set it explicitly "
            "for inputs without HoloVibes metadata"
        ) from exc
    f_bins = int(parameters.get("f_bins", 128))
    cardiac_parameters = {
        "spectral_endpoints_cardiac_fc_hz": float(
            parameters.get("spectral_endpoints_cardiac_fc_hz", 15000.0)
        ),
        "spectral_endpoints_cardiac_median_window_s": float(
            parameters.get("spectral_endpoints_cardiac_median_window_s", 0.035)
        ),
        "spectral_endpoints_cardiac_smoothing_s": float(
            parameters.get("spectral_endpoints_cardiac_smoothing_s", 0.0)
        ),
        "spectral_endpoints_peak_min_distance_s": float(
            parameters.get("spectral_endpoints_peak_min_distance_s", 0.3)
        ),
        "spectral_endpoints_peak_prominence_mad": float(
            parameters.get("spectral_endpoints_peak_prominence_mad", 1.0)
        ),
        "spectral_endpoints_peak_relative_height": float(
            parameters.get("spectral_endpoints_peak_relative_height", 0.5)
        ),
        "spectral_endpoints_min_beat_duration_s": float(
            parameters.get("spectral_endpoints_min_beat_duration_s", 0.35)
        ),
        "spectral_endpoints_max_beat_duration_s": float(
            parameters.get("spectral_endpoints_max_beat_duration_s", 1.5)
        ),
        "spectral_endpoints_phase_bins": int(
            parameters.get("spectral_endpoints_phase_bins", 128)
        ),
        "spectral_endpoints_streak_prominence": float(
            parameters.get("spectral_endpoints_streak_prominence", 6.0)
        ),
        "spectral_endpoints_streak_threshold": float(
            parameters.get("spectral_endpoints_streak_threshold", 6.0)
        ),
        "spectral_endpoints_streak_min_width": float(
            parameters.get("spectral_endpoints_streak_min_width", 1.0)
        ),
        "spectral_endpoints_streak_padding_phase_bins": int(
            parameters.get("spectral_endpoints_streak_padding_phase_bins", 0)
        ),
        "spectral_endpoints_min_clean_beats": int(
            parameters.get("spectral_endpoints_min_clean_beats", 2)
        ),
    }
    cardiac_parameters["spectral_endpoints_cardiac_fc_effective_hz"] = (
        resolve_cardiac_fc(
            cardiac_parameters["spectral_endpoints_cardiac_fc_hz"],
            sampling_frequency,
        )
    )
    if not np.isfinite(sampling_frequency) or sampling_frequency <= 0:
        raise ValueError("sampling_freq must be a positive finite number")
    if f_bins <= 0:
        raise ValueError("f_bins must be a positive integer")
    if cardiac_parameters["spectral_endpoints_cardiac_fc_hz"] < 0:
        raise ValueError("spectral_endpoints_cardiac_fc_hz must be non-negative")
    if (
        not np.isfinite(
            cardiac_parameters["spectral_endpoints_cardiac_median_window_s"]
        )
        or cardiac_parameters["spectral_endpoints_cardiac_median_window_s"] < 0
    ):
        raise ValueError(
            "spectral_endpoints_cardiac_median_window_s must be non-negative"
        )
    if cardiac_parameters["spectral_endpoints_cardiac_smoothing_s"] < 0:
        raise ValueError("spectral_endpoints_cardiac_smoothing_s must be non-negative")
    if cardiac_parameters["spectral_endpoints_peak_min_distance_s"] <= 0:
        raise ValueError("spectral_endpoints_peak_min_distance_s must be positive")
    if cardiac_parameters["spectral_endpoints_peak_prominence_mad"] < 0:
        raise ValueError("spectral_endpoints_peak_prominence_mad must be non-negative")
    relative_height = cardiac_parameters["spectral_endpoints_peak_relative_height"]
    if not np.isfinite(relative_height) or not 0 <= relative_height <= 1:
        raise ValueError(
            "spectral_endpoints_peak_relative_height must be between 0 and 1"
        )
    min_beat = cardiac_parameters["spectral_endpoints_min_beat_duration_s"]
    max_beat = cardiac_parameters["spectral_endpoints_max_beat_duration_s"]
    if min_beat <= 0 or max_beat <= min_beat:
        raise ValueError("Cardiac beat-duration bounds must satisfy 0 < min < max")
    if cardiac_parameters["spectral_endpoints_phase_bins"] < 2:
        raise ValueError("spectral_endpoints_phase_bins must be at least 2")
    if cardiac_parameters["spectral_endpoints_streak_prominence"] < 0:
        raise ValueError("spectral_endpoints_streak_prominence must be non-negative")
    if cardiac_parameters["spectral_endpoints_streak_threshold"] < 0:
        raise ValueError("spectral_endpoints_streak_threshold must be non-negative")
    if cardiac_parameters["spectral_endpoints_streak_min_width"] <= 0:
        raise ValueError("spectral_endpoints_streak_min_width must be positive")
    if cardiac_parameters["spectral_endpoints_streak_padding_phase_bins"] < 0:
        raise ValueError(
            "spectral_endpoints_streak_padding_phase_bins must be non-negative"
        )
    if cardiac_parameters["spectral_endpoints_min_clean_beats"] < 1:
        raise ValueError("spectral_endpoints_min_clean_beats must be positive")
    parameters.update(
        {
            "batch_size": batch_size,
            "batch_stride": batch_stride,
            "first_frame": first_frame,
            "end_frame": end_frame,
            "sampling_freq": sampling_frequency,
            "f_bins": f_bins,
            **cardiac_parameters,
        }
    )

    if f_bins > batch_size:
        raise ValueError(
            f"f_bins ({f_bins}) cannot exceed batch_size ({batch_size})"
        )

    return file_reader, parameters, starts


def _output_path(file_reader, parameters) -> tuple[Path, Path]:
    primary_h5_path = parameters.get(H5_OUTPUT_PATH_PARAMETER)
    if primary_h5_path:
        h5_path = Path(primary_h5_path)
        target_dir = (
            h5_path.parent.parent
            if h5_path.parent.name.lower() == "h5"
            else h5_path.parent
        )
        _create_directories(target_dir, "FULL")
        return target_dir, h5_path

    target_dir = _get_default_output_path(file_reader.file_path)
    if parameters.get("saving_to_folder"):
        target_dir = Path(parameters["saving_to_folder"])
    _create_directories(target_dir, "FULL")
    return target_dir, _get_h5_output_path(target_dir)


def _create_h5(path, file_reader, parameters, starts):
    ny, nx = file_reader.frame_shape
    f = binned_fft_frequencies(
        parameters["sampling_freq"], parameters["batch_size"], parameters["f_bins"]
    )
    t = (
        starts.astype(np.float64) + (parameters["batch_size"] - 1) / 2.0
    ) / parameters["sampling_freq"]

    handle = h5py.File(path, "a")
    if "spectrograms" in handle:
        del handle["spectrograms"]
    spectrograms = handle.create_group("spectrograms", track_order=True)
    spectrograms.attrs["complete"] = False
    spectrograms.attrs["source_file"] = str(file_reader.file_path)
    spectrograms.attrs["axis_order"] = "longtimes:(t,f); singlebeat:(phase,f)"
    longtimes = spectrograms.create_group("longtimes", track_order=True)

    signal = longtimes.create_dataset(
        "S",
        shape=(len(starts), len(f)),
        dtype=np.float32,
        chunks=None,
        compression=None,
        track_times=False,
    )
    signal.attrs["axis_order"] = "t,f"
    signal.attrs["description"] = (
        "Spatial median of the non-registered PSD inside a centered ellipse"
    )
    signal.attrs["dtype"] = "float32"
    signal.attrs["units"] = "power (arbitrary units)"
    signal.attrs["spatial_registration"] = False
    signal.attrs["svd_filter"] = True
    signal.attrs["svd_removed_components"] = 2
    signal.attrs["svd_remove_dc"] = False
    signal.attrs["spatial_aggregation"] = "median"
    signal.attrs["corner_compensation"] = bool(
        parameters.get("corner_compensation", False)
    )
    signal.attrs["temporal_window"] = "rectangular"
    signal.attrs["frequency_binning"] = "contiguous mean"
    signal_radius_y_factor = float(
        parameters.get("spectral_cube_signal_ellipse_radius_y_factor", 0.8)
    )
    signal_radius_x_factor = float(
        parameters.get("spectral_cube_signal_ellipse_radius_x_factor", 0.8)
    )
    signal.attrs["ellipse_radius_y_factor"] = signal_radius_y_factor
    signal.attrs["ellipse_radius_x_factor"] = signal_radius_x_factor
    signal.attrs["ellipse_radius_y_pixels"] = signal_radius_y_factor * ny / 2.0
    signal.attrs["ellipse_radius_x_pixels"] = signal_radius_x_factor * nx / 2.0
    signal_mask = centered_ellipse_mask(
        np,
        ny,
        nx,
        signal_radius_y_factor,
        signal_radius_x_factor,
    )
    signal_pixel_count = int(np.count_nonzero(signal_mask))
    signal.attrs["pixel_count"] = signal_pixel_count
    signal.attrs["pixel_fraction"] = signal_pixel_count / (ny * nx)

    background = longtimes.create_dataset(
        "S0",
        shape=(len(starts), len(f)),
        dtype=np.float32,
        chunks=None,
        compression=None,
        track_times=False,
    )
    background.attrs["axis_order"] = "t,f"
    background.attrs["description"] = (
        "Spatial median of the non-registered PSD outside a centered ellipse"
    )
    background.attrs["dtype"] = "float32"
    background.attrs["units"] = "power (arbitrary units)"
    background.attrs["spatial_registration"] = False
    background.attrs["svd_filter"] = True
    background.attrs["svd_removed_components"] = 2
    background.attrs["svd_remove_dc"] = False
    background.attrs["spatial_aggregation"] = "median"
    background.attrs["corner_compensation"] = bool(
        parameters.get("corner_compensation", False)
    )
    background.attrs["temporal_window"] = "rectangular"
    background.attrs["frequency_binning"] = "contiguous mean"
    background_radius_y_factor = float(
        parameters.get("spectral_cube_corner_ellipse_radius_y_factor", 1.2)
    )
    background_radius_x_factor = float(
        parameters.get("spectral_cube_corner_ellipse_radius_x_factor", 1.2)
    )
    background.attrs["ellipse_radius_y_factor"] = background_radius_y_factor
    background.attrs["ellipse_radius_x_factor"] = background_radius_x_factor
    background.attrs["ellipse_radius_y_pixels"] = (
        background_radius_y_factor * ny / 2.0
    )
    background.attrs["ellipse_radius_x_pixels"] = (
        background_radius_x_factor * nx / 2.0
    )
    background_mask = ~centered_ellipse_mask(
        np,
        ny,
        nx,
        background_radius_y_factor,
        background_radius_x_factor,
    )
    if not np.any(background_mask):
        raise ValueError(
            "The background ellipse covers the complete frame; reduce one or "
            "both corner radius factors"
        )
    background_pixel_count = int(np.count_nonzero(background_mask))
    background.attrs["pixel_count"] = background_pixel_count
    background.attrs["pixel_fraction"] = background_pixel_count / (ny * nx)

    log_ratio = longtimes.create_dataset(
        "L",
        shape=(len(starts), len(f)),
        dtype=np.float32,
        chunks=None,
        compression=None,
        track_times=False,
    )
    log_ratio.attrs["axis_order"] = "t,f"
    log_ratio.attrs["description"] = "Natural logarithm of S/S0"
    log_ratio.attrs["formula"] = "ln(max(S,tiny_float32)/max(S0,tiny_float32))"
    log_ratio.attrs["dtype"] = "float32"
    log_ratio.attrs["units"] = "dimensionless"

    f_dataset = longtimes.create_dataset("f", data=f, track_times=False)
    f_dataset.attrs["units"] = "Hz"
    f_dataset.attrs["description"] = "Mean frequency of each full-range FFT bin"
    t_dataset = longtimes.create_dataset("t", data=t, track_times=False)
    t_dataset.attrs["units"] = "s"
    t_dataset.attrs["description"] = "Temporal-window center from acquisition start"
    frame_start_dataset = longtimes.create_dataset(
        "frame_start", data=starts, track_times=False
    )
    frame_start_dataset.attrs["units"] = "frame index"

    string_dtype = h5py.string_dtype(encoding="utf-8")
    spectrograms.create_dataset(
        "spectral_cube_parameters",
        data=json.dumps(_spectral_cube_parameters_for_h5(parameters), default=str),
        dtype=string_dtype,
        track_times=False,
    )
    return handle, spectrograms, signal, background, log_ratio


def _write_cardiac_h5(handle, analysis, parameters):
    """Write cardiac detection QC and representative single-beat products."""
    longtimes = handle["longtimes"]
    g_dataset = longtimes.create_dataset(
        "g", data=analysis["g"], track_times=False
    )
    g_dataset.attrs["description"] = (
        "Leading temporal SVD mode used for cardiac segmentation"
    )
    g_dataset.attrs["formula"] = (
        "sigma_1 * U[:,0] from temporally centered, median-filtered "
        "S[:,abs(f)>fc]"
    )
    g_dataset.attrs["temporal_mean_removed_per_frequency"] = True
    g_dataset.attrs["svd_mode_index"] = 0
    g_dataset.attrs["svd_sign_orientation"] = (
        "positive correlation with g_sum - mean(g_sum)"
    )
    g_dataset.attrs["svd_sign_multiplier"] = analysis["svd_sign"]
    g_dataset.attrs["explained_variance_fraction"] = analysis[
        "svd_explained_variance_fraction"
    ]
    g_dataset.attrs["fc_hz"] = parameters[
        "spectral_endpoints_cardiac_fc_effective_hz"
    ]
    g_dataset.attrs["configured_fc_hz"] = parameters[
        "spectral_endpoints_cardiac_fc_hz"
    ]
    g_dataset.attrs["nyquist_hz"] = parameters["sampling_freq"] / 2.0
    g_dataset.attrs["units"] = "power (arbitrary units)"
    sum_dataset = longtimes.create_dataset(
        "g_sum", data=analysis["g_sum"], track_times=False
    )
    sum_dataset.attrs["description"] = (
        "Unfiltered high-frequency fundus Doppler power sum"
    )
    sum_dataset.attrs["formula"] = "sum_{abs(f)>fc} S(t,f)"
    sum_dataset.attrs["fc_hz"] = parameters[
        "spectral_endpoints_cardiac_fc_effective_hz"
    ]
    sum_dataset.attrs["configured_fc_hz"] = parameters[
        "spectral_endpoints_cardiac_fc_hz"
    ]
    sum_dataset.attrs["nyquist_hz"] = parameters["sampling_freq"] / 2.0
    sum_dataset.attrs["units"] = "power (arbitrary units)"
    median_sum_dataset = longtimes.create_dataset(
        "g_sum_median_filtered",
        data=analysis["g_sum_median_filtered"],
        track_times=False,
    )
    median_sum_dataset.attrs["description"] = (
        "Sum of high-frequency S after per-frequency temporal median filtering"
    )
    median_sum_dataset.attrs["formula"] = (
        "sum_f median_filter_time(S[:,abs(f)>fc])"
    )
    median_sum_dataset.attrs["requested_window_s"] = parameters[
        "spectral_endpoints_cardiac_median_window_s"
    ]
    median_sum_dataset.attrs["resolved_window_samples"] = analysis[
        "median_window_samples"
    ]
    median_sum_dataset.attrs["resolved_window_s"] = analysis[
        "median_window_resolved_s"
    ]
    smoothed_dataset = longtimes.create_dataset(
        "g_smoothed", data=analysis["g_smoothed"], track_times=False
    )
    smoothed_dataset.attrs["description"] = (
        "Leading temporal SVD mode after optional Gaussian smoothing, used for "
        "differentiation"
    )
    smoothed_dataset.attrs["source"] = "g"
    smoothed_dataset.attrs["smoothing_s"] = parameters[
        "spectral_endpoints_cardiac_smoothing_s"
    ]
    derivative_dataset = longtimes.create_dataset(
        "dg_dt", data=analysis["dg_dt"], track_times=False
    )
    derivative_dataset.attrs["description"] = (
        "Time derivative of the high-frequency cardiac signal g(t)"
    )
    derivative_dataset.attrs["formula"] = "d/dt (sigma_1 * U[:,0])"
    derivative_dataset.attrs["source"] = "g_smoothed"
    derivative_dataset.attrs["smoothing_s"] = parameters[
        "spectral_endpoints_cardiac_smoothing_s"
    ]
    derivative_dataset.attrs["units"] = "power (arbitrary units)/s"
    mask_dataset = longtimes.create_dataset(
        "cardiac_frequency_mask",
        data=analysis["high_frequency_mask"],
        track_times=False,
    )
    mask_dataset.attrs["description"] = "Frequency bins satisfying abs(f) > fc"
    singular_values_dataset = longtimes.create_dataset(
        "cardiac_singular_values",
        data=analysis["cardiac_singular_values"],
        track_times=False,
    )
    singular_values_dataset.attrs["description"] = (
        "Singular values of centered, median-filtered high-frequency S"
    )
    frequency_mode_dataset = longtimes.create_dataset(
        "cardiac_frequency_mode",
        data=analysis["cardiac_frequency_mode"],
        track_times=False,
    )
    frequency_mode_dataset.attrs["description"] = (
        "Leading SVD frequency mode, zero outside the cardiac frequency mask"
    )
    frequency_mode_dataset.attrs["axis"] = "longtimes/f"

    pulse_detected = bool(analysis.get("pulse_detected", True))
    singlebeat = handle.create_group("singlebeat", track_order=True)
    phase = singlebeat.create_dataset(
        "phase", data=analysis["phase"], track_times=False
    )
    singlebeat["f"] = longtimes["f"]
    phase.attrs["units"] = "normalized cardiac phase"
    phase.attrs["range"] = "[0,1)"

    beat_qc_datasets = {
        "beat_landmark_indices": analysis["beat_landmark_indices"],
        "beat_landmark_times": analysis["beat_landmark_times"],
        "beat_periods": analysis["beat_periods"],
        "beat_accepted": analysis["beat_accepted"],
        "accepted_beat_indices": analysis["accepted_beat_indices"],
        "rejected_beat_indices": analysis["rejected_beat_indices"],
    }
    for name, values in beat_qc_datasets.items():
        singlebeat.create_dataset(name, data=values, track_times=False)

    singlebeat.attrs["pulse_detected"] = pulse_detected
    singlebeat.attrs["representative_beat_available"] = pulse_detected
    singlebeat.attrs["detected_landmark_count"] = len(
        analysis["beat_landmark_indices"]
    )
    singlebeat.attrs["detected_beat_count"] = len(analysis["beat_periods"])
    singlebeat.attrs["accepted_beat_count"] = len(
        analysis["accepted_beat_indices"]
    )
    singlebeat.attrs["rejected_beat_count"] = len(
        analysis["rejected_beat_indices"]
    )
    singlebeat.attrs["resolved_peak_prominence"] = analysis[
        "resolved_peak_prominence"
    ]
    singlebeat.attrs["resolved_peak_relative_height"] = analysis[
        "resolved_peak_relative_height"
    ]
    for name, value in parameters.items():
        if name.startswith("spectral_endpoints_"):
            singlebeat.attrs[name] = value

    if not pulse_detected:
        singlebeat.attrs["pulse_detection_error"] = analysis[
            "pulse_detection_error"
        ]
        return

    signal = singlebeat.create_dataset(
        "S", data=analysis["S"], dtype=np.float32, compression=None, track_times=False
    )
    background = singlebeat.create_dataset(
        "S0",
        data=analysis["S0"],
        dtype=np.float32,
        compression=None,
        track_times=False,
    )
    log_ratio = singlebeat.create_dataset(
        "L", data=analysis["L"], dtype=np.float32, compression=None, track_times=False
    )
    signal.attrs["axis_order"] = "phase,f"
    signal.attrs["description"] = (
        "Median across phase-normalized fundus beats after S-only streak repair"
    )
    signal.attrs["streak_repair"] = True
    background.attrs["axis_order"] = "phase,f"
    background.attrs["description"] = (
        "Median across independently phase-normalized, unrepaired corner beats"
    )
    background.attrs["streak_repair"] = False
    log_ratio.attrs["axis_order"] = "phase,f"
    log_ratio.attrs["description"] = "Natural logarithm of aggregate S/S0"
    log_ratio.attrs["formula"] = "ln(median(repaired_S_beats)/median(S0_beats))"
    log_ratio.attrs["units"] = "dimensionless"

    streak_qc_datasets = {
        "streak_trace": analysis["streak_trace"],
        "streak_mask": analysis["streak_mask"],
        "streak_peak_count": analysis["streak_peak_count"],
        "streak_unrepaired_mask": analysis["streak_unrepaired_mask"],
    }
    for name, values in streak_qc_datasets.items():
        singlebeat.create_dataset(name, data=values, track_times=False)

    repaired_mask = analysis["streak_mask"] & ~analysis["streak_unrepaired_mask"]
    sample_count = int(analysis["streak_mask"].size)
    singlebeat.attrs["repaired_phase_sample_count"] = int(
        np.count_nonzero(repaired_mask)
    )
    singlebeat.attrs["repaired_phase_sample_fraction"] = (
        float(np.count_nonzero(repaired_mask)) / sample_count if sample_count else 0.0
    )
    singlebeat.attrs["unrepaired_phase_sample_count"] = int(
        np.count_nonzero(analysis["streak_unrepaired_mask"])
    )


def _save_cardiac_qc_plots(h5_path, png_dir):
    """Save time-domain landmark QC and one beat-specific streak trace."""
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    with h5py.File(h5_path, "r") as handle:
        root = handle["spectrograms"] if "spectrograms" in handle else handle
        longtimes = root["longtimes"]
        singlebeat = root["singlebeat"]
        t = np.asarray(longtimes["t"])
        g = np.asarray(longtimes["g"])
        g_sum = np.asarray(longtimes["g_sum"])
        g_smoothed = np.asarray(longtimes["g_smoothed"])
        derivative = np.asarray(longtimes["dg_dt"])
        landmarks = np.asarray(singlebeat["beat_landmark_indices"], dtype=np.int64)
        has_streak_qc = all(
            name in singlebeat for name in ("phase", "streak_trace", "streak_mask")
        )
        if has_streak_qc:
            phase = np.asarray(singlebeat["phase"])
            streak_trace = np.asarray(singlebeat["streak_trace"])
            streak_mask = np.asarray(singlebeat["streak_mask"], dtype=bool)

    figure, axes = plt.subplots(2, 1, sharex=True, figsize=(10, 6))
    axes[0].plot(t, g, label="SVD g(t)", linewidth=1.0)
    if not np.array_equal(g, g_smoothed):
        axes[0].plot(t, g_smoothed, label="filtered g(t)", linewidth=1.0)
    axes[0].set_ylabel("high-f power")
    sum_axis = axes[0].twinx()
    sum_line = sum_axis.plot(
        t, g_sum, color="0.65", linewidth=0.7, label="raw g_sum(t)"
    )[0]
    sum_axis.set_ylabel("raw high-f sum", color="0.4")
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend(handles + [sum_line], labels + ["raw g_sum(t)"], loc="best")
    axes[1].plot(t, derivative, label="dg/dt", linewidth=1.0)
    if landmarks.size:
        axes[1].scatter(
            t[landmarks],
            derivative[landmarks],
            color="red",
            marker="x",
            label="positive maxima",
            zorder=3,
        )
    axes[1].set_xlabel("acquisition time (s)")
    axes[1].set_ylabel("dg/dt")
    axes[1].legend(loc="best")
    figure.tight_layout()
    figure.savefig(png_dir / "cardiac_segmentation_qc.png", dpi=150)
    plt.close(figure)

    if not has_streak_qc:
        return

    iio.imwrite(
        png_dir / "singlebeat_streak_mask.png",
        (streak_mask.astype(np.uint8) * 255),
    )
    detected = np.flatnonzero(np.any(streak_mask, axis=1))
    if detected.size:
        beat_index = int(detected[0])
        figure, axis = plt.subplots(figsize=(10, 3))
        axis.plot(phase, streak_trace[beat_index], linewidth=1.0)
        axis.fill_between(
            phase,
            0,
            streak_trace[beat_index],
            where=streak_mask[beat_index],
            color="red",
            alpha=0.3,
            label="repaired interval",
        )
        axis.set_xlabel("normalized cardiac phase")
        axis.set_ylabel("mean fundus power")
        axis.set_title(f"Broadband streak QC, accepted beat {beat_index}")
        axis.legend(loc="best")
        figure.tight_layout()
        figure.savefig(png_dir / f"streak_qc_beat_{beat_index:04d}.png", dpi=150)
        plt.close(figure)


def _save_endpoint_pngs(h5_path, target_dir, parameters):
    """Save long-time and cardiac-phase maps with frequency vertical."""
    png_dir = Path(target_dir) / "png"
    png_dir.mkdir(parents=True, exist_ok=True)
    with h5py.File(h5_path, "r") as handle:
        root = handle["spectrograms"] if "spectrograms" in handle else handle
        endpoint_maps = {}
        for group_name in ("longtimes", "singlebeat"):
            if group_name not in root:
                continue
            for name in ("S", "S0", "L"):
                if name not in root[group_name]:
                    continue
                endpoint_maps[f"{group_name}_{name}"] = np.asarray(
                    root[group_name][name], dtype=np.float32
                )

    for name, values in endpoint_maps.items():
        # HDF5 is (time-or-phase,f); transposition makes f vertical.
        display = apply_contrast_adjustment(values.T, parameters)
        path = png_dir / f"{name}.png"
        iio.imwrite(path, normalize_to_uint8(display))
        print(f"Saving: {path}")
    _save_cardiac_qc_plots(h5_path, png_dir)


def process(file_path, parameters, progress_callback=None, warning_callback=None):
    """Compute and stream ``S(t,f)``, ``S0(t,f)``, and ``L(t,f)`` to HDF5."""
    file_reader, parameters, starts = _prepare(file_path, parameters)
    target_dir, h5_path = _output_path(file_reader, parameters)
    parameters.pop(H5_OUTPUT_PATH_PARAMETER, None)

    output_bytes = estimated_endpoint_bytes(len(starts), parameters["f_bins"])
    print(
        "Spectral endpoints: "
        f"S, S0, and L shapes=({len(starts)}, {parameters['f_bins']}) (t,f), "
        f"payload={output_bytes / 1024**2:.2f} MiB"
    )
    print(f"Saving spectral endpoints to: {h5_path}")

    started = time.time()
    handle = None
    pulse_detection_error = None
    try:
        (
            handle,
            spectrograms,
            signal_dataset,
            background_dataset,
            log_ratio_dataset,
        ) = _create_h5(h5_path, file_reader, parameters, starts)
        for index, frame_start in enumerate(tqdm(starts, desc="Spectral endpoints")):
            frames = file_reader.read_frames(
                first_frame=int(frame_start), batch_size=parameters["batch_size"]
            )
            frames = cp.asarray(frames, dtype=cp.float32)
            if parameters.get("filter2d", False):
                frames = filter_2d(
                    cp, cp.fft, frames, parameters.get("filter2d_low", 0.03)
                )

            signal_power, background_power = _endpoint_spectra_window(
                parameters, frames
            )
            log_ratio = log_power_ratio(cp, signal_power, background_power)
            signal_dataset[index] = cp.asnumpy(signal_power)
            background_dataset[index] = cp.asnumpy(background_power)
            log_ratio_dataset[index] = cp.asnumpy(log_ratio)
            del signal_power, background_power, log_ratio

            if progress_callback is not None:
                progress_callback(
                    index + 1,
                    len(starts),
                    f"Spectral window {index + 1}/{len(starts)}",
                )

        print("Detecting and aggregating cardiac beats")
        analysis = cardiac_phase_analysis(
            np.asarray(signal_dataset, dtype=np.float32),
            np.asarray(background_dataset, dtype=np.float32),
            np.asarray(spectrograms["longtimes/t"], dtype=np.float64),
            np.asarray(spectrograms["longtimes/f"], dtype=np.float64),
            parameters,
        )
        _write_cardiac_h5(spectrograms, analysis, parameters)
        pulse_detected = bool(analysis.get("pulse_detected", True))
        spectrograms.attrs["pulse_detected"] = pulse_detected
        spectrograms.attrs["singlebeat_available"] = pulse_detected
        if pulse_detected:
            print(
                "Cardiac aggregation: "
                f"{len(analysis['beat_landmark_indices'])} landmarks, "
                f"{len(analysis['accepted_beat_indices'])} accepted beats, "
                f"{np.count_nonzero(analysis['streak_mask'])} streak samples"
            )
        else:
            pulse_detection_error = analysis.get(
                "pulse_detection_error", CARDIAC_PULSE_NOT_DETECTED
            )
            spectrograms.attrs["pulse_detection_error"] = pulse_detection_error
            print(f"Warning: {pulse_detection_error}")
        spectrograms.attrs.modify("complete", True)
        handle.flush()
    finally:
        if handle is not None:
            handle.close()
        if hasattr(file_reader, "close"):
            file_reader.close()
        cp.get_default_memory_pool().free_all_blocks()

    _save_endpoint_pngs(h5_path, target_dir, parameters)
    _save_metadata(target_dir, file_reader, parameters)
    elapsed = time.time() - started
    print(f"Spectral endpoints completed in {elapsed:.1f} seconds")
    if pulse_detection_error is not None and warning_callback is not None:
        warning_callback("cardiac_pulse_not_detected", pulse_detection_error)
    return h5_path


def preview(file_path, parameters, save_debug=True):
    """Return S, S0, and L spectra from the first temporal window."""
    file_reader, parameters, starts = _prepare(file_path, parameters)
    try:
        frames = file_reader.read_frames(
            first_frame=int(starts[0]), batch_size=parameters["batch_size"]
        )
        frames = cp.asarray(frames, dtype=cp.float32)
        if parameters.get("filter2d", False):
            frames = filter_2d(
                cp, cp.fft, frames, parameters.get("filter2d_low", 0.03)
            )

        signal_power, background_power = _endpoint_spectra_window(parameters, frames)
        log_ratio = log_power_ratio(cp, signal_power, background_power)
        endpoint_spectra = cp.asnumpy(
            cp.stack((signal_power, background_power, log_ratio))
        )
        preview_image = normalize_to_uint8(endpoint_spectra)

        if save_debug:
            if parameters.get("saving_to_folder"):
                preview_path = Path(parameters["saving_to_folder"]) / "preview"
            else:
                preview_path = (
                    _get_default_output_path(file_reader.file_path) / "preview"
                )
            save_preview_images(
                {"spectral_endpoints": preview_image}, preview_path
            )
    finally:
        if hasattr(file_reader, "close"):
            file_reader.close()
        cp.get_default_memory_pool().free_all_blocks()
    return preview_image
