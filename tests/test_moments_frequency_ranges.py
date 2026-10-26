"""Per-range moments and temporal-average export options."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import h5py
import numpy as np
from PIL import Image
import pytest
from scipy.ndimage import gaussian_filter
import yaml

from holodoppler import backend, saving
from holodoppler.config import validate_main_parameters
from holodoppler.pipelines import main_default
from holodoppler.saving import media


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def cpu():
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    yield
    backend.set_backend(previous)


def parameters(**changes):
    p = yaml.safe_load((ROOT / "parameters/default_parameters_default.yaml").read_text())
    p.update(force_numpy=True, batch_size=8, batch_stride=8, first_frame=0,
             end_frame=-1, sampling_freq=1000, low_freq=0, high_freq=450,
             pixel_pitch=[1e-6, 1e-6], z=.1, numpy_num_workers=2,
             svd_threshold=0, svd_remove_dc=False, filter2d=False,
             shack_hartmann=False, shack_hartmann_autofocus=False,
             image_registration=False, image_registration_with_ecc=False,
             registration_ref_first_frame=0, registration_ref_batch_size=8,
             registration_flatfield_gw=1, frequency_bands=[], square=False,
             save_spectograms=False, save_averaged_spectrogram=False,
             color_Doppler_image=False, directional_Doppler_image=False,
             moments_frequency_ranges=[[0, 250], [250, 500]], overwrite_option="erase")
    p.update(changes)
    return p


@pytest.mark.parametrize("backend_name", ["numpy", "cupy"])
def test_range_moments_match_signed_psd_integrals(monkeypatch, backend_name):
    if backend_name == "cupy" and not backend._cupy_usable():
        pytest.skip("CUDA backend unavailable")
    backend.set_backend(backend_name)
    spectrum = np.random.default_rng(12).normal(size=(8, 6, 10)) + 1j
    device_spectrum = backend.to_backend(spectrum)
    monkeypatch.setattr(main_default, "fresnel_transform", lambda *a, **k: device_spectrum)
    monkeypatch.setattr(main_default, "svd_filter", lambda *a, **k: device_spectrum)
    monkeypatch.setattr(main_default, "fourier_time_transform", lambda *a: device_spectrum)
    p = parameters(frequency_bands=[[0, 250]], skip_every=2)
    result = main_default._process_batch(p, spectrum)
    psd = abs(spectrum) ** 2
    freqs = np.fft.fftfreq(8, 1 / 500)
    for index, (low, high) in enumerate(p["moments_frequency_ranges"]):
        mask = (abs(freqs) > low) & (abs(freqs) < high)
        for order in (0, 1):
            expected = (psd[mask] * freqs[mask, None, None] ** order).sum(axis=0)
            name = f"moment{order}_range_{index}_{low}_{high}"
            np.testing.assert_allclose(backend.to_numpy(result[name]), expected)
            if order == 0:
                blur = gaussian_filter(expected, 1)
                corrected = np.divide(expected, blur, out=np.zeros_like(expected), where=blur != 0)
                np.testing.assert_allclose(backend.to_numpy(result[name.replace("moment0_", "moment0ff_")]), corrected)
    assert not any(key.startswith("moment1ff") for key in result)
    np.testing.assert_allclose(backend.to_numpy(result["band_0_0_250"]), psd[(abs(freqs) > 0) & (abs(freqs) < 250)].mean(axis=0))


def test_disabled_ranges_and_translation(monkeypatch):
    frames = np.random.default_rng(3).random((8, 6, 10)).astype(np.float32)
    disabled = main_default._process_batch(parameters(moments_frequency_ranges=False), frames)
    assert not any("_range_" in key for key in disabled)
    p = parameters(image_registration=True)
    expected = main_default._process_batch(p, frames)
    monkeypatch.setattr(main_default, "register_images_shifts", lambda *a, **k: (0, 1))
    monkeypatch.setattr(main_default, "apply_register_images_shifts", lambda xp, value, **k: np.roll(value, 1, axis=-1))
    actual, _ = main_default._process_one_batch(p, frames)
    for key in expected:
        if "_range_" in key:
            np.testing.assert_allclose(actual[key], np.roll(expected[key], 1, axis=-1))


@pytest.mark.parametrize("ecc", [False, True])
def test_range_exports_stream_buffer_preview(tmp_path, monkeypatch, ecc):
    frames = np.random.default_rng(4).random((16, 6, 10)).astype(np.float32)
    reader = SimpleNamespace(file_path=tmp_path / "input.raw", extension=".raw", total_frames=16,
                             read_frames=lambda first_frame, batch_size, **k: frames[first_frame:first_frame + batch_size].copy())
    monkeypatch.setattr(main_default, "get_reader", lambda _: reader)
    monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *a: Mock())
    monkeypatch.setattr(media, "save_video", lambda *a, **k: None)
    monkeypatch.setattr(main_default, "register_with_ecc", lambda values, **k: np.zeros((len(values), 12)))
    ecc_calls = []
    def apply_ecc(values, *a, **k):
        ecc_calls.append(values.copy())
        return np.roll(values, 1, axis=-1)
    monkeypatch.setattr(main_default, "apply_ecc_registration", apply_ecc)
    captured = {}
    original_add = saving.OutputClass.add_batch
    original_save = main_default.save_outputs
    def add_batch(destination, outputs, index):
        for key, value in outputs.items():
            if "_range_" in key:
                captured.setdefault(key, []).append(value.copy())
        return original_add(destination, outputs, index)
    def save_outputs(*args, **kwargs):
        captured.update({key: value.copy() for key, value in kwargs["output"].items() if "_range_" in key})
        return original_save(*args, **kwargs)
    monkeypatch.setattr(saving.OutputClass, "add_batch", add_batch)
    monkeypatch.setattr(main_default, "save_outputs", save_outputs)
    snapshots = []
    for live in (True, False):
        captured.clear()
        p = parameters(live_saving=live, square=True, image_registration_with_ecc=ecc,
                       resize_averaged_images=True, num_saving_workers=2)
        main_default.process(reader.file_path, p)
        path = next(tmp_path.rglob("*_output.h5"))
        with h5py.File(path) as handle:
            assert not any("_range_" in key for key in handle)
            assert handle["moment0"].shape == (2, 10, 10)
        arrays = {key: np.asarray(value) for key, value in captured.items()}
        assert len(arrays) == 6
        assert not any(key.startswith("moment1ff") for key in arrays)
        for key, value in arrays.items():
            assert value.shape == (2, 10, 10)
            with Image.open(path.parent.parent / "png" / f"{key}.png") as image:
                assert image.size == (20, 20)
        snapshots.append(arrays)
    for key in snapshots[0]:
        np.testing.assert_allclose(snapshots[0][key], snapshots[1][key])
    if ecc:
        assert len(ecc_calls) == 20  # Four main moments plus six per-range maps per run.
    captured.clear()
    main_default.preview(reader.file_path, p)
    path = next(tmp_path.rglob("preview_output.h5"))
    with h5py.File(path) as handle:
        assert not any("_range_" in key for key in handle)
    assert len(captured) == 6
    assert not any(key.startswith("moment1ff") for key in captured)
    assert captured["moment0ff_range_0_0_250"].shape == (10, 10)
    assert not list(path.parent.parent.rglob("moment1ff*"))
    with Image.open(path.parent.parent / "png/moment0ff_range_0_0_250.png") as image:
        assert image.size == (10, 10)  # Preview is a standalone image.


@pytest.mark.parametrize("mode, workers", [("legacy", None), ("bundle", 0), ("bundle", 2), ("stream", 0), ("stream", 2)])
@pytest.mark.parametrize("enabled", [False, True])
def test_average_resize_all_saving_modes(tmp_path, monkeypatch, mode, workers, enabled):
    monkeypatch.setattr(media, "save_video", lambda *a, **k: None)
    encoders = []
    def open_video(*args):
        writer = Mock()
        encoders.append(writer)
        return writer
    monkeypatch.setattr(saving.OutputClass, "_open_video", open_video)
    reader = SimpleNamespace(file_path=tmp_path / "input.raw", extension=".raw")
    gray = np.arange(120, dtype=np.float32).reshape(2, 6, 10)
    rgb = np.random.default_rng(7).random((2, 6, 10, 3)).astype(np.float32)
    outputs = {"moment0": gray, "moment0_range_0_0_250": gray, "color_Doppler_image": rgb}
    p = {"resize_averaged_images": enabled, "num_saving_workers": workers or 0}
    if mode == "stream":
        with saving.OutputClass(reader, p, custom_path=tmp_path / "output") as destination:
            for index in range(2):
                destination.add_batch({key: value[index] for key, value in outputs.items()}, index)
            destination.write_static("diagnostic", gray[0])
        target = destination.target_dir
        for writer in encoders:
            assert writer.append_data.call_args.args[0].shape == (6, 10, 3)
    else:
        target = saving.save_outputs(reader, dict(outputs, diagnostic=gray[0]), p,
                                     custom_path=tmp_path / "output", num_saving_workers=workers)
    for key, value in outputs.items():
        expected = media.prepare_png_image(saving.average_video(value))
        if enabled:
            expected = expected.resize((20, 12), Image.Resampling.BICUBIC)
        with Image.open(target / "png" / f"{key}.png") as image:
            np.testing.assert_array_equal(np.asarray(image), np.asarray(expected))
    with Image.open(target / "png/diagnostic.png") as image:
        assert image.size == (10, 6)
    with h5py.File(next(target.rglob("*.h5"))) as handle:
        assert "moment0_range_0_0_250" not in handle
        np.testing.assert_array_equal(handle["moment0"][:], gray)


@pytest.mark.parametrize("changes", [
    {"resize_averaged_images": 2}, {"moments_frequency_ranges": True},
    {"moments_frequency_ranges": None}, {"moments_frequency_ranges": [[1]]},
    {"moments_frequency_ranges": [[True, 3]]}, {"moments_frequency_ranges": [[3, 1]]},
    {"moments_frequency_ranges": [[-1, 3]]}, {"moments_frequency_ranges": [[0, float("inf")]]},
    {"moments_frequency_ranges": [[float("nan"), 3]]},
])
def test_invalid_parameters(changes):
    with pytest.raises((TypeError, ValueError)):
        validate_main_parameters(parameters(**changes))


def test_yaml_defaults():
    normal = yaml.safe_load((ROOT / "parameters/default_parameters_default.yaml").read_text())
    offline = yaml.safe_load((ROOT / "parameters/default_parameters_default_offline.yaml").read_text())
    assert normal["resize_averaged_images"] is normal["moments_frequency_ranges"] is False
    assert "frequency_bands" in normal and "frequency_bands" not in offline
    assert offline["resize_averaged_images"] is True
    assert offline["moments_frequency_ranges"] == [
        [1000, 2000], [2000, 3000], [3000, 6000], [6000, 18300], [18300, 39000], [30000, 39000]]
    validate_main_parameters(parameters())
    validate_main_parameters(parameters(moments_frequency_ranges=False))
    validate_main_parameters(parameters(moments_frequency_ranges=[]))
