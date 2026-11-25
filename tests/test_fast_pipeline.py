import struct
from threading import Event
from pathlib import Path

import h5py
import numpy as np
import pytest

from holodoppler import backend
from holodoppler.cli.command import PipelineMode, _run_pipeline
from holodoppler.core.image_utils import gaussian_flatfield
from holodoppler.core.progress import ProcessingCancelled, ProgressReporter
from holodoppler.pipelines import main_fast as fast


@pytest.fixture(autouse=True)
def cpu():
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    yield
    backend.set_backend(previous)


@pytest.mark.parametrize("count", [0, 2, -2])
def test_fft_moments(count):
    rng = np.random.default_rng(1)
    field = (rng.normal(size=(64, 9, 10)) + 1j * rng.normal(size=(64, 9, 10))).astype(np.complex64)
    reducer = fast._temporal_reducer(
        dict(sampling_freq=64, svd_filter=count, frequency_ranges=[[4, 31], [33, 60], [6, 18]]),
        64,
    )
    expected = field
    if count:
        matrix = field.reshape(64, -1).T
        _, _, vh = np.linalg.svd(matrix, full_matrices=False)
        rejected = vh[:count] if count > 0 else vh[count:]
        expected = (matrix - matrix @ rejected.conj().T @ rejected).T.reshape(field.shape)
    bins = np.r_[4:31, 33:60]
    power = abs(np.fft.fft(expected, axis=0, norm="ortho")[bins]) ** 2
    freq = np.fft.fftfreq(64, 1 / 64)[bins]
    for order, image in enumerate(reducer(field.copy())):
        np.testing.assert_allclose(image, (power * freq[:, None, None] ** order).sum(axis=0),
                                   rtol=2e-5, atol=0.015)


def test_pca_projection():
    rng = np.random.default_rng(2)
    field = (rng.normal(size=(5, 4, 6)) + 1j * rng.normal(size=(5, 4, 6))).astype(np.complex64)
    reducer = fast._temporal_reducer(dict(mode="pca", pca_index_range=[1, 3]), 5)
    pixels = field.reshape(5, -1).T
    u, values, _ = np.linalg.svd(pixels, full_matrices=False)
    expected = abs(u[:, 2:4] * values[2:4]).sum(axis=1).reshape(4, 6)
    np.testing.assert_allclose(reducer(field)[0], expected, rtol=1e-5)
    with pytest.raises(ValueError, match="only available in FFT"):
        fast._temporal_reducer(dict(mode="pca", svd_filter=1), 5)


@pytest.fixture
def recording(tmp_path):
    frames = np.random.default_rng(6).integers(1, 255, (26, 10, 10), dtype=np.uint8)
    path = tmp_path / "sample.holo"
    header = struct.pack("<4sHHIIIQB", b"HOLO", 1, 8, 10, 10, 26, frames.size, 0)
    path.write_bytes(header.ljust(64, b"\0") + frames.tobytes())
    return path, frames


def parameters(**updates):
    return dict(dict(pipeline_name="fast", backend="numpy", z=.1, pixel_pitch=1e-6,
                     sampling_freq=120, time_window=4, accu=3), **updates)


@pytest.mark.parametrize("mode, names", [("fft", fast.FFT_MAPS), ("pca", fast.PCA_MAPS)])
def test_dispatch_and_exports(recording, mode, names, monkeypatch):
    path, _ = recording
    monkeypatch.setattr("holodoppler.cli.command.configure_logging", lambda: None)
    p = parameters(mode=mode)
    image = _run_pipeline(path, p, PipelineMode.PREVIEW, save_outputs=False)
    assert image.shape == (10, 10)
    assert len(list(path.parent.iterdir())) == 1
    _run_pipeline(path, p, PipelineMode.PREVIEW)
    [preview_h5] = path.parent.rglob("*.h5")
    with h5py.File(preview_h5) as handle:
        assert handle[names[-1]].shape == (10, 10)
    target = fast.process(path, p)
    [output_h5] = (Path(target) / "h5").glob("*.h5")
    with h5py.File(output_h5) as handle:
        assert set(handle).intersection((*fast.FFT_MAPS, "pca_sum", "pca_sum_ff")) == set(names)
        assert all(handle[name].shape == (2, 10, 10) for name in names)
        expected_preview = "pca_sum" if mode == "pca" else "moment0ff"
        np.testing.assert_allclose(image, handle[expected_preview][0])
        if mode == "pca":
            for raw, flat in zip(handle["pca_sum"], handle["pca_sum_ff"]):
                np.testing.assert_allclose(flat, gaussian_flatfield(raw, 35, backend.gaussian_filter))


def test_registration_and_autofocus_use_group_means(monkeypatch, recording):
    path, frames = recording
    phase = np.full((10, 10), .3, dtype=np.float32)
    calls = []
    shifts = []

    def subimages(raw, kernel, reducer):
        return np.full((5, 5, 2, 2), raw.mean(), dtype=np.float32)

    def estimate_shifts(xp, fft, images, **kwargs):
        np.testing.assert_allclose(images, frames[:12].mean(), rtol=1e-6)
        return np.zeros((5, 5)), np.zeros((5, 5))

    def propagate(xp, fft, raw, z, pitch, wavelength, *, input_kernel, **kwargs):
        kernel = fast.build_fresnel_kernel_in(xp, z, pitch, wavelength, 10, 10)
        np.testing.assert_allclose(input_kernel, kernel * np.exp(-1j * phase), atol=1e-6)
        return np.fft.ifftshift(raw.astype(np.complex64), axes=(-2, -1))

    def register(xp, fft, fixed, moving, **kwargs):
        calls.append((fixed, moving))
        return 0, 1

    def apply_shift(xp, maps, *, shift_y, shift_x, fft):
        shifts.append(maps.copy())
        return np.roll(maps, (shift_y, shift_x), axis=(-2, -1))

    monkeypatch.setattr(fast, "_subimages", subimages)
    monkeypatch.setattr(fast, "calculate_displacements_graph_laplacian", estimate_shifts)
    monkeypatch.setattr(fast, "fit_zernike_fresnel", lambda *args: (np.zeros(3), phase))
    monkeypatch.setattr(fast, "fresnel_transform", propagate)
    monkeypatch.setattr(fast, "register_images_shifts", register)
    monkeypatch.setattr(fast, "apply_register_images_shifts", apply_shift)
    target = fast.process(path, parameters(image_registration=True, shack_hartmann_autofocus=True))
    expected = (frames[:24].astype(np.float32) ** 2).reshape(2, 3, 4, 10, 10).sum(2).mean(1)
    assert len(calls) == 1
    for registered, image in zip(calls[0], expected):
        np.testing.assert_allclose(registered, gaussian_flatfield(image, 35, backend.gaussian_filter),
                                   rtol=1e-6)
    [output_h5] = (Path(target) / "h5").glob("*.h5")
    with h5py.File(output_h5) as handle:
        np.testing.assert_allclose(handle["moment0"][0], expected[0], rtol=1e-6)
        np.testing.assert_allclose(handle["moment0"][1], np.roll(expected[1], 1, axis=-1), rtol=1e-6)
        [unshifted] = shifts
        assert len(unshifted) == len(fast.FFT_MAPS)
        for name, image in zip(fast.FFT_MAPS, unshifted):
            np.testing.assert_allclose(handle[name][1], np.roll(image, 1, axis=-1))


def test_cancelled_compute_creates_no_outputs(recording):
    path, _ = recording
    stop = Event()
    progress = ProgressReporter(lambda *args: stop.set(), stop)
    with pytest.raises(ProcessingCancelled):
        fast.process(path, parameters(), progress_callback=progress)
    assert list(path.parent.iterdir()) == [path]
