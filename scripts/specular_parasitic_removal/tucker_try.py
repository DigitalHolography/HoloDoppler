
import numpy as np
import matplotlib.pyplot as plt
import tensorly as tl
from tensorly.decomposition import tucker
from holodoppler.file_reader import FileReaderFactory

# ============================================================
# PARAMETERS
# ============================================================
DATA_PATH = r"Y:\260113_IOP_BP\260113_FIY0713.holo"

n_frames = 512
ranks = (6, 32, 32)  # (time, y, x)
frame = 100

# ============================================================
# LOAD DATA
# ============================================================
reader = FileReaderFactory.create(DATA_PATH)
M = reader.read_frames(0, n_frames).astype(np.float32)

nt, ny, nx = M.shape
mean_field = M.mean(axis=0)
X = M - mean_field[None, :, :]

print("Input shape:", X.shape)

# ============================================================
# TUCKER DECOMPOSITION
# X ~ core x1 U_t x2 U_y x3 U_x
# ============================================================
core, factors = tucker(
    tl.tensor(X),
    rank=ranks,
    init="svd",
    n_iter_max=100,
    tol=1e-5,
    verbose=True,
)

Ut, Uy, Ux = [np.asarray(f) for f in factors]
core = np.asarray(core)

print("Core shape:", core.shape)
print("Temporal basis:", Ut.shape)
print("Y basis:", Uy.shape)
print("X basis:", Ux.shape)

# ============================================================
# RECONSTRUCTION
# ============================================================
Xr = np.asarray(
    tl.tucker_to_tensor((core, factors))
)
residual = X - Xr

rel_error = np.linalg.norm(residual) / max(np.linalg.norm(X), 1e-30)
print(f"Relative reconstruction error: {rel_error:.5f}")

# ============================================================
# FIGURE 1: TEMPORAL BASIS
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(13, 6), sharex=True)

for k, ax in enumerate(axes.flat):
    ax.plot(Ut[:, k])
    ax.set_title(f"Temporal basis {k+1}")
    ax.grid(alpha=0.3)

plt.tight_layout()

# ============================================================
# FIGURE 2: SPATIAL BASIS PATTERNS
# ============================================================
fig, axes = plt.subplots(4, 4, figsize=(13, 11))

for k, ax in enumerate(axes.flat):
    if k >= Uy.shape[1] or k >= Ux.shape[1]:
        ax.axis("off")
        continue

    # Display paired spatial basis vectors as an example.
    # These are NOT full Tucker components.
    pattern = np.outer(Uy[:, k], Ux[:, k])
    vmax = np.max(np.abs(pattern))

    ax.imshow(
        pattern, cmap="RdBu_r", origin="lower",
        vmin=-vmax if vmax else -1,
        vmax=vmax if vmax else 1,
    )
    ax.set_title(f"Spatial basis pair {k+1}")
    ax.set_xticks([])
    ax.set_yticks([])

plt.tight_layout()

# ============================================================
# FIGURE 3: CORE TENSOR ENERGY
# ============================================================
# Energy associated with each temporal core slice.
energy_t = np.sum(core**2, axis=(1, 2))
energy_t /= max(energy_t.sum(), 1e-30)

plt.figure(figsize=(8, 4))
plt.plot(np.arange(len(energy_t)) + 1, 100 * energy_t, "o-")
plt.xlabel("Temporal core index")
plt.ylabel("Core energy (%)")
plt.title("Tucker temporal-index energy")
plt.grid(alpha=0.3)
plt.tight_layout()

# ============================================================
# FIGURE 4: RECONSTRUCTION AND RESIDUAL
# ============================================================
frame = min(frame, nt - 1)

images = [X[frame], Xr[frame], residual[frame]]
titles = ["Centered input", "Tucker reconstruction", "Residual"]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for ax, img, title in zip(axes, images, titles):
    vmax = max(np.percentile(np.abs(img), 99.5), 1e-12)
    ax.imshow(
        img, cmap="RdBu_r", origin="lower",
        vmin=-vmax, vmax=vmax,
    )
    ax.set_title(title)
    ax.set_xticks([])
    ax.set_yticks([])

plt.tight_layout()
plt.show()
