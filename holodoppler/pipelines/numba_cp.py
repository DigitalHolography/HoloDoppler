import numpy as np
from numba import cuda, jit, prange
from tqdm import tqdm
import gc
from scipy.fft import fft2, fftshift, fft, fftfreq

# ----------------------------------------------------------------------
# CUDA Kernel for Fresnel input kernel (if needed for GPU)
# ----------------------------------------------------------------------
@cuda.jit
def _cuda_fresnel_kernel_in(kernel, z, wavelength, ppy, ppx, ny, nx):
    """CUDA kernel to build Fresnel input kernel"""
    i, j = cuda.grid(2)
    if i < ny and j < nx:
        y = (i - ny // 2) * ppy
        x = (j - nx // 2) * ppx
        phase = np.pi / (wavelength * z) * (x*x + y*y)
        kernel[0, i, j] = np.exp(1j * phase).astype(np.complex64)

# ----------------------------------------------------------------------
# CUDA Kernel for Fresnel output kernel
# ----------------------------------------------------------------------
@cuda.jit
def _cuda_fresnel_kernel_out(kernel, z, wavelength, ppy, ppx, ny, nx):
    """CUDA kernel to build Fresnel output kernel"""
    i, j = cuda.grid(2)
    if i < ny and j < nx:
        # Frequency coordinates
        fx = j / (nx * ppx) - 1.0 / (2 * ppx) if j < nx//2 else (j - nx) / (nx * ppx) - 1.0 / (2 * ppx)
        fy = i / (ny * ppy) - 1.0 / (2 * ppy) if i < ny//2 else (i - ny) / (ny * ppy) - 1.0 / (2 * ppy)
        
        X = wavelength * z * fx
        Y = wavelength * z * fy
        phase = 1j * np.pi / (wavelength * z) * (X*X + Y*Y)
        kernel[0, i, j] = (np.exp(1j * 2 * np.pi / wavelength * z) / 
                           (1j * wavelength * z) * np.exp(phase)).astype(np.complex64)

# ----------------------------------------------------------------------
# CUDA Kernel for squared magnitude
# ----------------------------------------------------------------------
@cuda.jit
def _cuda_squared_magnitude(A, result):
    """CUDA kernel: compute |A|^2 for complex array A (nt, ny, nx)"""
    t, y, x = cuda.grid(3)
    nt, ny, nx = A.shape
    
    if t < nt and y < ny and x < nx:
        val = A[t, y, x]
        result[t, y, x] = val.real * val.real + val.imag * val.imag

# ----------------------------------------------------------------------
# CUDA Kernel for spectral moment
# ----------------------------------------------------------------------
@cuda.jit
def _cuda_moment(filtered, weights, result, nf, ny, nx):
    """CUDA kernel: compute nth spectral moment"""
    y, x = cuda.grid(2)
    
    if y < ny and x < nx:
        total = 0.0
        for f in range(nf):
            total += filtered[f, y, x] * weights[f]
        result[y, x] = total

# ----------------------------------------------------------------------
# CPU Fresnel kernel builders (for reference, but we'll use GPU directly)
# ----------------------------------------------------------------------
def build_fresnel_kernel_in_cpu(z, pixel_pitch, wavelength, ny, nx):
    """CPU version of Fresnel input kernel"""
    ppy, ppx = pixel_pitch
    y = (np.arange(ny) - ny // 2) * ppy
    x = (np.arange(nx) - nx // 2) * ppx
    Y, X = np.meshgrid(y, x, indexing='ij')
    phase = np.pi / (wavelength * z) * (X**2 + Y**2)
    kernel = np.exp(1j * phase).astype(np.complex64)
    return kernel.reshape(1, ny, nx)

def build_fresnel_kernel_out_cpu(z, pixel_pitch, wavelength, ny, nx):
    """CPU version of Fresnel output kernel"""
    ppy, ppx = pixel_pitch
    fx = np.fft.fftfreq(nx, d=ppx)
    fx = np.fft.fftshift(fx)
    fy = np.fft.fftfreq(ny, d=ppy)
    fy = np.fft.fftshift(fy)
    FX, FY = np.meshgrid(fx, fy, indexing='ij')
    
    X = wavelength * z * FX
    Y = wavelength * z * FY
    phase = 1j * np.pi / (wavelength * z) * (X**2 + Y**2)
    kernel = (np.exp(1j * 2 * np.pi / wavelength * z) / 
              (1j * wavelength * z) * np.exp(phase)).astype(np.complex64)
    return kernel.reshape(1, ny, nx)

# ----------------------------------------------------------------------
# CUDA-enabled Fresnel transform
# ----------------------------------------------------------------------
def fresnel_transform_gpu(frames, z, pixel_pitch, wavelength, use_output_kernel=True):
    """
    Apply Fresnel transform using CUDA for kernel generation and SciPy for FFT.
    frames: (nt, ny, nx) complex64 on GPU or CPU
    """
    ny, nx = frames.shape[-2:]
    ppy, ppx = pixel_pitch
    
    # Move to GPU if on CPU
    if not isinstance(frames, cuda.devicearray.DeviceNDArray):
        frames_gpu = cuda.to_device(frames)
    else:
        frames_gpu = frames
    
    # Build input kernel on GPU
    kernel_in_gpu = cuda.device_array((1, ny, nx), dtype=np.complex64)
    threadsperblock = (16, 16)
    blockspergrid_x = (nx + threadsperblock[1] - 1) // threadsperblock[1]
    blockspergrid_y = (ny + threadsperblock[0] - 1) // threadsperblock[0]
    blockspergrid = (blockspergrid_y, blockspergrid_x)
    
    _cuda_fresnel_kernel_in[blockspergrid, threadsperblock](
        kernel_in_gpu, z, wavelength, ppy, ppx, ny, nx
    )
    
    # Apply input kernel
    tmp_gpu = frames_gpu * kernel_in_gpu
    
    # Copy to CPU for FFT (SciPy doesn't work directly on GPU arrays)
    tmp_cpu = tmp_gpu.copy_to_host()
    
    # FFT2 with SciPy
    tmp_cpu = fft2(tmp_cpu, axes=(-2, -1), norm="ortho")
    tmp_cpu = fftshift(tmp_cpu, axes=(-2, -1))
    
    # Apply output kernel (optional)
    if use_output_kernel:
        kernel_out_cpu = build_fresnel_kernel_out_cpu(z, pixel_pitch, wavelength, ny, nx)
        tmp_cpu = tmp_cpu * kernel_out_cpu
    
    # Move back to GPU if needed
    return cuda.to_device(tmp_cpu)

def fresnel_transform_cpu(frames, z, pixel_pitch, wavelength, use_output_kernel=True):
    """CPU version of Fresnel transform"""
    ny, nx = frames.shape[-2:]
    
    kernel_in = build_fresnel_kernel_in_cpu(z, pixel_pitch, wavelength, ny, nx)
    tmp = frames * kernel_in
    tmp = fft2(tmp, axes=(-2, -1), norm="ortho")
    tmp = fftshift(tmp, axes=(-2, -1))
    
    if use_output_kernel:
        kernel_out = build_fresnel_kernel_out_cpu(z, pixel_pitch, wavelength, ny, nx)
        tmp = tmp * kernel_out
    
    return tmp

# ----------------------------------------------------------------------
# Temporal FFT (always on CPU for SciPy compatibility)
# ----------------------------------------------------------------------
def fourier_time_transform(H):
    """FFT along time axis using SciPy"""
    return fft(H, axis=0, norm="ortho")

# ----------------------------------------------------------------------
# Frequency filtering (NumPy)
# ----------------------------------------------------------------------
def frequency_symmetric_filtering(batch_size, sampling_freq, low_freq, high_freq=None):
    """Return boolean mask and corresponding frequencies."""
    freqs = np.fft.fftfreq(batch_size, 1.0 / sampling_freq)
    if high_freq is None:
        idxs = np.abs(freqs) > low_freq
    else:
        idxs = (np.abs(freqs) > low_freq) & (np.abs(freqs) < high_freq)
    selected_freqs = freqs[idxs]
    return idxs, selected_freqs

# ----------------------------------------------------------------------
# Squared magnitude (CPU with Numba parallel)
# ----------------------------------------------------------------------
@jit(nopython=True, parallel=True, cache=True)
def compute_squared_magnitude_cpu(A):
    """Compute |A|^2 for complex array A (nt, ny, nx) on CPU."""
    nt, ny, nx = A.shape
    result = np.zeros((nt, ny, nx), dtype=np.float64)
    for t in prange(nt):
        for y in range(ny):
            for x in range(nx):
                val = A[t, y, x]
                result[t, y, x] = val.real * val.real + val.imag * val.imag
    return result

def compute_squared_magnitude_gpu(A_gpu):
    """Compute |A|^2 on GPU"""
    nt, ny, nx = A_gpu.shape
    result_gpu = cuda.device_array((nt, ny, nx), dtype=np.float64)
    
    threadsperblock = (8, 8, 8)
    blockspergrid_x = (nx + threadsperblock[2] - 1) // threadsperblock[2]
    blockspergrid_y = (ny + threadsperblock[1] - 1) // threadsperblock[1]
    blockspergrid_t = (nt + threadsperblock[0] - 1) // threadsperblock[0]
    blockspergrid = (blockspergrid_t, blockspergrid_y, blockspergrid_x)
    
    _cuda_squared_magnitude[blockspergrid, threadsperblock](A_gpu, result_gpu)
    return result_gpu

# ----------------------------------------------------------------------
# Spectral moment (CPU with Numba parallel)
# ----------------------------------------------------------------------
@jit(nopython=True, parallel=True, cache=True)
def moment_cpu(A, freqs, n):
    """
    Compute nth spectral moment on CPU.
    A: (n_freqs, ny, nx) real array
    freqs: (n_freqs,) float array
    Returns (ny, nx) array.
    """
    nf, ny, nx = A.shape
    result = np.zeros((ny, nx), dtype=np.float64)
    weights = freqs ** n
    for f in prange(nf):
        w = weights[f]
        for y in range(ny):
            for x in range(nx):
                result[y, x] += A[f, y, x] * w
    return result

def moment_gpu(filtered_gpu, freqs, n):
    """Compute nth spectral moment on GPU"""
    nf, ny, nx = filtered_gpu.shape
    weights = (freqs ** n).astype(np.float64)
    weights_gpu = cuda.to_device(weights)
    result_gpu = cuda.device_array((ny, nx), dtype=np.float64)
    
    threadsperblock = (16, 16)
    blockspergrid_x = (nx + threadsperblock[1] - 1) // threadsperblock[1]
    blockspergrid_y = (ny + threadsperblock[0] - 1) // threadsperblock[0]
    blockspergrid = (blockspergrid_y, blockspergrid_x)
    
    _cuda_moment[blockspergrid, threadsperblock](
        filtered_gpu, weights_gpu, result_gpu, nf, ny, nx
    )
    
    return result_gpu.copy_to_host()

# ----------------------------------------------------------------------
# Render moments for a single batch (GPU version)
# ----------------------------------------------------------------------
def render_moments_gpu(frames_gpu, parameters):
    """
    frames_gpu: GPU array (nt, ny, nx) complex64
    Returns dict with computed moments (numpy arrays on CPU).
    """
    propag_params = parameters.get("propag", {})
    moments_params = parameters.get("moments_calc", {})
    
    propag_mode = propag_params.get("mode", "")
    propag_dist = propag_params.get("propagation_dist", 0)
    wavelength = parameters.get("wavelength")
    pixel_pitch = parameters.get("pixel_pitch")
    sampling_freq = parameters.get("sampling_freq")
    low_freq = moments_params.get("low_freq")
    high_freq = moments_params.get("high_freq")
    use_output_kernel = propag_params.get("use_output_kernel", True)
    time_transform = parameters.get("time_transform", "")
    
    # Propagation (optional)
    if propag_mode == "Fresnel":
        frames_gpu = fresnel_transform_gpu(frames_gpu, propag_dist, pixel_pitch, 
                                           wavelength, use_output_kernel)
    elif propag_mode == "AngularSpectrum":
        # Placeholder for angular spectrum
        pass
    
    # Temporal FFT (optional) - must be on CPU for SciPy
    if time_transform == "FourierTransform":
        frames_cpu = frames_gpu.copy_to_host()
        frames_cpu = fourier_time_transform(frames_cpu)
        frames_gpu = cuda.to_device(frames_cpu)
    
    # Frequency filter
    nt = frames_gpu.shape[0]
    idxs, freqs = frequency_symmetric_filtering(nt, sampling_freq, low_freq, high_freq)
    
    # Squared magnitude on GPU
    A_sq_gpu = compute_squared_magnitude_gpu(frames_gpu)
    
    # Extract filtered frequencies (move to CPU for indexing)
    A_sq_cpu = A_sq_gpu.copy_to_host()
    filtered_cpu = A_sq_cpu[idxs, :, :]  # (n_freqs, ny, nx)
    
    # Compute moments on CPU (simpler than GPU for this step)
    results = {
        "M0": moment_cpu(filtered_cpu, freqs, 0),
        "M1": moment_cpu(filtered_cpu, freqs, 1),
        "M2": moment_cpu(filtered_cpu, freqs, 2),
    }
    
    return results

# ----------------------------------------------------------------------
# Render moments for a single batch (CPU version)
# ----------------------------------------------------------------------
def render_moments_cpu(frames, parameters):
    """
    frames: numpy array (nt, ny, nx) complex64
    Returns dict with computed moments.
    """
    propag_params = parameters.get("propag", {})
    moments_params = parameters.get("moments_calc", {})
    
    propag_mode = propag_params.get("mode", "")
    propag_dist = propag_params.get("propagation_dist", 0)
    wavelength = parameters.get("wavelength")
    pixel_pitch = parameters.get("pixel_pitch")
    sampling_freq = parameters.get("sampling_freq")
    low_freq = moments_params.get("low_freq")
    high_freq = moments_params.get("high_freq")
    use_output_kernel = propag_params.get("use_output_kernel", True)
    time_transform = parameters.get("time_transform", "")
    
    # Propagation (optional)
    if propag_mode == "Fresnel":
        frames = fresnel_transform_cpu(frames, propag_dist, pixel_pitch, 
                                       wavelength, use_output_kernel)
    elif propag_mode == "AngularSpectrum":
        # Placeholder for angular spectrum
        pass
    
    # Temporal FFT (optional)
    if time_transform == "FourierTransform":
        frames = fourier_time_transform(frames)
    
    # Frequency filter
    idxs, freqs = frequency_symmetric_filtering(frames.shape[0], sampling_freq, 
                                                 low_freq, high_freq)
    
    # Squared magnitude
    A_sq = compute_squared_magnitude_cpu(frames)
    
    # Extract filtered frequencies
    filtered = A_sq[idxs, :, :]  # (n_freqs, ny, nx)
    
    # Compute moment(s)
    results = {
        "M0": moment_cpu(filtered, freqs, 0),
        "M1": moment_cpu(filtered, freqs, 1),
        "M2": moment_cpu(filtered, freqs, 2),
    }
    
    return results

# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
def process_moments(file_path, parameters, use_gpu=True):
    """Main pipeline with CUDA GPU support."""
    
    try:
        from holodoppler.file_io import FileReaderFactory
    except ImportError:
        print("holodoppler not installed. Using dummy reader for testing.")
        return None
    
    reader = FileReaderFactory.create(file_path)
    reader.open()
    
    # Extract parameters
    frame_reader = parameters.get("frame_reader", {})
    frame_batcher = parameters.get("frame_batcher", {})
    registration_params = parameters.get("registration", {})
    
    first_frame = frame_reader.get("first_frame", 0)
    last_frame = frame_reader.get("last_frame", -1)
    batch_size = frame_batcher.get("batch_size", 64)
    batch_stride = frame_batcher.get("batch_stride", 64)
    
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
    
    print(f"Processing {num_batch} batches of size {batch_size}")
    if use_gpu and cuda.is_available():
        print("🚀 Running on GPU (CUDA)")
        render_func = render_moments_gpu
    else:
        print("💻 Running on CPU")
        render_func = render_moments_cpu
    
    # Get memmap
    m = reader.get_np_memmap()
    reader.close()
    
    out_list = []
    
    # Optional registration reference
    M0_reg = None
    if registration_params.get("enabled", False):
        ref_start = registration_params.get("ref_first_frame", 0)
        ref_size = registration_params.get("ref_batch_size", 512)
        frames_reg = np.array(m[ref_start : ref_start + ref_size]).astype(np.complex64)
        
        if use_gpu and cuda.is_available():
            frames_reg = cuda.to_device(frames_reg)
            M0_reg = render_func(frames_reg, parameters)["M0"]
        else:
            M0_reg = render_func(frames_reg, parameters)["M0"]
        del frames_reg
    
    # Main processing loop
    for i in tqdm(range(num_batch), desc="Processing batches"):
        batch_start = first_frame + i * batch_stride
        batch_end = batch_start + batch_size
        
        # Read batch from memmap
        frames = np.array(m[batch_start:batch_end]).astype(np.complex64)
        
        # Move to GPU if requested
        if use_gpu and cuda.is_available():
            frames = cuda.to_device(frames)
        
        # Process batch
        res = render_func(frames, parameters)
        
        # Stack results: (C, H, W) format
        stacked = np.stack([res["M0"], res["M1"], res["M2"]], axis=0)  # (3, ny, nx)
        
        out_list.append(stacked)
        
        # Periodic cleanup
        if i % 10 == 0:
            if use_gpu and cuda.is_available():
                cuda.current_context().deallocations.clear()
            gc.collect()
    
    # Stack all batches: (T, C, H, W)
    final_result = np.stack(out_list, axis=0)
    
    # Final cleanup
    del m, out_list
    if use_gpu and cuda.is_available():
        cuda.current_context().deallocations.clear()
    gc.collect()
    
    return final_result

# ----------------------------------------------------------------------
# Example usage
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Configuration
    parameters = {
        "wavelength": 532e-9,
        "pixel_pitch": (5.5e-6, 5.5e-6),
        "sampling_freq": 1000,
        "time_transform": "FourierTransform",  # Set to "FourierTransform" to enable
        "propag": {
            "mode": "Fresnel",  # Set to "Fresnel" to enable propagation
            "propagation_dist": 0.15,
            "use_output_kernel": True,
        },
        "moments_calc": {
            "low_freq": 10,
            "high_freq": None,
            "orders": [0, 1, 2],
        },
        "frame_reader": {
            "first_frame": 0,
            "last_frame": -1,
        },
        "frame_batcher": {
            "batch_size": 64,
            "batch_stride": 64,
        },
        "registration": {"enabled": False},
        "moments_accumulation": {"window": 1, "stride": 1},
    }
    
    # Check CUDA availability
    if cuda.is_available():
        print(f"CUDA available: {cuda.get_current_device()}")
    else:
        print("CUDA not available, using CPU only")
    
    # Process file (set use_gpu=False to force CPU)
    result = process_moments(r"D:\PROJETS\DATA\260113_AUZ0752_6.holo", parameters, use_gpu=True)
    print(f"Result shape: {result.shape if result is not None else 'None'}")