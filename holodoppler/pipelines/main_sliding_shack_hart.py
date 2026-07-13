from holodoppler.saving import save_preview_images, preview_image_from_results, _get_default_output_path, _save_videos, _save_h5_2, _create_directories, _save_pngs, _save_metadata, _save_reports
from holodoppler.propagation import fresnel_transform, fresnel_transform_with_phase, angular_spectrum_transform, angular_spectrum_transform_with_phase
from holodoppler.shack_hartmann import construct_subapertures_fresnel, construct_subapertures_angular, calculate_displacements, calculate_displacements_graph_laplacian
from holodoppler.zernike import fit_zernike_fresnel, fit_zernike_angular_spectrum
from holodoppler.utils import gaussian_flatfield, update_from_footer, normalize_to_uint8, square_cupy
from holodoppler.filtering import svd_filter, frequency_symmetric_filtering, fourier_time_transform, corner_compensation
from holodoppler.moments import cast_moment_outputs_float32, moment
from holodoppler.registration import register_images_shifts, apply_register_images_shifts
from holodoppler.file_reader import FileReaderFactory


import cupy as cp
# import numpy as np
from cupyx.scipy.ndimage import gaussian_filter
# from cupyx.scipy.ndimage import zoom
from tqdm import tqdm

from collections import defaultdict

def _batch_iterator(num_batch, progress_callback):
    batches = range(num_batch)
    return batches if progress_callback is not None else tqdm(batches)

def _notify_progress(progress_callback, completed, total):
    if progress_callback is not None:
        progress_callback(completed, total, f"Batch {completed}/{total}")

def _process_batch(parameters, frames, phase_term = None, output_dict = None):
    xp = cp
    fft = cp.fft
    nt_sub = frames.shape[0]
    prop_method = parameters["spatial_propagation"]

    # Propagation
    if phase_term is not None:
        if prop_method == "Fresnel":
            holograms = fresnel_transform_with_phase(
                xp, fft, frames, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
                phase_term, use_output_kernel=parameters["Fresnel_use_ouput_kernel"]
            )
        elif prop_method == "AngularSpectrum":
            holograms = angular_spectrum_transform_with_phase(
                xp, fft, frames, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
                phase_term
            )
    else:
        if prop_method == "Fresnel":
            holograms = fresnel_transform(
                xp, fft, frames, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
                use_output_kernel=parameters["Fresnel_use_ouput_kernel"]
            )
        elif prop_method == "AngularSpectrum":
            holograms = angular_spectrum_transform(
                xp, fft, frames, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
            )

    # SVD filtering
    holograms_f = svd_filter(xp, holograms, parameters["svd_threshold"], filter_mode = parameters["svd_filter_mode"], remove_dc = parameters["svd_remove_dc"])

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
        xp, fft, nt_sub, parameters["sampling_freq"], parameters["low_freq"], parameters.get("high_freq")
    )
    psd = xp.abs(spectrum_f) ** 2

    # psd_angle = xp.abs(spectrum_f_angle) ** 2

    if parameters.get("corner_compensation", False):
        psd = corner_compensation(xp, psd)

    # Moments
    output_dict["M0"] = moment(xp, psd[idxs], freqs, 0)
    output_dict["M1"] = moment(xp, psd[idxs], freqs, 1)
    output_dict["M2"] = moment(xp, psd[idxs], freqs, 2)
    output_dict["M0ff"] = gaussian_flatfield(output_dict["M0"], parameters.get("registration_flatfield_gw", 1.0), gaussian_filter)
    cast_moment_outputs_float32(xp, output_dict)

    # Frequency bands
    for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
        idxs_band, _ = frequency_symmetric_filtering(xp, fft, nt_sub, parameters["sampling_freq"], f1, f2)
        band = xp.mean(psd[idxs_band], axis=0)
        output_dict[f"band_{k}_{f1}_{f2}"] = band

def _process_shack_hartmann_U(parameters, frames, output_dict = None):

    fft = cp.fft
    nt, ny, nx = frames.shape

    prop_method = parameters["spatial_propagation"]


    if prop_method == "Fresnel":
        U = construct_subapertures_fresnel(
            cp, fft, frames, parameters["wavelength"], parameters["z"], parameters["pixel_pitch"],
            parameters["low_freq"], parameters.get("high_freq"), parameters["sampling_freq"],
            frames.shape[0], parameters["shack_hartmann_nx_subap"], parameters["shack_hartmann_ny_subap"],
            parameters["shack_hartmann_svd_threshold"]
        )
    elif prop_method == "AngularSpectrum":
        U = construct_subapertures_angular(
            cp, fft, frames, parameters["wavelength"],
            parameters["z"], parameters["pixel_pitch"], parameters["low_freq"], parameters.get("high_freq"),
            parameters["sampling_freq"], frames.shape[0], parameters["shack_hartmann_nx_subap"],
            parameters["shack_hartmann_ny_subap"], parameters["shack_hartmann_svd_threshold"]
        )
    else :
        U = None

    return U

def _process_shack_hartmann_phase(parameters, U, ny, nx, output_dict = None):
    fft = cp.fft

    prop_method = parameters["spatial_propagation"]
    # Displacement estimation
    if parameters.get("shack_hartmann_graph_laplacian", False): # Use all the sub aps
        shifts_y, shifts_x = calculate_displacements_graph_laplacian(
            cp, fft, U,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get("shack_hartmann_deviation_threshold", 3.0),
            shifts_range=parameters.get("shack_hartmann_shifts_pixel_range_threshold", 20.0)
        )
    else: # Use only the shifts to the central sub ap
        ny_s, nx_s, Ny, Nx = U.shape
        shifts_y, shifts_x = calculate_displacements(
            cp, fft, U,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get("shack_hartmann_deviation_threshold", 3.0),
            shifts_range=parameters.get("shack_hartmann_shifts_pixel_range_threshold", 20.0)
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
                cp, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
            )
        elif prop_method == "AngularSpectrum":
            coefs, phase = fit_zernike_angular_spectrum(
                cp, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], parameters["z"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
            )

    # Phase reconstruction
    phase = None
    if parameters.get("shack_hartmann_zernike_fit", True):
        if prop_method == "Fresnel":
            coefs, phase = fit_zernike_fresnel(
                cp, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
            )
        elif prop_method == "AngularSpectrum":
            coefs, phase = fit_zernike_angular_spectrum(
                cp, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], parameters["z"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
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

def preview(file_path, parameters):
    file_reader = FileReaderFactory.create(file_path)

    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)

    if file_reader.ext == ".cine":
        print("file header :", file_reader.metadata)
    print("parameters : ", parameters)

    time_window = parameters["time_window"]
    first_frame = parameters["first_frame"]

    time_slide_delay = parameters["time_slide_range"][0]
    time_slide_repetition = parameters["time_slide_range"][1]

    if time_slide_repetition<= 0:
        time_slide_repetition = 1

    res_tot = {}
    U_tot = None

    for n in range(time_slide_repetition):
        frames = file_reader.read_frames(first_frame=first_frame + n*time_slide_delay, batch_size=time_window)
        # transfer to gpu
        frames = cp.array(frames)
        if parameters.get("shack_hartmann", False):

            U = _process_shack_hartmann_U(parameters, frames)
            if U_tot is None:
                U_tot = U
            else:
                U_tot += U
    del U

    ny, nx = frames.shape[-2:]
    phase_term = None
    if parameters.get("shack_hartmann", False):
        phase_term = _process_shack_hartmann_phase(parameters, U_tot, ny, nx, output_dict=res_tot)

    for n in range(time_slide_repetition):

        res = {}

        frames = file_reader.read_frames(first_frame=first_frame + n*time_slide_delay, batch_size=time_window)
        # transfer to gpu
        frames = cp.array(frames)
        # calc on gpu
        _process_batch(parameters, frames=frames, phase_term=phase_term, output_dict=res)

        for k, v in res.items():
            if k in res_tot:
                res_tot[k] += res[k]
            else:
                res_tot[k] = res[k]

    for k, v in res_tot.items():
        res_tot[k] /= time_slide_repetition

    if U_tot is not None:
        sy, sx, numy, numx = U_tot.shape
        U_tot = cp.transpose(U_tot, axes=(0,2,1,3))
        res_tot["shack_hartmann_sub_images"] = cp.reshape(U_tot,(numy*sy,numx*sx))

    # transfer to cpu
    res_np = {k: cp.asnumpy(v) for k, v in res_tot.items()}

    # free gpu ram
    del res_tot, res
    cp.get_default_memory_pool().free_all_blocks()

    save_preview_images(res_np, _get_default_output_path(file_reader.file_path) / "preview")
    return preview_image_from_results(res_np)


def process(file_path, parameters, progress_callback=None):
    file_reader = FileReaderFactory.create(file_path)

    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)

    if file_reader.ext == ".cine":
        print("file header :", file_reader.metadata)

    print("parameters : ", parameters)

    time_window = parameters["time_window"]
    time_stride = parameters["time_stride"]

    first_frame = parameters["first_frame"]
    end_frame = parameters.get("end_frame", 0)

    time_slide_delay = parameters["time_slide_range"][0]
    time_slide_repetition = parameters["time_slide_range"][1]

    if time_slide_repetition<= 0:
        time_slide_repetition = 1

    if end_frame <= 0:
        end_frame = file_reader.file_header.num_frames if file_reader.ext == ".holo" else file_reader.TotalImageCount

    if time_stride >= (end_frame - first_frame):
        num_batch = 1 if time_window + time_slide_delay*time_slide_repetition <= (end_frame - first_frame) else 0
    else:
        num_batch = int((end_frame - first_frame - time_slide_delay*time_slide_repetition) / time_stride)


    if num_batch <= 0:
        return None

    output = defaultdict(list)

    M0_reg = None

    # Create CUDA streams
    h2d_stream = cp.cuda.Stream(non_blocking=True)
    compute_stream = cp.cuda.Stream(non_blocking=True)

    processed_batches = 0

    # Start reading frames
    for i in _batch_iterator(num_batch, progress_callback):

        res_tot = {}
        U_tot = None

        if parameters.get("shack_hartmann", False):
            for n in range(time_slide_repetition):

                # Start async H2D transfer for this batch
                with h2d_stream:

                    frames = file_reader.read_frames(first_frame = first_frame + i * time_stride + n * time_slide_delay, batch_size = time_window)
                    d_current = cp.asarray(frames)
                    del frames
                    h2d_event = cp.cuda.Event()
                    h2d_event.record(h2d_stream)

                h2d_event.synchronize()

                # Compute current batch on compute stream
                with compute_stream:
                    U = _process_shack_hartmann_U(parameters, d_current)
                    if U_tot is None:
                        U_tot = U
                    else:
                        U_tot += U

            ny, nx = d_current.shape[-2:]
        else:
            ny = nx = None

        phase_term = None
        if U_tot is not None:
            phase_term = _process_shack_hartmann_phase(parameters, U_tot, ny, nx)

        for n in range(time_slide_repetition):

            res = {}

            # Start async H2D transfer for this batch
            with h2d_stream:

                frames = file_reader.read_frames(first_frame = first_frame + i * time_stride + n * time_slide_delay, batch_size = time_window)
                d_current = cp.asarray(frames)
                h2d_event = cp.cuda.Event()
                h2d_event.record(h2d_stream)

            h2d_event.synchronize()

            # Compute current batch on compute stream
            with compute_stream:
                _process_batch(parameters, d_current, phase_term=phase_term, output_dict=res)

                shift_y, shift_x = 0, 0
                if M0_reg is None and parameters["image_registration"]: #first batch is used for fixed batch
                    M0_reg = res["M0ff"]

                if M0_reg is not None:
                    shift_y, shift_x = register_images_shifts(cp, cp.fft, M0_reg, res["M0ff"], radius=0.7, gaussian_sigma=0, gaussian_filter=gaussian_filter)

                for k, v in res.items():
                    if k in ["M0ff","M0","M1","M2"] or "band_" in k : #select the outputs that need the registration from M0ff applied
                        res[k] = apply_register_images_shifts(cp, v, shift_y, shift_x)

                res["registration"] = cp.stack([cp.array(shift_y), cp.array(shift_x)])

                compute_event = cp.cuda.Event()
                compute_event.record(compute_stream)

            # Wait for compute to finish
            compute_event.synchronize()

            for k, v in res.items():
                if k in res_tot:
                    res_tot[k] += res[k]
                else:
                    res_tot[k] = res[k]

        for k, v in res_tot.items():
            output[k].append(res_tot[k] / time_slide_repetition)

        if U_tot is not None:
            sy, sx, numy, numx = U_tot.shape
            U_tot = cp.transpose(U_tot, axes=(0,2,1,3))
            res_tot["shack_hartmann_sub_images"] = cp.reshape(U_tot,(numy*sy,numx*sx))
            output["shack_hartmann_sub_images"].append(res_tot["shack_hartmann_sub_images"])

        processed_batches += 1
        _notify_progress(progress_callback, processed_batches, num_batch)

    output = {k: cp.stack(v, axis=0) for k, v in output.items()}

    if parameters.get("square", False):
        output = {k: square_cupy(v) if v.ndim >=3 else v for k, v in output.items()}

    cast_moment_outputs_float32(cp, output)

    # transfer to cpu
    output_np = {k: cp.asnumpy(v) for k, v in output.items()}

    del output
    cp.get_default_memory_pool().free_all_blocks()

    target_dir = _get_default_output_path(file_reader.file_path)

    _create_directories(target_dir, "FULL")

    # save_to_h5_list = ["M0ff","M0","M1","M2","shack_hartmann_zernike_coefs", "shack_hartmann_sub_images"] "_bands"

    raw_output_np = output_np
    _save_h5_2(target_dir, raw_output_np, parameters)

    output_np = {k: normalize_to_uint8(v) for k, v in raw_output_np.items()}

    # Save videos (sequential to avoid encoding conflicts)
    _save_videos(target_dir, output_np, 30)

    # Save PNGs (parallel)
    _save_pngs(target_dir, output_np)

    # Save metadata (fast)
    _save_metadata(target_dir, file_reader, parameters)

    # Save visual result reports
    _save_reports(target_dir, raw_output_np, output_np, parameters, file_reader)
