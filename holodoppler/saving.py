from pathlib import Path
import base64
import h5py
import html
import imageio as iio
import numpy as np
import json
import time
from datetime import datetime
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
import os
from urllib.parse import quote

from .utils import (
    resize_slicewise,
    normalize_to_uint8,
    unsharp_projection,
    _pad_to_even,
    stretchlim,
    imadjust,
)
from .get_version import get_version

H5_DATASET_RENAMES = {
    "M0": "moment0",
    "M1": "moment1",
    "M2": "moment2",
    "M0ff": "moment0ff",
    "moment_0": "moment0",
    "moment_1": "moment1",
    "moment_2": "moment2",
    "moment_0_ff": "moment0ff",
}
H5_FLOAT32_DATASETS = {
    "M0",
    "M0ff",
    "M1",
    "M2",
    "moment0",
    "moment0ff",
    "moment1",
    "moment2",
    "moment_0",
    "moment_0_ff",
    "moment_1",
    "moment_2",
}
DEFAULT_VIDEO_FPS = 30.0
MP4_MAX_FPS = 60.0
NON_CONTRAST_OUTPUT_NAMES = {
    "registration",
    "register_laplacian",
    "shack_hartmann_zernike_coefs",
    "zernike_coefs_radians",
}


def apply_contrast_adjustment(data, parameters):
    """Apply configured display contrast to one image/video array."""
    settings = _contrast_settings(parameters)
    if settings is None or not _is_contrast_candidate(data):
        return data

    arr = np.asarray(data)
    if np.iscomplexobj(arr):
        arr = np.abs(arr)
    low, high = stretchlim(arr, settings["low_percent"], settings["high_percent"])
    return imadjust(arr, low, high, settings["gamma"])


def apply_contrast_adjustments(save_map, parameters, skip_debug=True):
    """Apply configured display contrast to visual outputs in a save map."""
    if _contrast_settings(parameters) is None:
        return dict(save_map)

    adjusted = {}
    for name, data in save_map.items():
        if _skip_contrast_for_name(name, skip_debug):
            adjusted[name] = data
        else:
            adjusted[name] = apply_contrast_adjustment(data, parameters)
    return adjusted


def _contrast_settings(parameters):
    parameters = parameters or {}
    cfg = parameters.get("contrast_adjustment")
    if isinstance(cfg, dict) and cfg.get("enabled", False):
        return {
            "low_percent": float(cfg.get("low_percent", 1.0)),
            "high_percent": float(cfg.get("high_percent", 99.0)),
            "gamma": float(cfg.get("gamma", 1.0)),
        }

    if not parameters.get("contrast", False):
        return None

    low_high = parameters.get("contrast_low_max_percent", (1.0, 99.0))
    if isinstance(low_high, (int, float)):
        low_percent, high_percent = float(low_high), 100.0 - float(low_high)
    else:
        low_percent, high_percent = low_high
    return {
        "low_percent": float(low_percent),
        "high_percent": float(high_percent),
        "gamma": float(parameters.get("contrast_gamma", 1.0)),
    }


def _is_contrast_candidate(data):
    arr = np.asarray(data)
    return arr.size > 0 and arr.ndim in (2, 3, 4) and np.issubdtype(arr.dtype, np.number)


def _skip_contrast_for_name(name, skip_debug):
    name = str(name)
    return (
        (skip_debug and name.startswith("debug_"))
        or name in NON_CONTRAST_OUTPUT_NAMES
        or name.endswith("_coefs")
        or "zernike_coefs" in name
    )


def _h5_data(name, data):
    if name in H5_FLOAT32_DATASETS:
        return np.asarray(data, dtype=np.float32)
    return data


def _h5_dataset_name(name):
    return H5_DATASET_RENAMES.get(name, name)


def save_preview_images(save_dict, save_dir, prefix="debug", square=False):
    os.makedirs(save_dir, exist_ok=True)
    for key, img in save_dict.items():
        if img is None:
            continue
        img_np = np.asarray(img)
        if img_np.ndim not in [2, 3]:
            continue
        if square:
            if img_np.ndim == 3 and img_np.shape[-1] in (3, 4):
                axes = (0, 1)
            else:
                axes = (-2, -1)
            size = max(img_np.shape[axis] for axis in axes)
            img_np = resize_slicewise(img_np, size, size, axes=axes)
        if img_np.dtype != np.uint8:
            img_np = normalize_to_uint8(img_np)
        filename = os.path.join(save_dir, f"{prefix}_{key}.png")
        print("Saving : ",filename)
        iio.imwrite(filename, img_np)


def preview_image_from_results(results):
    """Return a displayable uint8 preview image from a pipeline result dict."""
    if not results:
        return None

    preferred = ("M0ff", "M0", "moment_0_ff", "moment_0", "moment0ff", "moment0")
    keys = [key for key in preferred if key in results]
    keys.extend(key for key in results if key not in keys)

    for key in keys:
        image = _preview_image_candidate(results[key])
        if image is not None:
            return normalize_to_uint8(image)
    return None


def save_result_map(
    target_dir,
    raw_map,
    parameters,
    file_reader,
    *,
    num_batch=None,
    end_frame=None,
    first_frame=None,
):
    """Save a pipeline result map with the release rendering/report behavior."""
    target_dir = Path(target_dir)
    _create_directories(target_dir, "FULL")
    display_map = apply_contrast_adjustments(
        raw_map,
        parameters,
        skip_debug=True,
    )
    uint8_map = {
        name: normalize_to_uint8(data)
        for name, data in display_map.items()
        if data is not None
    }
    video_fps = _calculate_fps(
        num_batch,
        end_frame,
        first_frame,
        parameters,
    )
    _save_videos(target_dir, uint8_map, video_fps)
    _save_pngs(target_dir, uint8_map)
    _save_metadata(target_dir, file_reader, parameters)
    _save_reports(
        target_dir,
        display_map,
        uint8_map,
        parameters,
        file_reader,
    )
    return uint8_map


def _preview_image_candidate(data):
    arr = np.asarray(data)
    if arr.size == 0:
        return None
    if np.iscomplexobj(arr):
        arr = np.abs(arr)
    arr = np.squeeze(arr)

    if arr.ndim == 2:
        return arr

    if arr.ndim == 3:
        if arr.shape[-1] in (3, 4):
            return arr
        if arr.shape[0] in (3, 4):
            return np.moveaxis(arr, 0, -1)
        return np.mean(arr.astype(np.float32, copy=False), axis=0)

    if arr.ndim > 3:
        while arr.ndim > 3:
            arr = np.mean(arr.astype(np.float32, copy=False), axis=0)
        return _preview_image_candidate(arr)

    return None


def save_outputs(
    file_reader,
    video_path=None,
    holodoppler_path=None,
    vid=None,
    vid_debug=None,
    parameters=None,
    reg_list=None,
    coefs_list=None,
    end_frame=None,
    first_frame=None,
    num_batch=None,
    backend=None,
):
    """
    Main entry point for saving.
    Priority: holodoppler_path > video_path > default
    """
    start_time = time.time()

    # Path resolution
    default_path = _get_default_output_path(file_reader.file_path)

    if holodoppler_path:
        if isinstance(holodoppler_path, bool):
            holodoppler_path = default_path
        target_dir = Path(holodoppler_path)
        save_mode = "FULL"
    elif video_path:
        if isinstance(video_path, bool):
            video_path = default_path
        target_dir = Path(video_path)
        save_mode = "LITE"
    else:
        target_dir = default_path
        save_mode = "FULL"

    print(f"Output directory: {target_dir}")
    print(f"Save mode: {save_mode}")

    # Execute save
    _save_bundle(
        file_reader,
        target_dir=target_dir,
        mode=save_mode,
        vid=vid,
        vid_debug=vid_debug,
        parameters=parameters,
        reg_list=reg_list,
        coefs_list=coefs_list,
        end_frame=end_frame,
        first_frame=first_frame,
        num_batch=num_batch,
        backend=backend,
    )

    elapsed = time.time() - start_time
    print(f"\nSaving completed in {elapsed:.1f} seconds")


def _get_default_output_path(file_path):
    """Generates the standard Holodoppler directory structure"""
    path = Path(file_path)
    base_name = path.stem
    return path.parent / base_name / f"{base_name}_HD"


def _save_bundle(
    file_reader,
    target_dir,
    mode,
    vid,
    vid_debug,
    parameters,
    reg_list,
    coefs_list,
    end_frame,
    first_frame,
    num_batch,
    backend=None,
):
    """
    Unified saving engine.
    mode="FULL" -> Saves everything including H5.
    mode="LITE" -> Saves videos, pngs, json, txt.
    """
    start_time = time.time()

    # Create subdirectories
    _create_directories(target_dir, mode)

    video_fps = _calculate_fps(num_batch, end_frame, first_frame, parameters)

    # Prepare data for saving
    save_map = _build_save_map(vid, parameters, vid_debug, num_batch)

    # Process and save projections (unsharp masking)
    _save_projections(target_dir, save_map, parameters, backend)

    # Convert all data to uint8 once (memory efficient)
    uint8_map = {name: normalize_to_uint8(data) for name, data in save_map.items()}

    # Save videos (sequential to avoid encoding conflicts)
    _save_videos(target_dir, uint8_map, video_fps)

    # Save PNGs (parallel)
    _save_pngs(target_dir, uint8_map)

    # Save metadata (fast)
    _save_metadata(target_dir, file_reader, parameters)

    # Save H5 if FULL mode
    if mode == "FULL":
        _save_h5(target_dir, vid, parameters, reg_list, coefs_list)

    report_raw_map = dict(save_map)
    if reg_list:
        report_raw_map["registration"] = np.asarray(reg_list, dtype=np.float32)
    _save_reports(target_dir, report_raw_map, uint8_map, parameters, file_reader)

    elapsed = time.time() - start_time
    print(f"_save_bundle completed in {elapsed:.1f} seconds")


def _create_directories(target_dir, mode):
    """Create required subdirectories"""
    subdirs = ["png", "mp4", "avi", "json", "html", "pdf"]
    if mode == "FULL":
        subdirs.append("h5")
    for sub in subdirs:
        (target_dir / sub).mkdir(parents=True, exist_ok=True)


def _calculate_fps(num_batch, end_frame, first_frame, parameters):
    """Return the real-time cadence of the processed output frames."""
    parameters = parameters or {}
    sampling_freq = _positive_float(parameters.get("sampling_freq"))

    pipeline_name = str(parameters.get("pipeline_name", "")).lower()
    if "sliding" in pipeline_name:
        stride_keys = ("time_stride", "batch_stride")
    else:
        stride_keys = ("batch_stride", "time_stride")

    stride = next(
        (
            value
            for key in stride_keys
            if (value := _positive_float(parameters.get(key))) is not None
        ),
        None,
    )
    if sampling_freq is not None and stride is not None:
        fps = sampling_freq / stride
        print(f"Real-time video FPS: {fps:.6g} ({sampling_freq:.6g} Hz / {stride:.6g} frames)")
        return fps

    # Compatibility fallback for callers that do not provide a processing stride.
    frame_range = None
    if end_frame is not None and first_frame is not None:
        frame_range = _positive_float(end_frame - first_frame)
    batch_count = _positive_float(num_batch)
    if sampling_freq is not None and frame_range is not None and batch_count is not None:
        fps = batch_count / frame_range * sampling_freq
        print(f"Estimated real-time video FPS: {fps:.6g}")
        return fps

    print(f"Video timing unavailable, using default FPS: {DEFAULT_VIDEO_FPS:g}")
    return DEFAULT_VIDEO_FPS


def _positive_float(value):
    """Convert a finite positive value to float, or return None."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(value) or value <= 0:
        return None
    return value


def _prepare_mp4_frames(frames, source_fps, max_fps=MP4_MAX_FPS):
    """Limit MP4 playback FPS while preserving duration as closely as possible."""
    frames = np.asarray(frames)
    source_fps = _positive_float(source_fps)
    max_fps = _positive_float(max_fps)
    if source_fps is None:
        source_fps = DEFAULT_VIDEO_FPS
    if max_fps is None:
        raise ValueError("max_fps must be a finite positive number")

    frame_count = frames.shape[0]
    if frame_count <= 1 or source_fps <= max_fps:
        return frames, min(source_fps, max_fps)

    # Use as many frames as the MP4 limit permits. Adjusting the encoded FPS to
    # the retained count keeps retained_count / encoded_fps == count / source_fps.
    retained_count = max(1, int(np.floor(frame_count * max_fps / source_fps)))
    retained_count = min(retained_count, frame_count)
    indices = np.floor(
        np.arange(retained_count, dtype=np.float64) * frame_count / retained_count
    ).astype(np.intp)
    mp4_frames = frames[indices]
    mp4_fps = min(source_fps * retained_count / frame_count, max_fps)
    return mp4_frames, mp4_fps


def _build_save_map(vid, parameters, vid_debug, num_batch):
    """Build dictionary of all data to save"""
    save_map = {
        "moment_0": vid[:, 0, :, :],
        "moment_1": vid[:, 1, :, :],
        "moment_2": vid[:, 2, :, :],
        "moment_0_ff": vid[:, 3, :, :],
    }

    # Frequency bands
    for k, v in enumerate(parameters.get("frequency_bands", [])):
        band_name = f"band_avg_{v[0]}_{v[1]}"
        save_map[band_name] = vid[:, 4 + k, :, :]

    # Debug videos
    if vid_debug:
        for key, data in vid_debug.items():
            if data.ndim == 3 and data.shape[-1] == num_batch:
                data = np.moveaxis(data, -1, 0)  # ensure (T, H, W)

            # Handle special cases
            if parameters.get("square") and key in [
                "M0ffnoreg", "M0notfixed", "montage",
                "montagenormalized", "psd_map_avg", "SVD_M0_inversed_svd_filter"
            ]:
                m = max(data.shape[-2], data.shape[-1])
                data = resize_slicewise(data, m, m)

            if key == "psd_map_avg":  # Special normalization
                for i in range(data.shape[0]):
                    data[i] = normalize_to_uint8(data[i])

            if data.ndim == 3 or data.ndim == 4:
                save_map[f"debug_{key}"] = data

    return apply_contrast_adjustments(save_map, parameters, skip_debug=True)


def _save_projections(target_dir, save_map, parameters, backend):
    """Save unsharp masked projections as PNGs"""
    # Initialize backend if needed
    if backend is None:
        from .backend import BackendManager
        bm = BackendManager(backend=parameters.get("backend", "cpu"))
    else:
        bm = backend

    # Define which keys get projection
    projection_keys = {
        "moment_0", "moment_1", "moment_2", "moment_0_ff",
        "montage", "montagenormalized"
    }

    # Also include frequency bands
    projection_keys.update([k for k in save_map.keys() if "frequency_bands" in k])

    for name, data in save_map.items():
        if name in projection_keys:
            try:
                # Create projection
                im = unsharp_projection(bm, data, (1024, 1024), radius=2.0, amount=2.0)
                im = normalize_to_uint8(im)

                # Save
                png_path = target_dir / "png" / f"{name}_unsharped.png"
                iio.imwrite(png_path, im)
            except Exception as e:
                print(f"Failed to save projection for {name}: {e}")


def _save_videos(target_dir, uint8_map, source_fps):
    """Save real-time AVI files and compatibility MP4 previews."""
    start_time = time.time()
    completed = 0
    for name, data in uint8_map.items():

        if data.ndim !=3 and data.ndim !=4 : #check to avoid failure for outputs that are not videos exemple : list of coefficients
            continue
        uint8_data = normalize_to_uint8(data)
        # MP4 previews target broadly supported playback rates. Frames may be
        # discarded here only; AVI and H5 outputs retain every processed frame.
        mp4_data, mp4_fps = _prepare_mp4_frames(uint8_data, source_fps)
        dropped_frames = uint8_data.shape[0] - mp4_data.shape[0]
        if dropped_frames:
            print(
                f"MP4 {name}: {dropped_frames}/{uint8_data.shape[0]} frames dropped, "
                f"encoded at {mp4_fps:.6g} FPS"
            )
        mp4_path = target_dir / "mp4" / f"{name}.mp4"
        _write_video_fast(
            mp4_path,
            mp4_data,
            mp4_fps,
            codec="libx264",
            preset="ultrafast",
            crf=28,
        )

        # AVI
        avi_path = target_dir / "avi" / f"{name}.avi"
        _write_video_fast(
            avi_path,
            uint8_data,
            source_fps,
            codec="mjpeg",
            quality=8,
        )

        completed += 1

    elapsed = time.time() - start_time
    print(f"Videos saved in {elapsed:.1f} seconds ({completed} videos)")


def _spectral_cube_frequency_indices(selection, frequency_count):
    """Resolve the configured frequency-bin selection without reordering it."""
    if selection is None or (isinstance(selection, str) and selection.lower() == "all"):
        return list(range(frequency_count))

    if isinstance(selection, (int, np.integer)):
        selection = [int(selection)]
    if not isinstance(selection, (list, tuple)):
        raise ValueError(
            "spectral_cube_avi_frequency_indices must be 'all', an integer, "
            "or a list of integers"
        )

    indices = []
    for raw_index in selection:
        index = int(raw_index)
        if index < 0 or index >= frequency_count:
            raise ValueError(
                f"Frequency-bin index {index} is outside [0, {frequency_count - 1}]"
            )
        if index not in indices:
            indices.append(index)
    return indices


def _time_average_spectral_cube(cube, chunk_size=8):
    """Average an HDF5 ``S(t,f,y,x)`` dataset without loading it all at once."""
    if cube.ndim != 4 or cube.shape[0] == 0:
        raise ValueError(f"Expected a non-empty S(t,f,y,x) dataset, got {cube.shape}")
    chunk_size = int(chunk_size)
    if chunk_size <= 0:
        raise ValueError("spectral_cube_avi_time_chunk must be a positive integer")

    accumulator = np.zeros(cube.shape[1:], dtype=np.float64)
    for start in range(0, cube.shape[0], chunk_size):
        stop = min(start + chunk_size, cube.shape[0])
        accumulator += np.sum(
            np.asarray(cube[start:stop], dtype=np.float32),
            axis=0,
            dtype=np.float64,
        )
    return (accumulator / cube.shape[0]).astype(np.float32)


def _power_to_relative_db(power, floor_power=None, floor_db=-60.0):
    """Convert power to relative dB after applying a scalar or per-f floor."""
    floor_db = float(floor_db)
    if not np.isfinite(floor_db) or floor_db >= 0:
        raise ValueError("spectral_cube_avi_log_floor_db must be finite and negative")

    power = np.nan_to_num(
        np.asarray(power, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0
    )
    power = np.maximum(power, 0.0)
    peak = float(np.max(power))
    if peak <= 0:
        return np.full(power.shape, floor_db, dtype=np.float32)

    numerical_floor = peak * np.finfo(np.float32).eps
    if floor_power is None:
        effective_floor = peak * 10.0 ** (floor_db / 10.0)
    else:
        effective_floor = np.nan_to_num(
            np.asarray(floor_power, dtype=np.float32),
            nan=numerical_floor,
            posinf=peak,
            neginf=numerical_floor,
        )
        if effective_floor.ndim == 1 and power.ndim >= 3:
            if effective_floor.shape[0] != power.shape[0]:
                raise ValueError(
                    "Per-frequency floor length must match the first power axis"
                )
            effective_floor = effective_floor.reshape(
                (effective_floor.shape[0],) + (1,) * (power.ndim - 1)
            )
        effective_floor = np.maximum(effective_floor, numerical_floor)

    return (10.0 * np.log10(np.maximum(power, effective_floor) / peak)).astype(
        np.float32
    )


def save_spectral_cube_avi(h5_path, target_dir, parameters):
    """Export time-averaged log-power maps as one frequency-sweep AVI."""
    if not parameters.get("spectral_cube_avi", True):
        print("Spectral-cube AVI export disabled")
        return None

    h5_path = Path(h5_path)
    target_dir = Path(target_dir)
    avi_dir = target_dir / "avi"
    avi_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()

    with h5py.File(h5_path, "r") as handle:
        required = {"S", "f", "corner_average_power"}
        if not required.issubset(handle):
            missing = sorted(required.difference(handle))
            raise ValueError(
                f"Spectral-cube H5 is missing required datasets {missing}: {h5_path}"
            )

        cube = handle["S"]
        frequencies = np.asarray(handle["f"])
        if cube.ndim != 4 or cube.shape[1] != len(frequencies):
            raise ValueError(
                "Expected S with axis order (t,f,y,x) matching the f coordinate; "
                f"got S{cube.shape} and f{frequencies.shape}"
            )

        indices = _spectral_cube_frequency_indices(
            parameters.get("spectral_cube_avi_frequency_indices", "all"),
            cube.shape[1],
        )
        print(f"Averaging {cube.shape[0]} spectral-cube time samples")
        mean_power = _time_average_spectral_cube(
            cube,
            chunk_size=parameters.get("spectral_cube_avi_time_chunk", 8),
        )
        corner_floor = np.mean(
            np.asarray(handle["corner_average_power"], dtype=np.float32),
            axis=0,
            dtype=np.float64,
        ).astype(np.float32)

    mean_power = mean_power[indices]
    corner_floor = corner_floor[indices]
    selected_frequencies = frequencies[indices]
    log_power = _power_to_relative_db(
        mean_power,
        floor_power=corner_floor,
    )
    display_video = apply_contrast_adjustment(log_power, parameters)
    uint8_video = normalize_to_uint8(display_video)

    playback_fps = _positive_float(parameters.get("spectral_cube_avi_fps", 30.0))
    if playback_fps is None:
        raise ValueError("spectral_cube_avi_fps must be a finite positive number")
    avi_path = avi_dir / "spectral_cube_time_average_log_f.avi"
    _write_video_fast(
        avi_path,
        uint8_video,
        playback_fps,
        codec="mjpeg",
        quality=8,
    )

    frequency_path = avi_dir / "spectral_cube_time_average_log_f_frequency_hz.csv"
    np.savetxt(
        frequency_path,
        np.column_stack(
            (np.arange(len(indices)), indices, selected_frequencies, corner_floor)
        ),
        delimiter=",",
        header="avi_frame,f_index,frequency_hz,corner_floor_power",
        comments="",
        fmt=["%d", "%d", "%.12g", "%.12g"],
    )

    elapsed = time.time() - started
    print(
        f"Spectral-cube frequency-sweep AVI saved in {elapsed:.1f} seconds "
        f"({len(indices)} frequency frames, {playback_fps:.6g} FPS)"
    )
    return avi_path


def _save_pngs(target_dir, uint8_map):
    """Save mean frames as PNGs in parallel"""
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=8) as executor:
        tasks = []
        for name, data in uint8_map.items():
            if data.ndim !=3 and data.ndim !=4 : #check to avoid failure for outputs that are not videos exemple : list of coefficients
                continue
            uint8_data = normalize_to_uint8(data)
            png_path = target_dir / "png" / f"{name}.png"
            mean_frame = np.mean(uint8_data, axis=0).astype(np.uint8)
            tasks.append(executor.submit(iio.imwrite, png_path, mean_frame))

        # Wait for all tasks to complete
        completed = 0
        for future in as_completed(tasks):
            try:
                future.result()
                completed += 1
            except Exception as e:
                print(f"PNG save failed: {e}")

    elapsed = time.time() - start_time
    print(f"PNGs saved in {elapsed:.1f} seconds ({completed} images)")


def _save_reports(target_dir, raw_map, uint8_map, parameters, file_reader):
    """Save visual result summaries in HTML and PDF formats."""
    html_dir = target_dir / "html"
    pdf_dir = target_dir / "pdf"
    html_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    try:
        start_time = time.time()
        entries = _result_entries(raw_map, uint8_map)

        # Remove old assessment report names from earlier builds.
        legacy_report_dir = target_dir / "reports"
        for old_name in (
            "quality_report.html",
            "quality_report.pdf",
            "quality_report_error.txt",
            "results_report.html",
            "results_report.pdf",
            "results_report_error.txt",
        ):
            old_path = legacy_report_dir / old_name
            if old_path.exists():
                old_path.unlink()
        if legacy_report_dir.exists():
            try:
                legacy_report_dir.rmdir()
            except OSError:
                pass

        html_path = html_dir / "results_report.html"
        pdf_path = pdf_dir / "results_report.pdf"

        html_path.write_text(
            _render_results_report_html(entries, parameters, file_reader),
            encoding="utf-8",
        )
        _write_results_report_pdf(pdf_path, entries, parameters, file_reader)

        elapsed = time.time() - start_time
        print(f"Reports saved in {elapsed:.1f} seconds: {html_path.name}, {pdf_path.name}")
    except Exception as exc:
        error_path = html_dir / "results_report_error.txt"
        error_path.write_text(f"Report generation failed:\n{exc}\n", encoding="utf-8")
        print(f"Report generation failed: {exc}")


def _result_entries(raw_map, uint8_map):
    names = list(dict.fromkeys([*raw_map.keys(), *uint8_map.keys()]))
    return [
        _result_entry(name, raw_map.get(name), uint8_map.get(name))
        for name in names
    ]


def _result_entry(name, raw_data, uint8_data):
    source = raw_data if raw_data is not None else uint8_data
    arr = np.asarray(source)
    previews = _result_previews(raw_data, uint8_data)
    plot = None
    if not previews and arr.ndim <= 2:
        plot = _plot_array_preview(arr, name)

    return {
        "name": name,
        "shape": tuple(int(v) for v in getattr(arr, "shape", ())),
        "dtype": str(getattr(arr, "dtype", "")),
        "kind": _result_kind(arr, uint8_data),
        "previews": previews,
        "plot": plot,
        "links": _output_links(name, uint8_data),
    }


def _result_kind(arr, uint8_data):
    if getattr(uint8_data, "ndim", 0) in (3, 4):
        return "video-like output"
    if arr.ndim == 2:
        return "image or matrix"
    if arr.ndim == 1:
        return "vector"
    if arr.ndim == 0:
        return "scalar"
    return f"{arr.ndim}D array"


def _output_links(name, uint8_data):
    if getattr(uint8_data, "ndim", 0) not in (3, 4):
        return []
    url_name = quote(name, safe="")
    return [
        ("PNG", f"../png/{url_name}.png"),
        ("MP4", f"../mp4/{url_name}.mp4"),
    ]


def _result_previews(raw_data, uint8_data):
    if getattr(uint8_data, "ndim", 0) in (3, 4):
        return _video_preview_images(uint8_data)

    if raw_data is None:
        return []

    arr = np.asarray(raw_data)
    if arr.ndim == 2:
        if min(arr.shape) <= 16:
            return []
        return [{"label": "image", "image": _normalize_image_for_report(arr)}]
    if arr.ndim in (3, 4):
        return _video_preview_images(_normalize_array_for_report(arr))
    return []


def _video_preview_images(data):
    arr = np.asarray(data)
    if arr.shape[0] == 0:
        return []

    previews = []
    seen = set()
    for label, index in (
        ("first", 0),
        ("middle", arr.shape[0] // 2),
        ("last", arr.shape[0] - 1),
    ):
        if index in seen:
            continue
        seen.add(index)
        previews.append({"label": label, "image": _image_from_array(arr[index])})

    previews.append({"label": "mean", "image": _image_from_array(np.mean(arr.astype(np.float32, copy=False), axis=0))})
    return previews


def _normalize_array_for_report(data):
    arr = np.asarray(data)
    if arr.ndim == 2:
        return _normalize_image_for_report(arr)
    if arr.ndim == 3:
        return np.stack([_normalize_image_for_report(frame) for frame in arr], axis=0)
    if arr.ndim == 4:
        return np.stack([_image_from_array(frame) for frame in arr], axis=0)
    return arr


def _normalize_image_for_report(data):
    arr = np.asarray(data)
    if np.iscomplexobj(arr):
        arr = np.abs(arr)
    arr = arr.astype(np.float32, copy=False)
    finite = np.isfinite(arr)
    if not np.any(finite):
        return np.zeros(arr.shape, dtype=np.uint8)
    finite_values = arr[finite]
    low, high = np.percentile(finite_values, [1, 99])
    if high <= low:
        low = float(np.min(finite_values))
        high = float(np.max(finite_values))
    if high <= low:
        return np.zeros(arr.shape, dtype=np.uint8)
    arr = np.nan_to_num(arr, nan=low, posinf=high, neginf=low)
    return np.clip((arr - low) / (high - low) * 255, 0, 255).astype(np.uint8)


def _image_from_array(data):
    arr = np.asarray(data)
    if arr.ndim == 2:
        return np.clip(arr, 0, 255).astype(np.uint8)
    if arr.ndim == 3:
        if arr.shape[-1] == 1:
            return np.clip(arr[..., 0], 0, 255).astype(np.uint8)
        if arr.shape[-1] == 2:
            arr = np.concatenate([arr, arr[..., :1]], axis=-1)
        if arr.shape[-1] >= 3:
            return np.clip(arr[..., :3], 0, 255).astype(np.uint8)
        return np.clip(np.mean(arr.astype(np.float32, copy=False), axis=0), 0, 255).astype(np.uint8)
    while arr.ndim > 2:
        arr = np.mean(arr.astype(np.float32, copy=False), axis=0)
    return _normalize_image_for_report(arr)


def _plot_array_preview(data, title):
    arr = np.asarray(data)
    if arr.size == 0:
        return None
    if np.iscomplexobj(arr):
        arr = np.abs(arr)
    arr = np.squeeze(arr)

    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=120)
    if arr.ndim == 0:
        ax.text(0.5, 0.5, f"{float(arr):.4g}", ha="center", va="center", fontsize=16)
        ax.set_axis_off()
    elif arr.ndim == 1:
        ax.plot(arr)
        ax.set_xlabel("Index")
        ax.grid(True, alpha=0.3)
    elif arr.ndim == 2 and arr.shape[1] <= 16 and arr.shape[0] > 1:
        for col in range(arr.shape[1]):
            ax.plot(arr[:, col], label=f"col {col}")
        ax.set_xlabel("Index")
        ax.grid(True, alpha=0.3)
        if arr.shape[1] <= 6:
            ax.legend(fontsize=7)
    elif arr.ndim == 2:
        im = ax.imshow(arr, aspect="auto", cmap="viridis")
        fig.colorbar(im, ax=ax, shrink=0.8)
    else:
        ax.plot(arr.reshape(-1))
        ax.set_xlabel("Flattened index")
        ax.grid(True, alpha=0.3)
    ax.set_title(title)
    fig.tight_layout()
    image = _fig_to_image(fig)
    plt.close(fig)
    return image


def _fig_to_image(fig):
    fig.canvas.draw()
    rgba = np.asarray(fig.canvas.buffer_rgba())
    return rgba[..., :3].copy()


def _render_results_report_html(entries, parameters, file_reader):
    cards = "\n".join(_render_result_card(entry) for entry in entries)
    metadata_rows = _report_metadata_rows(parameters, file_reader)
    generated = datetime.now().isoformat(timespec="seconds")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>HoloDoppler Results Report</title>
<style>
body {{ font-family: Segoe UI, Arial, sans-serif; margin: 28px; color: #17202a; background: #f6f8fb; }}
h1, h2, h3 {{ margin: 0 0 10px; }}
.summary, .card, .metadata {{ background: #ffffff; border: 1px solid #d9e0ea; border-radius: 6px; padding: 16px; margin-bottom: 16px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; }}
.preview-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin: 10px 0; }}
.preview img {{ width: 100%; max-height: 260px; object-fit: contain; background: #111; border-radius: 4px; }}
.preview video {{ width: 100%; max-height: 320px; background: #111; border-radius: 4px; }}
.preview-label {{ color: #536271; font-size: 0.9em; margin-top: 4px; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid #e7ecf3; }}
.note {{ color: #536271; font-size: 0.92em; }}
a {{ color: #0b63ce; margin-right: 10px; }}
</style>
</head>
<body>
<h1>HoloDoppler Results Report</h1>
<div class="summary">
  <p class="note">Generated {html.escape(generated)}.</p>
</div>
<div class="metadata">
  <h2>Processing Metadata</h2>
  <table>{metadata_rows}</table>
</div>
<h2>Saved Outputs</h2>
<div class="grid">
{cards}
</div>
</body>
</html>
"""


def _render_result_card(entry):
    rows = [
        ("Shape", str(entry["shape"])),
        ("Dtype", entry["dtype"]),
    ]
    metrics = "".join(
        f"<tr><td>{html.escape(str(key))}</td><td>{html.escape(str(value))}</td></tr>"
        for key, value in rows
    )
    if entry["links"]:
        previews = _render_existing_output_preview(entry)
    else:
        previews = "".join(_render_preview(preview) for preview in entry["previews"])
        if entry["plot"] is not None:
            previews += _render_preview({"label": "plot", "image": entry["plot"]})
    if not previews:
        previews = '<p class="note">No visual preview available for this output shape.</p>'
    links = "".join(
        f'<a href="{html.escape(href)}" target="_blank" rel="noopener">{html.escape(label)}</a>'
        for label, href in entry["links"]
        if label == "PNG"
    )
    links_html = f"<p>{links}</p>" if links else ""
    return f"""<div class="card">
<h3>{html.escape(entry["name"])}</h3>
{links_html}
<div class="preview-grid">{previews}</div>
<table>{metrics}</table>
</div>"""


def _render_existing_output_preview(entry):
    png_href = _entry_link(entry, "PNG")
    mp4_href = _entry_link(entry, "MP4")
    if mp4_href is None:
        return ""
    poster = f' poster="{html.escape(png_href)}"' if png_href is not None else ""
    return f"""<div class="preview">
<video controls preload="auto" playsinline{poster} src="{html.escape(mp4_href)}"></video>
<div class="preview-label">MP4 preview</div>
</div>"""


def _entry_link(entry, label):
    return next((href for link_label, href in entry["links"] if link_label == label), None)


def _render_preview(preview):
    return f"""<div class="preview">
<img src="{_image_data_uri(preview["image"])}" alt="{html.escape(preview["label"])}">
<div class="preview-label">{html.escape(preview["label"])}</div>
</div>"""


def _report_metadata_rows(parameters, file_reader):
    file_path = str(getattr(file_reader, "file_path", ""))
    selected = {
        "Input": file_path,
        "Pipeline": parameters.get("pipeline_name", ""),
        "First frame": parameters.get("first_frame", ""),
        "End frame": parameters.get("end_frame", ""),
        "Batch size": parameters.get("batch_size", parameters.get("time_window", "")),
        "Batch stride": parameters.get("batch_stride", parameters.get("time_stride", "")),
        "Low frequency": parameters.get("low_freq", ""),
        "High frequency": parameters.get("high_freq", ""),
        "SVD threshold": parameters.get("svd_threshold", ""),
        "Version": f"py{get_version()}",
    }
    return "".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in selected.items()
    )


def _image_data_uri(image):
    from PIL import Image

    arr = np.asarray(image)
    if arr.ndim == 2:
        pil_image = Image.fromarray(arr, mode="L")
    else:
        if arr.shape[-1] == 1:
            arr = np.repeat(arr, 3, axis=-1)
        elif arr.shape[-1] == 2:
            arr = np.concatenate([arr, arr[..., :1]], axis=-1)
        pil_image = Image.fromarray(arr[..., :3], mode="RGB")
    pil_image.thumbnail((640, 640))
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _write_results_report_pdf(pdf_path, entries, parameters, file_reader):
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(pdf_path) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.patch.set_facecolor("white")
        ax = fig.add_subplot(111)
        ax.axis("off")

        lines = [
            "HoloDoppler Results Report",
            "",
            f"Generated: {datetime.now().isoformat(timespec='seconds')}",
            f"Output count: {len(entries)}",
            "",
            "Processing metadata",
        ]
        for key, value in _pdf_metadata_items(parameters, file_reader):
            lines.append(f"{key}: {value}")

        ax.text(0.05, 0.95, "\n".join(lines), va="top", ha="left", fontsize=11, wrap=True)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        for entry in entries:
            images = [preview["image"] for preview in entry["previews"]]
            labels = [preview["label"] for preview in entry["previews"]]
            if entry["plot"] is not None:
                images.append(entry["plot"])
                labels.append("plot")

            fig, axes = plt.subplots(2, 2, figsize=(8.27, 11.69))
            axes = axes.reshape(-1)
            fig.suptitle(entry["name"], fontsize=14)

            metadata_axis = axes[0]
            metadata_axis.axis("off")
            metadata_lines = [
                f"Shape: {entry['shape']}",
                f"Dtype: {entry['dtype']}",
            ]
            metadata_axis.text(
                0.0,
                1.0,
                "\n".join(metadata_lines),
                va="top",
                ha="left",
                fontsize=9,
                wrap=True,
            )

            for axis, image, label in zip(axes[1:], images[:3], labels[:3]):
                if image.ndim == 2:
                    axis.imshow(image, cmap="gray", vmin=0, vmax=255)
                else:
                    axis.imshow(image)
                axis.set_title(label, fontsize=10)
                axis.set_axis_off()

            shown = min(3, len(images))
            if shown == 0:
                axes[1].axis("off")
                axes[1].text(0.5, 0.5, "No visual preview", ha="center", va="center")
                shown = 1

            for axis in axes[1 + shown:]:
                axis.axis("off")

            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)


def _pdf_metadata_items(parameters, file_reader):
    return [
        ("Input", getattr(file_reader, "file_path", "")),
        ("Pipeline", parameters.get("pipeline_name", "")),
        ("First frame", parameters.get("first_frame", "")),
        ("End frame", parameters.get("end_frame", "")),
        ("Batch size", parameters.get("batch_size", parameters.get("time_window", ""))),
        ("Batch stride", parameters.get("batch_stride", parameters.get("time_stride", ""))),
        ("Low frequency", parameters.get("low_freq", "")),
        ("High frequency", parameters.get("high_freq", "")),
        ("SVD threshold", parameters.get("svd_threshold", "")),
        ("Version", f"py{get_version()}"),
    ]


def _chunks(items, size):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def _save_metadata(target_dir, file_reader, parameters):
    """Saves all configuration and versioning files"""
    start_time = time.time()

    # JSON params
    json_path = target_dir / "json" / "parameters_holodoppler.json"
    with open(json_path, "w") as f:
        json.dump(parameters, f, indent=4)

    # Version
    (target_dir / "version_holodoppler.txt").write_text(f"py{get_version()}")

    # Git commit (with error handling)
    try:
        import subprocess
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        info_text = f"Git commit: {commit}\npy{get_version()}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        info_text = "Git commit: Not Available (not a git repo)"
    (target_dir / "git_version.txt").write_text(info_text)

    # Holo-specific metadata
    if hasattr(file_reader, 'ext') and file_reader.ext == ".holo":
        with open(target_dir / "json" / "holovibes_footer.json", "w") as f:
            json.dump(file_reader.file_footer, f, indent=4)
        with open(target_dir / "json" / "holovibes_header.json", "w") as f:
            json.dump(asdict(file_reader.file_header), f, indent=4)

    elapsed = time.time() - start_time
    print(f"Metadata saved in {elapsed:.2f} seconds")

def _save_h5_2(target_dir, save_map, parameters, save_only_list=None):
    """
    Saves raw data to HDF5.
    """
    start_time = time.time()

    target_dir_name = target_dir.name if target_dir.name else "output"
    h5_path = target_dir / "h5" / f"{target_dir_name}_output.h5"

    print(f"Saving H5 to: {h5_path}")

    # No compression for faster writing and lower memory usage
    compression = None

    with h5py.File(h5_path, "w") as f:

        for k, v in save_map.items():
            if save_only_list is not None and k not in save_only_list:
                continue
            dataset_name = _h5_dataset_name(k)
            f.create_dataset(
                dataset_name,
                data=_h5_data(dataset_name, v),
                compression=compression,
            )

        # Save metadata
        f.create_dataset("HD_parameters", data=json.dumps(parameters))
        f.create_dataset("HD_version", data=f"py{get_version()}")

    elapsed = time.time() - start_time
    file_size = h5_path.stat().st_size / (1024**3)
    print(f"H5 saved in {elapsed:.1f} seconds (file size: {file_size:.2f} GB)")

def _save_h5(target_dir, vid, parameters, reg_list, coefs_list):
    """
    Saves raw data to HDF5.

    MEMORY WARNING:
    HDF5 writing can use large amounts of RAM because:
    1. The entire 'vid' array is kept in memory (size = nt * nchannels * h * w * dtype)
    2. HDF5 may buffer data during compression
    3. Each dataset copy uses additional memory
    4. If using compression, more memory is used for the compression buffer

    For a 1000-frame, 4-channel, 512x512 video at float32:
    - vid memory: 1000 * 4 * 512 * 512 * 4 = ~4GB
    - Additional buffers: 500MB - 2GB
    - Total: ~5-6GB RAM required

    To reduce memory:
    - Disable compression (set to None)
    - Use chunking
    - Process in batches
    """
    start_time = time.time()

    target_dir_name = target_dir.name if target_dir.name else "output"
    h5_path = target_dir / "h5" / f"{target_dir_name}_output.h5"

    print(f"Saving H5 to: {h5_path}")
    print(f"   Data shape: {vid.shape}")
    print(f"   Data size: {vid.nbytes / (1024**3):.2f} GB")

    # No compression for faster writing and lower memory usage
    compression = None

    with h5py.File(h5_path, "w") as f:
        # Save moments
        f.create_dataset("moment0", data=np.asarray(vid[:, 0, :, :], dtype=np.float32), compression=compression)
        f.create_dataset("moment1", data=np.asarray(vid[:, 1, :, :], dtype=np.float32), compression=compression)
        f.create_dataset("moment2", data=np.asarray(vid[:, 2, :, :], dtype=np.float32), compression=compression)
        f.create_dataset("moment0ff", data=np.asarray(vid[:, 3, :, :], dtype=np.float32), compression=compression)

        # Save frequency bands
        for k, v in enumerate(parameters.get("frequency_bands", [])):
            f.create_dataset(
                f"band_{v[0]}_{v[1]}",
                data=vid[:, 4 + k, :, :],
                compression=compression,
            )

        # Save metadata
        f.create_dataset("HD_parameters", data=json.dumps(parameters))
        f.create_dataset("HD_version", data=f"py{get_version()}")

        # Save registration data
        if parameters.get("image_registration") and reg_list:
            reg_data = np.array(reg_list, dtype=np.float32)
            f.create_dataset("registration", data=reg_data, compression=compression)
            print(f"   Registration data: {reg_data.shape}")

        # Save Zernike coefficients
        if parameters.get("shack_hartmann") and coefs_list:
            coefs_data = np.stack(coefs_list).astype(np.float32)
            f.create_dataset(
                "zernike_coefs_radians",
                data=coefs_data,
                compression=compression,
            )
            print(f"   Zernike coefficients: {coefs_data.shape}")

    elapsed = time.time() - start_time
    file_size = h5_path.stat().st_size / (1024**3)
    print(f"H5 saved in {elapsed:.1f} seconds (file size: {file_size:.2f} GB)")


def _write_video_fast(
    path,
    frames,
    fps,
    codec="libx264",
    preset=None,
    crf=None,
    quality=None,
    overwrite=True,
    pad_even=True,
):
    """
    Write video with ffmpeg backend.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if overwrite and path.exists():
        path.unlink()

    frames = np.asarray(frames)

    # Validate and normalize frames
    if frames.dtype != np.uint8:
        frames = np.nan_to_num(frames, nan=0, posinf=255, neginf=0)
        frames = np.clip(frames, 0, 255).astype(np.uint8)

    # Validate shape
    if frames.ndim == 3:
        # Grayscale: (T, H, W) - fine
        pass
    elif frames.ndim == 4:
        # Color: (T, H, W, C)
        if frames.shape[-1] == 4:
            frames = frames[..., :3]  # RGBA -> RGB
        elif frames.shape[-1] != 3:
            raise ValueError(f"Invalid color channels: {frames.shape[-1]}, expected 3")
    else:
        raise ValueError(f"Invalid video shape: {frames.shape}, expected 3D or 4D")

    if frames.shape[0] == 0:
        raise ValueError(f"Zero-frame video: {path}")

    # Pad to even dimensions for codec compatibility
    if pad_even and codec in ("libx264", "libx265", "h264", "hevc"):
        frames = _pad_to_even(frames)

    # Build writer parameters
    output_params = ["-y"] if overwrite else []
    if preset is not None:
        output_params += ["-preset", str(preset)]
    if crf is not None:
        output_params += ["-crf", str(crf)]
    if path.suffix.lower() == ".mp4":
        # Put the MP4 index before the media payload so browsers can start
        # playback immediately without requiring an initial seek.
        output_params += ["-movflags", "+faststart"]

    kwargs = {
        "fps": float(fps),
        "codec": codec,
        "macro_block_size": 1,
    }
    if output_params:
        kwargs["output_params"] = output_params
    if quality is not None:
        kwargs["quality"] = quality

    # Write video
    with iio.get_writer(str(path), **kwargs) as writer:
        for frame in frames:
            writer.append_data(frame)
