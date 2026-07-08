"""
Propagation kernels (Fresnel and Angular Spectrum)
"""


from functools import cache
from .utils import pad_array_centrally

@cache
def build_fresnel_kernel_in(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None):
    """Build input Fresnel kernel"""

    # if isinstance(pixel_pitch, (float, int)):
    #     pixel_pitch = (pixel_pitch, pixel_pitch) Removed for perf

    ppy, ppx = pixel_pitch
    # print(ppy, type(ppy))

    y = (xp.arange(0, ny) - xp.round(ny / 2)) * ppy
    x = (xp.arange(0, nx) - xp.round(nx / 2)) * ppx

    X, Y = xp.meshgrid(x, y)

    kernel = xp.exp(1j * xp.pi / (wavelength * z) * (X**2 + Y**2)).astype(xp.complex64)

    if zero_padding:
        kernel = pad_array_centrally(kernel, zero_padding, xp)

    return kernel[xp.newaxis, :, :].astype(xp.complex64)

@cache
def build_fresnel_kernel_out(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None):
    """Build output Fresnel kernel"""

    # if isinstance(pixel_pitch, (float, int)):
    #     pixel_pitch = (pixel_pitch, pixel_pitch) Removed for perf

    ppy, ppx = pixel_pitch

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
        kernel = pad_array_centrally(kernel, zero_padding, xp)

    return kernel[xp.newaxis, :, :].astype(xp.complex64)

@cache
def build_angular_kernel(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None):
    """Build Angular Spectrum kernel"""

    # if isinstance(pixel_pitch, (float, int)):
    #     pixel_pitch = (pixel_pitch, pixel_pitch) Removed for perf

    ppy, ppx = pixel_pitch

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
        kernel = pad_array_centrally(kernel, zero_padding, xp)

    return kernel[xp.newaxis, :, :].astype(xp.complex64)


def fresnel_transform(
    xp, fft, frames, z, pixel_pitch, wavelength, zero_padding=False, use_output_kernel=True
):
    """Apply Fresnel transform"""

    ny, nx = frames.shape[-2:]
    kernel_in = build_fresnel_kernel_in(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)

    if zero_padding:
        

        frames = pad_array_centrally(frames, zero_padding, xp)

    result = fft.fftshift(
        fft.fft2(frames * kernel_in, axes=(-1, -2), norm="ortho"), axes=(-1, -2)
    )

    if use_output_kernel:
        ny, nx = frames.shape[-2:]
        kernel_out = build_fresnel_kernel_out(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)
        result = result * kernel_out

    return result

def fresnel_transform_noshift(
    xp, fft, frames, z, pixel_pitch, wavelength, zero_padding=False, use_output_kernel=True
):
    """Apply Fresnel transform"""

    ny, nx = frames.shape[-2:]
    kernel_in = build_fresnel_kernel_in(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)

    if zero_padding:
        frames = pad_array_centrally(frames, zero_padding, xp)

    result = fft.fft2(frames * kernel_in, axes=(-1, -2), norm="ortho")

    if use_output_kernel:
        ny, nx = frames.shape[-2:]
        kernel_out = build_fresnel_kernel_out(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)
        result = result * kernel_out

    return result

def inverse_fresnel_transform(
    xp, fft, result, z, pixel_pitch, wavelength, zero_padding=False, use_output_kernel=False
):
    """Apply inverse Fresnel transform"""
    
    # Get dimensions
    ny, nx = result.shape[-2:]
    
    # Step 1: Remove output kernel if it was applied
    if use_output_kernel:
        kernel_out = build_fresnel_kernel_out(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)
        result = result * xp.conj(kernel_out)  # Multiply by complex conjugate to invert
    
    # Step 2: Apply inverse FFT (inverse of fft.fftshift(fft.fft2(...)))
    result = fft.ifftshift(result, axes=(-1, -2))  # Undo fftshift
    result = fft.ifft2(result, axes=(-1, -2), norm="ortho")  # Inverse FFT
    
    # Step 3: Remove input kernel
    kernel_in = build_fresnel_kernel_in(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)
    result = result * xp.conj(kernel_in)  # Multiply by complex conjugate to invert
    
    # Step 4: Remove zero padding if it was added
    if zero_padding:
        # Get original dimensions
        orig_ny = ny - 2 * zero_padding
        orig_nx = nx - 2 * zero_padding
        
        # Extract the central region
        start_y = zero_padding
        end_y = zero_padding + orig_ny
        start_x = zero_padding
        end_x = zero_padding + orig_nx
        
        result = result[..., start_y:end_y, start_x:end_x]
    
    return result

def fresnel_transform_retro_propagation(
    xp, fft, frames, z, pixel_pitch, wavelength, zero_padding=False, use_output_kernel=True
):
    """Apply Fresnel transform"""

    ny, nx = frames.shape[-2:]
    kernel_in = build_fresnel_kernel_in(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)

    # if zero_padding:
        

    #     frames = pad_array_centrally(frames, zero_padding, xp)

    result = fft.ifft2(fft.fftshift(frames, axes=(-1, -2)), axes=(-1, -2), norm="ortho") /  kernel_in

    # if use_output_kernel:
    #     ny, nx = frames.shape[-2:]
    #     kernel_out = build_fresnel_kernel_out(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)
    #     result = result * kernel_out

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

    ny, nx = frames.shape[-2:]
    kernel_in = build_fresnel_kernel_in(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)

    if zero_padding:
        ny, nx = frames.shape[-2:]
        frames = pad_array_centrally(frames, zero_padding, xp)
    result = fft.fftshift(
        fft.fft2(frames * kernel_in * phase_term, axes=(-1, -2), norm="ortho"),
        axes=(-1, -2),
    )

    if use_output_kernel:
        kernel_out = build_fresnel_kernel_out(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)
        result = result * kernel_out

    return result


def angular_spectrum_transform(xp, fft, frames, z, pixel_pitch, wavelength,  zero_padding=False):
    """Apply Angular Spectrum transform"""

    ny, nx = frames.shape[-2:]
    kernel = build_angular_kernel(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)

    if zero_padding:

        frames = pad_array_centrally(frames, zero_padding, xp)

    tmp = fft.fft2(frames, axes=(-1, -2), norm="ortho")
    tmp = tmp * fft.fftshift(kernel, axes=(-1, -2))

    return fft.ifft2(tmp, axes=(-1, -2), norm="ortho")


def angular_spectrum_transform_with_phase(
    xp, fft, frames, z, pixel_pitch, wavelength, phase_term, zero_padding=False
):
    """Apply Angular Spectrum transform with phase correction"""

    ny, nx = frames.shape[-2:]
    kernel = build_angular_kernel(xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None)

    # print("multiplying frames")

    frames = frames * phase_term

    # print(frames.dtype)

    # import matplotlib.pyplot as plt
    # plt.imshow(xp.angle(frames[0]).get())
    # plt.show()

    if zero_padding:

        frames = pad_array_centrally(frames, zero_padding, xp)

    return fft.ifft2(
        fft.fft2(frames, axes=(-1, -2), norm="ortho")
        * fft.fftshift(kernel, axes=(-1, -2)), norm="ortho"
    )