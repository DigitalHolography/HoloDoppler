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
from holodoppler.file_io import FileReaderFactory

import os
import time
import threading
import queue
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import imageio as iio
from tqdm import tqdm

# Optional line profiler
try:
    import lblprof
except ImportError:
    lblprof = None

from holodoppler.utils import load_config

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

def print_timings_summary():
    """Print cumulated time, calls, ratio, and total for all tracked functions."""
    with _timings_lock:
        total = sum(v["cum_time"] for v in _func_timings.values())
    if total == 0:
        return

    print("\n[ Timing Summary ]")
    print(f"{'Function':<45} | {'Calls':>5} | {'Time (s)':>10} | {'Ratio':>6}")
    print("-" * 78)
    sorted_funcs = sorted(_func_timings.items(), key=lambda x: x[1]["cum_time"], reverse=True)
    for fname, data in sorted_funcs:
        ratio = data["cum_time"] / total if total > 0 else 0
        print(f"{fname:<45} | {data['calls']:>5} | {data['cum_time']:>10.4f} | {ratio:>6.2%}")
    print(f"{'TOTAL':<45} | {'':>5} | {total:>10.4f} | 100.00%")
    print("-" * 78)
    
calculate_displacements_graph_laplacian = track_time('calculate_displacements_graph_laplacian')(calculate_displacements_graph_laplacian)
calculate_displacements = track_time('calculate_displacements')(calculate_displacements)
fit_zernike = track_time('fit_zernike')(fit_zernike)
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
                self.accumulators[k] = self.xp.zeros_like(v)
        # In-place addition
        for k, v in data_dict.items():
            if k in self.accumulators:
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
                parameters["svd_threshold"]
            )
        elif prop_method == "AngularSpectrum":
            U = construct_subapertures_angular(
                xp, fft, frames_sub, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], parameters["z"], parameters["low_freq"], parameters.get("high_freq"),
                parameters["sampling_freq"], frames_sub.shape[0], parameters["shack_hartmann_nx_subap"],
                parameters["shack_hartmann_ny_subap"], parameters["svd_threshold"]
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
        coefs, phase = fit_zernike(
            xp, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
            parameters["wavelength"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
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
                phase_term, zero_padding=zero_pad
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
                zero_padding=zero_pad
            )
        elif prop_method == "AngularSpectrum":
            holograms = angular_spectrum_transform(
                xp, fft, frames_sub, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
                zero_padding=zero_pad
            )

    # SVD filtering
    holograms_f = svd_filter(xp, holograms, 1e20, filter_mode="amplitude_threshold")
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
            holo_nofix = fresnel_transform(xp, fft, frames_sub, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"], zero_padding=zero_pad)
        elif prop_method == "AngularSpectrum":
            holo_nofix = angular_spectrum_transform(xp, fft, frames_sub, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"], zero_padding=zero_pad)
        holo_nofix_f = svd_filter(xp, holo_nofix, parameters["svd_threshold"])
        spec_nofix = fourier_time_transform(xp, fft, holo_nofix_f)
        psd_nofix = xp.abs(spec_nofix[idxs]) ** 2
        batch["M0notfixed"] = moment(xp, psd_nofix, freqs, 0)
        del holo_nofix, holo_nofix_f, spec_nofix, psd_nofix

    if compute_debug:
        batch["spectrum_line"] = xp.mean(psd, axis=(-1, -2))
        batch["freqs"] = freqs

    return batch

# ------------------------------------------------------------------
# Render moments for a single batch
# ------------------------------------------------------------------
def render_moments(bm, parameters, frames=None, registration_ref=None):
    xp = bm.xp
    nt, ny, nx = frames.shape
    res = {}
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

    # --- Image registration ---
    if parameters.get("image_registration", False) and registration_ref is not None:
        M0_ff = res["M0ff"]#gaussian_flatfield(res["M0"], parameters.get("registration_flatfield_gw", 1.0), bm.gaussian_filter)
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
        res["registration"] = reg

    return res

# ------------------------------------------------------------------
# Footer parameter update
# ------------------------------------------------------------------
def update_from_footer(parameters, holofooter):
    try:
        if parameters.get("wavelength") == "use_holovibes" and holofooter is not None:
            parameters["wavelength"] = holofooter["compute_settings"]["image_rendering"]["lambda"]
        if parameters.get("z") == "use_holovibes" and holofooter is not None:
            parameters["z"] = holofooter["compute_settings"]["image_rendering"]["propagation_distance"]
        if parameters.get("pixel_pitch") == "use_holovibes" and holofooter is not None:
            parameters["pixel_pitch"] = (holofooter["info"]["pixel_pitch"]["y"], holofooter["info"]["pixel_pitch"]["x"])
        if parameters.get("sampling_freq") == "use_holovibes" and holofooter is not None:
            parameters["sampling_freq"] = holofooter["info"]["camera_fps"]
    except Exception as e:
        print(f"Issue from holovibes footer: {e}")
    return parameters

# ------------------------------------------------------------------
# Preview (single batch)
# ------------------------------------------------------------------
def preview_process_moments(file_path, parameters, tictoc=True):
    bm = BackendManager(backend=parameters["backend"])
    file_reader = FileReaderFactory.create(file_path)
    file_reader.open()
    
    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)
    print("parameters : ", parameters)
    
    batch_size = parameters["batch_size"]
    first_frame = parameters["first_frame"]
    frames = file_reader.read_frames(first_frame, batch_size)
    frames = bm.to_backend(frames)
    res = render_moments(bm, parameters, frames=frames)
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
def process_moments(file_path, parameters, mp4_path=None, return_numpy=False, holodoppler_path=True, tictoc=True):
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
    if parameters.get("use_memmap", False) and hasattr(file_reader, "get_np_memmap"):
        try:
            memmap = file_reader.get_np_memmap()[first_frame:end_frame]
        except Exception as e:
            print(f"Memmap loading failed: {e}, falling back to regular reads.")
            memmap = None
    else:
        memmap = None

    out_list = []
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
        M0_reg = render_moments(bm, parameters, frames=frames_reg)["M0ff"]
        # M0_reg = gaussian_flatfield(M0_reg, parameters.get("registration_flatfield_gw", 1.0), bm.gaussian_filter)

    # Dispatch to backend-specific loop
    if memmap is not None:
        _process_memmap(bm, memmap, parameters, num_batch, first_frame, batch_stride, batch_size,
                        M0_reg, out_list, coefs_list, reg_list, debug_manager, debug_queue, res_store, lock)
    elif parameters["backend"] == "cupy":
        _process_gpu_streaming(bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
                               M0_reg, out_list, coefs_list, reg_list, debug_manager, debug_queue, res_store, lock)
    elif parameters["backend"] == "cupyRAM":
        _process_gpu_streaming_onram(bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
                                     M0_reg, out_list, coefs_list, reg_list, debug_manager, debug_queue, res_store, lock)
    elif parameters["backend"] == "cupyRAMmultistream":
        _process_gpu_streaming_onram_multistream(bm, file_reader, parameters, num_batch, first_frame, batch_stride,
                                                 batch_size, M0_reg, out_list, coefs_list, reg_list,
                                                 debug_manager, debug_queue, res_store, lock, end_frame)
    else:
        _process_cpu(bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
                     M0_reg, out_list, coefs_list, reg_list, debug_manager, debug_queue, res_store, lock)

    file_reader.close()
    
    @track_time("collecting")
    def collecting(bm,out_list,debug_manager,debug_queue,stop_event,debug_thread,coefs_list,reg_list,compute_debug,debug_results,num_batch,parameters):

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
        

        if coefs_list is not None:
            coefs_list = [bm.to_numpy(c) for c in coefs_list]
        # print(f"coefs_list: {time.time()-t0:.2f}s")
        if reg_list is not None:
            reg_list = [bm.to_numpy(r) for r in reg_list]
        # print(f"reg_list: {time.time()-t0:.2f}s")

        vid_debug = {}
        if compute_debug and debug_results:
            for key in debug_results[0].keys():
                vid_debug[key] = np.stack([bm.to_numpy(debug_results[k][key]) for k in range(num_batch)], axis=0)
        # print(f"vid_debug: {time.time()-t0:.2f}s")
        return vid_t, vid_debug
    
    vid_t, vid_debug = collecting(bm,out_list,debug_manager,debug_queue,stop_event,debug_thread,coefs_list,reg_list,compute_debug,debug_results,num_batch,parameters)
    
    print(vid_t.shape)
    t0 = time.time()
    # Spatial transforms
    if parameters.get("square", False):
        m = max(vid_t.shape[-2], vid_t.shape[-1])
        vid_t = zoom_slicewise_fast(vid_t, m, m, use_gpu=bm.is_gpu)
    print(f"square: {time.time()-t0:.2f}s")
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

    if tictoc:
        print_timings_summary()

    if return_numpy:
        return vid_t
    return None

# ------------------------------------------------------------------
# Specialised loops
# ------------------------------------------------------------------
def _process_cpu(bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
                 M0_reg, out_list, coefs_list, reg_list, debug_manager, debug_queue, res_store, lock):
    for i in tqdm(range(num_batch)):
        frames = file_reader.read_frames(first_frame + i * batch_stride, batch_size)
        frames = bm.to_backend(frames)
        res = render_moments(bm, parameters, frames=frames, registration_ref=M0_reg)
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

def _process_gpu_streaming(bm, file_reader, parameters, num_batch, first_frame, batch_stride,
                           batch_size, M0_reg, out_list, coefs_list, reg_list,
                           debug_manager, debug_queue, res_store, lock):
    import cupy as cp
    stream_h2d = cp.cuda.Stream(non_blocking=True)
    stream_compute = cp.cuda.Stream(non_blocking=True)

    frames_next = file_reader.read_frames(first_frame, batch_size)
    frames_next = bm.to_backend(frames_next)
    with stream_h2d:
        d_frames_next = cp.asarray(frames_next)

    for i in tqdm(range(num_batch)):
        d_frames = d_frames_next
        if i + 1 < num_batch:
            with stream_h2d:
                frames_next = file_reader.read_frames(first_frame + (i+1) * batch_stride, batch_size)
                d_frames_next = cp.asarray(frames_next)
        with stream_compute:
            res = render_moments(bm, parameters, frames=d_frames, registration_ref=M0_reg)
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
        stream_compute.synchronize()
    stream_h2d.synchronize()
    cp.cuda.Device().synchronize()

@track_time("_process_gpu_streaming_onram")
def _process_gpu_streaming_onram(bm, file_reader, parameters, num_batch, first_frame, batch_stride,
                                 batch_size, M0_reg, out_list, coefs_list, reg_list,
                                 debug_manager, debug_queue, res_store, lock):
    import queue as qmod
    import threading
    from tqdm import tqdm
    import cupy as cp

    frame_queue = qmod.Queue(maxsize=4)
    stop_reader = threading.Event()

    def reader():
        frame_idx = first_frame
        try:
            for i in range(num_batch):
                if stop_reader.is_set(): break
                frames = file_reader.read_frames(frame_idx, batch_size)
                frame_queue.put((i, frames))
                frame_idx += batch_stride
        finally:
            frame_queue.put(None)

    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()

    stream_h2d = cp.cuda.Stream(non_blocking=True)
    stream_compute = cp.cuda.Stream(non_blocking=True)
    h2d_done = cp.cuda.Event(disable_timing=True)

    def enqueue_h2d(frames):
        if frames is None: return None, None
        with stream_h2d:
            d_frames = cp.asarray(frames)
            event = cp.cuda.Event(disable_timing=True)
            event.record(stream_h2d)
        return d_frames, event

    try:
        item = frame_queue.get()
        if item is None: return
        _, frames = item
        d_frames, ready_event = enqueue_h2d(frames)

        for i in tqdm(range(num_batch)):
            next_item = frame_queue.get() if i + 1 < num_batch else None
            d_frames_next = None
            ready_event_next = None
            if next_item is not None:
                _, frames_next = next_item
                d_frames_next, ready_event_next = enqueue_h2d(frames_next)

            with stream_compute:
                stream_compute.wait_event(ready_event)
                res = render_moments(bm, parameters, frames=d_frames, registration_ref=M0_reg)
            stream_compute.synchronize()
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
            d_frames = d_frames_next
            ready_event = ready_event_next
            if d_frames is None: break

    finally:
        stop_reader.set()
        reader_thread.join(timeout=5)
        stream_h2d.synchronize()
        stream_compute.synchronize()
        cp.cuda.Device().synchronize()

def _process_memmap(bm, memmap, parameters, num_batch, first_frame, batch_stride, batch_size,
                    M0_reg, out_list, coefs_list, reg_list, debug_manager, debug_queue, res_store, lock):
    for i in tqdm(range(num_batch)):
        start = i * batch_stride
        frames_np = memmap[start:start + batch_size]
        frames = bm.to_backend(frames_np)
        res = render_moments(bm, parameters, frames=frames, registration_ref=M0_reg)
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
                res = render_moments(bm, parameters, frames=d_frames, registration_ref=M0_reg)
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
