"""
Filtering operations: SVD, frequency filtering
"""

from functools import cache
from .utils import elliptical_mask

def svd_filter(xp, H, svd_threshold, filter_mode="number_of_values", remove_dc=False, debug=False):
    """SVD filtering to remove tissue signal"""

    if svd_threshold < 0:
        if debug:
            return H, None,  None, None, None, None, None
        return H
    
    if remove_dc:
        dc = xp.mean(H,axis=0)
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

    if debug:
        U = H2 @ Vt
        Ht = H2 - H2 @ Vtbar @ Vtbar.conj().T
        H2 -= U @ Vt.conj().T
        # filtered H (complex), removed features U (complex), removed H (complex), eigenvalues S (real >=0), cov matrix (complex), eigenvectors (complex), dc image (complex)
        return H2.T.reshape(sz), U.reshape((sz[-2],sz[-1],-1)), Ht.T.reshape(sz), S, cov, V, dc
    
    H2 -= H2 @ Vt @ Vt.conj().T
    return H2.T.reshape(sz)

def svd_filter_stdmeanratio(xp, H, svd_threshold, stdmeanratio = 0.5, filter_mode="number_of_values", remove_dc=False, debug=False):
    """SVD filtering to remove tissue signal"""

    if svd_threshold < 0:
        if debug:
            return H, None,  None, None, None, None, None
        return H
    
    if remove_dc:
        dc = xp.mean(H,axis=0)
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

    U = U.reshape((sz[-2],sz[-1],-1))

    ratios = xp.std(U,axis = (0,1)) / xp.mean(U,axis = (0,1))

    second_mask = ratios < stdmeanratio
    Vtt = Vt[:, second_mask]




    if debug:
        U = U[:,:,second_mask]
        U = U.reshape((-1,U.shape[-1]))
        # print(Vtbar.shape, Vt[:, ~second_mask].shape)
        Vttbar = xp.concatenate([Vtbar,Vt[:, ~second_mask]], axis=-1)
        Ht = H2 - H2 @ Vttbar @ Vttbar.conj().T
        H2 -= U @ Vtt.conj().T
        # filtered H (complex), removed features U (complex), removed H (complex), eigenvalues S (real >=0), cov matrix (complex), eigenvectors (complex), dc image (complex)
        return H2.T.reshape(sz), U.reshape((sz[-2],sz[-1],-1)), Ht.T.reshape(sz), S, cov, V, dc
    
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
        dc = xp.mean(H,axis=0)
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