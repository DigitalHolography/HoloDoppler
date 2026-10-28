"""Regression checks for power, averaging, backend selection and moment names."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from scipy.ndimage import gaussian_filter
import yaml

from holodoppler import backend
from holodoppler.cli import command
from holodoppler.cli.command import _apply_cli_overrides, _run_pipeline, PipelineMode
from holodoppler.config import validate_main_parameters
from holodoppler.core.image_utils import gaussian_flatfield
from holodoppler.pipelines import main_default as pipeline


def parameters(**updates):
    path = Path(__file__).resolve().parents[1] / "parameters/default_parameters_default.yaml"
    result = yaml.safe_load(path.read_text())
    result.update(
        backend="numpy", sampling_freq=800, pixel_pitch=[1e-6, 1e-6], z=.1,
        batch_size=8, batch_stride=8, first_frame=0, end_frame=-1,
        low_freq=0, high_freq=400, svd_threshold=0, svd_remove_dc=False,
        square=False, frequency_bands=[], image_registration=False,
        image_registration_with_ecc=False, shack_hartmann=False,
        shack_hartmann_autofocus=False, color_Doppler_image=False,
        directional_Doppler_image=False, save_spectograms=False,
        save_averaged_spectrogram=True,
    )
    result.update(updates)
    return result


@pytest.fixture(autouse=True)
def cpu_backend():
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    yield
    backend.set_backend(previous)


@pytest.mark.parametrize("sigma", [0, 1])
def test_flatfield_zero_background_has_no_divide_warnings(sigma):
    image = np.zeros((5, 7), np.float32)
    image[2, 3] = 4
    background = gaussian_filter(image, sigma)
    expected = np.divide(image, background, out=np.zeros_like(image), where=background != 0)
    with np.errstate(divide="raise", invalid="raise"):
        np.testing.assert_allclose(gaussian_flatfield(image, sigma, gaussian_filter), expected)
        np.testing.assert_array_equal(gaussian_flatfield(image * 0, sigma, gaussian_filter), 0)


@pytest.mark.parametrize("corner", [False, True])
def test_fft_is_unconditional_and_directional_receives_power(monkeypatch, corner):
    spectrum = np.arange(1, 9, dtype=np.float32)[:, None, None] * np.ones((8, 3, 5)) * (1 + 2j)
    transform = Mock(return_value=spectrum)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **k: spectrum)
    monkeypatch.setattr(pipeline, "svd_filter", lambda *a, **k: spectrum)
    monkeypatch.setattr(pipeline, "fourier_time_transform", transform)
    monkeypatch.setattr(pipeline, "corner_compensation", lambda xp, psd: psd * 3)
    directional = Mock(return_value=(np.ones((3, 5)), np.ones((3, 5))))
    monkeypatch.setattr(pipeline, "directional", directional)
    result = pipeline._process_batch(parameters(
        directional_Doppler_image=True, corner_compensation=corner), spectrum)
    transform.assert_called_once()
    expected = abs(spectrum) ** 2 * (3 if corner else 1)
    np.testing.assert_allclose(directional.call_args.args[2], expected)
    frequencies = np.fft.fftfreq(8, 1 / 800)
    selected = (abs(frequencies) > 0) & (abs(frequencies) < 400)
    for order in range(3):
        np.testing.assert_allclose(result[f"moment{order}"],
            (expected[selected] * frequencies[selected, None, None] ** order).sum(axis=0))
    assert {"moment0", "moment0ff", "moment1", "moment2"} <= result.keys()


@pytest.mark.parametrize("live", [False, True])
@pytest.mark.parametrize("ecc", [False, True])
@pytest.mark.parametrize("workers", [0, 2])
def test_psd_mean_uses_all_complete_batches(monkeypatch, live, ecc, workers):
    p = parameters(live_saving=live, image_registration_with_ecc=ecc,
                   numpy_num_workers=workers)
    frames = np.repeat(np.array([1, 3, 5], np.float32), 8)[:, None, None] * np.ones((24, 3, 5), np.float32)
    reader = SimpleNamespace(read_frames=lambda first_frame, batch_size, **kw:
        frames[first_frame:first_frame + batch_size].copy())

    def process(parameters, batch, **kwargs):
        image = batch[0].copy()
        return {"sh_psd": batch ** 2, "moment0": image,
                "moment0ff": image, "moment1": image, "moment2": image}, None

    monkeypatch.setattr(pipeline, "_process_one_batch", process)
    monkeypatch.setattr(pipeline, "register_with_ecc", lambda images, **kw: np.zeros((len(images), 2)))
    monkeypatch.setattr(pipeline, "apply_ecc_registration", lambda images, *a, **kw: images)
    saved = {}
    monkeypatch.setattr(pipeline, "save_outputs", lambda **kw: saved.update(kw["output"]))
    destination = Mock() if live else None
    if live:
        destination.write_static.side_effect = lambda name, value: saved.update({name: value})
    pipeline._process_to_output(reader, p, [0, 8, 16], destination, None)
    np.testing.assert_allclose(saved["averaged_spectrogram"], (1 + 9 + 25) / 3)


@pytest.mark.parametrize("mode", [PipelineMode.PREVIEW, PipelineMode.PROCESS])
@pytest.mark.parametrize("selection", ["numpy", "auto", "cupy"])
def test_cli_backend_override_reaches_each_default_entrypoint(monkeypatch, mode, selection):
    monkeypatch.setattr(command, "configure_logging", lambda: None)
    args = SimpleNamespace(tictoc=False, debug=False, backend=selection, dynamic_options={})
    p = _apply_cli_overrides(parameters(), args)
    reader = SimpleNamespace(extension=".raw", total_frames=0)
    monkeypatch.setattr(pipeline, "get_reader", lambda path: reader)
    choose = Mock(wraps=backend.set_backend)
    monkeypatch.setattr(backend, "set_backend", choose)
    # Force deterministic CPU fallback while still checking the requested selection.
    monkeypatch.setattr(backend, "_cupy_available", False)
    if mode == PipelineMode.PREVIEW:
        monkeypatch.setattr(pipeline, "_validate_reference_batch", lambda *a: None)
        reader.read_frames = lambda **kw: np.ones((8, 3, 5), np.float32)
        monkeypatch.setattr(pipeline, "_process_one_batch", lambda *a, **kw:
            ({f"moment{suffix}": np.ones((3, 5)) for suffix in ("0", "0ff", "1", "2")}, None))
        monkeypatch.setattr(pipeline, "save_outputs", lambda **kw: None)
    _run_pipeline(Path("input.raw"), p, mode)
    choose.assert_called_once_with(selection)
    assert backend.get_backend_name() == "numpy"


@pytest.mark.parametrize("selection", [None, True, 3, "invalid"])
def test_backend_configuration_rejects_invalid_choices(selection):
    with pytest.raises(ValueError, match="backend"):
        validate_main_parameters(parameters(backend=selection))


def test_temporal_transform_is_no_longer_configurable():
    validate_main_parameters(parameters())
    with pytest.raises(ValueError, match="removed"):
        validate_main_parameters(parameters(temporal_transformation="None"))
