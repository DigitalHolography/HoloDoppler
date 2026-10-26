from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import cv2
import h5py
import numpy as np
from PIL import Image
import pytest
from scipy.ndimage import gaussian_filter
import yaml

from holodoppler import backend, saving
from holodoppler.saving import media as saving_media
from holodoppler.config import validate_main_parameters
from holodoppler.core.doppler_images import directional, construct_colored_image, construct_colored_image_lab, construct_directional_image
from holodoppler.pipelines import main_default


@pytest.fixture(autouse=True)
def cpu():
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    yield
    backend.set_backend(previous)


def params(**updates):
    p = yaml.safe_load((Path(__file__).resolve().parents[1] /
                       "parameters/default_parameters_default.yaml").read_text())
    p.update(force_numpy=True, batch_size=8, batch_stride=8, first_frame=0,
             end_frame=-1, skip_every=1, sampling_freq=1000, low_freq=0, high_freq=450,
             pixel_pitch=[1e-6, 1e-6], z=.1, numpy_num_workers=2,
             svd_threshold=0, svd_remove_dc=False, filter2d=False,
             shack_hartmann=False, shack_hartmann_autofocus=False,
             image_registration=False, image_registration_with_ecc=False,
             registration_ref_first_frame=0, registration_ref_batch_size=8,
             registration_flatfield_gw=1, frequency_bands=[], square=False,
             save_spectograms=False, save_averaged_spectrogram=False,
             color_Doppler_image=True, directional_Doppler_image=True,
             color_Doppler_low_frequency_band=[0, 200],
             color_Doppler_high_frequency_band=[200, 500],
             directional_Doppler_frequency_band=[125, 375],
             directional_Doppler_gaussian_width=1, overwrite_option="erase")
    p.update(updates)
    return p


@pytest.mark.parametrize("n", [7, 8])
@pytest.mark.parametrize("width", [0, 1.2])
def test_directional_intervals_and_normalization(n, width):
    sh = np.random.default_rng(2).normal(size=(n, 3, 5)) + 1j
    first, last = 1, 3
    pos = np.abs(sh[first - 1:last]).sum(axis=0)
    neg = np.abs(sh[n - last:n - first + 1]).sum(axis=0)
    background = pos + neg
    if width:
        background = gaussian_filter(background, width, mode="nearest", radius=int(np.ceil(2 * width)))
    expected_pos = pos / background
    expected_pos *= pos.sum() / expected_pos.sum()
    expected_neg = neg / background
    expected_neg *= neg.sum() / expected_neg.sum()
    actual_pos, actual_neg = directional(np, gaussian_filter, sh, 1, 3, n, width)
    np.testing.assert_allclose(actual_pos, expected_pos)
    np.testing.assert_allclose(actual_neg, expected_neg)
    assert actual_pos.sum() == pytest.approx(pos.sum())
    assert actual_neg.sum() == pytest.approx(neg.sum())


def test_empty_spectrum_and_flat_composites_are_finite():
    pos, neg = directional(np, gaussian_filter, np.zeros((8, 1, 1)), 0, 100, 8, 1)
    assert np.all(pos == 0) and np.all(neg == 0)
    assert np.all(construct_directional_image(np, pos, neg) == 0)
    assert np.all(construct_colored_image(np, np.ones((2, 3)), np.ones((2, 3)))[0] == 0)


def test_lab_composite_channels_and_cv2_srgb():
    m0, low, high = np.random.default_rng(3).uniform(0, 10, (3, 5, 7))
    lightness = (m0 - m0.min()) / np.ptp(m0) * 100
    a = high - high.mean()
    b = low - low.mean()
    a *= 127 / np.abs(a).max()
    b *= 127 / np.abs(b).max()
    lab = np.stack([lightness, a - .7 * b, -.7 * b], axis=-1).astype(np.float32)
    expected = np.clip(cv2.cvtColor(lab, cv2.COLOR_Lab2RGB), 0, 1)
    np.testing.assert_allclose(construct_colored_image_lab(np, m0, low, high), expected, atol=.004)
    stacked = construct_colored_image_lab(np, np.stack([m0, 3 * m0]),
                                     np.stack([low, 2 * low]), np.stack([high, 4 * high]))
    np.testing.assert_array_equal(stacked[0], stacked[1])


def test_decorrelation_preserves_channel_statistics_and_removes_correlation():
    from holodoppler.core.doppler_images import _decorrelation_stretch
    source = np.random.default_rng(24).normal(size=(20, 30, 3))
    source = source @ np.array([[1, .6, .4], [.1, 2, .7], [.2, .3, .8]]) + [2, 5, 9]
    result = _decorrelation_stretch(np, source)
    np.testing.assert_allclose(result.mean(axis=(0, 1)), source.mean(axis=(0, 1)), atol=4e-6)
    np.testing.assert_allclose(result.std(axis=(0, 1), ddof=1), source.std(axis=(0, 1), ddof=1), atol=4e-6)
    covariance = np.cov(result.reshape(-1, 3), rowvar=False)
    np.testing.assert_allclose(covariance - np.diag(np.diag(covariance)), 0, atol=1e-6)
    # The stretch retains scientific float values rather than clipping for display.
    assert result.max() > 1


@pytest.mark.parametrize("shape", [(5, 7), (1, 7), (5, 1), (1, 1)])
def test_multiband_composite_handles_duplicate_and_constant_channels(shape):
    low = np.arange(np.prod(shape), dtype=float).reshape(shape)
    high = np.flip(low, axis=-1) ** 2
    rgb, img_low, img_high = construct_colored_image(np, low, high)
    assert rgb.shape == (*shape, 3)
    assert rgb.dtype == np.float32 and np.isfinite(rgb).all()
    np.testing.assert_allclose(rgb[..., 1], rgb[..., 2], atol=1e-6)
    assert img_low.shape == img_high.shape == shape
    if np.prod(shape) == 1:
        np.testing.assert_array_equal(rgb, np.zeros((*shape, 3)))


def test_multiband_stack_is_averaged_before_rescaling():
    low = np.array([[[0., 3.], [1., 2.]], [[8., 2.], [5., 1.]]])
    high = low[:, ::-1, :] ** 2
    stacked = construct_colored_image(np, low, high)
    expected = construct_colored_image(np, low.mean(axis=0), high.mean(axis=0))
    for actual, reference in zip(stacked, expected):
        np.testing.assert_array_equal(actual, reference)


def test_unclipped_rgb_is_averaged_before_display_clipping(tmp_path, monkeypatch):
    video = np.stack([np.full((6, 10, 3), -.4, np.float32),
                      np.full((6, 10, 3), .8, np.float32)])
    expected = saving.cast_png_data(video.mean(axis=0, dtype=np.float64))
    np.testing.assert_array_equal(saving.average_video(video), expected)
    assert expected[0, 0, 0] == 51  # Clipping inputs first would instead give 102.
    monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *args: Mock())
    reader = SimpleNamespace(file_path=tmp_path / "input.raw", extension=".raw")
    with saving.OutputClass(reader, {}, custom_path=tmp_path / "output") as destination:
        for index, frame in enumerate(video):
            destination.add("color_Doppler_image", frame, index)
    np.testing.assert_array_equal(np.array(Image.open(destination.target_dir / "png/color_Doppler_image.png")), expected)
    with h5py.File(destination.target_dir / "h5/output_output.h5") as handle:
        assert "color_Doppler_image" not in handle


def test_directional_hsv_formula_and_balanced_pixels():
    from colorsys import hsv_to_rgb
    def stretch(image, tol):
        bins = np.rint(image.ravel() * 65535).astype(int)
        cdf = np.cumsum(np.bincount(bins, minlength=65536)) / image.size
        lo = np.searchsorted(cdf, tol[0], side="right") / 65535
        hi = np.searchsorted(cdf, tol[1], side="left") / 65535
        if lo >= hi:
            lo, hi = 0, 1
        return np.clip((image - lo) / (hi - lo), 0, 1)
    pos, neg = np.random.default_rng(5).uniform(1, 100, (2, 8, 10))
    pos[0, 0] = neg[0, 0]
    low, high = min(pos.min(), neg.min()), max(pos.max(), neg.max())
    p, n = (pos - low) / (high - low), (neg - low) / (high - low)
    diff = p - n
    sat = .7 * stretch(abs(diff), [.6, .999])
    brightness = (p + n) / 2
    brightness -= brightness.mean()
    brightness = (brightness - brightness.min()) / np.ptp(brightness)
    brightness = stretch(brightness, [.02, .998])
    expected = np.zeros((*pos.shape, 3), np.float32)
    for index in np.ndindex(pos.shape):
        if diff[index]:
            expected[index] = hsv_to_rgb(1 if diff[index] > 0 else .66, sat[index], brightness[index])
    expected = (expected - expected.min()) / np.ptp(expected)
    actual = construct_directional_image(np, pos, neg)
    np.testing.assert_allclose(actual, expected, atol=2e-7)
    assert actual.dtype == np.float32
    np.testing.assert_array_equal(actual[0, 0], [0, 0, 0])
    stacked = construct_directional_image(np, np.stack([pos, pos * 3]), np.stack([neg, neg * 3]))
    np.testing.assert_allclose(stacked[0], actual)
    np.testing.assert_allclose(stacked[1], actual)


@pytest.mark.parametrize("lab", [False, True])
@pytest.mark.parametrize("square", [False, True])
@pytest.mark.parametrize("ecc", [False, True])
@pytest.mark.parametrize("workers", [0, 2])
def test_default_doppler_video_average_and_preview(tmp_path, monkeypatch, square, ecc, workers, lab):
    frames = np.random.default_rng(55).uniform(1, 100, (24, 6, 10)).astype(np.float32)
    reader = SimpleNamespace(file_path=tmp_path / "input.raw", extension=".raw", total_frames=24,
                             read_frames=lambda first_frame, batch_size, skip_every=None:
                             frames[first_frame:first_frame + batch_size * (skip_every or 1):skip_every or 1].copy())
    monkeypatch.setattr(main_default, "get_reader", lambda _: reader)
    monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *args: Mock())
    monkeypatch.setattr(saving_media, "save_video", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_default, "register_with_ecc", lambda values, **kwargs: np.zeros((len(values), 12)))
    monkeypatch.setattr(main_default, "apply_ecc_registration", lambda values, *args, **kwargs:
                        np.roll(values, 1, axis=-1))
    snapshots = []
    for live in (True, False):
        p = params(live_saving=live, square=square, image_registration=True, color_Doppler_use_lab=lab,
                   image_registration_with_ecc=ecc, num_saving_workers=workers)
        main_default.process(reader.file_path, p)
        path = next(tmp_path.rglob("*_output.h5"))
        with h5py.File(path) as handle:
            assert not any(key.startswith("_") for key in handle)
            assert "color_Doppler_image" not in handle
            assert "directional_Doppler_image" not in handle
            assert "moment0" in handle
        outputs = {}
        for name in ("color_Doppler_image", "directional_Doppler_image"):
            image = np.array(Image.open(path.parent.parent / "png" / f"{name}.png"))
            assert image.shape == (10 if square else 6, 10, 3)
            outputs[name] = image
        snapshots.append(outputs)
    for key in snapshots[0]:
        np.testing.assert_array_equal(snapshots[0][key], snapshots[1][key])
    main_default.preview(reader.file_path, p)
    preview_path = next(tmp_path.rglob("preview_output.h5"))
    with h5py.File(preview_path) as handle:
        assert "color_Doppler_image" not in handle
        assert "directional_Doppler_image" not in handle
    for name in ("color_Doppler_image", "directional_Doppler_image"):
        image = np.array(Image.open(preview_path.parent.parent / "png" / f"{name}.png"))
        assert image.shape == (10 if square else 6, 10, 3)


def test_disabled_outputs_do_not_compute_directional(monkeypatch):
    monkeypatch.setattr(main_default, "directional", Mock(side_effect=AssertionError("unexpected computation")))
    p = params(color_Doppler_image=False, directional_Doppler_image=False)
    result = main_default._process_batch(p, np.ones((8, 6, 10), np.float32))
    assert not any("Doppler" in key for key in result)


def test_rgb_average_does_not_renormalize_channels():
    video = np.array([[[[10, 20, 40]]], [[[20, 40, 80]]]], np.uint8)
    np.testing.assert_array_equal(saving.average_video(video), [[[15, 30, 60]]])


def test_float_rgb_average_preserves_sub_byte_values(tmp_path, monkeypatch):
    # Quantizing the input frames first gives mean byte value 0.5 -> 0;
    # averaging their original float values gives byte value 0.7 -> 1.
    video = np.stack([np.full((6, 10, 3), .1 / 255, np.float32),
                      np.full((6, 10, 3), 1.3 / 255, np.float32)])
    np.testing.assert_array_equal(saving.average_video(video), np.ones((6, 10, 3), np.uint8))
    monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *args: Mock())
    reader = SimpleNamespace(file_path=tmp_path / "input.raw", extension=".raw")
    with saving.OutputClass(reader, {}, custom_path=tmp_path / "output") as destination:
        for index, frame in enumerate(video):
            destination.add("directional_Doppler_image", frame, index)
    actual = np.array(Image.open(destination.target_dir / "png/directional_Doppler_image.png"))
    np.testing.assert_array_equal(actual, np.ones((6, 10, 3), np.uint8))
    with h5py.File(destination.target_dir / "h5/output_output.h5") as handle:
        assert "directional_Doppler_image" not in handle


@pytest.mark.parametrize("hues", [[1, .66], [.08, .5], [.83, .33], [.75, .16]])
def test_directional_palette_changes_only_hues(hues):
    pos, neg = np.random.default_rng(19).random((2, 6, 10))
    image = construct_directional_image(np, pos, neg, hues)
    assert image.dtype == np.float32 and image.min() >= 0 and image.max() <= 1
    default = construct_directional_image(np, pos, neg)
    np.testing.assert_allclose(image.max(axis=-1), default.max(axis=-1), atol=1e-6)


def test_doppler_rgb_real_encoder_round_trip(tmp_path):
    import imageio.v2 as imageio
    reader = SimpleNamespace(file_path=tmp_path / "input.raw", extension=".raw")
    red = np.zeros((6, 10, 3), np.float32)
    red[..., 0] = 240 / 255
    blue = np.zeros_like(red)
    blue[..., 2] = 200 / 255
    with saving.OutputClass(reader, {"overwrite_option": "erase"}, custom_path=tmp_path / "output") as output:
        for index, frame in enumerate((red, blue)):
            output.add_batch({"color_Doppler_image": frame, "directional_Doppler_image": frame}, index)
    for name in ("color_Doppler_image", "directional_Doppler_image"):
        for fmt in ("avi", "mp4"):
            with imageio.get_reader(str(output.target_dir / fmt / f"{name}.{fmt}")) as video:
                first, second = video.get_data(0), video.get_data(1)
            assert first.shape == second.shape == (6, 10, 3)
            assert first[..., 0].mean() > first[..., 2].mean() + 100
            assert second[..., 2].mean() > second[..., 0].mean() + 100
        np.testing.assert_array_equal(np.array(Image.open(output.target_dir / "png" / f"{name}.png")),
                                      saving.cast_png_data((red.astype(float) + blue) / 2))


@pytest.mark.parametrize("name", ["color_Doppler_image", "directional_Doppler_image"])
def test_outputs_can_be_enabled_independently(name):
    from holodoppler.core.doppler_images import finish_doppler_images
    p = params(**{**dict(color_Doppler_image=False, directional_Doppler_image=False), name: True})
    result = main_default._process_batch(p, np.random.default_rng(14).uniform(1, 100, (8, 6, 10)).astype(np.float32))
    finish_doppler_images(result, np)
    assert name in result
    assert len(set(result) & {"color_Doppler_image", "directional_Doppler_image"}) == 1


def test_directional_uses_main_band_and_effective_sampling_frequency(monkeypatch):
    spy = Mock(wraps=main_default.directional)
    monkeypatch.setattr(main_default, "directional", spy)
    p = params(color_Doppler_image=False, directional_Doppler_frequency_band=None, skip_every=2)
    main_default._process_batch(p, np.random.default_rng(15).random((8, 6, 10)).astype(np.float32))
    assert spy.call_args.args[3:6] == (p["low_freq"], p["high_freq"], 500)


@pytest.mark.parametrize("changes", [
    {"color_Doppler_image": 1},
    {"color_Doppler_use_lab": "yes"},
    {"color_Doppler_low_frequency_band": [200, 0]},
    {"directional_Doppler_frequency_band": [-1, 200]},
    {"directional_Doppler_gaussian_width": -1},
    {"directional_Doppler_hues": [0, 2]},
    {"temporal_transformation": "None"},
])
def test_doppler_parameter_validation(changes):
    with pytest.raises((ValueError, TypeError)):
        validate_main_parameters(params(**changes))
