"""Stream a registered, reduced-resolution Doppler spectrum to HDF5."""

from __future__ import annotations

import json
from pathlib import Path
import time

import cupy as cp
from cupyx.scipy.ndimage import gaussian_filter
import h5py
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
from holodoppler.registration import (
    apply_register_images_shifts,
    register_images_shifts,
)
from holodoppler.saving import (
    _create_directories,
    _get_default_output_path,
    _save_metadata,
    normalize_to_uint8,
    save_spectral_cube_avis,
    save_preview_images,
)
from holodoppler.spectral_cube import (
    binned_fft_frequencies,
    estimated_cube_bytes,
    mean_bin_axis,
    spatial_block_mean,
    window_starts,
)
from holodoppler.utils import gaussian_flatfield, update_from_footer


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
    """Return frequency-binned PSD planes and the full-resolution M0 flatfield."""
    holograms = _propagate(parameters, frames, phase_term=phase_term)
    del frames

    if parameters.get("svd_filter", True):
        holograms = svd_filter(
            cp,
            holograms,
            parameters["svd_threshold"],
            filter_mode=parameters.get("svd_filter_mode", "number_of_values"),
            remove_dc=parameters.get("svd_remove_dc", True),
        )

    spectrum = fourier_time_transform(cp, cp.fft, holograms)
    del holograms
    psd = cp.square(cp.abs(spectrum)).astype(cp.float32, copy=False)
    del spectrum

    if parameters.get("corner_compensation", False):
        psd = corner_compensation(cp, psd).astype(cp.float32, copy=False)

    moment0 = cp.sum(psd, axis=0, dtype=cp.float32)
    moment0ff = gaussian_flatfield(
        moment0,
        parameters.get("registration_flatfield_gw", 35.0),
        gaussian_filter,
    ).astype(cp.float32, copy=False)
    del moment0

    psd = cp.fft.fftshift(psd, axes=0)
    # The same spatial translation is applied at every f, so frequency averaging
    # commutes with registration and halves the default registration workload.
    psd = mean_bin_axis(cp, psd, parameters["f_bins"], axis=0)
    return psd.astype(cp.float32, copy=False), moment0ff


def _phase_term(parameters, frames):
    if not parameters.get("shack_hartmann", False):
        return None

    # Reuse the correction path from the simple pipeline without duplicating it.
    from holodoppler.pipelines.main_simple import _process_shack_hartmann

    return _process_shack_hartmann(parameters, frames)


def _registered_and_binned_window(parameters, frames, fixed_moment0ff):
    phase_term = _phase_term(parameters, frames)
    psd, moving_moment0ff = _process_spectral_window(
        parameters,
        frames,
        phase_term=phase_term,
    )
    del phase_term

    shift_y = 0.0
    shift_x = 0.0
    if parameters.get("image_registration", True):
        if fixed_moment0ff is None:
            fixed_moment0ff = moving_moment0ff.copy()
        else:
            shift_y, shift_x = register_images_shifts(
                cp,
                cp.fft,
                fixed_moment0ff,
                moving_moment0ff,
                radius=parameters.get("registration_radius", 0.8),
                integer_translation=False,
            )
            psd = apply_register_images_shifts(
                cp,
                psd,
                shift_y,
                shift_x,
                fft=cp.fft,
                integer_translation=False,
            )
    del moving_moment0ff

    psd = spatial_block_mean(
        cp,
        psd,
        parameters["ratio_y"],
        parameters["ratio_x"],
    ).astype(cp.float32, copy=False)
    return psd, fixed_moment0ff, (float(shift_y), float(shift_x))


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
    ratio_y = int(parameters.get("ratio_y", 8))
    ratio_x = int(parameters.get("ratio_x", 8))
    if not np.isfinite(sampling_frequency) or sampling_frequency <= 0:
        raise ValueError("sampling_freq must be a positive finite number")
    if f_bins <= 0:
        raise ValueError("f_bins must be a positive integer")
    if ratio_y <= 0 or ratio_x <= 0:
        raise ValueError("ratio_y and ratio_x must be positive integers")
    parameters.update(
        {
            "batch_size": batch_size,
            "batch_stride": batch_stride,
            "first_frame": first_frame,
            "end_frame": end_frame,
            "sampling_freq": sampling_frequency,
            "f_bins": f_bins,
            "ratio_y": ratio_y,
            "ratio_x": ratio_x,
        }
    )

    ny, nx = file_reader.frame_shape
    if ny % ratio_y or nx % ratio_x:
        raise ValueError(
            "Input frame dimensions must be divisible by ratio_y and ratio_x: "
            f"input=(y={ny}, x={nx}), ratios=(y={ratio_y}, x={ratio_x})"
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
        "spectral_cube_filename",
        f"{Path(file_reader.file_path).stem}_spectral_cube.h5",
    )
    filename = Path(filename).name
    if not filename.lower().endswith((".h5", ".hdf5")):
        filename += ".h5"
    return target_dir, target_dir / "h5" / filename


def _create_h5(path, file_reader, parameters, starts):
    ny, nx = file_reader.frame_shape
    ratio_y = parameters["ratio_y"]
    ratio_x = parameters["ratio_x"]
    output_y = ny // ratio_y
    output_x = nx // ratio_x
    f = binned_fft_frequencies(
        parameters["sampling_freq"], parameters["batch_size"], parameters["f_bins"]
    )
    t = (
        starts.astype(np.float64) + (parameters["batch_size"] - 1) / 2.0
    ) / parameters["sampling_freq"]

    handle = h5py.File(path, "w")
    handle.attrs["complete"] = False
    handle.attrs["source_file"] = str(file_reader.file_path)
    handle.attrs["axis_order"] = "t,f,y,x"

    cube = handle.create_dataset(
        "S",
        shape=(len(starts), len(f), output_y, output_x),
        dtype=np.float32,
        chunks=None,
        compression=None,
        track_times=False,
    )
    cube.attrs["axis_order"] = "t,f,y,x"
    cube.attrs["description"] = "Registered, spatially and spectrally averaged PSD"
    cube.attrs["dtype"] = "float32"
    registration_enabled = bool(parameters.get("image_registration", True))
    cube.attrs["spatial_registration"] = registration_enabled
    cube.attrs["registration_interpolation"] = (
        "subpixel Fourier shift" if registration_enabled else "none"
    )
    cube.attrs["svd_filter"] = bool(parameters.get("svd_filter", True))
    cube.attrs["temporal_window"] = "rectangular"
    cube.attrs["frequency_binning"] = "contiguous mean"
    cube.attrs["ratio_y"] = ratio_y
    cube.attrs["ratio_x"] = ratio_x

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

    x = (np.arange(output_x, dtype=np.float64) + 0.5) * ratio_x - 0.5
    y = (np.arange(output_y, dtype=np.float64) + 0.5) * ratio_y - 0.5
    x_dataset = handle.create_dataset("x", data=x, track_times=False)
    y_dataset = handle.create_dataset("y", data=y, track_times=False)
    x_dataset.attrs["units"] = "input pixel"
    y_dataset.attrs["units"] = "input pixel"

    registration = handle.create_dataset(
        "registration",
        shape=(len(starts), 2),
        dtype=np.float32,
        chunks=None,
        compression=None,
        track_times=False,
    )
    registration.attrs["components"] = "shift_y,shift_x"
    registration.attrs["units"] = "input pixel"
    registration.attrs["method"] = (
        "subpixel intensity correlation" if registration_enabled else "none"
    )

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
    return handle, cube, registration


def process(file_path, parameters, progress_callback=None):
    """Compute and stream ``S(t, f, y, x)`` to an uncompressed HDF5 file."""
    file_reader, parameters, starts = _prepare(file_path, parameters)
    target_dir, h5_path = _output_path(file_reader, parameters)

    ny, nx = file_reader.frame_shape
    output_y = ny // parameters["ratio_y"]
    output_x = nx // parameters["ratio_x"]
    output_bytes = estimated_cube_bytes(
        len(starts), parameters["f_bins"], output_y, output_x
    )
    print(
        "Spectral cube: "
        f"shape=({len(starts)}, {parameters['f_bins']}, {output_y}, {output_x}) "
        "(t,f,y,x), "
        f"payload={output_bytes / 1024**3:.2f} GiB"
    )
    print(f"Saving spectral cube to: {h5_path}")

    started = time.time()
    fixed_moment0ff = None
    handle = None
    try:
        handle, cube, registration = _create_h5(
            h5_path, file_reader, parameters, starts
        )
        for index, frame_start in enumerate(tqdm(starts, desc="Spectral cube")):
            frames = file_reader.read_frames(
                first_frame=int(frame_start), batch_size=parameters["batch_size"]
            )
            frames = cp.asarray(frames, dtype=cp.float32)
            if parameters.get("filter2d", False):
                frames = filter_2d(
                    cp, cp.fft, frames, parameters.get("filter2d_low", 0.03)
                )

            reduced, fixed_moment0ff, shifts = _registered_and_binned_window(
                parameters, frames, fixed_moment0ff
            )
            cube[index] = cp.asnumpy(reduced)
            registration[index] = shifts
            del reduced

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

    save_spectral_cube_avis(h5_path, target_dir, parameters)
    _save_metadata(target_dir, file_reader, parameters)
    elapsed = time.time() - started
    print(f"Spectral cube completed in {elapsed:.1f} seconds")
    return h5_path


def preview(file_path, parameters, save_debug=True):
    """Return integrated power from the first reduced spectral window."""
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

        reduced, _fixed_moment0ff, _shifts = _registered_and_binned_window(
            parameters, frames, None
        )
        integrated_power = cp.asnumpy(cp.mean(reduced, axis=0))
        preview_image = normalize_to_uint8(integrated_power)

        if save_debug:
            if parameters.get("saving_to_folder"):
                preview_path = Path(parameters["saving_to_folder"]) / "preview"
            else:
                preview_path = (
                    _get_default_output_path(file_reader.file_path) / "preview"
                )
            save_preview_images(
                {"spectral_cube_integrated_power": preview_image}, preview_path
            )
    finally:
        if hasattr(file_reader, "close"):
            file_reader.close()
        cp.get_default_memory_pool().free_all_blocks()
    return preview_image
