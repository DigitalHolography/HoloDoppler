from ..saving import *
from ..propagation import *
from ..shack_hartmann import *
from ..zernike import *
from ..utils import *
from ..filtering import *
from ..moments import moment
from ..registration import *
from ..plotting import *
from ..backend import BackendManager
from ..file_io import FileReaderFactory

import os
import json
import time
import threading
import queue
import traceback
from collections import defaultdict
from pathlib import Path
import subprocess
import h5py
import numpy as np
import matplotlib.pyplot as plt
import imageio as iio
from tqdm import tqdm

# Optional line profiler
try:
    import lblprof
except ImportError:
    lblprof = None


# ------------------------------------------------------------
# Helpers for parameter unpacking (readability)
# ------------------------------------------------------------

def _get_params(parameters):
    """Extract commonly used parameters into a simple namespace."""
    class P:
        pass
    p = P()
    p.wavelength = parameters["wavelength"]
    p.z = parameters["z"]
    p.pixel_pitch = parameters["pixel_pitch"]
    p.low_freq = parameters["low_freq"]
    p.high_freq = parameters.get("high_freq")
    p.sampling_freq = parameters["sampling_freq"]
    p.svd_threshold = parameters["svd_threshold"]
    p.shack_hartmann = parameters.get("shack_hartmann", False)
    p.sh_nx = parameters.get("shack_hartmann_nx_subap")
    p.sh_ny = parameters.get("shack_hartmann_ny_subap")
    p.sh_zernike_fit = parameters.get("shack_hartmann_zernike_fit", False)
    p.sh_zernike_modes = parameters.get("shack_hartmann_zernike_fit_modes")
    p.sh_southwell = parameters.get("shack_hartmann_southwell_phase_integration", False)
    p.sh_graph_laplacian = parameters.get("shack_hartmann_graph_laplacian", False)
    p.sh_pupil_thresh = parameters.get("shack_hartmann_pupil_threshold", 1.0)
    p.sh_dev_thresh = parameters.get("shack_hartmann_deviation_threshold", 3.0)
    p.sh_shift_range = parameters.get("shack_hartmann_shifts_pixel_range_threshold", 20.0)
    p.sh_graph_ref = parameters.get("shack_hartmann_graph_ref")
    p.sh_acc = parameters.get("shack_hartmann_accumulation", 1)
    p.main_acc = parameters.get("accumulation", 1)
    p.spatial_prop = parameters["spatial_propagation"]
    p.temporal_trans = parameters["temporal_transformation"]
    p.zero_padding = parameters.get("zero_padding")
    p.debug = parameters.get("debug", False)
    p.registration = parameters.get("image_registration", False)
    p.reg_type = parameters.get("image_registration_type", "translation_rotation_scale")
    p.reg_disc_ratio = parameters.get("registration_disc_ratio")
    p.apply_reg = parameters.get("apply_registration", False)
    p.reg_flatfield_gw = parameters.get("registration_flatfield_gw", 1.0)
    p.freq_bands = parameters.get("frequency_bands", [])
    p.square = parameters.get("square", False)
    p.transpose = parameters.get("transpose", False)
    p.flip_x = parameters.get("flip_x", False)
    p.flip_y = parameters.get("flip_y", False)
    return p


# ------------------------------------------------------------
# Shack-Hartmann sub‑pipeline
# ------------------------------------------------------------

def _process_shack_hartmann(bm, p, frames, registration_ref):
    """Run SH wavefront sensing & phase correction, return phase_term and optional debug info."""
    xp = bm.xp
    fft = bm.fft
    nt, ny, nx = frames.shape
    debug = {}

    # Sub‑aperture accumulation
    sub_batch_size = nt // p.sh_acc
    sub_batch_stride = sub_batch_size
    U_subaps_sum = None
    for it in range(p.sh_acc):
        frames_sub = frames[sub_batch_stride * it : sub_batch_stride * it + sub_batch_size]
        if p.spatial_prop == "Fresnel":
            U = construct_subapertures_fresnel(
                xp, fft, frames_sub, p.wavelength, p.z, p.pixel_pitch,
                p.low_freq, p.high_freq, p.sampling_freq,
                frames_sub.shape[0], p.sh_nx, p.sh_ny, p.svd_threshold
            )
        else:  # AngularSpectrum
            U = construct_subapertures_angular(
                xp, fft, frames_sub, p.pixel_pitch[0], p.pixel_pitch[1],
                p.wavelength, p.z, p.low_freq, p.high_freq, p.sampling_freq,
                frames_sub.shape[0], p.sh_nx, p.sh_ny, p.svd_threshold
            )
        U_subaps_sum = U if U_subaps_sum is None else U_subaps_sum + U

    U_subaps = U_subaps_sum / p.sh_acc
    if p.debug:
        debug["U_subaps"] = U_subaps

    # Displacement estimation
    if p.sh_graph_laplacian:
        shifts_y, shifts_x = calculate_displacements_graph_laplacian(
            xp, fft, U_subaps,
            pupil_threshold=p.sh_pupil_thresh,
            deviation_threshold=p.sh_dev_thresh,
            shifts_range=p.sh_shift_range
        )
    else:
        ny_s, nx_s, Ny, Nx = U_subaps.shape
        imref = p.sh_graph_ref
        if imref == "ref_from_registration":
            imref = None if registration_ref is None else resize_slicewise(
                registration_ref, Ny, Nx, xp=xp, fft=fft
            )
        shifts_y, shifts_x = calculate_displacements(
            xp, fft, U_subaps,
            pupil_threshold=p.sh_pupil_thresh,
            deviation_threshold=p.sh_dev_thresh,
            shifts_range=p.sh_shift_range,
            ref=imref
        )
    if p.debug:
        debug["shifts_y"] = shifts_y
        debug["shifts_x"] = shifts_x

    # Phase reconstruction
    if p.sh_zernike_fit:
        coefs, phase = fit_zernike(
            xp, ny, nx, p.pixel_pitch[0], p.pixel_pitch[1],
            p.wavelength, shifts_y, shifts_x, p.sh_zernike_modes
        )
        debug["coefs"] = coefs
    elif p.sh_southwell:
        phase = southwell_phase_integration(
            bm, ny, nx, p.pixel_pitch[0], p.pixel_pitch[1],
            p.wavelength, shifts_y, shifts_x
        )
    else:
        phase = None
    if p.debug:
        debug["phase"] = phase

    # Phase correction term
    phase_term = None
    if phase is not None:
        phase_term = xp.exp(-1j * phase)
        phase_term = xp.nan_to_num(phase_term, nan=0.0)
        if p.zero_padding:
            phase_term = pad_array_centrally(phase_term, p.zero_padding, xp)

    return phase_term, debug


# ------------------------------------------------------------
# Main processing of a sub‑batch (within one accumulation cycle)
# ------------------------------------------------------------

def _process_sub_batch(bm, p, frames_sub, phase_term, compute_debug):
    """Propagate, SVD‑filter, compute moments and frequency bands."""
    xp = bm.xp
    fft = bm.fft
    nt_sub = frames_sub.shape[0]

    # Propagation
    if phase_term is not None:
        if p.spatial_prop == "Fresnel":
            holograms = fresnel_transform_with_phase(
                xp, fft, frames_sub, p.z, p.pixel_pitch, p.wavelength,
                phase_term, zero_padding=p.zero_padding
            )
        else:
            holograms = angular_spectrum_transform_with_phase(
                xp, fft, frames_sub, p.z, p.pixel_pitch, p.wavelength,
                phase_term, zero_padding=p.zero_padding
            )
    else:
        if p.spatial_prop == "Fresnel":
            holograms = fresnel_transform(
                xp, fft, frames_sub, p.z, p.pixel_pitch, p.wavelength,
                zero_padding=p.zero_padding
            )
        else:
            holograms = angular_spectrum_transform(
                xp, fft, frames_sub, p.z, p.pixel_pitch, p.wavelength,
                zero_padding=p.zero_padding
            )

    # SVD filtering
    holograms_f = svd_filter(xp, holograms, p.svd_threshold)

    batch = {}
    if compute_debug:
        batch["average_signal"] = xp.squeeze(xp.mean(holograms_f, axis=(-1, -2)))

    # Temporal transform
    if p.temporal_trans == "FourierTransform":
        spectrum_f = fourier_time_transform(xp, fft, holograms_f)
    else:
        spectrum_f = holograms_f

    # Frequency selection
    idxs, freqs = frequency_symmetric_filtering(
        xp, fft, nt_sub, p.sampling_freq, p.low_freq, p.high_freq
    )
    psd = xp.abs(spectrum_f) ** 2

    # Moments
    batch["M0"] = moment(xp, psd[idxs], freqs, 0)
    batch["M1"] = moment(xp, psd[idxs], freqs, 1)
    batch["M2"] = moment(xp, psd[idxs], freqs, 2)
    batch["M0ff"] = gaussian_flatfield(batch["M0"], p.reg_flatfield_gw, bm.gaussian_filter)

    # Frequency bands
    for k, (f1, f2) in enumerate(p.freq_bands):
        idxs_band, _ = frequency_symmetric_filtering(
            xp, fft, nt_sub, p.sampling_freq, f1, f2
        )
        band = xp.mean(psd[idxs_band], axis=0)
        batch[f"band_{k}_{f1}_{f2}"] = band

    if compute_debug:
        batch["spectrum_line"] = xp.mean(psd, axis=(-1, -2))
        batch["freqs"] = freqs
        # optional: moments without phase correction (if phase_term used)
        if phase_term is not None:
            if p.spatial_prop == "Fresnel":
                holo_nofix = fresnel_transform(
                    xp, fft, frames_sub, p.z, p.pixel_pitch, p.wavelength,
                    zero_padding=p.zero_padding
                )
            else:
                holo_nofix = angular_spectrum_transform(
                    xp, fft, frames_sub, p.z, p.pixel_pitch, p.wavelength,
                    zero_padding=p.zero_padding
                )
            holo_nofix_f = svd_filter(xp, holo_nofix, p.svd_threshold)
            spec_nofix = fourier_time_transform(xp, fft, holo_nofix_f)
            psd_nofix = xp.abs(spec_nofix[idxs]) ** 2
            batch["M0notfixed"] = moment(xp, psd_nofix, freqs, 0)

    return batch


# ------------------------------------------------------------
# Render moments for a single batch (with optional line profiling)
# ------------------------------------------------------------

def render_moments(bm, parameters, frames=None, registration_ref=None, tictoc=False):
    """Process a single batch of frames. Returns dict with moments and optional debug."""
    p = _get_params(parameters)
    xp = bm.xp
    nt, ny, nx = frames.shape
    res = {}

    # Accumulator helper
    class Accumulator:
        def __init__(self, batch_size, xp):
            self.xp = xp
            self.batch_size = batch_size
            self.buffers = defaultdict(list)

        def add(self, data_dict):
            for k, v in data_dict.items():
                self.buffers[k].append(v)
            if len(next(iter(self.buffers.values()))) >= self.batch_size:
                return self.flush()
            return None

        def flush(self):
            if not self.buffers:
                return None
            batch = {
                k: self.xp.sum(self.xp.stack(v), axis=0) / self.batch_size
                for k, v in self.buffers.items()
            }
            self.buffers.clear()
            return batch

    # Line profiling wrapper (if requested and available)
    if tictoc and lblprof is not None:
        profiler = lblprof.Profiler()
        profiler.start()
    else:
        profiler = None

    # --- Shack‑Hartmann phase correction ---
    phase_term = None
    debug_sh = {}
    if p.shack_hartmann:
        phase_term, debug_sh = _process_shack_hartmann(bm, p, frames, registration_ref)
        if p.debug:
            res.update(debug_sh)

    # --- Main moment accumulation ---
    main_acc = Accumulator(p.main_acc, xp)
    sub_batch_size = nt // p.main_acc
    sub_batch_stride = sub_batch_size

    for it in range(p.main_acc):
        frames_sub = frames[sub_batch_stride * it : sub_batch_stride * it + sub_batch_size]
        batch = _process_sub_batch(bm, p, frames_sub, phase_term, p.debug)
        out = main_acc.add(batch)
        if out is not None:
            res.update(out)

    # --- Image registration ---
    if p.registration and registration_ref is not None:
        M0_ff = gaussian_flatfield(res["M0"], p.reg_flatfield_gw, bm.gaussian_filter)
        if p.debug:
            res["M0_ff_noreg"] = M0_ff
        if p.reg_type == "translation_rotation_scale":
            reg = register_trs(xp, bm.fft, bm.ndi, registration_ref, M0_ff, p.reg_disc_ratio)
        else:
            reg = register_trs(xp, bm.fft, bm.ndi, registration_ref, M0_ff, p.reg_disc_ratio,
                               estimate_similarity=False)
        if p.apply_reg:
            res["M0"] = apply_registration(xp, bm.fft, bm.ndi, res["M0"], reg)
            res["M1"] = apply_registration(xp, bm.fft, bm.ndi, res["M1"], reg)
            res["M2"] = apply_registration(xp, bm.fft, bm.ndi, res["M2"], reg)
            res["M0ff"] = apply_registration(xp, bm.fft, bm.ndi, res["M0ff"], reg)
            for k, (f1, f2) in enumerate(p.freq_bands):
                key = f"band_{k}_{f1}_{f2}"
                res[key] = apply_registration(xp, bm.fft, bm.ndi, res[key], reg)
        res["registration"] = reg

    if profiler is not None:
        profiler.stop()
        print(profiler.output_text(show_all=True))

    return res


# ------------------------------------------------------------
# Preview (single batch) unchanged but uses refactored render_moments
# ------------------------------------------------------------

def preview_process_moments(file_path, parameters, tictoc=False):
    backend_name = parameters["backend"]
    bm = BackendManager(backend=backend_name)
    file_reader = FileReaderFactory.create(file_path)
    file_reader.open()
    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
    print("parameters : ", parameters)
    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]

    frames = file_reader.read_frames(first_frame, batch_size)
    frames = bm.to_backend(frames)
    res = render_moments(bm, parameters, frames=frames, tictoc=tictoc)
    file_reader.close()

    def save_debug_images(debug_dict, save_dir, prefix="debug"):
        os.makedirs(save_dir, exist_ok=True)
        for key, img in debug_dict.items():
            if img is None:
                continue
            img_np = bm.to_numpy(img)
            if img_np.ndim == 2 and parameters["square"]:
                H, W = img_np.shape
                L = max(H, W)
                img_np = resize_slicewise(img_np, L, L)
            if img_np.dtype != np.uint8:
                img_min = np.min(img_np)
                img_max = np.max(img_np)
                if img_max > img_min:
                    img_np = (img_np - img_min) / (img_max - img_min + 1e-12)
                img_np = (img_np * 255).astype(np.uint8)
            filename = os.path.join(save_dir, f"{prefix}_{key}.png")
            iio.imwrite(filename, img_np)
            print(f"Saved: {filename} | shape={img_np.shape} dtype={img_np.dtype}")

    debug_manager = DebugPlotterManager(parameters) if parameters.get("debug") else None
    debug_imgs = debug_manager.plot_all(res) if parameters.get("debug") else {}

    if parameters.get("debug") and parameters.get("shack_hartmann") and parameters.get("shack_hartmann_zernike_fit"):
        coefs = bm.to_numpy(res["coefs"]) if "coefs" in res else None
        print("zernike_fit_coeffs (radians):", coefs)
        if coefs is not None:
            delta_z = (4 * np.sqrt(3) * parameters["z"]**2 /
                       ((min(frames.shape[1:]) * parameters["pixel_pitch"][0])**2) *
                       parameters["wavelength"] / (2 * np.pi) * coefs[0] * 1e3)
            print("delta to true z in mm if coef[0] is defocus :", delta_z)

    if "M0" in res:
        M0 = bm.to_numpy(res["M0"])
        M0 = (M0 - np.min(M0)) / (np.max(M0) - np.min(M0) + 1e-12)
        debug_imgs["M0"] = (M0 * 255).astype(np.uint8)

    save_dir = "./debug_outputs"
    save_debug_images(debug_imgs, save_dir)
    plt.close("all")

    M0img = debug_imgs.get("M0")
    if M0img is not None:
        if M0img.ndim == 2 and parameters["square"]:
            H, W = M0img.shape
            L = max(H, W)
            M0img = resize_slicewise(M0img, L, L)
        return M0img


# ------------------------------------------------------------
# Full video processing with memmap support
# ------------------------------------------------------------

def _get_memmap_if_available(file_reader, parameters, first_frame, end_frame):
    """Return a memory‑mapped array if use_memmap is True and file_reader supports it."""
    if not parameters.get("use_memmap", False):
        return None
    if hasattr(file_reader, "get_np_memmap"):
        try:
            mm = file_reader.get_np_memmap()
            # slice to requested range
            return mm[first_frame:end_frame]
        except Exception as e:
            print(f"Memmap loading failed: {e}, falling back to regular reads.")
    return None


def _read_batch_from_memmap(memmap, start, batch_size):
    """Slice a batch from memmap array (assumed shape (T, H, W))."""
    return memmap[start:start + batch_size]


def process_moments(
    file_path, parameters, mp4_path=None, return_numpy=False, holodoppler_path=True
):
    backend_name = parameters["backend"]
    bm = BackendManager(backend=backend_name)
    file_reader = FileReaderFactory.create(file_path)
    file_reader.open()
    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
    print("parameters : ", parameters)

    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]
    end_frame = parameters.get("end_frame", 0)
    if end_frame <= 0:
        if file_reader.ext == ".holo":
            end_frame = file_reader.file_header["num_frames"]
        else:
            end_frame = file_reader.metadata["ImageCount"]

    if batch_stride >= (end_frame - first_frame):
        num_batch = 1 if batch_size <= (end_frame - first_frame) else 0
    else:
        num_batch = int((end_frame - first_frame) / batch_stride)
    if num_batch <= 0:
        return None

    # Memmap support
    memmap = _get_memmap_if_available(file_reader, parameters, first_frame, end_frame)

    out_list = []
    coefs_list = [None] * num_batch if parameters.get("shack_hartmann") else None
    reg_list = [None] * num_batch if parameters.get("image_registration") else None

    # Debug threading setup
    debug_manager = DebugPlotterManager(parameters) if parameters.get("debug") else None
    debug_queue = queue.Queue(maxsize=14) if debug_manager else None
    res_store = {} if debug_manager else None
    lock = threading.Lock() if debug_manager else None
    stop_event = threading.Event() if debug_manager else None
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
        debug_results = {}

    # Registration reference
    if parameters.get("image_registration"):
        frames_reg = file_reader.read_frames(first_frame, parameters["batch_size_registration"])
        frames_reg = bm.to_backend(frames_reg)
        M0_reg = render_moments(bm, parameters, frames=frames_reg)["M0"]
        M0_reg = gaussian_flatfield(
            M0_reg, parameters.get("registration_flatfield_gw", 1.0), bm.gaussian_filter
        )
    else:
        M0_reg = None

    # Choose processing loop based on backend and memmap presence
    if memmap is not None:
        # Memory‑mapped reading: all batches already in RAM (or disk‑backed view)
        _process_memmap(
            bm, memmap, parameters, num_batch, first_frame, batch_stride, batch_size,
            M0_reg, out_list, coefs_list, reg_list,
            debug_manager, debug_queue, res_store, lock
        )
    elif backend_name == "cupy":
        _process_gpu_streaming(
            bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
            M0_reg, out_list, coefs_list, reg_list,
            debug_manager, debug_queue, res_store, lock
        )
    elif backend_name == "cupyRAM":
        _process_gpu_streaming_onram(
            bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
            M0_reg, out_list, coefs_list, reg_list,
            debug_manager, debug_queue, res_store, lock
        )
    elif backend_name == "cupyRAMmultistream":        # <-- new backend
        _process_gpu_streaming_onram_multistream(
            bm, file_reader, parameters, num_batch, first_frame,
            batch_stride, batch_size, M0_reg, out_list, coefs_list,
            reg_list, debug_manager, debug_queue, res_store, lock, end_frame
        )
    else:
        _process_cpu(
            bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
            M0_reg, out_list, coefs_list, reg_list,
            debug_manager, debug_queue, res_store, lock
        )

    file_reader.close()

    # --- Post‑processing ---
    vid_t = bm.to_numpy(bm.xp.stack(out_list, axis=0))
    bm.clear_gpu_memory()

    if debug_manager:
        debug_queue.join()
        stop_event.set()
        debug_thread.join()
        debug_manager.close_all()

    if coefs_list is not None:
        coefs_list = [bm.to_numpy(c) for c in coefs_list]
    if reg_list is not None:
        reg_list = [bm.to_numpy(r) for r in reg_list]

    vid_debug = {}
    if parameters.get("debug") and debug_results:
        for key in debug_results[0].keys():
            vid_debug[key] = np.stack(
                [bm.to_numpy(debug_results[k][key]) for k in range(num_batch)], axis=0
            )

    # Spatial transforms
    p = _get_params(parameters)
    if p.square:
        m = max(vid_t.shape[-2], vid_t.shape[-1])
        vid_t = resize_slicewise(vid_t, m, m)
    if p.transpose:
        vid_t = np.transpose(vid_t, axes=(0, 1, 3, 2))
    if p.flip_x:
        vid_t = np.flip(vid_t, axis=-1)
    if p.flip_y:
        vid_t = np.flip(vid_t, axis=-2)

    save_outputs(
        file_reader, video_path=mp4_path, holodoppler_path=holodoppler_path,
        vid=vid_t, vid_debug=vid_debug, parameters=parameters,
        reg_list=reg_list, coefs_list=coefs_list,
        end_frame=end_frame, first_frame=first_frame, num_batch=num_batch
    )
    plt.close("all")

    if return_numpy:
        return vid_t
    return None


# ------------------------------------------------------------
# Specialised loops (CPU, GPU streaming, memmap)
# ------------------------------------------------------------

def _process_cpu(bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
                 M0_reg, out_list, coefs_list, reg_list, debug_manager, debug_queue, res_store, lock):
    for i in tqdm(range(num_batch)):
        frames = file_reader.read_frames(first_frame + i * batch_stride, batch_size)
        frames = bm.to_backend(frames)
        res = render_moments(bm, parameters, frames=frames, registration_ref=M0_reg)
        if res is None:
            break
        l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
        for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
            l.append(res[f"band_{k}_{f1}_{f2}"])
        out_list.append(bm.xp.stack(l, axis=0))
        if "coefs" in res and coefs_list is not None:
            coefs_list[i] = res["coefs"]
        if "registration" in res and reg_list is not None:
            reg_list[i] = res["registration"]
        if debug_manager and lock:
            with lock:
                res_store[i] = res
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
        if res is None:
            break
        l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
        for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
            l.append(res[f"band_{k}_{f1}_{f2}"])
        out_list.append(bm.xp.stack(l, axis=0))
        if "coefs" in res and coefs_list is not None:
            coefs_list[i] = res["coefs"]
        if "registration" in res and reg_list is not None:
            reg_list[i] = res["registration"]
        if debug_manager and lock:
            with lock:
                res_store[i] = res
            debug_queue.put(i)
        stream_compute.synchronize()
    stream_h2d.synchronize()
    cp.cuda.Device().synchronize()


def _process_gpu_streaming_onram(bm, file_reader, parameters, num_batch, first_frame, batch_stride,
                                 batch_size, M0_reg, out_list, coefs_list, reg_list,
                                 debug_manager, debug_queue, res_store, lock):
    import queue as qmod, threading
    import cupy as cp

    frame_queue = qmod.Queue(maxsize=4)
    stop_reader = threading.Event()

    def reader():
        frame_idx = first_frame
        for i in range(num_batch):
            if stop_reader.is_set():
                break
            frames = file_reader.read_frames(frame_idx, batch_size)
            frames = bm.to_backend(frames)
            frame_queue.put((i, frames))
            frame_idx += batch_stride
        frame_queue.put(None)

    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()

    stream_h2d = cp.cuda.Stream(non_blocking=True)
    stream_compute = cp.cuda.Stream(non_blocking=True)

    item = frame_queue.get()
    if item is None:
        return
    _, frames = item
    with stream_h2d:
        d_frames = cp.asarray(frames)
    stream_h2d.synchronize()

    for i in tqdm(range(num_batch)):
        next_item = frame_queue.get() if i + 1 < num_batch else None
        d_frames_next = None
        if next_item is not None:
            _, frames_next = next_item
            with stream_h2d:
                d_frames_next = cp.asarray(frames_next)

        with stream_compute:
            res = render_moments(bm, parameters, frames=d_frames, registration_ref=M0_reg)
        stream_compute.synchronize()
        if res is None:
            break
        l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
        for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
            l.append(res[f"band_{k}_{f1}_{f2}"])
        out_list.append(bm.xp.stack(l, axis=0))
        if "coefs" in res and coefs_list is not None:
            coefs_list[i] = res["coefs"]
        if "registration" in res and reg_list is not None:
            reg_list[i] = res["registration"]
        if debug_manager and lock:
            with lock:
                res_store[i] = res
            debug_queue.put(i)

        if d_frames_next is not None:
            stream_h2d.synchronize()
            d_frames = d_frames_next

    stop_reader.set()
    reader_thread.join(timeout=5)
    stream_h2d.synchronize()
    stream_compute.synchronize()
    cp.cuda.Device().synchronize()


def _process_memmap(bm, memmap, parameters, num_batch, first_frame, batch_stride, batch_size,
                    M0_reg, out_list, coefs_list, reg_list,
                    debug_manager, debug_queue, res_store, lock):
    """Processing loop using a memory‑mapped array (no I/O per batch)."""
    # memmap shape: (T, H, W), already sliced to [first_frame:end_frame]
    for i in tqdm(range(num_batch)):
        start = i * batch_stride
        frames_np = memmap[start:start + batch_size]
        frames = bm.to_backend(frames_np)
        res = render_moments(bm, parameters, frames=frames, registration_ref=M0_reg)
        if res is None:
            break
        l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
        for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
            l.append(res[f"band_{k}_{f1}_{f2}"])
        out_list.append(bm.xp.stack(l, axis=0))
        if "coefs" in res and coefs_list is not None:
            coefs_list[i] = res["coefs"]
        if "registration" in res and reg_list is not None:
            reg_list[i] = res["registration"]
        if debug_manager and lock:
            with lock:
                res_store[i] = res
            debug_queue.put(i)

def _process_gpu_streaming_onram_multistream(
    bm, file_reader, parameters, num_batch, first_frame, batch_stride, batch_size,
    M0_reg, out_list, coefs_list, reg_list,
    debug_manager, debug_queue, res_store, lock, end_frame
):
    """
    GPU processing with all frames preloaded in RAM and multiple parallel compute streams.
    """
    import cupy as cp

    # Load entire video range into RAM
    all_frames = file_reader.read_frames(first_frame, end_frame - first_frame)
    all_frames = np.asarray(all_frames)                     # ensure ndarray
    n_streams = parameters.get("gpu_multistream_count", 8)

    # Precompute start indices for each batch
    batch_starts = [i * batch_stride for i in range(num_batch)]

    # Process batches in chunks of n_streams
    for chunk_start in tqdm(range(0, num_batch, n_streams)):
        chunk_size = min(n_streams, num_batch - chunk_start)
        streams = []
        batch_results = [None] * chunk_size

        # Launch parallel work
        for j in range(chunk_size):
            i = chunk_start + j
            start = batch_starts[i]
            frames_sub = all_frames[start : start + batch_size]

            stream = cp.cuda.Stream(non_blocking=True)
            with stream:
                d_frames = cp.asarray(frames_sub)
                res = render_moments(bm, parameters, frames=d_frames,
                                     registration_ref=M0_reg)
            streams.append(stream)
            batch_results[j] = res          # res is CuPy dict, still under stream

        # Wait for all streams in chunk to finish
        for stream in streams:
            stream.synchronize()

        # Collect results (now safe)
        for j in range(chunk_size):
            i = chunk_start + j
            res = batch_results[j]
            if res is None:
                break

            # Build output array
            l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
            for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
                l.append(res[f"band_{k}_{f1}_{f2}"])
            out_list.append(bm.xp.stack(l, axis=0))

            if "coefs" in res and coefs_list is not None:
                coefs_list[i] = res["coefs"]
            if "registration" in res and reg_list is not None:
                reg_list[i] = res["registration"]

            # Debug handling (same as other loops)
            if debug_manager is not None and lock is not None:
                with lock:
                    res_store[i] = res
                debug_queue.put(i)