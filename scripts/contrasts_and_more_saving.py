

import h5py
import numpy as np
import cupy as cp
import time
from pathlib import Path
from scipy.ndimage import gaussian_filter
import imageio.v3 as iio
from holodoppler.saving import _write_video_fast
from holodoppler.utils import stretchlim, imadjustcp, stretchlimcp, scaling
from cupyx.scipy.ndimage import zoom, gaussian_filter


""" From an h5 file containing raw images arrays this scripts can generate avi and pngs with high quality of details with different parameters"""


INPUT = r"D:\STAGE\250314_GUJ_L\250314_GUJ_L_HD\h5\250314_GUJ_L_HD_output.h5"

# Multiple parameter sets for different results
# GAMMA_VALUES = [0.5, 0.8, 1.0, 1.2, 1.5]  # Different gamma values for contrast
LOW_PERCENT = 1.0
HIGH_PERCENT = 99.0

BRIGHTNESS = 1.
FPS = 30

# Interpolation and smoothing parameters
INTERPOLATION_FACTOR = 2  # Interpolate 2 times
GAUSSIAN_SIGMA = [3, 0.1, 0.1]  # Sigma for Gaussian3D filter



input_path = Path(INPUT)
output_dir = input_path.parent 
output_dir.mkdir(exist_ok=True)

def normalize(data):
    lo, hi = data.min(), data.max()
    return ((data - lo) / (hi - lo))

def save_data_avi_png(data, name):
    png_path = output_dir / "png" 
    png_path.mkdir(exist_ok=True)
    png_path = png_path / f"{name}.png"

    data_avg = np.mean(data, axis=0)
    data_avg = (data_avg*255).astype(np.uint8)
    iio.imwrite(png_path, data_avg)

    data = (data*255).astype(np.uint8)

    avi_path = output_dir / "avi" 
    avi_path.mkdir(exist_ok=True)
    avi_path = avi_path / f"{name}.avi"
    _write_video_fast(avi_path,data,FPS,codec="mjpeg")




with h5py.File(input_path, 'r') as f:
    print("\nFields in H5 file:")
    for key in f.keys():
        print(f"  - {key}: {f[key].shape} {f[key].dtype}")

    target_fields = ['M0', 'M1', 'M2']
    band_fields = [key for key in f.keys() if key.startswith('band_')]
    all_fields = ["M0ff"]#target_fields + band_fields

    for field_name in all_fields:
        
        if field_name not in f:
            print(f"Warning: {field_name} not found in H5 file")
            continue
        data = f[field_name][()]
        if data.ndim != 3:
            print(f"  Skipping {field_name}: expected 3D (time, ny, nx), got {data.shape}D")
            continue

        print(f"processing {field_name}, of shape {data.shape}")
        
        data = cp.array(data)

        data = zoom(data, (1, INTERPOLATION_FACTOR, INTERPOLATION_FACTOR))
        data = gaussian_filter(data, sigma=tuple(GAUSSIAN_SIGMA))
        low, high = stretchlimcp(data, low_percent=LOW_PERCENT, high_percent=HIGH_PERCENT)
        data = scaling(data, low, high)


        # for gamma in GAMMA_VALUES:
        #     # data = imadjustcp(data, low, high, gamma = gamma)

        data = normalize(data)
        data = cp.clip(data*BRIGHTNESS, 0, 1)
        data = normalize(data)
        save_data_avi_png(data.get(),field_name+"_improved")


