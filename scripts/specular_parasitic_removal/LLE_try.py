import numpy as np
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from sklearn.manifold import LocallyLinearEmbedding
from sklearn.cluster import KMeans
from matplotlib.widgets import Slider, Button
from holodoppler.file_reader import FileReaderFactory

# ==================================================
# SETTINGS
# ==================================================
DATA_PATH = r"Y:\260113_IOP_BP\260113_FIY0713.holo"

N_FRAMES = 256
SPATIAL_STRIDE = 4
N_NEIGHBORS = 20
N_COMPONENTS = 2
N_CLUSTERS = 4
NORMALIZE_TRACES = True

# ==================================================
# LOAD DATA: M(time, y, x)
# ==================================================
reader = FileReaderFactory.create(DATA_PATH)
M = reader.read_frames(0, N_FRAMES).astype(np.float32)

nt, ny, nx = M.shape
print("Data shape:", M.shape)

# Remove the static spatial background
X = M - M.mean(axis=0, keepdims=True)

# Subsample spatially to reduce computational cost
Xs = X[:, ::SPATIAL_STRIDE, ::SPATIAL_STRIDE]
_, h, w = Xs.shape

# Each pixel becomes one sample with its temporal trace as features
P = Xs.transpose(1, 2, 0).reshape(-1, nt)

# Normalize each trace to focus on its temporal shape
if NORMALIZE_TRACES:
    scale = np.sqrt(np.mean(P**2, axis=1, keepdims=True))
    P = P / np.maximum(scale, 1e-8)

# Remove constant/invalid samples
valid = np.isfinite(P).all(axis=1) & (np.std(P, axis=1) > 1e-8)
P_valid = P[valid]

if len(P_valid) <= N_NEIGHBORS:
    raise ValueError("Too few valid pixels for the selected n_neighbors.")

# ==================================================
# PCA PRE-REDUCTION -> LLE
# ==================================================
n_pca = min(20, P_valid.shape[1], P_valid.shape[0] - 1)
P_pca = PCA(n_components=n_pca).fit_transform(P_valid)

lle = LocallyLinearEmbedding(
    n_neighbors=N_NEIGHBORS,
    n_components=N_COMPONENTS,
    method="standard",
    eigen_solver="auto",
    random_state=0,
    n_jobs=-1,
)

embedding_valid = lle.fit_transform(P_pca)

print("LLE reconstruction error:", lle.reconstruction_error_)

# ==================================================
# CLUSTER IN THE LLE EMBEDDING
# ==================================================
clusterer = KMeans(
    n_clusters=N_CLUSTERS,
    n_init=10,
    random_state=0,
)

labels_valid = clusterer.fit_predict(embedding_valid)

# Restore labels to the subsampled spatial grid; -1 = invalid
labels = np.full(h * w, -1, dtype=int)
labels[valid] = labels_valid
labels = labels.reshape(h, w)

embedding = np.full((h * w, N_COMPONENTS), np.nan)
embedding[valid] = embedding_valid
embedding = embedding.reshape(h, w, N_COMPONENTS)

# ==================================================
# BUILD FULL-RESOLUTION MASKS AND MASKED STACKS
# ==================================================
# Nearest-neighbor block expansion of the subsampled labels
labels_full = np.repeat(
    np.repeat(labels, SPATIAL_STRIDE, axis=0),
    SPATIAL_STRIDE, axis=1
)[:ny, :nx]

# Each masked stack retains original values only in its cluster.
# This is spatial selection, NOT an additive source decomposition.
masked_stacks = []
for k in range(N_CLUSTERS):
    mask = labels_full == k
    masked = np.where(mask[None, :, :], X, np.nan)
    masked_stacks.append(masked)

# ==================================================
# STATIC DIAGNOSTIC PLOTS
# ==================================================
fig, ax = plt.subplots(2, 3, figsize=(15, 9))

im = ax[0, 0].imshow(embedding[..., 0], cmap="RdBu_r")
ax[0, 0].set_title("LLE coordinate 1")
plt.colorbar(im, ax=ax[0, 0])

im = ax[0, 1].imshow(embedding[..., 1], cmap="RdBu_r")
ax[0, 1].set_title("LLE coordinate 2")
plt.colorbar(im, ax=ax[0, 1])

im = ax[0, 2].imshow(labels, cmap="tab10", vmin=0,
                      vmax=N_CLUSTERS - 1)
ax[0, 2].set_title("K-means clusters")
plt.colorbar(im, ax=ax[0, 2], ticks=range(N_CLUSTERS))

sc = ax[1, 0].scatter(
    embedding_valid[:, 0],
    embedding_valid[:, 1],
    c=labels_valid,
    s=4,
    cmap="tab10",
)
ax[1, 0].set_title("LLE embedding + clusters")
ax[1, 0].set_xlabel("LLE coordinate 1")
ax[1, 0].set_ylabel("LLE coordinate 2")

im = ax[1, 1].imshow(X[nt // 2], cmap="RdBu_r")
ax[1, 1].set_title(f"Original centered frame {nt // 2}")
plt.colorbar(im, ax=ax[1, 1])

im = ax[1, 2].imshow(
    masked_stacks[0][nt // 2], cmap="RdBu_r"
)
ax[1, 2].set_title("Cluster 0: masked frame")
plt.colorbar(im, ax=ax[1, 2])

for a in ax.flat:
    if a not in (ax[1, 0],):
        a.set_xticks([])
        a.set_yticks([])

plt.tight_layout()
plt.show()

# ==================================================
# INTERACTIVE VIEWER: FRAME + CLUSTER
# ==================================================
fig, ax = plt.subplots(figsize=(8, 7))
plt.subplots_adjust(bottom=0.24)

initial_frame = 0
initial_cluster = 0

shown = np.where(
    labels_full == initial_cluster,
    X[initial_frame],
    np.nan,
)

vmax = np.nanpercentile(np.abs(X), 99.5)
im = ax.imshow(shown, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
ax.set_title("Cluster 0, frame 0")
ax.set_axis_off()

ax_frame = fig.add_axes([0.18, 0.12, 0.64, 0.03])
frame_slider = Slider(
    ax_frame, "Frame", 0, nt - 1,
    valinit=initial_frame, valstep=1
)

ax_cluster = fig.add_axes([0.18, 0.07, 0.64, 0.03])
cluster_slider = Slider(
    ax_cluster, "Cluster", 0, N_CLUSTERS - 1,
    valinit=initial_cluster, valstep=1
)

def update(_):
    t = int(frame_slider.val)
    k = int(cluster_slider.val)
    frame = np.where(labels_full == k, X[t], np.nan)
    im.set_data(frame)
    ax.set_title(f"Cluster {k}, frame {t}")
    fig.canvas.draw_idle()

frame_slider.on_changed(update)
cluster_slider.on_changed(update)

plt.show()

# ==================================================
# SAVE RESULTS
# ==================================================
np.savez_compressed(
    "lle_results.npz",
    embedding=embedding,
    labels=labels,
    labels_full=labels_full,
    cluster_centers=clusterer.cluster_centers_,
)

for k, stack in enumerate(masked_stacks):
    np.save(f"lle_cluster_{k}.npy", stack)

print("Saved LLE embedding, cluster labels, and masked stacks.")