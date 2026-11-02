"""Welch averaging, frequency-axis integration and configuration contracts."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml
from scipy import fft
from scipy.signal.windows import get_window

from holodoppler import backend
from holodoppler.config import validate_main_parameters
from holodoppler.core.filtering import welch_power_spectrum
from holodoppler.pipelines import main_default as pipeline


def parameters(**updates):
    path = Path(__file__).resolve().parents[1] / "parameters/default_parameters_default.yaml"
    p = yaml.safe_load(path.read_text())
    p.update(backend="numpy", z=.1, pixel_pitch=[1e-6, 1e-6], sampling_freq=800,
             batch_size=11, batch_stride=11, welch_enabled=True,
             welch_batch_size=4, welch_stride=3, low_freq=0, high_freq=400,
             image_registration=False, shack_hartmann=False,
             shack_hartmann_autofocus=False, frequency_bands=[[0, 400]],
             moments_frequency_ranges=[[0, 400]], corner_compensation=False,
             color_Doppler_image=True, directional_Doppler_image=True,
             color_Doppler_low_frequency_band=[0, 200],
             color_Doppler_high_frequency_band=[200, 400],
             directional_Doppler_frequency_band=[0, 400],
             save_averaged_spectrogram=True)
    p.update(updates)
    return p


@pytest.mark.parametrize("window", [None, "hann", "hamming"])
@pytest.mark.parametrize("stride", [2, 4, 6])
def test_segment_average(window, stride):
    rng = np.random.default_rng(42)
    data = (rng.normal(size=(13, 3, 5)) + 1j * rng.normal(size=(13, 3, 5))).astype(np.complex64)
    original = data.copy()
    weights = np.ones(4) if window is None else get_window(window, 4)
    expected = np.mean([
        abs(np.fft.fft(data[start:start + 4] * weights[:, None, None],
                       axis=0, norm="ortho")) ** 2
        for start in range(0, 10, stride)], axis=0) / np.mean(weights ** 2)
    np.testing.assert_allclose(welch_power_spectrum(np, fft, data, 4, stride, window),
                               expected, rtol=2e-6, atol=1e-6)
    np.testing.assert_array_equal(data, original)


def test_single_untapered_segment_matches_existing_fft():
    data = np.arange(24).reshape(8, 3, 1).astype(np.complex64)
    np.testing.assert_array_equal(welch_power_spectrum(np, fft, data, 8, 32),
                                  abs(fft.fft(data, axis=0, norm="ortho")) ** 2)
    with pytest.raises(ValueError, match="welch_batch_size"):
        welch_power_spectrum(np, fft, data, 9)


@pytest.mark.parametrize("key", ["welch_batch_size", "welch_stride"])
@pytest.mark.parametrize("value", [None, True, 0, -1, 2.5, "32"])
def test_invalid_sizes(key, value):
    with pytest.raises((TypeError, ValueError), match=key):
        validate_main_parameters(parameters(**{key: value}))


@pytest.mark.parametrize("updates,match", [
    ({"welch_enabled": 1}, "welch_enabled"),
    ({"welch_windowing": "missing-window"}, "welch_windowing"),
    ({"welch_windowing": []}, "welch_windowing"),
    ({"welch_batch_size": 12}, "batch_size"),
    ({"image_registration": True, "registration_ref_batch_size": 3}, "registration_ref_batch_size"),
])
def test_invalid_configuration(updates, match):
    with pytest.raises((TypeError, ValueError), match=match):
        validate_main_parameters(parameters(**updates))


def test_pipeline_uses_segment_frequency_axis(monkeypatch):
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    try:
        rng = np.random.default_rng(7)
        data = (rng.normal(size=(11, 3, 5)) + 1j * rng.normal(size=(11, 3, 5))).astype(np.complex64)
        monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **k: data)
        monkeypatch.setattr(pipeline, "svd_filter", lambda *a, **k: data)
        p = parameters()
        validate_main_parameters(p)
        result = pipeline._process_batch(p, data)
        psd = welch_power_spectrum(np, fft, data, 4, 3)
        np.testing.assert_allclose(result["sh_psd"], psd)
        assert result["spectrum_line"].shape == (4,)
        frequencies = np.fft.fftfreq(4, 1 / 800)
        selected = (abs(frequencies) > 0) & (abs(frequencies) < 400)
        for order in range(3):
            np.testing.assert_allclose(result[f"moment{order}"],
                (psd[selected] * frequencies[selected, None, None] ** order).sum(axis=0), rtol=2e-6)
        np.testing.assert_allclose(result["band_0_0_400"], psd[selected].mean(axis=0))
        reference = pipeline._process_batch(p, data, reference_only=True)
        np.testing.assert_allclose(reference["moment0ff"], result["moment0ff"])
        p["welch_enabled"] = False
        legacy = pipeline._process_batch(p, data)
        np.testing.assert_allclose(legacy["sh_psd"], abs(fft.fft(data, axis=0, norm="ortho")) ** 2)
    finally:
        backend.set_backend(previous)


def test_gpu_parity_when_available():
    if not backend._cupy_usable():
        pytest.skip("CUDA backend unavailable")
    import cupy as cp
    import cupyx.scipy.fft as cp_fft
    data = np.arange(60, dtype=np.float32).reshape(10, 2, 3).astype(np.complex64)
    expected = welch_power_spectrum(np, fft, data, 4, 2, "hann")
    actual = welch_power_spectrum(cp, cp_fft, cp.asarray(data), 4, 2, "hann")
    np.testing.assert_allclose(cp.asnumpy(actual), expected, rtol=2e-6, atol=1e-5)


@pytest.mark.parametrize("preview", [False, True])
def test_entrypoints_preserve_input_batching(monkeypatch, preview):
    previous = backend.get_backend_name()
    rng = np.random.default_rng(20)
    frames = rng.normal(size=(22, 3, 5)).astype(np.float32)
    reads, saved = [], {}

    def read(first_frame, batch_size, **kwargs):
        reads.append((first_frame, batch_size))
        return frames[first_frame:first_frame + batch_size].copy()

    reader = SimpleNamespace(extension=".raw", total_frames=22, read_frames=read)
    monkeypatch.setattr(pipeline, "get_reader", lambda path: reader)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda xp, fft, data, *a, **k: data.astype(np.complex64))
    monkeypatch.setattr(pipeline, "svd_filter", lambda xp, linalg, data, *a, **k: data)
    monkeypatch.setattr(pipeline, "save_outputs", lambda **kw: saved.update(kw["output"]))
    p = parameters(first_frame=0, end_frame=-1, square=False, live_saving=False,
                   image_registration_with_ecc=False, numpy_num_workers=0,
                   save_spectograms=False, color_Doppler_image=False,
                   directional_Doppler_image=False)
    try:
        if preview:
            pipeline.preview("unused.raw", p)
            assert reads == [(0, 11)]
            np.testing.assert_allclose(saved["sh_psd"], welch_power_spectrum(
                np, fft, frames[:11].astype(np.complex64), 4, 3))
        else:
            pipeline.process("unused.raw", p)
            assert reads == [(0, 11), (11, 11)]
            expected = np.mean([welch_power_spectrum(
                np, fft, data.astype(np.complex64), 4, 3)
                for data in (frames[:11], frames[11:])], axis=0)
            np.testing.assert_allclose(saved["averaged_spectrogram"], expected, rtol=2e-6)
    finally:
        backend.set_backend(previous)
