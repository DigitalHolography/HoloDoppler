import yaml
import dask
from dask import delayed
from pathlib import Path
from functools import lru_cache
from collections import defaultdict
import numpy as np
import threading
import queue

from .backend import BackendManager
from .file_io import FileReaderFactory
from .propagation import fresnel_transform, build_fresnel_kernel_in, build_fresnel_kernel_out
from .filtering import fourier_time_transform, frequency_symmetric_filtering
from .moments import moment
from .utils import normalize_to_uint8, write_video_file, flatfield3D



def process_moments_classical(bm, file_path,parameters):
    """Takes backend manager, filepath and parameters. Main pipeline function defining the pipeline graph through the delayed dask operator"""
    xp = bm.xp
    fft = bm.fft


    reader = FileReaderFactory.create(file_path)
    reader.open()
    m = reader.get_np_memmap()
    reader.close()

    batch_size = parameters["frame_batcher"]["batch_size"]
    batch_stride = parameters["frame_batcher"]["batch_stride"]
    first_frame = parameters["frame_reader"]["first_frame"]
    end_frame = parameters["frame_reader"]["last_frame"]

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

    if parameters["registration"]["enabled"]:
        ref_first_frame = parameters["registration"]["ref_first_frame"]
        frames_reg = m[parameters["registration"]["ref_first_frame"]:
        M0_reg = self.render_moments(parameters, frames=frames_reg)["M0"]
        M0_reg = gaussian_flatfield(M0_reg, parameters["registration_flatfield_gw"],self.bm.gaussian_filter)
        M0_reg = self.bm.to_backend(M0_reg)
    
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



    ...

pipelines = {
    "process_moments_latest" : process_moments_latest
}

def define_nodes(bm, global_parameters):
    """
    Returns a dictionary mapping node type names to their callable implementations.
    The callables are closures that capture the backend and global parameters.
    """
    xp = bm.xp
    fft = bm.fft
    wavelength = global_parameters["wavelength"]
    pixel_pitch = tuple(global_parameters["pixel_pitch"])  # ensure tuple
    sampling_freq = global_parameters["sampling_freq"]

    # --------------------------------------------------------------------------
    # Node implementations
    # --------------------------------------------------------------------------

    def filereader(file_path, first_frame=0, last_frame=-1):
        """
        Returns the entire hologram stack as a memorymapped array.
        """
        reader = FileReaderFactory.create(file_path)
        reader.open()
        m = reader.get_np_memmap()
        reader.close()
        return m

    def batcher(frames, batch_size, batch_stride):
        """
        Slices the full frame array into a list of delayed batches.
        """
        if frames
        n_frames = frames.shape[0]
        batches = []
        for start in range(0, n_frames, batch_stride):
            end = min(start + batch_size, n_frames)
            if end <= start:
                break
            # Slicing a delayed array yields another delayed array
            batches.append(frames[start:end])
        return batches

    def fresnel_kernel_mult(frame_batch, propagation_dist):
        ny, nx = frame_batch.shape[-2:]
        kernel = build_fresnel_kernel_in(xp, propagation_dist, pixel_pitch, wavelength, ny, nx, zero_padding=None)
        return frame_batch * kernel

    def fresnel_propag(frame_batch_kernel, zero_padding, use_output_kernel):
        """
        Inverse FFT the Fourier-domain product to obtain the propagated field.
        """
        if zero_padding:
            frame_batch_kernel = pad_array_centrally(frame_batch_kernel, zero_padding, xp)

        result = fft.fftshift(
            fft.fft2(frames * kernel_in, axes=(-1, -2), norm="ortho"), axes=(-1, -2)
        )

        if use_output_kernel:
            kernel_out = build_fresnel_kernel_out(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)
            result = result * kernel_out

        return result

    def spectrum_calc(propagated_batch):
        """
        Temporal Fourier transform of the propagated field.
        """
        return fourier_time_transform(xp, fft, propagated_batch)

    def power_density_calc(spectrum_batches):
        return xp.abs(spectrum_batches).astype(xp.float32) ** 2

    def moments_calc(power_density_batches, low_freq, high_freq, orders):
        # Expects power_density_batches with shape (N_freq, H, W)
        idxs, freqs = frequency_symmetric_filtering(
            xp, fft, power_density_batches.shape[0], sampling_freq,
            low_freq, high_freq=None
        )
        # Compute moment for each order and stack
        return xp.stack([moment(xp, power_density_batches[idxs], freqs, n) for n in orders])

    def accumulator(moments_list, window, stride):
        """
        """
        if not isinstance(moments_list, list):
            raise TypeError("accumulator expects a list of moment arrays")
        n = len(moments_list)
        avg = []
        for i in range(0, n - window + 1, stride):
            chunk = moments_list[i:i+window]
            # Stack along a new axis and take mean
            stacked = xp.stack(chunk, axis=0)
            avg.append(xp.mean(stacked, axis=0))
        return avg

    def registerer(moment, accu_moments, ref_moment):
        """
        Register the sequence of moments arrays to a reference.
        """
        if ref_moment == "first_batch":
            ref_moment = accu_moments[0]

        registered = []
        for mom in moments:
            
            registered.append(mom)
        return registered

    # --------------------------------------------------------------------------
    # Node registry
    # --------------------------------------------------------------------------
    return {
        "holoreader":            filereader,
        "batcher":               batcher,
        "fresnel_kernel_mult":   fresnel_kernel_mult,
        "fresnel_propag":        fresnel_propag,
        "spectrum_calc":         spectrum_calc,
        "power_density_calc":    power_density_calc,
        "moments_calc":          moments_calc,
        "accumulator":           accumulator,
        "registerer":            registerer,
    }

# ------------------------------------------------------------------------------
# Config loading (with tuple conversion)
# ------------------------------------------------------------------------------

def load_config(config_path):
    config_path = Path(config_path)
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f) if config_path.suffix == '.yaml' else json.load(f)

    def list_to_tuple(d):
        for k, v in d.items():
            if isinstance(v, dict):
                d[k] = list_to_tuple(v)
            elif isinstance(v, list):
                d[k] = tuple(v)
        return d

    return list_to_tuple(config)

# ------------------------------------------------------------------------------
# Main pipeline engine
# ------------------------------------------------------------------------------

def pipeline_processing(config_path, file_path):
    """
    Builds and executes the Dask delayed graph according to the YAML pipeline.
    """
    config = load_config(config_path)
    global_params = config["globals"]

    # Initialize backend
    bm = BackendManager(backend=config["runtime"].get("backend", "numpy"))

    # Get node implementations
    NODE_IMPL = define_nodes(bm, global_params)

    # Build the task graph
    graph = {}
    graph["file_path"] = file_path   # external input

    for node_name, node_spec in config["pipeline_graph"].items():
        node_type = node_spec["type"]
        fn = NODE_IMPL[node_type]

        # Collect inputs (which are keys into the graph)
        in_key = node_spec["in"]
        if isinstance(in_key, list) or isinstance(in_key, tuple):
            inputs = [graph[k] for k in in_key]
        else:
            inputs = [graph[in_key]]

        params = node_spec.get("params", {})

        # Wrap the node call in a delayed task
        graph[node_spec["out"]] = delayed(fn)(*inputs, **params)

    # Execute the final goal
    goal = config["goals"][0]
    result = dask.compute(graph[goal])
    return result


if __name__ == "__main__":
    # Example usage
    result = pipeline_processing(
        r"D:\PROJETS\HoloDopplerPython\parameters\latest.yaml",
        r"D:\PROJETS\DATA\260113_AUZ0752_6.holo"
    )
    print(result)