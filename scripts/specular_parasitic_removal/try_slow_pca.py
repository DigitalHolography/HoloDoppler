import numpy as np
from scipy.ndimage import gaussian_filter1d
import matplotlib.pyplot as plt

def slow_pca_filter(video, rank=10, sigma_t=10):
    """
    video: (nt, ny, nx)
    rank: number of PCA modes
    sigma_t: temporal smoothing scale in frames
    """
    nt, ny, nx = video.shape
    X = video.reshape(nt, -1).astype(np.float32)

    # Remove temporal mean
    mean = X.mean(axis=0, keepdims=True)
    Xc = X - mean

    # Temporally smooth each pixel
    Xslow = gaussian_filter1d(
        Xc, sigma=sigma_t, axis=0, mode="reflect"
    )

    # Temporal covariance (256 x 256)
    C = Xslow @ Xslow.T

    eigvals, U = np.linalg.eigh(C)
    U = U[:, -rank:]

    # Rank-k reconstruction of slow component
    L = U @ (U.T @ Xslow)

    # Subtract from ORIGINAL signal
    Xclean = Xc - L

    return Xclean.reshape(nt, ny, nx), U


import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy.signal import welch


def pca_slow_debug(
    data,
    rank=10,
    sigma_t=10,
    shape=(320, 512),
    fps=1.0,
    n_modes_plot=10,
    n_frames_plot=5,
    n_pixels_plot=6,
    plot=True,
):
    """
    Low-pass temporal PCA with extensive diagnostic plots.

    Parameters
    ----------
    data : ndarray
        Input video, shape (nt, ny, nx) OR (nt, npixels).
        Time must be the first dimension.
    rank : int
        Number of PCA components to subtract.
    sigma_t : float
        Gaussian temporal smoothing sigma, in frames.
    shape : tuple
        (ny, nx) for matrix input.
    fps : float
        Acquisition frame rate. Use 1 for cycles/frame.
    plot : bool
        Produce diagnostic figures.

    Returns
    -------
    clean : ndarray
        Cleaned data, same shape as input.
    debug : dict
        Intermediate results and diagnostic quantities.
    """

    data = np.asarray(data)
    original_shape = data.shape

    if data.ndim == 3:
        nt, ny, nx = data.shape
    elif data.ndim == 2:
        nt, npix = data.shape
        ny, nx = shape
        if ny * nx != npix:
            raise ValueError("shape does not match number of pixels")
    else:
        raise ValueError("data must have shape (nt, ny, nx) or (nt, npix)")

    if not 1 <= rank <= nt:
        raise ValueError("rank must be between 1 and nt")
    if sigma_t <= 0:
        raise ValueError("sigma_t must be positive")
    if fps <= 0:
        raise ValueError("fps must be positive")

    # ---------------------------------------------------------
    # 1. Reshape and center
    # ---------------------------------------------------------
    X = data.reshape(nt, -1).astype(np.float64)

    mean = X.mean(axis=0, keepdims=True)
    Xc = X - mean

    # ---------------------------------------------------------
    # 2. Temporal low-pass
    # ---------------------------------------------------------
    Xslow = gaussian_filter1d(
        Xc,
        sigma=sigma_t,
        axis=0,
        mode="reflect",
    )

    # ---------------------------------------------------------
    # 3. PCA of slow video
    # ---------------------------------------------------------
    C = Xslow @ Xslow.T

    eigvals, U = np.linalg.eigh(C)

    idx = np.argsort(eigvals)[::-1]
    eigvals = np.maximum(eigvals[idx], 0)
    U = U[:, idx]

    # Singular values and spatial PCA patterns
    singular_values = np.sqrt(eigvals)
    k = min(rank, np.count_nonzero(
        singular_values > singular_values[0] * 1e-10
    )) if singular_values[0] > 0 else 0

    Uk = U[:, :k]
    sk = singular_values[:k]

    # Spatial modes, normalized to unit L2 norm
    P = (Xslow.T @ Uk) / sk[None, :] if k else np.empty((ny * nx, 0))

    # ---------------------------------------------------------
    # 4. PCA reconstruction / subtraction
    # ---------------------------------------------------------
    # Slow temporal coefficients
    A_slow = Xslow @ P

    # Coefficients projected from original centered video
    A_raw = Xc @ P

    # Low-rank smooth nuisance estimate
    L = A_slow @ P.T

    # Cleaned centered video
    Xclean = Xc - L

    # Full decomposition identity:
    # X = mean + L + Xclean

    # ---------------------------------------------------------
    # 5. Energy diagnostics
    # ---------------------------------------------------------
    total_energy = np.sum(Xc**2)
    slow_energy = np.sum(Xslow**2)
    removed_energy = np.sum(L**2)
    clean_energy = np.sum(Xclean**2)

    explained_ratio = (
        eigvals / eigvals.sum()
        if eigvals.sum() > 0
        else np.zeros_like(eigvals)
    )

    cumulative_ratio = np.cumsum(explained_ratio)

    original_rms_t = np.sqrt(np.mean(Xc**2, axis=1))
    slow_rms_t = np.sqrt(np.mean(Xslow**2, axis=1))
    removed_rms_t = np.sqrt(np.mean(L**2, axis=1))
    clean_rms_t = np.sqrt(np.mean(Xclean**2, axis=1))

    original_std_map = Xc.std(axis=0).reshape(ny, nx)
    removed_std_map = L.std(axis=0).reshape(ny, nx)
    clean_std_map = Xclean.std(axis=0).reshape(ny, nx)

    # Residual identity verification
    decomposition_error = np.linalg.norm(
        Xc - L - Xclean
    ) / (np.linalg.norm(Xc) + 1e-30)

    orthogonality_error = (
        np.linalg.norm(P.T @ P - np.eye(k))
        if k else 0.0
    )

    # ---------------------------------------------------------
    # 6. Debug dictionary
    # ---------------------------------------------------------
    debug = {
        "mean_frame": mean.reshape(ny, nx),
        "slow_video": Xslow.reshape(nt, ny, nx),
        "removed_video": L.reshape(nt, ny, nx),
        "clean_centered": Xclean.reshape(nt, ny, nx),
        "spatial_modes": P.T.reshape(k, ny, nx),
        "temporal_modes": Uk,
        "coefficients_raw": A_raw,
        "coefficients_slow": A_slow,
        "eigenvalues": eigvals,
        "singular_values": singular_values,
        "explained_ratio": explained_ratio,
        "cumulative_ratio": cumulative_ratio,
        "original_rms_t": original_rms_t,
        "slow_rms_t": slow_rms_t,
        "removed_rms_t": removed_rms_t,
        "clean_rms_t": clean_rms_t,
        "original_std_map": original_std_map,
        "removed_std_map": removed_std_map,
        "clean_std_map": clean_std_map,
        "energy": {
            "original": total_energy,
            "slow": slow_energy,
            "removed": removed_energy,
            "clean": clean_energy,
        },
        "decomposition_error": decomposition_error,
        "orthogonality_error": orthogonality_error,
        "rank_effective": k,
        "sigma_t": sigma_t,
    }

    # ---------------------------------------------------------
    # 7. Console diagnostics
    # ---------------------------------------------------------
    print("\n========== SLOW PCA DEBUG ==========")
    print(f"Input shape            : {original_shape}")
    print(f"Video dimensions       : {nt} x {ny} x {nx}")
    print(f"Requested rank         : {rank}")
    print(f"Effective rank         : {k}")
    print(f"Temporal sigma         : {sigma_t} frames")
    print(f"Approx. -3 dB cutoff   : {0.1325/sigma_t:.5f} cycles/frame")
    print(f"Slow PCA variance      : {100*cumulative_ratio[k-1]:.2f}%"
          if k else "Slow PCA variance      : 0%")
    print(f"Removed/original energy: {100*removed_energy/(total_energy+1e-30):.2f}%")
    print(f"Clean/original energy  : {100*clean_energy/(total_energy+1e-30):.2f}%")
    print(f"Decomposition error    : {decomposition_error:.3e}")
    print(f"Spatial orthogonality  : {orthogonality_error:.3e}")

    # ---------------------------------------------------------
    # 8. Diagnostic plots
    # ---------------------------------------------------------
    if plot:

        # Figure 1: Original / slow / removed / clean frames
        frame_indices = np.linspace(
            0, nt - 1, min(n_frames_plot, nt), dtype=int
        )

        fig, axes = plt.subplots(
            len(frame_indices), 4,
            figsize=(16, 3.4 * len(frame_indices)),
            squeeze=False,
            constrained_layout=True,
        )

        panels = [
            ("Original centered", Xc),
            ("Temporal low-pass", Xslow),
            ("Removed nuisance", L),
            ("Cleaned", Xclean),
        ]

        for j, (name, arr) in enumerate(panels):
            lim = np.percentile(np.abs(arr), 99)
            lim = max(lim, 1e-12)

            for i, t in enumerate(frame_indices):
                ax = axes[i, j]
                im = ax.imshow(
                    arr[t].reshape(ny, nx),
                    cmap="RdBu_r",
                    vmin=-lim, vmax=lim,
                )
                ax.set_title(f"{name} / frame {t}")
                ax.axis("off")
                fig.colorbar(im, ax=ax, fraction=0.035)

        fig.suptitle("Frame-by-frame PCA subtraction", fontsize=15)
        plt.show()

        # Figure 2: PCA eigenvalues
        fig, axes = plt.subplots(1, 2, figsize=(13, 4))

        axes[0].semilogy(
            np.arange(1, nt + 1),
            np.maximum(eigvals, 1e-30),
        )
        axes[0].axvline(k, color="red", ls="--")
        axes[0].set_xlabel("Mode index")
        axes[0].set_ylabel("Eigenvalue")
        axes[0].set_title("Slow PCA eigenvalue spectrum")
        axes[0].grid(alpha=0.3)

        axes[1].plot(
            np.arange(1, nt + 1),
            cumulative_ratio * 100,
        )
        axes[1].axvline(k, color="red", ls="--")
        axes[1].set_xlabel("Number of modes")
        axes[1].set_ylabel("Cumulative variance (%)")
        axes[1].set_title("Explained slow variance")
        axes[1].grid(alpha=0.3)

        plt.tight_layout()
        plt.show()

        # Figure 3: Spatial PCA patterns
        m = min(n_modes_plot, k)

        if m:
            cols = min(5, m)
            rows = int(np.ceil(m / cols))

            fig, axes = plt.subplots(
                rows, cols,
                figsize=(3.5 * cols, 3 * rows),
                squeeze=False,
            )

            for i, ax in enumerate(axes.flat):
                if i >= m:
                    ax.axis("off")
                    continue

                mode = P[:, i].reshape(ny, nx)
                lim = np.max(np.abs(mode))

                ax.imshow(
                    mode, cmap="RdBu_r",
                    vmin=-lim, vmax=lim,
                )
                ax.set_title(
                    f"Mode {i+1}: {explained_ratio[i]*100:.2f}%"
                )
                ax.axis("off")

            fig.suptitle("Spatial PCA modes")
            plt.tight_layout()
            plt.show()

        # Figure 4: Temporal coefficients
        if m:
            fig, axes = plt.subplots(
                m, 1,
                figsize=(13, 2.1 * m),
                sharex=True,
                squeeze=False,
            )

            for i in range(m):
                ax = axes[i, 0]
                ax.plot(A_raw[:, i], alpha=0.45,
                        label="Raw projection")
                ax.plot(A_slow[:, i], lw=2,
                        label="Slow coefficient")
                ax.set_ylabel(f"PC {i+1}")
                ax.grid(alpha=0.25)
                if i == 0:
                    ax.legend()

            axes[-1, 0].set_xlabel("Frame")
            fig.suptitle("Temporal amplitudes of spatial modes")
            plt.tight_layout()
            plt.show()

        # Figure 5: Frequency spectra of PCA amplitudes
        if m:
            fig, axes = plt.subplots(
                1, 2, figsize=(14, 5)
            )

            nperseg = min(128, nt)

            for i in range(m):
                f, psd_raw = welch(
                    A_raw[:, i],
                    fs=fps,
                    nperseg=nperseg,
                )
                _, psd_slow = welch(
                    A_slow[:, i],
                    fs=fps,
                    nperseg=nperseg,
                )
                axes[0].semilogy(
                    f, psd_raw + 1e-30,
                    alpha=0.65,
                    label=f"PC {i+1}",
                )
                axes[1].semilogy(
                    f, psd_slow + 1e-30,
                    alpha=0.65,
                    label=f"PC {i+1}",
                )

            axes[0].set_title("Raw temporal coefficient PSD")
            axes[1].set_title("Slow temporal coefficient PSD")

            for ax in axes:
                ax.set_xlabel("Frequency (Hz)" if fps != 1 else "Cycles/frame")
                ax.set_ylabel("PSD")
                ax.grid(alpha=0.3)

            axes[0].legend(ncol=2, fontsize=8)
            plt.tight_layout()
            plt.show()

        # Figure 6: Variability maps
        fig, axes = plt.subplots(1, 3, figsize=(16, 4))

        maps = [
            original_std_map,
            removed_std_map,
            clean_std_map,
        ]
        titles = [
            "Original temporal std",
            "Removed temporal std",
            "Clean temporal std",
        ]

        vmax = np.percentile(original_std_map, 99)

        for ax, arr, title in zip(axes, maps, titles):
            im = ax.imshow(arr, vmin=0, vmax=max(vmax, 1e-12))
            ax.set_title(title)
            ax.axis("off")
            fig.colorbar(im, ax=ax, fraction=0.035)

        plt.tight_layout()
        plt.show()

        # Figure 7: Frame RMS
        plt.figure(figsize=(13, 5))
        plt.plot(original_rms_t, label="Original")
        plt.plot(slow_rms_t, label="Low-pass")
        plt.plot(removed_rms_t, label="Removed")
        plt.plot(clean_rms_t, label="Clean")
        plt.xlabel("Frame")
        plt.ylabel("Spatial RMS")
        plt.title("RMS versus time")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.show()

        # Figure 8: Selected pixel traces
        rng = np.random.default_rng(42)
        pix_idx = rng.choice(
            X.shape[1],
            size=min(n_pixels_plot, X.shape[1]),
            replace=False,
        )

        fig, axes = plt.subplots(
            len(pix_idx), 1,
            figsize=(13, 2.2 * len(pix_idx)),
            sharex=True,
            squeeze=False,
        )

        for i, p in enumerate(pix_idx):
            ax = axes[i, 0]
            ax.plot(Xc[:, p], label="Original", alpha=0.7)
            ax.plot(L[:, p], label="Removed", lw=2)
            ax.plot(Xclean[:, p], label="Clean", alpha=0.7)
            ax.set_ylabel(f"({p//nx},{p%nx})")
            ax.grid(alpha=0.25)
            if i == 0:
                ax.legend()

        axes[-1, 0].set_xlabel("Frame")
        fig.suptitle("Individual pixel time traces")
        plt.tight_layout()
        plt.show()

        # Figure 9: Space-time images
        y = ny // 2
        sl = slice(y * nx, (y + 1) * nx)

        fig, axes = plt.subplots(1, 3, figsize=(16, 5))

        spacetime = [
            Xc[:, sl],
            L[:, sl],
            Xclean[:, sl],
        ]

        lim = np.percentile(np.abs(Xc[:, sl]), 99)
        lim = max(lim, 1e-12)

        for ax, arr, title in zip(
            axes, spacetime, ["Original", "Removed", "Clean"]
        ):
            ax.imshow(
                arr,
                aspect="auto",
                origin="lower",
                cmap="RdBu_r",
                vmin=-lim,
                vmax=lim,
            )
            ax.set_title(f"{title}: y={y}")
            ax.set_xlabel("x")
            ax.set_ylabel("Frame")

        plt.tight_layout()
        plt.show()

        # Figure 10: Temporal power spectra of full videos
        # FFT over time, then spatially average power
        freq = np.fft.rfftfreq(nt, d=1/fps)

        power_original = np.mean(
            np.abs(np.fft.rfft(Xc, axis=0))**2, axis=1
        )
        power_removed = np.mean(
            np.abs(np.fft.rfft(L, axis=0))**2, axis=1
        )
        power_clean = np.mean(
            np.abs(np.fft.rfft(Xclean, axis=0))**2, axis=1
        )

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        axes[0].semilogy(
            freq, power_original + 1e-30, label="Original"
        )
        axes[0].semilogy(
            freq, power_removed + 1e-30, label="Removed"
        )
        axes[0].semilogy(
            freq, power_clean + 1e-30, label="Clean"
        )
        axes[0].set_xlabel("Frequency (Hz)" if fps != 1 else "Cycles/frame")
        axes[0].set_ylabel("Spatially averaged temporal power")
        axes[0].set_title("Temporal power spectra")
        axes[0].legend()
        axes[0].grid(alpha=0.3)

        axes[1].plot(
            freq,
            power_removed / (power_original + 1e-30),
        )
        axes[1].set_xlabel("Frequency (Hz)" if fps != 1 else "Cycles/frame")
        axes[1].set_ylabel("Removed power / Original power")
        axes[1].set_title("Relative nuisance power spectrum")
        axes[1].grid(alpha=0.3)

        plt.tight_layout()
        plt.show()

    return Xclean.reshape(original_shape), debug



DATA_PATH = r"Y:\260113_IOP_BP\260113_FIY0713.holo"

from holodoppler.file_reader import FileReaderFactory

reader = FileReaderFactory.create(DATA_PATH)

data = reader.read_frames(0,512).copy().astype(np.float64)

nt, ny, nx = data.shape
n_modes = 10
sigma_t=100

dataclean= pca_slow_debug(data, rank=n_modes, sigma_t=sigma_t)
