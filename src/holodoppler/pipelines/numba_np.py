import numpy as np
from numba import jit, prange
from tqdm import tqdm
import gc
from rocket_fft import numpy_like, scipy_like

numpy_like()
# ----------------------------------------------------------------------
# JIT‑compatible kernel builders (no zero padding)
# ----------------------------------------------------------------------

@jit(nopython=True, cache=True)
def build_fresnel_kernel_in(z, pixel_pitch, wavelength, ny, nx):
    """Build input Fresnel kernel (1, ny, nx)"""
    ppy, ppx = pixel_pitch
    # Create coordinate arrays
    y = (np.arange(ny) - round(ny / 2)) * ppy
    x = (np.arange(nx) - round(nx / 2)) * ppx
    # Manual meshgrid (Numba doesn't like np.meshgrid inside jit)
    Y = np.zeros((ny, nx), dtype=np.float64)
    X = np.zeros((ny, nx), dtype=np.float64)
    for i in range(ny):
        for j in range(nx):
            Y[i, j] = y[i]
            X[i, j] = x[j]

    phase = np.pi / (wavelength * z) * (X**2 + Y**2)
    kernel = np.exp(1j * phase).astype(np.complex64)
    return kernel.reshape(1, ny, nx)

@jit(nopython=True, cache=True)
def build_fresnel_kernel_out(z, pixel_pitch, wavelength, ny, nx):
    """Build output Fresnel kernel (1, ny, nx)"""
    ppy, ppx = pixel_pitch
    # Frequency coordinates
    fx = np.fft.fftfreq(nx, d=ppx)
    fx = np.fft.fftshift(fx)
    fy = np.fft.fftfreq(ny, d=ppy)
    fy = np.fft.fftshift(fy)

    # Manual meshgrid
    FX = np.zeros((ny, nx), dtype=np.float64)
    FY = np.zeros((ny, nx), dtype=np.float64)
    for i in range(ny):
        for j in range(nx):
            FY[i, j] = fy[i]
            FX[i, j] = fx[j]

    X = wavelength * z * FX
    Y = wavelength * z * FY
    phase = 1j * np.pi / (wavelength * z) * (X**2 + Y**2)
    kernel = (
        np.exp(1j * 2 * np.pi / wavelength * z) / (1j * wavelength * z) * np.exp(phase)
    ).astype(np.complex64)
    return kernel.reshape(1, ny, nx)

# ----------------------------------------------------------------------
# Fresnel transform (uses FFT, can be JIT‑compiled)
# ----------------------------------------------------------------------
@jit(nopython=True, cache=True)
def fresnel_transform(frames, z, pixel_pitch, wavelength, use_output_kernel=True):
    """
    Apply Fresnel transform to a stack of frames (nt, ny, nx) complex64.
    No zero padding.
    """
    nt, ny, nx = frames.shape
    # Build input kernel once per call (cached by Numba via cache=True)
    kernel_in = build_fresnel_kernel_in(z, pixel_pitch, wavelength, ny, nx)  # (1, ny, nx)

    # Multiply frames by kernel (broadcasting)
    tmp = frames * kernel_in  # (nt, ny, nx)

    # 2D FFT + shift (Numba supports np.fft.fft2 with axis)
    # Note: norm="ortho" not directly available in Numba's FFT; we apply scaling manually
    tmp = np.fft.fft2(tmp, axes=(-2, -1))
    tmp = np.fft.fftshift(tmp) # , axes=(-2, -1) TODO somehow fix this

    # Ortho norm: divide by sqrt(ny * nx) for each frame
    norm_factor = 1.0 / np.sqrt(ny * nx)
    tmp = tmp * norm_factor

    if use_output_kernel:
        kernel_out = build_fresnel_kernel_out(z, pixel_pitch, wavelength, ny, nx)
        tmp = tmp * kernel_out

    return tmp

# ----------------------------------------------------------------------
# Temporal FFT
# ----------------------------------------------------------------------
@jit(nopython=True, cache=True)
def fourier_time_transform(H):
    """FFT along time axis with ortho norm"""
    nt = H.shape[0]
    H_fft = np.fft.fft(H, axis=0)
    # ortho norm: divide by sqrt(nt) for each frequency
    H_fft = H_fft / np.sqrt(nt)
    return H_fft

# ----------------------------------------------------------------------
# Frequency filtering
# ----------------------------------------------------------------------
@jit(nopython=True, cache=True)
def frequency_symmetric_filtering(batch_size, sampling_freq, low_freq, high_freq=None):
    """Return boolean mask and corresponding frequencies (Numba‑compatible)."""
    freqs = np.fft.fftfreq(batch_size, 1.0 / sampling_freq)
    if high_freq is None:
        idxs = np.abs(freqs) > low_freq
    else:
        idxs = (np.abs(freqs) > low_freq) & (np.abs(freqs) < high_freq)
    # Extract selected frequencies
    selected_freqs = freqs[idxs]
    return idxs, selected_freqs

# ----------------------------------------------------------------------
# Squared magnitude
# ----------------------------------------------------------------------
@jit(nopython=True, parallel=True, cache=True)
def compute_squared_magnitude(A):
    """Compute |A|^2 for complex array A (nt, ny, nx)."""
    nt, ny, nx = A.shape
    result = np.zeros((nt, ny, nx), dtype=np.float64)
    for t in prange(nt):
        for y in range(ny):
            for x in range(nx):
                val = A[t, y, x]
                result[t, y, x] = val.real * val.real + val.imag * val.imag
    return result

# ----------------------------------------------------------------------
# Spectral moment
# ----------------------------------------------------------------------
@jit(nopython=True, parallel=True, cache=True)
def moment_jit(A, freqs, n):
    """
    Compute nth spectral moment.
    A: (n_freqs, ny, nx) real array
    freqs: (n_freqs,) float array
    Returns (ny, nx) array.
    """
    nf, ny, nx = A.shape
    result = np.zeros((ny, nx), dtype=np.float64)
    # Precompute weights
    weights = freqs ** n
    for f in prange(nf):
        w = weights[f]
        for y in range(ny):
            for x in range(nx):
                result[y, x] += A[f, y, x] * w
    return result

# ----------------------------------------------------------------------
# Render moments for a single batch
# ----------------------------------------------------------------------
def render_moments_cpu(A, parameters):
    """
    A: numpy array (nt, ny, nx) complex64
    Returns dict with computed moments.
    """
    propag_params = parameters.get("propag")
    moments_params = parameters.get("moments_calc")

    propag_mode = propag_params.get("mode")
    propag_dist = propag_params.get("propagation_dist")
    wavelength = parameters.get("wavelength")
    pixel_pitch = parameters.get("pixel_pitch")
    sampling_freq = parameters.get("sampling_freq")
    low_freq = moments_params.get("low_freq")
    high_freq = moments_params.get("high_freq")

    # Propagation
    if propag_mode == "Fresnel":
        A = fresnel_transform(A, propag_dist, pixel_pitch, wavelength, use_output_kernel=True)
    # Other modes could be added here (AngularSpectrum etc.)

    # Temporal FFT
    if parameters.get("time_transform") == "FourierTransform":
        A = fourier_time_transform(A)

    # Frequency filter
    idxs, freqs = frequency_symmetric_filtering(A.shape[0], sampling_freq, low_freq, high_freq)

    # Squared magnitude
    A_sq = compute_squared_magnitude(A)

    # Extract filtered frequencies
    filtered = A_sq[idxs, :, :]  # (n_freqs, ny, nx)

    # Compute moment(s)
    res = {
        "M0": moment_jit(filtered, freqs, 0),
        # "M1": moment_jit(filtered, freqs, 1),
        # "M2": moment_jit(filtered, freqs, 2),
    }
    return res

# ----------------------------------------------------------------------
# Main pipeline – reads batches directly from memmap
# ----------------------------------------------------------------------
def process_moments_cpu(file_path, parameters):
    """CPU pipeline using Numba JIT and memmap slicing (batches only in RAM)."""
    from holodoppler.file_io import FileReaderFactory  # local import if needed

    reader = FileReaderFactory.create(file_path)
    reader.open()

    # Extract parameters
    frame_reader = parameters.get("frame_reader")
    frame_batcher = parameters.get("frame_batcher")
    registration_params = parameters.get("registration")

    first_frame = frame_reader.get("first_frame")
    last_frame = frame_reader.get("last_frame")
    batch_size = frame_batcher.get("batch_size")
    batch_stride = frame_batcher.get("batch_stride")

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

    print(f"Processing {num_batch} batches (size {batch_size})")

    # Get memmap – huge file, do NOT load entirely
    m = reader.get_np_memmap()
    reader.close()  # file handle can be closed, memmap stays alive

    out_list = []

    # Optional registration reference
    M0_reg = None
    if registration_params.get("enabled", False):
        ref_start = registration_params.get("ref_first_frame", 0)
        ref_size = registration_params.get("ref_batch_size", 512)
        frames_reg = m[ref_start : ref_start + ref_size]  # slice stays memory‑mapped
        # Numba prefers C‑contiguous arrays, so copy if needed
        if not frames_reg.flags['C_CONTIGUOUS']:
            frames_reg = np.ascontiguousarray(frames_reg)
        M0_reg = render_moments_cpu(frames_reg.astype(np.complex64), parameters)["M0"]
        del frames_reg

    # Main loop
    for i in tqdm(range(num_batch), desc="Overall progress"):
        batch_start = first_frame + i * batch_stride
        batch_end = batch_start + batch_size
        frames = m[batch_start:batch_end]  # slice of memmap

        # Ensure C‑contiguous and correct dtype
        if not frames.flags['C_CONTIGUOUS']:
            frames = np.ascontiguousarray(frames)
        frames = frames.astype(np.complex64)  # complex64 for phase operations

        res = render_moments_cpu(frames, parameters)

        # Stack result as (1, H, W) then accumulate
        stacked = np.stack([res["M0"]], axis=0)  # (1, ny, nx)
        out_list.append(stacked)

        # Periodic cleanup
        if i % 10 == 0:
            gc.collect()

    # Concatenate all batches along time axis -> (T, ny, nx)
    final_result = np.concatenate(out_list, axis=0)

    # Final cleanup
    del m, out_list
    gc.collect()

    return final_result