"""
Filtering operations: SVD, frequency filtering
"""

from functools import cache

import numpy as np
from scipy.signal.windows import get_window

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

def butterworth_high_pass_filter(xp, psd, low_freq, order, fs):
    """
    Applies a Butterworth high-pass filter to a PSD along axis 0 (fftfreq ordering)
    using a specified array namespace (e.g., numpy or cupy).
    
    Parameters:
    -----------
    xp : module
        Array module/namespace (e.g., numpy or cupy).
    psd : ndarray
        Power Spectral Density array where axis 0 is the frequency axis.
    low_freq : float
        Cutoff frequency of the high-pass filter.
    order : int
        Order of the Butterworth filter.
    fs : float
        Sampling frequency.
        
    Returns:
    --------
    ndarray
        Filtered PSD with the same shape as the input.
    """
    n = psd.shape[0]
    
    # Get frequencies corresponding to fftfreq ordering using xp
    freqs = xp.fft.fftfreq(n, d=1.0/fs)
    abs_freqs = xp.abs(freqs)
    
    # Compute Butterworth high-pass squared magnitude response: |H(f)|^2
    h_squared = xp.zeros_like(abs_freqs)
    mask = abs_freqs > 0
    h_squared[mask] = 1.0 / (1.0 + (low_freq / abs_freqs[mask]) ** (2 * order))
    # DC component (f = 0) automatically remains 0.0
    
    # Reshape h_squared to broadcast correctly along axis 0 for any N-D psd shape
    broadcast_shape = (n,) + (1,) * (psd.ndim - 1)
    h_squared = h_squared.reshape(broadcast_shape)
    
    return psd * h_squared



def svd_filter_by_bloc(xp, linalg, images, window_size=5, threshold=0,
                       remove_dc=False, svd_filter_by_bloc_window_stride=1, *,
                       svd_filter_by_bloc_parallel=False,
                       svd_filter_by_bloc_mib_block_size=8):
    """Local SVD with overlap averaging, preserving complex data.

    DC removal subtracts each pixel's temporal mean, even at threshold zero.
    The stride is in pixels along both spatial axes and cannot exceed the
    window size. Final windows align with the image edges for full coverage.
    """
    for name, value, minimum in (("window_size", window_size, 1),
                                  ("threshold", threshold, 0),
                                  ("svd_filter_by_bloc_window_stride", svd_filter_by_bloc_window_stride, 1)):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
            raise TypeError(f"{name} must be an integer")
        if value < minimum:
            raise ValueError(f"{name} must be >= {minimum}")
    if svd_filter_by_bloc_window_stride > window_size:
        raise ValueError("svd_filter_by_bloc_window_stride must be <= window_size")
    if not isinstance(svd_filter_by_bloc_parallel, bool):
        raise TypeError("svd_filter_by_bloc_parallel must be a boolean")
    budget = svd_filter_by_bloc_mib_block_size
    if budget is not None:
        if isinstance(budget, (bool, np.bool_)) or not isinstance(budget, (int, float, np.integer, np.floating)):
            raise TypeError("svd_filter_by_bloc_mib_block_size must be a real number or null")
        if not np.isfinite(budget) or budget <= 0:
            raise ValueError("svd_filter_by_bloc_mib_block_size must be finite and positive")
    if images.ndim != 3:
        raise ValueError("images must have shape (T, H, W)")
    nt, height, width = images.shape
    if window_size > min(height, width):
        raise ValueError("window_size exceeds image dimensions")
    work = images if images.dtype.kind in "fc" else images.astype(xp.float32)
    if remove_dc:
        work = work - work.mean(axis=0, keepdims=True)
    if threshold == 0:
        return work.copy()
    output = xp.zeros_like(work)
    weights = xp.zeros((height, width), dtype=xp.float32)
    def window_starts(size):
        last = size - window_size
        starts = list(range(0, last + 1, svd_filter_by_bloc_window_stride))
        if starts[-1] != last:
            starts.append(last)
        return starts

    pixels = window_size**2
    count = min(threshold, nt, pixels)
    if count == min(nt, pixels):
        return output
    ys = xp.asarray(window_starts(height))
    xs = xp.asarray(window_starts(width))
    origins = (ys[:, None] * width + xs[None, :]).reshape(-1)
    offsets = (xp.arange(window_size)[:, None] * width
               + xp.arange(window_size)[None, :]).reshape(-1)
    n_windows = origins.size
    # Estimate explicit temporaries; backend eigensolver workspace is additional.
    bytes_per_window = ((3 * nt * pixels + 2 * pixels**2 + nt * count)
                        * work.dtype.itemsize + pixels * 8)
    batch_size = n_windows if svd_filter_by_bloc_parallel or budget is None else max(
        1, int(budget * 1024**2) // bytes_per_window)
    flat = work.reshape(nt, -1)
    flat_output = output.reshape(nt, -1)
    times = xp.arange(nt)[:, None, None]
    for start in range(0, n_windows, batch_size):
        indices = origins[start:start + batch_size, None] + offsets[None, :]
        matrix = flat[:, indices].transpose(1, 0, 2)
        covariance = matrix.conj().swapaxes(-1, -2) @ matrix
        _, vectors = linalg.eigh(covariance)
        selected = vectors[..., -count:]
        filtered = matrix - (matrix @ selected) @ selected.conj().swapaxes(-1, -2)
        target = (times, indices[None, ...])
        values = filtered.transpose(1, 0, 2)
        if work.dtype.kind == "c":
            # CuPy scatter-add supports real types only. These are writable
            # views, so both additions update the original complex output.
            xp.add.at(flat_output.real, target, values.real)
            xp.add.at(flat_output.imag, target, values.imag)
        else:
            xp.add.at(flat_output, target, values)
        xp.add.at(weights.reshape(-1), indices, 1)
    output /= weights[None]
    return output


def svd_filter(
    xp,
    linalg,
    H,
    svd_threshold,
    filter_mode="number_of_values",
    remove_dc=False,
    diagnostic=None,
    block_size_mib=8,
    *,
    summary=None,
    effective_rank_multiplier=1.0,
    energy_fraction=0.9,
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
        "number_of_values", "amplitude_threshold", "effective_rank", or
        "energy_fraction". Adaptive modes ignore a nonnegative svd_threshold.
    remove_dc : bool
        Subtract the temporal mean before filtering.
    diagnostic : dict, optional
        Dictionary populated with intermediate results when provided.
    summary : dict, optional
        Requested keys (with arbitrary initial values): static_pc_sum,
        dynamic_pc_sum, svd_eigenvalues. Images sum absolute PC coefficients.
    effective_rank_multiplier : float
        Nonnegative multiplier of entropy effective rank, rounded up.
    energy_fraction : float
        Fraction of covariance energy removed in energy_fraction mode, in (0, 1].

    block_size_mib : positive float or None, optional
        Target size in MiB for each pixel-block work array, not total memory.
        Larger blocks can improve throughput at the cost of RAM/VRAM.
        None processes all pixels in one block without a workspace limit.

    Returns
    -------
    H_filtered : array
        Filtered data with the same shape as H.
    """
    if svd_threshold < 0 and summary is None:
        return H

    filtered = xp.empty(H.shape, dtype=H.dtype)
    _svd_filter_matrix(
        xp, linalg, H.reshape(H.shape[0], -1) if H.flags.c_contiguous else H,
        filtered.reshape(H.shape[0], -1), svd_threshold,
        filter_mode, remove_dc, diagnostic, H.shape, block_size_mib=block_size_mib,
        summary=summary, effective_rank_multiplier=effective_rank_multiplier,
        energy_fraction=energy_fraction,
    )
    return H if svd_threshold < 0 else filtered


def _validate_adaptive_svd(effective_rank_multiplier, energy_fraction):
    from numbers import Real
    from math import isfinite

    for name, value in (("effective_rank_multiplier", effective_rank_multiplier),
                        ("energy_fraction", energy_fraction)):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a real number")
        if not isfinite(value) or (value < 0 if name == "effective_rank_multiplier"
                                  else not 0 < value <= 1):
            raise ValueError(f"Invalid {name}: {value}")


def _svd_filter_matrix(xp, linalg, data, output, threshold, mode,
                       remove_dc=False, diagnostic=None, shape=None, regularization=0,
                       block_size_mib=8, *, summary=None,
                       effective_rank_multiplier=1.0, energy_fraction=0.9):
    """Filter time-first data into a time-by-pixel output without changing input."""
    nt, pixels = output.shape
    _validate_adaptive_svd(effective_rank_multiplier, energy_fraction)
    if threshold < 0:
        remove_dc = False
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
    if threshold < 0:
        selected = vectors[:, :0]
    elif mode == "number_of_values":
        selected = vectors[:, :min(int(threshold), nt)]
    elif mode == "amplitude_threshold":
        selected = vectors[:, values > threshold]
    elif mode in {"effective_rank", "energy_fraction"}:
        energy = xp.maximum(values, 0)
        total = float(xp.sum(energy))
        count = 0
        if total > 0:
            p = energy / total
            if mode == "effective_rank":
                positive = p[p > 0]
                rank = float(xp.exp(-xp.sum(positive * xp.log(positive))))
                from math import ceil
                count = min(nt, ceil(effective_rank_multiplier * rank))
            else:
                tolerance = xp.finfo(values.dtype).eps * nt
                count = min(nt, int(xp.searchsorted(xp.cumsum(p), energy_fraction - tolerance)) + 1)
        selected = vectors[:, :count]
    else:
        raise ValueError(f"Unknown filter_mode: {mode}")

    removed_features = (xp.empty((pixels, selected.shape[1]), dtype=data.dtype)
                        if diagnostic is not None else None)
    conjugate = selected.conj()
    projections = {}
    if summary is not None:
        if "svd_eigenvalues" in summary:
            summary["svd_eigenvalues"] = values
        for name in ("static_pc_sum", "dynamic_pc_sum"):
            if name in summary:
                projections[name] = xp.empty(pixels, dtype=values.dtype)
    for start in range(0, pixels, block_size):
        stop = min(start + block_size, pixels)
        block = output[:, start:stop]
        count = selected.shape[1]
        for name, projection in projections.items():
            basis = vectors[:, :count] if name == "static_pc_sum" else vectors[:, count:]
            projection[start:stop] = xp.sum(xp.abs(basis.T @ block), axis=0)
        if selected.shape[1]:
            removed = selected.T @ block
            block -= conjugate @ removed
            if removed_features is not None:
                removed_features[start:stop] = removed.T
        elif removed_features is not None:
            removed_features[start:stop] = 0

    for name, projection in projections.items():
        summary[name] = projection.reshape(shape[1:])
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


@cache
def _welch_window(name, length):
    """Return immutable CPU taper weights and their mean squared weight."""
    if not isinstance(name, str):
        raise TypeError("welch_windowing must be a window name or null")
    try:
        weights = get_window(name, length, fftbins=True)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid welch_windowing: {name!r}") from exc
    energy = float(np.mean(weights ** 2))
    if not np.isfinite(energy) or energy <= 0:
        raise ValueError("welch_windowing must have finite positive mean squared weight")
    weights.setflags(write=False)
    return weights, energy


def welch_power_spectrum(xp, fft, H, batch_size=32, stride=32, windowing=None):
    """Average complete, time-first segment periodograms without detrending."""
    if batch_size > H.shape[0]:
        raise ValueError("welch_batch_size must fit within the supplied frame stack")
    taper, energy = None, 1.0
    if windowing is not None:
        weights, energy = _welch_window(windowing, batch_size)
        taper = xp.asarray(weights, dtype=H.real.dtype).reshape(
            (batch_size,) + (1,) * (H.ndim - 1))
    total = None
    starts = range(0, H.shape[0] - batch_size + 1, stride)
    for start in starts:
        segment = H[start:start + batch_size]
        if taper is not None:
            segment = segment * taper
        spectrum = fourier_time_transform(xp, fft, segment)
        power = xp.abs(spectrum)
        del spectrum
        xp.square(power, out=power)
        if total is None:
            total = power
        else:
            total += power
    total /= len(starts) * energy
    return total


def pca_packet_mean(xp, holograms, window, index_range):
    """Average PCA magnitude sums over complete, consecutive time packets."""
    start, end = index_range
    count = holograms.shape[0] // window
    if count == 0:
        raise ValueError("pca_time_window must fit within the supplied frame stack")
    total = None
    for offset in range(0, count * window, window):
        projected = pca_time_transform(
            xp, holograms[offset:offset + window], remove_dc=False)
        image = xp.sum(xp.abs(projected[start:end]), axis=0)
        if total is None:
            total = image
        else:
            total += image
    return total / count


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
