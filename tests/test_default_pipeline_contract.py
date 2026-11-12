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
    result.pop("outputs", None)
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


@pytest.mark.parametrize("temporal_dc", [False, True])
@pytest.mark.parametrize("spatial_dc", [False, True])
@pytest.mark.parametrize("threshold", [-1, 0, 2])
def test_dc_output_and_filtered_spectrum(monkeypatch, temporal_dc, spatial_dc, threshold):
    rng = np.random.default_rng(17)
    frames = (rng.normal(size=(8, 3, 5)) + 1j * rng.normal(size=(8, 3, 5))).astype(np.complex64)
    frames += np.arange(8)[:, None, None] * (1 + 2j)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **k: frames.copy())
    transform = Mock(wraps=pipeline.fourier_time_transform)
    monkeypatch.setattr(pipeline, "fourier_time_transform", transform)
    p = parameters(svd_threshold=threshold, svd_remove_dc=temporal_dc,
                   svd_remove_spatial_dc=spatial_dc, svd_block_size_mib=.0002,
                   outputs={"svd_dc": ["h5"], "svd_dc_spatial": ["h5"]})
    result = pipeline._process_batch(p, frames)
    centered = frames.copy()
    temporal_mean = np.zeros(frames.shape[1:], dtype=frames.dtype)
    spatial_mean = None
    if threshold >= 0:
        if temporal_dc:
            temporal_mean = centered.mean(axis=0)
            centered -= temporal_mean
        if spatial_dc:
            spatial_mean = centered.mean(axis=(1, 2))
            centered -= spatial_mean[:, None, None]
    np.testing.assert_allclose(result["svd_dc"], np.abs(temporal_mean), atol=1e-5)
    if spatial_mean is None:
        assert "svd_dc_spatial" not in result
    else:
        assert result["svd_dc_spatial"].shape == (frames.shape[0],)
        np.testing.assert_allclose(result["svd_dc_spatial"], np.abs(spatial_mean), atol=1e-5)
    assert "pc_sum_static" not in result
    expected = pipeline.svd_filter(np, backend.linalg, centered, threshold,
                                   block_size_mib=.0002)
    np.testing.assert_allclose(transform.call_args.args[2], expected, atol=1e-5)
    # DC can serve as a reference without computing a temporal spectrum.
    transform.reset_mock()
    reference = pipeline._process_batch(dict(p, registration_image="svd_dc"), frames,
                                        reference_only=True)
    np.testing.assert_allclose(reference["svd_dc"], result["svd_dc"])
    transform.assert_not_called()


def test_spatial_dc_output_can_be_selected_alone(monkeypatch):
    frames = np.arange(8 * 3 * 5, dtype=np.float32).reshape(8, 3, 5).astype(np.complex64)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **k: frames.copy())
    result = pipeline._process_batch(parameters(
        svd_remove_spatial_dc=True, outputs={"svd_dc_spatial": ["csv"]}), frames)
    assert "svd_dc" not in result
    np.testing.assert_allclose(result["svd_dc_spatial"], np.abs(frames.mean(axis=(1, 2))),
                               rtol=1e-6, atol=1e-5)


@pytest.mark.parametrize("rules, selected", [
    (None, False), ({}, False), ({"eigen_spectrogram": []}, False),
    ({"eigen_spectrogram": ["h5"]}, True), ({"eigen_*": ["h5"]}, True),
    ({"eigen_*": ["h5"], "eigen_spectrogram": [],
      "eigen_spectrogram_time_projection": []}, False),
])
def test_eigen_spectrogram_selection(monkeypatch, rules, selected):
    frames = np.random.default_rng(21).normal(size=(8, 3, 5)).astype(np.complex64)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **k: frames.copy())
    eigen_fft = Mock(wraps=np.fft.fft)
    monkeypatch.setattr(np.fft, "fft", eigen_fft)
    p = parameters()
    if rules is not None:
        p["outputs"] = rules
    result = pipeline._process_batch(p, frames)
    assert ("eigen_spectrogram" in result) == selected
    assert eigen_fft.call_count == int(selected)


def test_eigen_spectrogram_preserved_by_spatial_operations(monkeypatch):
    frames = np.random.default_rng(21).normal(size=(8, 3, 5)).astype(np.complex64)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **k: frames.copy())
    monkeypatch.setattr(pipeline, "_prepare_batch_frames", lambda p, f, phase, res: (f, phase))
    monkeypatch.setattr(pipeline, "register_images_shifts", lambda *a, **kw: (1., 2.))
    # A visible change to spatial arrays catches accidental spectrum registration.
    monkeypatch.setattr(pipeline, "apply_register_images_shifts", lambda xp, value, **kw: value + 10)
    p = parameters(square=True, image_registration=True,
                   outputs={"eigen_spectrogram": ["h5"], "moment0ff": ["h5"]})
    expected = pipeline._process_batch(p, frames)["eigen_spectrogram"]
    result, _ = pipeline._process_one_batch(p, frames, registration_ref=np.ones((3, 5)))
    resize = Mock(wraps=pipeline.resize_frames)
    monkeypatch.setattr(pipeline, "resize_frames", resize)
    finished = pipeline._finalize_spatial_result(result, p)
    np.testing.assert_array_equal(finished["eigen_spectrogram"], expected)
    assert all(call.args[2] is not result["eigen_spectrogram"] for call in resize.call_args_list)


@pytest.mark.parametrize("value", [1, "true", None])
def test_invalid_spatial_dc_option(value):
    with pytest.raises(TypeError, match="svd_remove_spatial_dc"):
        validate_main_parameters(parameters(svd_remove_spatial_dc=value))


@pytest.mark.parametrize("level", [None, 0, 1, 9])
def test_h5_compression_parameter_valid(level):
    validate_main_parameters(parameters(h5compression=level))


@pytest.mark.parametrize("level, error", [(-1, ValueError), (10, ValueError),
                                         (True, TypeError), (1.5, TypeError), ("4", TypeError)])
def test_h5_compression_parameter_invalid(level, error):
    with pytest.raises(error, match="h5compression"):
        validate_main_parameters(parameters(h5compression=level))


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("welch", [False, True])
@pytest.mark.parametrize("remove_dc", [False, True])
def test_gaussian_width_svd_follows_prefilter(monkeypatch, enabled, welch, remove_dc):
    rng = np.random.default_rng(42)
    holograms = (rng.normal(size=(8, 3, 5)) + 1j * rng.normal(size=(8, 3, 5))).astype(np.complex64)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **k: holograms)
    p = parameters(
        compute_gaussian_width=True, registration_image="gaussian_width",
        compute_gaussian_width_prefilter_low_freq=100,
        compute_gaussian_width_svd_filter=enabled,
        compute_gaussian_width_svd_threshold=1,
        compute_gaussian_width_svd_remove_dc=remove_dc,
        welch_enabled=welch, welch_batch_size=8, welch_stride=8,
    )
    frequencies = np.fft.fftfreq(8, 1 / 800)
    response = np.zeros(8)
    nonzero = frequencies != 0
    response[nonzero] = 1 / (1 + (100 / abs(frequencies[nonzero])) ** 8)
    spectrum = backend.fft.fft(holograms, axis=0, norm="ortho") * np.sqrt(response[:, None, None])
    if enabled:
        temporal = backend.fft.ifft(spectrum, axis=0, norm="ortho")
        filtered = pipeline.svd_filter(np, backend.linalg, temporal, 1, remove_dc=remove_dc)
        spectrum = backend.fft.fft(filtered, axis=0, norm="ortho")
    expected = abs(spectrum) ** 2
    svd = Mock(wraps=pipeline.svd_filter)
    monkeypatch.setattr(pipeline, "svd_filter", svd)
    welch_filter = Mock(side_effect=AssertionError("Gaussian width must not use Welch"))
    monkeypatch.setattr(pipeline, "welch_power_spectrum", welch_filter)
    width = Mock(return_value=np.ones((3, 5)))
    monkeypatch.setattr(pipeline, "gaussian_width", width)
    pipeline._process_batch(p, holograms, reference_only=True)
    np.testing.assert_allclose(width.call_args.args[1], expected, rtol=1e-5, atol=1e-5)
    assert svd.call_count == int(enabled)
    if enabled:
        assert svd.call_args.kwargs["remove_dc"] is remove_dc
        assert np.iscomplexobj(svd.call_args.args[2])
        np.testing.assert_allclose(svd.call_args.args[2], temporal, rtol=1e-5, atol=1e-5)
    welch_filter.assert_not_called()


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


def test_pca_sum_averages_full_packets_before_svd(monkeypatch):
    from holodoppler.core.filtering import pca_time_transform
    from holodoppler.saving.policy import save_to_hdf5
    rng = np.random.default_rng(12)
    frames = (rng.normal(size=(10, 3, 5)) + 1j * rng.normal(size=(10, 3, 5))).astype(np.complex64)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **k: frames.copy())
    def svd(xp, linalg, holograms, *args, **kwargs):
        holograms[:] = 0
        return holograms
    monkeypatch.setattr(pipeline, "svd_filter", svd)
    expected = np.mean([np.abs(pca_time_transform(np, frames[i:i+4]))[:2].sum(axis=0)
                        for i in (0, 4)], axis=0)
    p = parameters(pca_compute=True, pca_time_window=4, pca_index_range=[0, 2])
    result = pipeline._process_batch(p, frames)
    np.testing.assert_allclose(result["pca_sum"], expected)
    assert save_to_hdf5("pca_sum")
    assert "pca_sum" not in pipeline._process_batch(dict(p, pca_compute=False), frames)
    assert "pca_sum" not in pipeline._process_batch(p, frames, reference_only=True)


@pytest.mark.parametrize("updates", [
    {"pca_compute": 1}, {"pca_time_window": 0},
    {"pca_index_range": [0, 33]}, {"pca_index_range": [2, 2]},
    {"pca_compute": True, "pca_time_window": 32},
])
def test_invalid_pca_parameters(updates):
    with pytest.raises((TypeError, ValueError), match="pca_"):
        validate_main_parameters(parameters(**updates))


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("dc", [False, True])
@pytest.mark.parametrize("global_threshold", [-1, 0, 1])
def test_block_svd_follows_global(monkeypatch, enabled, dc, global_threshold):
    from holodoppler.core.filtering import svd_filter, svd_filter_by_bloc
    data = (np.random.default_rng(7).normal(size=(8, 3, 5)) + 2j).astype(np.complex64)
    monkeypatch.setattr(pipeline, "fresnel_transform", lambda *a, **k: data)
    global_filter = Mock(wraps=svd_filter)
    local_filter = Mock(wraps=svd_filter_by_bloc)
    transform = Mock(wraps=pipeline.fourier_time_transform)
    monkeypatch.setattr(pipeline, "svd_filter", global_filter)
    monkeypatch.setattr(pipeline, "svd_filter_by_bloc", local_filter)
    monkeypatch.setattr(pipeline, "fourier_time_transform", transform)
    pipeline._process_batch(parameters(svd_filter_by_bloc=enabled,
        svd_filter_by_bloc_window_size=2, svd_filter_by_bloc_threshold=0,
        svd_threshold=global_threshold, svd_remove_dc=dc), data)
    expected = svd_filter(np, np.linalg, data, global_threshold, remove_dc=dc)
    global_filter.assert_called_once()
    assert local_filter.call_count == int(enabled)
    if enabled:
        np.testing.assert_allclose(local_filter.call_args.args[2], expected, atol=1e-6)
        assert local_filter.call_args.kwargs["remove_dc"] == dc
        expected = svd_filter_by_bloc(np, np.linalg, expected, 2, 0, dc)
    np.testing.assert_allclose(transform.call_args.args[2], expected, atol=1e-6)



@pytest.mark.parametrize("live", [False, True])
def test_cancellation_after_batches_skips_default_finalization(monkeypatch, live):
    from threading import Event
    from holodoppler.core.progress import ProgressReporter, ProcessingCancelled

    stop = Event()
    p = parameters(live_saving=live, numpy_num_workers=0)
    monkeypatch.setattr(pipeline, "run_batches", lambda *args, **kwargs: stop.set())
    save = Mock()
    monkeypatch.setattr(pipeline, "save_outputs", save)
    destination = Mock() if live else None
    with pytest.raises(ProcessingCancelled):
        pipeline._process_to_output(
            SimpleNamespace(), p, [0], destination,
            ProgressReporter(lambda *args: None, stop),
        )
    save.assert_not_called()
    if live:
        destination.add_batch.assert_not_called()
        destination.write_static.assert_not_called()
