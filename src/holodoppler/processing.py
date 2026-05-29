import yaml
import dask
from dask import delayed
from pathlib import Path
from functools import lru_cache
from collections import defaultdict
import numpy as np

from .backend import BackendManager
from .file_io import FileReaderFactory
from .propagation import fresnel_transform
from .filtering import fourier_time_transform, frequency_symmetric_filtering
from .moments import moment
from .utils import normalize_to_uint8, write_video_file, flatfield3D  # kept if needed

# ------------------------------------------------------------------------------
# Pipeline nodes
# ------------------------------------------------------------------------------

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
    # Helper: apply a single‑frame function to a list of batches
    # --------------------------------------------------------------------------
    def map_batches(func, *args, **kwargs):
        """
        If the first argument is a list, map `func` over each element;
        otherwise call directly. This lets nodes work seamlessly with both
        a single batch and a list of batches.
        """
        if isinstance(args[0], list):
            return [delayed(func)(batch, *args[1:], **kwargs) for batch in args[0]]
        return func(*args, **kwargs)

    # --------------------------------------------------------------------------
    # Node implementations
    # --------------------------------------------------------------------------

    def filereader(file_path, first_frame=0, last_frame=-1):
        """
        Returns the entire hologram stack as a memory‑mapped array.
        This acts as a lazy “frame‑by‑frame” source.
        """
        reader = FileReaderFactory.create(file_path)
        reader.open()
        # Assume the reader provides a memmap of shape (N_frames, height, width)
        data = reader.get_np_memmap()
        if last_frame == -1 or last_frame > data.shape[0]:
            last_frame = data.shape[0]
        return data[first_frame:last_frame]

    def batcher(frames, batch_size, batch_stride):
        """
        Slices the full frame array into a list of delayed batches.
        """
        n_frames = frames.shape[0]
        batches = []
        for start in range(0, n_frames, batch_stride):
            end = min(start + batch_size, n_frames)
            if end <= start:
                break
            # Slicing a delayed array yields another delayed array
            batches.append(frames[start:end])
        return batches

    def fresnel_kernel_mult(frame_batches, propagation_dist):
        """
        Multiply the 2D FFT of each frame by the Fresnel propagation kernel.
        Input : list of (N, H, W) complex arrays (or a single batch).
        Output: list of (N, H, W) complex arrays still in Fourier domain.
        """
        # Compute kernel only once per shape / distance
        @lru_cache(maxsize=16)
        def get_kernel(H, W, dist):
            # Create frequency grids
            fy = xp.fft.fftfreq(H, d=pixel_pitch[0])
            fx = xp.fft.fftfreq(W, d=pixel_pitch[1])
            FX, FY = xp.meshgrid(fx, fy)
            k = 2 * np.pi / wavelength
            # Fresnel kernel in Fourier domain
            kernel = xp.exp(1j * k * dist) * xp.exp(-1j * np.pi * wavelength * dist * (FX**2 + FY**2))
            return kernel[None, ...]  # add batch dim for broadcasting

        def process_batch(batch):
            N, H, W = batch.shape
            kernel = get_kernel(H, W, propagation_dist)
            # FFT along spatial axes (2D per frame)
            batch_ft = fft.fft2(batch, axes=(1,2))
            # Multiply by kernel
            return batch_ft * kernel

        return map_batches(process_batch, frame_batches)

    def fresnel_propag(frame_batches_kernel):
        """
        Inverse FFT the Fourier‑domain product to obtain the propagated field.
        """
        def process_batch(batch_ft):
            return fft.ifft2(batch_ft, axes=(1,2))

        return map_batches(process_batch, frame_batches_kernel)

    def spectrum_calc(propagated_batches):
        """
        Temporal Fourier transform of the propagated field.
        If a list of batches is given, first concatenate along the time axis.
        """
        if isinstance(propagated_batches, list):
            # Concatenate all batches along axis 0 (time)
            full_cube = xp.concatenate(propagated_batches, axis=0)
        else:
            full_cube = propagated_batches
        return fourier_time_transform(xp, fft, full_cube)

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
        Sliding‑window average of a sequence of moment arrays.
        moments_list : list of delayed arrays, each of shape (n_orders, H, W)
        Returns a list of averaged arrays, one every `stride` windows.
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

    def registerer(moments, accu_moments, ref="first_batch"):
        """
        Register the sequence of moment arrays to a reference (e.g., the first
        accumulated moment). Placeholder implementation.
        """
        # TODO: implement real registration (e.g., phase cross‑correlation)
        if ref == "first_batch":
            reference = accu_moments[0]
        else:
            reference = accu_moments[-1]  # fallback

        registered = []
        for mom in moments:
            # Stub: apply a trivial translation (identity)
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