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
from holodoppler.get_version import get_version
from holodoppler.propagation import (
    angular_spectrum_transform,
    angular_spectrum_transform_with_phase,
    fresnel_transform,
    fresnel_transform_with_phase,
)
from holodoppler.saving import (
    _create_directories,
    _get_default_output_path,
    _save_metadata,
    apply_contrast_adjustment,
    normalize_to_uint8,
    save_preview_images,
)
from holodoppler.spectral_cube import (
    binned_fft_frequencies,
    centered_ellipse_mask,
    ellipse_median_power,
    estimated_endpoint_bytes,
    log_power_ratio,
    mean_bin_axis,
    window_starts,
)
from holodoppler.utils import update_from_footer


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
    if not np.isfinite(sampling_frequency) or sampling_frequency <= 0:
        raise ValueError("sampling_freq must be a positive finite number")
    if f_bins <= 0:
        raise ValueError("f_bins must be a positive integer")
    parameters.update(
        {
            "batch_size": batch_size,
            "batch_stride": batch_stride,
            "first_frame": first_frame,
            "end_frame": end_frame,
            "sampling_freq": sampling_frequency,
            "f_bins": f_bins,
        }
    )

    if f_bins > batch_size:
        raise ValueError(
            f"f_bins ({f_bins}) cannot exceed batch_size ({batch_size})"
        )

    return file_reader, parameters, starts


def _output_path(file_reader, parameters) -> tuple[Path, Path]:
    target_dir = _get_default_output_path(file_reader.file_path)
    if parameters.get("saving_to_folder"):
        target_dir = Path(parameters["saving_to_folder"])
    _create_directories(target_dir, "FULL")

    filename = parameters.get(
        "spectral_endpoints_filename",
        parameters.get(
            "spectral_cube_filename",
            f"{Path(file_reader.file_path).stem}_spectral_endpoints.h5",
        ),
    )
    filename = Path(filename).name
    if not filename.lower().endswith((".h5", ".hdf5")):
        filename += ".h5"
    return target_dir, target_dir / "h5" / filename


def _create_h5(path, file_reader, parameters, starts):
    ny, nx = file_reader.frame_shape
    f = binned_fft_frequencies(
        parameters["sampling_freq"], parameters["batch_size"], parameters["f_bins"]
    )
    t = (
        starts.astype(np.float64) + (parameters["batch_size"] - 1) / 2.0
    ) / parameters["sampling_freq"]

    handle = h5py.File(path, "w")
    handle.attrs["complete"] = False
    handle.attrs["source_file"] = str(file_reader.file_path)
    handle.attrs["axis_order"] = "t,f"

    signal = handle.create_dataset(
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

    background = handle.create_dataset(
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

    log_ratio = handle.create_dataset(
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

    f_dataset = handle.create_dataset("f", data=f, track_times=False)
    f_dataset.attrs["units"] = "Hz"
    f_dataset.attrs["description"] = "Mean frequency of each full-range FFT bin"
    t_dataset = handle.create_dataset("t", data=t, track_times=False)
    t_dataset.attrs["units"] = "s"
    t_dataset.attrs["description"] = "Temporal-window center from acquisition start"
    frame_start_dataset = handle.create_dataset(
        "frame_start", data=starts, track_times=False
    )
    frame_start_dataset.attrs["units"] = "frame index"

    string_dtype = h5py.string_dtype(encoding="utf-8")
    handle.create_dataset(
        "HD_parameters",
        data=json.dumps(parameters, default=str),
        dtype=string_dtype,
        track_times=False,
    )
    handle.create_dataset(
        "HD_version", data=f"py{get_version()}", dtype=string_dtype, track_times=False
    )
    return handle, signal, background, log_ratio


def _save_endpoint_pngs(h5_path, target_dir, parameters):
    """Save endpoint maps with frequency vertical and time horizontal."""
    png_dir = Path(target_dir) / "png"
    png_dir.mkdir(parents=True, exist_ok=True)
    with h5py.File(h5_path, "r") as handle:
        endpoint_maps = {
            name: np.asarray(handle[name], dtype=np.float32)
            for name in ("S", "S0", "L")
        }

    for name, values in endpoint_maps.items():
        # HDF5 remains (t,f); transposition is only for the PNG display axes.
        display = apply_contrast_adjustment(values.T, parameters)
        path = png_dir / f"{name}.png"
        iio.imwrite(path, normalize_to_uint8(display))
        print(f"Saving: {path}")


def process(file_path, parameters, progress_callback=None):
    """Compute and stream ``S(t,f)``, ``S0(t,f)``, and ``L(t,f)`` to HDF5."""
    file_reader, parameters, starts = _prepare(file_path, parameters)
    target_dir, h5_path = _output_path(file_reader, parameters)

    output_bytes = estimated_endpoint_bytes(len(starts), parameters["f_bins"])
    print(
        "Spectral endpoints: "
        f"S, S0, and L shapes=({len(starts)}, {parameters['f_bins']}) (t,f), "
        f"payload={output_bytes / 1024**2:.2f} MiB"
    )
    print(f"Saving spectral endpoints to: {h5_path}")

    started = time.time()
    handle = None
    try:
        (
            handle,
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

        handle.attrs.modify("complete", True)
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
