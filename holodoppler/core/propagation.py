"""
Propagation kernels (Fresnel, Angular Spectrum, and Scalable Angular Spectrum)
"""

from functools import cache
from math import isfinite
from numbers import Integral, Real
from .image_utils import pad_array_centrally


def _validate_sas_parameters(z, pixel_pitch, wavelength):
    """Validate forward SAS optical parameters and return a hashable pitch."""
    if isinstance(pixel_pitch, Real) and not isinstance(pixel_pitch, bool):
        pixel_pitch = (pixel_pitch, pixel_pitch)
    if not isinstance(pixel_pitch, (tuple, list)) or len(pixel_pitch) != 2:
        raise ValueError("pixel_pitch must be a scalar or a (y, x) pair")
    for name, value in (("z", z), ("wavelength", wavelength),
                        ("pixel_pitch[y]", pixel_pitch[0]),
                        ("pixel_pitch[x]", pixel_pitch[1])):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a finite positive real number for SAS")
        if not isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive for SAS")
    return tuple(float(value) for value in pixel_pitch)


def scalable_angular_spectrum_output_pitch(z, pixel_pitch, wavelength, ny, nx):
    """Return SAS output pitch (y, x), in meters, with fixed twofold padding.

    ``ny, nx`` are the unpadded input dimensions. The returned field has these
    same dimensions, cropped from the center of the padded propagation.
    """
    ppy, ppx = _validate_sas_parameters(z, pixel_pitch, wavelength)
    for size in (ny, nx):
        if isinstance(size, bool) or not isinstance(size, Integral) or size <= 0:
            raise ValueError("SAS spatial dimensions must be positive integers")
    return wavelength * z / (2 * ny * ppy), wavelength * z / (2 * nx * ppx)


@cache
def _build_sas_kernels(xp, z, pixel_pitch, wavelength, ny, nx, use_output_kernel):
    """Build bandlimited precompensation and centered Fresnel phase factors.

    Implements Heintzmann, Loetgering and Wechsler (Optica 2023),
    doi:10.1364/OPTICA.497809. Frequency arrays use native FFT ordering.
    """
    ppy, ppx = pixel_pitch
    py, px = 2 * ny, 2 * nx
    fy = xp.fft.fftfreq(py, d=ppy)[:, None]
    fx = xp.fft.fftfreq(px, d=ppx)[None, :]
    cy, cx = wavelength * fy, wavelength * fx
    rho = cx**2 + cy**2
    ty = py * ppy / (2 * z) + xp.abs(cy)
    tx = px * ppx / (2 * z) + xp.abs(cx)
    window = ((rho <= 1) & (cx**2 * (1 + tx**2) / tx**2 + cy**2 <= 1)
              & (cy**2 * (1 + ty**2) / ty**2 + cx**2 <= 1))
    root = xp.sqrt(xp.maximum(1 - rho, 0))
    # Stable form of sqrt(1-rho) - (1-rho/2), even for small angles.
    delta = -rho**2 / (2 * (1 + root)**2)
    correction = (window * xp.exp(2j * xp.pi * z / wavelength * delta)).astype(xp.complex64)
    y = ((xp.arange(py) - py // 2) * ppy)[:, None]
    x = ((xp.arange(px) - px // 2) * ppx)[None, :]
    phase_in = xp.exp(1j * xp.pi / (wavelength * z) * (y**2 + x**2)).astype(xp.complex64)
    phase_out = None
    if use_output_kernel:
        dqy, dqx = scalable_angular_spectrum_output_pitch(z, pixel_pitch, wavelength, ny, nx)
        qy = ((xp.arange(py) - py // 2) * dqy)[:, None]
        qx = ((xp.arange(px) - px // 2) * dqx)[None, :]
        phase_out = xp.exp(1j * (2 * xp.pi * z / wavelength
                            + xp.pi / (wavelength * z) * (qy**2 + qx**2))).astype(xp.complex64)
    return correction, phase_in, phase_out


def scalable_angular_spectrum_transform(
    xp, fft, frames, z, pixel_pitch, wavelength, use_output_kernel=False,
):
    """Propagate with the bandlimited three-FFT Scalable Angular Spectrum method.

    Accepts spatial arrays with any leading batch dimensions. Uses twofold
    padding and returns the original shape as complex64, without changing input.
    Output sampling is given by ``scalable_angular_spectrum_output_pitch``.
    FFTs are orthonormal; the optional output kernel adds global and quadratic
    phase only (no radiometric amplitude factor). Large distances can vignette
    the reconstructed field due to the precompensation bandlimit.
    """
    pixel_pitch = _validate_sas_parameters(z, pixel_pitch, wavelength)
    if frames.ndim < 2:
        raise ValueError("SAS requires at least two spatial dimensions")
    ny, nx = frames.shape[-2:]
    scalable_angular_spectrum_output_pitch(z, pixel_pitch, wavelength, ny, nx)
    correction, phase_in, phase_out = _build_sas_kernels(
        xp, z, pixel_pitch, wavelength, ny, nx, use_output_kernel)
    # Align the central sample for odd sizes as well as even sizes.
    sy, sx = ny - ny // 2, nx - nx // 2
    padding = [(0, 0)] * (frames.ndim - 2) + [(sy, ny - sy), (sx, nx - sx)]
    padded = xp.pad(frames.astype(xp.complex64, copy=False), padding)
    spectrum = fft.fft2(fft.ifftshift(padded, axes=(-2, -1)), axes=(-2, -1), norm="ortho")
    precomp = fft.fftshift(fft.ifft2(spectrum * correction, axes=(-2, -1), norm="ortho"),
                             axes=(-2, -1))
    result = fft.fftshift(fft.fft2(fft.ifftshift(precomp * phase_in, axes=(-2, -1)),
                                  axes=(-2, -1), norm="ortho"), axes=(-2, -1))
    if phase_out is not None:
        result = result * phase_out
    return result[..., sy:sy + ny, sx:sx + nx].astype(xp.complex64, copy=False)

def ensure_yx_pixel_pitch(pixel_pitch):
    if isinstance(pixel_pitch, (int, float)):
        return (float(pixel_pitch), float(pixel_pitch))
    return tuple(pixel_pitch)


@cache
def build_fresnel_kernel_in(
    xp,
    z,
    pixel_pitch,
    wavelength,
    ny,
    nx,
    offset_to_center=None,
    zero_padding=None,
):
    """Build input Fresnel kernel"""

    # if isinstance(pixel_pitch, (float, int)):
    #     pixel_pitch = (pixel_pitch, pixel_pitch) Removed for perf

    ppy, ppx = ensure_yx_pixel_pitch(pixel_pitch)
    # print(ppy, type(ppy))

    y = (xp.arange(0, ny) - xp.round(ny / 2)) * ppy
    x = (xp.arange(0, nx) - xp.round(nx / 2)) * ppx

    X, Y = xp.meshgrid(x, y)

    kernel = xp.exp(1j * xp.pi / (wavelength * z) * (X**2 + Y**2)).astype(xp.complex64)

    if offset_to_center is not None:
        offset_y_pixels, offset_x_pixels = offset_to_center
        offset_x = offset_x_pixels / (nx * ppx)
        offset_y = offset_y_pixels / (ny * ppy)
        kernel *= xp.exp(-1j * 2 * xp.pi * (offset_y * Y + offset_x * X)).astype(
            xp.complex64
        )

    if zero_padding:
        kernel = pad_array_centrally(xp, kernel, zero_padding)

    return kernel[xp.newaxis, :, :].astype(xp.complex64)


@cache
def build_fresnel_kernel_out(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None):
    """Build output Fresnel kernel"""

    # if isinstance(pixel_pitch, (float, int)):
    #     pixel_pitch = (pixel_pitch, pixel_pitch) Removed for perf

    ppy, ppx = ensure_yx_pixel_pitch(pixel_pitch)

    fx = xp.fft.fftfreq(nx, d=ppx)
    fx = xp.fft.fftshift(fx)
    fy = xp.fft.fftfreq(ny, d=ppy)
    fy = xp.fft.fftshift(fy)
    FX, FY = xp.meshgrid(fx, fy)

    X = wavelength * z * FX
    Y = wavelength * z * FY
    phase = 1j * xp.pi / (wavelength * z) * (X**2 + Y**2)
    kernel = (
        xp.exp(1j * 2 * xp.pi / wavelength * z) / (1j * wavelength * z) * xp.exp(phase)
    ).astype(xp.complex64)

    if zero_padding:
        kernel = pad_array_centrally(xp, kernel, zero_padding)

    return kernel[xp.newaxis, :, :].astype(xp.complex64)


@cache
def build_angular_kernel(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None):
    """Build Angular Spectrum kernel"""

    # if isinstance(pixel_pitch, (float, int)):
    #     pixel_pitch = (pixel_pitch, pixel_pitch) Removed for perf

    ppy, ppx = ensure_yx_pixel_pitch(pixel_pitch)

    du = 1.0 / (nx * ppx)
    dv = 1.0 / (ny * ppy)
    u = (xp.arange(1, int(nx) + 1) - 1 - xp.round(nx / 2)) * du
    v = (xp.arange(1, int(ny) + 1) - 1 - xp.round(ny / 2)) * dv
    U, V = xp.meshgrid(u, v)

    kernel = xp.exp(
        2j
        * xp.pi
        * z
        / wavelength
        * xp.sqrt(1.0 - (wavelength * U) ** 2 - (wavelength * V) ** 2)
    )

    if zero_padding:
        kernel = pad_array_centrally(xp, kernel, zero_padding)

    return kernel[xp.newaxis, :, :].astype(xp.complex64)


def fresnel_transform(
    xp,
    fft,
    frames,
    z,
    pixel_pitch,
    wavelength,
    zero_padding=False,
    use_output_kernel=True,
    input_kernel=None,
):
    """Apply Fresnel propagation, optionally reusing a corrected input kernel."""

    pixel_pitch = ensure_yx_pixel_pitch(pixel_pitch)
    ny, nx = frames.shape[-2:]
    kernel_in = input_kernel
    if kernel_in is None:
        kernel_in = build_fresnel_kernel_in(
            xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None
        )

    if zero_padding:

        frames = pad_array_centrally(xp, frames, zero_padding)

    result = fft.fftshift(
        fft.fft2(frames * kernel_in, axes=(-1, -2), norm="ortho"), axes=(-1, -2)
    )

    if use_output_kernel:
        ny, nx = frames.shape[-2:]
        kernel_out = build_fresnel_kernel_out(
            xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None
        )
        result = result * kernel_out

    return result


def fresnel_transform_with_phase(
    xp,
    fft,
    frames,
    z,
    pixel_pitch,
    wavelength,
    phase_term,
    zero_padding=False,
    use_output_kernel=True,
):
    """Apply Fresnel transform with phase correction"""

    pixel_pitch = ensure_yx_pixel_pitch(pixel_pitch)
    ny, nx = frames.shape[-2:]
    kernel_in = build_fresnel_kernel_in(
        xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None
    )

    if zero_padding:
        ny, nx = frames.shape[-2:]
        frames = pad_array_centrally(xp, frames, zero_padding)
    corrected_kernel = (kernel_in * phase_term).astype(xp.complex64, copy=False)
    result = fft.fftshift(
        fft.fft2(frames * corrected_kernel, axes=(-1, -2), norm="ortho"),
        axes=(-1, -2),
    )

    if use_output_kernel:
        kernel_out = build_fresnel_kernel_out(
            xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None
        )
        result = result * kernel_out

    return result


def angular_spectrum_transform(
    xp, fft, frames, z, pixel_pitch, wavelength, zero_padding=False
):
    """Apply Angular Spectrum transform"""

    pixel_pitch = ensure_yx_pixel_pitch(pixel_pitch)
    ny, nx = frames.shape[-2:]
    kernel = build_angular_kernel(
        xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None
    )

    if zero_padding:

        frames = pad_array_centrally(xp, frames, zero_padding)

    tmp = fft.fft2(frames, axes=(-1, -2), norm="ortho")
    tmp = tmp * fft.fftshift(kernel, axes=(-1, -2))

    return fft.ifft2(tmp, axes=(-1, -2), norm="ortho")


def angular_spectrum_transform_with_phase(
    xp, fft, frames, z, pixel_pitch, wavelength, phase_term, zero_padding=False
):
    """Apply Angular Spectrum transform with phase correction"""

    pixel_pitch = ensure_yx_pixel_pitch(pixel_pitch)
    ny, nx = frames.shape[-2:]
    kernel = build_angular_kernel(
        xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None
    )

    # print("multiplying frames")

    frames = frames * phase_term

    # print(frames.dtype)

    # import matplotlib.pyplot as plt
    # plt.imshow(xp.angle(frames[0]).get())
    # plt.show()

    if zero_padding:

        frames = pad_array_centrally(xp, frames, zero_padding)

    return fft.ifft2(
        fft.fft2(frames, axes=(-1, -2), norm="ortho")
        * fft.fftshift(kernel, axes=(-1, -2)),
        norm="ortho",
    )
