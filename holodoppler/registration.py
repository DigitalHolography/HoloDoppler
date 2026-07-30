"""
Image registration using phase correlation for Translation, Rotation, and Scale (TRS).
"""

from .utils import elliptical_mask, signed_peak, subpixel_parabola


def register_images_shifts(
    xp,
    fft,
    fixed,
    moving,
    radius=None
):
    ny, nx = fixed.shape[-2:]
    # print(radius)
    if radius is not None and isinstance(radius, tuple):

        r1, r2 = radius
        m1 = ~elliptical_mask(ny, nx, r1, xp)
        m2 = elliptical_mask(ny, nx, r2, xp)
        mask = m1 & m2

    else:
        mask = elliptical_mask(ny, nx, radius, xp) if radius else None

    fixed_f = fixed.astype(xp.float32, copy=False)
    moving_f = moving.astype(xp.float32, copy=False)

    fixed_e = _preprocess(
        xp,
        fixed_f,
        mask=mask
    )
    moving_e = _preprocess(
        xp,
        moving_f,
        mask=mask
    )

    shift_y, shift_x = intensity_corr_sub_pixel(xp, fft, fixed_e, moving_e)

    return shift_y, shift_x


def apply_register_images_shifts(xp, fft, image, shift_y, shift_x):
    if isinstance(shift_y, int) and isinstance(shift_x, int):
        return xp.roll(xp.roll(image, shift_y, axis=-2), shift_x, axis=-1)
    else:
        ny, nx = image.shape[-2:]

        fy = fft.fftfreq(ny).reshape(ny, 1)
        fx = fft.fftfreq(nx).reshape(1, nx)

        phase = xp.exp(-2j * xp.pi * (fy * shift_y + fx * shift_x))

        out = fft.ifft2(
            fft.fft2(image, axes=(-2, -1)) * phase,
            axes=(-2, -1),
        )

        return xp.real(out)


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


def intensity_corr_sub_pixel(xp, fft, fixed, moving):
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


def logpolar_transform(xp, ndi, img, radial_bins, angular_bins):
    """Log-polar transform for rotation/scale estimation."""
    ny, nx = img.shape[-2:]
    cy, cx = (ny - 1) * 0.5, (nx - 1) * 0.5

    max_radius = min(nx, ny) /2

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

    return ndi.map_coordinates(img, coords, order=3, mode="constant", cval=0.0)


# ---------------- functions in tests


def register_laplacian(xp, fft, video, radius=None, gauge="minimal", ref_frame=0):
    nt, ny, nx = video.shape

    # Precompute mask and preprocess all frames
    mask = elliptical_mask(ny, nx, radius, xp) if radius else None
    preprocessed = xp.zeros((nt, ny, nx), dtype=xp.float32)
    for k in range(nt):
        frame = video[k].astype(xp.float32, copy=False)
        preprocessed[k] = _preprocess(xp, frame, mask=mask)

    # Compute pairwise shifts (upper triangle only)
    shifts_y = xp.zeros((nt, nt), dtype=xp.float32)
    shifts_x = xp.zeros((nt, nt), dtype=xp.float32)
    count = xp.zeros((nt, nt), dtype=xp.float32)

    for k in range(nt):
        for m in range(k + 1, nt):
            shift_y, shift_x = intensity_corr_integer(
                xp, fft, preprocessed[k], preprocessed[m]
            )
            shifts_y[k, m] = shift_y
            shifts_x[k, m] = shift_x
            shifts_y[m, k] = -shift_y  # Inverse relation
            shifts_x[m, k] = -shift_x
            count[k, m] = 1
            count[m, k] = 1

    # Solve for shifts using least squares
    # We want to find s_i such that s_i - s_j = d_ij (where d_ij are pairwise shifts)
    # This is a linear system that can be solved by averaging

    # For each frame, compute average shift relative to all others
    sum_y = xp.sum(shifts_y, axis=1)
    sum_x = xp.sum(shifts_x, axis=1)
    row_counts = xp.sum(count, axis=1)

    # Avoid division by zero
    row_counts = xp.maximum(row_counts, 1)

    raw_shifts_y = sum_y / row_counts
    raw_shifts_x = sum_x / row_counts

    # Apply gauge choice
    if gauge == "minimal":
        # Center shifts to minimize L2 norm (zero mean)
        mean_y = xp.mean(raw_shifts_y)
        mean_x = xp.mean(raw_shifts_x)
        shifts_y_final = raw_shifts_y - mean_y
        shifts_x_final = raw_shifts_x - mean_x

    elif gauge == "reference":
        # Relative to reference frame
        shifts_y_final = raw_shifts_y - raw_shifts_y[ref_frame]
        shifts_x_final = raw_shifts_x - raw_shifts_x[ref_frame]

    else:
        raise ValueError(f"gauge must be 'minimal' or 'reference', got '{gauge}'")

    return shifts_y_final, shifts_x_final

def crop_inscribed_rectangle(xp, img, radius):

    if radius is None:
        return img

    ny, nx = img.shape[-2:]

    if isinstance(radius, tuple):
        ry_frac, rx_frac = radius
    else:
        ry_frac = rx_frac = radius

    cy = ny // 2
    cx = nx // 2

    # ellipse semi-axes (pixels)
    ry = ry_frac * ny / 2
    rx = rx_frac * nx / 2

    # inscribed rectangle half sizes
    hy = int(ry / xp.sqrt(2))
    hx = int(rx / xp.sqrt(2))

    return img[
        cy - hy : cy + hy,
        cx - hx : cx + hx,
    ]

def register_rotation_scale(
    xp,
    fft,
    ndi,
    fixed,
    moving,
    radius=None,
    radial_bins=None,
    angular_bins=360 * 2,
):

    fixed_f = fixed.astype(xp.float32, copy=False)
    moving_f = moving.astype(xp.float32, copy=False)

    fixed_e = crop_inscribed_rectangle(xp, fixed_f, radius)
    moving_e = crop_inscribed_rectangle(xp, moving_f, radius)

    ny, nx = fixed_e.shape[-2:]

    if radial_bins is None:
        radial_bins = min(ny, nx) // 2

    # Optional Hann window
    # wy = xp.hanning(ny)
    # wx = xp.hanning(nx)
    # window = wy[:, None] * wx[None, :]
    # fixed_e *= window
    # moving_e *= window

    F_fixed = xp.abs(fft.fftshift(fft.fft2(fixed_e)))
    F_moving = xp.abs(fft.fftshift(fft.fft2(moving_e)))

    # # Radial high-pass weighting
    # yy, xx = xp.mgrid[:ny, :nx]
    # cy = (ny - 1) / 2
    # cx = (nx - 1) / 2

    # rr = xp.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)

    # F_fixed *= rr
    # F_moving *= rr

    LP_fixed = logpolar_transform(
        xp,
        ndi,
        F_fixed,
        radial_bins,
        angular_bins,
    )

    LP_moving = logpolar_transform(
        xp,
        ndi,
        F_moving,
        radial_bins,
        angular_bins,
    )

    # Optional:
    # cut = radial_bins // 10
    # LP_fixed = LP_fixed[cut:]
    # LP_moving = LP_moving[cut:]

    dr, dtheta = intensity_corr_sub_pixel(
        xp,
        fft,
        LP_fixed,
        LP_moving,
    )

    angle = -360.0 * dtheta / angular_bins

    max_radius = min(nx, ny) /2
    log_step = xp.log(max_radius) / (radial_bins - 1)
    scale = float(xp.exp(dr * log_step))

    return angle, scale


def translation_matrix(xp, ty, tx):
    M = xp.eye(3, dtype=xp.float32)
    M[0, 2] = tx
    M[1, 2] = ty
    return M


def rotation_scale_matrix(xp, angle_deg, scale):
    theta = xp.deg2rad(angle_deg)

    c = xp.cos(theta) * scale
    s = xp.sin(theta) * scale

    M = xp.eye(3, dtype=xp.float32)

    M[0, 0] = c
    M[0, 1] = -s
    M[1, 0] = s
    M[1, 1] = c

    return M


def registration(
    xp,
    fft,
    ndi,
    fixed,
    moving,
    registration_mode="TL",
    radius = None,
):
    """
    Returns
    -------
    registered : ndarray
    M : (3,3) homogeneous transform matrix

    M maps the ORIGINAL moving image onto the registered image.
    """

    ny,nx = fixed.shape[-2:]

    registered = moving.copy()

    M = xp.eye(3, dtype=xp.float32)

    for op in registration_mode.upper():

        if op == "T":

            ty, tx = register_images_shifts(
                xp,
                fft,
                fixed,
                registered,
                radius=radius
            )

            registered = apply_register_images_shifts(
                xp,
                fft,
                registered,
                ty,
                tx,
            )

            T = translation_matrix(xp, ty, tx)

            # compose
            M = T @ M

        elif op == "L":

            angle, scale = register_rotation_scale(
                xp,
                fft,
                ndi,
                fixed,
                registered,
                radius=radius
            )

            registered = apply_rotation_scale(
                xp,
                ndi,
                registered,
                angle,
                scale,
            )

            L = rotation_scale_matrix(
                xp,
                angle,
                scale,
            )

            cy = (ny - 1) / 2.0
            cx = (nx - 1) / 2.0

            Tc = xp.array([[1,0,-cx],
                        [0,1,-cy],
                        [0,0,1]], dtype=xp.float32)

            Tc_inv = xp.array([[1,0,cx],
                            [0,1,cy],
                            [0,0,1]], dtype=xp.float32)

            L = Tc_inv @ rotation_scale_matrix(xp, angle, scale) @ Tc # rotation scale is centered when usinf rotation

            M = L @ M

        else:

            raise ValueError(f"Unknown registration mode '{op}'")

    return registered, M


def registration_apply(
    xp,
    ndi,
    image,
    M,
    order=3,
    mode="mirror", # other option could be "constant" or "reflect"
    cval=0.0,
):
    """
    Apply a registration matrix returned by registration().

    Parameters
    ----------
    image : ndarray
    M : (3,3)
        Homogeneous transform returned by registration().
    """

    ny, nx = image.shape[-2:]

    cy = (ny - 1) / 2.0
    cx = (nx - 1) / 2.0

    Tc = xp.array(
        [
            [1, 0, -cx],
            [0, 1, -cy],
            [0, 0, 1],
        ],
        dtype=xp.float32,
    )

    Tc_inv = xp.array(
        [
            [1, 0, cx],
            [0, 1, cy],
            [0, 0, 1],
        ],
        dtype=xp.float32,
    )

    # rotate/scale about image centre
    M_center = Tc_inv @ M @ Tc

    # affine_transform expects output->input mapping
    A = xp.linalg.inv(M_center)

    matrix = A[:2, :2]
    offset = A[:2, 2]
    offset = offset[::-1]

    return ndi.affine_transform(
        image,
        matrix,
        offset=offset,
        order=order,
        mode=mode,
        cval=cval,
    )

def matrix_to_trs(xp, M):
    """
    Recover translation, rotation and isotropic scale from a
    homogeneous 3x3 similarity transform.

    Returns
    -------
    ty : float
    tx : float
    rot : float   # degrees
    scale : float
    """

    tx = float(M[0, 2])
    ty = float(M[1, 2])

    a = M[0, 0]
    c = M[1, 0]

    # isotropic scale
    scale = float(xp.sqrt(a * a + c * c))

    # rotation
    rot = float(xp.rad2deg(xp.arctan2(c, a)))

    return xp.array([ty, tx, rot, scale]).astype(xp.float32)


# ---------------- deprecated (keep for compatibility)

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


def fourier_magnitude(xp, fft, img, dc_radius_factor=32):
    """Fourier magnitude with DC component removal."""
    mag = xp.abs(fft.fftshift(fft.fft2(img, axes=(-2, -1))))
    mag = xp.log1p(mag)

    ny, nx = mag.shape[-2:]
    cy, cx = ny // 2, nx // 2
    r = max(4, min(ny, nx) // dc_radius_factor)

    yy, xx = xp.ogrid[:ny, :nx]
    dc_mask = (yy - cy) ** 2 + (xx - cx) ** 2 <= r**2

    mag[dc_mask] = 0
    return mag


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
        order=3,
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
        img3D[i] = apply_registration(
            xp,
            fft,
            ndi,
            img3D[i],
            reg,
            integer_translation=integer_translation,
            translation_method=translation_method,
        )

    return img3D
