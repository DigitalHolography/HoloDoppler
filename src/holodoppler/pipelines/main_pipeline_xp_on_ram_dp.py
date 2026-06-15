from holodoppler.saving import *
from holodoppler.propagation import *
from holodoppler.shack_hartmann import *
from holodoppler.zernike import *
from holodoppler.utils import *
from holodoppler.filtering import *
from holodoppler.moments import moment
from holodoppler.registration import *
from holodoppler.plotting import *
from holodoppler.backend import BackendManager
from holodoppler.file_io import FileReaderFactory, CineFileReader, HoloFileReader

import os
import time
import threading
import queue
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import imageio as iio
from tqdm import tqdm
import cupy as cp
import multiprocessing as mp
from multiprocessing import shared_memory

# ------------------------------------------------------------------
# Timing & Profiling Utilities
# ------------------------------------------------------------------
_func_timings = defaultdict(lambda: {"cum_time": 0.0, "calls": 0})
_timings_lock = threading.Lock()

def track_time(name):
    """Decorator to track cumulative execution time per function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            with _timings_lock:
                _func_timings[name]["cum_time"] += end - start
                _func_timings[name]["calls"] += 1
            return result
        return wrapper
    return decorator

_total_time_start = 0.0
def total_time_start():
    global _total_time_start
    _total_time_start = time.perf_counter()
    # print(_total_time_start)

def print_timings_summary():
    """Print cumulated time, calls, ratio, and total for all tracked functions."""
    total = time.perf_counter() - _total_time_start

    with _timings_lock:
        cumulated = sum(v["cum_time"] for v in _func_timings.values())

    if cumulated == 0:
        return

    print("\n[ Timing Summary ]")
    print(f"{'Function':<45} | {'Calls':>5} | {'Time (s)':>10} | {'Ratio':>6}")
    print("-" * 78)
    sorted_funcs = sorted(_func_timings.items(), key=lambda x: x[1]["cum_time"], reverse=True)
    for fname, data in sorted_funcs:
        ratio = data["cum_time"] / total if total > 0 else 0
        print(f"{fname:<45} | {data['calls']:>5} | {data['cum_time']:>10.4f} | {ratio:>6.2%}")
    print(f"{'TOTAL':<45} | {'':>5} | {total:>10.4f} | 100.00%")
    print(f"{'CUMULATED':<45} | {'':>5} | {cumulated:>10.4f} | {(cumulated / total if total > 0 else 0) :>6.2%}")
    print("-" * 78)

construct_subapertures_fresnel = track_time('construct_subapertures_fresnel')(construct_subapertures_fresnel)
construct_subapertures_angular = track_time('construct_subapertures_angular')(construct_subapertures_angular)
calculate_displacements_graph_laplacian = track_time('calculate_displacements_graph_laplacian')(calculate_displacements_graph_laplacian)
calculate_displacements = track_time('calculate_displacements')(calculate_displacements)
fit_zernike_fresnel = track_time('fit_zernike_fresnel')(fit_zernike_fresnel)
fit_zernike_angular_spectrum = track_time('fit_zernike_angular_spectrum')(fit_zernike_angular_spectrum)
southwell_phase_integration = track_time('southwell_phase_integration')(southwell_phase_integration)
pad_array_centrally = track_time('pad_array_centrally')(pad_array_centrally)
fresnel_transform_with_phase = track_time('fresnel_transform_with_phase')(fresnel_transform_with_phase)
angular_spectrum_transform_with_phase = track_time('angular_spectrum_transform_with_phase')(angular_spectrum_transform_with_phase)
fresnel_transform = track_time('fresnel_transform')(fresnel_transform)
angular_spectrum_transform = track_time('angular_spectrum_transform')(angular_spectrum_transform)
svd_filter = track_time('svd_filter')(svd_filter)
fourier_time_transform = track_time('fourier_time_transform')(fourier_time_transform)
frequency_symmetric_filtering = track_time('frequency_symmetric_filtering')(frequency_symmetric_filtering)
moment = track_time('moment')(moment)
gaussian_flatfield = track_time('gaussian_flatfield')(gaussian_flatfield)
register_trs = track_time('register_trs')(register_trs)
apply_registration = track_time('apply_registration')(apply_registration)
save_outputs = track_time('save_outputs')(save_outputs)
zoom_slicewise_fast = track_time('zoom_slicewise_fast')(zoom_slicewise_fast)

DebugPlotterManager.plot_all = track_time('DebugPlotterManager.debug_plot_all')(DebugPlotterManager.plot_all)
CineFileReader.read_frames = track_time('CineFileReader.read_frames')(CineFileReader.read_frames)
HoloFileReader.read_frames = track_time('HoloFileReader.read_frames')(HoloFileReader.read_frames)

# ------------------------------------------------------------------
# Optimized Accumulator (In-place addition, no list stacking)
# ------------------------------------------------------------------
class Accumulator:
    def __init__(self, batch_size, xp):
        self.xp = xp
        self.batch_size = batch_size
        self.accumulators = {}
        self.count = 0

    def add(self, data_dict):
        if not self.accumulators:
            # Initialize buffers on first call to avoid reallocation
            for k, v in data_dict.items():
                if v is None:
                    self.accumulators[k] = None
                    continue
                self.accumulators[k] = self.xp.zeros_like(v)
        # In-place addition
        for k, v in data_dict.items():
            if k in self.accumulators:
                if v is None:
                    # self.accumulators[k] = None
                    continue
                self.xp.add(self.accumulators[k], v, out=self.accumulators[k])
            else:
                self.accumulators[k] = v.copy()
        self.count += 1
        if self.count >= self.batch_size:
            return self.flush()
        return None

    def flush(self):
        if not self.accumulators:
            return None
        batch = {}
        for k, buf in self.accumulators.items():
            if buf is None:
                batch[k] = None
                continue
            batch[k] = buf / self.count
            buf.fill(0)  # Reuse memory for next cycle
        self.count = 0
        return batch

# ------------------------------------------------------------------
# Shack-Hartmann sub‑pipeline
# ------------------------------------------------------------------
def _process_shack_hartmann(bm, parameters, frames, registration_ref):
    xp = bm.xp
    fft = bm.fft
    nt, ny, nx = frames.shape
    debug = {}
    compute_debug = parameters.get("debug", False)

    prop_method = parameters["spatial_propagation"]
    sh_acc = parameters.get("shack_hartmann_accumulation", 1)
    sub_batch_size = nt // sh_acc
    U_subaps_sum = None

    for it in range(sh_acc):
        frames_sub = frames[sub_batch_size * it : sub_batch_size * it + sub_batch_size]
        if prop_method == "Fresnel":
            U = construct_subapertures_fresnel(
                xp, fft, frames_sub, parameters["wavelength"], parameters["z"], parameters["pixel_pitch"],
                parameters["low_freq"], parameters.get("high_freq"), parameters["sampling_freq"],
                frames_sub.shape[0], parameters["shack_hartmann_nx_subap"], parameters["shack_hartmann_ny_subap"],
                parameters["shack_hartmann_svd_threshold"]
            )
        elif prop_method == "AngularSpectrum":
            U = construct_subapertures_angular(
                xp, fft, frames_sub, parameters["wavelength"],
                parameters["z"], parameters["pixel_pitch"], parameters["low_freq"], parameters.get("high_freq"),
                parameters["sampling_freq"], frames_sub.shape[0], parameters["shack_hartmann_nx_subap"],
                parameters["shack_hartmann_ny_subap"], parameters["shack_hartmann_svd_threshold"]
            )
        U_subaps_sum = U if U_subaps_sum is None else (U_subaps_sum + U)
        del U, frames_sub  # Memory footprint reduction

    U_subaps = U_subaps_sum / sh_acc
    if compute_debug:
        debug["U_subaps"] = U_subaps

    # Displacement estimation
    imref = parameters.get("shack_hartmann_graph_ref")
    if parameters.get("shack_hartmann_graph_laplacian", False):
        shifts_y, shifts_x = calculate_displacements_graph_laplacian(
            xp, fft, U_subaps,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get("shack_hartmann_deviation_threshold", 3.0),
            shifts_range=parameters.get("shack_hartmann_shifts_pixel_range_threshold", 20.0)
        )
    else:
        ny_s, nx_s, Ny, Nx = U_subaps.shape
        if imref == "ref_from_registration":
            imref = None if registration_ref is None else resize_slicewise(registration_ref, Ny, Nx, xp=xp, fft=fft)
        shifts_y, shifts_x = calculate_displacements(
            xp, fft, U_subaps,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get("shack_hartmann_deviation_threshold", 3.0),
            shifts_range=parameters.get("shack_hartmann_shifts_pixel_range_threshold", 20.0),
            ref=imref
        )
    if compute_debug:
        debug["shifts_y"] = shifts_y
        debug["shifts_x"] = shifts_x

    # Phase reconstruction
    phase = None
    if parameters.get("shack_hartmann_zernike_fit", False):
        if prop_method == "Fresnel":
            coefs, phase = fit_zernike_fresnel(
                xp, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
            )
        elif prop_method == "AngularSpectrum":
            coefs, phase = fit_zernike_angular_spectrum(
                xp, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], parameters["z"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
            )
        if compute_debug: debug["coefs"] = coefs
    elif parameters.get("shack_hartmann_southwell_phase_integration", False):
        phase = southwell_phase_integration(
            bm, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
            parameters["wavelength"], shifts_y, shifts_x
        )
    else:
        phase = None
    if compute_debug: debug["phase"] = phase

    # Phase correction term
    phase_term = None
    if phase is not None:
        phase_term = xp.exp(-1j * phase)
        phase_term = xp.nan_to_num(phase_term, nan=0.0)
        if parameters.get("zero_padding"):
            phase_term = pad_array_centrally(phase_term, parameters["zero_padding"], xp)

    return phase_term, debug

# ------------------------------------------------------------------
# Main processing of a sub‑batch
# ------------------------------------------------------------------
def _process_sub_batch(bm, parameters, frames_sub, phase_term, compute_debug):
    xp = bm.xp
    fft = bm.fft
    nt_sub = frames_sub.shape[0]
    prop_method = parameters["spatial_propagation"]
    zero_pad = parameters.get("zero_padding")

    # Propagation
    if phase_term is not None:
        if prop_method == "Fresnel":
            holograms = fresnel_transform_with_phase(
                xp, fft, frames_sub, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
                phase_term, zero_padding=zero_pad, use_output_kernel=parameters["Fresnel_use_ouput_kernel"]
            )
        elif prop_method == "AngularSpectrum":
            holograms = angular_spectrum_transform_with_phase(
                xp, fft, frames_sub, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
                phase_term, zero_padding=zero_pad
            )
    else:
        if prop_method == "Fresnel":
            holograms = fresnel_transform(
                xp, fft, frames_sub, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
                zero_padding=zero_pad, use_output_kernel=parameters["Fresnel_use_ouput_kernel"]
            )
        elif prop_method == "AngularSpectrum":
            holograms = angular_spectrum_transform(
                xp, fft, frames_sub, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
                zero_padding=zero_pad
            )

    # SVD filtering
    if compute_debug:
        holograms_f, removedU, holograms_fbar, eigenvalues, _, _, dc = svd_filter(xp, holograms, parameters["svd_threshold"], filter_mode = parameters["svd_filter_mode"], remove_dc = parameters["svd_remove_dc"], debug = compute_debug)
    else :
        holograms_f = svd_filter(xp, holograms, parameters["svd_threshold"], filter_mode = parameters["svd_filter_mode"], remove_dc = parameters["svd_remove_dc"])

    if not compute_debug:
        del holograms  # Free memory early in non-debug mode

    batch = {}
    if compute_debug:
        batch["average_signal"] = xp.squeeze(xp.mean(holograms_f, axis=(-1, -2)))

    # Temporal transform
    if parameters.get("temporal_transformation") == "FourierTransform":
        spectrum_f = fourier_time_transform(xp, fft, holograms_f)
    else:
        spectrum_f = holograms_f

    # Frequency selection
    idxs, freqs = frequency_symmetric_filtering(
        xp, fft, nt_sub, parameters["sampling_freq"], parameters["low_freq"], parameters.get("high_freq")
    )
    psd = xp.abs(spectrum_f) ** 2

    if compute_debug and parameters["save_psd_avg"]:
        batch["psd"] = psd

    # Moments
    batch["M0"] = moment(xp, psd[idxs], freqs, 0)
    batch["M1"] = moment(xp, psd[idxs], freqs, 1)
    batch["M2"] = moment(xp, psd[idxs], freqs, 2)
    batch["M0ff"] = gaussian_flatfield(batch["M0"], parameters.get("registration_flatfield_gw", 1.0), bm.gaussian_filter)

    # Frequency bands
    for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
        idxs_band, _ = frequency_symmetric_filtering(xp, fft, nt_sub, parameters["sampling_freq"], f1, f2)
        band = xp.mean(psd[idxs_band], axis=0)
        batch[f"band_{k}_{f1}_{f2}"] = band

    # Debug-only recomputation without phase fix
    if compute_debug and phase_term is not None:
        if prop_method == "Fresnel":
            holo_nofix = fresnel_transform(xp, fft, frames_sub, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"], zero_padding=zero_pad, use_output_kernel=parameters["Fresnel_use_ouput_kernel"])
        elif prop_method == "AngularSpectrum":
            holo_nofix = angular_spectrum_transform(xp, fft, frames_sub, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"], zero_padding=zero_pad)
        holo_nofix_f = svd_filter(xp, holo_nofix, parameters["svd_threshold"], filter_mode=parameters["svd_filter_mode"], remove_dc=parameters["svd_remove_dc"])
        spec_nofix = fourier_time_transform(xp, fft, holo_nofix_f)
        psd_nofix = xp.abs(spec_nofix[idxs]) ** 2
        batch["M0notfixed"] = moment(xp, psd_nofix, freqs, 0)
        del holo_nofix, holo_nofix_f, spec_nofix, psd_nofix
    
    # Debug-only recomputation without inversed svd_filtering
    if compute_debug and holograms_fbar is not None:
        spec_fbar = fourier_time_transform(xp, fft, holograms_fbar)
        psd_fbar = xp.abs(spec_fbar[idxs]) ** 2
        batch["M0svdbar"] = moment(xp, psd_fbar, freqs, 0)
        del spec_fbar, psd_fbar

    if compute_debug :
        batch["spectrum_line"] = xp.mean(psd, axis=(-1, -2))
        batch["freqs"] = freqs
    if compute_debug and removedU is not None :
        batch["svd_U"] = removedU
    if compute_debug and eigenvalues is not None :
        batch["eigenvalues"] = eigenvalues
    if compute_debug and dc is not None :
        batch["svd_dc"] = dc

    return batch

# ------------------------------------------------------------------
# Render moments for a single batch
# ------------------------------------------------------------------
def render_moments(bm, parameters, frames=None, registration_ref=None):
    xp = bm.xp
    nt, ny, nx = frames.shape
    res = {}
    accu = {}
    compute_debug = parameters.get("debug", False)

    # --- Shack‑Hartmann phase correction ---
    phase_term = None
    if parameters.get("shack_hartmann", False):
        phase_term, debug_sh = _process_shack_hartmann(bm, parameters, frames, registration_ref)
        if compute_debug:
            res.update(debug_sh)

    # --- Main moment accumulation ---
    main_acc = Accumulator(parameters.get("accumulation", 1), xp)
    sub_batch_size = nt // main_acc.batch_size
    sub_batch_stride = sub_batch_size

    for it in range(main_acc.batch_size):
        frames_sub = frames[sub_batch_stride * it : sub_batch_stride * it + sub_batch_size]
        batch = _process_sub_batch(bm, parameters, frames_sub, phase_term, compute_debug)
        out = main_acc.add(batch)
        if out is not None:
            res.update(out)
        del frames_sub  # Reduce memory footprint
    
    if compute_debug and 'psd' in res:
        accu["psd_map_avg"] = res.pop('psd') # transfer to the accu dict where results are accumulated through all iterations


    # --- Image registration ---
    if parameters.get("image_registration", False) and registration_ref is not None:
        M0_ff = res["M0ff"] #gaussian_flatfield(res["M0"], parameters.get("registration_flatfield_gw", 1.0), bm.gaussian_filter)
        if compute_debug:
            res["M0_ff_noreg"] = M0_ff
            
        reg = register_trs(
            xp, bm.fft, bm.ndi, registration_ref, M0_ff, parameters.get("registration_disc_ratio"),
            estimate_similarity=(parameters.get("image_registration_type") == "translation_rotation_scale"),
            gaussian_sigma=parameters.get("registration_gaussian_sigma"),
            integer_translation=parameters.get("registration_integer_translation", False)
        )
            
        if parameters.get("apply_registration", False):
            res["M0"] = apply_registration(xp, bm.fft, bm.ndi, res["M0"], reg, integer_translation=parameters.get("registration_integer_translation", False))
            res["M1"] = apply_registration(xp, bm.fft, bm.ndi, res["M1"], reg, integer_translation=parameters.get("registration_integer_translation", False))
            res["M2"] = apply_registration(xp, bm.fft, bm.ndi, res["M2"], reg, integer_translation=parameters.get("registration_integer_translation", False))
            res["M0ff"] = apply_registration(xp, bm.fft, bm.ndi, res["M0ff"], reg, integer_translation=parameters.get("registration_integer_translation", False))
            for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
                key = f"band_{k}_{f1}_{f2}"
                res[key] = apply_registration(xp, bm.fft, bm.ndi, res[key], reg, integer_translation=parameters.get("registration_integer_translation", False))
            if "M0svdbar" in res:
                res["M0svdbar"] = apply_registration(xp, bm.fft, bm.ndi, res["M0svdbar"], reg, integer_translation=parameters.get("registration_integer_translation", False))
            if "psd_map_avg" in accu:
                accu["psd_map_avg"] = apply_registration3D(xp, bm.fft, bm.ndi, accu["psd_map_avg"], reg, integer_translation=parameters.get("registration_integer_translation", False))
        res["registration"] = reg

    return res, accu



# ------------------------------------------------------------------
# Preview (single batch)
# ------------------------------------------------------------------
def preview_process_moments(file_path, parameters):
    total_time_start()

    tictoc = parameters["tictoc"]


    bm = BackendManager(backend=parameters["backend"])
    file_reader = FileReaderFactory.create(file_path)
    file_reader.open()
    
    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)

    if file_reader.ext == ".cine":
        print("file header :", file_reader.metadata)
    print("parameters : ", parameters)
    
    batch_size = parameters["batch_size"]
    first_frame = parameters["first_frame"]
    frames = file_reader.read_frames(first_frame, batch_size)
    frames = bm.to_backend(frames)
    res, accu = render_moments(bm, parameters, frames=frames)
    file_reader.close()

    def save_debug_images(debug_dict, save_dir, prefix="debug"):
        os.makedirs(save_dir, exist_ok=True)
        for key, img in debug_dict.items():
            if img is None:
                continue
            img_np = bm.to_numpy(img)
            if img_np.ndim == 2 and parameters.get("square", False):
                H, W = img_np.shape
                L = max(H, W)
                img_np = resize_slicewise(img_np, L, L)
            if img_np.dtype != np.uint8:
                img_min, img_max = np.min(img_np), np.max(img_np)
                if img_max > img_min:
                    img_np = (img_np - img_min) / (img_max - img_min + 1e-12)
                img_np = (img_np * 255).astype(np.uint8)
            filename = os.path.join(save_dir, f"{prefix}_{key}.png")
            print("Saving : ",filename)
            iio.imwrite(filename, img_np)

    compute_debug = parameters.get("debug", False)
    debug_manager = DebugPlotterManager(parameters) if compute_debug else None
    debug_imgs = debug_manager.plot_all(res) if compute_debug else {}

    if compute_debug and parameters.get("shack_hartmann") and parameters.get("shack_hartmann_zernike_fit"):
        coefs = bm.to_numpy(res["coefs"]) if "coefs" in res else None
        if coefs is not None:
            print("zernike_fit_coeffs (radians):", coefs)
            delta_z = (4 * np.sqrt(3) * parameters["z"]**2 /
                       ((min(frames.shape[1:]) * parameters["pixel_pitch"][0])**2) *
                       parameters["wavelength"] / (2 * np.pi) * coefs[0] * 1e3)
            print("delta to true z in mm if coef[0] is defocus :", delta_z)

    if "M0" in res:
        M0 = bm.to_numpy(res["M0"])
        M0 = (M0 - np.min(M0)) / (np.max(M0) - np.min(M0) + 1e-12)
        debug_imgs["M0"] = (M0 * 255).astype(np.uint8)
    if "M0ff" in res:
        M0 = bm.to_numpy(res["M0ff"])
        M0 = (M0 - np.min(M0)) / (np.max(M0) - np.min(M0) + 1e-12)
        debug_imgs["M0ff"] = (M0 * 255).astype(np.uint8)

    save_debug_images(debug_imgs, "./debug_outputs")
    plt.close("all")

    M0img = debug_imgs.get("M0")
    
    if tictoc:
        print_timings_summary()
    if M0img is not None:
        if M0img.ndim == 2 and parameters.get("square", False):
            H, W = M0img.shape
            L = max(H, W)
            M0img = resize_slicewise(M0img, L, L)
        return M0img

# ------------------------------------------------------------------
# Full video processing
# ------------------------------------------------------------------
def process_moments(file_path, parameters, mp4_path=None, return_numpy=False, holodoppler_path=True):
    tictoc = parameters["tictoc"]

    total_time_start()
    bm = BackendManager(backend=parameters["backend"])
    file_reader = FileReaderFactory.create(file_path)
    file_reader.open()
    
    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)
    print("parameters : ", parameters)

    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]
    end_frame = parameters.get("end_frame", 0)
    if end_frame <= 0:
        end_frame = file_reader.file_header["num_frames"] if file_reader.ext == ".holo" else file_reader.metadata["ImageCount"]

    if batch_stride >= (end_frame - first_frame):
        num_batch = 1 if batch_size <= (end_frame - first_frame) else 0
    else:
        num_batch = int((end_frame - first_frame) / batch_stride)
    if num_batch <= 0:
        return None

    # Memmap support
    # if parameters.get("use_memmap", False) and hasattr(file_reader, "get_np_memmap"):
    #     try:
    #         memmap = file_reader.get_np_memmap()[first_frame:end_frame]
    #     except Exception as e:
    #         print(f"Memmap loading failed: {e}, falling back to regular reads.")
    #         memmap = None
    # else:
    #     memmap = None

    out_list = []
    out_accumulation = {}
    coefs_list = [None] * num_batch if parameters.get("shack_hartmann") else None
    reg_list = [None] * num_batch if parameters.get("image_registration") else None

    compute_debug = parameters.get("debug", False)
    debug_manager = DebugPlotterManager(parameters) if compute_debug else None

    
    debug_queue = queue.Queue(maxsize=14) if debug_manager else None
    res_store = {} if debug_manager else None
    lock = threading.Lock() if debug_manager else None
    stop_event = threading.Event() if debug_manager else None
    debug_results = {}

    if debug_manager:
        debug_manager.plot_all = track_time("debug_manager_plot_all")(debug_manager.plot_all)
        def plotting_worker():
            while not stop_event.is_set() or not debug_queue.empty():
                try:
                    i = debug_queue.get(timeout=0.1)
                    with lock:
                        res = res_store.pop(i)
                    out = debug_manager.plot_all(res)
                    with lock:
                        debug_results[i] = out
                    debug_queue.task_done()
                except queue.Empty:
                    continue
        debug_thread = threading.Thread(target=plotting_worker, daemon=True)
        debug_thread.start()
    else:
        debug_thread = None

    # Registration reference
    M0_reg = None
    if parameters.get("image_registration"):
        frames_reg = file_reader.read_frames(first_frame, parameters.get("batch_size_registration", batch_size))
        frames_reg = bm.to_backend(frames_reg)
        M0_reg = render_moments(bm, parameters, frames=frames_reg)[0]["M0ff"]
        # M0_reg = gaussian_flatfield(M0_reg, parameters.get("registration_flatfield_gw", 1.0), bm.gaussian_filter)

    bm.clear_gpu_memory()
    bm.print_gpu_used_memory()

    # Dispatch to backend-specific loop
    if parameters["backend"] == "cupy":
        _process_gpu_streaming_onram(bm, file_path, parameters, num_batch, first_frame, batch_stride, batch_size,
                                     M0_reg, out_list, out_accumulation, coefs_list, reg_list, debug_manager, debug_queue, res_store, lock)
    else:
        _process_cpu(bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
                     M0_reg, out_list, out_accumulation, coefs_list, reg_list, debug_manager, debug_queue, res_store, lock)

    

    if coefs_list is not None:
            coefs_list = [bm.to_numpy(c) for c in coefs_list]
    # print(f"coefs_list: {time.time()-t0:.2f}s")
    if reg_list is not None:
        reg_list = [bm.to_numpy(r) for r in reg_list]
    
    @track_time("collecting")
    def collecting(bm,out_list,out_accumulation,debug_manager,debug_queue,stop_event,debug_thread,coefs_list,reg_list,compute_debug,debug_results,num_batch,parameters):

        # Post-processing
        # t0 = time.time()
        np_list = [bm.to_numpy(xparr) for xparr in out_list]
        # print(f"TransferRAM: {time.time()-t0:.2f}s")
        vid_t = np.stack(np_list, axis=0)
        # plt.imshow(vid_t[0,3,:,:])
        # plt.show()
        # print(f"stack CPU: {time.time()-t0:.2f}s")
        bm.clear_gpu_memory()
        # print(f"clear_gpu_memory: {time.time()-t0:.2f}s")

        if debug_manager:
            debug_queue.join()
            stop_event.set()
            debug_thread.join()
            debug_manager.close_all()
        # print(f"debug_manager: {time.time()-t0:.2f}s")
        

        
        # print(f"reg_list: {time.time()-t0:.2f}s")

        vid_debug = {}
        if compute_debug and debug_results:
            for key in debug_results[0].keys():
                try:
                    vid_debug[key] = np.stack([bm.to_numpy(debug_results[k][key]) for k in range(num_batch)], axis=0)
                except Exception as e:
                    print(f"Couldn't stack debug output {key}: ", e)
        if compute_debug and out_accumulation:
            for key in out_accumulation.keys():
                if out_accumulation[key].ndim == 3:
                    vid_debug[key] = bm.to_numpy(out_accumulation[key])
        # print(f"vid_debug: {time.time()-t0:.2f}s")
        return vid_t, vid_debug
    
    vid_t, vid_debug = collecting(bm,out_list,out_accumulation,debug_manager,debug_queue,stop_event,debug_thread,coefs_list,reg_list,compute_debug,debug_results,num_batch,parameters)
    
    # print(vid_t.shape)
    # t0 = time.time()
    # Spatial transforms
    if parameters.get("square", False):
        m = max(vid_t.shape[-2], vid_t.shape[-1])
        print(f"Input shape: {vid_t.shape}")
        # print(f"Expected axes: {axes}")
        # print(f"Zoom factors: {zoom_factors}")
        vid_t = zoom_slicewise_fast(vid_t, m, m, use_gpu=bm.is_gpu)
        # plt.imshow(vid_t[0,1,:,:])
        # plt.show()
        print(f"Output shape: {vid_t.shape}")
    # print(f"square: {time.time()-t0:.2f}s")
    if parameters.get("transpose", False):
        vid_t = np.transpose(vid_t, axes=(0, 1, 3, 2))
    # print(f"transpose: {time.time()-t0:.2f}s")
    if parameters.get("flip_x", False):
        vid_t = np.flip(vid_t, axis=-1)
    if parameters.get("flip_y", False):
        vid_t = np.flip(vid_t, axis=-2)
    
    # print(f"flip: {time.time()-t0:.2f}s")
    
    # import matplotlib.pyplot as plt
    # plt.imshow(vid_t[0,3,:,:])
    # plt.show()

    save_outputs(
        file_reader, video_path=mp4_path, holodoppler_path=holodoppler_path,
        vid=vid_t, vid_debug=vid_debug, parameters=parameters,
        reg_list=reg_list, coefs_list=coefs_list,
        end_frame=end_frame, first_frame=first_frame, num_batch=num_batch
    )
    plt.close("all")
    file_reader.close()

    if tictoc:
        print_timings_summary()

    if return_numpy:
        return vid_t
    return None

# ------------------------------------------------------------------
# Specialised loops
# ------------------------------------------------------------------
def _process_cpu(bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
                 M0_reg, out_list, out_accumulation, coefs_list, reg_list, debug_manager, debug_queue, res_store, lock):
    
    for i in tqdm(range(num_batch)):
        frames = file_reader.read_frames(first_frame + i * batch_stride, batch_size)
        frames = bm.to_backend(frames)
        res, accu = render_moments(bm, parameters, frames=frames, registration_ref=M0_reg)

        for key in accu.keys():
            if key not in out_accumulation:
                out_accumulation[key] = accu[key]
            else : 
                out_accumulation[key] += accu[key]

        if res is None: break
        l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
        for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
            l.append(res[f"band_{k}_{f1}_{f2}"])
        out_list.append(bm.xp.stack(l, axis=0))
        if "coefs" in res and coefs_list is not None: coefs_list[i] = res["coefs"]
        if "registration" in res and reg_list is not None: reg_list[i] = res["registration"]
        if debug_manager and lock:
            with lock: res_store[i] = res
            debug_queue.put(i)
            
            
def _fetch_batch_worker_sharedmem(worker_id,
                                  batch_indices,
                                  file_path,
                                  first_frame,
                                  batch_stride,
                                  batch_size,
                                  shm_names,
                                  frame_shape,
                                  frame_dtype_str,
                                  free_queue,
                                  ready_queue):
    """
    Worker process:
      - waits for a free shared-memory slot
      - reads one batch
      - copies it into that slot
      - sends only metadata to main process
    """

    dtype = np.dtype(frame_dtype_str)

    shm_objects = []
    shm_arrays = []

    try:
        for name in shm_names:
            shm = shared_memory.SharedMemory(name=name)
            arr = np.ndarray(frame_shape, dtype=dtype, buffer=shm.buf)
            shm_objects.append(shm)
            shm_arrays.append(arr)

        file_reader = FileReaderFactory.create(file_path)
        file_reader.open()

        try:
            for batch_index in batch_indices:
                t0 = time.perf_counter()
                frames_batch = file_reader.read_frames(
                    first_frame + batch_index * batch_stride,
                    batch_size
                )
                read_dt = time.perf_counter() - t0

                if frames_batch.shape != frame_shape:
                    raise RuntimeError(
                        f"Worker {worker_id}: unexpected batch shape "
                        f"{frames_batch.shape}, expected {frame_shape}"
                    )

                if frames_batch.dtype != dtype:
                    frames_batch = frames_batch.astype(dtype, copy=False)

                slot_id = free_queue.get()

                t0 = time.perf_counter()
                np.copyto(shm_arrays[slot_id], frames_batch)
                copy_dt = time.perf_counter() - t0

                ready_queue.put((
                    slot_id,
                    batch_index,
                    read_dt,
                    copy_dt,
                    int(frames_batch.nbytes),
                    None,
                ))

        finally:
            file_reader.close()

    except Exception as e:
        ready_queue.put((
            None,
            None,
            0.0,
            0.0,
            0,
            repr(e),
        ))

    finally:
        for shm in shm_objects:
            shm.close()

@track_time("_process_gpu_streaming_onram")
def _process_gpu_streaming_onram(bm, file_path, parameters, num_batch, first_frame, batch_stride,
                                 batch_size, M0_reg, out_list, out_accumulation, coefs_list, reg_list,
                                 debug_manager, debug_queue, res_store, lock):

    tictoc = bool(parameters.get("tictoc", False))

    prof_sum = defaultdict(float)
    prof_cnt = defaultdict(int)
    prof_max = defaultdict(float)
    prof_bytes = defaultdict(int)

    def now():
        return time.perf_counter()

    def prof_add(name, dt):
        if not tictoc:
            return
        prof_sum[name] += float(dt)
        prof_cnt[name] += 1
        prof_max[name] = max(prof_max[name], float(dt))

    def prof_add_bytes(name, nbytes):
        if not tictoc:
            return
        prof_bytes[name] += int(nbytes)

    t_total0 = now()

    if num_batch <= 0:
        return

    FETCH_NUM_WORKERS = int(parameters.get("fetch_num_workers", 8))
    SHM_NUM_SLOTS = int(parameters.get("shm_num_slots", max(2 * FETCH_NUM_WORKERS, 8)))

    stream_h2d = cp.cuda.Stream(non_blocking=True)
    stream_compute = cp.cuda.Stream(non_blocking=True)

    shm_objects = []
    shm_arrays = []
    processes = []

    free_queue = None
    ready_queue = None

    processed_batches = 0
    normal_exit = False

    def print_profile():
        if not tictoc:
            return

        total_dt = now() - t_total0

        print("\n[tictoc] _process_gpu_streaming_onram shared_memory profile")
        print(f"processed_batches: {processed_batches}/{num_batch}")
        print(f"total wall time:    {total_dt:.3f} s")

        def print_row(name):
            s = prof_sum.get(name, 0.0)
            c = prof_cnt.get(name, 0)
            m = prof_max.get(name, 0.0)
            avg = s / c if c else 0.0
            pct = 100.0 * s / total_dt if total_dt > 0 else 0.0
            print(
                f"{name:36s} "
                f"total={s:9.3f}s  "
                f"avg={avg * 1e3:9.3f}ms  "
                f"max={m * 1e3:9.3f}ms  "
                f"n={c:6d}  "
                f"{pct:6.1f}%"
            )

        ordered = [
            "first_batch_read_for_shape",
            "shared_memory_create_total",
            "first_batch_copy_to_shm",
            "worker_process_start_total",
            "ready_queue_get",
            "worker_read_frames",
            "worker_copy_to_shm",
            "h2d_enqueue_cpu",
            "h2d_wait_cpu",
            "h2d_gpu_elapsed",
            "compute_enqueue_cpu",
            "compute_wait_cpu",
            "compute_gpu_elapsed",
            "postprocess_accumulate_and_store",
            "debug_manager_store",
            "final_average_accumulation",
            "worker_join_total",
            "final_cuda_synchronize",
            "shared_memory_cleanup",
        ]

        for name in ordered:
            if name in prof_cnt:
                print_row(name)

        input_gb = prof_bytes.get("input_bytes", 0) / 1e9
        h2d_gb = prof_bytes.get("h2d_bytes", 0) / 1e9

        print(f"input bytes:        {input_gb:.3f} GB")
        print(f"h2d bytes:          {h2d_gb:.3f} GB")

        if prof_sum.get("h2d_gpu_elapsed", 0.0) > 0:
            print(f"h2d GPU bandwidth:  {h2d_gb / prof_sum['h2d_gpu_elapsed']:.3f} GB/s")

        if total_dt > 0:
            print(f"end-to-end input throughput: {input_gb / total_dt:.3f} GB/s")

        print("")

    def enqueue_h2d_from_slot(slot_id):
        host_arr = shm_arrays[slot_id]
        prof_add_bytes("h2d_bytes", host_arr.nbytes)

        if tictoc:
            h2d_start = cp.cuda.Event()
            h2d_end = cp.cuda.Event()
        else:
            h2d_start = None
            h2d_end = cp.cuda.Event(disable_timing=True)

        t0 = now()
        with stream_h2d:
            if tictoc:
                h2d_start.record(stream_h2d)

            # This copies from shared host memory to GPU.
            # Note: shared_memory is not CUDA pinned memory, so this may not have
            # the same async behavior as a true pinned host buffer.
            d_frames = cp.asarray(host_arr)

            h2d_end.record(stream_h2d)

        prof_add("h2d_enqueue_cpu", now() - t0)

        return d_frames, h2d_end, h2d_start, slot_id

    def get_ready_item():
        t0 = now()
        item = ready_queue.get()
        prof_add("ready_queue_get", now() - t0)

        slot_id, batch_index, read_dt, copy_dt, nbytes, err = item

        if err is not None:
            raise RuntimeError(f"Shared-memory fetch worker failed: {err}")

        prof_add("worker_read_frames", read_dt)
        prof_add("worker_copy_to_shm", copy_dt)
        prof_add_bytes("input_bytes", nbytes)

        return slot_id, batch_index

    try:
        # ------------------------------------------------------------
        # 1. Read the first batch in the main process to infer shape/dtype.
        # ------------------------------------------------------------
        t0 = now()
        file_reader = FileReaderFactory.create(file_path)
        file_reader.open()
        try:
            first_frames = file_reader.read_frames(first_frame, batch_size)
        finally:
            file_reader.close()

        prof_add("first_batch_read_for_shape", now() - t0)
        prof_add_bytes("input_bytes", first_frames.nbytes)

        frame_shape = tuple(first_frames.shape)
        frame_dtype = first_frames.dtype
        frame_dtype_str = frame_dtype.str
        frame_nbytes = int(first_frames.nbytes)

        # ------------------------------------------------------------
        # 2. Allocate shared-memory slots.
        # ------------------------------------------------------------
        t0 = now()
        for _ in range(SHM_NUM_SLOTS):
            shm = shared_memory.SharedMemory(create=True, size=frame_nbytes)
            arr = np.ndarray(frame_shape, dtype=frame_dtype, buffer=shm.buf)
            shm_objects.append(shm)
            shm_arrays.append(arr)

        prof_add("shared_memory_create_total", now() - t0)

        shm_names = [shm.name for shm in shm_objects]

        # ------------------------------------------------------------
        # 3. Fill slot 0 with the first batch.
        # ------------------------------------------------------------
        t0 = now()
        np.copyto(shm_arrays[0], first_frames)
        prof_add("first_batch_copy_to_shm", now() - t0)

        del first_frames

        # ------------------------------------------------------------
        # 4. Queues carry only small metadata now.
        # ------------------------------------------------------------
        free_queue = mp.Queue(maxsize=SHM_NUM_SLOTS)
        ready_queue = mp.Queue(maxsize=SHM_NUM_SLOTS)

        # Slot 0 is already occupied by batch 0.
        for slot_id in range(1, SHM_NUM_SLOTS):
            free_queue.put(slot_id)

        # Manually enqueue first batch metadata.
        ready_queue.put((0, 0, 0.0, 0.0, frame_nbytes, None))

        # ------------------------------------------------------------
        # 5. Launch workers for batches 1..num_batch-1.
        # ------------------------------------------------------------
        remaining_batch_indices = list(range(1, num_batch))
        batch_indices_per_worker = [[] for _ in range(FETCH_NUM_WORKERS)]

        for i, batch_index in enumerate(remaining_batch_indices):
            worker_id = i % FETCH_NUM_WORKERS
            batch_indices_per_worker[worker_id].append(batch_index)

        t0 = now()
        for worker_id in range(FETCH_NUM_WORKERS):
            indices = batch_indices_per_worker[worker_id]
            if not indices:
                continue

            p = mp.Process(
                target=_fetch_batch_worker_sharedmem,
                args=(
                    worker_id,
                    indices,
                    file_path,
                    first_frame,
                    batch_stride,
                    batch_size,
                    shm_names,
                    frame_shape,
                    frame_dtype_str,
                    free_queue,
                    ready_queue,
                )
            )
            processes.append(p)
            p.start()

        prof_add("worker_process_start_total", now() - t0)

        # ------------------------------------------------------------
        # 6. Prime first H2D.
        # ------------------------------------------------------------
        slot_id, batch_index = get_ready_item()
        d_frames, ready_event, h2d_start, active_slot_id = enqueue_h2d_from_slot(slot_id)
        active_batch_index = batch_index

        # ------------------------------------------------------------
        # 7. Streaming loop.
        # ------------------------------------------------------------
        for _ in tqdm(range(num_batch)):
            # Wait for current H2D.
            t0 = now()
            ready_event.synchronize()
            prof_add("h2d_wait_cpu", now() - t0)

            if tictoc and h2d_start is not None:
                h2d_ms = cp.cuda.get_elapsed_time(h2d_start, ready_event)
                prof_add("h2d_gpu_elapsed", h2d_ms / 1000.0)

            # H2D from this shared-memory slot is complete.
            # The slot can be reused by a worker.
            free_queue.put(active_slot_id)

            # Enqueue next H2D before compute if a next batch exists.
            # This lets H2D of next batch overlap with compute of current batch.
            d_frames_next = None
            ready_event_next = None
            h2d_start_next = None
            active_slot_id_next = None
            active_batch_index_next = None

            if processed_batches + 1 < num_batch:
                slot_id_next, batch_index_next = get_ready_item()
                d_frames_next, ready_event_next, h2d_start_next, active_slot_id_next = enqueue_h2d_from_slot(slot_id_next)
                active_batch_index_next = batch_index_next

            # Compute current batch.
            if tictoc:
                compute_start = cp.cuda.Event()
                compute_end = cp.cuda.Event()
            else:
                compute_start = None
                compute_end = cp.cuda.Event(disable_timing=True)

            t0 = now()
            with stream_compute:
                if tictoc:
                    compute_start.record(stream_compute)

                res, accu = render_moments(
                    bm,
                    parameters,
                    frames=d_frames,
                    registration_ref=M0_reg
                )

                compute_end.record(stream_compute)

            prof_add("compute_enqueue_cpu", now() - t0)

            t0 = now()
            compute_end.synchronize()
            prof_add("compute_wait_cpu", now() - t0)

            if tictoc:
                compute_ms = cp.cuda.get_elapsed_time(compute_start, compute_end)
                prof_add("compute_gpu_elapsed", compute_ms / 1000.0)

            if res is None:
                break

            # Store results.
            t0 = now()

            for key in accu.keys():
                if key not in out_accumulation:
                    out_accumulation[key] = accu[key]
                else:
                    out_accumulation[key] += accu[key]

            l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
            for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
                l.append(res[f"band_{k}_{f1}_{f2}"])

            # Warning: appending still stores in arrival order, not necessarily batch_index order.
            out_list.append(bm.xp.stack(l, axis=0))

            if "coefs" in res and coefs_list is not None:
                coefs_list[active_batch_index] = res["coefs"]

            if "registration" in res and reg_list is not None:
                reg_list[active_batch_index] = res["registration"]

            prof_add("postprocess_accumulate_and_store", now() - t0)

            if debug_manager and lock:
                t0 = now()
                with lock:
                    res_store[active_batch_index] = res
                debug_queue.put(active_batch_index)
                prof_add("debug_manager_store", now() - t0)

            processed_batches += 1

            d_frames = d_frames_next
            ready_event = ready_event_next
            h2d_start = h2d_start_next
            active_slot_id = active_slot_id_next
            active_batch_index = active_batch_index_next

            if d_frames is None:
                break

        normal_exit = True

    finally:
        # ------------------------------------------------------------
        # Final accumulation.
        # ------------------------------------------------------------
        t0 = now()
        denom = max(processed_batches, 1)
        for key in out_accumulation.keys():
            out_accumulation[key] /= denom
        prof_add("final_average_accumulation", now() - t0)

        # ------------------------------------------------------------
        # Stop workers safely on abnormal exit.
        # ------------------------------------------------------------
        t0 = now()
        if not normal_exit:
            for p in processes:
                if p.is_alive():
                    p.terminate()

        for p in processes:
            p.join()

        prof_add("worker_join_total", now() - t0)

        # ------------------------------------------------------------
        # CUDA sync.
        # ------------------------------------------------------------
        t0 = now()
        stream_h2d.synchronize()
        stream_compute.synchronize()
        cp.cuda.Device().synchronize()
        prof_add("final_cuda_synchronize", now() - t0)

        # ------------------------------------------------------------
        # Queue cleanup.
        # ------------------------------------------------------------
        try:
            if free_queue is not None:
                free_queue.close()
                free_queue.join_thread()
        except Exception:
            pass

        try:
            if ready_queue is not None:
                ready_queue.close()
                ready_queue.join_thread()
        except Exception:
            pass

        # ------------------------------------------------------------
        # Shared-memory cleanup.
        # ------------------------------------------------------------
        t0 = now()
        for shm in shm_objects:
            try:
                shm.close()
            except Exception:
                pass

            try:
                shm.unlink()
            except FileNotFoundError:
                pass
            except Exception:
                pass

        prof_add("shared_memory_cleanup", now() - t0)

        print_profile()
# def _process_memmap(bm, memmap, parameters, num_batch, first_frame, batch_stride, batch_size,
#                     M0_reg, out_list, coefs_list, reg_list, debug_manager, debug_queue, res_store, lock):
#     for i in tqdm(range(num_batch)):
#         start = i * batch_stride
#         frames_np = memmap[start:start + batch_size]
#         frames = bm.to_backend(frames_np)
#         res, accu = render_moments(bm, parameters, frames=frames, registration_ref=M0_reg)
#         if res is None: break
#         l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
#         for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
#             l.append(res[f"band_{k}_{f1}_{f2}"])
#         out_list.append(bm.xp.stack(l, axis=0))
#         if "coefs" in res and coefs_list is not None: coefs_list[i] = res["coefs"]
#         if "registration" in res and reg_list is not None: reg_list[i] = res["registration"]
#         if debug_manager and lock:
#             with lock: res_store[i] = res
#             debug_queue.put(i)

def _process_gpu_streaming_onram_multistream(bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
                                              M0_reg, out_list, coefs_list, reg_list,
                                              debug_manager, debug_queue, res_store, lock, end_frame):
    import cupy as cp
    all_frames = file_reader.read_frames(first_frame, end_frame - first_frame)
    all_frames = np.asarray(all_frames)
    n_streams = parameters.get("gpu_multistream_count", 8)
    batch_starts = [i * batch_stride for i in range(num_batch)]

    for chunk_start in tqdm(range(0, num_batch, n_streams)):
        chunk_size = min(n_streams, num_batch - chunk_start)
        streams = []
        batch_results = [None] * chunk_size

        for j in range(chunk_size):
            i = chunk_start + j
            start = batch_starts[i]
            frames_sub = all_frames[start : start + batch_size]
            stream = cp.cuda.Stream(non_blocking=True)
            with stream:
                d_frames = cp.asarray(frames_sub)
                res, accu = render_moments(bm, parameters, frames=d_frames, registration_ref=M0_reg)
            streams.append(stream)
            batch_results[j] = res

        for stream in streams:
            stream.synchronize()

        for j in range(chunk_size):
            i = chunk_start + j
            res = batch_results[j]
            if res is None: break
            l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
            for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
                l.append(res[f"band_{k}_{f1}_{f2}"])
            out_list.append(bm.xp.stack(l, axis=0))
            if "coefs" in res and coefs_list is not None: coefs_list[i] = res["coefs"]
            if "registration" in res and reg_list is not None: reg_list[i] = res["registration"]
            if debug_manager is not None and lock is not None:
                with lock: res_store[i] = res
                debug_queue.put(i)
