import numpy as np
from collections import defaultdict
from pathlib import Path

import holodoppler.backend as backend
from tqdm import tqdm

from holodoppler.saving import save_preview_images, save_outputs, get_default_output_path, save_h5
from holodoppler.propagation import (
    fresnel_transform,
    fresnel_transform_with_phase,
    angular_spectrum_transform,
    angular_spectrum_transform_with_phase,
)
from holodoppler.shack_hartmann import (
    construct_subapertures_fresnel,
    construct_subapertures_angular,
    calculate_displacements,
    calculate_displacements_graph_laplacian,
)
from holodoppler.zernike import fit_zernike_fresnel, fit_zernike_angular_spectrum
from holodoppler.utils import gaussian_flatfield, update_from_holo_footer, resize_frames
from holodoppler.filtering import (
    filter_2d,
    svd_filter,
    frequency_symmetric_filtering,
    fourier_time_transform,
    corner_compensation,
)
from holodoppler.moments import moment
from holodoppler.registration import (
    register_images_shifts,
    apply_register_images_shifts,
)
from holodoppler.file_reader import FileReaderFactory


def _process_batch(parameters, frames, phase_term=None, output_dict=None):
    xp = backend.xp
    fft = backend.fft
    nt_sub = frames.shape[0]
    prop_method = parameters["spatial_propagation"]

    if phase_term is not None:
        if prop_method == "Fresnel":
            holograms = fresnel_transform_with_phase(
                xp,
                fft,
                frames,
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["wavelength"],
                phase_term,
                use_output_kernel=parameters["Fresnel_use_ouput_kernel"],
            )
        elif prop_method == "AngularSpectrum":
            holograms = angular_spectrum_transform_with_phase(
                xp,
                fft,
                frames,
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["wavelength"],
                phase_term,
            )
        else:
            raise ValueError(f"Unknown propagation method: {prop_method!r}")
    else:
        if prop_method == "Fresnel":
            holograms = fresnel_transform(
                xp,
                fft,
                frames,
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["wavelength"],
                use_output_kernel=parameters["Fresnel_use_ouput_kernel"],
            )
        elif prop_method == "AngularSpectrum":
            holograms = angular_spectrum_transform(
                xp,
                fft,
                frames,
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["wavelength"],
            )
        else:
            raise ValueError(f"Unknown propagation method: {prop_method!r}")

    holograms_f = svd_filter(
        holograms,
        parameters["svd_threshold"],
        filter_mode=parameters["svd_filter_mode"],
        remove_dc=parameters["svd_remove_dc"],
    )
    del holograms

    if output_dict is None:
        output_dict = {}

    if parameters.get("temporal_transformation") == "FourierTransform":
        spectrum_f = fourier_time_transform(xp, fft, holograms_f)
    else:
        spectrum_f = holograms_f

    idxs, freqs = frequency_symmetric_filtering(
        xp,
        fft,
        nt_sub,
        parameters["sampling_freq"],
        parameters["low_freq"],
        parameters.get("high_freq"),
    )

    psd = xp.abs(spectrum_f) ** 2

    if parameters.get("corner_compensation", False):
        psd = corner_compensation(xp, psd)

    output_dict["M0"] = moment(xp, psd[idxs], freqs, 0)
    output_dict["M1"] = moment(xp, psd[idxs], freqs, 1)
    output_dict["M2"] = moment(xp, psd[idxs], freqs, 2)

    output_dict["M0ff"] = gaussian_flatfield(
        output_dict["M0"],
        parameters.get("registration_flatfield_gw", 1.0),
        backend.gaussian_filter,
    )

    output_dict["spectrum_line"] = xp.mean(psd, axis=(-2, -1))

    for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
        idxs_band, _ = frequency_symmetric_filtering(
            xp, fft, nt_sub, parameters["sampling_freq"], f1, f2
        )
        output_dict[f"band_{k}_{f1}_{f2}"] = xp.mean(psd[idxs_band], axis=0)

    return output_dict


def _process_shack_hartmann(parameters, frames, output_dict=None):
    xp = backend.xp
    fft = backend.fft
    nt, ny, nx = frames.shape
    prop_method = parameters["spatial_propagation"]

    if prop_method == "Fresnel":
        U = construct_subapertures_fresnel(
            xp,
            fft,
            frames,
            parameters["wavelength"],
            parameters["z"],
            parameters["pixel_pitch"],
            parameters["low_freq"],
            parameters.get("high_freq"),
            parameters["sampling_freq"],
            frames.shape[0],
            parameters["shack_hartmann_nx_subap"],
            parameters["shack_hartmann_ny_subap"],
            parameters["shack_hartmann_svd_threshold"],
        )
    elif prop_method == "AngularSpectrum":
        U = construct_subapertures_angular(
            xp,
            fft,
            frames,
            parameters["wavelength"],
            parameters["z"],
            parameters["pixel_pitch"],
            parameters["low_freq"],
            parameters.get("high_freq"),
            parameters["sampling_freq"],
            frames.shape[0],
            parameters["shack_hartmann_nx_subap"],
            parameters["shack_hartmann_ny_subap"],
            parameters["shack_hartmann_svd_threshold"],
        )
    else:
        raise ValueError(f"Unknown propagation method: {prop_method!r}")

    if parameters.get("shack_hartmann_graph_laplacian", False):
        shifts_y, shifts_x = calculate_displacements_graph_laplacian(
            xp,
            fft,
            U,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get(
                "shack_hartmann_deviation_threshold", 3.0
            ),
            shifts_range=parameters.get(
                "shack_hartmann_shifts_pixel_range_threshold", 20.0
            ),
        )
    else:
        shifts_y, shifts_x = calculate_displacements(
            xp,
            fft,
            U,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get(
                "shack_hartmann_deviation_threshold", 3.0
            ),
            shifts_range=parameters.get(
                "shack_hartmann_shifts_pixel_range_threshold", 20.0
            ),
        )

    if output_dict is not None:
        sy, sx, numy, numx = U.shape
        U = xp.transpose(U, axes=(0, 2, 1, 3))
        output_dict["shack_hartmann_sub_images"] = xp.reshape(U, (numy * sy, numx * sx))

    del U, frames

    phase = None
    coefs = None

    if parameters.get("shack_hartmann_zernike_fit", True):
        if prop_method == "Fresnel":
            coefs, phase = fit_zernike_fresnel(
                xp,
                ny,
                nx,
                parameters["pixel_pitch"][0],
                parameters["pixel_pitch"][1],
                parameters["wavelength"],
                shifts_y,
                shifts_x,
                parameters.get("shack_hartmann_zernike_fit_modes"),
            )
        else:
            coefs, phase = fit_zernike_angular_spectrum(
                xp,
                ny,
                nx,
                parameters["pixel_pitch"][0],
                parameters["pixel_pitch"][1],
                parameters["wavelength"],
                parameters["z"],
                shifts_y,
                shifts_x,
                parameters.get("shack_hartmann_zernike_fit_modes"),
            )

        if output_dict is not None:
            output_dict["shack_hartmann_zernike_coefs"] = coefs
            output_dict["shack_hartmann_wavefront_phase"] = phase

    if phase is None:
        return None

    phase_term = xp.exp(-1j * phase)
    return xp.nan_to_num(phase_term, nan=0.0)


def _process_one_batch(parameters, frames, M0_reg=None):
    """Process one batch on the active backend."""
    if parameters.get("filter2d", False):
        frames = filter_2d(
            backend.xp,
            backend.fft,
            frames,
            parameters["filter2d_low"],
        )

    res = {}
    phase_term = None

    if parameters.get("shack_hartmann", False):
        phase_term = _process_shack_hartmann(
            parameters,
            frames,
            output_dict=res,
        )

    _process_batch(
        parameters,
        frames,
        phase_term=phase_term,
        output_dict=res,
    )

    if M0_reg is None and parameters.get("image_registration", False):
        M0_reg = res["M0ff"]

    if M0_reg is not None:
        shift_y, shift_x = register_images_shifts(
            backend.xp,
            backend.fft,
            M0_reg,
            res["M0ff"],
            radius=parameters["registration_radius"],
            sub_pixel=parameters["registration_sub_pixel"],
        )

        for key, value in list(res.items()):
            if key in {"M0ff", "M0", "M1", "M2"} or "band_" in key:
                res[key] = apply_register_images_shifts(
                    backend.xp,
                    backend.fft,
                    value,
                    shift_y,
                    shift_x,
                )

        res["registration"] = backend.xp.stack(
            [
                backend.xp.asarray(shift_y),
                backend.xp.asarray(shift_x),
            ]
        )

    return res, M0_reg


def _append_numpy_results(output, res):
    for key, value in res.items():
        output[key].append(backend.to_numpy(value))


def preview(file_path, parameters):
    file_reader = FileReaderFactory.create(file_path)

    print("previewing file :", file_path)

    if file_reader.extension == ".holo":
        print("file header :", file_reader.header)
        parameters = update_from_holo_footer(parameters, file_reader.footer)

    if file_reader.extension == ".cine":
        print("file header :", file_reader.metadata)

    print("parameters : ", parameters)

    frames = file_reader.read_frames(
        first_frame=parameters["first_frame"],
        batch_size=parameters["batch_size"],
    )
    frames = backend.to_backend(frames).astype(backend.xp.float32, copy=False)

    if parameters.get("filter2d", False):
        frames = filter_2d(
            backend.xp,
            backend.fft,
            frames,
            parameters["filter2d_low"],
        )

    res = {}
    phase_term = None

    if parameters.get("shack_hartmann", False):
        phase_term = _process_shack_hartmann(parameters, frames, output_dict=res)

    _process_batch(
        parameters,
        frames,
        phase_term=phase_term,
        output_dict=res,
    )

    if parameters.get("square", False):
        res = {k: resize_frames(v, max(v.shape[-2:]), max(v.shape[-2:])) if v.ndim==2 else v for k, v in res.items()}

    res_np = {k: backend.to_numpy(v) for k, v in res.items()}

    del res
    backend.clear_gpu_memory()

    save_dir = get_default_output_path(file_reader.file_path) / "preview"
    save_preview_images(res_np, save_dir, square=True)
    save_h5(save_dir, res_np, parameters)

    return res_np


def process(file_path, parameters):
    file_reader = FileReaderFactory.create(file_path)

    if file_reader.extension == ".holo":
        print("file header :", file_reader.header)
        parameters = update_from_holo_footer(parameters, file_reader.footer)

    if file_reader.extension == ".cine":
        print("file header :", file_reader.metadata)

    print("parameters : ", parameters)

    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]

    end_frame = parameters.get("end_frame", 0)
    if end_frame <= 0:
        end_frame = (
            file_reader.total_frames
        )

    if batch_stride >= (end_frame - first_frame):
        num_batch = 1 if batch_size <= (end_frame - first_frame) else 0
    else:
        num_batch = int((end_frame - first_frame) / batch_stride)

    if num_batch <= 0:
        return

    output = defaultdict(list)
    M0_reg = None

    # Build the registration reference once, using the active backend.
    if parameters.get("image_registration", False) and (
        parameters["registration_ref_first_frame"] != 0
        or parameters["registration_ref_batch_size"] != parameters["batch_size"]
    ):
        ref_frames = file_reader.read_frames(
            first_frame=parameters["registration_ref_first_frame"],
            batch_size=parameters["registration_ref_batch_size"],
        )
        ref_frames = backend.to_backend(ref_frames)

        ref_res, _ = _process_one_batch(
            parameters,
            ref_frames,
            M0_reg=None,
        )
        M0_reg = ref_res["M0ff"].copy()

        del ref_frames, ref_res
        backend.clear_gpu_memory()

    # NumPy/CPU path: no CUDA streams or events are created.
    if not backend.is_gpu:
        for i in tqdm(range(num_batch)):
            frames = file_reader.read_frames(
                first_frame=first_frame + i * batch_stride,
                batch_size=batch_size,
            )
            frames = backend.to_backend(frames)

            res, M0_reg = _process_one_batch(
                parameters,
                frames,
                M0_reg=M0_reg,
            )
            _append_numpy_results(output, res)

            del frames, res

    else:
        # CuPy path: retain asynchronous host-to-device prefetching.
        h2d_stream = backend.xp.cuda.Stream(non_blocking=True)
        compute_stream = backend.xp.cuda.Stream(non_blocking=True)

        PREFETCH_DEPTH = 4
        d_buffers = [None] * PREFETCH_DEPTH
        h2d_events = [None] * PREFETCH_DEPTH
        compute_events = [None] * PREFETCH_DEPTH
        buffer_ready = [False] * PREFETCH_DEPTH
        current_idx = 0
        processed_batches = 0

        for i in tqdm(range(num_batch + PREFETCH_DEPTH)):
            prefetch_idx = i % PREFETCH_DEPTH

            if i < num_batch:
                with h2d_stream:
                    frames = file_reader.read_frames(
                        first_frame=first_frame + i * batch_stride,
                        batch_size=batch_size,
                    )
                    d_buffers[prefetch_idx] = backend.xp.asarray(frames)
                    h2d_events[prefetch_idx] = backend.xp.cuda.Event()
                    h2d_events[prefetch_idx].record(h2d_stream)
                    buffer_ready[prefetch_idx] = True

            while buffer_ready[current_idx] and current_idx != prefetch_idx:
                h2d_events[current_idx].synchronize()

                with compute_stream:
                    d_current = d_buffers[current_idx]
                    res, M0_reg = _process_one_batch(
                        parameters,
                        d_current,
                        M0_reg=M0_reg,
                    )
                    compute_events[current_idx] = backend.xp.cuda.Event()
                    compute_events[current_idx].record(compute_stream)

                compute_events[current_idx].synchronize()
                _append_numpy_results(output, res)

                processed_batches += 1
                buffer_ready[current_idx] = False
                d_buffers[current_idx] = None
                current_idx = (current_idx + 1) % PREFETCH_DEPTH

                if processed_batches >= num_batch:
                    break

            if processed_batches >= num_batch:
                break

        while buffer_ready[current_idx]:
            h2d_events[current_idx].synchronize()

            with compute_stream:
                d_current = d_buffers[current_idx]
                res, M0_reg = _process_one_batch(
                    parameters,
                    d_current,
                    M0_reg=M0_reg,
                )
                compute_events[current_idx] = backend.xp.cuda.Event()
                compute_events[current_idx].record(compute_stream)

            compute_events[current_idx].synchronize()
            _append_numpy_results(output, res)

            processed_batches += 1
            buffer_ready[current_idx] = False
            d_buffers[current_idx] = None
            current_idx = (current_idx + 1) % PREFETCH_DEPTH

            if processed_batches >= num_batch:
                break

    output = {key: np.stack(values, axis=0) for key, values in output.items()}

    if parameters.get("square", False):
        output = {
            key: resize_frames(value,max(value.shape[-2:]),max(value.shape[-2:])) if value.ndim == 3 else value
            for key, value in output.items()
        }

    backend.clear_gpu_memory()

    # Renaming for compatibility with Doppler View.
    output["moment0"] = output.pop("M0")
    output["moment0ff"] = output.pop("M0ff")
    output["moment1"] = output.pop("M1")
    output["moment2"] = output.pop("M2")

    save_outputs(
        file_reader=file_reader,
        output=output,
        parameters=parameters,
    )
