import os

# Set these BEFORE importing numpy/scipy
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"  # For Accelerate framework (macOS)
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import numpy as np
import scipy
from multiprocessing import Pool, cpu_count
from functools import partial
from tqdm import tqdm
from pathlib import Path
from collections import defaultdict
from scipy.ndimage import gaussian_filter

# Assume these imports are now NumPy‑based
from holodoppler.saving import save_preview_images, _get_default_output_path, _save_videos, _save_h5_2, _create_directories, _save_pngs, _save_metadata
from holodoppler.propagation import fresnel_transform, fresnel_transform_with_phase, angular_spectrum_transform, angular_spectrum_transform_with_phase
from holodoppler.shack_hartmann import construct_subapertures_fresnel, construct_subapertures_angular, calculate_displacements, calculate_displacements_graph_laplacian
from holodoppler.zernike import fit_zernike_fresnel, fit_zernike_angular_spectrum
from holodoppler.utils import gaussian_flatfield, update_from_footer, normalize_to_uint8, square_cupy, stretchlim, imadjust, temporal_gaussian
from holodoppler.filtering import svd_filter, frequency_symmetric_filtering, fourier_time_transform, corner_compensation
from holodoppler.moments import moment
from holodoppler.registration import register_images_shifts, apply_register_images_shifts
from holodoppler.file_reader import FileReaderFactory

# ----------------------------------------------------------------------
# Worker function for processing a single batch (used by multiprocessing)
# ----------------------------------------------------------------------
def _process_batch_worker(batch_index, file_path, parameters, first_frame, batch_stride, batch_size):
    """
    Reads one batch from the file, computes all moments (and Shack‑Hartmann if enabled),
    and returns a dictionary of NumPy arrays for that batch.
    """
    file_reader = FileReaderFactory.create(file_path)
    start = first_frame + batch_index * batch_stride
    frames = file_reader.read_frames(first_frame=start, batch_size=batch_size)
    frames = np.array(frames, dtype=np.float32)

    # Local references (using NumPy)
    res = {}

    # 1. Shack‑Hartmann (if requested) – returns phase_term for propagation
    phase_term = None
    if parameters.get("shack_hartmann", False):
        phase_term = _process_shack_hartmann(parameters, frames, output_dict=res)

    # 2. Main batch processing (propagation, SVD, temporal transform, moments)
    _process_batch(parameters, frames, phase_term=phase_term, output_dict=res)

    # All returned arrays are NumPy arrays (from the helper functions)
    return res

# ----------------------------------------------------------------------
# preview – unchanged except for removing CuPy and using NumPy
# ----------------------------------------------------------------------
def preview(file_path, parameters):
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

    # Use NumPy instead of CuPy
    frames = np.array(frames, dtype=np.float32)

    res = {}

    phase_term = None
    if parameters.get("shack_hartmann", False):
        phase_term = _process_shack_hartmann(parameters, frames, output_dict=res)

    _process_batch(parameters, frames=frames, phase_term=phase_term, output_dict=res)

    # (No GPU memory freeing needed)
    save_preview_images(res, _get_default_output_path(file_reader.file_path) / "preview" / "SIMPLE_NUMPY")


# ----------------------------------------------------------------------
# process – rewritten to use multiprocessing and NumPy
# ----------------------------------------------------------------------
def process(file_path, parameters):
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
        end_frame = file_reader.file_header.num_frames if file_reader.ext == ".holo" else file_reader.TotalImageCount

    if batch_stride >= (end_frame - first_frame):
        num_batch = 1 if batch_size <= (end_frame - first_frame) else 0
    else:
        num_batch = int((end_frame - first_frame) / batch_stride)
    if num_batch <= 0:
        return None

    # ------------------------------------------------------------------
    # Parallel processing of batches using multiprocessing.Pool
    # ------------------------------------------------------------------
    n_workers = parameters.get("num_workers", min(int(cpu_count()//2), num_batch)) #  # use all available cores, capped by number of batches
    worker_func = partial(
        _process_batch_worker,
        file_path=file_path,
        parameters=parameters,
        first_frame=first_frame,
        batch_stride=batch_stride,
        batch_size=batch_size
    )

    # Collect results from all batches in parallel
    with Pool(processes=n_workers) as pool:
        # tqdm is not multiprocessing‑safe, so we wrap it manually if needed
        batch_results = list(tqdm(pool.imap(worker_func, range(num_batch)), total=num_batch))

    # Combine results: stack arrays along the time axis (first dimension)
    combined = defaultdict(list)
    for res in batch_results:
        for k, v in res.items():
            combined[k].append(v)

    # Stack each key into a single NumPy array
    output = {k: np.stack(v, axis=0) for k, v in combined.items()}

    # ------------------------------------------------------------------
    # Image registration using the first batch as reference
    # ------------------------------------------------------------------
    if parameters.get("image_registration", False) and "M0ff" in output:
        # Reference from first batch
        M0_reg = output["M0ff"][0]  # shape (H, W)

        # List of keys that need registration applied
        reg_keys = [k for k in output.keys() if k in ["M0ff", "M0", "M1", "M2"] or k.startswith("band_")]

        # Compute shifts for each batch and apply to all registered keys
        shifts_y = []
        shifts_x = []
        for i in range(num_batch):
            sy, sx = register_images_shifts(
                np, np.fft, M0_reg, output["M0ff"][i],
                radius=0.8, gaussian_sigma=3, gaussian_filter=gaussian_filter
            )
            shifts_y.append(sy)
            shifts_x.append(sx)
            for k in reg_keys:
                output[k][i] = apply_register_images_shifts(np, output[k][i], sy, sx)

        output["registration"] = np.stack([np.array(shifts_y), np.array(shifts_x)], axis=1)

    # Optional square cropping
    if parameters.get("square", False):
        output = {k: square_cupy(v) if v.ndim >= 3 else v for k, v in output.items()}

    # All arrays are already NumPy, so no conversion needed

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------
    target_dir = _get_default_output_path(file_reader.file_path)
    if "saving_to_folder" in parameters:
        target_dir = Path(parameters["saving_to_folder"]) / "SIMPLE_NUMPY"

    _create_directories(target_dir, "FULL")

    # Save HDF5
    _save_h5_2(target_dir, output, parameters)

    # Temporal smoothing (if requested)
    if parameters.get("smoothing_gaussian", False):
        import time
        start_time = time.time()
        sigma = parameters.get("smoothing_gaussian_size", 2)
        for k in output.keys():
            output[k] = temporal_gaussian(output[k], sigma=sigma)
        print(f"smoothing_gaussian in {time.time() - start_time:.1f} seconds")

    # Contrast adjustment and normalization to uint8
    if parameters.get("contrast", False):
        low_pct, high_pct = parameters.get("contrast_low_max_percent", (1.0, 99.0))
        gamma = parameters.get("contrast_gamma", 1.0)
        for k in output.keys():
            low, high = stretchlim(output[k], low_pct, high_pct)
            output[k] = imadjust(output[k], low, high, gamma)
            output[k] = normalize_to_uint8(output[k])
    else:
        output = {k: normalize_to_uint8(v) for k, v in output.items()}

    # Save videos and PNGs
    _save_videos(target_dir, output, 30)
    _save_pngs(target_dir, output)

    # Metadata
    _save_metadata(target_dir, file_reader, parameters)

def _process_batch(parameters, frames, phase_term = None, output_dict = None):
    xp = np
    fft = scipy.fft
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

    # Frequency bands
    for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
        idxs_band, _ = frequency_symmetric_filtering(xp, fft, nt_sub, parameters["sampling_freq"], f1, f2)
        band = xp.mean(psd[idxs_band], axis=0)
        output_dict[f"band_{k}_{f1}_{f2}"] = band

def _process_shack_hartmann(parameters, frames, output_dict = None):
    
    fft = scipy.fft
    nt, ny, nx = frames.shape

    prop_method = parameters["spatial_propagation"]
    
    
    if prop_method == "Fresnel":
        U = construct_subapertures_fresnel(
            np, fft, frames, parameters["wavelength"], parameters["z"], parameters["pixel_pitch"],
            parameters["low_freq"], parameters.get("high_freq"), parameters["sampling_freq"],
            frames.shape[0], parameters["shack_hartmann_nx_subap"], parameters["shack_hartmann_ny_subap"],
            parameters["shack_hartmann_svd_threshold"]
        )
    elif prop_method == "AngularSpectrum":
        U = construct_subapertures_angular(
            np, fft, frames, parameters["wavelength"],
            parameters["z"], parameters["pixel_pitch"], parameters["low_freq"], parameters.get("high_freq"),
            parameters["sampling_freq"], frames.shape[0], parameters["shack_hartmann_nx_subap"],
            parameters["shack_hartmann_ny_subap"], parameters["shack_hartmann_svd_threshold"]
        )

    # Displacement estimation
    if parameters.get("shack_hartmann_graph_laplacian", False): # Use all the sub aps
        shifts_y, shifts_x = calculate_displacements_graph_laplacian(
            np, fft, U,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get("shack_hartmann_deviation_threshold", 3.0),
            shifts_range=parameters.get("shack_hartmann_shifts_pixel_range_threshold", 20.0)
        )
    else: # Use only the shifts to the central sub ap
        ny_s, nx_s, Ny, Nx = U.shape
        shifts_y, shifts_x = calculate_displacements(
            np, fft, U,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get("shack_hartmann_deviation_threshold", 3.0),
            shifts_range=parameters.get("shack_hartmann_shifts_pixel_range_threshold", 20.0)
        )

    if output_dict is not None:

        sy, sx, numy, numx = U.shape
        U = np.transpose(U, axes=(0,2,1,3))
        output_dict["shack_hartmann_sub_images"] = np.reshape(U,(numy*sy,numx*sx))

    del U, frames  # Memory footprint reduction

    # Phase reconstruction
    phase = None
    if parameters.get("shack_hartmann_zernike_fit", True):
        if prop_method == "Fresnel":
            coefs, phase = fit_zernike_fresnel(
                np, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
            )
        elif prop_method == "AngularSpectrum":
            coefs, phase = fit_zernike_angular_spectrum(
                np, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], parameters["z"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
            )

    # Phase reconstruction
    phase = None
    if parameters.get("shack_hartmann_zernike_fit", True):
        if prop_method == "Fresnel":
            coefs, phase = fit_zernike_fresnel(
                np, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
            )
        elif prop_method == "AngularSpectrum":
            coefs, phase = fit_zernike_angular_spectrum(
                np, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], parameters["z"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
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
        phase_term = np.exp(-1j * phase)
        phase_term = np.nan_to_num(phase_term, nan=0.0)

    return phase_term