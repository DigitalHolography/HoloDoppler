from holodoppler.saving import (
    save_preview_images,
    preview_image_from_results,
    save_result_map,
    _get_default_output_path,
    _save_videos,
    _save_h5_2,
    _create_directories,
    _save_pngs,
    _save_metadata,
)
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
from holodoppler.utils import (
    gaussian_flatfield,
    update_from_footer,
    normalize_to_uint8,
    square_cupy,
    stretchlim,
    imadjust,
    temporal_gaussian,
)
from holodoppler.filtering import (
    svd_filter,
    frequency_symmetric_filtering,
    fourier_time_transform,
    corner_compensation,
    pca_time_transform,
)
from holodoppler.moments import moment
from holodoppler.registration import (
    register_images_shifts,
    apply_register_images_shifts,
)
from holodoppler.file_reader import FileReaderFactory


import cupy as cp

# import numpy as np
from cupyx.scipy.ndimage import gaussian_filter

# from cupyx.scipy.ndimage import zoom
from tqdm import tqdm

from pathlib import Path


from collections import defaultdict


def _process_batch(parameters, frames, phase_term=None):
    xp = cp
    fft = cp.fft
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

    if parameters["time_transform"] == "PCA":

        # PCA projection
        holograms = pca_time_transform(cp, holograms, remove_dc=False)

        # Moments
        start, end = parameters["pca_range"]
        return cp.sum(cp.abs(holograms)[start:end], axis=0)
    elif parameters["time_transform"] == "FFT":

        spectrum_f = fourier_time_transform(xp, fft, holograms)

        psd = xp.abs(spectrum_f) ** 2

        idxs, freqs = frequency_symmetric_filtering(
            xp,
            fft,
            psd.shape[0],
            1.0,
            parameters["low_freq"],
            parameters.get("high_freq"),
        )

        return moment(xp, psd[idxs], freqs, 0)


def _process_shack_hartmann_U(parameters, frames):

    fft = cp.fft
    nt, ny, nx = frames.shape

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
    else:
        U = None

    return U


def _process_shack_hartmann_phase(parameters, U, ny, nx, output_dict=None):
    fft = cp.fft

    prop_method = parameters["spatial_propagation"]
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
        ny_s, nx_s, Ny, Nx = U.shape
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

    # if output_dict is not None:

    #     sy, sx, numy, numx = U.shape
    #     U = cp.transpose(U, axes=(0,2,1,3))
    #     output_dict["shack_hartmann_sub_images"] = cp.reshape(U,(numy*sy,numx*sx))

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
            print(coefs)
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


def accumulate_on_frames(
    file_reader, n_accu, first_frame, batch_size, batch_stride, func
):
    U = None
    for i in range(n_accu):
        frames = file_reader.read_frames(
            first_frame=first_frame + i * batch_stride, batch_size=batch_size
        )
        # transfer to gpu
        frames = cp.array(frames, dtype=cp.float32)
        if U is None:
            U = func(frames)
        else:
            if U is dict:
                res = func(frames)
                for k in U.keys():
                    U[k] += res[k]
            else:
                U += func(frames)
    if U is dict:
        for k in U.keys():
            U[k] /= n_accu
    else:
        U /= n_accu
    return U


def preview(file_path, parameters, save_debug=True):
    file_reader = FileReaderFactory.create(file_path)

    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        ny, nx = file_reader.file_header.height, file_reader.file_header.width
        parameters = update_from_footer(parameters, file_reader.file_footer)

    if file_reader.ext == ".cine":
        print("file header :", file_reader.metadata)
    print("parameters : ", parameters)

    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]
    n_accu = parameters["accumulation"]

    if parameters.get("shack_hartmann", False):
        U_tot = accumulate_on_frames(
            file_reader,
            n_accu,
            first_frame,
            batch_size,
            batch_stride,
            lambda frames: _process_shack_hartmann_U(parameters, frames),
        )
    res = {}

    phase_term = None
    if parameters.get("shack_hartmann", False):
        phase_term = _process_shack_hartmann_phase(
            parameters, U_tot, ny, nx, output_dict=res
        )

    Projection_tot = accumulate_on_frames(
        file_reader,
        n_accu,
        first_frame,
        batch_size,
        batch_stride,
        lambda frames: _process_batch(parameters, frames=frames, phase_term=phase_term),
    )

    res_np = {k: cp.asnumpy(v) for k, v in res.items()}

    # transfer to cpu
    res_np["Projection"] = cp.asnumpy(Projection_tot)
    if parameters.get("shack_hartmann", False):
        res_np["shack_hartmann_sub_images"] = cp.asnumpy(U_tot)

    # free gpu ram
    del Projection_tot
    if parameters.get("shack_hartmann", False):
        del U_tot
    cp.get_default_memory_pool().free_all_blocks()

    if save_debug:
        save_preview_images(
            res_np,
            _get_default_output_path(file_reader.file_path) / "preview" / "PCA_ACCU",
            square=parameters.get("square", False),
        )
    return preview_image_from_results(res_np)


def process(file_path, parameters, progress_callback=None):
    file_reader = FileReaderFactory.create(file_path)

    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)
        ny, nx = file_reader.file_header.height, file_reader.file_header.width

    if file_reader.ext == ".cine":
        print("file header :", file_reader.metadata)

    print("parameters : ", parameters)

    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]
    end_frame = parameters.get("end_frame", 0)
    n_accu = parameters["accumulation"]

    if end_frame <= 0:
        end_frame = (
            file_reader.file_header.num_frames
            if file_reader.ext == ".holo"
            else file_reader.TotalImageCount
        )

    if batch_stride >= (end_frame - first_frame):
        num_batch = 1 if batch_size <= (end_frame - first_frame) else 0
    else:
        num_batch = int((end_frame - first_frame) / (batch_stride * n_accu))
    if num_batch <= 0:
        return None

    output = defaultdict(list)

    reg_img = None

    processed_batches = 0

    # Start reading frames
    for i in tqdm(range(num_batch)):

        if parameters.get("shack_hartmann", False):
            U_tot = accumulate_on_frames(
                file_reader,
                n_accu,
                first_frame,
                batch_size,
                batch_stride,
                lambda frames: _process_shack_hartmann_U(parameters, frames),
            )
        res = {}

        phase_term = None
        if parameters.get("shack_hartmann", False):
            phase_term = _process_shack_hartmann_phase(
                parameters, U_tot, ny, nx, output_dict=res
            )

        Projection_tot = accumulate_on_frames(
            file_reader,
            n_accu,
            first_frame + i * batch_stride * n_accu,
            batch_size,
            batch_stride,
            lambda frames: _process_batch(
                parameters, frames=frames, phase_term=phase_term
            ),
        )
        Projection_tot_ff = gaussian_flatfield(
            Projection_tot,
            parameters.get("registration_flatfield_gw", 35.0),
            gaussian_filter,
        )
        if parameters.get("image_registration", False):

            if reg_img is None:
                reg_img = Projection_tot_ff

            shift_y, shift_x = register_images_shifts(
                cp,
                cp.fft,
                reg_img,
                Projection_tot_ff,
                radius=0.8,
                gaussian_sigma=0,
                gaussian_filter=gaussian_filter,
            )

            Projection_tot = apply_register_images_shifts(
                cp, cp.fft, Projection_tot, shift_y, shift_x
            )

            Projection_tot_ff = apply_register_images_shifts(
                cp, cp.fft, Projection_tot_ff, shift_y, shift_x
            )

            res["registration"] = cp.stack([cp.array(shift_y), cp.array(shift_x)])

        for k, v in res.items():
            output[k].append(v)
        output["Projection"].append(Projection_tot)
        output["Projectionff"].append(Projection_tot_ff)
        if parameters.get("shack_hartmann", False):
            output["shack_hartmann_sub_images"].append(U_tot)

        processed_batches += 1
        if progress_callback is not None:
            progress_callback(
                processed_batches,
                num_batch,
                f"Batch {processed_batches}/{num_batch}",
            )

    output = {k: cp.stack(v, axis=0) for k, v in output.items()}

    if parameters.get("square", False):
        output = {k: square_cupy(v) if v.ndim >= 3 else v for k, v in output.items()}

    # transfer to cpu
    output_np = {k: cp.asnumpy(v) for k, v in output.items()}

    del output
    cp.get_default_memory_pool().free_all_blocks()

    target_dir = _get_default_output_path(file_reader.file_path) / "PCA_ACCU"

    if "saving_to_folder" in parameters:
        target_dir = Path(parameters["saving_to_folder"])

    _create_directories(target_dir, "FULL")

    # save_to_h5_list = ["M0ff","M0","M1","M2","shack_hartmann_zernike_coefs", "shack_hartmann_sub_images"] "_bands"

    _save_h5_2(target_dir, output_np, parameters)

    import time

    start_time = time.time()

    if parameters.get("smoothing_gaussian", False):
        smoothing_gaussian_size = parameters.get("smoothing_gaussian_size", 2)
        for k in output_np.keys():
            output_np[k] = temporal_gaussian(
                output_np[k], sigma=smoothing_gaussian_size
            )

    elapsed = time.time() - start_time
    print(f"smoothing_gaussian in {elapsed:.1f} seconds")

    save_result_map(
        target_dir,
        output_np,
        parameters,
        file_reader,
        num_batch=num_batch,
        end_frame=end_frame,
        first_frame=first_frame,
    )
