"""SAS complex-field accuracy, sampling, and default-pipeline integration."""
from unittest.mock import Mock

import numpy as np
import pytest
from scipy import fft

from holodoppler import backend
from holodoppler.config import validate_main_parameters
from holodoppler.core.propagation import (
    scalable_angular_spectrum_output_pitch as output_pitch,
    scalable_angular_spectrum_transform as propagate,
)
from holodoppler.pipelines import main_default as pipeline
from test_default_pipeline_contract import parameters
from test_default_preview import input_reader, settings


def dense_reference(field, z, pitch, wavelength, final_phase):
    """Independent dense DFT operators and the paper's original phase formula."""
    ny, nx = field.shape
    py, px = 2 * ny, 2 * nx
    ys, xs = np.arange(py) - py // 2, np.arange(px) - px // 2
    fy = np.arange(-py // 2, py // 2) / (py * pitch[0])
    fx = np.arange(-px // 2, px // 2) / (px * pitch[1])
    dy = np.exp(-2j * np.pi * fy[:, None] * (ys * pitch[0])[None, :]) / np.sqrt(py)
    dx = np.exp(-2j * np.pi * fx[:, None] * (xs * pitch[1])[None, :]) / np.sqrt(px)
    padded = np.zeros((py, px), complex)
    sy, sx = py // 2 - ny // 2, px // 2 - nx // 2
    padded[sy:sy + ny, sx:sx + nx] = field
    cx, cy = wavelength * fx[None, :], wavelength * fy[:, None]
    rho = cx**2 + cy**2
    root = np.sqrt(np.maximum(1 - rho, 0))
    # Bandlimit expressed as limits on transfer-function phase derivatives.
    safe_root = np.where(root > 0, root, 1)
    window = ((rho < 1)
              & (np.abs(z * cx * (1 / safe_root - 1)) <= px * pitch[1] / 2)
              & (np.abs(z * cy * (1 / safe_root - 1)) <= py * pitch[0] / 2))
    transfer = window * np.exp(2j * np.pi * z / wavelength * (root - 1 + rho / 2))
    corrected = dy.conj().T @ ((dy @ padded @ dx.T) * transfer) @ dx.conj()
    chirp = np.exp(1j * np.pi / (wavelength * z)
                   * ((ys[:, None] * pitch[0])**2 + (xs[None, :] * pitch[1])**2))
    result = dy @ (corrected * chirp) @ dx.T
    if final_phase:
        qy, qx = wavelength * z * fy, wavelength * z * fx
        result *= np.exp(1j * (2 * np.pi * z / wavelength
                         + np.pi / (wavelength * z) * (qy[:, None]**2 + qx[None, :]**2)))
    return result[sy:sy + ny, sx:sx + nx]


@pytest.mark.parametrize("shape", [(6, 8), (5, 7), (5, 8)])
@pytest.mark.parametrize("final_phase", [False, True])
def test_complex_field_matches_dense_reference(shape, final_phase):
    rng = np.random.default_rng(13)
    fields = (rng.normal(size=(2, 3, *shape)) + 1j * rng.normal(size=(2, 3, *shape))).astype(np.complex64)
    original = fields.copy()
    pitch, wavelength, z = (0.7e-6, 0.9e-6), 0.5e-6, 18e-6
    actual = propagate(np, fft, fields, z, pitch, wavelength, final_phase)
    expected = np.array([dense_reference(field, z, pitch, wavelength, final_phase)
                         for field in fields.reshape(-1, *shape)]).reshape(fields.shape)
    np.testing.assert_allclose(actual, expected, rtol=3e-5, atol=3e-7)
    np.testing.assert_array_equal(fields, original)
    assert actual.shape == fields.shape
    assert actual.dtype == np.complex64
    assert np.isfinite(actual).all()


def test_scalar_pitch_and_evanescent_suppression():
    field = np.ones((7, 9), np.float32)
    actual = propagate(np, fft, field, 1e-6, .1e-6, .8e-6)
    expected = propagate(np, fft, field, 1e-6, [.1e-6, .1e-6], .8e-6)
    np.testing.assert_array_equal(actual, expected)
    assert np.isfinite(actual).all()
    np.testing.assert_allclose(output_pitch(1e-6, .1e-6, .8e-6, 7, 9),
                               [.8e-6 / 1.4, .8e-6 / 1.8])


@pytest.mark.parametrize("key", ["z", "wavelength", "pixel_pitch"])
@pytest.mark.parametrize("value", [0, -1, np.nan, np.inf, True, "bad"])
def test_invalid_optical_parameters(key, value):
    values = dict(z=10e-6, pixel_pitch=(1e-6, 1e-6), wavelength=.5e-6)
    values[key] = value
    with pytest.raises((TypeError, ValueError), match=key):
        propagate(np, fft, np.ones((3, 4)), **values)
    if key == "pixel_pitch":
        values[key] = (1e-6, value)
    with pytest.raises((TypeError, ValueError), match=key):
        output_pitch(**values, ny=3, nx=4)
    with pytest.raises((TypeError, ValueError), match=key):
        validate_main_parameters(parameters(spatial_propagation="ScalableAngularSpectrum", **values))


@pytest.mark.parametrize("flag", ["shack_hartmann", "shack_hartmann_autofocus"])
def test_wavefront_estimation_is_rejected(flag):
    with pytest.raises(ValueError, match="shack_hartmann: false.*shack_hartmann_autofocus: false"):
        validate_main_parameters(parameters(spatial_propagation="ScalableAngularSpectrum", **{flag: True}))


def test_empty_or_nonspatial_fields_are_rejected():
    for shape in [(0, 3), (3, 0), (3,)]:
        with pytest.raises(ValueError):
            propagate(np, fft, np.ones(shape), 1e-5, 1e-6, .5e-6)


@pytest.mark.parametrize("reference_only", [False, True])
def test_pipeline_dispatch_and_reference_equivalence(monkeypatch, reference_only):
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    try:
        p = parameters(spatial_propagation="ScalableAngularSpectrum", z=50e-6,
                       pixel_pitch=[1e-6, 1.2e-6], wavelength=.5e-6)
        validate_main_parameters(p)
        frames = np.random.default_rng(5).random((8, 7, 9), dtype=np.float32)
        transform = Mock(wraps=propagate)
        monkeypatch.setattr(pipeline, "scalable_angular_spectrum_transform", transform)
        result = pipeline._process_batch(p, frames, reference_only=reference_only)
        transform.assert_called_once()
        holograms = propagate(np, fft, frames, p["z"], p["pixel_pitch"], p["wavelength"])
        monkeypatch.setattr(pipeline, "angular_spectrum_transform", lambda *a, **k: holograms)
        expected = pipeline._process_batch(dict(p, spatial_propagation="AngularSpectrum"), frames,
                                           reference_only=reference_only)
        np.testing.assert_allclose(result["moment0ff"], expected["moment0ff"])
        assert np.isfinite(result["moment0ff"]).all()
    finally:
        backend.set_backend(previous)


def test_preview_equals_registration_reference(tmp_path, monkeypatch):
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    try:
        reader = input_reader(tmp_path, monkeypatch)
        p = settings(spatial_propagation="ScalableAngularSpectrum", z=50e-6,
                     pixel_pitch=[1e-6, 1.2e-6], wavelength=.5e-6,
                     shack_hartmann=False, shack_hartmann_autofocus=False)
        image = pipeline.preview(reader.file_path, p, save_outputs=False)
        frames = reader.read_frames(first_frame=0, batch_size=8)
        reference = pipeline._compute_reference_image(p, frames)
        np.testing.assert_allclose(image, reference, rtol=2e-6, atol=1e-7)
        assert image.shape == (8, 10)
        reader.close.assert_called_once()
    finally:
        backend.set_backend(previous)


def test_optional_cupy_agreement():
    if not backend.cupy_available:
        pytest.skip("CUDA unavailable")
    import cupy as cp
    from cupyx.scipy import fft as gpu_fft
    field = np.random.default_rng(31).random((2, 5, 8), dtype=np.float32)
    for final_phase in (False, True):
        args = (18e-6, (.7e-6, .9e-6), .5e-6, final_phase)
        expected = propagate(np, fft, field, *args)
        actual = cp.asnumpy(propagate(cp, gpu_fft, cp.asarray(field), *args))
        np.testing.assert_allclose(actual, expected, rtol=5e-5, atol=5e-6)
