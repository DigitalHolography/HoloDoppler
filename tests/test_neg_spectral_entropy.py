"""Numerical and batch-output contracts for negative spectral entropy."""
from types import SimpleNamespace
from unittest.mock import Mock

import h5py
import numpy as np
import pytest

from holodoppler import backend
from holodoppler.core.moments import neg_spectral_entropy
from holodoppler.pipelines import main_default as pipeline
from holodoppler.saving.default_output import DefaultOutput
from test_default_pipeline_contract import parameters


@pytest.fixture(autouse=True)
def cpu_backend():
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    yield
    backend.set_backend(previous)


def matlab_reference(spectrum, f1, f2, fs):
    # Explicit bin loop provides an independent reference for the vectorized helper.
    result = np.zeros(spectrum.shape[1:])
    for frequency, values in zip(np.fft.fftfreq(len(spectrum), 1 / fs), spectrum):
        if abs(frequency) >= f1 and (f2 is None or abs(frequency) <= f2):
            p = np.abs(values)
            positive = p > 0
            result[positive] += p[positive] * np.log(p[positive])
    return result


def test_entropy_zero_bins_and_unnormalized_magnitude():
    spectrum = np.zeros((8, 2, 3), dtype=complex)
    spectrum[1, 0, 0] = 3 + 4j
    spectrum[2, 0, 1] = .5j
    spectrum[3, 0, 2] = 100
    spectrum[-1, 1, 0] = -2j
    spectrum[0, 1, 1] = 100
    with np.errstate(all="raise"):
        result = neg_spectral_entropy(np, spectrum, 100, 200, 800)
    np.testing.assert_allclose(result, [[5 * np.log(5), .5 * np.log(.5), 0],
                                       [2 * np.log(2), 0, 0]])


@pytest.mark.parametrize("size", [7, 8])
@pytest.mark.parametrize("band", [(0, None), (100, 200), (200, 200), (500, 600)])
def test_matches_matlab_reference(size, band):
    rng = np.random.default_rng(3)
    spectrum = rng.normal(size=(size, 3, 5)) + 1j * rng.normal(size=(size, 3, 5))
    spectrum[0] = 0
    for scale in (.1, 1, 10):
        actual = neg_spectral_entropy(np, spectrum * scale, *band, 800)
        np.testing.assert_allclose(actual, matlab_reference(spectrum * scale, *band, 800))


def test_cupy_parity():
    cp = pytest.importorskip("cupy")
    try:
        if not cp.cuda.runtime.getDeviceCount():
            pytest.skip("No CUDA device")
        power = cp.asarray(np.random.default_rng(4).random((8, 3, 5)))
    except cp.cuda.runtime.CUDARuntimeError as exc:
        pytest.skip(f"CUDA unavailable: {exc}")
    np.testing.assert_allclose(cp.asnumpy(neg_spectral_entropy(cp, power, 100, 200, 800)),
                               neg_spectral_entropy(np, cp.asnumpy(power), 100, 200, 800))


@pytest.mark.parametrize("rules, enabled", [
    (None, False), ({}, False), ({"neg_spectral_entropy": []}, False),
    ({"neg_spectral_entropy": ["h5"]}, True), ({"neg_*": ["avi"]}, True),
    ({"neg_spectral_entropy_time_projection": ["png"]}, True),
    ({"neg_*": ["h5"], "neg_spectral_entropy": [],
      "neg_spectral_entropy_time_projection": []}, False),
])
def test_optional_computation(monkeypatch, rules, enabled):
    frames = np.random.default_rng(5).random((8, 3, 5)).astype(np.complex64)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **kw: frames.copy())
    entropy = Mock(wraps=neg_spectral_entropy)
    monkeypatch.setattr(pipeline, "neg_spectral_entropy", entropy)
    p = parameters()
    if rules is not None:
        p["outputs"] = rules
    result = pipeline._process_batch(p, frames)
    assert ("neg_spectral_entropy" in result) == enabled
    assert entropy.call_count == int(enabled)


@pytest.mark.parametrize("welch", [False, True])
@pytest.mark.parametrize("corners", [False, True])
@pytest.mark.parametrize("skip", [1, 2])
def test_spectrum_band_and_reference(monkeypatch, welch, corners, skip):
    frames = np.random.default_rng(6).random((16, 3, 5)).astype(np.complex64)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **kw: frames.copy())
    monkeypatch.setattr(pipeline, "svd_filter", lambda xp, linalg, data, *a, **kw: data)
    p = parameters(batch_size=16, low_freq=100, high_freq=200, skip_every=skip,
                   welch_enabled=welch, welch_batch_size=8, welch_stride=4,
                   welch_windowing="hann", corner_compensation=corners,
                   outputs={"neg_spectral_entropy": ["h5"]},
                   registration_image="neg_spectral_entropy")
    spectrum = pipeline.fourier_time_transform(np, backend.fft, frames)
    expected = matlab_reference(spectrum, 100, 200, 800 / skip)
    result = pipeline._process_batch(p, frames)["neg_spectral_entropy"]
    np.testing.assert_allclose(result, expected, rtol=1e-6)
    changed = pipeline._process_batch(dict(p, low_freq=0, high_freq=400), frames)
    np.testing.assert_allclose(changed["neg_spectral_entropy"],
                               matlab_reference(spectrum, 0, 400, 800 / skip), rtol=1e-6)
    assert not np.allclose(changed["neg_spectral_entropy"], result)
    # Registration dependencies compute the map even without an export selection.
    p.update(outputs={}, image_registration=True)
    np.testing.assert_allclose(pipeline._compute_reference_image(p, frames), result)
    np.testing.assert_allclose(pipeline._process_batch(p, frames)["neg_spectral_entropy"], result)


def test_translation_and_resizing(monkeypatch):
    frames = np.random.default_rng(7).random((8, 3, 5)).astype(np.complex64)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **kw: frames.copy())
    monkeypatch.setattr(pipeline, "_prepare_batch_frames", lambda p, f, phase, res: (f, phase))
    monkeypatch.setattr(pipeline, "register_images_shifts", lambda *a, **kw: (1., 2.))
    monkeypatch.setattr(pipeline, "apply_register_images_shifts", lambda xp, value, **kw: value + 10)
    p = parameters(square=True, image_registration=True, outputs={"neg_spectral_entropy": ["h5"]})
    expected = pipeline._process_batch(p, frames)["neg_spectral_entropy"] + 10
    result, _ = pipeline._process_one_batch(p, frames, registration_ref=np.ones((3, 5)))
    np.testing.assert_allclose(result["neg_spectral_entropy"], expected)
    finished = pipeline._finalize_spatial_result(result, p)
    assert finished["neg_spectral_entropy"].shape == (5, 5)


@pytest.mark.parametrize("live", [False, True])
@pytest.mark.parametrize("ecc", [False, True])
def test_batch_exports_and_projection(tmp_path, monkeypatch, live, ecc):
    frames = np.random.default_rng(8).random((16, 4, 6)).astype(np.float32)
    reader = SimpleNamespace(file_path=tmp_path / "input.raw",
                             read_frames=lambda first_frame, batch_size, **kw:
                             frames[first_frame:first_frame + batch_size].copy())
    name = "neg_spectral_entropy"
    p = parameters(live_saving=live, numpy_num_workers=0, num_saving_workers=0,
                   square=True, image_registration_with_ecc=ecc,
                   outputs={name: ["h5", "avi", "mp4"], name + "_time_projection": ["h5", "png"]})
    expected = []
    for start in (0, 8):
        result, _ = pipeline._process_one_batch(p, frames[start:start + 8])
        if ecc:
            result[name] += 1
        expected.append(pipeline._finalize_spatial_result(result, p)[name])
    monkeypatch.setattr(pipeline, "register_with_ecc", lambda *a, **kw: np.zeros((2, 2)))
    monkeypatch.setattr(pipeline, "apply_ecc_registration", lambda images, *a, **kw: images + 1)
    writers = {fmt: Mock() for fmt in ("avi", "mp4")}
    monkeypatch.setattr(DefaultOutput, "_open_video", lambda self, name, fmt: writers[fmt])
    with DefaultOutput(reader, p) as out:
        pipeline._process_to_output(reader, p, [0, 8], out, None)
    with h5py.File(next(out.target_dir.glob("h5/*.h5"))) as h5:
        np.testing.assert_allclose(h5[name], expected, rtol=1e-6)
        np.testing.assert_allclose(h5[name + "_time_projection"], np.mean(expected, axis=0), rtol=1e-6)
    assert (out.target_dir / "png" / (name + "_time_projection.png")).exists()
    for writer in writers.values():
        assert writer.append_data.call_count == 2
        writer.close.assert_called_once()
