"""
Filtering operations: SVD, frequency filtering
"""

from functools import cache

from .utils import elliptical_mask

import holodoppler.backend as backend


def filter_2d(xp, fft, frames, filter2d_low):
    _, ny, nx = frames.shape

    F = fft.fft2(frames)

    mask = elliptical_mask(ny, nx, filter2d_low, xp)

    # import matplotlib.pyplot as plt
    # plt.imshow(fft.fftshift(~mask).get())
    # plt.show()

    F = F * fft.fftshift(~mask)

    F = fft.ifft2(F)

    return F



def svd_filter(
    H,
    svd_threshold,
    filter_mode="number_of_values",
    remove_dc=False,
    debug=False,
):
    """SVD filtering to remove tissue signal.

    The covariance eigendecomposition is performed in the temporal
    dimension. For Nt > 300 this is generally preferable to computing
    a full SVD of the pixel x time matrix.

    Parameters
    ----------
    H : array
        Input complex data, shape (Nt, Ny, Nx).

    svd_threshold : int or float
        Threshold used according to ``filter_mode``.

    filter_mode : str
        ``"number_of_values"``
            Remove the N largest singular/eigenvalue components.

        ``"amplitude_threshold"``
            Remove components whose eigenvalue is greater than the
            supplied threshold.

        ``"relative_amplitude_threshold"``
            Remove components whose eigenvalue / maximum eigenvalue
            exceeds the supplied threshold.

    remove_dc : bool
        Remove the temporal mean before filtering.

    debug : bool
        Return intermediate SVD quantities.

    Returns
    -------
    H_filtered : array
        Filtered data.

    If debug=True, also returns:
        removed_features,
        kept_data,
        eigenvalues,
        covariance,
        eigenvectors,
        dc
    """

    if svd_threshold < 0:
        if debug:
            return H, None, None, None, None, None, None
        return H

    xp = backend.xp

    # ------------------------------------------------------------------
    # Remove DC
    # ------------------------------------------------------------------
    if remove_dc:
        dc = xp.mean(H, axis=0)
        H = H - dc
    else:
        dc = None

    # ------------------------------------------------------------------
    # Arrange as:
    #
    #       H2 = [pixels, time]
    #
    # This makes H2.conj().T @ H2 an Nt x Nt covariance matrix.
    # ------------------------------------------------------------------
    sz = H.shape
    nt = sz[0]

    H2 = H.reshape(nt, -1).T

    # ------------------------------------------------------------------
    # Temporal covariance
    # ------------------------------------------------------------------
    cov = H2.conj().T @ H2

    # Small regularization.
    #
    # Scale epsilon with the covariance rather than using an absolute
    # 1e-12. This behaves better for very small or very large signals.
    trace = xp.real(xp.trace(cov))

    if nt:
        eps = xp.finfo(cov.real.dtype).eps * trace / nt
        if eps == 0:
            eps = xp.finfo(cov.real.dtype).eps

        cov = cov + eps * xp.eye(nt, dtype=cov.dtype)

    # ------------------------------------------------------------------
    # Hermitian eigendecomposition
    #
    # backend.linalg should map to the appropriate implementation:
    # NumPy/SciPy on CPU, CuPy on GPU.
    # ------------------------------------------------------------------
    S, V = backend.linalg.eigh(cov)

    # eigh returns ascending eigenvalues.
    #
    # Reversing is cheap compared with argsort and is sufficient here
    # because eigh already returns sorted eigenvalues.
    S = S[::-1]
    V = V[:, ::-1]

    # ------------------------------------------------------------------
    # Select components to REMOVE
    # ------------------------------------------------------------------
    if filter_mode == "number_of_values":

        n_remove = int(svd_threshold)

        if n_remove < 0:
            raise ValueError(
                "svd_threshold must be >= 0 for "
                "'number_of_values'"
            )

        n_remove = min(n_remove, nt)

        mask = xp.zeros(nt, dtype=bool)
        mask[:n_remove] = True

    elif filter_mode == "amplitude_threshold":

        mask = S > svd_threshold

    elif filter_mode == "relative_amplitude_threshold":

        smax = S[0]

        if smax == 0:
            mask = xp.zeros(nt, dtype=bool)
        else:
            mask = S / smax > svd_threshold

    else:
        raise ValueError(
            f"Unknown filter_mode: {filter_mode!r}. "
            "Expected 'number_of_values', "
            "'amplitude_threshold' or "
            "'relative_amplitude_threshold'."
        )

    V_remove = V[:, mask]
    V_keep = V[:, ~mask]

    # ------------------------------------------------------------------
    # Projection
    #
    # H_filtered = H2 - projection_onto_removed_subspace
    #
    # Computing H2 @ V_remove first is considerably cheaper than forming
    # the full Nt x Nt projection matrix.
    # ------------------------------------------------------------------
    if V_remove.shape[1] == 0:
        H_filtered = H2

    elif V_remove.shape[1] == nt:
        # Everything is removed.
        H_filtered = xp.zeros_like(H2)

    else:
        coefficients = H2 @ V_remove
        H_filtered = H2 - coefficients @ V_remove.conj().T

    # ------------------------------------------------------------------
    # Debug information
    # ------------------------------------------------------------------
    if debug:

        # Coordinates of the removed temporal modes.
        if V_remove.shape[1]:
            U_remove = H2 @ V_remove
        else:
            U_remove = xp.empty(
                (H2.shape[0], 0),
                dtype=H2.dtype,
            )

        # Reconstruct kept signal without constructing the full
        # projection matrix.
        if V_keep.shape[1]:
            H_kept = (H2 @ V_keep) @ V_keep.conj().T
        else:
            H_kept = xp.zeros_like(H2)

        return (
            H_filtered.T.reshape(sz),
            U_remove.reshape((sz[-2], sz[-1], -1)),
            H_kept.T.reshape(sz),
            S,
            cov,
            V,
            dc,
        )

    return H_filtered.T.reshape(sz)


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


def svd_filter_batched(xp, U_subaps, svd_threshold):
    """Batched SVD filter for subapertures"""

    if svd_threshold < 0:
        return U_subaps

    ny_s, nx_s, sub_ny, sub_nx, nz = U_subaps.shape
    B = ny_s * nx_s

    H2 = U_subaps.reshape(B, sub_ny * sub_nx, nz)
    eps = 1e-12

    cov = xp.einsum("bpi,bpj->bij", H2.conj(), H2) + eps * xp.eye(nz, dtype=H2.dtype)

    V_list = []
    for b in range(B):
        _, Vb = xp.linalg.eigh(cov[b])
        V_list.append(Vb[:, ::-1])

    Vt = xp.stack([Vb[:, :svd_threshold] for Vb in V_list], axis=0)
    H2_Vt = xp.einsum("bpi,bik->bpk", H2, Vt)
    proj = xp.einsum("bpk,bjk->bpj", H2_Vt, Vt.conj())

    return (H2 - proj).reshape(ny_s, nx_s, sub_ny, sub_nx, nz)


@cache
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
    disk = elliptical_mask(ny, nx, 1.2, xp)
    mask_3d = xp.tile(~disk, (n_freqs, 1, 1))

    # Create masked PSD for outside region
    psd_outside = psd.copy()
    psd_outside[mask_3d] = xp.nan

    mean_outside = xp.nanmean(psd_outside, axis=(-1, -2), keepdims=True)

    psd = psd / mean_outside

    return psd
