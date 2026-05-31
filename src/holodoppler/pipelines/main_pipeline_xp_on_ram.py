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
import json
import subprocess
import h5py
import numpy as np
import matplotlib.pyplot as plt

import numpy as np
import cv2
import h5py
from tqdm import tqdm
from pathlib import Path

import imageio as iio


# ------------------------------------------------------------
# Single batch processing
# ------------------------------------------------------------


def render_moments(bm, parameters, frames=None, registration_ref=None, tictoc=False):
    """Process a single batch of frames"""

    xp = bm.xp
    fft = bm.fft

    nt, ny, nx = frames.shape
    res = {}

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
            batch = {k: self.xp.sum(self.xp.stack(v), axis=0) / self.batch_size 
                    for k, v in self.buffers.items()}
            self.buffers.clear()
            return batch


    subaps_acc = Accumulator(parameters.get("shack_hartmann_accumulation", 1), bm.xp)
    main_acc = Accumulator(parameters.get("accumulation", 1), bm.xp)

    # Shack-Hartmann phase estimation
    if parameters.get("shack_hartmann", False):
        sub_batch_size = nt // subaps_acc.batch_size
        sub_batch_stride = sub_batch_size

        for it in range(subaps_acc.batch_size):
            frames_sub = frames[
                sub_batch_stride * it : sub_batch_stride * it + sub_batch_size
            ]

            if parameters["spatial_propagation"] == "Fresnel":
                U_subaps = construct_subapertures_fresnel(
                    xp,
                    fft,
                    frames_sub,
                    parameters["wavelength"],
                    parameters["z"],
                    parameters["pixel_pitch"],
                    parameters["low_freq"],
                    parameters["high_freq"],
                    parameters["sampling_freq"],
                    frames_sub.shape[0],
                    parameters["shack_hartmann_nx_subap"],
                    parameters["shack_hartmann_ny_subap"],
                    parameters["svd_threshold"],
                )
            elif parameters["spatial_propagation"] == "Fresnel":  # AngularSpectrum
                U_subaps = construct_subapertures_angular(
                    xp,
                    fft,
                    frames_sub,
                    parameters["pixel_pitch"],
                    parameters["pixel_pitch"],
                    parameters["wavelength"],
                    parameters["z"],
                    parameters["low_freq"],
                    parameters["high_freq"],
                    parameters["sampling_freq"],
                    frames_sub.shape[0],
                    parameters["shack_hartmann_nx_subap"],
                    parameters["shack_hartmann_ny_subap"],
                    parameters["svd_threshold"],
                )
            subaps_acc.add({"U_subaps": U_subaps})

        b = subaps_acc.flush()
        if b is not None:
            U_subaps = b["U_subaps"]

        if parameters.get("debug"):
            res["U_subaps"] = U_subaps

        # Calculate displacements
        if parameters.get("shack_hartmann_graph_laplacian"):
            shifts_y, shifts_x = calculate_displacements_graph_laplacian(
                xp,
                fft,
                U_subaps,
                pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
                deviation_threshold=parameters.get(
                    "shack_hartmann_deviation_threshold", 3.0
                ),
                shifts_range=parameters.get(
                    "shack_hartmann_shifts_pixel_range_threshold", 20.0
                ),
            )
        else:
            ny_s, nx_s, Ny, Nx = U_subaps.shape
            imref = parameters.get("shack_hartmann_graph_ref")
            if imref == "ref_from_registration":
                if registration_ref is None:
                    # first iteration caculation of the ref
                    imref = None
                else:
                    imref = resize_fft2_slicewise(
                        registration_ref, Ny, Nx, xp=bm.xp, fft=bm.fft
                    )

            shifts_y, shifts_x = calculate_displacements(
                xp,
                fft,
                U_subaps,
                pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
                deviation_threshold=parameters.get(
                    "shack_hartmann_deviation_threshold", 3.0
                ),
                shifts_range=parameters.get(
                    "shack_hartmann_shifts_pixel_range_threshold", 20.0
                ),
                ref=imref,
            )
        if parameters.get("debug"):
            res["shifts_y"] = shifts_y
            res["shifts_x"] = shifts_x

        # Phase reconstruction
        if parameters.get("shack_hartmann_zernike_fit"):
            coefs, phase = fit_zernike(
                xp,
                ny,
                nx,
                parameters["pixel_pitch"][0],
                parameters["pixel_pitch"][1],
                parameters["wavelength"],
                shifts_y,
                shifts_x,
                parameters["shack_hartmann_zernike_fit_modes"],
            )
            res["coefs"] = coefs
            if parameters.get("debug"):
                res["phase"] = phase
        elif parameters.get("shack_hartmann_southwell_phase_integration"):
            print("shack_hartmann_southwell_phase_integration")
            phase = southwell_phase_integration(
                bm,
                ny,
                nx,
                parameters["pixel_pitch"],
                parameters["pixel_pitch"],
                parameters["wavelength"],
                shifts_y,
                shifts_x,
            )
            if parameters.get("debug"):
                res["phase"] = phase
        else:
            phase = None

        # Apply phase correction
        if phase is not None:
            phase_term = xp.exp(-1j * phase)
            phase_term = xp.nan_to_num(phase_term, nan=0.0)
            if parameters.get("zero_padding"):
                phase_term = pad_array_centrally(
                    phase_term, parameters["zero_padding"], self.bm.xp
                )
        else:
            phase_term = None

    # Main processing loop
    sub_batch_size = nt // main_acc.batch_size
    sub_batch_stride = sub_batch_size

    for it in range(main_acc.batch_size):
        frames_sub = frames[
            sub_batch_stride * it : sub_batch_stride * it + sub_batch_size
        ]

        # Propagate with or without phase correction
        if parameters.get("shack_hartmann") and phase_term is not None:
            if parameters["spatial_propagation"] == "Fresnel":
                holograms = fresnel_transform_with_phase(
                    xp,
                    fft,
                    frames_sub,
                    parameters["z"],
                    parameters["pixel_pitch"],
                    parameters["wavelength"],
                    phase_term,
                    zero_padding=parameters.get("zero_padding"),
                )
            elif parameters["spatial_propagation"] == "AngularSpectrum":
                holograms = angular_spectrum_transform_with_phase(
                    xp,
                    fft,
                    frames_sub,
                    parameters["z"],
                    parameters["pixel_pitch"],
                    parameters["wavelength"],
                    phase_term,
                    zero_padding=parameters.get("zero_padding"),
                )
            else:
                holograms = frames_sub

            if parameters.get("debug"):
                if parameters["spatial_propagation"] == "Fresnel":
                    holograms_not_fixed = fresnel_transform(xp, fft, frames_sub, parameters["z"],
                    parameters["pixel_pitch"],
                    parameters["wavelength"],
                    zero_padding=parameters.get("zero_padding")
                    )
                elif parameters["spatial_propagation"] == "AngularSpectrum":
                    holograms_not_fixed = angular_spectrum_transform(xp, fft, frames_sub, parameters["z"],
                    parameters["pixel_pitch"],
                    parameters["wavelength"], 
                    zero_padding=parameters.get("zero_padding")
                    )
                else:
                    holograms_not_fixed = frames_sub
        else:
            if parameters["spatial_propagation"] == "Fresnel":
                holograms = fresnel_transform(
                    xp, fft, frames_sub, zero_padding=parameters.get("zero_padding")
                )
            elif parameters["spatial_propagation"] == "AngularSpectrum":
                holograms = angular_spectrum_transform(
                    xp, fft, frames_sub, zero_padding=parameters.get("zero_padding")
                )
            else:
                holograms = frames_sub

            holograms_not_fixed = None

        # SVD filtering
        holograms_f = svd_filter(xp, holograms, parameters["svd_threshold"])
        # holograms_f = self.filtering.tucker_filter(holograms, ranks=holograms.shape, temporal_modes_to_remove=parameters["svd_threshold"])

        if parameters.get("debug"):
            sig = xp.squeeze(xp.mean(holograms_f, axis=(-1, -2)))
            res_batch = {"average_signal": sig}
        else:
            res_batch = {}

        # Temporal FFT
        if parameters["temporal_transformation"] == "FourierTransform":
            spectrum_f = fourier_time_transform(xp, fft, holograms_f)
        else:
            spectrum_f = holograms_f

        # Frequency filtering
        idxs, freqs = frequency_symmetric_filtering(
            xp,
            fft,
            frames_sub.shape[0],
            parameters["sampling_freq"],
            parameters["low_freq"],
            parameters.get("high_freq"),
        )
        psd = xp.abs(spectrum_f) ** 2

        res_batch.update(
            {
                "M0": moment(xp, psd[idxs, :, :], freqs, 0),
                "M1": moment(xp, psd[idxs, :, :], freqs, 1),
                "M2": moment(xp, psd[idxs, :, :], freqs, 2),
            }
        )

        res_batch["M0ff"] = gaussian_flatfield(
            res_batch["M0"],
            parameters["registration_flatfield_gw"],
            bm.gaussian_filter,
        )

        for k, range_band in enumerate(parameters.get("frequency_bands", [])):
            idxs_band, _ = frequency_symmetric_filtering(
                xp,
                fft,
                frames_sub.shape[0],
                parameters["sampling_freq"],
                range_band[0],
                range_band[1],
            )
            band = xp.mean(psd[idxs_band, :, :], axis=0)
            res_batch[f"band_{k}_{range_band[0]}_{range_band[1]}"] = band

        if parameters.get("debug"):
            res_batch["spectrum_line"] = xp.mean(psd, axis=(-1, -2))
            res_batch["freqs"] = freqs

            if holograms_not_fixed is not None:
                holograms_not_fixed_f = svd_filter(
                    xp, holograms_not_fixed, parameters["svd_threshold"]
                )
                spectrum_not_fixed = fourier_time_transform(
                    xp, fft, holograms_not_fixed_f
                )
                psd_not_fixed = xp.abs(spectrum_not_fixed[idxs, :, :]) ** 2
                res_batch["M0notfixed"] = moment(xp, psd_not_fixed, freqs, 0)

        b = main_acc.add(res_batch)

    if b is not None:
        res.update(b)

    # Registration
    if parameters.get("image_registration") and registration_ref is not None:
        M0_ff = gaussian_flatfield(
            res["M0"], parameters["registration_flatfield_gw"], bm.gaussian_filter
        )
        if parameters.get("debug"):
            res["M0_ff_noreg"] = M0_ff
        if (
            parameters.get("image_registration_type", "translation_rotation_scale")
            == "translation_rotation_scale"
        ):
            reg = register_trs(
                xp,
                bm.ndi,
                registration_ref,
                M0_ff,
                parameters.get("registration_disc_ratio"),
            )
        else:
            reg = register_trs(
                xp,
                bm.ndi,
                registration_ref,
                M0_ff,
                parameters.get("registration_disc_ratio"),
                estimate_similarity=False,
            )
        if parameters.get("apply_registration"):
            res["M0"] = apply_registration(xp, bm.ndi, res["M0"], reg)
            res["M1"] = apply_registration(xp, bm.ndi, res["M1"], reg)
            res["M2"] = apply_registration(xp, bm.ndi, res["M2"], reg)
            res["M0ff"] = apply_registration(xp, bm.ndi, res["M0ff"], reg)

        for k, v in enumerate(parameters.get("frequency_bands", [])):
            res[f"band_{k}_{v[0]}_{v[1]}"] = apply_registration(xp, bm.ndi,res[f"band_{k}_{v[0]}_{v[1]}"], reg)

        res["registration"] = reg

    return res


def preview_process_moments(file_path, parameters, tictoc=False):
    backend_name = parameters["backend"]
    bm = BackendManager(backend=backend_name)
    xp = bm.xp
    fft = bm.fft
    file_reader = FileReaderFactory.create(file_path)
    file_reader.open()
    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
    print("parameters : ", parameters)
    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]
    

    frames = file_reader.read_frames(first_frame,batch_size)

    frames = bm.to_backend(frames)
    res = render_moments(bm, parameters, frames,  tictoc=tictoc)
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
                # --- Resize ---
                img_np = imresize.imresize(img_np, output_shape=(L, L))

            if img_np.dtype != np.uint8:
                img_min = np.min(img_np)
                img_max = np.max(img_np)

                if img_max > img_min:
                    img_np = (img_np - img_min) / (img_max - img_min + 1e-12)

                img_np = (img_np * 255).astype(np.uint8)

            filename = os.path.join(save_dir, f"{prefix}_{key}.png")

            iio.imwrite(filename, img_np)

            print(f"Saved: {filename} | shape={img_np.shape} dtype={img_np.dtype}")

    # --- Generate debug safely ---
    debug_manager = DebugPlotterManager(parameters) if parameters.get("debug") else None
    debug_imgs = debug_manager.plot_all(res) if parameters.get("debug") else {}

    if parameters["debug"] and parameters["shack_hartmann"] and parameters["shack_hartmann_zernike_fit"]:
        print("zernike_fit_coeffs (radians):", bm.to_numpy(res["coefs"]) if "coefs" in res else "N/A")
        print("delta to true z in mm if coef[0] is defocus : ", 4* np.sqrt(3) * parameters["z"]**2 / ((min(frames.shape[1:])* parameters["pixel_pitch"][0])**2)  * parameters["wavelength"] / (2*np.pi) * (bm.to_numpy(res["coefs"])[0] if "coefs" in res else 0) * 1e3)

    # --- Add M0 ---
    if "M0" in res:
        M0 = bm.to_numpy(res["M0"])
        M0 = (M0 - np.min(M0)) / (np.max(M0) - np.min(M0) + 1e-12)
        debug_imgs["M0"] = (M0 * 255).astype(np.uint8)

    print("DEBUG KEYS:", list(debug_imgs.keys()))

    # --- Save ---
    save_dir = "./debug_outputs"
    save_debug_images(debug_imgs, save_dir)
    
    M0img = debug_imgs.get("M0")
    if M0img is not None:
        if M0img.ndim == 2 and parameters["square"]:
            H, W = M0img.shape
            L = max(H, W)
            # --- Resize ---
            M0img = resize_fft2_slicewise(M0img, L, L)
            
        return M0img


# ------------------------------------------------------------
# Full video processing
# ------------------------------------------------------------


def process_moments( file_path, 
    parameters, mp4_path=None, return_numpy=False, holodoppler_path=True
):
    """Process entire video"""

    backend_name = parameters["backend"]

    # Initialize backend
    bm = BackendManager(backend=backend_name)
    xp = bm.xp
    fft = bm.fft

    file_reader = FileReaderFactory.create(file_path)

    if file_reader.ext == ".holo":
        print("file header :", HD.file_reader.file_header)

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

    out_list = []

    # Debug setup
    debug_manager = DebugPlotterManager(parameters) if parameters.get("debug") else None

    if parameters.get("debug") and debug_manager is not None:
        import threading
        import queue

        debug_results = {}
        res_store = {}
        lock = threading.Lock()
        debug_queue = queue.Queue(maxsize=14)
        stop_event = threading.Event()

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
        debug_queue = None
        res_store = None
        lock = None

    # Registration reference
    if parameters.get("image_registration"):
        frames_reg = file_reader.read_frames(
            first_frame, parameters["batch_size_registration"]
        )
        M0_reg = render_moments(parameters, frames=frames_reg)["M0"]
        M0_reg = gaussian_flatfield(
            M0_reg, parameters["registration_flatfield_gw"], bm.gaussian_filter
        )
        M0_reg = bm.to_backend(M0_reg)
    else:
        M0_reg = None

    coefs_list = [None] * num_batch if parameters.get("shack_hartmann") else None
    reg_list = [None] * num_batch if parameters.get("image_registration") else None

    # Main processing loop with GPU streaming if enabled
    if backend_name == "cupy":
        _process_gpu_streaming(
            parameters,
            num_batch,
            first_frame,
            batch_stride,
            batch_size,
            M0_reg,
            out_list,
            coefs_list,
            reg_list,
            debug_manager,
            debug_queue,
            res_store,
            lock,
        )
    elif backend_name == "cupyRAM":
        _process_gpu_streaming_onram(
            parameters,
            num_batch,
            first_frame,
            batch_stride,
            batch_size,
            M0_reg,
            out_list,
            coefs_list,
            reg_list,
            debug_manager,
            debug_queue,
            res_store,
            lock,
        )
    else:
        _process_cpu(
            parameters,
            num_batch,
            first_frame,
            batch_stride,
            batch_size,
            M0_reg,
            out_list,
            coefs_list,
            reg_list,
            debug_manager,
            debug_queue,
            res_store,
            lock,
        )

    # 1. Stack and move to CPU immediately to free VRAM
    # stack(out_list, axis=0) creates (T, C, H, W) where C channel is moments 0, 1, 2 and frequency bands in order
    vid_t = bm.to_numpy(bm.xp.stack(out_list, axis=0))

    # 2. Cleanup GPU resources
    bm.clear_gpu_memory()
    if parameters.get("debug") and debug_manager is not None:
        debug_queue.join()
        stop_event.set()
        debug_thread.join()
        debug_manager.close_all()

    # 3. Convert auxiliary lists to numpy (Clean list comprehensions)
    if coefs_list is not None:
        coefs_list = [bm.to_numpy(c) for c in coefs_list]
    if reg_list is not None:
        reg_list = [bm.to_numpy(r) for r in reg_list]

    # 4. Handle Debug data figures
    # Convert debug_results from list of dicts -> dict of (T, H, W, C) arrays where C really is color channel
    vid_debug = {}
    if parameters.get("debug") and debug_results:
        for key in debug_results[0].keys():
            # print(key,debug_results[0][key])
            # Stack into (T, H, W, C)
            vid_debug[key] = np.stack(
                [bm.to_numpy(debug_results[k][key]) for k in range(num_batch)], axis=0
            )

    # 5. Post-processing: Spatial transforms
    # Since vid_t is (T, H, W, C), H=Axis 1 and W=Axis 2
    if parameters.get("square"):
        # m is max of H or W
        m = max(vid_t.shape[-2], vid_t.shape[-1])
        vid_t = resize_fft2_slicewise(vid_t, m, m)

    if parameters.get("transpose"):
        # Swap Y and X
        vid_t = np.transpose(vid_t, axes=(0, 1, 3, 2))

    if parameters.get("flip_x"):
        # Flip W (axis 2)
        vid_t = np.flip(vid_t, axis=-1)

    if parameters.get("flip_y"):
        # Flip H (axis 1)
        vid_t = np.flip(vid_t, axis=-2)

    # 6. Save outputs (Passing the optimized vid_t)
    self._save_outputs(
        video_path=mp4_path,
        holodoppler_path=holodoppler_path,
        vid=vid_t,
        vid_debug=vid_debug,
        parameters=parameters,
        reg_list=reg_list,
        coefs_list=coefs_list,
        end_frame=end_frame,
        first_frame=first_frame,
        num_batch=num_batch,
    )

    self.close_file()
    plt.close("all")

    if return_numpy:
        return vid_t

    return None


def _process_cpu(
    self,
    parameters,
    num_batch,
    first_frame,
    batch_stride,
    batch_size,
    M0_reg,
    out_list,
    coefs_list,
    reg_list,
    debug_manager,
    debug_queue,
    res_store,
    lock,
):
    """CPU processing loop"""
    for i in tqdm(range(num_batch)):
        frames = self.read_frames(first_frame + i * batch_stride, batch_size)
        res = self.render_moments(parameters, frames=frames, registration_ref=M0_reg)

        if res is None:
            break

        l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
        for k, v in enumerate(parameters.get("frequency_bands", [])):
            l.append(res[f"band_{k}_{v[0]}_{v[1]}"])
        out_list.append(self.bm.xp.stack(l, axis=0))

        if "coefs" in res and coefs_list is not None:
            coefs_list[i] = res["coefs"]
        if "registration" in res and reg_list is not None:
            reg_list[i] = res["registration"]

        if debug_manager is not None and lock is not None:
            with lock:
                res_store[i] = res
            debug_queue.put(i)


def _process_gpu_streaming(
    self,
    parameters,
    num_batch,
    first_frame,
    batch_stride,
    batch_size,
    M0_reg,
    out_list,
    coefs_list,
    reg_list,
    debug_manager,
    debug_queue,
    res_store,
    lock,
):
    """GPU streaming processing loop"""
    import cupy as cp

    stream_h2d = cp.cuda.Stream(non_blocking=True)
    stream_compute = cp.cuda.Stream(non_blocking=True)

    # Prefetch first batch
    frames_next = self.read_frames(first_frame, batch_size)
    with stream_h2d:
        d_frames_next = cp.asarray(frames_next)

    for i in tqdm(range(num_batch)):
        d_frames = d_frames_next

        # Prefetch next batch
        if i + 1 < num_batch:
            with stream_h2d:
                frames_next = self.read_frames(
                    first_frame + (i + 1) * batch_stride, batch_size
                )
                d_frames_next = cp.asarray(frames_next)

        # Compute current batch
        with stream_compute:
            res = self.render_moments(
                parameters, frames=d_frames, registration_ref=M0_reg
            )

        if res is None:
            break

        l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
        for k, v in enumerate(parameters.get("frequency_bands", [])):
            l.append(res[f"band_{k}_{v[0]}_{v[1]}"])
        out_list.append(self.bm.xp.stack(l, axis=0))

        if "coefs" in res and coefs_list is not None:
            coefs_list[i] = res["coefs"]
        if "registration" in res and reg_list is not None:
            reg_list[i] = res["registration"]

        if debug_manager is not None and lock is not None:
            with lock:
                res_store[i] = res
            debug_queue.put(i)

        stream_compute.synchronize()

    stream_h2d.synchronize()
    cp.cuda.Device().synchronize()


def _process_gpu_streaming_onram(
    self,
    parameters,
    num_batch,
    first_frame,
    batch_stride,
    batch_size,
    M0_reg,
    out_list,
    coefs_list,
    reg_list,
    debug_manager,
    debug_queue,
    res_store,
    lock,
):
    """GPU streaming processing loop with CPU RAM prefetch queue."""
    import queue, threading
    import cupy as cp
    from tqdm import tqdm

    frame_queue = queue.Queue(maxsize=4)
    stop_reader = threading.Event()

    def reader():
        frame_idx = first_frame
        for i in range(num_batch):
            if stop_reader.is_set():
                break
            frames = self.read_frames(frame_idx, batch_size)
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
            res = self.render_moments(
                parameters, frames=d_frames, registration_ref=M0_reg
            )

        stream_compute.synchronize()

        if res is None:
            break
        l = [res["M0"], res["M1"], res["M2"], res["M0ff"]]
        for k, v in enumerate(parameters.get("frequency_bands", [])):
            l.append(res[f"band_{k}_{v[0]}_{v[1]}"])
        out_list.append(self.bm.xp.stack(l, axis=0))

        if "coefs" in res and coefs_list is not None:
            coefs_list[i] = res["coefs"]
        if "registration" in res and reg_list is not None:
            reg_list[i] = res["registration"]

        if debug_manager is not None and debug_queue is not None and lock is not None:
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
