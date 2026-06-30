"""
Utility functions for array operations
"""

import numpy as np

from scipy.ndimage import gaussian_filter as np_gaussian_filter
from scipy.ndimage import gaussian_filter1d
import numpy as np
from scipy.ndimage import zoom as zoom_cpu
import cupy as cp
from cupyx.scipy.ndimage import zoom as zoom_gpu

# in utils.py
import cv2

from pathlib import Path
import yaml
import json

from functools import cache

# # Assuming video_frames is a GPU array of shape (n_frames, height, width, channels)
# def resize_cupy(video_frames, scale_factor):
#     # zoom works on spatial dimensions only
#     return zoom(video_frames, (1, scale_factor, scale_factor, 1), order=1)

# For exact dimensions instead of scale
def square_cupy(video_frames):
    h, w = video_frames.shape[1], video_frames.shape[2]
    m = max(h,w)
    scale_h = m / h
    scale_w = m / w
    return zoom_gpu(video_frames, (1, scale_h, scale_w), order=1)

def normalize_to_uint8(data):
    """
    Normalizes any float array to 0-255 uint8.
    Handles (T, H, W) or (T, H, W, C).
    """

    data = np.asanyarray(data)

    if data.dtype == np.uint8:
        return data
    # Calculate global min/max across all dimensions except the first (Time)
    # Or global overall for consistency across the video
    vmin = data.min()
    vmax = data.max()

    # vectorized normalization
    normalized = 255 * (data - vmin) / (vmax - vmin + 1e-12)
    return np.clip(normalized, 0, 255).astype(np.uint8)

def write_video_file(path, frames, fps, fourcc_code="mp4v"):
    """
    Writes a video file.
    Expects frames as (T, H, W) or (T, H, W, C) in uint8.
    """
    if frames.ndim == 3:  # (T, H, W)
        h, w = frames.shape[1:]
        is_color = False
    elif frames.ndim == 4:  # (T, H, W, C)
        h, w = frames.shape[1:3]
        is_color = frames.shape[3] == 3
        if is_color:
            # Convert RGB to BGR for OpenCV
            frames = frames[..., ::-1]
    else:
        raise ValueError(f"Invalid frame shape: {frames.shape}")

    out = cv2.VideoWriter(
        path, cv2.VideoWriter_fourcc(*fourcc_code), fps, (w, h), isColor=is_color
    )
    for frame in frames:
        out.write(frame)
    out.release()

def resize_slicewise(img, new_h, new_w, axes=(-2, -1), xp=np, fft=np.fft):
    """
    Resize using FFT. Vectorized across all non-target axes. Keeping comparable values.

    Parameters
    ----------
    img : ndarray
        Input image array. The dimensions specified by `axes` will be resized.
    new_h, new_w : int
        Target height and width for the resize operation.
    axes : tuple, optional
        Axes to resize (height, width). Default is (-2, -1) for last two dimensions.
    xp : module, optional
        Array module (numpy or cupy). Default is numpy.
    fft : module, optional
        FFT module (numpy.fft or cupyx.scipy.fft). Default is numpy.fft.

    Returns
    -------
    resized : ndarray
        Resized image with same number of dimensions, but target size on specified axes.
    """

    # Get the target axes positions (convert negative indices)
    axes = tuple(axes)
    h_axis, w_axis = axes
    ndim = img.ndim

    # Convert negative axes to positive indices
    if h_axis < 0:
        h_axis = ndim + h_axis
    if w_axis < 0:
        w_axis = ndim + w_axis

    # Get original shape and ensure axes are valid
    orig_shape = img.shape
    orig_h = orig_shape[h_axis]
    orig_w = orig_shape[w_axis]

    # Create slices for indexing
    slice_before_h = [slice(None)] * ndim
    slice_before_w = [slice(None)] * ndim
    slice_before_h[h_axis] = slice(0, new_h)
    slice_before_w[w_axis] = slice(0, new_w)

    # Apply FFT to target axes
    # Move target axes to the end for easier vectorization
    axes_to_move = [h_axis, w_axis]
    other_axes = [i for i in range(ndim) if i not in axes_to_move]
    new_order = other_axes + axes_to_move
    inverse_order = list(np.argsort(new_order))

    # Transpose to bring target axes to the end
    img_transposed = xp.transpose(img, new_order)

    # Get shape after transpose
    transposed_shape = img_transposed.shape
    batch_shape = transposed_shape[:-2]

    # Reshape to 2D: (batch_size, orig_h * orig_w) for FFT
    img_flat = img_transposed.reshape(-1, orig_h, orig_w)

    # Apply 2D FFT to each slice
    img_fft = fft.fft2(img_flat, axes=(-2, -1))

    # Crop or pad in frequency domain
    # Center the FFT (shift zero frequency to center)
    img_fft_shifted = fft.fftshift(img_fft, axes=(-2, -1))

    # Calculate crop/pad regions
    h_center = orig_h // 2
    w_center = orig_w // 2
    h_half_new = new_h // 2
    w_half_new = new_w // 2

    # Create output frequency array
    new_shape_2d = (img_fft.shape[0], new_h, new_w)
    img_fft_resized = xp.zeros(new_shape_2d, dtype=img_fft.dtype)

    # Determine source slices
    h_start_src = max(0, h_center - h_half_new)
    h_end_src = min(orig_h, h_center + h_half_new + (new_h % 2))
    w_start_src = max(0, w_center - w_half_new)
    w_end_src = min(orig_w, w_center + w_half_new + (new_w % 2))

    # Determine destination slices
    h_start_dst = max(0, h_half_new - h_center)
    h_end_dst = h_start_dst + (h_end_src - h_start_src)
    w_start_dst = max(0, w_half_new - w_center)
    w_end_dst = w_start_dst + (w_end_src - w_start_src)

    # Copy frequency components
    img_fft_resized[:, h_start_dst:h_end_dst, w_start_dst:w_end_dst] = img_fft_shifted[
        :, h_start_src:h_end_src, w_start_src:w_end_src
    ]

    # Inverse shift and inverse FFT
    img_fft_resized_shifted = fft.ifftshift(img_fft_resized, axes=(-2, -1))
    img_resized_flat = fft.ifft2(img_fft_resized_shifted, axes=(-2, -1)).real

    # Reshape back to original batch dimensions
    img_resized_batch = img_resized_flat.reshape(*batch_shape, new_h, new_w)

    # Transpose back to original axis order
    img_resized = xp.transpose(img_resized_batch, inverse_order)

    # Scale to preserve energy/values
    scale_factor = (orig_h * orig_w) / (new_h * new_w)
    img_resized = img_resized * scale_factor

    return img_resized

def zoom_slicewise_fast(arr, new_h, new_w, axes=(-2, -1), use_gpu=True):
    """
    Zoom each 2D slice independently to new height and width.
    Vectorized for better performance.
    """
    
    original_shape = arr.shape
    ndim = len(original_shape)
    
    # Determine dimensions
    if ndim == 3:  # (nt, ny, nx)
        nt, ny, nx = original_shape
        nchannel = 1
        arr_reshaped = arr.reshape(nt, 1, ny, nx)
    elif ndim == 4:  # (nt, nchannel, ny, nx)
        nt, nchannel, ny, nx = original_shape
        arr_reshaped = arr
    else:
        raise ValueError(f"Expected 3 or 4D array, got {ndim}D")
    
    # Calculate zoom factors
    zoom_h = new_h / ny
    zoom_w = new_w / nx
    
    # Reshape to combine all slices into a single batch dimension
    # This way each slice is processed independently but in parallel
    total_slices = nt * nchannel
    arr_flat = arr_reshaped.reshape(total_slices, ny, nx)
    
    if use_gpu:
        try:
            
            if not isinstance(arr, cp.ndarray):
                arr_flat_gpu = cp.asarray(arr_flat)
            else:
                arr_flat_gpu = arr_flat
            
            # Create output array
            result_flat_gpu = cp.zeros((total_slices, new_h, new_w), dtype=arr_flat_gpu.dtype)
            
            # Process each slice independently (still loop, but fewer iterations)
            for i in range(total_slices):
                result_flat_gpu[i, :, :] = zoom_gpu(arr_flat_gpu[i, :, :], (zoom_h, zoom_w), order=1)
            
            # Reshape back
            result_gpu = result_flat_gpu.reshape(nt, nchannel, new_h, new_w)
            
            if ndim == 3:
                return result_gpu.reshape(nt, new_h, new_w).get()
            else:
                return result_gpu.get()
                
        except (ImportError, Exception) as e:
            print(f"GPU zoom failed or not available: {e}")
            print("Falling back to CPU...")
    
    # CPU version
    result_flat = np.zeros((total_slices, new_h, new_w), dtype=arr_flat.dtype)
    
    for i in range(total_slices):
        result_flat[i, :, :] = zoom_cpu(arr_flat[i, :, :], (zoom_h, zoom_w), order=1)
    
    result = result_flat.reshape(nt, nchannel, new_h, new_w)
    
    if ndim == 3:
        return result.reshape(nt, new_h, new_w)
    else:
        return result

def resize_fft2_slicewise(img, new_h, new_w, axes=(-2, -1), xp=np, fft=np.fft):
    """Spectral resize using FFT. Vectorized across all non-target axes."""
    # 1. Move target axes to front: (..., H, W, ...) -> (H, W, ...)
    img_t = np.moveaxis(img, axes, (0, 1))
    h, w = img_t.shape[:2]

    # 2. Vectorized FFT across the first two dimensions
    F = fft.fftshift(fft.fft2(img_t, axes=(0, 1)), axes=(0, 1))

    # 3. Create zero-padded array and calculate center crop/pad indices
    F_new = xp.zeros((new_h, new_w, *img_t.shape[2:]), dtype=F.dtype)
    h_min, w_min = min(h, new_h), min(w, new_w)

    ho, wo = (h - h_min) // 2, (w - w_min) // 2
    hn, wn = (new_h - h_min) // 2, (new_w - w_min) // 2

    # 4. Perform center crop/pad (Vectorized)
    F_new[hn : hn + h_min, wn : wn + w_min, ...] = F[
        ho : ho + h_min, wo : wo + w_min, ...
    ]

    # 5. Inverse FFT and Scale
    res_t = fft.ifftshift(F_new, axes=(0, 1))
    res_t = fft.ifft2(res_t, axes=(0, 1)).real * (new_h * new_w / (h * w))

    # 6. Restore original axes positions
    return np.moveaxis(res_t, (0, 1), axes)

# def resize_matlab_slicewise(img, new_h, new_w, axes=(-2, -1), xp=np):
#     """Spatial resize. Loops over remaining dimensions since imresize is 2D."""
#     img_t = np.moveaxis(img, axes, (0, 1))
#     h, w = img_t.shape[:2]

#     # Reshape to (H, W, -1) to loop through all other dimensions as one slice
#     flat_img = img_t.reshape(h, w, -1)
#     out = xp.empty((new_h, new_w, flat_img.shape[-1]), dtype=img.dtype)

#     for i in range(flat_img.shape[-1]):
#         # Assuming imresize is a provided utility function
#         out[:, :, i] = imresize(flat_img[:, :, i], output_shape=(new_h, new_w))

#     # Reshape back to target axes and move axes back
#     res_t = out.reshape(new_h, new_w, *img_t.shape[2:])
#     return np.moveaxis(res_t, (0, 1), axes)


def pad_array_centrally(arr, new_shape, xp):
    """Pad array centrally to new shape"""
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    ny, nx = arr.shape[-2:]
    new_ny, new_nx = new_shape

    if new_ny < ny or new_nx < nx:
        raise ValueError("new_shape must be >= current shape")

    pad_y0 = (new_ny - ny) // 2
    pad_y1 = new_ny - ny - pad_y0
    pad_x0 = (new_nx - nx) // 2
    pad_x1 = new_nx - nx - pad_x0

    pad_width = [(0, 0)] * arr.ndim
    pad_width[-2] = (pad_y0, pad_y1)
    pad_width[-1] = (pad_x0, pad_x1)

    return xp.pad(arr, pad_width, mode="constant")


def crop_array_centrally(arr, target_shape, xp):
    """Crop array centrally to target shape"""
    if isinstance(target_shape, int):
        target_shape = (target_shape, target_shape)

    ny, nx = arr.shape[-2:]
    tgt_ny, tgt_nx = target_shape

    if tgt_ny > ny or tgt_nx > nx:
        raise ValueError("target_shape must be <= current shape")

    crop_y0 = (ny - tgt_ny) // 2
    crop_y1 = crop_y0 + tgt_ny
    crop_x0 = (nx - tgt_nx) // 2
    crop_x1 = crop_x0 + tgt_nx

    slices = [slice(None)] * arr.ndim
    slices[-2] = slice(crop_y0, crop_y1)
    slices[-1] = slice(crop_x0, crop_x1)

    return arr[tuple(slices)]

@cache
def elliptical_mask(ny, nx, radius_frac, xp):
    """Create elliptical boolean mask"""
    radius_frac = max(0.0, min(1.0, float(radius_frac)))
    a = (nx / 2) * radius_frac
    b = (ny / 2) * radius_frac

    Y, X = xp.ogrid[:ny, :nx]
    cy, cx = ny / 2, nx / 2

    mask = ((X - cx) / a) ** 2 + ((Y - cy) / b) ** 2 <= 1.0
    return mask


def gaussian_flatfield(A, gaussian_width, gaussian_filter_func):
    """Apply Gaussian flatfield correction"""
    return A / gaussian_filter_func(A, gaussian_width)


def subpixel_parabola(vm, v0, vp):
    """Subpixel refinement using parabola fit"""
    denom = vm - 2.0 * v0 + vp
    if abs(float(denom)) < 1e-12:
        return 0.0
    return 0.5 * float(vm - vp) / float(denom)


def signed_peak(ky, kx, ny, nx):
    """Convert peak indices to signed shifts"""
    if ky > ny // 2:
        ky -= ny
    if kx > nx // 2:
        kx -= nx
    return float(ky), float(kx)


def temporal_gaussian_filter(arr, sigma):
    """Apply 1D Gaussian filter along time axis"""
    if sigma == 0:
        return arr
    from scipy.ndimage import gaussian_filter1d

    return gaussian_filter1d(arr.astype(np.float32), sigma=sigma, axis=2)


def normalize_image(arr):
    """Normalize image to 0-255 range"""
    arr = arr.astype(np.float32)
    lo, hi = arr.min(), arr.max()
    if hi > lo:
        return ((arr - lo) / (hi - lo) * 255).astype(np.uint8)
    return arr.astype(np.uint8)


def temporal_gaussian(arr, sigma):
    if sigma == 0:
        return arr
    return gaussian_filter1d(arr.astype(np.float32), sigma=sigma, axis=2)


def flatfield3D(arr, gw):
    if arr.ndim != 3:
        raise ValueError("Input array must be 3D")
    if gw <= 1:
        return arr
    blurred = np_gaussian_filter(arr, sigma=(gw, gw, 1))
    blurred[blurred == 0] = 1
    return arr / blurred

def complex_to_color(complex_img, mode='hsv', normalize=True):
    """
    Convert a complex 2D array to a color image.
    
    Parameters:
    -----------
    complex_img : np.ndarray
        2D complex-valued array
    mode : str
        Color mapping mode: 'hsv', 'phase_amplitude', 'log_amplitude', or 'amplitude_phase'
    normalize : bool
        Whether to normalize amplitude values to [0,1]
    
    Returns:
    --------
    np.ndarray
        RGB image (H, W, 3) with values in [0, 255] dtype=uint8
    """
    phase = np.angle(complex_img)  # Range: [-π, π]
    amplitude = np.abs(complex_img)
    
    if normalize and mode != 'log_amplitude':
        amplitude = amplitude / (amplitude.max() + 1e-10)
    elif mode == 'log_amplitude':
        amplitude = np.log1p(amplitude)
        amplitude = amplitude / (amplitude.max() + 1e-10)
    
    if mode == 'hsv':
        # HSV: Hue = phase, Saturation = 1, Value = amplitude
        hue = (phase + np.pi) / (2 * np.pi)  # Map to [0, 1]
        saturation = np.ones_like(phase)
        value = amplitude
        
        # Convert HSV to RGB
        rgb = hsv_to_rgb(np.stack([hue, saturation, value], axis=-1))
        
    elif mode == 'phase_amplitude':
        # RGB: Red = cos(phase), Green = sin(phase), Blue = amplitude
        r = (np.cos(phase) + 1) / 2
        g = (np.sin(phase) + 1) / 2
        b = amplitude
        rgb = np.stack([r, g, b], axis=-1)
        
    elif mode == 'amplitude_phase':
        # Amplitude modulates intensity, phase modulates color
        hue = (phase + np.pi) / (2 * np.pi)
        # Use amplitude as both saturation and value for different effects
        saturation = np.clip(amplitude * 1.5, 0, 1)
        value = np.clip(amplitude * 1.2, 0, 1)
        rgb = hsv_to_rgb(np.stack([hue, saturation, value], axis=-1))
        
    elif mode == 'log_amplitude_phase':
        # Log amplitude with phase coloring
        amplitude_log = np.log1p(np.abs(complex_img))
        amplitude_log = amplitude_log / (amplitude_log.max() + 1e-10)
        hue = (phase + np.pi) / (2 * np.pi)
        rgb = hsv_to_rgb(np.stack([hue, np.ones_like(phase), amplitude_log], axis=-1))
        
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'hsv', 'phase_amplitude', 'amplitude_phase', or 'log_amplitude_phase'")
    
    # Convert to uint8 in range [0, 255]
    rgb = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    
    return rgb

def hsv_to_rgb(hsv):
    """
    Convert HSV to RGB.
    
    Parameters:
    -----------
    hsv : np.ndarray
        HSV image (H, W, 3) with values in [0, 1]
    
    Returns:
    --------
    np.ndarray
        RGB image (H, W, 3) with values in [0, 1]
    """
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    
    h = h * 6.0  # Scale hue to [0, 6)
    i = np.floor(h).astype(int)
    f = h - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    
    i = i % 6
    rgb = np.zeros_like(hsv)
    
    # Vectorized assignment
    mask0 = i == 0
    rgb[mask0] = np.stack([v[mask0], t[mask0], p[mask0]], axis=-1)
    
    mask1 = i == 1
    rgb[mask1] = np.stack([q[mask1], v[mask1], p[mask1]], axis=-1)
    
    mask2 = i == 2
    rgb[mask2] = np.stack([p[mask2], v[mask2], t[mask2]], axis=-1)
    
    mask3 = i == 3
    rgb[mask3] = np.stack([p[mask3], q[mask3], v[mask3]], axis=-1)
    
    mask4 = i == 4
    rgb[mask4] = np.stack([t[mask4], p[mask4], v[mask4]], axis=-1)
    
    mask5 = i == 5
    rgb[mask5] = np.stack([v[mask5], p[mask5], q[mask5]], axis=-1)
    
    return rgb

# Alternative simpler version using only numpy and standard functions
def complex_to_color_simple(complex_img):
    """
    Simple conversion: phase -> hue, amplitude -> value.
    """
    phase = np.angle(complex_img)
    amplitude = np.abs(complex_img)
    
    # Normalize amplitude
    amplitude = amplitude / (amplitude.max() + 1e-10)
    
    # Map phase from [-π, π] to [0, 1] for hue
    hue = (phase + np.pi) / (2 * np.pi)
    
    # Create HSV image
    hsv = np.stack([hue, np.ones_like(hue), amplitude], axis=-1)
    
    # Convert to RGB manually (simpler HSV to RGB)
    rgb = np.zeros((*complex_img.shape, 3))
    
    h = hue * 6.0
    i = np.floor(h).astype(int)
    f = h - i
    p = amplitude * (1 - 1)  # saturation=1, so p=0
    q = amplitude * (1 - f)
    t = amplitude * f
    
    i = i % 6
    # Apply for each hue sector
    rgb[i == 0] = np.stack([amplitude[i == 0], t[i == 0], p[i == 0]], axis=-1)
    rgb[i == 1] = np.stack([q[i == 1], amplitude[i == 1], p[i == 1]], axis=-1)
    rgb[i == 2] = np.stack([p[i == 2], amplitude[i == 2], t[i == 2]], axis=-1)
    rgb[i == 3] = np.stack([p[i == 3], q[i == 3], amplitude[i == 3]], axis=-1)
    rgb[i == 4] = np.stack([t[i == 4], p[i == 4], amplitude[i == 4]], axis=-1)
    rgb[i == 5] = np.stack([amplitude[i == 5], p[i == 5], q[i == 5]], axis=-1)
    
    return (rgb * 255).astype(np.uint8)


def load_config(config_path):
    if isinstance(config_path,dict):
        config = config_path
    else :
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



def _pad_to_even(frames):
    """
    Pads H/W to even size for libx264/yuv420p.
    Supports:
      (T, H, W)
      (T, H, W, C)
    """
    h = frames.shape[1]
    w = frames.shape[2]

    pad_h = h % 2
    pad_w = w % 2

    if pad_h == 0 and pad_w == 0:
        return frames

    if frames.ndim == 3:
        pad_width = (
            (0, 0),      # T
            (0, pad_h),  # H
            (0, pad_w),  # W
        )
    else:
        pad_width = (
            (0, 0),      # T
            (0, pad_h),  # H
            (0, pad_w),  # W
            (0, 0),      # C
        )

    return np.pad(frames, pad_width, mode="edge")

def unsharp_projection(
    bm,
    imgs_arr,
    output_shape,
    radius=2.0,
    amount=2.0,
    dtype=np.float32,
):

    imgs_arr = np.asarray(imgs_arr, dtype=dtype)

    if imgs_arr.ndim != 3:
        raise ValueError("imgs_arr must have shape (nt, nx, ny)")

    nt, nx, ny = imgs_arr.shape
    out_nx, out_ny = output_shape

    zoom_factors = (out_nx / nx, out_ny / ny)
    
    xp = bm.xp


    imgs_gpu = xp.asarray(imgs_arr)

    acc = xp.zeros(output_shape, dtype=xp.float32)

    for i in range(nt):
        img = imgs_gpu[i]

        blurred = bm.gaussian_filter(img, sigma=radius)
        sharp = img + amount * (img - blurred)

        sharp_resized = bm.zoom(
            sharp,
            zoom_factors,
            order=3,          # bicubic interpolation, prettier / MATLAB like
            # mode="nearest",
        )

        acc += sharp_resized

    projection = acc / nt
    return xp.asnumpy(projection)
    
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
            parameters["pixel_pitch"] = (holofooter["info"]["pixel_pitch"]["y"] * 1e-6, holofooter["info"]["pixel_pitch"]["x"] * 1e-6)
        if parameters.get("sampling_freq") == "use_holovibes" and holofooter is not None:
            parameters["sampling_freq"] = holofooter["info"]["camera_fps"]
        if parameters.get("high_freq") == "use_holovibes" and holofooter is not None:
            parameters["high_freq"] = holofooter["info"]["camera_fps"]/2
    except Exception as e:
        print(f"Issue from holovibes footer: {e}")
    return parameters