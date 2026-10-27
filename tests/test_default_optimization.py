"""Numerical and data-flow regressions for the default pipeline optimizations."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
import yaml
from scipy import fft, linalg, ndimage

from holodoppler import backend
from holodoppler.core import filtering, moments, propagation, registration
from holodoppler.pipelines import main_default as pipeline


@pytest.fixture(autouse=True)
def numpy_backend():
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    yield
    backend.set_backend(previous)


def params(**changes):
    values = yaml.safe_load((Path(__file__).resolve().parents[1]
                            / "parameters/default_parameters_default.yaml").read_text())
    values.update(batch_size=4, batch_stride=4, first_frame=0, end_frame=-1,
                  sampling_freq=1000, low_freq=0, high_freq=500,
                  pixel_pitch=[1e-6, 1e-6], z=.1, numpy_num_workers=1,
                  svd_threshold=1, registration_ref_first_frame=0,
                  registration_ref_batch_size=4, shack_hartmann_autofocus_batch_size=4,
                  registration_flatfield_gw=1, shack_hartmann=False,
                  image_registration=False, square=False, frequency_bands=[],
                  save_spectograms=False, save_averaged_spectrogram=False,
                  color_Doppler_image=False, directional_Doppler_image=False)
    values.update(changes)
    return values


def normalized_error(actual, expected):
    return np.max(np.abs(actual - expected), initial=0) / max(
        np.max(np.abs(expected), initial=0), 1)


@pytest.mark.parametrize("dtype", [np.float32, np.float64, np.complex64, np.complex128])
@pytest.mark.parametrize("remove_dc", [False, True])
@pytest.mark.parametrize("mode,threshold", [
    ("number_of_values", 0), ("number_of_values", 2),
    ("number_of_values", 20), ("amplitude_threshold", 80),
])
def test_blocked_svd_projection_and_diagnostics(monkeypatch, dtype, remove_dc, mode, threshold):
    rng = np.random.default_rng(37)
    data = rng.normal(size=(6, 7, 9)) * np.arange(1, 7)[:, None, None]
    if np.issubdtype(dtype, np.complexfloating):
        data = data + 1j * rng.normal(size=data.shape)
    data = data.astype(dtype)
    original = data.copy()
    # Multiple blocks, with a final partial block.
    block_size_mib = 6 * data.dtype.itemsize * 11 / 1024**2
    reference = data.astype(np.complex128 if np.iscomplexobj(data) else np.float64)
    if remove_dc:
        reference -= reference.mean(axis=0)
    matrix = reference.reshape(6, -1).T
    cov = matrix.conj().T @ matrix
    values, vectors = linalg.eigh(cov)
    values, vectors = values[::-1], vectors[:, ::-1]
    selected = vectors[:, :min(threshold, 6)] if mode == "number_of_values" else vectors[:, values > threshold]
    expected = (matrix - (matrix @ selected) @ selected.conj().T).T.reshape(data.shape)
    diagnostic = {}
    actual = filtering.svd_filter(np, linalg, data, threshold, mode, remove_dc, diagnostic, block_size_mib=block_size_mib)
    assert actual.dtype == data.dtype
    assert normalized_error(actual, expected) <= 1e-3
    np.testing.assert_array_equal(data, original)
    np.testing.assert_allclose(diagnostic["covariance"], cov, rtol=2e-6, atol=1e-4)
    assert diagnostic["kept_data"].shape == data.shape
    assert diagnostic["removed_features"].shape == (*data.shape[1:], selected.shape[1])
    if remove_dc:
        np.testing.assert_allclose(diagnostic["dc"], data.mean(axis=0), atol=2e-6)
    else:
        assert diagnostic["dc"] is None
    assert filtering.svd_filter(np, linalg, data, -1) is data


def test_svd_noncontiguous_and_subapertures(monkeypatch):
    block_size_mib = 256 / 1024**2
    rng = np.random.default_rng(9)
    source = (rng.normal(size=(5, 7, 9)) + 1j).astype(np.complex64)
    data = source.swapaxes(1, 2)
    actual = filtering.svd_filter(np, linalg, data, 2, block_size_mib=block_size_mib)
    expected = filtering.svd_filter(np, linalg, data.copy(), 2, block_size_mib=block_size_mib)
    np.testing.assert_allclose(actual, expected, atol=1e-5)
    subaps = rng.normal(size=(2, 3, 4, 5, 6)).astype(np.float32)
    original = subaps.copy()
    original_filter = filtering._svd_filter_matrix
    def filter_view(xp, linalg, data, output, *args, **kwargs):
        assert data.ndim == 3
        assert np.shares_memory(data, subaps)
        return original_filter(xp, linalg, data, output, *args, **kwargs)
    with monkeypatch.context() as local:
        local.setattr(filtering, "_svd_filter_matrix", filter_view)
        actual = filtering.svd_filter_batched(np, subaps, 2, block_size_mib=block_size_mib)
    for y in range(2):
        for x in range(3):
            expected = filtering.svd_filter(np, linalg, subaps[y, x].transpose(2, 0, 1), 2)
            np.testing.assert_allclose(actual[y, x], expected.transpose(1, 2, 0), atol=2e-5)
    np.testing.assert_array_equal(subaps, original)


@pytest.mark.parametrize("n", [7, 8, 9, 16])
@pytest.mark.parametrize("band", [(0, 500), (125, 375), (0, None), (500, 600), (-1, None)])
def test_frequency_slices_and_moments(n, band):
    freqs = fft.fftfreq(n, 1 / 1000)
    mask = abs(freqs) > band[0]
    if band[1] is not None:
        mask &= abs(freqs) < band[1]
    slices = filtering.symmetric_frequency_slices(n, 1000, *band)
    indices = np.concatenate([np.arange(part.start, part.stop) for part in slices]) if slices else np.array([], dtype=int)
    np.testing.assert_array_equal(indices, np.flatnonzero(mask))
    psd = np.random.default_rng(n).random((n, 6, 8)).astype(np.float32)
    actual = pipeline._band_moments(psd, 1000, *band, [0, 1, 2])
    for order, image in enumerate(actual):
        expected = (psd[mask].astype(np.float64) * freqs[mask, None, None] ** order).sum(axis=0)
        assert image.dtype == np.float64
        assert normalized_error(image, expected) <= 1e-4
    summed = pipeline._band_moments(psd, 1000, *band, [0])[0]
    np.testing.assert_allclose(summed, psd[mask].sum(axis=0), rtol=2e-6)


def test_moment_cancellation_empty_input_and_khz():
    data = np.ones((2, 3, 4), dtype=np.float32)
    freqs = np.array([1e4, -1e4], dtype=np.float64)
    actual = moments.moments(np, data, freqs, [0, 1, 2])
    assert all(value.dtype == np.float64 for value in actual)
    np.testing.assert_array_equal(actual[1], 0)
    np.testing.assert_array_equal(moments.moment_khz(np, data, freqs, 2), 200)
    assert moments.moments(np, data, freqs, []) == []
    for image in moments.moments(np, data[:0], freqs[:0], [0, 1, 2]):
        np.testing.assert_array_equal(image, np.zeros((3, 4)))


@pytest.mark.parametrize("autofocus", ["accepted", "rejected", "disabled"])
@pytest.mark.parametrize("reference_size,autofocus_size", [(4, 4), (8, 8), (8, 4)])
@pytest.mark.parametrize("skip", [1, 2])
def test_reference_uses_autofocus_and_reuses_matching_frames(monkeypatch, autofocus, reference_size, autofocus_size, skip):
    p = params(image_registration=True, shack_hartmann_autofocus=autofocus != "disabled",
               registration_ref_batch_size=reference_size,
               shack_hartmann_autofocus_batch_size=autofocus_size,
               skip_every=skip, filter2d=True)
    data = np.random.default_rng(5).random((32, 6, 8)).astype(np.float32)
    reader = SimpleNamespace(total_frames=32)
    reader.read_frames = Mock(side_effect=lambda first_frame, batch_size, skip_every:
                              data[first_frame:first_frame + batch_size * skip_every:skip_every].copy())
    phase = np.linspace(0, .5, 48, dtype=np.float32).reshape(6, 8)
    correction = np.exp(-1j * phase)
    def autofocus_result(parameters, frames, output_dict=None, diagnostics=None):
        output_dict.update(shack_hartmann_zernike_coefs=np.array([2 if autofocus == "rejected" else 1, 0, 0]),
                           shack_hartmann_wavefront_phase=phase)
        return correction
    monkeypatch.setattr(pipeline, "_process_shack_hartmann", autofocus_result)
    original = pipeline._process_batch
    calls, references, saved = [], [], {}
    def processing(parameters, frames, **options):
        calls.append((options.get("reference_only", False), options.get("phase_term")))
        return original(parameters, frames, **options)
    monkeypatch.setattr(pipeline, "_process_batch", processing)
    def shifts(xp, fft, fixed, moving, **options):
        references.append(fixed.copy())
        return 0, 0
    monkeypatch.setattr(pipeline, "register_images_shifts", shifts)
    monkeypatch.setattr(pipeline, "save_outputs", lambda **options: saved.update(options["output"]))
    pipeline._process_to_output(reader, p, [0, 4 * skip], None, None)
    for _, actual in calls:
        if autofocus == "accepted":
            np.testing.assert_array_equal(actual, correction)
        else:
            assert actual is None
    assert calls[0][0] == (reference_size != 4)
    explicit = reference_size != 4
    expected_reads = 2 + int(explicit) + int(autofocus != "disabled")
    if explicit and autofocus != "disabled" and reference_size == autofocus_size:
        expected_reads -= 1
    assert reader.read_frames.call_count == expected_reads
    for call in reader.read_frames.call_args_list:
        assert call.kwargs["skip_every"] == skip
    ref_frames = data[:reference_size * skip:skip]
    ref_frames = filtering.filter_2d(np, fft, ref_frames, p["filter2d_low"])
    expected = original(p, ref_frames, phase_term=correction if autofocus == "accepted" else None,
                        reference_only=True)["M0ff"]
    np.testing.assert_allclose(references[0], expected, rtol=2e-5, atol=1e-6)
    assert saved["moment0"].dtype == np.float64


def test_reference_only_avoids_doppler_and_spectrograms(monkeypatch):
    p = params(shack_hartmann_autofocus=False, color_Doppler_image=True,
               directional_Doppler_image=True, save_spectograms=True,
               save_averaged_spectrogram=True, frequency_bands=[[0, 400]])
    monkeypatch.setattr(pipeline, "directional", Mock(side_effect=AssertionError("unused output")))
    frames = np.random.default_rng(11).random((4, 6, 8)).astype(np.float32)
    result = pipeline._process_batch(p, frames, reference_only=True)
    assert set(result) == {"M0", "M0ff"}


@pytest.mark.parametrize("ecc", [False, True])
@pytest.mark.parametrize("live", [False, True])
@pytest.mark.parametrize("lab", [False, True])
def test_finalization_matches_cpu_formulas(monkeypatch, ecc, live, lab):
    p = params(shack_hartmann_autofocus=False, image_registration_with_ecc=ecc,
               square=True, color_Doppler_image=True, directional_Doppler_image=True,
               color_Doppler_use_lab=lab, color_Doppler_low_frequency_band=[0, 250],
               color_Doppler_high_frequency_band=[250, 500], live_saving=live,
               save_spectograms=True, save_averaged_spectrogram=True,
               spectrogram_resize_shape=[3, 4], spectrogram_frequency_binning=2,
               spectrogram_frequency_start=0, spectrogram_frequency_end=.5)
    frames = np.random.default_rng(6).random((4, 6, 8)).astype(np.float32)
    raw = pipeline._process_one_batch(p, frames)[0]
    # Independent CPU reference: ECC scalar maps, square them, render colors;
    # spectrogram frequency grouping happens at its own requested resolution.
    expected = {}
    for key, value in raw.items():
        if value.ndim == 2:
            if ecc:
                value = np.roll(value, 1, axis=-1)
            expected[key] = ndimage.zoom(value, (8 / 6, 1), order=3)
        elif key != "sh_psd":
            expected[key] = value.copy()
    spectrum = ndimage.zoom(raw["sh_psd"], (1, .5, .5), order=1)
    expected["spectrograms"] = spectrum.reshape(2, 2, 3, 4).mean(axis=1)
    pipeline.finish_doppler_images(expected, np, p)
    saved = {}
    if live:
        destination = Mock()
        destination.add_batch.side_effect = lambda values, index: saved.update(values)
        destination.write_static.side_effect = lambda key, value: saved.update({key: value})
    else:
        destination = None
        monkeypatch.setattr(pipeline, "save_outputs", lambda **options: saved.update(
            {key: value if key == "averaged_spectrogram" else value[0]
             for key, value in options["output"].items()}))
    monkeypatch.setattr(pipeline, "register_with_ecc", lambda images, **kw: np.zeros((len(images), 2)))
    monkeypatch.setattr(pipeline, "apply_ecc_registration", lambda images, *a, **kw: np.roll(images, 1, axis=-1))
    reader = SimpleNamespace(read_frames=lambda **kw: frames.copy())
    pipeline._process_to_output(reader, p, [0], destination, None)
    for key, value in expected.items():
        if key == "sh_psd":
            continue
        np.testing.assert_allclose(saved[pipeline._output_name(key)], value, rtol=1e-5, atol=1e-6)
    assert saved["spectrograms"].shape == (2, 3, 4)
    assert saved["averaged_spectrogram"].shape == (4, 8, 8)
    assert saved["color_Doppler_image"].shape == (8, 8, 3)
    assert saved["directional_Doppler_image"].dtype == np.float32


def test_prepared_kernel_reuses_spatial_factor_and_preserves_result():
    p = params()
    phase = np.exp(-1j * np.ones((6, 8), np.float32))
    prepared = pipeline._fixed_fresnel_kernel(p, phase)
    assert prepared.dtype == np.complex64
    frames = np.random.default_rng(3).random((4, 6, 8)).astype(np.float32)
    expected = propagation.fresnel_transform_with_phase(np, fft, frames, p["z"], p["pixel_pitch"],
                                                       p["wavelength"], phase, use_output_kernel=False)
    actual = propagation.fresnel_transform(np, fft, frames, p["z"], p["pixel_pitch"], p["wavelength"],
                                         use_output_kernel=False, input_kernel=prepared)
    np.testing.assert_array_equal(actual, expected)


def test_chunked_psd_registration_matches_full_transform():
    frames = np.random.default_rng(24).random((9, 384, 384)).astype(np.float32)
    shifts = (.25, -.6)
    fy = fft.fftfreq(384).astype(np.float32)[:, None]
    fx = fft.fftfreq(384).astype(np.float32)[None, :]
    phase = np.exp(-2j * np.pi * (fy * shifts[0] + fx * shifts[1]))
    expected = fft.ifft2(fft.fft2(frames) * phase).real
    actual = registration.apply_shifts(np, fft, frames, *shifts)
    assert actual.dtype == np.float32
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=5e-7)


def test_default_config_drops_parallel_toggle_but_accepts_legacy_key():
    from holodoppler.config import validate_main_parameters
    for profile in ("default", "default_offline"):
        values = yaml.safe_load((Path(__file__).resolve().parents[1]
                                / f"parameters/default_parameters_{profile}.yaml").read_text())
        assert "use_parallel" not in values
    validate_main_parameters(params(use_parallel=False))
    validate_main_parameters(params(use_parallel="legacy ignored value"))


def test_noop_resize_does_not_interpolate():
    from holodoppler.core.image_utils import resize_frames
    image = np.ones((6, 8), np.float32)
    zoom = Mock(side_effect=AssertionError("unnecessary interpolation"))
    assert np.shares_memory(resize_frames(np, zoom, image, 6, 8), image)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("ecc", [False, True])
def test_optional_gpu_finalization_and_transfer_parity(monkeypatch, asynchronous, ecc):
    if not backend.cupy_available:
        pytest.skip("CUDA unavailable")
    p = params(batch_size=8, batch_stride=8, image_registration=True,
               registration_ref_batch_size=8, shack_hartmann_autofocus=False,
               image_registration_with_ecc=ecc, square=True,
               color_Doppler_image=True, directional_Doppler_image=True,
               color_Doppler_low_frequency_band=[0, 250],
               color_Doppler_high_frequency_band=[250, 500],
               save_spectograms=True, save_averaged_spectrogram=True,
               spectrogram_resize_shape=[4, 6], spectrogram_frequency_binning=2,
               cupy_async=asynchronous, cupy_prefetch_depth=2)
    frames = np.random.default_rng(7).random((16, 12, 18)).astype(np.float32)
    reader = SimpleNamespace(read_frames=lambda first_frame, batch_size, **kw:
                              frames[first_frame:first_frame + batch_size].copy())
    monkeypatch.setattr(pipeline, "register_with_ecc", lambda images, **kw: np.zeros((len(images), 2)))
    monkeypatch.setattr(pipeline, "apply_ecc_registration", lambda images, *a, **kw: np.roll(images, 1, axis=-1))
    outputs = []
    for device in ("numpy", "cupy"):
        backend.set_backend(device)
        destination = Mock()
        saved = {}
        destination.add_batch.side_effect = lambda values, index: [
            saved.setdefault(key, []).append(value.copy()) for key, value in values.items()]
        destination.write_static.side_effect = lambda key, value: saved.update({key: value.copy()})
        original_finalize = pipeline._finalize_spatial_result
        def finalize(result, parameters):
            assert all(isinstance(value, backend.xp.ndarray) for value in result.values())
            return original_finalize(result, parameters)
        with monkeypatch.context() as local:
            local.setattr(pipeline, "_finalize_spatial_result", finalize)
            pipeline._process_to_output(reader, p, [0, 8], destination, None)
        outputs.append({key: np.asarray(value) for key, value in saved.items()})
    assert outputs[0].keys() == outputs[1].keys()
    for key in outputs[0]:
        # Registration and signed moments are cancellation-sensitive.
        assert normalized_error(outputs[1][key], outputs[0][key]) <= 1e-3, key


def test_fractional_moment_orders_preserve_original_formulas():
    data = np.ones((2, 1, 1), np.float32)
    freqs = np.array([4., 9.])
    np.testing.assert_array_equal(moments.moments(np, data, freqs, [.5])[0], [[5.]])
    np.testing.assert_array_equal(moments.moment(np, data, freqs, .5), [[5.]])
    np.testing.assert_array_equal(moments.moment_khz(np, data, freqs * 1000, .5), [[5.]])


def test_signed_band_moment_preserves_original_symmetric_cancellation():
    count = 256
    psd = np.random.default_rng(23).random((count, 4, 5), dtype=np.float32)
    psd[count // 2 + 1:] = psd[1:count // 2][::-1]
    freqs = backend.fft.fftfreq(count, 1 / 39000)
    mask = (abs(freqs) > 6000) & (abs(freqs) < 18300)
    expected = moments.moments(np, psd[mask], freqs[mask], [0, 1, 2])
    actual = pipeline._band_moments(psd, 39000, 6000, 18300, [0, 1, 2])
    for value, reference in zip(actual, expected):
        np.testing.assert_array_equal(value, reference)
    np.testing.assert_array_equal(actual[1], np.zeros((4, 5)))
