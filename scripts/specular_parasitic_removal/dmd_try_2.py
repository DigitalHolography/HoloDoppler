import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# PARAMETERS
# ============================================================

rank = 50          # SVD truncation rank
n_modes_plot = 8   # number of DMD modes to display

dt = 1.0           # time between frames

DATA_PATH = r"/data/Lourds/langevin/data/AUZOS.holo"

from holodoppler.file_reader import FileReaderFactory

reader = FileReaderFactory.create(DATA_PATH)

data1 = reader.read_frames(0,512).copy().astype(np.float64)
data2 = reader.read_frames(512,512).copy().astype(np.float64)

# ============================================================
# PREPARE SNAPSHOT MATRICES
# ============================================================

nt, ny, nx = data1.shape

X1 = data1.reshape(nt, ny*nx).T
X2 = data2.reshape(nt, ny*nx).T


print("X1 shape:", X1.shape)
print("X2 shape:", X2.shape)


# ============================================================
# SVD OF X1
# ============================================================

U, S, Vh = np.linalg.svd(
    X1,
    full_matrices=False
)


# truncate
U_r = U[:, :rank]
S_r = S[:rank]
V_r = Vh.conj().T[:, :rank]


# ============================================================
# LOW DIMENSIONAL DMD OPERATOR
# ============================================================

Atilde = (
    U_r.conj().T
    @ X2
    @ V_r
    @ np.diag(1/S_r)
)


# ============================================================
# EIGEN DECOMPOSITION
# ============================================================

eigvals, W = np.linalg.eig(Atilde)


# DMD modes
Phi = (
    X2
    @ V_r
    @ np.diag(1/S_r)
    @ W
)


# ============================================================
# SORT MODES
# ============================================================

# amplitude at initial condition

x0 = X1[:,0]

b = np.linalg.lstsq(
    Phi,
    x0,
    rcond=None
)[0]


idx = np.argsort(
    np.abs(b)
)[::-1]


eigvals = eigvals[idx]
Phi = Phi[:,idx]
b = b[idx]


# ============================================================
# DMD FREQUENCIES AND GROWTH RATES
# ============================================================

omega = np.log(eigvals)/dt

frequency = omega.imag/(2*np.pi)

growth = omega.real



# ============================================================
# FIGURE 1
# SVD singular values
# ============================================================

plt.figure(figsize=(7,4))

plt.semilogy(
    S,
    'o-'
)

plt.xlabel("SVD mode")
plt.ylabel("Singular value")
plt.title("SVD spectrum used for DMD")
plt.grid(alpha=.3)




# ============================================================
# FIGURE 2
# DMD eigenvalues
# ============================================================

plt.figure(figsize=(6,6))

circle = np.exp(
    1j*np.linspace(0,2*np.pi,300)
)

plt.plot(
    circle.real,
    circle.imag,
    '--'
)

plt.scatter(
    eigvals.real,
    eigvals.imag,
    s=80
)


plt.xlabel("Real")
plt.ylabel("Imaginary")

plt.axis("equal")
plt.grid(alpha=.3)

plt.title(
    "DMD eigenvalues"
)




# ============================================================
# FIGURE 3
# Frequency and growth rate
# ============================================================

fig,ax = plt.subplots(
    1,2,
    figsize=(12,4)
)


ax[0].stem(
    frequency[:n_modes_plot]
)

ax[0].set_xlabel("Mode")
ax[0].set_ylabel("Frequency (Hz)")
ax[0].set_title("DMD frequencies")


ax[1].stem(
    growth[:n_modes_plot]
)

ax[1].set_xlabel("Mode")
ax[1].set_ylabel("Growth rate")
ax[1].set_title("DMD growth/decay")

plt.tight_layout()



# ============================================================
# FIGURE 4
# DMD SPATIAL MODES
# ============================================================

fig,axes = plt.subplots(
    2,
    int(np.ceil(n_modes_plot/2)),
    figsize=(14,7)
)


axes = axes.ravel()


for i in range(n_modes_plot):

    mode = Phi[:,i].real.reshape(ny,nx)

    vmax=np.max(abs(mode))

    im=axes[i].imshow(
        mode,
        cmap="RdBu_r",
        vmin=-vmax,
        vmax=vmax,
        origin="lower"
    )


    axes[i].set_title(
        f"Mode {i+1}\n"
        f"f={frequency[i]:.3f} Hz"
    )

    axes[i].set_xticks([])
    axes[i].set_yticks([])

    plt.colorbar(
        im,
        ax=axes[i],
        shrink=.8
    )


for i in range(n_modes_plot,len(axes)):
    axes[i].axis("off")


plt.tight_layout()



# ============================================================
# FIGURE 5
# MODE AMPLITUDES
# ============================================================

plt.figure(figsize=(7,4))


plt.stem(
    np.abs(b[:n_modes_plot])
)

plt.xlabel("DMD mode")
plt.ylabel("|Amplitude|")

plt.title(
    "Initial DMD amplitudes"
)

plt.grid(alpha=.3)




# ============================================================
# FIGURE 6
# DMD modal time signals
# ============================================================

time = np.arange(nt)*dt


fig,axes = plt.subplots(
    n_modes_plot,
    1,
    figsize=(12,2*n_modes_plot),
    sharex=True
)


for i in range(n_modes_plot):

    signal = (
        b[i]
        *
        eigvals[i]**np.arange(nt)
    )


    axes[i].plot(
        time,
        signal.real
    )


    axes[i].set_ylabel(
        f"M{i+1}"
    )

    axes[i].grid(alpha=.3)


axes[-1].set_xlabel("Time")

fig.suptitle(
    "DMD temporal evolution"
)

plt.tight_layout()




# ============================================================
# FIGURE 7
# RECONSTRUCTION
# ============================================================

modes_used = n_modes_plot


time_dynamics = np.zeros(
    (modes_used,nt),
    dtype=complex
)


for i in range(modes_used):

    time_dynamics[i,:] = (
        b[i]
        *
        eigvals[i]**np.arange(nt)
    )


X_dmd = (
    Phi[:,:modes_used]
    @ time_dynamics
)


frame=50


original = X1[:,frame].reshape(ny,nx)

reconstructed = (
    X_dmd[:,frame]
    .real
    .reshape(ny,nx)
)


error = original-reconstructed


fig,ax=plt.subplots(
    1,3,
    figsize=(15,5)
)


ax[0].imshow(
    original,
    cmap="viridis",
    origin="lower"
)

ax[0].set_title("Original")


ax[1].imshow(
    reconstructed,
    cmap="viridis",
    origin="lower"
)

ax[1].set_title(
    f"DMD reconstruction\n{modes_used} modes"
)


v=np.max(abs(error))

ax[2].imshow(
    error,
    cmap="RdBu_r",
    vmin=-v,
    vmax=v,
    origin="lower"
)

ax[2].set_title("Residual")


for a in ax:
    a.set_xticks([])
    a.set_yticks([])


plt.tight_layout()
plt.show()