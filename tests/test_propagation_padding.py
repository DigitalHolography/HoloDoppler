"""Per-side padding references independent of production kernel builders."""
from unittest.mock import Mock

import numpy as np
import pytest
from scipy import fft

from holodoppler import backend
from holodoppler.config import validate_main_parameters
from holodoppler.core import propagation as prop
from holodoppler.pipelines import main_default as pipeline
from test_default_pipeline_contract import parameters
from test_default_preview import input_reader, settings


Z, PITCH, WAVELENGTH = .012, (2e-6, 3e-6), 532e-9
TRANSFORMS = [prop.fresnel_transform, prop.fresnel_transform_with_phase,
              prop.angular_spectrum_transform, prop.angular_spectrum_transform_with_phase]


def assert_field_close(actual, expected):
    # Fresnel's physical amplitude factor can exceed 1e8; compare at field scale.
    scale = np.max(np.abs(expected))
    np.testing.assert_allclose(actual / scale, expected / scale, rtol=3e-5, atol=1e-6)


def reference(frames, method, padding, phase=None, output_kernel=True):
    """Reproduce established grids/FFT conventions, padding explicitly with NumPy."""
    ny, nx = frames.shape[-2:]
    field = frames
    if method == "Fresnel":
        y = (np.arange(ny) - np.round(ny / 2)) * PITCH[0]
        x = (np.arange(nx) - np.round(nx / 2)) * PITCH[1]
        kernel = np.exp(1j * np.pi / (WAVELENGTH * Z)
                        * (y[:, None] ** 2 + x[None, :] ** 2)).astype(np.complex64)
        if phase is not None:
            kernel = (kernel * phase).astype(np.complex64)
        field = field * kernel
    elif phase is not None:
        field = field * phase
    py, px = (0, 0) if padding is False or padding is None else padding
    field = np.pad(field, [(0, 0)] * (field.ndim - 2) + [(py, py), (px, px)])
    ny, nx = field.shape[-2:]
    if method == "Fresnel":
        result = np.fft.fftshift(np.fft.fft2(field, norm="ortho"), axes=(-2, -1))
        if output_kernel:
            fy = np.fft.fftshift(np.fft.fftfreq(ny, d=PITCH[0]))
            fx = np.fft.fftshift(np.fft.fftfreq(nx, d=PITCH[1]))
            kernel = (np.exp(1j * 2 * np.pi / WAVELENGTH * Z) / (1j * WAVELENGTH * Z)
                      * np.exp(1j * np.pi / (WAVELENGTH * Z)
                               * ((WAVELENGTH * Z * fy[:, None]) ** 2
                                  + (WAVELENGTH * Z * fx[None, :]) ** 2)))
            result = result * kernel.astype(np.complex64)
        return result
    u = (np.arange(nx) - np.round(nx / 2)) / (nx * PITCH[1])
    v = (np.arange(ny) - np.round(ny / 2)) / (ny * PITCH[0])
    kernel = np.exp(2j * np.pi * Z / WAVELENGTH
                    * np.sqrt(1 - (WAVELENGTH * u[None, :]) ** 2
                              - (WAVELENGTH * v[:, None]) ** 2)).astype(np.complex64)
    return np.fft.ifft2(np.fft.fft2(field, norm="ortho")
                        * np.fft.fftshift(kernel), norm="ortho")


@pytest.mark.parametrize("transform", TRANSFORMS)
@pytest.mark.parametrize("shape", [(5, 8), (2, 6, 9), (2, 3, 5, 8)])
@pytest.mark.parametrize("padding", [[2, 3], [0, 2], [3, 0], [0, 0], False, None])
@pytest.mark.parametrize("dtype", [np.complex64, np.complex128])
def test_explicit_padding_reference(transform, shape, padding, dtype):
    rng = np.random.default_rng(7)
    frames = (rng.normal(size=shape) + 1j * rng.normal(size=shape)).astype(dtype)
    original = frames.copy()
    phase = np.exp(-1j * rng.normal(size=shape[-2:])).astype(np.complex64)
    original_phase = phase.copy()
    corrected = transform.__name__.endswith("with_phase")
    method = "Fresnel" if transform.__name__.startswith("fresnel") else "AngularSpectrum"
    args = (np, fft, frames, Z, PITCH, WAVELENGTH)
    for output_kernel in ([False, True] if method == "Fresnel" else [True]):
        kwargs = {"use_output_kernel": output_kernel} if method == "Fresnel" else {}
        actual = transform(*args, *([phase] if corrected else []), zero_padding=padding, **kwargs)
        expected = reference(frames, method, padding, phase if corrected else None, output_kernel)
        assert_field_close(actual, expected)
        assert actual.shape == expected.shape
        assert actual.dtype == dtype
    np.testing.assert_array_equal(frames, original)
    np.testing.assert_array_equal(phase, original_phase)


INVALID_PADDING = [(-1, 2), (0, -1), (1.0, 2), (True, 0), (0, False),
                   (1, "2"), (), (1,), (1, 2, 3), True, 0, 2, "1,2"]


@pytest.mark.parametrize("transform", TRANSFORMS)
@pytest.mark.parametrize("padding", INVALID_PADDING)
def test_invalid_padding(transform, padding):
    args = [np, fft, np.ones((2, 5, 8), np.complex64), Z, PITCH, WAVELENGTH]
    if transform.__name__.endswith("with_phase"):
        args.append(np.ones((5, 8), np.complex64))
    with pytest.raises((TypeError, ValueError), match="zero_padding"):
        transform(*args, zero_padding=padding)


@pytest.mark.parametrize("padding", INVALID_PADDING)
def test_invalid_pipeline_padding(padding):
    with pytest.raises((TypeError, ValueError), match="zero_padding"):
        validate_main_parameters(parameters(zero_padding=padding))


@pytest.mark.parametrize("padding", [False, None, [0, 0], [0, 2], (np.int64(1), 3)])
def test_valid_pipeline_padding(padding):
    validate_main_parameters(parameters(zero_padding=padding))


@pytest.mark.parametrize("padding", [False, None, [0, 0], [0, 2], [1, 0]])
def test_sas_padding_configuration(padding):
    p = parameters(spatial_propagation="ScalableAngularSpectrum", zero_padding=padding)
    if padding and any(padding):
        with pytest.raises(ValueError, match="ScalableAngularSpectrum.*zero_padding"):
            validate_main_parameters(p)
    else:
        validate_main_parameters(p)


@pytest.mark.parametrize("dtype", [np.float32, np.float64, np.complex64, np.complex128])
def test_padding_helper_preserves_dtype_and_batch_axes(dtype):
    frames = np.ones((2, 3, 5, 8), dtype=dtype)
    padded = prop._pad_propagation_field(np, frames, [1, 3])
    assert padded.dtype == frames.dtype
    np.testing.assert_array_equal(padded, np.pad(frames, [(0, 0), (0, 0), (1, 1), (3, 3)]))


def test_supplied_fresnel_kernel_is_corrected_before_padding():
    frames = np.random.default_rng(4).normal(size=(5, 8)).astype(np.complex64)
    phase = np.exp(-1j * np.arange(40).reshape(5, 8) / 20).astype(np.complex64)
    cached = prop.build_fresnel_kernel_in(np, Z, PITCH, WAVELENGTH, 5, 8)
    original_cached = cached.copy()
    kernel = (cached * phase).astype(np.complex64)
    original_kernel = kernel.copy()
    actual = prop.fresnel_transform(np, fft, frames, Z, PITCH, WAVELENGTH,
                                    zero_padding=[2, 3], input_kernel=kernel)
    expected = reference(frames, "Fresnel", [2, 3], phase)
    assert_field_close(actual, expected)
    np.testing.assert_array_equal(cached, original_cached)
    np.testing.assert_array_equal(kernel, original_kernel)


@pytest.mark.parametrize("transform", TRANSFORMS)
def test_default_padding_and_batched_phase(transform):
    frames = np.random.default_rng(11).random((2, 3, 5, 8), dtype=np.float32)
    phase = np.exp(-1j * frames).astype(np.complex64)
    args = [np, fft, frames, Z, PITCH, WAVELENGTH]
    corrected = transform.__name__.endswith("with_phase")
    if corrected:
        args.append(phase)
    np.testing.assert_array_equal(transform(*args), transform(*args, zero_padding=None))
    actual = transform(*args, zero_padding=(np.int64(1), np.int64(3)))
    method = "Fresnel" if transform.__name__.startswith("fresnel") else "AngularSpectrum"
    assert_field_close(actual, reference(frames, method, [1, 3], phase if corrected else None))
    assert actual.shape == (2, 3, 7, 14)


@pytest.mark.parametrize("transform", TRANSFORMS)
def test_optional_gpu_padding_reference(transform):
    if not backend.cupy_available:
        pytest.skip("CUDA unavailable")
    import cupy as cp
    from cupyx.scipy import fft as gpu_fft
    frames = np.random.default_rng(12).random((2, 3, 5, 8), dtype=np.float32)
    phase = np.exp(-1j * frames[0, 0]).astype(np.complex64)
    args = [cp, gpu_fft, cp.asarray(frames), Z, PITCH, WAVELENGTH]
    corrected = transform.__name__.endswith("with_phase")
    if corrected:
        args.append(cp.asarray(phase))
    method = "Fresnel" if transform.__name__.startswith("fresnel") else "AngularSpectrum"
    for padding in ([1, 3], [0, 3], [1, 0], False):
        actual = cp.asnumpy(transform(*args, zero_padding=padding))
        expected = reference(frames, method, padding, phase if corrected else None)
        assert actual.shape == expected.shape
        assert actual.dtype == np.complex64
        assert_field_close(actual, expected)


@pytest.fixture
def cpu_backend():
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    yield
    backend.set_backend(previous)


@pytest.mark.parametrize("method,correction", [("Fresnel", "none"), ("Fresnel", "phase"),
    ("Fresnel", "fixed"), ("AngularSpectrum", "none"), ("AngularSpectrum", "phase")])
def test_pipeline_dispatch_and_reference(cpu_backend, monkeypatch, method, correction):
    frames = np.random.default_rng(42).random((8, 5, 8), dtype=np.float32)
    phase = np.exp(-1j * np.arange(40).reshape(5, 8) / 20).astype(np.complex64)
    p = parameters(spatial_propagation=method, zero_padding=[1, 3], z=Z,
                   pixel_pitch=PITCH, wavelength=WAVELENGTH)
    name = "fresnel_transform" if method == "Fresnel" else "angular_spectrum_transform"
    if correction == "phase":
        name += "_with_phase"
    spy = Mock(wraps=getattr(pipeline, name))
    monkeypatch.setattr(pipeline, name, spy)
    kernel = pipeline._fixed_fresnel_kernel(p, phase) if correction == "fixed" else None
    kwargs = dict(phase_term=None if correction == "none" else phase, propagation_kernel=kernel)
    full = pipeline._process_batch(p, frames, **kwargs)
    ref = pipeline._compute_reference_image(p, frames, **kwargs)
    assert spy.call_count == 2
    assert spy.call_args.kwargs["zero_padding"] == [1, 3]
    assert ref.shape == (7, 14)
    np.testing.assert_allclose(ref, full["moment0ff"], rtol=2e-6, atol=1e-7)
    expected = reference(frames, method, [1, 3], None if correction == "none" else phase,
                         p["Fresnel_use_ouput_kernel"])
    # Propagation results drive downstream outputs unchanged.
    monkeypatch.setattr(pipeline, name, lambda *a, **k: expected)
    compared = pipeline._process_batch(p, frames, **kwargs)
    np.testing.assert_allclose(full["moment0"], compared["moment0"], rtol=3e-5, atol=1e-6)


@pytest.mark.parametrize("method", ["Fresnel", "AngularSpectrum"])
@pytest.mark.parametrize("autofocus", [False, True])
def test_padded_preview_matches_process_registration(cpu_backend, tmp_path, monkeypatch, method, autofocus):
    reader = input_reader(tmp_path, monkeypatch)
    p = settings(spatial_propagation=method, zero_padding=[1, 3],
                 shack_hartmann_autofocus=autofocus, square=False)
    def estimate(parameters, frames, output_dict=None, diagnostics=None, **kwargs):
        assert frames.shape[-2:] == (8, 10)
        phase = np.linspace(0, .5, 80, dtype=np.float32).reshape(8, 10)
        output_dict.update(shack_hartmann_zernike_coefs=np.array([1, 0, 0]),
                           shack_hartmann_wavefront_phase=phase)
        return np.exp(-1j * phase)
    monkeypatch.setattr(pipeline, "_process_shack_hartmann", estimate)
    image = pipeline.preview(reader.file_path, dict(p), save_outputs=False)
    assert image.shape == (10, 16)
    references = []
    def shifts(xp, fft, fixed, moving, **kwargs):
        references.append(fixed.copy())
        assert moving.shape == fixed.shape == (10, 16)
        return 0, 0
    monkeypatch.setattr(pipeline, "register_images_shifts", shifts)
    monkeypatch.setattr(pipeline, "apply_register_images_shifts", lambda xp, image, **kw: image)
    monkeypatch.setattr(pipeline, "save_outputs", Mock())
    pipeline.process(reader.file_path, dict(p))
    assert references
    for fixed in references:
        np.testing.assert_allclose(image, fixed, rtol=2e-6, atol=1e-7)
