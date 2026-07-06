"""
Image registration using phase correlation for Translation, Rotation, and Scale (TRS).
"""

from .utils import elliptical_mask
from .utils import signed_peak, subpixel_parabola


def register_laplacian(xp, fft, video, radius=None):
    nt, ny, nx = video.shape
    
    # Precompute mask once
    mask = elliptical_mask(ny, nx, radius, xp) if radius else None
    
    # Preprocess all frames once
    preprocessed = xp.zeros((nt, ny, nx), dtype=xp.float32)
    for k in range(nt):
        frame = video[k].astype(xp.float32, copy=False)
        preprocessed[k] = _preprocess(xp, frame, mask=mask)
    
    # Store shifts (only upper triangle to save memory)
    shifts_y = xp.zeros((nt, nt), dtype=xp.float32)
    shifts_x = xp.zeros((nt, nt), dtype=xp.float32)
    
    # Compute pairwise shifts more efficiently
    for k in range(nt):
        for m in range(k + 1, nt):
            shift_y, shift_x = intensity_corr_integer(
                xp, fft, preprocessed[k], preprocessed[m]
            )
            shifts_y[k, m] = shift_y
            shifts_x[k, m] = shift_x
    
    # Create full symmetric matrix (optional)
    shifts_y = shifts_y + shifts_y.T
    shifts_x = shifts_x + shifts_x.T
    
    # Compute average shifts with safe division
    # For each frame, average shifts to all other frames
    # Exclude self (diagonal)
    row_counts = xp.full(nt, nt - 1, dtype=xp.float32)  # nt-1 shifts per row
    
    # Sum each row
    sum_y = xp.sum(shifts_y, axis=1)
    sum_x = xp.sum(shifts_x, axis=1)
    
    # Safe division
    res_y = sum_y / row_counts
    res_x = sum_x / row_counts
    
    return res_y, res_x


def register_images_shifts(xp, fft, fixed, moving, radius=None, gaussian_sigma=None, gaussian_filter=None):
    ny, nx = fixed.shape[-2:]

    mask = elliptical_mask(ny, nx, radius, xp) if radius else None

    fixed_f = fixed.astype(xp.float32, copy=False)
    moving_f = moving.astype(xp.float32, copy=False)

    fixed_e = _preprocess(xp, fixed_f, mask=mask, gaussian_sigma=gaussian_sigma, gaussian_filter=gaussian_filter)
    moving_e = _preprocess(xp, moving_f, mask=mask, gaussian_sigma=gaussian_sigma, gaussian_filter=gaussian_filter)

    shift_y, shift_x = intensity_corr_integer(xp, fft, fixed_e, moving_e)

    return shift_y, shift_x

def apply_register_images_shifts(xp, image, shift_y, shift_x):

    return xp.roll(xp.roll(image,shift_y, axis=-2),shift_x, axis=-1)

    
def _preprocess(xp, img, mask=None, gaussian_sigma=None, gaussian_filter=None):
    """Convert to float32, optionally smooth, subtract masked mean, and apply mask."""
    out = img.astype(xp.float32, copy=False)

    if gaussian_sigma is not None and gaussian_sigma > 0:
        out = gaussian_filter(out, sigma=gaussian_sigma)

    if mask is None:
        return out - xp.mean(out)

    # Usually faster and cleaner than out[mask] on GPU because it avoids compaction.
    mask_f = mask.astype(xp.float32, copy=False)
    mean = xp.sum(out * mask_f) / xp.maximum(xp.sum(mask_f), 1.0)

    return (out - mean) * mask_f
















_EPS = 1e-12


def register_trs(
    xp,
    fft,
    ndi,
    fixed,
    moving,
    radius=None,
    estimate_similarity=True,
    translation_only=False,
    integer_translation=False,
    gaussian_sigma=None,
    radial_bins=256,
    angular_bins=360,
    return_registered=False,
):
    """
    Register moving onto fixed.

    Parameters
    ----------
    translation_only : bool
        If True, skip rotation/scale estimation.
    integer_translation : bool
        If True, estimate and apply integer shifts only. This is faster and allows xp.roll.
    gaussian_sigma : float or None
        If not None, apply gaussian_filter before estimating registration.
        Typical value: 1.5.
    """
    ny, nx = fixed.shape[-2:]

    mask = elliptical_mask(ny, nx, radius, xp) if radius else None

    fixed_f = fixed.astype(xp.float32, copy=False)
    moving_f = moving.astype(xp.float32, copy=False)

    fixed_e = _preprocess_for_registration(xp, ndi, fixed_f, mask, gaussian_sigma)
    moving_e = _preprocess_for_registration(xp, ndi, moving_f, mask, gaussian_sigma)

    do_similarity = estimate_similarity and not translation_only

    if do_similarity:
        angle_deg, scale = estimate_rotation_scale(
            xp,
            fft,
            ndi,
            fixed_e,
            moving_e,
            radial_bins=radial_bins,
            angular_bins=angular_bins,
        )

        moving_rs = apply_rotation_scale(xp, ndi, moving_f, angle_deg, scale)

        moving_rs_e = _preprocess_for_registration(
            xp,
            ndi,
            moving_rs,
            mask,
            gaussian_sigma,
        )
    else:
        angle_deg = 0.0
        scale = 1.0
        moving_rs_e = moving_e

    if integer_translation:
        shift_y, shift_x = phase_corr_integer(xp, fft, fixed_e, moving_rs_e)
    else:
        shift_y, shift_x = phase_corr_subpixel(xp, fft, fixed_e, moving_rs_e)

    if not return_registered:
        return shift_y, shift_x, angle_deg, scale

    reg = (shift_y, shift_x, angle_deg, scale)

    moving_registered = apply_registration(
        xp,
        fft,
        ndi,
        moving_f,
        reg,
        integer_translation=integer_translation,
    )

    return shift_y, shift_x, angle_deg, scale, moving_registered


def _preprocess_for_registration(xp, ndi, img, mask=None, gaussian_sigma=None):
    """Convert to float32, optionally smooth, subtract masked mean, and apply mask."""
    out = img.astype(xp.float32, copy=False)

    if gaussian_sigma is not None and gaussian_sigma > 0:
        out = ndi.gaussian_filter(out, sigma=gaussian_sigma)

    if mask is None:
        return out - xp.mean(out)

    # Usually faster and cleaner than out[mask] on GPU because it avoids compaction.
    mask_f = mask.astype(xp.float32, copy=False)
    mean = xp.sum(out * mask_f) / xp.maximum(xp.sum(mask_f), 1.0)

    return (out - mean) * mask_f


def phase_corr_integer(xp, fft, fixed, moving):
    """Integer-pixel phase-correlation shift estimate."""
    ny, nx = fixed.shape[-2:]

    fa = fft.fft2(fixed, axes=(-2, -1))
    fb = fft.fft2(moving, axes=(-2, -1))

    cps = fb * fa.conj()
    cps *= 1.0 / (xp.abs(cps))

    corr = fft.ifft2(cps, axes=(-2, -1))
    mag = xp.abs(corr)

    idx = xp.argmax(mag)
    ky, kx = xp.unravel_index(idx, mag.shape)
    ky, kx = int(ky), int(kx)

    peak_y, peak_x = signed_peak(ky, kx, ny, nx)

    return -int(peak_y), -int(peak_x)

def intensity_corr_integer(xp, fft, fixed, moving):
    """Integer-pixel intensity-correlation shift estimate."""
    ny, nx = fixed.shape[-2:]

    fa = fft.fft2(fixed, axes=(-2, -1))
    fb = fft.fft2(moving, axes=(-2, -1))

    cps = fb * fa.conj()

    corr = fft.ifft2(cps, axes=(-2, -1))
    mag = xp.abs(corr)

    idx = xp.argmax(mag)
    ky, kx = xp.unravel_index(idx, mag.shape)
    ky, kx = int(ky), int(kx)

    peak_y, peak_x = signed_peak(ky, kx, ny, nx)

    return -int(peak_y), -int(peak_x)


def phase_corr_subpixel(xp, fft, fixed, moving):
    """Subpixel phase-correlation shift estimate."""
    ny, nx = fixed.shape[-2:]

    fa = fft.fft2(fixed, axes=(-2, -1))
    fb = fft.fft2(moving, axes=(-2, -1))

    cps = fb * fa.conj()
    cps *= 1.0 / (xp.abs(cps) + _EPS)

    corr = fft.ifft2(cps, axes=(-2, -1))
    mag = xp.abs(corr)

    idx = xp.argmax(mag)
    ky, kx = xp.unravel_index(idx, mag.shape)
    ky, kx = int(ky), int(kx)

    peak_y, peak_x = signed_peak(ky, kx, ny, nx)

    sub_y = subpixel_parabola(
        mag[(ky - 1) % ny, kx],
        mag[ky, kx],
        mag[(ky + 1) % ny, kx],
    )
    sub_x = subpixel_parabola(
        mag[ky, (kx - 1) % nx],
        mag[ky, kx],
        mag[ky, (kx + 1) % nx],
    )

    return -(peak_y + sub_y), -(peak_x + sub_x)


def fourier_magnitude(xp, fft, img, dc_radius_factor=32):
    """Fourier magnitude with DC component removal."""
    mag = xp.abs(fft.fftshift(fft.fft2(img, axes=(-2, -1))))
    mag = xp.log1p(mag)

    ny, nx = mag.shape[-2:]
    cy, cx = ny // 2, nx // 2
    r = max(4, min(ny, nx) // dc_radius_factor)

    yy, xx = xp.ogrid[:ny, :nx]
    dc_mask = (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2

    mag[dc_mask] = 0
    return mag


def logpolar_transform(xp, ndi, img, radial_bins, angular_bins):
    """Log-polar transform for rotation/scale estimation."""
    ny, nx = img.shape[-2:]
    cy, cx = (ny - 1) * 0.5, (nx - 1) * 0.5

    max_radius = min(cx, cy)

    log_r = xp.linspace(0.0, xp.log(max_radius), radial_bins, dtype=xp.float32)
    theta = xp.linspace(
        0.0,
        2.0 * xp.pi,
        angular_bins,
        endpoint=False,
        dtype=xp.float32,
    )

    rr = xp.exp(log_r)[:, None]
    tt = theta[None, :]

    yy = cy + rr * xp.sin(tt)
    xx = cx + rr * xp.cos(tt)

    coords = xp.stack((yy, xx), axis=0)

    return ndi.map_coordinates(img, coords, order=1, mode="constant", cval=0.0)


def estimate_rotation_scale(
    xp,
    fft,
    ndi,
    fixed,
    moving,
    radial_bins=256,
    angular_bins=360,
):
    """Estimate rotation angle and scale factor."""
    fixed_mag = fourier_magnitude(xp, fft, fixed)
    moving_mag = fourier_magnitude(xp, fft, moving)

    fixed_lp = logpolar_transform(xp, ndi, fixed_mag, radial_bins, angular_bins)
    moving_lp = logpolar_transform(xp, ndi, moving_mag, radial_bins, angular_bins)

    d_r, d_theta = phase_corr_subpixel(xp, fft, fixed_lp, moving_lp)

    angle_deg = -d_theta * 360.0 / angular_bins

    max_radius = min(fixed.shape[-1], fixed.shape[-2]) * 0.5
    log_base = xp.log(max_radius) / radial_bins
    scale = xp.exp(d_r * log_base)

    return float(angle_deg), float(scale)


def apply_rotation_scale(xp, ndi, img, angle_deg, scale):
    """Apply rotation and scaling to image."""
    ny, nx = img.shape[-2:]
    cy, cx = (ny - 1) * 0.5, (nx - 1) * 0.5

    angle = xp.deg2rad(angle_deg)
    c = float(xp.cos(angle))
    s = float(xp.sin(angle))

    inv_scale = 1.0 / scale

    matrix = xp.asarray(
        (
            (c * inv_scale, s * inv_scale),
            (-s * inv_scale, c * inv_scale),
        ),
        dtype=xp.float32,
    )

    center = xp.asarray((cy, cx), dtype=xp.float32)
    offset = center - matrix @ center

    out = ndi.affine_transform(
        img,
        matrix,
        offset=offset,
        order=1,
        mode="nearest",
    )

    return out.astype(img.dtype, copy=False)


def apply_shifts(
    xp,
    fft,
    img,
    shift_y,
    shift_x,
    method="fourier",
    integer=False,
):
    """
    Apply translation.

    Parameters
    ----------
    method : {"fourier", "roll"}
        "fourier" gives subpixel translation.
        "roll" uses integer xp.roll and is much faster.
    integer : bool
        If True, round shifts to int before applying.
    """
    if integer or method == "roll":
        sy = int(round(float(shift_y)))
        sx = int(round(float(shift_x)))
        return xp.roll(img, shift=(sy, sx), axis=(-2, -1))

    ny, nx = img.shape[-2:]

    fy = fft.fftfreq(ny).reshape(ny, 1)
    fx = fft.fftfreq(nx).reshape(1, nx)

    phase = xp.exp(-2j * xp.pi * (fy * shift_y + fx * shift_x))

    out = fft.ifft2(
        fft.fft2(img, axes=(-2, -1)) * phase,
        axes=(-2, -1),
    )

    if xp.isrealobj(img):
        out = out.real

    return out.astype(img.dtype, copy=False)


def apply_registration(
    xp,
    fft,
    ndi,
    img,
    reg,
    integer_translation=False,
    translation_method=None,
):
    """
    Apply a registration tuple to an image.

    reg can be:
        (shift_y, shift_x)
        (shift_y, shift_x, angle_deg, scale)
    """
    if len(reg) == 2:
        shift_y, shift_x = reg
        angle_deg = 0.0
        scale = 1.0
    elif len(reg) == 4:
        shift_y, shift_x, angle_deg, scale = reg
    else:
        raise ValueError("reg must have 2 or 4 elements.")

    out = img

    if angle_deg != 0.0 or scale != 1.0:
        out = apply_rotation_scale(xp, ndi, out, angle_deg, scale)

    if translation_method is None:
        translation_method = "roll" if integer_translation else "fourier"

    out = apply_shifts(
        xp,
        fft,
        out,
        shift_y,
        shift_x,
        method=translation_method,
        integer=integer_translation,
    )

    return out

def apply_registration3D(
    xp,
    fft,
    ndi,
    img3D,
    reg,
    integer_translation=False,
    translation_method=None,
):
    """
    Apply a registration tuple to every image of a 3D image.

    reg can be:
        (shift_y, shift_x)
        (shift_y, shift_x, angle_deg, scale)
    """
    if len(reg) == 2:
        shift_y, shift_x = reg
        angle_deg = 0.0
        scale = 1.0
    elif len(reg) == 4:
        shift_y, shift_x, angle_deg, scale = reg
    else:
        raise ValueError("reg must have 2 or 4 elements.")

    for i in range(img3D.shape[0]):
        img3D[i] = apply_registration(xp,fft,ndi,img3D[i],reg,integer_translation=integer_translation,translation_method=translation_method)

    return img3D