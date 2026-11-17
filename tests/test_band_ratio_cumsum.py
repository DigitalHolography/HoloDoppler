"""Optional band ratios and full-PSD power quantile images."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import h5py
import numpy as np
import pytest
import yaml

from holodoppler import backend
from holodoppler.config import validate_main_parameters
from holodoppler.core.moments import cumsum_frequency
from holodoppler.pipelines import main_default as pipeline
from holodoppler.saving.default_output import DefaultOutput, selected_formats

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def cpu():
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    yield
    backend.set_backend(previous)


def parameters(**updates):
    p = yaml.safe_load((ROOT / "parameters/default_parameters_default.yaml").read_text())
    p.update(sampling_freq=800, pixel_pitch=[1e-6, 1e-6], z=.1,
             low_freq=0, high_freq=400, batch_size=8, svd_threshold=-1,
             compute_gaussian_width=False, pca_compute=False,
             color_Doppler_image=False, directional_Doppler_image=False,
             shack_hartmann_autofocus=False, image_registration=False,
             image_registration_with_ecc=False, square=False,
             frequency_bands=[[0, 150], [150, 350]], outputs={})
    p.update(updates)
    return p


def process(monkeypatch, p, psd):
    spectrum = np.sqrt(psd).astype(np.complex128)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **k: spectrum.copy())
    monkeypatch.setattr(pipeline, "svd_filter", lambda *a, **k: spectrum.copy())
    monkeypatch.setattr(pipeline, "fourier_time_transform", lambda *a: spectrum.copy())
    return pipeline._process_batch(p, spectrum)


@pytest.mark.parametrize("nt", [7, 8, 9])
@pytest.mark.parametrize("threshold", [.25, .75, 1.])
def test_cumsum_matches_absolute_frequency_oracle(nt, threshold):
    psd = np.random.default_rng(34).integers(1, 10, (nt, 3, 5)).astype(float)
    original = psd.copy()
    f = abs(np.fft.fftfreq(nt, 1 / 800))
    bins = np.unique(f)
    folded = np.stack([psd[f == value].sum(axis=0) for value in bins])
    cumulative = folded.cumsum(axis=0)
    expected = bins[(cumulative >= threshold * cumulative[-1]).argmax(axis=0)]
    np.testing.assert_allclose(cumsum_frequency(np, psd, 800, threshold), expected)
    np.testing.assert_array_equal(psd, original)


def test_cumsum_dc_nyquist_and_invalid():
    psd = np.zeros((8, 1, 6))
    psd[0, 0, 0] = 1
    psd[4, 0, 1] = 1
    psd[1, 0, 3] = np.nan
    psd[1, 0, 4] = np.inf
    psd[1, 0, 5] = -1
    np.testing.assert_array_equal(cumsum_frequency(np, psd, 800), [[0, 400, 0, 0, 0, 0]])


def test_gpu_matches_cpu():
    if not backend._cupy_usable():
        pytest.skip("CUDA backend unavailable")
    psd = np.random.default_rng(15).random((9, 3, 5)).astype(np.float32)
    expected = cumsum_frequency(np, psd, 800)
    backend.set_backend("cupy")
    actual = cumsum_frequency(backend.xp, backend.to_backend(psd), 800)
    np.testing.assert_allclose(backend.to_numpy(actual), expected)
    first = backend.to_backend(np.array([[0., 2., np.nan]]))
    last = backend.to_backend(np.array([[1., 6., 1.]]))
    np.testing.assert_array_equal(backend.to_numpy(pipeline._band_ratio(first, last)), [[0, 3, 0]])


@pytest.mark.parametrize("value", [0, -1, 1.01, np.nan, np.inf, True, None, "0.75"])
def test_invalid_threshold(value):
    with pytest.raises((TypeError, ValueError), match="cumsum_threshold"):
        validate_main_parameters(parameters(cumsum_threshold=value))


@pytest.mark.parametrize("projection", [False, True])
def test_ratio_dependencies_and_selection(monkeypatch, projection):
    name = "band_ratio_time_projection" if projection else "band_ratio"
    p = parameters(outputs={name: ["h5"]})
    psd = np.ones((8, 3, 5))
    psd[[2, 3, 5, 6]] = 4
    result = process(monkeypatch, p, psd)
    np.testing.assert_allclose(result["band_ratio"], 4)
    assert not any(key.startswith("band_0_") or key.startswith("band_1_") for key in result)
    assert "cumsum" not in result


def test_ratio_invalid_single_empty_and_disabled(monkeypatch):
    first = np.array([[0., 2, np.nan, 3, 4]])
    last = np.array([[3., 6, 2, np.inf, np.nan]])
    np.testing.assert_array_equal(pipeline._band_ratio(first, last), [[0, 3, 0, 0, 0]])
    psd = np.ones((8, 3, 5))
    p = parameters(frequency_bands=[[0, 150]], outputs={"band_ratio": ["h5"]})
    np.testing.assert_allclose(process(monkeypatch, p, psd)["band_ratio"], 1)
    p["frequency_bands"] = [[900, 1000], [0, 150]]
    np.testing.assert_array_equal(process(monkeypatch, p, psd)["band_ratio"], 0)
    p["frequency_bands"] = []
    assert "band_ratio" not in process(monkeypatch, p, psd)
    p = parameters(outputs={"band_*": ["h5"], "band_ratio": [],
                            "band_ratio_time_projection": [], "cumsum": []})
    result = process(monkeypatch, p, psd)
    assert "band_ratio" not in result and "cumsum" not in result


@pytest.mark.parametrize("welch", [False, True])
def test_cumsum_full_psd_sampling_and_reference(monkeypatch, welch):
    psd = np.ones((8, 3, 5))
    psd[2] = 100
    p = parameters(low_freq=0, high_freq=30, skip_every=2,
                   welch_enabled=welch, outputs={"cumsum_time_projection": ["png"]})
    monkeypatch.setattr(pipeline, "welch_power_spectrum", lambda *a, **k: psd.copy())
    result = process(monkeypatch, p, psd)
    np.testing.assert_array_equal(result["cumsum"], 100)
    for name in ("cumsum", "band_ratio"):
        p["registration_image"] = name
        p["image_registration"] = True
        assert pipeline._reference_output_key(p, {}) == name
        reference = pipeline._reference_from_psd(p, psd, name)[name]
        normal = process(monkeypatch, p, psd)[name]
        np.testing.assert_allclose(reference, normal)
        np.testing.assert_allclose(pipeline._compute_reference_image(p, np.sqrt(psd)), normal)


def test_translation_applies_to_both_images(monkeypatch):
    images = {name: np.full((3, 5), value) for name, value in
              (("moment0ff", 1.), ("band_ratio", 2.), ("cumsum", 100.))}
    monkeypatch.setattr(pipeline, "_process_batch", lambda *a, **kw: kw["output_dict"].update(images))
    monkeypatch.setattr(pipeline, "register_images_shifts", lambda *a, **kw: (1., 2.))
    monkeypatch.setattr(pipeline, "apply_register_images_shifts", lambda xp, data, **kw: data + 10)
    p = parameters(image_registration=True, registration_image="cumsum")
    result, reference = pipeline._process_one_batch(p, np.ones((8, 3, 5)))
    np.testing.assert_array_equal(reference, images["cumsum"])
    for name in ("band_ratio", "cumsum"):
        np.testing.assert_array_equal(result[name], images[name] + 10)


@pytest.mark.parametrize("live", [False, True])
def test_ecc_projection_uses_registered_images(tmp_path, monkeypatch, live):
    p = parameters(live_saving=live, image_registration_with_ecc=True,
                   numpy_num_workers=0, num_saving_workers=0,
                   outputs={name + "_time_projection": ["h5"]
                            for name in ("band_ratio", "cumsum")})
    images = {name: np.ones((4, 6)) for name in ("moment0ff", "band_ratio", "cumsum")}
    monkeypatch.setattr(pipeline, "_process_one_batch", lambda *a, **kw: (dict(images), None))
    monkeypatch.setattr(pipeline, "register_with_ecc", lambda *a, **kw: np.zeros((2, 2)))
    monkeypatch.setattr(pipeline, "apply_ecc_registration", lambda data, *a, **kw: data * 2)
    source = SimpleNamespace(file_path=tmp_path / "input.raw",
                             read_frames=lambda **kw: np.ones((8, 4, 6)))
    with DefaultOutput(source, p) as out:
        pipeline._process_to_output(source, p, [0, 8], out, None)
    with h5py.File(next(out.target_dir.glob("h5/*.h5"))) as h5:
        for name in ("band_ratio", "cumsum"):
            np.testing.assert_array_equal(h5[name + "_time_projection"], 2)


@pytest.mark.parametrize("name", ["band_ratio", "cumsum"])
def test_videos_and_mean_projection(tmp_path, monkeypatch, name):
    writers = []
    def open_video(self, key, fmt):
        writer = Mock()
        writers.append((fmt, writer))
        return writer
    monkeypatch.setattr(DefaultOutput, "_open_video", open_video)
    p = {"outputs": {name: ["avi", "mp4"], name + "_time_projection": ["h5", "png"]}}
    with DefaultOutput(SimpleNamespace(file_path=tmp_path / "input.raw"), p) as out:
        for i in range(2):
            out.add_batch({name: np.full((4, 6), 1. + 2 * i)}, i)
    assert {fmt for fmt, _ in writers} == {"avi", "mp4"}
    assert all(writer.append_data.call_count == 2 for _, writer in writers)
    with h5py.File(next(out.target_dir.glob("h5/*.h5"))) as h5:
        np.testing.assert_array_equal(h5[name + "_time_projection"], 2)
    assert (out.target_dir / "png" / (name + "_time_projection.png")).exists()


@pytest.mark.parametrize("preset", ["default", "default_offline"])
def test_preset_exports(preset):
    p = yaml.safe_load((ROOT / f"parameters/default_parameters_{preset}.yaml").read_text())
    assert p["cumsum_threshold"] == .75
    for name in ("band_ratio", "cumsum"):
        assert selected_formats(p, name) == {"avi", "mp4"}
        assert selected_formats(p, name + "_time_projection") == {"png"}
