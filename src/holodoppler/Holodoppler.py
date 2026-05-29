"""
Holodoppler - Main processing class
"""

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
from .utils import normalize_to_uint8, write_video_file, flatfield3D

import numpy as np
import cv2
import h5py
from tqdm import tqdm
import matplotlib.pyplot as plt

from .backend import BackendManager
from .file_io import FileReaderFactory
from .propagation import PropagationKernels
from .filtering import Filtering
from .registration import ImageRegistration
from .shack_hartmann import ShackHartmann
from .zernike import ZernikeReconstructor
from .moments import MomentCalculator
from .plotting import DebugPlotterManager
from .utils import (gaussian_flatfield, normalize_image, temporal_gaussian_filter, flatfield3D, 
                    pad_array_centrally, crop_array_centrally, elliptical_mask, resize_fft2_slicewise, resize_matlab_slicewise)

from pathlib import Path

def get_version() -> str:
    # Check if in dev mode (pyproject.toml exists)
    dev_toml = Path(__file__).parent.parent.parent / "pyproject.toml"
    
    if dev_toml.exists():
        # Development mode - parse version from pyproject.toml as text
        with open(dev_toml, "r") as f:
            for line in f:
                if line.strip().startswith("version"):
                    version = line.split("=")[1].strip().strip('"').strip("'")
                    return version
    
    # Production mode - use installed metadata
    from importlib.metadata import version
    return version("holodoppler")


class Holodoppler:
    """
    Holodoppler processing class for .holo and .cine files.
    
    Backend:
        backend="numpy"  -> CPU
        backend="cupy"   -> GPU (if available)
        backend="cupyRAM" -> GPU with async I/O
    
    Pipeline versions:
        "latest" - Current optimized pipeline
        "old" - Legacy MATLAB-compatible pipeline
        "latest_old_reg" - Current pipeline with old registration
    """
    
    def __init__(self, backend="numpy", pipeline_version="latest"):
        self.__version__ = get_version()
        
        
        self.backend_name = backend
        self.pipeline_version = pipeline_version
        
        print(f"HoloDoppler : py{self.__version__}  {self.backend_name}  {self.pipeline_version}")
        
        # Initialize components
        self.bm = BackendManager(backend)
        self.propagation = PropagationKernels(self.bm)
        self.filtering = Filtering(self.bm)
        self.registration = ImageRegistration(self.bm)
        self.shack_hartmann = ShackHartmann(self.bm, self.propagation, self.filtering)
        self.zernike = ZernikeReconstructor(self.bm)
        self.moments = MomentCalculator(self.bm)
        
        # State
        self.file_reader = None
        self.parameters = {}
        
        # Pipeline version configuration
        self._configure_pipeline()
    
    def _configure_pipeline(self):
        """Configure pipeline functions based on version"""
        if self.pipeline_version == "latest":
            self._frequency_filter = self.filtering.frequency_symmetric_filtering
            self._register = self.registration.register_trs
            self._apply_registration = self.registration.apply_registration
            self._moment = self.moments.moment
            self._resize_to_square = resize_fft2_slicewise
        elif self.pipeline_version == "old":
            self._frequency_filter = self._old_frequency_filter
            self._register = self.registration.translation_only
            self._apply_registration = self.registration.apply_roll
            self._moment = self.moments.moment_khz
            self._resize_to_square = resize_matlab_slicewise
        elif self.pipeline_version == "latest_old_reg":
            self._frequency_filter = self.filtering.frequency_symmetric_filtering
            self._register = self.registration.translation_only
            self._apply_registration = self.registration.apply_translation
            self._moment = self.moments.moment
            self._resize_to_square = resize_fft2_slicewise
    
    def _old_frequency_filter(self, batch_size, sampling_freq, low_freq, high_freq=None): # TODO move elsewhere
        """Legacy frequency filtering (MATLAB compatible)"""
        if high_freq is None:
            high_freq = sampling_freq / 2
        
        n1 = int(np.ceil(low_freq * batch_size / sampling_freq))
        n2 = int(np.ceil(high_freq * batch_size / sampling_freq))
        
        n1 = max(min(n1, batch_size), 1)
        n2 = max(min(n2, batch_size), 1)
        
        n3 = batch_size - n2 + 1
        n4 = batch_size - n1 + 1
        
        i1, i2 = n1 - 1, n2
        i3, i4 = n3 - 1, n4
        
        f_range = np.arange(n1, n2 + 1) * (sampling_freq / batch_size)
        f_range_sym = np.arange(-n2, -n1 + 1) * (sampling_freq / batch_size)
        freqs = np.concatenate([f_range, f_range_sym])
        
        idxs = np.zeros(batch_size, dtype=bool)
        idxs[i1:i2] = True
        idxs[i3:i4] = True
        
        return self.bm.to_backend(idxs), self.bm.to_backend(freqs)
    
    # ------------------------------------------------------------
    # File handling
    # ------------------------------------------------------------
    
    def load_file(self, file_path):
        """Load a .holo or .cine file"""
        if self.file_reader is not None:
            self.file_reader.close()
        
        self.file_reader = FileReaderFactory.create(file_path)
        self.file_reader.open()
        
        # Store metadata for export
        if self.file_reader.ext == ".holo":
            self.holo_header = self.file_reader.file_header
            self.holo_footer = self.file_reader.file_footer
        else:
            self.cine_metadata = self.file_reader.metadata_json
    
    def close_file(self):
        """Close the currently open file"""
        if self.file_reader is not None:
            self.file_reader.close()
            self.file_reader = None
    
    def read_frames(self, first_frame, batch_size):
        """Read frames (returns CPU array)"""
        frames = self.file_reader.read_frames(first_frame, batch_size)
        if frames is None:
            return None
        return self.bm.to_backend(frames)
    
    # ------------------------------------------------------------
    # Single batch processing
    # ------------------------------------------------------------
    
    def render_moments(self, parameters, frames=None, registration_ref=None, tictoc=False):
        """Process a single batch of frames"""
        if frames is None:
            frames = self.read_frames(parameters["first_frame"], parameters["batch_size"])
        if frames is None:
            raise RuntimeError("Could not read frames properly")
        
        nt, ny, nx = frames.shape
        res = {}
        
        
        # ---- Lightweight Profiler ----
        class StepTimer:
            def __init__(self, enabled, bm):
                self.enabled = enabled
                self.bm = bm
                self._last = time.perf_counter()
                self._logs = []

            def tick(self, name):
                if not self.enabled: return
                now = time.perf_counter()
                dt = (now - self._last) * 1000
                self._last = now
                
                xp = self.bm.xp
                try:
                    mem = f"GPU: {xp.get_default_memory_pool().used_bytes()/1e6:.1f}/{xp.get_default_memory_pool().total_bytes()/1e6:.1f} MB"
                except Exception as e:
                    mem = f"CPU:  MB"
                    print(e)
                    
                log = f"[{name:18s}] {dt:6.2f} ms | {mem}"
                print(log)
                self._logs.append(log)
        
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
        
        subaps_acc = Accumulator(parameters.get("shack_hartmann_accumulation", 1), self.bm.xp)
        main_acc = Accumulator(parameters.get("accumulation", 1), self.bm.xp)
        
        prof = StepTimer(tictoc, self.bm)
        
        prof.tick("PipelineStart")

        # Shack-Hartmann phase estimation
        if parameters.get("shack_hartmann", False):
            sub_batch_size = nt // subaps_acc.batch_size
            sub_batch_stride = sub_batch_size
            
            for it in range(subaps_acc.batch_size):
                frames_sub = frames[sub_batch_stride*it:sub_batch_stride*it + sub_batch_size]
                
                prof.tick("UsubapsStart")
                
                if parameters["spatial_propagation"] == "Fresnel":
                    self.propagation.build_fresnel_kernel(
                        parameters["z"], parameters["pixel_pitch"],
                        parameters["wavelength"], ny, nx,
                        zero_padding=parameters.get("zero_padding")
                    )
                    prof.tick("build_fresnel_kernel")
                    U_subaps = self.shack_hartmann.construct_subapertures_fresnel(
                        frames_sub, parameters["pixel_pitch"], parameters["pixel_pitch"],
                        parameters["wavelength"], parameters["z"],
                        parameters["low_freq"], parameters["high_freq"],
                        parameters["sampling_freq"], frames_sub.shape[0],
                        parameters["shack_hartmann_nx_subap"],
                        parameters["shack_hartmann_ny_subap"],
                        parameters["svd_threshold"]
                    )
                    prof.tick("construct_subapertures_fresnel")
                else:  # AngularSpectrum
                    self.propagation.build_angular_kernel(
                        parameters["z"], parameters["pixel_pitch"],
                        parameters["wavelength"], ny, nx,
                        zero_padding=parameters.get("zero_padding")
                    )
                    U_subaps = self.shack_hartmann.construct_subapertures_angular(
                        frames_sub, parameters["pixel_pitch"], parameters["pixel_pitch"],
                        parameters["wavelength"], parameters["z"],
                        parameters["low_freq"], parameters["high_freq"],
                        parameters["sampling_freq"], frames_sub.shape[0],
                        parameters["shack_hartmann_nx_subap"],
                        parameters["shack_hartmann_ny_subap"],
                        parameters["svd_threshold"]
                    )
                    prof.tick("construct_subapertures_angular")
                subaps_acc.add({"U_subaps": U_subaps})
            
            b = subaps_acc.flush()
            if b is not None:
                U_subaps = b["U_subaps"]
            
            if parameters.get("debug"):
                res["U_subaps"] = U_subaps
                
            prof.tick("saving U_subaps")
            
            # Calculate displacements
            if parameters.get("shack_hartmann_graph_laplacian"):
                shifts_y, shifts_x = self.shack_hartmann.calculate_displacements_graph_laplacian(
                    U_subaps,
                    pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
                    deviation_threshold=parameters.get("shack_hartmann_deviation_threshold", 3.0),
                    shifts_range=parameters.get("shack_hartmann_shifts_pixel_range_threshold", 20.0)
                )
                prof.tick("calculate_displacements_graph_laplacian")
            else:
                ny_s, nx_s, Ny, Nx = U_subaps.shape
                imref = parameters.get("shack_hartmann_graph_ref")
                if imref == "ref_from_registration":
                    if registration_ref is None:
                        # first iteration caculation of the ref
                        imref = None
                    else:
                        imref = resize_fft2_slicewise(registration_ref, Ny, Nx, xp = self.bm.xp, fft = self.bm.fft)
                
                shifts_y, shifts_x = self.shack_hartmann.calculate_displacements(
                    U_subaps,
                    pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
                    deviation_threshold=parameters.get("shack_hartmann_deviation_threshold", 3.0),
                    shifts_range=parameters.get("shack_hartmann_shifts_pixel_range_threshold", 20.0),
                    ref = imref
                )
                prof.tick("calculate_displacements")
            if parameters.get("debug"):
                res["shifts_y"] = shifts_y
                res["shifts_x"] = shifts_x
            
            # Phase reconstruction
            if parameters.get("shack_hartmann_zernike_fit"):
                coefs, phase = self.zernike.fit_zernike(
                    ny, nx, parameters["pixel_pitch"], parameters["pixel_pitch"],
                    parameters["wavelength"], shifts_y, shifts_x,
                    parameters["shack_hartmann_zernike_fit_modes"]
                )
                prof.tick("fit_zernike")
                res["coefs"] = coefs
                if parameters.get("debug"):
                    res["phase"] = phase
            elif parameters.get("shack_hartmann_southwell_phase_integration"):
                print("shack_hartmann_southwell_phase_integration")
                phase = self.zernike.southwell_phase_integration(
                    ny, nx, parameters["pixel_pitch"], parameters["pixel_pitch"],
                    parameters["wavelength"], shifts_y, shifts_x
                )
                prof.tick("southwell_phase_integration")
                if parameters.get("debug"):
                    res["phase"] = phase
            else:
                phase = None
            
            # Apply phase correction
            if phase is not None:
                phase_term = self.bm.xp.exp(-1j * phase)
                phase_term = self.bm.xp.nan_to_num(phase_term, nan=0.0)
                if parameters.get("zero_padding"):
                    phase_term = pad_array_centrally(phase_term, parameters["zero_padding"], self.bm.xp)
            else:
                phase_term = None
        prof.tick("Usubaps")

        # Main processing loop
        sub_batch_size = nt // main_acc.batch_size
        sub_batch_stride = sub_batch_size
        
        for it in range(main_acc.batch_size):
            frames_sub = frames[sub_batch_stride*it:sub_batch_stride*it + sub_batch_size]
            
            # Propagate with or without phase correction
            if parameters.get("shack_hartmann") and phase_term is not None:
                if parameters["spatial_propagation"] == "Fresnel":
                    holograms = self.propagation.fresnel_transform_with_phase(frames_sub, phase_term, 
                                                           zero_padding=parameters.get("zero_padding"))
                else:
                    holograms = self.propagation.angular_spectrum_transform_with_phase(
                        frames_sub, phase_term, zero_padding=parameters.get("zero_padding")
                    )
                
                if parameters.get("debug"):
                    if parameters["spatial_propagation"] == "Fresnel":
                        holograms_not_fixed = self.propagation.fresnel_transform(frames_sub, 
                                                               zero_padding=parameters.get("zero_padding"))
                    else:
                        holograms_not_fixed = self.propagation.angular_spectrum_transform(
                            frames_sub, zero_padding=parameters.get("zero_padding")
                        )
            else:
                if parameters["spatial_propagation"] == "Fresnel":
                    self.propagation.build_fresnel_kernel(
                        parameters["z"], parameters["pixel_pitch"],
                        parameters["wavelength"], ny, nx,
                        zero_padding=parameters.get("zero_padding")
                    )
                    holograms = self.propagation.fresnel_transform(frames_sub, zero_padding=parameters.get("zero_padding"))
                elif parameters["spatial_propagation"] == "AngularSpectrum":
                    self.propagation.build_angular_kernel(
                        parameters["z"], parameters["pixel_pitch"],
                        parameters["wavelength"], ny, nx,
                        zero_padding=parameters.get("zero_padding")
                    )
                    holograms = self.propagation.angular_spectrum_transform(
                        frames_sub, zero_padding=parameters.get("zero_padding")
                    )
                else :
                    holograms = frames_sub
                    
                holograms_not_fixed = None
            
            # SVD filtering
            holograms_f = self.filtering.svd_filter(holograms, parameters["svd_threshold"])
            # holograms_f = self.filtering.tucker_filter(holograms, ranks=holograms.shape, temporal_modes_to_remove=parameters["svd_threshold"])
            
            
            
            if parameters.get("debug"):
                sig = self.bm.xp.squeeze(self.bm.xp.mean(holograms_f, axis=(-1,-2)))
                res_batch = {"average_signal" : sig}
            else :
                res_batch = {}
            
            
            
            
            # Temporal FFT
            if parameters["temporal_transformation"] == "FourierTransform":
                spectrum_f = self.filtering.fourier_time_transform(holograms_f)
            
            else :
                spectrum_f = holograms_f
                
            
            
            # Frequency filtering
            idxs, freqs = self._frequency_filter(
                frames_sub.shape[0], parameters["sampling_freq"],
                parameters["low_freq"], parameters.get("high_freq")
            )
            psd = self.bm.xp.abs(spectrum_f) ** 2
            
            res_batch.update({
                "M0": self._moment(psd[idxs, :, :], freqs, 0),
                "M1": self._moment(psd[idxs, :, :], freqs, 1),
                "M2": self._moment(psd[idxs, :, :], freqs, 2)
            })
            
            res_batch["M0ff"] = gaussian_flatfield(res_batch["M0"], parameters["registration_flatfield_gw"], self.bm.gaussian_filter)
            
            for k, range_band in enumerate(parameters.get("frequency_bands", [])):
                idxs_band, _ = self._frequency_filter(
                    frames_sub.shape[0], parameters["sampling_freq"],
                    range_band[0], range_band[1]
                )
                band = self.bm.xp.mean(psd[idxs_band, :, :], axis=0)
                res_batch[f"band_{k}_{range_band[0]}_{range_band[1]}"] = band
            
            if parameters.get("debug"):
                res_batch["spectrum_line"] = self.bm.xp.mean(
                    psd , axis=(-1, -2)
                )
                res_batch["freqs"] = freqs
                
                if holograms_not_fixed is not None:
                    holograms_not_fixed_f = self.filtering.svd_filter(holograms_not_fixed, 
                                                                       parameters["svd_threshold"])
                    spectrum_not_fixed = self.filtering.fourier_time_transform(holograms_not_fixed_f)
                    psd_not_fixed = self.bm.xp.abs(spectrum_not_fixed[idxs, :, :]) ** 2
                    res_batch["M0notfixed"] = self._moment(psd_not_fixed, freqs, 0)
            
            b = main_acc.add(res_batch)
        prof.tick("Propag")
        
        if b is not None:
            res.update(b)
        
        # Registration
        if parameters.get("image_registration") and registration_ref is not None:
            M0_ff = gaussian_flatfield(res["M0"], parameters["registration_flatfield_gw"], 
                                        self.bm.gaussian_filter)
            if parameters.get("debug"):
                res["M0_ff_noreg"] = M0_ff
            reg = self._register(registration_ref, M0_ff, parameters.get("registration_disc_ratio"), estimate_similarity = parameters.get("image_registration_type") == "translation_rotation_scale")
            if parameters.get("apply_registration"):
                res["M0"] = self._apply_registration(res["M0"], reg)
                res["M1"] = self._apply_registration(res["M1"], reg)
                res["M2"] = self._apply_registration(res["M2"], reg)
                res["M0ff"] = self._apply_registration(res["M0ff"], reg)
            
            for k,v in enumerate(parameters.get("frequency_bands", [])):
                res[f"band_{k}_{v[0]}_{v[1]}"] = self._apply_registration(res[f"band_{k}_{v[0]}_{v[1]}"], reg)
                
            res["registration"] = reg
        prof.tick("Reg")
        
        return res
    
    # ------------------------------------------------------------
    # Full video processing
    # ------------------------------------------------------------
    
    def process_moments(self, parameters, mp4_path = None, 
                        return_numpy = False, holodoppler_path = True):
        """Process entire video"""
        
        batch_size = parameters["batch_size"]
        batch_stride = parameters["batch_stride"]
        first_frame = parameters["first_frame"]
        end_frame = parameters.get("end_frame", 0)
        
        if end_frame <= 0:
            if self.file_reader.ext == ".holo":
                end_frame = self.file_reader.file_header["num_frames"]
            else:
                end_frame = self.file_reader.metadata["ImageCount"]
        
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
        else :
            debug_queue = None
            res_store = None
            lock = None  
        
        # Registration reference
        if parameters.get("image_registration"):
            frames_reg = self.read_frames(first_frame, parameters["batch_size_registration"])
            M0_reg = self.render_moments(parameters, frames=frames_reg)["M0"]
            M0_reg = gaussian_flatfield(M0_reg, parameters["registration_flatfield_gw"], 
                                         self.bm.gaussian_filter)
            M0_reg = self.bm.to_backend(M0_reg)
        else:
            M0_reg = None
        
        coefs_list = [None] * num_batch if parameters.get("shack_hartmann") else None
        reg_list = [None] * num_batch if parameters.get("image_registration") else None
        
        # Main processing loop with GPU streaming if enabled
        if self.backend_name =="cupy":
            self._process_gpu_streaming(parameters, num_batch, first_frame, batch_stride,
                                        batch_size, M0_reg, out_list, coefs_list, reg_list,
                                        debug_manager, debug_queue, res_store, lock)
        elif self.backend_name =="cupyRAM":
            self._process_gpu_streaming_onram(parameters, num_batch, first_frame, batch_stride,
                                    batch_size, M0_reg, out_list, coefs_list, reg_list,
                                    debug_manager, debug_queue, res_store, lock )
        else:
            self._process_cpu(parameters, num_batch, first_frame, batch_stride,
                             batch_size, M0_reg, out_list, coefs_list, reg_list,
                             debug_manager, debug_queue, res_store, lock)
            
        # 1. Stack and move to CPU immediately to free VRAM
        # stack(out_list, axis=0) creates (T, C, H, W) where C channel is moments 0, 1, 2 and frequency bands in order
        vid_t = self.bm.to_numpy(self.bm.xp.stack(out_list, axis=0))
        
        # 2. Cleanup GPU resources
        self.bm.clear_gpu_memory()
        if parameters.get("debug") and debug_manager is not None:
            debug_queue.join()
            stop_event.set()
            debug_thread.join()
            debug_manager.close_all()

        # 3. Convert auxiliary lists to numpy (Clean list comprehensions)
        if coefs_list is not None:
            coefs_list = [self.bm.to_numpy(c) for c in coefs_list]
        if reg_list is not None:
            reg_list = [self.bm.to_numpy(r) for r in reg_list]

        # 4. Handle Debug data figures
        # Convert debug_results from list of dicts -> dict of (T, H, W, C) arrays where C really is color channel
        vid_debug = {}
        if parameters.get("debug") and debug_results:
            for key in debug_results[0].keys():
                # print(key,debug_results[0][key])
                # Stack into (T, H, W, C)
                vid_debug[key] = np.stack([self.bm.to_numpy(debug_results[k][key]) 
                                          for k in range(num_batch)], axis=0)
        
        # 5. Post-processing: Spatial transforms
        # Since vid_t is (T, H, W, C), H=Axis 1 and W=Axis 2
        if parameters.get("square"):
            # m is max of H or W
            m = max(vid_t.shape[-2], vid_t.shape[-1])
            vid_t = self._resize_to_square(vid_t, m, m)
            
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
            num_batch=num_batch
        )
        
        self.close_file()
        plt.close('all')
        
        if return_numpy:
            return vid_t
        
        return None
    
    def _process_cpu(self, parameters, num_batch, first_frame, batch_stride,
                     batch_size, M0_reg, out_list, coefs_list, reg_list,
                     debug_manager, debug_queue, res_store, lock):
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
    
    def _process_gpu_streaming(self, parameters, num_batch, first_frame, batch_stride,
                               batch_size, M0_reg, out_list, coefs_list, reg_list,
                               debug_manager, debug_queue, res_store, lock):
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
                res = self.render_moments(parameters, frames=d_frames, registration_ref=M0_reg)
            
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
        
    def _process_gpu_streaming_onram(self, parameters, num_batch, first_frame, batch_stride,
                                    batch_size, M0_reg, out_list, coefs_list, reg_list,
                                    debug_manager, debug_queue, res_store, lock):
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
                res = self.render_moments(parameters, frames=d_frames, registration_ref=M0_reg)

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
        
    def _save_outputs(self, video_path=None, holodoppler_path=None, vid=None, 
                    vid_debug=None, parameters=None, reg_list=None, 
                    coefs_list=None, end_frame=None, first_frame=None, num_batch=None):
        """
        Main entry point for saving. 
        Determines priority: holodoppler_path > video_path > default
        """
        
        # 1. Path and Mode Resolution
        # Default path generation
        default_path = self._get_default_output_path()
        
        if holodoppler_path:
            if isinstance(holodoppler_path,bool):
                holodoppler_path = default_path
            target_dir = Path(holodoppler_path)
            save_mode = "FULL"
        elif video_path:
            if isinstance(video_path,bool):
                video_path = default_path
            target_dir = Path(video_path)
            save_mode = "LITE"
        else:
            target_dir = default_path
            save_mode = "FULL"

        # 2. Execute Save Bundle
        self._save_bundle(
            target_dir=target_dir,
            mode=save_mode,
            vid=vid,
            vid_debug=vid_debug,
            parameters=parameters,
            reg_list=reg_list,
            coefs_list=coefs_list,
            end_frame=end_frame,
            first_frame=first_frame,
            num_batch=num_batch
        )

    def _get_default_output_path(self):
        """Generates the standard Holodoppler directory structure"""
        base_name = Path(self.file_reader.file_path).stem
        return Path(self.file_reader.file_path).parent / base_name / f"{base_name}_HD"

    def _save_bundle(self, target_dir, mode, vid, vid_debug, parameters, 
                    reg_list, coefs_list, end_frame, first_frame, num_batch):
        """
        Unified saving engine. 
        mode="FULL" -> Saves everything including H5.
        mode="LITE" -> Saves videos, pngs, json, txt.
        """
        # Create subdirectories
        subdirs = ["png", "mp4", "avi", "json"]
        if mode == "FULL":
            subdirs.append("h5")
            
        for sub in subdirs:
            (target_dir / sub).mkdir(parents=True, exist_ok=True)

        fps = min((num_batch / (end_frame - first_frame) * parameters["sampling_freq"]), 65)
        # vid = np.transpose(vid_t, axes=[0,1,3,2]) # flip x-y
        
        # vid = np.flip(vid, axis=2) # flip y

        # --- 1. Setup Data Map ---
        save_map = {
            "moment_0": vid[:,0,:,:],
            "moment_1": vid[:,1,:,:],
            "moment_2": vid[:,2,:,:],
            "moment_0_ff": vid[:,3,:,:],
            # "moment_0_flatfield": flatfield3D(vid_t[:,0,:,:], parameters["registration_flatfield_gw"]), sorry but too slow
        }
        
        for k, v in enumerate(parameters.get("frequency_bands", [])):
            save_map[f"band_{v[0]}_{v[1]}"] = vid[:,4+k,:,:]
        
        # Add debug videos to map
        for key, data in vid_debug.items():
            
            # Ensure debug videos are (T, H, W)
            if data.ndim == 3 and data.shape[-1] == num_batch:
                data = np.moveaxis(data, -1, 0)
                
            if parameters["square"] and key in ["M0ffnoreg", "M0notfixed", "montage", "montagenormalized"]:
                m = max(data.shape[-2], data.shape[-1])
                data = self._resize_to_square(data, m, m)
            
            save_map[f"debug_{key}"] = data

        # --- 2. Save Visuals (MP4, AVI, PNG) ---
        for name, data in save_map.items():
            uint8_data = normalize_to_uint8(data)
            write_video_file(target_dir / "mp4" / f"{name}.mp4", uint8_data, fps, "mp4v")
            write_video_file(target_dir / "avi" / f"{name}.avi", uint8_data, fps, "MJPG")
            if uint8_data.ndim == 3:
                plt.imsave(target_dir / "png" / f"{name}.png", np.mean(uint8_data, axis=0), cmap="gray")

        # --- 3. Save Metadata (JSON, TXT) ---
        self._save_metadata(target_dir, parameters)
        
        # --- 4. Save H5 (Only if mode is FULL) ---
        if mode == "FULL":
            self._save_h5(target_dir, vid, parameters, reg_list, coefs_list)
            
        plt.close('all')

    def _save_metadata(self, target_dir, parameters):
        """Saves all configuration and versioning files"""
        # JSON Params
        with open(target_dir / "json" / "parameters_holodoppler.json", "w") as f:
            json.dump(parameters, f, indent=4)
        
        # Versioning/Info
        info_text = f"py{self.__version__}  {self.backend_name}  {self.pipeline_version}"
        (target_dir / "info_holodoppler.txt").write_text(info_text)
        (target_dir / "version_holodoppler.txt").write_text(f"py{self.__version__}")
        
        try:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
            (target_dir / "git_version.txt").write_text(f"Git commit: {commit}\n{info_text}")
        except:
            (target_dir / "git_version.txt").write_text("Git commit: Not Available")

        if self.file_reader.ext == ".holo":
            with open(target_dir / "json" / "holovibes_footer.json", "w") as f:
                json.dump(self.file_reader.file_footer, f, indent=4)
            with open(target_dir / "json" / "holovibes_header.json", "w") as f:
                json.dump(self.file_reader.file_header, f, indent=4)

    def _save_h5(self, target_dir, vid, parameters, reg_list, coefs_list):
        """Saves raw data to HDF5 with compression"""
        
        target_dir_name = target_dir.name if target_dir.name else "output"
        
        vid_t = np.flip(vid,axis=2) # flip y for doppler view
        with h5py.File(target_dir / "h5" / f"{target_dir_name}_output.h5", "w") as f:
            f.create_dataset("moment0", data=vid_t[:,0,:,:]) # compression="gzip"
            f.create_dataset("moment1", data=vid_t[:,1,:,:])
            f.create_dataset("moment2", data=vid_t[:,2,:,:])
            f.create_dataset("moment0ff", data=vid_t[:,3,:,:])
            for k, v in enumerate(parameters.get("frequency_bands", [])):
                f.create_dataset(f"band_{v[0]}_{v[1]}", data=vid_t[:,4+k,:,:])
            f.create_dataset("HD_parameters", data=json.dumps(parameters))
            info_text = f"py{self.__version__}  {self.backend_name}  {self.pipeline_version}"
            f.create_dataset("HD_info", data=info_text)
            
            if parameters.get("image_registration") and reg_list:
                f.create_dataset("registration", data=np.array(reg_list, dtype=np.float32))
            
            if parameters.get("shack_hartmann") and coefs_list:
                f.create_dataset("zernike_coefs_radians", data=np.stack(coefs_list).astype(np.float32))
