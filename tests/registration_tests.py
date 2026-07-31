import numpy as np
import matplotlib.pyplot as plt
from scipy import fft
from scipy import ndimage as ndi

from holodoppler.registration import *

# -------------------------------------------------------
# Load images
# -------------------------------------------------------

fixed = plt.imread("debug_outputs/debug_M0ff.png").astype(np.float32)
moving = plt.imread("debug_outputs/debug_M0ff2.png").astype(np.float32)

if fixed.ndim == 3:
    fixed = fixed[..., 0]
if moving.ndim == 3:
    moving = moving[..., 0]

# -------------------------------------------------------
# Translation registration
# -------------------------------------------------------

ty, tx = register_images_shifts(
    np,
    fft,
    fixed,
    moving,
)

moving_T = apply_register_images_shifts(
    np,
    fft,
    moving,
    ty,
    tx,
)

print(f"Translation : ty={ty:.3f}  tx={tx:.3f}")

# -------------------------------------------------------
# Crop
# -------------------------------------------------------

radius = 0.8

fixed_crop = crop_inscribed_rectangle(np, fixed, radius)
moving_crop = crop_inscribed_rectangle(np, moving_T, radius)

a = fixed_crop.astype(np.float32)
b = moving_crop.astype(np.float32)

a = (a - a.min()) / (a.max() - a.min() + 1e-8)
b = (b - b.min()) / (b.max() - b.min() + 1e-8)

rgb = np.zeros(a.shape + (3,), dtype=np.float32)
rgb[..., 0] = a          # red
rgb[..., 1] = b          # green
rgb[..., 2] = b          # blue

plt.figure(figsize=(7,7))
plt.imshow(rgb)
plt.title("Fixed (red) / Moving (cyan)")
plt.axis("off")
plt.show()

# -------------------------------------------------------
# FFT Magnitudes
# -------------------------------------------------------

F_fixed = np.abs(fft.fftshift(fft.fft2(fixed_crop)))
F_moving = np.abs(fft.fftshift(fft.fft2(moving_crop)))

# Uncomment if wanted
F_fixed = np.log1p(F_fixed)
F_moving = np.log1p(F_moving)

ny, nx = F_fixed.shape

yy, xx = np.mgrid[:ny, :nx]
cy = (ny - 1) / 2
cx = (nx - 1) / 2

rr = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)

F_fixed_hp = F_fixed * rr
F_moving_hp = F_moving * rr

# -------------------------------------------------------
# Log-polar
# -------------------------------------------------------

radial_bins = min(ny, nx) // 2
angular_bins = 720

LP_fixed = logpolar_transform(
    np,
    ndi,
    F_fixed_hp,
    radial_bins,
    angular_bins,
)

LP_moving = logpolar_transform(
    np,
    ndi,
    F_moving_hp,
    radial_bins,
    angular_bins,
)

# -------------------------------------------------------
# Correlation surface
# -------------------------------------------------------

fa = fft.fft2(LP_fixed)
fb = fft.fft2(LP_moving)

corr = fft.ifft2(fb * fa.conj())
corr = np.abs(corr)

dr, dtheta = phase_corr_subpixel(
    np,
    fft,
    LP_fixed,
    LP_moving,
)

angle = -360 * dtheta / angular_bins

max_radius = min((nx - 1) / 2, (ny - 1) / 2)
log_step = np.log(max_radius) / (radial_bins - 1)
scale = np.exp(dr * log_step)

print(f"Rotation : {angle:.3f} deg")
print(f"Scale    : {scale:.6f}")

moving_TR = apply_rotation_scale(
    np,
    ndi,
    moving_T,
    angle,
    scale,
)

# -------------------------------------------------------
# Overlay helper
# -------------------------------------------------------

def overlay(a, b):
    a = a.astype(np.float32)
    b = b.astype(np.float32)

    a = (a - a.min()) / (a.max() - a.min() + 1e-8)
    b = (b - b.min()) / (b.max() - b.min() + 1e-8)

    rgb = np.zeros(a.shape + (3,), dtype=np.float32)

    rgb[..., 0] = a
    rgb[..., 1] = b
    rgb[..., 2] = b

    return rgb

# -------------------------------------------------------
# Display
# -------------------------------------------------------

fig, ax = plt.subplots(3, 4, figsize=(18, 13))

ax[0,0].imshow(fixed, cmap="gray")
ax[0,0].set_title("Fixed")

ax[0,1].imshow(moving, cmap="gray")
ax[0,1].set_title("Moving")

ax[0,2].imshow(moving_T, cmap="gray")
ax[0,2].set_title("After Translation")

ax[0,3].imshow(moving_TR, cmap="gray")
ax[0,3].set_title("After Rotation+Scale")

ax[1,0].imshow(np.log1p(F_fixed_hp), cmap="magma")
ax[1,0].set_title("FFT Fixed")

ax[1,1].imshow(np.log1p(F_moving_hp), cmap="magma")
ax[1,1].set_title("FFT Moving")

ax[1,2].imshow(LP_fixed, aspect="auto", cmap="magma")
ax[1,2].set_title("LogPolar Fixed")

ax[1,3].imshow(LP_moving, aspect="auto", cmap="magma")
ax[1,3].set_title("LogPolar Moving")

ax[2,0].imshow(corr, cmap="viridis")
ax[2,0].set_title("LogPolar Correlation")

ax[2,1].imshow(overlay(fixed, moving))
ax[2,1].set_title("Overlay Original")

ax[2,2].imshow(overlay(fixed, moving_T))
ax[2,2].set_title("Overlay Translation")

ax[2,3].imshow(overlay(fixed, moving_TR))
ax[2,3].set_title("Overlay Final")

for a in ax.ravel():
    a.axis("off")

plt.tight_layout()
plt.show()