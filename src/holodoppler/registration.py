import numpy as np

class ImageRegistration:
    """Image registration using phase correlation for Translation, Rotation, and Scale (TRS)."""

    def __init__(self, backend_manager):
        self.bm = backend_manager

    @staticmethod
    def _xcorr2_fft(fa, fb, xp):
        """Cross-correlation via FFT. Expects FFT-transformed images."""
        return xp.fft.ifft2(fa * xp.conj(fb))

    def _phase_corr_subpixel(self, a, b):
        """Subpixel phase correlation estimation."""
        xp = self.bm.xp
        ny, nx = a.shape[-2:]

        fa = xp.fft.fft2(a)
        fb = xp.fft.fft2(b)

        cps = fb * fa.conj()
        cps /= (xp.abs(cps) + 1e-12)

        corr = xp.fft.ifft2(cps)
        mag = xp.abs(corr)

        idx = xp.argmax(mag)
        ky, kx = xp.unravel_index(idx, mag.shape)
        ky, kx = int(ky), int(kx)

        from .utils import signed_peak, subpixel_parabola
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

    def apply_shifts(self, img, shift_y, shift_x):
        """Apply translation using Fourier phase shift."""
        xp = self.bm.xp
        ny, nx = img.shape[-2:]

        fy = xp.fft.fftfreq(ny).reshape(ny, 1)
        fx = xp.fft.fftfreq(nx).reshape(1, nx)

        phase = xp.exp(-2j * xp.pi * (fy * shift_y + fx * shift_x))

        out = xp.fft.ifft2(
            xp.fft.fft2(img, axes=(-2, -1)) * phase,
            axes=(-2, -1),
        )

        if xp.isrealobj(img):
            out = out.real

        return out.astype(img.dtype, copy=False)

    def _logpolar_transform(self, img, radial_bins, angular_bins):
        """Log-polar transform for rotation/scale estimation."""
        xp = self.bm.xp
        ny, nx = img.shape
        cy, cx = (ny - 1) * 0.5, (nx - 1) * 0.5

        max_radius = min(cx, cy)
        log_r = xp.linspace(0.0, xp.log(max_radius), radial_bins)
        theta = xp.linspace(0.0, 2.0 * xp.pi, angular_bins, endpoint=False)

        rr = xp.exp(log_r).reshape(-1, 1)
        tt = theta.reshape(1, -1)

        yy = cy + rr * xp.sin(tt)
        xx = cx + rr * xp.cos(tt)

        coords = xp.stack([yy, xx], axis=0)
        # Uses the pre-initialized self.ndimage
        return self.bm.ndi.map_coordinates(img, coords, order=1, mode="constant", cval=0.0)

    def _fourier_magnitude(self, img, dc_radius_factor=32):
        """Fourier magnitude with DC component removal."""
        xp = self.bm.xp
        mag = xp.abs(xp.fft.fftshift(xp.fft.fft2(img)))
        mag = xp.log1p(mag)

        ny, nx = mag.shape
        cy, cx = ny // 2, nx // 2
        r = max(4, min(ny, nx) // dc_radius_factor)
        
        yy, xx = xp.ogrid[:ny, :nx]
        dc_mask = (yy - cy)**2 + (xx - cx)**2 <= r**2
        
        mag[dc_mask] = 0
        return mag

    def estimate_rotation_scale(self, fixed, moving, radial_bins=256, angular_bins=360):
        """Estimate rotation angle and scale factor."""
        xp = self.bm.xp

        fixed_mag = self._fourier_magnitude(fixed)
        moving_mag = self._fourier_magnitude(moving)

        fixed_lp = self._logpolar_transform(fixed_mag, radial_bins, angular_bins)
        moving_lp = self._logpolar_transform(moving_mag, radial_bins, angular_bins)

        d_r, d_theta = self._phase_corr_subpixel(fixed_lp, moving_lp)

        angle_deg = -d_theta * 360.0 / angular_bins
        max_radius = min(fixed.shape[-1], fixed.shape[-2]) * 0.5
        log_base = xp.log(max_radius) / radial_bins
        scale = float(xp.exp(d_r * log_base))

        return float(angle_deg), scale

    def apply_rotation_scale(self, img, angle_deg, scale):
        """Apply rotation and scaling to image."""
        xp = self.bm.xp
        ny, nx = img.shape[-2:]
        cy, cx = (ny - 1) * 0.5, (nx - 1) * 0.5

        angle = xp.deg2rad(angle_deg)
        c, s = float(xp.cos(angle)), float(xp.sin(angle))

        matrix = xp.asarray([
            [c / scale, s / scale],
            [-s / scale, c / scale],
        ], dtype=xp.float32)

        center = xp.asarray([cy, cx], dtype=xp.float32)
        offset = center - matrix @ center

        # Uses the pre-initialized self.ndimage
        out = self.bm.ndi.affine_transform(img, matrix, offset=offset, order=1, mode="nearest")
        return out.astype(img.dtype)

    def apply_registration(self, img, reg):
        """
        Apply a registration tuple to an image.

        Parameters
        ----------
        img : array (numpy or cupy)
        reg : tuple
            (shift_y, shift_x, angle_deg, scale)
            or (shift_y, shift_x) for translation-only
        """
        xp = self.bm.xp
        
        # Parse registration tuple
        if len(reg) == 2:
            shift_y, shift_x = reg
            angle_deg = 0.0
            scale = 1.0
        elif len(reg) == 4:
            shift_y, shift_x, angle_deg, scale = reg
        else:
            raise ValueError("Registration tuple 'reg' must have 2 or 4 elements.")

        out = img

        # 1. Apply rotation + scale first
        if angle_deg != 0.0 or scale != 1.0:
            out = self.apply_rotation_scale(out, angle_deg, scale)

        # 2. Apply translation shifts last
        out = self.apply_shifts(out, shift_y, shift_x)

        return out

    def register_trs(self, fixed, moving, radius=None, estimate_similarity=True,
                     radial_bins=256, angular_bins=360, return_registered=False):
        """Full TRS (Translation, Rotation, Scale) registration."""
        xp = self.bm.xp
        ny, nx = fixed.shape

        from .utils import elliptical_mask

        mask = elliptical_mask(ny, nx, radius, xp) if radius else xp.ones((ny, nx), dtype=bool)

        fixed_f = fixed.astype(xp.float32)
        moving_f = moving.astype(xp.float32)

        fixed_c = (fixed_f - xp.mean(fixed_f[mask])) * mask
        moving_c = (moving_f - xp.mean(moving_f[mask])) * mask

        if estimate_similarity:
            angle_deg, scale = self.estimate_rotation_scale(fixed_c, moving_c, radial_bins, angular_bins)
            moving_rs = self.apply_rotation_scale(moving_f, angle_deg, scale)
            moving_rs_c = (moving_rs - xp.mean(moving_rs[mask])) * mask
        else:
            angle_deg, scale = 0.0, 1.0
            moving_rs = moving_f
            moving_rs_c = moving_c

        shift_y, shift_x = self._phase_corr_subpixel(fixed_c, moving_rs_c)

        if not return_registered:
            return shift_y, shift_x, angle_deg, scale

        # Use the apply_registration helper for a clean final step
        reg_tuple = (shift_y, shift_x, angle_deg, scale)
        moving_registered = self.apply_registration(moving_f, reg_tuple)
        
        return shift_y, shift_x, angle_deg, scale, moving_registered