from holodoppler.saving import save_outputs
from holodoppler.propagation import fresnel_transform, fresnel_transform_with_phase, angular_spectrum_transform, angular_spectrum_transform_with_phase
from holodoppler.shack_hartmann import construct_subapertures_fresnel, construct_subapertures_angular, calculate_displacements, calculate_displacements_graph_laplacian
from holodoppler.zernike import fit_zernike_fresnel, fit_zernike_angular_spectrum, southwell_phase_integration
from holodoppler.utils import resize_slicewise, zoom_slicewise_fast, pad_array_centrally, gaussian_flatfield, update_from_footer
from holodoppler.filtering import svd_filter, frequency_symmetric_filtering, fourier_time_transform, corner_compensation
from holodoppler.moments import moment
from holodoppler.registration import register_trs, apply_registration, apply_registration3D
from holodoppler.plotting import DebugPlotterManager
from holodoppler.backend import BackendManager
from holodoppler.file_reader import FileReaderFactory, CineFileReader, HoloFileReader

import os
import time

import threading
import queue
from multiprocessing import Process, Queue, Event, JoinableQueue

import numpy as np
import cupy as cp
import matplotlib.pyplot as plt

import imageio as iio
from tqdm import tqdm

from collections import defaultdict

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
        # if compute_debug:
        #     spectrum_f_angle = fourier_time_transform(xp, fft, xp.angle(holograms_f))
    else:
        spectrum_f = holograms_f
        # if compute_debug:
        #     spectrum_f_angle = None

    # Frequency selection
    idxs, freqs = frequency_symmetric_filtering(
        xp, fft, nt_sub, parameters["sampling_freq"], parameters["low_freq"], parameters.get("high_freq")
    )
    psd = xp.abs(spectrum_f) ** 2
    # if compute_debug:
    #     psd_angle = xp.abs(spectrum_f_angle) ** 2

    if parameters.get("corner_compensation", False):
        psd = corner_compensation(xp, psd)

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
    frames = file_reader.read_frames(first_frame=first_frame, batch_size=batch_size)
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

    for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
        key = f"band_{k}_{f1}_{f2}"
        debug_imgs[key] = res[key]

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


def _debug_plotting_worker(input_q, output_q, stop_ev, params):
    """
    Runs in a separate process. Creates its own DebugPlotterManager,
    optionally times plot_all, and processes tasks until a None sentinel.
    """
    # Prevent GPU usage in this worker process

    try:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''

        mgr = DebugPlotterManager(params)

        if track_time is not None:
            mgr.plot_all = track_time("debug_manager_plot_all")(mgr.plot_all)

        while True:
            # print("hey")
            try:
                item = input_q.get(timeout=0.1)
            except queue.Empty:
                if stop_ev.is_set() and input_q.empty():
                    break
                continue
            # print("ho")


            if item is None:            # sentinel → shut down after this task
                input_q.task_done()     # mark sentinel as done
                output_q.put(None)     # sentinel
                break

            i, res = item
            # print(i)
            try:
                # print(f"plotting {i}")
                out = mgr.plot_all(res)
                output_q.put((i, out))
                # print(i)
            except Exception as e:
                output_q.put((i, e))
            finally:
                input_q.task_done()     # mark actual task as done

        # Drain any remaining items that arrived after the sentinel
        while not input_q.empty():
            try:
                item = input_q.get_nowait()
                if item is None:
                    input_q.task_done()
                    output_q.put(None)
                    continue
                i, res = item
                out = mgr.plot_all(res)
                output_q.put((i, out))
                input_q.task_done()
            except queue.Empty:
                break
        # print("close_all")
        mgr.close_all()
        # print("bye")
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(traceback_str)
    finally:
        pass
        # print("bye")

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
        end_frame = file_reader.file_header.num_frames if file_reader.ext == ".holo" else file_reader.TotalImageCount

    if batch_stride >= (end_frame - first_frame):
        num_batch = 1 if batch_size <= (end_frame - first_frame) else 0
    else:
        num_batch = int((end_frame - first_frame) / batch_stride)
    if num_batch <= 0:
        return None

    debug = parameters.get("debug")

    out_list = []
    out_accumulation = {}
    coefs_list = [None] * num_batch if parameters.get("shack_hartmann") else None
    reg_list = [None] * num_batch if parameters.get("image_registration") else None

    debug_results = {}
    debug_input_queue = None
    debug_output_queue = None
    debug_plot_process = None
    _stop_event = None

    if debug:
        _stop_event = Event()
        debug_input_queue = JoinableQueue(maxsize=14)   # <-- JoinableQueue now
        debug_output_queue = Queue()

        debug_plot_process = Process(
            target=_debug_plotting_worker,
            args=(debug_input_queue, debug_output_queue, _stop_event, parameters),
            daemon=True
        )
        debug_plot_process.start()

        # ---- Helper functions (used by the main loop) ----
        def submit_debug_task(i, res_dict):
            """Enqueue a debug task. Converts any GPU arrays to CPU numpy arrays."""
            cpu_res = {}
            for k, v in res_dict.items():
                if hasattr(v, 'get'):# cupy array
                    cpu_res[k] = v.get()

            debug_input_queue.put((i, cpu_res))

        def shutdown_debug_plotter():
            """Gracefully stop the worker process and collect remaining results."""
            debug_input_queue.put(None)# sentinel
            debug_input_queue.join()# wait until last input sent

            # wait until last output received (sentinel)
            print("Collecting the debug plotting process videos...")
            while True:
                item = debug_output_queue.get()

                if item is None: #sentinel
                    break

                i, out = item
                debug_results[i] = out
            
            debug_plot_process.join()

    else:
        submit_debug_task = None
        collect_debug_results = None
        shutdown_debug_plotter = None

    # Registration reference
    M0_reg = None
    if parameters.get("image_registration"):
        frames_reg = file_reader.read_frames(first_frame=first_frame, batch_size=parameters.get("batch_size_registration", batch_size))
        frames_reg = bm.to_backend(frames_reg)
        M0_reg = render_moments(bm, parameters, frames=frames_reg)[0]["M0ff"]
        # M0_reg = gaussian_flatfield(M0_reg, parameters.get("registration_flatfield_gw", 1.0), bm.gaussian_filter)

    bm.clear_gpu_memory()
    # bm.print_gpu_used_memory()

    # Dispatch to backend-specific loop
    if parameters["backend"] == "cupyRAM":
        _process_gpu_streaming_onram(bm, file_reader.file_path, parameters, num_batch, end_frame, first_frame, batch_stride, batch_size,
                                     M0_reg, out_list, out_accumulation, coefs_list, reg_list, debug, submit_debug_task)
    elif parameters["backend"] == "numpy":
        _process_cpu_streaming(bm, file_reader, parameters, num_batch, end_frame, first_frame, batch_stride, batch_size,
                     M0_reg, out_list, out_accumulation, coefs_list, reg_list, debug, submit_debug_task)
    elif "cupy" in parameters["backend"]:
        _process_cpu_streaming(bm, file_reader, parameters, num_batch, end_frame, first_frame, batch_stride, batch_size,
                     M0_reg, out_list, out_accumulation, coefs_list, reg_list, debug, submit_debug_task)
    else : 
        raise ValueError(f"backend requested not implemented :{parameters["backend"]}")

    if coefs_list is not None:
            coefs_list = [bm.to_numpy(c) for c in coefs_list]
    # print(f"coefs_list: {time.time()-t0:.2f}s")
    if reg_list is not None:
        reg_list = [bm.to_numpy(r) for r in reg_list]

    
    
    @track_time("collecting")
    def collecting(bm,out_list,out_accumulation,debug,coefs_list,reg_list,num_batch,parameters):
        np_list = [bm.to_numpy(xparr) for xparr in out_list]
        vid_t = np.stack(np_list, axis=0)
        bm.clear_gpu_memory()
        if debug:
            shutdown_debug_plotter()
        vid_debug = {}
        if debug and debug_results:
            for key in debug_results[0].keys():
                try:
                    vid_debug[key] = np.stack([bm.to_numpy(debug_results[k][key]) for k in range(num_batch)], axis=0)
                except Exception as e:
                    # import traceback
                    # print(traceback.format_exc())
                    print(f"Couldn't stack debug output {key}: ", e)
        if debug and out_accumulation:
            for key in out_accumulation.keys():
                if out_accumulation[key].ndim == 3:
                    vid_debug[key] = bm.to_numpy(out_accumulation[key])
        return vid_t, vid_debug

    vid_t, vid_debug = collecting(bm,out_list,out_accumulation,debug,coefs_list,reg_list,num_batch,parameters)
    
    if parameters.get("square", False):
        m = max(vid_t.shape[-2], vid_t.shape[-1])
        vid_t = zoom_slicewise_fast(vid_t, m, m, use_gpu=bm.is_gpu)
    if parameters.get("transpose", False):
        vid_t = np.transpose(vid_t, axes=(0, 1, 3, 2))
    if parameters.get("flip_x", False):
        vid_t = np.flip(vid_t, axis=-1)
    if parameters.get("flip_y", False):
        vid_t = np.flip(vid_t, axis=-2)

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
def _process_cpu_streaming(bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
                 M0_reg, out_list, out_accumulation, coefs_list, reg_list, debug, submit_debug_task):
    for i in tqdm(range(num_batch)):

        frames = file_reader.read_frames(first_frame=first_frame+i*batch_stride, batch_size=batch_size)
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
        if debug:
            submit_debug_task(i, res)


class PrefetchBuffer:
    """Double-buffer for CPU→GPU transfers with prefetch capability."""
    
    def __init__(self, num_slots=2):
        self.num_slots = num_slots
        self.slots = [None] * num_slots  # Each slot: (np_array, cuda_array, event)
        self.write_idx = 0
        self.read_idx = 0
        self.ready_count = 0
        self.stream = cp.cuda.Stream(non_blocking=True)
    
    def put(self, np_array, block=True):
        """Copy numpy array to a GPU buffer slot asynchronously."""
        slot = self.write_idx % self.num_slots
        
        with self.stream:
            d_array = cp.asarray(np_array)
            event = cp.cuda.Event()
            event.record(self.stream)
        
        self.slots[slot] = (np_array, d_array, event)
        self.write_idx += 1
        self.ready_count += 1
    
    def get(self):
        """Get the next available GPU buffer (blocks until ready)."""
        while self.ready_count == 0:
            time.sleep(0)  # Yield to other threads
        
        slot = self.read_idx % self.num_slots
        np_array, d_array, event = self.slots[slot]
        
        # Wait for the async copy to complete
        event.synchronize()
        
        self.read_idx += 1
        self.ready_count -= 1
        
        return np_array, d_array
    
    def synchronize(self):
        """Synchronize the transfer stream."""
        self.stream.synchronize()

@track_time("_process_gpu_streaming_onram")
def _process_gpu_streaming_onram(bm, file_path, parameters, num_batch, end_frame, first_frame, batch_stride,
                                 batch_size, M0_reg, out_list, out_accumulation, coefs_list, reg_list,
                                 debug, submit_debug_task):
    """
    GPU streaming pipeline using iterator-based frame reading with double-buffering.
    """
    
    tictoc = bool(parameters.get("tictoc", False))
    
    if num_batch <= 0:
        return
    
    # Open file reader and get the frame iterator
    file_reader = FileReaderFactory.create(file_path)
    file_reader.open()
    
    try:
        # Create CUDA streams
        h2d_stream = cp.cuda.Stream(non_blocking=True)
        compute_stream = cp.cuda.Stream(non_blocking=True)
        
        processed_batches = 0
        
        # Use simple double-buffering with explicit state
        d_current = None
        d_next = None
        h2d_event_current = None
        h2d_event_next = None
        
        # Start reading frames
        for i, frames in enumerate(tqdm(file_reader.iter_frames(
            first_frame=first_frame,
            end_frame = end_frame,
            batch_size=batch_size,
            batch_stride=batch_stride
        ), total=num_batch)):
            
            # Start async H2D transfer for this batch
            with h2d_stream:
                d_next = cp.asarray(frames)
                h2d_event_next = cp.cuda.Event()
                h2d_event_next.record(h2d_stream)
            
            # If we have a previous batch, wait for its H2D and compute it
            if d_current is not None:
                # Wait for H2D of current batch to complete
                h2d_event_current.synchronize()
                
                # Compute current batch on compute stream
                with compute_stream:
                    res, accu = render_moments(
                        bm, parameters,
                        frames=d_current,
                        registration_ref=M0_reg
                    )
                    compute_event = cp.cuda.Event()
                    compute_event.record(compute_stream)
                
                # Wait for compute to finish
                compute_event.synchronize()
                
                if res is None:
                    break
                
                # Store results
                for key, value in accu.items():
                    if key not in out_accumulation:
                        out_accumulation[key] = value
                    else:
                        out_accumulation[key] += value
                
                l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
                for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
                    l.append(res[f"band_{k}_{f1}_{f2}"])
                
                out_list.append(bm.xp.stack(l, axis=0))
                
                if "coefs" in res and coefs_list is not None:
                    coefs_list[processed_batches] = res["coefs"]
                if "registration" in res and reg_list is not None:
                    reg_list[processed_batches] = res["registration"]
                
                if debug:
                    submit_debug_task(processed_batches, res)
                
                processed_batches += 1
            
            # Advance: next becomes current
            d_current = d_next
            h2d_event_current = h2d_event_next
        
        # Process the last batch
        if d_current is not None:
            h2d_event_current.synchronize()
            
            with compute_stream:
                res, accu = render_moments(
                    bm, parameters,
                    frames=d_current,
                    registration_ref=M0_reg
                )
                compute_event = cp.cuda.Event()
                compute_event.record(compute_stream)
            
            compute_event.synchronize()
            
            if res is not None:
                for key, value in accu.items():
                    if key not in out_accumulation:
                        out_accumulation[key] = value
                    else:
                        out_accumulation[key] += value
                
                l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
                for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
                    l.append(res[f"band_{k}_{f1}_{f2}"])
                
                out_list.append(bm.xp.stack(l, axis=0))
                
                if "coefs" in res and coefs_list is not None:
                    coefs_list[processed_batches] = res["coefs"]
                if "registration" in res and reg_list is not None:
                    reg_list[processed_batches] = res["registration"]
                
                if debug:
                    submit_debug_task(processed_batches, res)
                
                processed_batches += 1
        
    finally:
        # Finalize accumulations
        if processed_batches > 0:
            denom = processed_batches
            for key in out_accumulation:
                out_accumulation[key] /= denom
        
        # Synchronize CUDA
        h2d_stream.synchronize()
        compute_stream.synchronize()
        cp.cuda.Device().synchronize()
        
        # Close file reader
        try:
            file_reader.close()
        except Exception:
            pass
        