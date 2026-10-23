
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import maximum_filter

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

# Peak detection: minimum separation in FFT bins.
# Increase to avoid selecting nearby peaks.
min_separation = (3, 3, 3)  # (ft, fy, fx)

# Half-width of each reconstruction mask, in FFT bins.
# Increase to capture a broader spectral contribution.
f_width_factor = 15
peak_width = (2, 3*f_width_factor, 3*f_width_factor)      # (ft, fy, fx)

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

# ============================================================
# 3D FFT
# ============================================================
F = np.fft.fftn(Mc, axes=(0, 1, 2))
P = np.abs(F)**2

# Centered copies are used for visualization and peak search.
Fc = np.fft.fftshift(F)
Pc = np.fft.fftshift(P)

ft = np.fft.fftshift(np.fft.fftfreq(nt, d=dt))
fy = np.fft.fftshift(np.fft.fftfreq(ny, d=dy))
fx = np.fft.fftshift(np.fft.fftfreq(nx, d=dx))

# ============================================================
# FIND DISTINCT PEAKS
# ============================================================
# Suppress the DC bin and its immediate neighborhood.
Psearch = Pc.copy()

ct, cy, cx = nt // 2, ny // 2, nx // 2
dc_radius = (1, 1, 1)

Psearch[
    max(0, ct-dc_radius[0]):ct+dc_radius[0]+1,
    max(0, cy-dc_radius[1]):cy+dc_radius[1]+1,
    max(0, cx-dc_radius[2]):cx+dc_radius[2]+1,
] = 0

# Find local maxima in a neighborhood.
neighborhood = tuple(2 * r + 1 for r in min_separation)
local_max = Psearch == maximum_filter(
    Psearch, size=neighborhood, mode="wrap"
)
Psearch[~local_max] = 0

# Coordinates of the conjugate-symmetric partner in shifted FFT.
def conjugate_index(idx, shape):
    return tuple((2 * (n // 2) - i) % n for i, n in zip(idx, shape))

peaks = []
suppressed = np.zeros(Psearch.shape, dtype=bool)

for _ in range(n_peaks):
    work = Psearch.copy()
    work[suppressed] = 0

    idx = np.unravel_index(np.argmax(work), work.shape)
    power = work[idx]

    if power <= 0:
        print("No more distinct peaks.")
        break

    partner = conjugate_index(idx, Psearch.shape)

    peaks.append((idx, power))
    
    # Suppress both a peak and its conjugate partner.
    for p in (idx, partner):
        slices = tuple(
            slice(max(0, i-r), min(n, i+r+1))
            for i, r, n in zip(p, min_separation, Psearch.shape)
        )
        suppressed[slices] = True

print("\nDetected spectral peaks:")
for k, (idx, power) in enumerate(peaks, 1):
    i, j, l = idx
    print(
        f"{k}: ft={ft[i]:.6g}, fy={fy[j]:.6g}, "
        f"fx={fx[l]:.6g}, power={power:.4e}"
    )

# ============================================================
# VISUALIZE THE 3D SPECTRUM USING 2D MAX PROJECTIONS
# ============================================================
eps = np.finfo(float).tiny
logP = np.log10(Pc + eps)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Max projection over temporal frequency: spatial spectrum
axes[0].imshow(
    logP.max(axis=0),
    origin="lower", aspect="auto",
    extent=[fx[0], fx[-1], fy[0], fy[-1]],
)
axes[0].set_xlabel("fx")
axes[0].set_ylabel("fy")
axes[0].set_title("Max log power over ft")

# Max projection over vertical spatial frequency
axes[1].imshow(
    logP.max(axis=1),
    origin="lower", aspect="auto",
    extent=[fx[0], fx[-1], ft[0], ft[-1]],
)
axes[1].set_xlabel("fx")
axes[1].set_ylabel("ft")
axes[1].set_title("Max log power over fy")

plt.tight_layout()

# ============================================================
# BUILD PEAK MASKS AND RECONSTRUCT CONTRIBUTIONS
# ============================================================
components = []
claimed = np.zeros(F.shape, dtype=bool)

# Convert shifted peak indices to unshifted FFT indices.
def unshift_index(idx, shape):
    return tuple((i - n // 2) % n for i, n in zip(idx, shape))

for k, (idx, power) in enumerate(peaks, 1):
    idx_unshift = unshift_index(idx, F.shape)
    partner_unshift = tuple(
        (-i) % n for i, n in zip(idx_unshift, F.shape)
    )

    mask = np.zeros(F.shape, dtype=bool)

    # Include neighborhoods around both conjugate peaks.
    for p in (idx_unshift, partner_unshift):
        slices = tuple(
            slice(max(0, i-r), min(n, i+r+1))
            for i, r, n in zip(p, peak_width, F.shape)
        )
        mask[slices] = True

    # Avoid assigning the same frequency bin to multiple components.
    mask &= ~claimed
    claimed |= mask

    component = np.fft.ifftn(F * mask).real
    components.append(component)

# Sum of selected components and remaining spectrum.
selected = np.sum(components, axis=0) if components else np.zeros_like(Mc)
residual = Mc - selected

print("\nReconstruction check:")
print("Max absolute error:", np.max(np.abs(Mc - selected - residual)))

# ============================================================
# DISPLAY ORIGINAL, COMPONENTS, AND RESIDUAL
# ============================================================
frame = min(100, nt - 1)

images = [Mc[frame], *[c[frame] for c in components], residual[frame]]
titles = ["Centered input"] + [
    f"Peak {k}: {ft[idx[0]]:.3g}, {fy[idx[1]]:.3g}, {fx[idx[2]]:.3g}"
    for k, (idx, _) in enumerate(peaks, 1)
] + ["Residual"]

ncols = 4
nrows = int(np.ceil(len(images) / ncols))

fig, axes = plt.subplots(
    nrows, ncols, figsize=(4*ncols, 3.5*nrows)
)
axes = np.asarray(axes).ravel()

for ax, img, title in zip(axes, images, titles):
    vmax = np.max(np.abs(img))
    ax.imshow(
        img, cmap="RdBu_r", origin="lower",
        vmin=-vmax if vmax else -1,
        vmax=vmax if vmax else 1,
    )
    ax.set_title(title)
    ax.set_xticks([])
    ax.set_yticks([])

for ax in axes[len(images):]:
    ax.axis("off")

plt.tight_layout()

# ============================================================
# TEMPORAL COEFFICIENTS / ENERGY
# ============================================================
fig, axes = plt.subplots(
    len(components) + 1, 1,
    figsize=(12, 2*(len(components)+1)),
    sharex=True, squeeze=False
)
axes = axes.ravel()

for k, c in enumerate(components):
    axes[k].plot(np.sqrt(np.mean(c**2, axis=(1, 2))))
    axes[k].set_ylabel(f"Peak {k+1}\nRMS")
    axes[k].grid(alpha=0.3)

axes[-1].plot(np.sqrt(np.mean(residual**2, axis=(1, 2))))
axes[-1].set_ylabel("Residual\nRMS")
axes[-1].set_xlabel("Frame")
axes[-1].grid(alpha=0.3)

plt.tight_layout()
plt.show()
