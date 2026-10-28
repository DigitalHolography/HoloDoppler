"""
Shack-Hartmann wavefront sensing
"""

from .propagation import (
    build_fresnel_kernel_in,
    build_angular_kernel,
    ensure_yx_pixel_pitch,
)
from .filtering import (
    svd_filter_batched,
    symmetric_frequency_slices,
)
from .image_utils import elliptical_mask


def construct_subapertures_fresnel(
    xp,
    fft,
    U0,
    wavelength,
    z_prop,
    pixel_pitch,
    low_freq,
    high_freq,
    fs,
    time_window,
    nx_subabs,
    ny_subabs,
    svd_threshold,
    *,
    sub_aps_process="sequential",
    svd_block_size_mib=8,
    svd_regularization=1e-12,
):
    """Construct Fresnel subaperture images sequentially or in backend batches.

    Sequential mode finishes one tile at a time to minimize RAM/VRAM. Parallel
    mode batches propagation, SVD, and FFTs for throughput, using much more memory.
    """
    _validate_subaperture_mode(sub_aps_process)
    nt, ny, nx = U0.shape
    sub_ny, sub_nx = ny // ny_subabs, nx // nx_subabs
    crop_ny, crop_nx = sub_ny * ny_subabs, sub_nx * nx_subabs
    y0, x0 = (ny - crop_ny) // 2, (nx - crop_nx) // 2
    kernel = build_fresnel_kernel_in(
        xp, z_prop, ensure_yx_pixel_pitch(pixel_pitch), wavelength, ny, nx,
        zero_padding=None,
    )
    bands = symmetric_frequency_slices(time_window, fs, low_freq, high_freq)
    if sub_aps_process == "parallel":
        field = U0[:, y0:y0 + crop_ny, x0:x0 + crop_nx] * kernel[:, y0:y0 + crop_ny, x0:x0 + crop_nx]
        tiles = field.reshape(nt, ny_subabs, sub_ny, nx_subabs, sub_nx).transpose(1, 3, 2, 4, 0)
        filtered = svd_filter_batched(
            xp, tiles, svd_threshold, parallel=True,
            block_size_mib=svd_block_size_mib, regularization=svd_regularization,
        )
        del tiles, field
        filtered = filtered.reshape(ny_subabs * nx_subabs, sub_ny, sub_nx, nt).transpose(0, 3, 1, 2)
        spatial = fft.fft2(filtered, axes=(-2, -1))
        del filtered
        centered = fft.fftshift(spatial, axes=(-2, -1))
        del spatial
        spectrum = fft.fft(centered, axis=1)
        del centered
        return _subaperture_power(xp, spectrum, bands, axis=1).reshape(
            ny_subabs, nx_subabs, sub_ny, sub_nx)

    result = xp.empty((ny_subabs, nx_subabs, sub_ny, sub_nx), dtype=xp.float32)

    for y in range(ny_subabs):
        ys = slice(y0 + y * sub_ny, y0 + (y + 1) * sub_ny)
        for x in range(nx_subabs):
            xs = slice(x0 + x * sub_nx, x0 + (x + 1) * sub_nx)
            field = U0[:, ys, xs] * kernel[:, ys, xs]
            tiled = field.transpose(1, 2, 0)[None, None, ...]
            filtered = svd_filter_batched(
                xp, tiled, svd_threshold, block_size_mib=svd_block_size_mib,
                regularization=svd_regularization,
            )
            filtered = filtered[0, 0].transpose(2, 0, 1)
            del tiled, field

            spatial = fft.fft2(filtered, axes=(-2, -1))
            del filtered
            centered = fft.fftshift(spatial, axes=(-2, -1))
            del spatial
            spectrum = fft.fft(centered, axis=0)
            del centered

            result[y, x] = _subaperture_power(xp, spectrum, bands, axis=0)
            del spectrum
    return result


def construct_subapertures_angular(
    xp,
    fft,
    U0,
    wavelength,
    z_prop,
    pixel_pitch,
    low_freq,
    high_freq,
    fs,
    time_window,
    nx_subabs,
    ny_subabs,
    svd_threshold,
    *,
    sub_aps_process="sequential",
    svd_block_size_mib=8,
    svd_regularization=1e-12,
):
    """Construct angular subapertures in sequential or batched backend mode.

    Angular propagation needs the full spatial Fourier stack in either mode;
    sequential mode bounds the following inverse FFT, SVD, and temporal FFT work.
    """
    _validate_subaperture_mode(sub_aps_process)
    nt, ny, nx = U0.shape
    sub_ny, sub_nx = ny // ny_subabs, nx // nx_subabs
    kernel = build_angular_kernel(
        xp, z_prop, ensure_yx_pixel_pitch(pixel_pitch), wavelength, ny, nx,
        zero_padding=None,
    )
    spectrum = fft.fft2(U0.astype(xp.complex64, copy=False), axes=(-2, -1))
    spectrum *= fft.fftshift(kernel, axes=(-2, -1))
    crop_ny, crop_nx = sub_ny * ny_subabs, sub_nx * nx_subabs
    y0, x0 = (ny - crop_ny) // 2, (nx - crop_nx) // 2
    spectrum = fft.fftshift(spectrum[:, y0:y0 + crop_ny, x0:x0 + crop_nx], axes=(-2, -1))
    bands = symmetric_frequency_slices(time_window, fs, low_freq, high_freq)

    if sub_aps_process == "parallel":
        tiles = spectrum.reshape(nt, ny_subabs, sub_ny, nx_subabs, sub_nx).transpose(0, 1, 3, 2, 4)
        tiles = fft.ifftshift(tiles, axes=(-2, -1))
        del spectrum
        field = fft.ifft2(tiles, axes=(-2, -1))
        del tiles
        filtered = svd_filter_batched(
            xp, field.transpose(1, 2, 3, 4, 0), svd_threshold, parallel=True,
            block_size_mib=svd_block_size_mib, regularization=svd_regularization,
        )
        del field
        filtered = filtered.reshape(ny_subabs * nx_subabs, sub_ny, sub_nx, nt).transpose(0, 3, 1, 2)
        temporal = fft.fft(filtered, axis=1, norm="ortho")
        del filtered
        return _subaperture_power(xp, temporal, bands, axis=1).reshape(
            ny_subabs, nx_subabs, sub_ny, sub_nx)

    result = xp.empty((ny_subabs, nx_subabs, sub_ny, sub_nx), dtype=xp.float32)
    for y in range(ny_subabs):
        ys = slice(y * sub_ny, (y + 1) * sub_ny)
        for x in range(nx_subabs):
            xs = slice(x * sub_nx, (x + 1) * sub_nx)
            shifted = fft.ifftshift(spectrum[:, ys, xs], axes=(-2, -1))
            field = fft.ifft2(shifted, axes=(-2, -1))
            del shifted
            filtered = svd_filter_batched(
                xp, field.transpose(1, 2, 0)[None, None, ...], svd_threshold,
                block_size_mib=svd_block_size_mib, regularization=svd_regularization,
            )[0, 0].transpose(2, 0, 1)
            del field
            temporal = fft.fft(filtered, axis=0, norm="ortho")
            del filtered
            result[y, x] = _subaperture_power(xp, temporal, bands, axis=0)
            del temporal
    return result


def _validate_subaperture_mode(mode):
    if mode not in ("sequential", "parallel"):
        raise ValueError("sub_aps_process must be 'sequential' or 'parallel'")


def _subaperture_power(xp, spectrum, bands, axis):
    """Mean band power, preserving the original frequency-bin normalization."""
    count = sum(part.stop - part.start for part in bands)
    shape = spectrum.shape[:axis] + spectrum.shape[axis + 1:]
    image = xp.zeros(shape, dtype=xp.float32)
    for part in bands:
        selection = (slice(None),) * axis + (part,)
        power = xp.abs(spectrum[selection])
        xp.square(power, out=power)
        image += xp.sum(power, axis=axis)
        del power
    return image / count if count else xp.full_like(image, xp.nan)


def calculate_displacements(
    xp,
    fft,
    U_subaps,
    pupil_threshold=1.0,
    deviation_threshold=3.0,
    shifts_range=20.0,
    ref=None,
    mask_disk_ratio=None,
    diagnostics=None,
):
    """Calculate subaperture displacements using phase correlation"""
    ny_s, nx_s, Ny, Nx = U_subaps.shape

    if ref is None or ref == "central_sub_ap":
        ref = U_subaps[ny_s // 2, nx_s // 2]

    moving_stack = U_subaps.reshape(ny_s * nx_s, Ny, Nx)

    if mask_disk_ratio is not None:
        mask = elliptical_mask(xp, Ny, Nx, mask_disk_ratio)

        ref_masked = ref * mask
        moving_masked = moving_stack * mask

        masked_pixels_ref = ref_masked[mask]
        if len(masked_pixels_ref) > 0:
            ref_mean = xp.mean(masked_pixels_ref)
        else:
            ref_mean = 0.0
        ref_zm = ref_masked - ref_mean

        moving_zm = xp.zeros_like(moving_masked)
        for i in range(moving_masked.shape[0]):
            masked_pixels_moving = moving_masked[i][mask]
            if len(masked_pixels_moving) > 0:
                moving_mean = xp.mean(masked_pixels_moving)
            else:
                moving_mean = 0.0
            moving_zm[i] = moving_masked[i] - moving_mean
    else:
        ref_zm = ref - xp.mean(ref)
        moving_zm = moving_stack - xp.mean(moving_stack, axis=(1, 2), keepdims=True)

    F_ref = fft.fft2(ref_zm)
    F_moving = fft.fft2(moving_zm)
    cp_corr = F_moving * F_ref.conj()
    xcorr = xp.abs(
        fft.fftshift(fft.ifft2(cp_corr / (xp.abs(cp_corr) + 1e-12)), axes=(1, 2))
    )

    xcorr_2d = xcorr.reshape(-1, Ny * Nx)
    peaks = xp.argmax(xcorr_2d, axis=1)
    py = peaks // Nx
    px = peaks % Nx

    py = xp.clip(py, 1, Ny - 2)
    px = xp.clip(px, 1, Nx - 2)

    n = py.shape[0]
    idx = xp.arange(n)

    v0 = xcorr[idx, py, px]
    vm_y = xcorr[idx, py - 1, px]
    vp_y = xcorr[idx, py + 1, px]
    vm_x = xcorr[idx, py, px - 1]
    vp_x = xcorr[idx, py, px + 1]

    den_y = vm_y - 2 * v0 + vp_y + 1e-12
    den_x = vm_x - 2 * v0 + vp_x + 1e-12

    cy = (Ny - 1) / 2 if Ny % 2 == 1 else Ny / 2
    cx = (Nx - 1) / 2 if Nx % 2 == 1 else Nx / 2

    shift_y = py + 0.5 * (vm_y - vp_y) / den_y - cy
    shift_x = px + 0.5 * (vm_x - vp_x) / den_x - cx

    shift_y = shift_y.reshape(ny_s, nx_s)
    shift_x = shift_x.reshape(ny_s, nx_s)

    # Pupil mask for outlier rejection
    xs = xp.linspace(-1, 1, nx_s)
    ys = xp.linspace(-1, 1, ny_s)
    YY, XX = xp.meshgrid(ys, xs, indexing="ij")
    pupil_mask = (XX**2 + YY**2) <= pupil_threshold

    shift_y_flat = shift_y[pupil_mask]
    shift_x_flat = shift_x[pupil_mask]

    mean_y = xp.mean(shift_y_flat) if len(shift_y_flat) > 0 else 0
    mean_x = xp.mean(shift_x_flat) if len(shift_x_flat) > 0 else 0
    std_y = xp.std(shift_y_flat) if len(shift_y_flat) > 0 else 1
    std_x = xp.std(shift_x_flat) if len(shift_x_flat) > 0 else 1

    thresh_y = deviation_threshold * std_y
    thresh_x = deviation_threshold * std_x

    bad = (
        (xp.abs(shift_y - mean_y) > thresh_y)
        | (xp.abs(shift_x - mean_x) > thresh_x)
        | (xp.abs(shift_y) > shifts_range)
        | (xp.abs(shift_x) > shifts_range)
        | (~pupil_mask)
    )

    shift_y[bad] = xp.nan
    shift_x[bad] = xp.nan

    if diagnostics is not None:
        diagnostics["shack_hartmann_shifts"] = xp.stack((shift_y, shift_x), axis=-1).astype(xp.float32)

    return shift_y.astype(xp.float32), shift_x.astype(xp.float32)


def calculate_displacements_graph_laplacian(
    xp,
    fft,
    U_subaps,
    mask=None,
    pupil_threshold=1.0,
    deviation_threshold=3.0,
    shifts_range=20.0,
    use_corr_weights=False,
    diagnostics=None,
):
    """Solve shifts; optional diagnostics store accepted directed pair shifts.

    Shape is (ny_sub, nx_sub, ny_sub, nx_sub, 2), last axis (dy, dx)
    in pixels. Pair [iy, ix, jy, jx] measures j relative to i.
    Rejected, self, and uncomputed pairs are NaN.
    """
    ny_s, nx_s, Ny, Nx = U_subaps.shape
    B = ny_s * nx_s
    eps = 1e-12

    U = U_subaps.reshape(B, Ny, Nx)
    if mask is not None:
        mask_f = mask.astype(xp.float32, copy=False)
        mean = xp.sum(U * mask_f, axis=(-2, -1)) / xp.maximum(
            xp.sum(mask_f, axis=(-2, -1)), 1.0
        )
        U = (U - mean[:, xp.newaxis, xp.newaxis]) * mask_f

    yy, xx = xp.meshgrid(
        xp.linspace(-1, 1, ny_s),
        xp.linspace(-1, 1, nx_s),
        indexing="ij",
    )
    pupil_mask = (xx * xx + yy * yy) <= pupil_threshold
    pupil_flat = pupil_mask.reshape(B)

    pair_shifts = None
    if diagnostics is not None:
        pair_shifts = xp.full((B, B, 2), xp.nan, dtype=xp.float32)
        diagnostics["shack_hartmann_shifts"] = pair_shifts.reshape(ny_s, nx_s, ny_s, nx_s, 2)

    valid_ids = xp.where(pupil_flat)[0]
    if valid_ids.size < 2:
        out = xp.full((ny_s, nx_s), xp.nan, dtype=xp.float32)
        return out, out.copy()

    cy, cx = ny_s // 2, nx_s // 2
    d2 = (valid_ids // nx_s - cy) ** 2 + (valid_ids % nx_s - cx) ** 2
    center_idx = int(valid_ids[xp.argmin(d2)])

    F = fft.fft2(U - xp.mean(U, axis=(1, 2), keepdims=True), axes=(-2, -1))

    S_y = xp.zeros((B, B), dtype=xp.float32)
    S_x = xp.zeros((B, B), dtype=xp.float32)
    Wd = xp.zeros((B, B), dtype=xp.float32)

    ar = xp.arange(B)

    cy = (Ny - 1) / 2 if Ny % 2 == 1 else Ny / 2
    cx = (Nx - 1) / 2 if Nx % 2 == 1 else Nx / 2

    for i in valid_ids.tolist() if hasattr(valid_ids, "tolist") else list(valid_ids):
        i = int(i)
        cp_corr = F * F[i : i + 1].conj()
        cp_corr /= xp.abs(cp_corr) + eps

        xcorr = xp.abs(fft.fftshift(fft.ifft2(cp_corr, axes=(-2, -1)), axes=(-2, -1)))

        peaks = xp.argmax(xcorr.reshape(B, -1), axis=1)
        py = xp.clip(peaks // Nx, 1, Ny - 2)
        px = xp.clip(peaks % Nx, 1, Nx - 2)

        v0 = xcorr[ar, py, px]

        dy = (
            py
            + 0.5
            * (xcorr[ar, py - 1, px] - xcorr[ar, py + 1, px])
            / (xcorr[ar, py - 1, px] - 2 * v0 + xcorr[ar, py + 1, px] + eps)
            - cy
        )

        dx = (
            px
            + 0.5
            * (xcorr[ar, py, px - 1] - xcorr[ar, py, px + 1])
            / (xcorr[ar, py, px - 1] - 2 * v0 + xcorr[ar, py, px + 1] + eps)
            - cx
        )

        ok = (
            pupil_flat
            & xp.isfinite(dy)
            & xp.isfinite(dx)
            & (xp.abs(dy) <= 2 * shifts_range)
            & (xp.abs(dx) <= 2 * shifts_range)
        )
        ok[i] = False

        if pair_shifts is not None:
            pair_shifts[i, ok, 0] = dy[ok]
            pair_shifts[i, ok, 1] = dx[ok]

        S_y[i, ok] = dy[ok].astype(xp.float32)
        S_x[i, ok] = dx[ok].astype(xp.float32)
        Wd[i, ok] = v0[ok].astype(xp.float32) if use_corr_weights else 1

    upper = xp.triu(xp.ones((B, B), dtype=bool), 1)
    upper &= pupil_flat[:, None] & pupil_flat[None, :]

    both = upper & (Wd > 0) & (Wd.T > 0)
    only_ij = upper & (Wd > 0) & ~(Wd.T > 0)
    only_ji = upper & ~(Wd > 0) & (Wd.T > 0)

    W_up = xp.where(
        both, 0.5 * (Wd + Wd.T), xp.where(only_ij, Wd, xp.where(only_ji, Wd.T, 0))
    )
    Sy_up = xp.where(
        both, 0.5 * (S_y - S_y.T), xp.where(only_ij, S_y, xp.where(only_ji, -S_y.T, 0))
    )
    Sx_up = xp.where(
        both, 0.5 * (S_x - S_x.T), xp.where(only_ij, S_x, xp.where(only_ji, -S_x.T, 0))
    )

    edge = upper & (W_up > 0) & xp.isfinite(Sy_up) & xp.isfinite(Sx_up)

    W = xp.where(edge, W_up, 0).astype(xp.float64)
    Sy = xp.where(edge, Sy_up, 0).astype(xp.float64)
    Sx = xp.where(edge, Sx_up, 0).astype(xp.float64)

    W = W + W.T
    Sy = Sy - Sy.T
    Sx = Sx - Sx.T

    keep = pupil_flat.copy()
    keep[center_idx] = False
    K = xp.where(keep)[0]
    n = K.size

    shift_y = xp.full(B, xp.nan, dtype=xp.float64)
    shift_x = xp.full(B, xp.nan, dtype=xp.float64)
    shift_y[center_idx] = 0.0
    shift_x[center_idx] = 0.0

    if n:
        L = -W[xp.ix_(K, K)]
        diag = xp.sum(W[K, :], axis=1) + eps
        L[xp.arange(n), xp.arange(n)] = diag

        rhs_y = -xp.sum(W[K, :] * Sy[K, :], axis=1)
        rhs_x = -xp.sum(W[K, :] * Sx[K, :], axis=1)

        sol = xp.linalg.solve(L, xp.stack((rhs_y, rhs_x), axis=1))
        shift_y[K] = sol[:, 0]
        shift_x[K] = sol[:, 1]

    result_y = shift_y.reshape(ny_s, nx_s).astype(xp.float32)
    result_x = shift_x.reshape(ny_s, nx_s).astype(xp.float32)

    valid = pupil_mask & xp.isfinite(result_y) & xp.isfinite(result_x)

    if bool(xp.any(valid)):
        my, mx = xp.mean(result_y[valid]), xp.mean(result_x[valid])
        sy, sx = xp.std(result_y[valid]) + eps, xp.std(result_x[valid]) + eps

        bad = (
            ~valid
            | (xp.abs(result_y - my) > deviation_threshold * sy)
            | (xp.abs(result_x - mx) > deviation_threshold * sx)
            | (xp.abs(result_y) > shifts_range)
            | (xp.abs(result_x) > shifts_range)
        )

        result_y[bad] = xp.nan
        result_x[bad] = xp.nan

    return result_y, result_x
