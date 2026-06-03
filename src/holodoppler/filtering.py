"""
Filtering operations: SVD, frequency filtering
"""

from functools import cache


def svd_filter(xp, H, svd_threshold, filter_mode="number_of_values"):
    """SVD filtering to remove tissue signal"""

    if svd_threshold < 0:
        return H

    sz = H.shape
    H2 = H.reshape((sz[0], sz[-1] * sz[-2])).T

    cov = H2.conj().T @ H2
    eps = 1e-12
    cov = cov + eps * xp.eye(cov.shape[0], dtype=cov.dtype)

    S, V = xp.linalg.eigh(cov)

    if filter_mode == "number_of_values":
        idx = xp.argsort(S)[::-1]
        V = V[:, idx]
        Vt = V[:, :svd_threshold]
    elif filter_mode == "amplitude_threshold":
        S, V = xp.linalg.eigh(cov)
        idx = S > svd_threshold
        Vt = V[:, idx]
    elif filter_mode == "relative_amplitude_threshold":
        S, V = xp.linalg.eigh(cov)
        idx = S/S.max() > svd_threshold
        Vt = V[:, idx]

    H2 -= H2 @ Vt @ Vt.conj().T
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