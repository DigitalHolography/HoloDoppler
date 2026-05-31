"""
Zernike polynomial generation and wavefront reconstruction
"""
from functools import cache

@cache
def get_zernike_mode(xp, mode_index, Nx, Ny, radius=2.0):
    """Generate Zernike mode on a grid"""
    
    if Nx > Ny:
        x = xp.linspace(-Nx / Ny, Nx / Ny, Nx)
        y = xp.linspace(-1, 1, Ny)
    else:
        x = xp.linspace(-1, 1, Nx)
        y = xp.linspace(-Ny / Nx, Ny / Nx, Ny)
    
    X, Y = xp.meshgrid(x, y)
    R = xp.sqrt(X**2 + Y**2)
    Theta = xp.arctan2(Y, X)
    
    Z = xp.full_like(R, xp.nan)
    mask = R <= radius
    
    if mode_index == 1:      # Piston
        Z[mask] = 1
    elif mode_index == 2:    # Tilt X
        Z[mask] = 2 * X[mask]
    elif mode_index == 3:    # Tilt Y
        Z[mask] = 2 * Y[mask]
    elif mode_index == 4:    # Defocus
        Z[mask] = xp.sqrt(3) * (2 * R[mask]**2 - 1)
    elif mode_index == 5:    # Astigmatism 45°
        Z[mask] = xp.sqrt(6) * R[mask]**2 * xp.sin(2 * Theta[mask])
    elif mode_index == 6:    # Astigmatism 0°
        Z[mask] = xp.sqrt(6) * R[mask]**2 * xp.cos(2 * Theta[mask])
    elif mode_index == 7:    # Coma Y
        Z[mask] = xp.sqrt(8) * (3*R[mask]**3 - 2*R[mask]) * xp.sin(Theta[mask])
    elif mode_index == 8:    # Coma X
        Z[mask] = xp.sqrt(8) * (3*R[mask]**3 - 2*R[mask]) * xp.cos(Theta[mask])
    elif mode_index == 9:    # Trefoil Y
        Z[mask] = xp.sqrt(8) * R[mask]**3 * xp.sin(3 * Theta[mask])
    elif mode_index == 10:   # Trefoil X
        Z[mask] = xp.sqrt(8) * R[mask]**3 * xp.cos(3 * Theta[mask])
    elif mode_index == 11:   # Spherical
        Z[mask] = xp.sqrt(5) * (6*R[mask]**4 - 6*R[mask]**2 + 1)
    elif mode_index == 12:   # Astigmatism higher 0°
        Z[mask] = xp.sqrt(10) * (4*R[mask]**4 - 3*R[mask]**2) * xp.cos(2 * Theta[mask])
    elif mode_index == 13:   # Astigmatism higher 45°
        Z[mask] = xp.sqrt(10) * (4*R[mask]**4 - 3*R[mask]**2) * xp.sin(2 * Theta[mask])
    elif mode_index == 14:   # Quadrafoil X
        Z[mask] = xp.sqrt(10) * R[mask]**4 * xp.cos(4 * Theta[mask])
    elif mode_index == 15:   # Quadrafoil Y
        Z[mask] = xp.sqrt(10) * R[mask]**4 * xp.sin(4 * Theta[mask])
    elif mode_index == 16:   # Secondary coma X
        Z[mask] = xp.sqrt(12) * (10*R[mask]**5 - 12*R[mask]**3 + 3*R[mask]) * xp.cos(Theta[mask])
    elif mode_index == 17:   # Secondary coma Y
        Z[mask] = xp.sqrt(12) * (10*R[mask]**5 - 12*R[mask]**3 + 3*R[mask]) * xp.sin(Theta[mask])
    elif mode_index == 18:   # Secondary trefoil X
        Z[mask] = xp.sqrt(12) * (5*R[mask]**5 - 4*R[mask]**3) * xp.cos(3 * Theta[mask])
    elif mode_index == 19:   # Secondary trefoil Y
        Z[mask] = xp.sqrt(12) * (5*R[mask]**5 - 4*R[mask]**3) * xp.sin(3 * Theta[mask])
    elif mode_index == 20:   # Pentafoil X
        Z[mask] = xp.sqrt(12) * R[mask]**5 * xp.cos(5 * Theta[mask])
    elif mode_index == 21:   # Pentafoil Y
        Z[mask] = xp.sqrt(12) * R[mask]**5 * xp.sin(5 * Theta[mask])
    else:
        raise ValueError(f"Mode index {mode_index} not implemented")
    
    return Z.astype(xp.float32)

@cache
def make_gradient_matrix(xp, zernike_modes, nysubabs, nxsubabs, nx, ny, pixel_pitch_x, pixel_pitch_y, wavelength):
    n_modes = len(zernike_modes)
    G = xp.zeros((2, nysubabs, nxsubabs, n_modes), dtype=xp.float32)
    
    for k, idx in enumerate(zernike_modes):
        Z = get_zernike_mode(xp, idx, nx, ny, radius=2)
        
        dZdx = xp.gradient(Z, pixel_pitch_x, axis=1)
        dZdy = xp.gradient(Z, pixel_pitch_y, axis=0)
        
        sub_ny = ny // nysubabs
        sub_nx = nx // nxsubabs
        
        for iy in range(nysubabs):
            y_start = iy * sub_ny
            y_end = y_start + sub_ny
            for ix in range(nxsubabs):
                x_start = ix * sub_nx
                x_end = x_start + sub_nx
                dZdx_subap = dZdx[y_start:y_end, x_start:x_end]
                dZdy_subap = dZdy[y_start:y_end, x_start:x_end]
                G[0, iy, ix, k] = xp.nanmean(dZdy_subap)
                G[1, iy, ix, k] = xp.nanmean(dZdx_subap)
    
    G *= wavelength / (2 * xp.pi)
    return G

def fit_zernike(xp, ny, nx, pixel_pitch_y, pixel_pitch_x, wavelength,
                shifts_y, shifts_x, zernike_modes):
    """Fit Zernike polynomials to displacement data"""
    
    nysubabs, nxsubabs = shifts_y.shape
    
    slopes_y = (shifts_y) * wavelength / (pixel_pitch_y * (ny // nysubabs)) # z / z
    slopes_x = (shifts_x) * wavelength / (pixel_pitch_x * (nx // nxsubabs)) # z / z
    
    s = xp.stack([slopes_y, slopes_x])
    
    # Build gradient matrix
    G = make_gradient_matrix(xp, zernike_modes, nysubabs, nxsubabs, nx, ny, pixel_pitch_x, pixel_pitch_y, wavelength)
    
    # Solve linear system
    n_modes = len(zernike_modes)
    A = G.reshape(-1, n_modes)
    b = s.reshape(-1)
    valid = ~xp.isnan(b) & ~xp.isnan(A).any(1)
    
    coefs, _, _, _ = xp.linalg.lstsq(A[valid], b[valid], rcond=None)
    
    # Reconstruct phase
    phase = xp.zeros((ny, nx), dtype=xp.float32)
    for idx, coef in zip(zernike_modes, coefs):
        Z = get_zernike_mode(xp, idx, nx, ny, radius=2)
        phase += coef * Z
    
    return coefs.astype(xp.float32), phase.astype(xp.float32)

def southwell_phase_integration(
    bm,
    ny,
    nx,
    pixel_pitch_y,
    pixel_pitch_x,
    wavelength,
    shifts_y,
    shifts_x,
    ):
    """NaN-robust Southwell phase reconstruction using a DCT Poisson solver."""

    xp = bm.xp
    xp_name = getattr(xp, "__name__", "")

    if xp_name == "numpy":
        shifts_y = bm._to_numpy(shifts_y)
        shifts_x = bm._to_numpy(shifts_x)
        
    zoom = bm.zoom
    fft = bm.fft

    def dct2(a):
        return fft.dct(fft.dct(a, axis=0, norm="ortho"), axis=1, norm="ortho")

    def idct2(a):
        return fft.idct(fft.idct(a, axis=1, norm="ortho"), axis=0, norm="ortho")

    def southwell_poisson_nan(slope_y, slope_x):
        rows, cols = slope_y.shape
        dtype = xp.result_type(slope_y.dtype, slope_x.dtype, xp.float32)

        mask_x = xp.isfinite(slope_x)
        mask_y = xp.isfinite(slope_y)

        div = xp.zeros((rows, cols), dtype=dtype)

        valid_x = mask_x[:, :-1]
        sx = xp.where(valid_x, slope_x[:, :-1], 0.0)
        div[:, :-1] += sx
        div[:, 1:] -= sx

        valid_y = mask_y[:-1, :]
        sy = xp.where(valid_y, slope_y[:-1, :], 0.0)
        div[:-1, :] += sy
        div[1:, :] -= sy

        valid = xp.zeros((rows, cols), dtype=bool)
        valid[:, :-1] |= valid_x
        valid[:, 1:] |= valid_x
        valid[:-1, :] |= valid_y
        valid[1:, :] |= valid_y

        div = xp.where(valid, div, 0.0)

        div_hat = dct2(div)

        ky = xp.arange(rows, dtype=dtype)
        kx = xp.arange(cols, dtype=dtype)

        cy = xp.cos(xp.pi * ky / rows)
        cx = xp.cos(xp.pi * kx / cols)

        eig = 2.0 * (cy[:, None] + cx[None, :] - 2.0)
        eig[0, 0] = 1.0

        phi_hat = div_hat / eig
        phi_hat[0, 0] = 0.0

        phi = idct2(phi_hat)
        phi = xp.where(valid, phi, xp.nan)

        return phi

    def resize_nan(phi, out_rows, out_cols, order=1):
        phi = phi.reshape(phi.shape[-2], phi.shape[-1])

        mask = xp.isfinite(phi)
        phi_filled = xp.where(mask, phi, 0.0)

        zoom_y = out_rows / phi.shape[0]
        zoom_x = out_cols / phi.shape[1]

        phi_zoom = zoom(phi_filled, (zoom_y, zoom_x), order=order)
        mask_zoom = zoom(mask.astype(xp.float32), (zoom_y, zoom_x), order=order)

        phi_zoom = phi_zoom / xp.maximum(mask_zoom, 1e-6)
        phi_zoom = xp.where(mask_zoom > 0.1, phi_zoom, xp.nan)

        return phi_zoom.reshape(out_rows, out_cols)

    # Keep your original calibration convention.
    # Note: pixel_pitch_y and pixel_pitch_x are currently unused.
    slopes_y = shifts_y * wavelength
    slopes_x = shifts_x * wavelength

    phase = southwell_poisson_nan(slopes_y, slopes_x)
    phase = phase * (2.0 * xp.pi / wavelength)
    phase = resize_nan(phase, ny, nx)

    return phase


"""
Zernike polynomial generation and wavefront reconstruction
"""

import numpy as np

class ZernikeReconstructor:
    """Zernike polynomial-based wavefront reconstruction"""
    
    def __init__(self, backend_manager):
        self.bm = backend_manager
    
    def get_zernike_mode(self, mode_index, Nx, Ny, radius=2.0):
        """Generate Zernike mode on a grid"""
        xp = self.bm.xp
        
        if Nx > Ny:
            x = xp.linspace(-Nx / Ny, Nx / Ny, Nx)
            y = xp.linspace(-1, 1, Ny)
        else:
            x = xp.linspace(-1, 1, Nx)
            y = xp.linspace(-Ny / Nx, Ny / Nx, Ny)
        
        X, Y = xp.meshgrid(x, y)
        R = xp.sqrt(X**2 + Y**2)
        Theta = xp.arctan2(Y, X)
        
        Z = xp.full_like(R, xp.nan)
        mask = R <= radius
        
        if mode_index == 1:      # Piston
            Z[mask] = 1
        elif mode_index == 2:    # Tilt X
            Z[mask] = 2 * X[mask]
        elif mode_index == 3:    # Tilt Y
            Z[mask] = 2 * Y[mask]
        elif mode_index == 4:    # Defocus
            Z[mask] = xp.sqrt(3) * (2 * R[mask]**2 - 1)
        elif mode_index == 5:    # Astigmatism 45°
            Z[mask] = xp.sqrt(6) * R[mask]**2 * xp.sin(2 * Theta[mask])
        elif mode_index == 6:    # Astigmatism 0°
            Z[mask] = xp.sqrt(6) * R[mask]**2 * xp.cos(2 * Theta[mask])
        elif mode_index == 7:    # Coma Y
            Z[mask] = xp.sqrt(8) * (3*R[mask]**3 - 2*R[mask]) * xp.sin(Theta[mask])
        elif mode_index == 8:    # Coma X
            Z[mask] = xp.sqrt(8) * (3*R[mask]**3 - 2*R[mask]) * xp.cos(Theta[mask])
        elif mode_index == 9:    # Trefoil Y
            Z[mask] = xp.sqrt(8) * R[mask]**3 * xp.sin(3 * Theta[mask])
        elif mode_index == 10:   # Trefoil X
            Z[mask] = xp.sqrt(8) * R[mask]**3 * xp.cos(3 * Theta[mask])
        elif mode_index == 11:   # Spherical
            Z[mask] = xp.sqrt(5) * (6*R[mask]**4 - 6*R[mask]**2 + 1)
        elif mode_index == 12:   # Astigmatism higher 0°
            Z[mask] = xp.sqrt(10) * (4*R[mask]**4 - 3*R[mask]**2) * xp.cos(2 * Theta[mask])
        elif mode_index == 13:   # Astigmatism higher 45°
            Z[mask] = xp.sqrt(10) * (4*R[mask]**4 - 3*R[mask]**2) * xp.sin(2 * Theta[mask])
        elif mode_index == 14:   # Quadrafoil X
            Z[mask] = xp.sqrt(10) * R[mask]**4 * xp.cos(4 * Theta[mask])
        elif mode_index == 15:   # Quadrafoil Y
            Z[mask] = xp.sqrt(10) * R[mask]**4 * xp.sin(4 * Theta[mask])
        elif mode_index == 16:   # Secondary coma X
            Z[mask] = xp.sqrt(12) * (10*R[mask]**5 - 12*R[mask]**3 + 3*R[mask]) * xp.cos(Theta[mask])
        elif mode_index == 17:   # Secondary coma Y
            Z[mask] = xp.sqrt(12) * (10*R[mask]**5 - 12*R[mask]**3 + 3*R[mask]) * xp.sin(Theta[mask])
        elif mode_index == 18:   # Secondary trefoil X
            Z[mask] = xp.sqrt(12) * (5*R[mask]**5 - 4*R[mask]**3) * xp.cos(3 * Theta[mask])
        elif mode_index == 19:   # Secondary trefoil Y
            Z[mask] = xp.sqrt(12) * (5*R[mask]**5 - 4*R[mask]**3) * xp.sin(3 * Theta[mask])
        elif mode_index == 20:   # Pentafoil X
            Z[mask] = xp.sqrt(12) * R[mask]**5 * xp.cos(5 * Theta[mask])
        elif mode_index == 21:   # Pentafoil Y
            Z[mask] = xp.sqrt(12) * R[mask]**5 * xp.sin(5 * Theta[mask])
        else:
            raise ValueError(f"Mode index {mode_index} not implemented")
        
        return Z.astype(xp.float32)
    
    def fit_zernike(self, ny, nx, pixel_pitch_y, pixel_pitch_x, wavelength,
                    shifts_y, shifts_x, zernike_modes):
        """Fit Zernike polynomials to displacement data"""
        xp = self.bm.xp
        
        
        nysubabs, nxsubabs = shifts_y.shape
        
        slopes_y = (shifts_y) * wavelength / (pixel_pitch_y * (ny // nysubabs)) # z / z
        slopes_x = (shifts_x) * wavelength / (pixel_pitch_x * (nx // nxsubabs)) # z / z
        
        s = xp.stack([slopes_y, slopes_x])
        
        # Build gradient matrix
        n_modes = len(zernike_modes)
        G = xp.zeros((2, nysubabs, nxsubabs, n_modes), dtype=xp.float32)
        
        for k, idx in enumerate(zernike_modes):
            Z = self.get_zernike_mode(idx, nx, ny, radius=2)
            
            dZdx = xp.gradient(Z, pixel_pitch_x, axis=1)
            dZdy = xp.gradient(Z, pixel_pitch_y, axis=0)
            
            sub_ny = ny // nysubabs
            sub_nx = nx // nxsubabs
            
            for iy in range(nysubabs):
                y_start = iy * sub_ny
                y_end = y_start + sub_ny
                for ix in range(nxsubabs):
                    x_start = ix * sub_nx
                    x_end = x_start + sub_nx
                    dZdx_subap = dZdx[y_start:y_end, x_start:x_end]
                    dZdy_subap = dZdy[y_start:y_end, x_start:x_end]
                    G[0, iy, ix, k] = xp.nanmean(dZdy_subap)
                    G[1, iy, ix, k] = xp.nanmean(dZdx_subap)
        
        G *= wavelength / (2 * xp.pi)
        
        # Solve linear system
        A = G.reshape(-1, n_modes)
        b = s.reshape(-1)
        valid = ~xp.isnan(b) & ~xp.isnan(A).any(1)
        
        coefs, _, _, _ = xp.linalg.lstsq(A[valid], b[valid], rcond=None)
        
        # Reconstruct phase
        phase = xp.zeros((ny, nx), dtype=xp.float32)
        for idx, coef in zip(zernike_modes, coefs):
            Z = self.get_zernike_mode(idx, nx, ny, radius=2)
            phase += coef * Z
        
        return coefs.astype(xp.float32), phase.astype(xp.float32)
    
    def southwell_phase_integration(
        self,
        ny,
        nx,
        pixel_pitch_y,
        pixel_pitch_x,
        wavelength,
        shifts_y,
        shifts_x,
    ):
        """NaN-robust Southwell phase reconstruction using a DCT Poisson solver."""

        xp = self.bm.xp
        xp_name = getattr(xp, "__name__", "")

        if xp_name == "numpy":
            shifts_y = self._to_numpy(shifts_y)
            shifts_x = self._to_numpy(shifts_x)
            
        zoom = self.bm.zoom
        fft = self.bm.fft

        def dct2(a):
            return fft.dct(fft.dct(a, axis=0, norm="ortho"), axis=1, norm="ortho")

        def idct2(a):
            return fft.idct(fft.idct(a, axis=1, norm="ortho"), axis=0, norm="ortho")

        def southwell_poisson_nan(slope_y, slope_x):
            rows, cols = slope_y.shape
            dtype = xp.result_type(slope_y.dtype, slope_x.dtype, xp.float32)

            mask_x = xp.isfinite(slope_x)
            mask_y = xp.isfinite(slope_y)

            div = xp.zeros((rows, cols), dtype=dtype)

            valid_x = mask_x[:, :-1]
            sx = xp.where(valid_x, slope_x[:, :-1], 0.0)
            div[:, :-1] += sx
            div[:, 1:] -= sx

            valid_y = mask_y[:-1, :]
            sy = xp.where(valid_y, slope_y[:-1, :], 0.0)
            div[:-1, :] += sy
            div[1:, :] -= sy

            valid = xp.zeros((rows, cols), dtype=bool)
            valid[:, :-1] |= valid_x
            valid[:, 1:] |= valid_x
            valid[:-1, :] |= valid_y
            valid[1:, :] |= valid_y

            div = xp.where(valid, div, 0.0)

            div_hat = dct2(div)

            ky = xp.arange(rows, dtype=dtype)
            kx = xp.arange(cols, dtype=dtype)

            cy = xp.cos(xp.pi * ky / rows)
            cx = xp.cos(xp.pi * kx / cols)

            eig = 2.0 * (cy[:, None] + cx[None, :] - 2.0)
            eig[0, 0] = 1.0

            phi_hat = div_hat / eig
            phi_hat[0, 0] = 0.0

            phi = idct2(phi_hat)
            phi = xp.where(valid, phi, xp.nan)

            return phi

        def resize_nan(phi, out_rows, out_cols, order=1):
            phi = phi.reshape(phi.shape[-2], phi.shape[-1])

            mask = xp.isfinite(phi)
            phi_filled = xp.where(mask, phi, 0.0)

            zoom_y = out_rows / phi.shape[0]
            zoom_x = out_cols / phi.shape[1]

            phi_zoom = zoom(phi_filled, (zoom_y, zoom_x), order=order)
            mask_zoom = zoom(mask.astype(xp.float32), (zoom_y, zoom_x), order=order)

            phi_zoom = phi_zoom / xp.maximum(mask_zoom, 1e-6)
            phi_zoom = xp.where(mask_zoom > 0.1, phi_zoom, xp.nan)

            return phi_zoom.reshape(out_rows, out_cols)

        # Keep your original calibration convention.
        # Note: pixel_pitch_y and pixel_pitch_x are currently unused.
        slopes_y = shifts_y * wavelength
        slopes_x = shifts_x * wavelength

        phase = southwell_poisson_nan(slopes_y, slopes_x)
        phase = phase * (2.0 * xp.pi / wavelength)
        phase = resize_nan(phase, ny, nx)

        return phase