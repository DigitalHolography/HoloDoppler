import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# SVD / POD decomposition of a data cube
#
# Input:
#     data.shape = (nt, ny, nx)
#
# Example:
#     data.shape = (320,512,512)
#
# Returns:
#     U      : spatial modes
#     S      : singular values
#     Vt     : temporal coefficients
# ============================================================

# ------------------------------------------------------------
# PARAMETERS
# ------------------------------------------------------------
center = True          # subtract temporal mean
n_modes = 6            # number of modes to display

DATA_PATH = r"/data/Lourds/langevin/data/AUZOS.holo"

from holodoppler.file_reader import FileReaderFactory

reader = FileReaderFactory.create(DATA_PATH)

data = reader.read_frames(0,512).copy().astype(np.float64)

# ------------------------------------------------------------
# Build snapshot matrix
# ------------------------------------------------------------
nt, ny, nx = data.shape

X = data.reshape(nt, ny * nx).T      # (pixels, time)

if center:
    mean_field = X.mean(axis=1, keepdims=True)
    X -= mean_field

print("Snapshot matrix :", X.shape)

# ------------------------------------------------------------
# Compute SVD
# ------------------------------------------------------------
U, S, Vt = np.linalg.svd(X, full_matrices=False)

print("Spatial modes :", U.shape)
print("Singular values :", S.shape)
print("Temporal coefficients :", Vt.shape)

# ============================================================
# Explained variance
# ============================================================

energy = S**2
energy_ratio = energy / energy.sum()
cum_energy = np.cumsum(energy_ratio)

# ============================================================
# FIGURE 1 : Singular values
# ============================================================

fig, ax = plt.subplots(figsize=(7,4))

ax.semilogy(S, 'o-', lw=2)
ax.set_xlabel("Mode")
ax.set_ylabel("Singular value")
ax.set_title("Singular Value Spectrum")
ax.grid(alpha=.3)

plt.tight_layout()

# ============================================================
# FIGURE 2 : Explained variance
# ============================================================

fig, ax = plt.subplots(figsize=(7,4))

ax.plot(100*energy_ratio, 'o-', lw=2, label='Individual')
ax.plot(100*cum_energy, 's-', lw=2, label='Cumulative')

ax.set_xlabel("Mode")
ax.set_ylabel("Explained variance (%)")
ax.set_ylim(0,105)
ax.grid(alpha=.3)
ax.legend()

plt.tight_layout()

# ============================================================
# FIGURE 3 : Spatial modes
# ============================================================

fig, axes = plt.subplots(
    2,
    int(np.ceil(n_modes/2)),
    figsize=(14,6)
)

axes = axes.ravel()

for k in range(n_modes):

    mode = U[:,k].reshape(ny,nx)

    vmax = np.max(np.abs(mode))

    im = axes[k].imshow(
        mode,
        cmap='RdBu_r',
        vmin=-vmax,
        vmax=vmax,
        origin='lower'
    )

    axes[k].set_title(
        f"Mode {k+1}\n"
        f"{100*energy_ratio[k]:.2f}% energy"
    )

    axes[k].set_xticks([])
    axes[k].set_yticks([])

    plt.colorbar(im, ax=axes[k], shrink=.8)

for k in range(n_modes, len(axes)):
    axes[k].axis("off")

plt.tight_layout()

# ============================================================
# FIGURE 4 : Temporal coefficients
# ============================================================

fig, axes = plt.subplots(
    n_modes,
    1,
    figsize=(12,2*n_modes),
    sharex=True
)

time = np.arange(nt)

for k in range(n_modes):

    coeff = S[k] * Vt[k]

    axes[k].plot(time, coeff, lw=2)

    axes[k].set_ylabel(f"Mode {k+1}")
    axes[k].grid(alpha=.3)

axes[-1].set_xlabel("Frame")
fig.suptitle("Temporal coefficients", fontsize=16)

plt.tight_layout()

# ============================================================
# FIGURE 5 : Reconstruction example
# ============================================================

r = 5          # number of retained modes

Xr = U[:,:r] @ np.diag(S[:r]) @ Vt[:r]

frame = 100

original = X[:,frame].reshape(ny,nx)
recon = Xr[:,frame].reshape(ny,nx)
residual = original - recon

fig, ax = plt.subplots(1,3,figsize=(15,5))

vmin = original.min()
vmax = original.max()

ax[0].imshow(original,
             cmap='viridis',
             origin='lower',
             vmin=vmin,
             vmax=vmax)

ax[0].set_title("Original")

ax[1].imshow(recon,
             cmap='viridis',
             origin='lower',
             vmin=vmin,
             vmax=vmax)

ax[1].set_title(f"Reconstruction ({r} modes)")

m = np.max(np.abs(residual))

ax[2].imshow(residual,
             cmap='RdBu_r',
             origin='lower',
             vmin=-m,
             vmax=m)

ax[2].set_title("Residual")

for a in ax:
    a.set_xticks([])
    a.set_yticks([])

plt.tight_layout()

plt.show()