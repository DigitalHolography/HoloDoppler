import numpy as np
from scipy import ndimage

import matplotlib.pyplot as plt

from holodoppler.file_reader import FileReaderFactory

# ============================================================
# PARAMETERS
# ============================================================
DATA_PATH = r"Y:\260113_IOP_BP\260113_FIY0713.holo"

n_frames = 512
n_peaks = 10

# Sampling intervals: replace with your actual values.
dt = 1.0       # seconds / frame (set to 1/fps if known)
dy = 1.0       # spatial units / pixel
dx = 1.0       # spatial units / pixel

center = True  # subtract temporal mean at every pixel

# ============================================================
# LOAD DATA
# ============================================================
reader = FileReaderFactory.create(DATA_PATH)
M = reader.read_frames(0, n_frames).copy().astype(np.float64)

nt, ny, nx = M.shape
print("Data shape:", M.shape)

# Remove static spatial content if desired.
# Keep the mean field separately for correct reconstruction.
mean_field = M.mean(axis=0, keepdims=True) if center else 0.0
Mc = M - mean_field

import numpy as np
import matplotlib.pyplot as plt
from scipy import fft, ndimage

# ============================================================
# SETTINGS
# ============================================================
target_fraction = 0.05
max_peaks = 2000

# Ellipsoidal blob radii in FFT bins: (ft, fy, fx).
blob_radius = (2, 14, 14)

# Local maxima search neighborhood.
peak_neighborhood = (2, 10, 10)

# Chunk size along temporal frequency.
chunk_size = 16
workers = 4

# ============================================================
# REAL 3D FFT
# ============================================================
Mc32 = np.asarray(Mc, dtype=np.float32)
nt, ny, nx = Mc32.shape

F = fft.rfftn(Mc32, axes=(0, 1, 2), workers=workers)
P = np.abs(F)**2
del Mc32

shape = P.shape
target_voxels = int(target_fraction * P.size)

print("Half-spectrum:", shape)
print(f"Target mask voxels: {target_voxels:,} ({target_fraction:.2%})")

# ============================================================
# FIND 3D LOCAL MAXIMA IN CHUNKS
# ============================================================
peak_coords = []
peak_powers = []

# A one-bin halo prevents chunk boundaries from creating peaks.
halo = 1

for start in range(0, nt, chunk_size):
    stop = min(start + chunk_size, nt)
    a = max(0, start - halo)
    b = min(nt, stop + halo)

    chunk = P[a:b]

    local_max = ndimage.maximum_filter(
        chunk,
        size=peak_neighborhood,
        mode="wrap",
    )

    lo = start - a
    hi = lo + stop - start

    core = chunk[lo:hi]
    core_max = local_max[lo:hi]

    # Exclude DC.
    peak_mask = (core == core_max) & (core > 0)

    if start == 0:
        peak_mask[0, 0, 0] = False

    coords = np.argwhere(peak_mask)
    if coords.size == 0:
        continue

    coords[:, 0] += start

    powers = P[coords[:, 0], coords[:, 1], coords[:, 2]]
    peak_coords.append(coords)
    peak_powers.append(powers)

if not peak_coords:
    raise RuntimeError("No nonzero local maxima found.")

peak_coords = np.concatenate(peak_coords)
peak_powers = np.concatenate(peak_powers)

# Retain strongest candidates only.
n_candidates = min(max_peaks, len(peak_powers))
top = np.argpartition(peak_powers, -n_candidates)[-n_candidates:]
peak_coords = peak_coords[top]
peak_powers = peak_powers[top]

order = np.argsort(peak_powers)[::-1]
peak_coords = peak_coords[order]
peak_powers = peak_powers[order]

print(f"Local maxima candidates: {len(peak_coords):,}")


# ============================================================
# BUILD BLOBS UNTIL THE 1% BUDGET IS REACHED — FAST
# ============================================================
rt, ry, rx = blob_radius
remove_mask = np.zeros(shape, dtype=bool)

tt, yy, xx = np.ogrid[-rt:rt+1, -ry:ry+1, -rx:rx+1]
blob_structure = (
    (tt / max(rt, 1))**2
    + (yy / max(ry, 1))**2
    + (xx / max(rx, 1))**2
) <= 1.0

offsets = np.argwhere(blob_structure) - np.array([rt, ry, rx])

boundary_x = {0}
if nx % 2 == 0:
    boundary_x.add(nx // 2)

removed_count = 0

for (ti, yi, xi) in peak_coords:
    if removed_count >= target_voxels:
        break

    coords = offsets + (ti, yi, xi)
    coords[:, 0] %= nt
    coords[:, 1] %= ny
    coords[:, 2] %= shape[2]

    if xi in boundary_x:
        partner = coords.copy()
        partner[:, 0] = (-partner[:, 0]) % nt
        partner[:, 1] = (-partner[:, 1]) % ny
        coords = np.concatenate((coords, partner), axis=0)

    # Mark only previously unmarked voxels; no full-array sum.
    t, y, x = coords.T
    new = ~remove_mask[t, y, x]
    remove_mask[t[new], y[new], x[new]] = True
    removed_count += int(new.sum())

print(
    f"Removed {removed_count:,} bins "
    f"({removed_count / remove_mask.size:.3%})"
)

# ============================================================
# FILTER AND INVERSE FFT
# ============================================================
F[remove_mask] = 0

filtered = fft.irfftn(
    F,
    s=(nt, ny, nx),
    axes=(0, 1, 2),
    workers=workers,
).astype(np.float32, copy=False)


# ============================================================
# DEBUG: 3D FFT POWER WITH REMOVED REGIONS OVERLAID
# ============================================================
# Run before deleting P and F.
# P has shape (ft, fy, fx//2+1), in rFFT ordering.
# remove_mask has the same shape.

fx = np.fft.rfftfreq(nx, d=dx)
fy = np.fft.fftfreq(ny, d=dy)
ft = np.fft.fftfreq(nt, d=dt)

# Shift the full-frequency axes to center zero frequency.
# Do not shift the rFFT fx axis.
P_centered = np.fft.fftshift(P, axes=(0, 1))
mask_centered = np.fft.fftshift(remove_mask, axes=(0, 1))

# Projection 1: fx, fy averaged over temporal frequency.
power_xy = np.mean(P_centered, axis=0)
removed_xy = np.any(mask_centered, axis=0)

# Projection 2: fx, ft averaged over vertical spatial frequency.
power_tx = np.mean(P_centered, axis=1)
removed_tx = np.any(mask_centered, axis=1)

# Centered axes for plotting.
fy_centered = np.fft.fftshift(fy)
ft_centered = np.fft.fftshift(ft)

# Log power for visualization.
eps = np.finfo(np.float32).tiny
log_xy = np.log10(power_xy + eps)
log_tx = np.log10(power_tx + eps)

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# ------------------------------------------------------------
# fx, fy projection
# ------------------------------------------------------------
axes[0].imshow(
    log_xy,
    origin="lower",
    aspect="auto",
    extent=[fx[0], fx[-1], fy_centered[0], fy_centered[-1]],
    cmap="gray",
)
axes[0].imshow(
    np.ma.masked_where(~removed_xy, removed_xy),
    origin="lower",
    aspect="auto",
    extent=[fx[0], fx[-1], fy_centered[0], fy_centered[-1]],
    cmap="Reds",
    alpha=0.8,
    interpolation="nearest",
)
axes[0].set_xlabel("fx")
axes[0].set_ylabel("fy")
axes[0].set_title("Mean power over ft — removed regions in red")

# ------------------------------------------------------------
# fx, ft projection
# ------------------------------------------------------------
axes[1].imshow(
    log_tx,
    origin="lower",
    aspect="auto",
    extent=[fx[0], fx[-1], ft_centered[0], ft_centered[-1]],
    cmap="gray",
)
axes[1].imshow(
    np.ma.masked_where(~removed_tx, removed_tx),
    origin="lower",
    aspect="auto",
    extent=[fx[0], fx[-1], ft_centered[0], ft_centered[-1]],
    cmap="Reds",
    alpha=0.8,
    interpolation="nearest",
)
axes[1].set_xlabel("fx")
axes[1].set_ylabel("ft")
axes[1].set_title("Mean power over fy — removed regions in red")

plt.tight_layout()
plt.show()

del P_centered, mask_centered, power_xy, power_tx



# ============================================================
# VISUAL CHECK
# ============================================================
frame = min(100, nt - 1)
removed = Mc[frame] - filtered[frame]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

vmax = max(
    float(np.max(np.abs(Mc[frame]))),
    float(np.max(np.abs(filtered[frame]))),
    1e-12,
)

axes[0].imshow(
    Mc[frame], cmap="RdBu_r", vmin=-vmax, vmax=vmax
)
axes[0].set_title("Original")

axes[1].imshow(
    filtered[frame], cmap="RdBu_r", vmin=-vmax, vmax=vmax
)
axes[1].set_title("Filtered")

axes[2].imshow(removed, cmap="RdBu_r")
axes[2].set_title("Removed contribution")

for ax in axes:
    ax.set_xticks([])
    ax.set_yticks([])

plt.tight_layout()
plt.show()
