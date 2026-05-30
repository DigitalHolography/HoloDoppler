import yaml
import dask
from dask import delayed
from pathlib import Path
from functools import lru_cache
from collections import defaultdict
import numpy as np
import threading
import queue
import tqdm

from .backend import BackendManager
from .file_io import FileReaderFactory
from .propagation import (
    fresnel_transform,
    build_fresnel_kernel_in,
    build_fresnel_kernel_out,
)
from .filtering import fourier_time_transform, frequency_symmetric_filtering
from .moments import moment
from .utils import normalize_to_uint8, write_video_file, flatfield3D


def process_template(bm, file_path, parameters):
    """Takes backend manager, filepath and pipeline parameters. Returns a dask delayed result"""

    return delayed(lambda x: x**2)(5)  # -> will return 25 on compute


@delayed
def stack(bm,l,axis=0):
    return bm.xp.stack(l, axis=axis)

@delayed
def to_backend(bm, arr):
    return bm.to_backend(arr)

@delayed
def to_numpy(bm, arr):
    return bm.to_numpy(arr)

@delayed
def render_moments_classical(bm, A, parameters):
    """A is the input framebatch"""

    xp = bm.xp
    fft = bm.fft

    propag_params = parameters.get("propag")
    moments_params = parameters.get("moments_calc")
    debug_params = parameters.get("debug")

    propag_mode = propag_params.get("mode")
    propag_dist = propag_params.get("propagation_dist")
    wavelength = parameters.get("wavelength")
    pixel_pitch = parameters.get("pixel_pitch")
    zero_padding = propag_params.get("zero_padding")
    use_output_kernel = propag_params.get("use_output_kernel")
    sampling_freq = parameters.get("sampling_freq")

    low_freq = moments_params.get("low_freq")
    high_freq = moments_params.get("high_freq")
    orders = moments_params.get("orders")

    nt, ny, nx = A.shape
    res = {}

    if propag_mode == "Fresnel":
        A = fresnel_transform(
            xp,
            fft,
            A,
            propag_dist,
            pixel_pitch,
            wavelength,
            zero_padding=parameters.get("zero_padding"),
        )
    elif propag_mode == "AngularSpectrum":
        A = A
        # A = angular_spectrum_transform(A, zero_padding=parameters.get("zero_padding"))
    else:
        A = A
    # Temporal FFT
    if parameters["time_transform"] == "FourierTransform":
        A = fourier_time_transform(xp, fft, A)
    else:
        A = A
    # Frequency filtering
    idxs, freqs = frequency_symmetric_filtering(
        xp,
        fft,
        A.shape[0],
        sampling_freq,
        low_freq,
        high_freq,
    )
    A = bm.xp.abs(A) ** 2

    res.update(
        {
            "M0": moment(xp, A[idxs, :, :], freqs, 0),
            "M1": moment(xp, A[idxs, :, :], freqs, 1),
            "M2": moment(xp, A[idxs, :, :], freqs, 2),
        }
    )

    return res


def process_moments_classical(bm, file_path, parameters):
    """Takes backend manager, filepath and pipeline parameters. Main pipeline function"""
    xp = bm.xp
    fft = bm.fft

    reader = FileReaderFactory.create(file_path)

    reader.open()

    # Extract parameters with YAML structure
    frame_reader = parameters.get("frame_reader")
    frame_batcher = parameters.get("frame_batcher")
    propag_params = parameters.get("propag")
    moments_params = parameters.get("moments_calc")
    accumulation_params = parameters.get("moments_accumulation")
    registration_params = parameters.get("registration")
    debug_params = parameters.get("debug")
    saving_params = parameters.get("saving")

    first_frame = frame_reader.get("first_frame")
    last_frame = frame_reader.get("last_frame")
    batch_size = frame_batcher.get("batch_size")
    batch_stride = frame_batcher.get("batch_stride")
    use_memmap = frame_batcher.get("use_memmap")
    # Get propagation parameters
    propag_mode = propag_params.get("mode")
    propag_dist = propag_params.get("propagation_dist")
    wavelength = parameters.get("wavelength")
    pixel_pitch = parameters.get("pixel_pitch")
    zero_padding = propag_params.get("zero_padding")
    use_output_kernel = propag_params.get("use_output_kernel")
    sampling_freq = parameters.get("sampling_freq")

    # Get moment calculation parameters
    low_freq = moments_params.get("low_freq")
    high_freq = moments_params.get("high_freq")
    orders = moments_params.get("orders")

    # Accumulation parameters
    acc_window = accumulation_params.get("window")
    acc_stride = accumulation_params.get("stride")

    # Determine end frame
    if last_frame <= 0:
        if reader.ext == ".holo":
            last_frame = reader.file_header["num_frames"]
        else:
            last_frame = reader.metadata.get("ImageCount", batch_size)

    # Calculate number of batches
    if batch_stride >= (last_frame - first_frame):
        num_batch = 1 if batch_size <= (last_frame - first_frame) else 0
    else:
        num_batch = int((last_frame - first_frame) / batch_stride)

    if num_batch <= 0:
        reader.close()
        return None

    pbar = tqdm.tqdm(total=num_batch, desc="Overall progress")

    # Use memmap if available and requested
    if use_memmap and reader.ext == ".holo":
        m = reader.get_np_memmap()
        reader.close()
        @delayed
        def read_frames(start, size, tqdm=True):
            if tqdm:
                pbar.update(1)
            return m[start : start + size]
    else:
        @delayed
        def read_frames(start, size, tqdm=True):
            if tqdm:
                pbar.update(1)
            return reader.read_frames(start, size)

    out_list = []

    # Process registration reference if enabled
    M0_reg = None
    if registration_params.get("enabled", False):
        ref_first_frame = registration_params.get("ref_first_frame", 0)
        ref_batch_size = registration_params.get("ref_batch_size", 512)
        frames_reg = read_frames(ref_first_frame, ref_batch_size, tqdm = False)
        frames_reg = to_backend(bm, frames_reg)
        M0_reg = render_moments_classical(bm, frames_reg, parameters)["M0"]

    # Process each batch
    for i in range(num_batch):
        batch_start = first_frame + i * batch_stride
        frames = read_frames(batch_start, batch_size)

        # Move to backend
        d_frames = to_backend(bm, frames)#.astype(xp.float32)

        res = render_moments_classical(bm, d_frames, parameters)

        stacked_result = stack(bm, [res["M0"], res["M1"], res["M2"]], axis=0)
        out_list.append(stacked_result)

    # Stack all batches (T, C, H, W)
    final_result = stack(bm, out_list, axis=0)

    # Move to CPU
    vid_t = to_numpy(bm, final_result)

    # # Apply post-processing spatial transforms
    # if saving_params.get("square", False):
    #     m_size = max(vid_t.shape[-2], vid_t.shape[-1])
    #     # Simple center crop to square
    #     h, w = vid_t.shape[-2], vid_t.shape[-1]
    #     start_h = (h - m_size) // 2
    #     start_w = (w - m_size) // 2
    #     vid_t = vid_t[..., start_h : start_h + m_size, start_w : start_w + m_size]

    # if saving_params.get("transpose", False):
    #     vid_t = np.transpose(vid_t, axes=(0, 1, 3, 2))

    # if saving_params.get("flip_x", False):
    #     vid_t = np.flip(vid_t, axis=-1)

    # if saving_params.get("flip_y", False):
    #     vid_t = np.flip(vid_t, axis=-2)

    # Cleanup
    @delayed
    def cleanup():
        if not use_memmap:
            reader.close()
        bm.clear_gpu_memory()
    cleanup()

    return vid_t


pipelines = {"process_moments_latest": process_moments_classical}


# ------------------------------------------------------------------------------
# Config loading (with tuple conversion)
# ------------------------------------------------------------------------------


def load_config(config_path):
    config_path = Path(config_path)
    with open(config_path, "r") as f:
        config = yaml.safe_load(f) if config_path.suffix == ".yaml" else json.load(f)

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
    Defines and executes the Dask delayed graph according to the YAML pipeline.
    """
    config = load_config(config_path)

    from dask.distributed import Client
    client = Client()

    # Extract runtime configuration
    runtime_config = config.get("runtime", {})
    backend_name = runtime_config.get("backend", "numpy")

    # Get pipeline name and parameters
    pipeline_name = config.get("pipeline_name", "process_moments_latest")
    parameters = config.get("parameters", {})

    # Initialize backend
    bm = BackendManager(backend=backend_name)

    # Get the pipeline function
    pipeline_func = pipelines.get(pipeline_name)
    if pipeline_func is None:
        raise ValueError(f"Unknown pipeline: {pipeline_name}")

    # Create the delayed computation graph
    delayed_result = pipeline_func(bm, file_path, parameters)

    # delayed_result.visualize(filename='transpose.svg')

    # Execute the computation
    result = dask.compute(delayed_result)

    # If result is a tuple (from dask.compute), extract the first element
    if isinstance(result, tuple):
        result = result[0]

    return result


if __name__ == "__main__":
    # Example usage
    result = pipeline_processing(
        r"D:\PROJETS\HoloDopplerPython\parameters\default_parameters.yaml",
        r"D:\PROJETS\DATA\260113_AUZ0752_6.holo",
    )
