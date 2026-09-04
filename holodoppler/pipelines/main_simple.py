from collections import defaultdict
from pathlib import Path

import cupy as cp
import numpy as np

# import numpy as np
from cupyx.scipy.ndimage import gaussian_filter

# from cupyx.scipy.ndimage import zoom
from tqdm import tqdm

from holodoppler.file_reader import FileReaderFactory
from holodoppler.filtering import (
    corner_compensation,
    filter_2d,
    fourier_time_transform,
    frequency_symmetric_filtering,
    svd_filter,
)
from holodoppler.moments import moment
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
    _save_h5_2,
    preview_image_from_results,
    save_preview_images,
    save_result_map,
)
from holodoppler.shack_hartmann import (
    calculate_displacements,
    calculate_displacements_graph_laplacian,
    construct_subapertures_angular,
    construct_subapertures_fresnel,
)
from holodoppler.utils import gaussian_flatfield, square_cupy, update_from_footer
from holodoppler.zernike import fit_zernike_angular_spectrum, fit_zernike_fresnel


def _process_batch(parameters, frames, phase_term=None, output_dict=None):
    xp = cp
    fft = cp.fft
    nt_sub = frames.shape[0]
    prop_method = parameters["spatial_propagation"]

    # Propagation
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

    # SVD filtering
    holograms_f = svd_filter(
        xp,
        holograms,
        parameters["svd_threshold"],
        filter_mode=parameters["svd_filter_mode"],
        remove_dc=parameters["svd_remove_dc"],
    )

    del holograms  # Free memory early

    if output_dict is None:
        output_dict = {}

    # Temporal transform
    if parameters.get("temporal_transformation") == "FourierTransform":
        spectrum_f = fourier_time_transform(xp, fft, holograms_f)
        # spectrum_f_angle = fourier_time_transform(xp, fft, xp.angle(holograms_f))
    else:
        spectrum_f = holograms_f

    # Frequency selection
    idxs, freqs = frequency_symmetric_filtering(
        xp,
        fft,
        nt_sub,
        parameters["sampling_freq"],
        parameters["low_freq"],
        parameters.get("high_freq"),
    )
    psd = xp.abs(spectrum_f) ** 2

    # psd_angle = xp.abs(spectrum_f_angle) ** 2

    if parameters.get("corner_compensation", False):
        psd = corner_compensation(xp, psd)

    # Moments
    output_dict["M0"] = moment(xp, psd[idxs], freqs, 0)
    output_dict["M1"] = moment(xp, psd[idxs], freqs, 1)
    output_dict["M2"] = moment(xp, psd[idxs], freqs, 2)
    # output_dict["M3"] = moment(xp, psd[idxs], freqs, 3)
    # output_dict["M4"] = moment(xp, psd[idxs], freqs, 4)
    # output_dict["M5"] = moment(xp, psd[idxs], freqs, 5)
    # output_dict["M6"] = moment(xp, psd[idxs], freqs, 6)
    output_dict["M0ff"] = gaussian_flatfield(
        output_dict["M0"],
        parameters.get("registration_flatfield_gw", 1.0),
        gaussian_filter,
    )

    output_dict["spectrum_line"] = xp.mean(psd, axis=(-2, -1))

    # Frequency bands
    for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
        idxs_band, _ = frequency_symmetric_filtering(
            xp, fft, nt_sub, parameters["sampling_freq"], f1, f2
        )
        band = xp.mean(psd[idxs_band], axis=0)
        output_dict[f"band_{k}_{f1}_{f2}"] = band


def _process_shack_hartmann(parameters, frames, output_dict=None):

    fft = cp.fft
    _, ny, nx = frames.shape

    prop_method = parameters["spatial_propagation"]

    if prop_method == "Fresnel":
        U = construct_subapertures_fresnel(
            cp,
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
            cp,
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

    # Displacement estimation
    if parameters.get("shack_hartmann_graph_laplacian", False):  # Use all the sub aps
        shifts_y, shifts_x = calculate_displacements_graph_laplacian(
            cp,
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
    else:  # Use only the shifts to the central sub ap
        _, _, _, _ = U.shape
        shifts_y, shifts_x = calculate_displacements(
            cp,
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
        U = cp.transpose(U, axes=(0, 2, 1, 3))
        output_dict["shack_hartmann_sub_images"] = cp.reshape(U, (numy * sy, numx * sx))

    del U, frames  # Memory footprint reduction

    # Phase reconstruction
    phase = None
    if parameters.get("shack_hartmann_zernike_fit", True):
        if prop_method == "Fresnel":
            coefs, phase = fit_zernike_fresnel(
                cp,
                ny,
                nx,
                parameters["pixel_pitch"][0],
                parameters["pixel_pitch"][1],
                parameters["wavelength"],
                shifts_y,
                shifts_x,
                parameters.get("shack_hartmann_zernike_fit_modes"),
            )
        elif prop_method == "AngularSpectrum":
            coefs, phase = fit_zernike_angular_spectrum(
                cp,
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

    # Phase reconstruction
    phase = None
    if parameters.get("shack_hartmann_zernike_fit", True):
        if prop_method == "Fresnel":
            coefs, phase = fit_zernike_fresnel(
                cp,
                ny,
                nx,
                parameters["pixel_pitch"][0],
                parameters["pixel_pitch"][1],
                parameters["wavelength"],
                shifts_y,
                shifts_x,
                parameters.get("shack_hartmann_zernike_fit_modes"),
            )
        elif prop_method == "AngularSpectrum":
            coefs, phase = fit_zernike_angular_spectrum(
                cp,
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
        # elif parameters.get("shack_hartmann_southwell_phase_integration", False):
        #     phase = southwell_phase_integration(
        #         bm, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
        #         parameters["wavelength"], shifts_y, shifts_x
        #     )
        if output_dict is not None:
            output_dict["shack_hartmann_zernike_coefs"] = coefs
            output_dict["shack_hartmann_wavefront_phase"] = phase
    else:
        phase = None

    # Phase correction term
    phase_term = None
    if phase is not None:
        phase_term = cp.exp(-1j * phase)
        phase_term = cp.nan_to_num(phase_term, nan=0.0)

    return phase_term


def preview(file_path, parameters, save_debug=True):
    file_reader = FileReaderFactory.create(file_path)

    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)

    if file_reader.ext == ".cine":
        print("file header :", file_reader.metadata)
    print("parameters : ", parameters)

    batch_size = parameters["batch_size"]
    first_frame = parameters["first_frame"]
    frames = file_reader.read_frames(first_frame=first_frame, batch_size=batch_size)

    # transfer to gpu
    frames = cp.array(frames, dtype=cp.float32)

    # 2D filtering
    if parameters.get("filter2d", False):
        frames = filter_2d(cp, cp.fft, frames, parameters["filter2d_low"])

    res = {}

    phase_term = None
    if parameters.get("shack_hartmann", False):
        phase_term = _process_shack_hartmann(parameters, frames, output_dict=res)

    # calc on gpu
    _process_batch(parameters, frames=frames, phase_term=phase_term, output_dict=res)

    if parameters.get("square", False):
        res = {
            k: cp.squeeze(square_cupy(v[cp.newaxis, ...])) if v.ndim == 2 else v
            for k, v in res.items()
        }

    # transfer to cpu
    res_np = {k: cp.asnumpy(v) for k, v in res.items()}

    # free gpu ram
    del res
    cp.get_default_memory_pool().free_all_blocks()

    preview_path = _get_default_output_path(file_reader.file_path) / "preview"

    if save_debug:
        save_preview_images(res_np, preview_path)
        (preview_path / "h5").mkdir(parents=True, exist_ok=True)
        _save_h5_2(preview_path, res_np, parameters)

    return preview_image_from_results(res_np)


def process(file_path, parameters, progress_callback=None):
    file_reader = FileReaderFactory.create(file_path)

    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)

    if file_reader.ext == ".cine":
        print("file header :", file_reader.metadata)

    print("parameters : ", parameters)

    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]
    end_frame = parameters.get("end_frame", 0)
    if end_frame <= 0:
        end_frame = (
            file_reader.file_header.num_frames
            if file_reader.ext == ".holo"
            else file_reader.TotalImageCount
        )

    if batch_stride >= (end_frame - first_frame):
        num_batch = 1 if batch_size <= (end_frame - first_frame) else 0
    else:
        num_batch = int((end_frame - first_frame) / batch_stride)
    if num_batch <= 0:
        return None

    output = defaultdict(list)

    # creating the registration reference image
    M0_reg = None
    if parameters.get("image_registration", False) and (
        parameters.get("registration_ref_first_frame", 0) != 0
        or parameters.get("registration_ref_batch_size", batch_size) != batch_size
    ):
        frames = file_reader.read_frames(
            first_frame=parameters.get("registration_ref_first_frame", 0),
            batch_size=parameters.get("registration_ref_batch_size", batch_size),
        )
        frames = cp.array(frames)
        # 2D filtering
        if parameters.get("filter2d", False):
            frames = filter_2d(cp, cp.fft, frames, parameters["filter2d_low"])
        phase_term = None
        if parameters.get("shack_hartmann", False):
            phase_term = _process_shack_hartmann(parameters, frames)
        res = {}
        _process_batch(parameters, frames, phase_term=phase_term, output_dict=res)
        M0_reg = res["M0ff"].copy()
        print(res.keys())
        del frames, phase_term  # Memory footprint reduction
        res.clear()
        del res

    h2d_stream = cp.cuda.Stream(non_blocking=True)
    # d2h_stream = cp.cuda.Stream(non_blocking=True)
    compute_stream = cp.cuda.Stream(non_blocking=True)

    processed_batches = 0

    PREFETCH_DEPTH = 4  # Number of batches to prefetch ahead (set to 3 or 4)

    # prefetch buffers
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
                    first_frame=first_frame + i * batch_stride, batch_size=batch_size
                )
                d_buffers[prefetch_idx] = cp.asarray(frames)

                h2d_events[prefetch_idx] = cp.cuda.Event()
                h2d_events[prefetch_idx].record(h2d_stream)
                buffer_ready[prefetch_idx] = True

        while buffer_ready[current_idx] and current_idx != prefetch_idx:

            h2d_events[current_idx].synchronize()

            with compute_stream:
                d_current = d_buffers[current_idx]

                # 2D filtering
                if parameters.get("filter2d", False):
                    d_current = filter_2d(cp, cp.fft, d_current, parameters["filter2d_low"])

                res = {}

                phase_term = None
                if parameters.get("shack_hartmann", False):
                    phase_term = _process_shack_hartmann(
                        parameters, d_current, output_dict=res
                    )

                _process_batch(
                    parameters, d_current, phase_term=phase_term, output_dict=res
                )

                if (
                    M0_reg is None
                    and parameters.get("image_registration", False)
                ):  # first batch is used for fixed batch
                    M0_reg = res["M0ff"]

                if M0_reg is not None:
                    shift_y, shift_x = register_images_shifts(
                        cp,
                        cp.fft,
                        M0_reg,
                        res["M0ff"],
                        radius=parameters.get("registration_radius", 0.8),
                        sub_pixel=parameters.get("registration_sub_pixel", False),
                    )

                    for k, v in res.items():
                        if k in ["M0ff", "M0", "M1", "M2"] or "band_" in k:
                            res[k] = apply_register_images_shifts(
                                cp, cp.fft, v, shift_y, shift_x
                            )

                    res["registration"] = cp.stack([cp.array(shift_y), cp.array(shift_x)])

                compute_events[current_idx] = cp.cuda.Event()
                compute_events[current_idx].record(compute_stream)

            compute_events[current_idx].synchronize()

            if res:
                for k, v in res.items():
                    output[k].append(v.get()) # transfer to cpu

            processed_batches += 1
            if progress_callback is not None:
                progress_callback(
                    processed_batches,
                    num_batch,
                    f"Batch {processed_batches}/{num_batch}",
                )

            buffer_ready[current_idx] = False
            d_buffers[current_idx] = None  # Free memory
            current_idx = (current_idx + 1) % PREFETCH_DEPTH

            if processed_batches >= num_batch:
                break

    while buffer_ready[current_idx]:

        h2d_events[current_idx].synchronize()

        with compute_stream:
            d_current = d_buffers[current_idx]

            # 2D filtering
            if parameters.get("filter2d", False):
                d_current = filter_2d(cp, cp.fft, d_current, parameters["filter2d_low"])

            res = {}

            phase_term = None
            if parameters.get("shack_hartmann", False):
                phase_term = _process_shack_hartmann(
                    parameters, d_current, output_dict=res
                )

            _process_batch(
                parameters, d_current, phase_term=phase_term, output_dict=res
            )

            if M0_reg is None and parameters.get("image_registration", False):
                M0_reg = res["M0ff"]

            if M0_reg is not None:
                shift_y, shift_x = register_images_shifts(
                    cp,
                    cp.fft,
                    M0_reg,
                    res["M0ff"],
                    radius=parameters.get("registration_radius", 0.8),
                    sub_pixel=parameters.get("registration_sub_pixel", False),
                )

                for k, v in res.items():
                    if k in ["M0ff", "M0", "M1", "M2"] or "band_" in k:
                        res[k] = apply_register_images_shifts(
                            cp, cp.fft, v, shift_y, shift_x
                        )

                res["registration"] = cp.stack(
                    [cp.array(shift_y), cp.array(shift_x)]
                )

            compute_events[current_idx] = cp.cuda.Event()
            compute_events[current_idx].record(compute_stream)

        compute_events[current_idx].synchronize()

        if res:
            for k, v in res.items():
                output[k].append(v.get()) # transfer to cpu

        processed_batches += 1
        if progress_callback is not None:
            progress_callback(
                processed_batches,
                num_batch,
                f"Batch {processed_batches}/{num_batch}",
            )

        buffer_ready[current_idx] = False
        d_buffers[current_idx] = None
        current_idx = (current_idx + 1) % PREFETCH_DEPTH

        if processed_batches >= num_batch:
            break

    output = {k: np.stack(v, axis=0) for k, v in output.items()}

    if parameters.get("square", False):
        output = {k: square_cupy(cp.array(v)).get() if v.ndim == 3 else v for k, v in output.items()}

    cp.get_default_memory_pool().free_all_blocks()

    target_dir = _get_default_output_path(file_reader.file_path)

    if "saving_to_folder" in parameters:
        target_dir = Path(parameters["saving_to_folder"])

    _create_directories(target_dir, "FULL")

    # renaming for compatibility with Doppler View
    output["moment0"] = output.pop("M0")
    output["moment0ff"] = output.pop("M0ff")
    output["moment1"] = output.pop("M1")
    output["moment2"] = output.pop("M2")

    save_to_h5_list = [
        "moment0ff",
        "moment0",
        "moment1",
        "moment2",
        "shack_hartmann_zernike_coefs",
        "registration",
        "spectrum_line",
    ] + [key for key in output if "band_" in key]

    _save_h5_2(target_dir, output, parameters, save_only_list=save_to_h5_list)
    return save_result_map(
        target_dir,
        output,
        parameters,
        file_reader,
        num_batch=num_batch,
        end_frame=end_frame,
        first_frame=first_frame,
    )
