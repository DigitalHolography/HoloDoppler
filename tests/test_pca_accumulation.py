"""PCA packet numerics and registration of complete accumulated images."""

import copy

import numpy as np
import pytest

from holodoppler import backend
from holodoppler.core import filtering, pipeline
from holodoppler.core.image_utils import gaussian_flatfield
from holodoppler.pipelines import main_default, main_pca_accumulation as pca
from test_pipeline_migration import parameters, reader_for


@pytest.fixture(autouse=True)
def cpu_backend():
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    yield
    backend.set_backend(previous)


@pytest.mark.parametrize("method", ["Fresnel", "AngularSpectrum"])
def test_packet_average_matches_default_before_flatfield(monkeypatch, method):
    rng = np.random.default_rng(27)
    frames = (rng.normal(size=(12, 5, 7)) + 1j * rng.normal(size=(12, 5, 7))).astype(np.complex64)
    transform = "fresnel_transform" if method == "Fresnel" else "angular_spectrum_transform"
    for module in (pca, main_default):
        monkeypatch.setattr(module, transform, lambda xp, fft, frames, *a, **k: frames.copy())
    p = parameters("pca_accumulation", batch_size=4, accumulation=3, pca_range=[1, 4],
                   spatial_propagation=method, pca_compute=True, pca_time_window=4,
                   pca_index_range=[1, 4], pca_flatfield=False)
    expected = np.mean([
        np.abs(filtering.pca_time_transform(np, packet, remove_dc=False)[1:4]).sum(axis=0)
        for packet in frames.reshape(3, 4, 5, 7)
    ], axis=0)
    result = pca._process_batch(p, frames)
    np.testing.assert_allclose(result["pca_sum"], expected, rtol=1e-6)
    np.testing.assert_allclose(result["pca_sum_ff"], gaussian_flatfield(
        expected, p["registration_flatfield_gw"], backend.gaussian_filter), rtol=1e-6)
    # Use reference-only calculation to avoid unrelated default spectral work.
    for key in ("pca_sum", "pca_sum_ff"):
        default = main_default._process_batch(
            dict(p, registration_image=key, pca_flatfield=key.endswith("_ff")),
            frames, reference_only=True)
        np.testing.assert_allclose(result[key], default[key], rtol=1e-6)


@pytest.mark.parametrize("workers", [0, 2])
def test_live_registration_uses_first_accumulated_image(tmp_path, monkeypatch, workers):
    frames = np.arange(1, 13, dtype=np.float32)[:, None, None] * np.ones((12, 3, 5), np.float32)
    reader, calls = reader_for(tmp_path, frames)
    monkeypatch.setattr(pipeline, "get_reader", lambda _: reader)
    monkeypatch.setattr(pca, "fresnel_transform", lambda xp, fft, frames, *a, **k: frames)
    monkeypatch.setattr(filtering, "pca_time_transform", lambda xp, frames, **k: frames)
    monkeypatch.setattr(pca, "gaussian_flatfield", lambda image, *a: image ** 2)
    estimates, shifts, saved = [], [], []

    def estimate(xp, fft, reference, current, **kwargs):
        estimates.append((reference.copy(), current.copy()))
        return 1., 2.

    def shift(xp, image, **kwargs):
        shifts.append((image.copy(), kwargs["block_size_mib"]))
        return image + 100

    monkeypatch.setattr(pca, "register_images_shifts", estimate)
    monkeypatch.setattr(pca, "apply_register_images_shifts", shift)
    monkeypatch.setattr(pipeline, "save_outputs", lambda **kw: saved.append(kw) or tmp_path)
    p = parameters("pca_accumulation", batch_size=2, accumulation=2, batch_stride=4,
                   pca_range=[0, 2], image_registration=True, live_saving=False,
                   numpy_num_workers=workers, registration_block_size_mib=3,
                   registration_ref_first_frame=999, registration_ref_batch_size=999,
                   shack_hartmann=True, shack_hartmann_autofocus=True)
    original = copy.deepcopy(p)
    pca.process(reader.file_path, p)
    assert p == original
    assert sorted(calls) == [(0, 4, None), (4, 4, None), (8, 4, None)]
    assert len(estimates) == 3 and len(shifts) == 6
    # Packet sums are [3, 7], [11, 15], [19, 23]; accumulated means are 5, 13, 21.
    for reference, current in estimates:
        np.testing.assert_allclose(reference, 25)
    np.testing.assert_allclose(sorted(current[0, 0] for _, current in estimates), [25, 169, 441])
    assert all(block == 3 for _, block in shifts)
    result = saved[0]["output"]
    assert set(result) == {"pca_sum", "pca_sum_ff", "registration"}
    np.testing.assert_allclose(result["pca_sum"][:, 0, 0], [105, 113, 121])
    np.testing.assert_allclose(result["pca_sum_ff"][:, 0, 0], [125, 269, 541])
    np.testing.assert_allclose(result["registration"], [[1, 2]] * 3)


def test_skip_end_frame_and_explicit_fps(tmp_path, monkeypatch):
    frames = np.arange(24, dtype=np.float32)[:, None, None] * np.ones((24, 3, 5), np.float32)
    reader, calls = reader_for(tmp_path, frames)
    monkeypatch.setattr(pipeline, "get_reader", lambda _: reader)
    monkeypatch.setattr(pca, "fresnel_transform", lambda xp, fft, frames, *a, **k: frames)
    monkeypatch.setattr(filtering, "pca_time_transform", lambda xp, frames, **k: frames)
    monkeypatch.setattr(pca, "gaussian_flatfield", lambda image, *a: image)
    saved = []
    monkeypatch.setattr(pipeline, "save_outputs", lambda **kw: saved.append(kw) or tmp_path)
    p = parameters("pca_accumulation", batch_size=2, accumulation=2, batch_stride=8,
                   first_frame=1, end_frame=20, skip_every=2, pca_range=[0, 2],
                   live_saving=False, output_fps=17)
    pca.process(reader.file_path, p)
    assert sorted(calls) == [(1, 4, 2), (9, 4, 2)]
    np.testing.assert_allclose(saved[0]["output"]["pca_sum"][:, 0, 0], [8, 24])
    assert saved[0]["parameters"]["output_fps"] == 17
    assert saved[0]["parameters"]["output_frame_stride"] == 8


@pytest.mark.parametrize("changes", [
    {"accumulation": 0}, {"accumulation": True}, {"accumulation": 1.5},
    {"batch_size": 0}, {"batch_stride": 0}, {"pca_range": [0, 5]},
    {"pca_range": [2, 2]}, {"pca_range": [False, 2]},
])
def test_invalid_accumulation_parameters(changes):
    with pytest.raises((TypeError, ValueError)):
        pca._validate_parameters(parameters("pca_accumulation", **changes))
