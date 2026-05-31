"""
Utility functions for array operations
"""

import numpy as np
import scipy.fftpack as fft
from matlab_imresize import imresize
from scipy.ndimage import gaussian_filter as np_gaussian_filter
from scipy.ndimage import gaussian_filter1d

# in utils.py
import cv2
import numpy as np

from pathlib import Path
import yaml
import json


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


import numpy as np


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


def resize_matlab_slicewise(img, new_h, new_w, axes=(-2, -1), xp=np):
    """Spatial resize. Loops over remaining dimensions since imresize is 2D."""
    img_t = np.moveaxis(img, axes, (0, 1))
    h, w = img_t.shape[:2]

    # Reshape to (H, W, -1) to loop through all other dimensions as one slice
    flat_img = img_t.reshape(h, w, -1)
    out = xp.empty((new_h, new_w, flat_img.shape[-1]), dtype=img.dtype)

    for i in range(flat_img.shape[-1]):
        # Assuming imresize is a provided utility function
        out[:, :, i] = imresize(flat_img[:, :, i], output_shape=(new_h, new_w))

    # Reshape back to target axes and move axes back
    res_t = out.reshape(new_h, new_w, *img_t.shape[2:])
    return np.moveaxis(res_t, (0, 1), axes)


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
