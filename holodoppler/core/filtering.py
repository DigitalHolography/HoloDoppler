"""
Filtering operations: SVD, frequency filtering
"""

from functools import cache

from .image_utils import elliptical_mask


def filter_2d(xp, fft, frames, filter2d_low):
    _, ny, nx = frames.shape

    F = fft.fft2(frames)

    mask = elliptical_mask(xp, ny, nx, filter2d_low)

    # import matplotlib.pyplot as plt
    # plt.imshow(fft.fftshift(~mask).get())
    # plt.show()

    F = F * fft.fftshift(~mask)

    F = fft.ifft2(F)

    return F




def svd_filter(
    xp,
    linalg,
    H,
    svd_threshold,
    filter_mode="number_of_values",
    remove_dc=False,
    diagnostic=None,
    block_size_mib=8,
):
    """SVD clutter filtering using temporal covariance eigendecomposition.

    Parameters
    ----------
    H : array
        Complex data of shape (Nt, Ny, Nx).
    svd_threshold : int or float
        Number of leading modes to remove, or eigenvalue threshold.
        Negative values disable filtering.
    filter_mode : str
        "number_of_values" or "amplitude_threshold".
    remove_dc : bool
        Subtract the temporal mean before filtering.
    diagnostic : dict, optional
        Dictionary populated with intermediate results when provided.

    block_size_mib : positive float or None, optional
        Target size in MiB for each pixel-block work array, not total memory.
        Larger blocks can improve throughput at the cost of RAM/VRAM.
        None processes all pixels in one block without a workspace limit.

    Returns
    -------
    H_filtered : array
        Filtered data with the same shape as H.
    """
    if svd_threshold < 0:
        return H

    filtered = xp.empty(H.shape, dtype=H.dtype)
    _svd_filter_matrix(
        xp, linalg, H.reshape(H.shape[0], -1) if H.flags.c_contiguous else H,
        filtered.reshape(H.shape[0], -1), svd_threshold,
        filter_mode, remove_dc, diagnostic, H.shape, block_size_mib=block_size_mib,
    )
    return filtered


def _svd_filter_matrix(xp, linalg, data, output, threshold, mode,
                       remove_dc=False, diagnostic=None, shape=None, regularization=0,
                       block_size_mib=8):
    """Filter time-first data into a time-by-pixel output without changing input."""
    nt, pixels = output.shape
    block_size = (max(1, pixels) if block_size_mib is None else
                  max(1, int(block_size_mib * 1024**2) // (nt * data.dtype.itemsize)))
    cov = xp.zeros((nt, nt), dtype=data.dtype)
    dc = xp.empty(pixels, dtype=data.dtype) if remove_dc and diagnostic is not None else None

    # Reuse the final output as centered storage. Time-major blocks follow the
    # main pipeline's native layout and avoid a large strided transpose copy.
    for start in range(0, pixels, block_size):
        stop = min(start + block_size, pixels)
        if data.ndim == 2:
            block = data[:, start:stop].copy()
        else:
            # A tiled subaperture is a strided view of the original hologram.
            # Gather only this pixel block, never reshape-copy the whole view.
            indices = xp.arange(start, stop)
            block = data[:, indices // data.shape[2], indices % data.shape[2]]
        if remove_dc:
            mean = xp.mean(block, axis=0)
            block -= mean[None, :]
            if dc is not None:
                dc[start:stop] = mean
        cov += block.conj() @ block.T
        output[:, start:stop] = block
    del block
    if regularization:
        cov[xp.diag_indices(nt)] += regularization
    values, vectors = linalg.eigh(cov)
    values, vectors = values[::-1], vectors[:, ::-1]
    if mode == "number_of_values":
        selected = vectors[:, :min(int(threshold), nt)]
    elif mode == "amplitude_threshold":
        selected = vectors[:, values > threshold]
    else:
        raise ValueError(f"Unknown filter_mode: {mode}")

    removed_features = (xp.empty((pixels, selected.shape[1]), dtype=data.dtype)
                        if diagnostic is not None else None)
    conjugate = selected.conj()
    for start in range(0, pixels, block_size):
        stop = min(start + block_size, pixels)
        block = output[:, start:stop]
        if selected.shape[1]:
            removed = selected.T @ block
            block -= conjugate @ removed
            if removed_features is not None:
                removed_features[start:stop] = removed.T
        elif removed_features is not None:
            removed_features[start:stop] = 0

    if diagnostic is not None:
        diagnostic.update({
            "removed_features": removed_features.reshape(*shape[1:], -1),
            "kept_data": output.reshape(shape),
            "eigenvalues": values,
            "covariance": cov,
            "eigenvectors": vectors,
            "dc": None if dc is None else dc.reshape(shape[1:]),
        })


def svd_filter_stdmeanratio(
    xp,
    H,
    svd_threshold,
    stdmeanratio=0.5,
    filter_mode="number_of_values",
    remove_dc=False,
    debug=False,
):
    """SVD filtering to remove tissue signal"""

    if svd_threshold < 0:
        if debug:
            return H, None, None, None, None, None, None
        return H

    if remove_dc:
        dc = xp.mean(H, axis=0)
        H = H - dc
    else:
        dc = None

    sz = H.shape
    H2 = H.reshape((sz[0], sz[-1] * sz[-2])).T

    cov = H2.conj().T @ H2
    eps = 1e-12
    cov = cov + eps * xp.eye(cov.shape[0], dtype=cov.dtype)

    S, V = xp.linalg.eigh(cov)

    if filter_mode == "number_of_values":
        idx = xp.argsort(S)[::-1][:svd_threshold]
        mask = xp.zeros(len(S), dtype=bool)
        mask[idx] = True
    elif filter_mode == "amplitude_threshold":
        mask = S > svd_threshold
    elif filter_mode == "relative_amplitude_threshold":
        mask = S / S.max() > svd_threshold
    else:
        raise ValueError(f"Unknown filter_mode: {filter_mode}")

    Vt = V[:, mask]
    Vtbar = V[:, ~mask]

    U = H2 @ Vt

    U = U.reshape((sz[-2], sz[-1], -1))

    ratios = xp.std(U, axis=(0, 1)) / xp.mean(U, axis=(0, 1))

    second_mask = ratios < stdmeanratio
    Vtt = Vt[:, second_mask]

    if debug:
        U = U[:, :, second_mask]
        U = U.reshape((-1, U.shape[-1]))
        # print(Vtbar.shape, Vt[:, ~second_mask].shape)
        Vttbar = xp.concatenate([Vtbar, Vt[:, ~second_mask]], axis=-1)
        Ht = H2 - H2 @ Vttbar @ Vttbar.conj().T
        H2 -= U @ Vtt.conj().T
        # filtered H (complex), removed features U (complex), removed H (complex), eigenvalues S (real >=0), cov matrix (complex), eigenvectors (complex), dc image (complex)
        return (
            H2.T.reshape(sz),
            U.reshape((sz[-2], sz[-1], -1)),
            Ht.T.reshape(sz),
            S,
            cov,
            V,
            dc,
        )

    H2 -= H2 @ Vtt @ Vtt.conj().T
    return H2.T.reshape(sz)


def svd_filter_batched(xp, U_subaps, svd_threshold, *, block_size_mib=8,
                       regularization=1e-12, parallel=False):
    """Filter subapertures with bounded blocks or batched backend operations.

    Parallel processing trades stack-sized covariance/projection temporaries for
    fewer launches and batched eigendecomposition. It requires much more VRAM.
    In sequential mode, block_size_mib=None processes each subaperture's pixels
    in one block. Parallel mode does not use the pixel-block limit.
    """

    if svd_threshold < 0:
        return U_subaps

    ny_s, nx_s, sub_ny, sub_nx, nz = U_subaps.shape
    if parallel:
        count = min(int(svd_threshold), nz)
        if count == 0:
            return U_subaps.copy()
        matrix = U_subaps.reshape(ny_s * nx_s, sub_ny * sub_nx, nz)
        covariance = matrix.conj().swapaxes(-1, -2) @ matrix
        if regularization:
            covariance += regularization * xp.eye(nz, dtype=matrix.dtype)
        _, vectors = xp.linalg.eigh(covariance)
        selected = vectors[..., -count:]
        removed = matrix @ selected
        return (matrix - removed @ selected.conj().swapaxes(-1, -2)).reshape(U_subaps.shape)

    # Transposed tiling can be noncontiguous. Keep input views where possible;
    # process one subaperture at a time and write into the final output.
    result = xp.empty(U_subaps.shape, dtype=U_subaps.dtype)
    for y in range(ny_s):
        for x in range(nx_s):
            data = U_subaps[y, x].transpose(2, 0, 1)
            target = result[y, x].reshape(sub_ny * sub_nx, nz).T
            _svd_filter_matrix(xp, xp.linalg, data, target, svd_threshold,
                               "number_of_values", regularization=regularization,
                               block_size_mib=block_size_mib)
    return result


@cache # pyright: ignore[reportArgumentType]
def frequency_symmetric_filtering(
    xp, fft, batch_size, sampling_freq, low_freq, high_freq=None
):
    """Create symmetric frequency filter mask"""

    freqs = fft.fftfreq(batch_size, 1 / sampling_freq)

    if high_freq is None:
        idxs = xp.abs(freqs) > low_freq
    else:
        idxs = (high_freq > xp.abs(freqs)) & (xp.abs(freqs) > low_freq)

    return idxs, freqs[idxs]


def fourier_time_transform(xp, fft, H):
    """FFT along time axis"""
    return fft.fft(H, axis=0, norm="ortho")


def pca_time_transform(xp, H, remove_dc=False):
    if remove_dc:
        dc = xp.mean(H, axis=0)
        H = H - dc
    sz = H.shape
    H2 = H.reshape((sz[0], sz[-1] * sz[-2])).T

    cov = H2.conj().T @ H2

    S, V = xp.linalg.eigh(cov)

    return (H2 @ V).T.reshape(sz)


def corner_compensation(xp, psd):
    n_freqs, ny, nx = psd.shape

    # Create the mask
    disk = elliptical_mask(xp, ny, nx, 1.2)
    mask_3d = xp.tile(~disk, (n_freqs, 1, 1))

    # Create masked PSD for outside region
    psd_outside = psd.copy()
    psd_outside[mask_3d] = xp.nan

    mean_outside = xp.nanmean(psd_outside, axis=(-1, -2), keepdims=True)

    psd = psd / mean_outside

    return psd


@cache
def symmetric_frequency_slices(batch_size, sampling_freq, low_freq, high_freq=None):
    """Contiguous FFT-order runs matching the strict symmetric band mask.

    Planning uses CPU metadata so CuPy boolean indexing never synchronizes the
    compute stream or materializes a selected PSD stack.
    """
    import numpy as np

    frequencies = np.fft.fftfreq(batch_size, 1 / sampling_freq)
    selected = np.abs(frequencies) > low_freq
    if high_freq is not None:
        selected &= np.abs(frequencies) < high_freq
    edges = np.flatnonzero(np.diff(np.r_[False, selected, False]))
    return tuple(slice(int(start), int(stop)) for start, stop in edges.reshape(-1, 2))
