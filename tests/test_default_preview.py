"""Default display-only previews must equal the unregistered reference image."""
import copy
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from holodoppler import backend
from holodoppler.pipelines import main_default as pipeline
from test_default_pipeline_contract import parameters


@pytest.fixture(autouse=True)
def cpu_backend():
    previous = backend.get_backend_name()
    backend.set_backend('numpy')
    yield
    backend.set_backend(previous)


def input_reader(tmp_path, monkeypatch, frames=None):
    if frames is None:
        frames = np.random.default_rng(39).uniform(10, 100, (64, 8, 10)).astype(np.float32)
    def read(first_frame, batch_size, skip_every=None):
        step = skip_every or 1
        return frames[first_frame:first_frame + step * batch_size:step].copy()
    reader = SimpleNamespace(extension='.raw', total_frames=len(frames),
                             file_path=tmp_path / 'input.raw', read_frames=Mock(side_effect=read), close=Mock())
    monkeypatch.setattr(pipeline, 'get_reader', lambda _: reader)
    return reader


def settings(**options):
    p = parameters(image_registration=True, registration_ref_first_frame=0,
                   registration_ref_batch_size=8, registration_radius=.8,
                   registration_sub_pixel=True, registration_flatfield_gw=1,
                   shack_hartmann_autofocus_batch_size=8,
                   shack_hartmann_autofocus_z4_threshold_rad=1.5,
                   shack_hartmann_zernike_fit_modes=[4, 5, 6],
                   live_saving=False, numpy_num_workers=0, end_frame=15,
                   pca_time_window=4, pca_index_range=[0, 2])
    p.update(options)
    return p


@pytest.mark.parametrize('propagation', ['Fresnel', 'AngularSpectrum'])
@pytest.mark.parametrize('distinct', [False, True])
@pytest.mark.parametrize('skip', [1, 2])
@pytest.mark.parametrize('autofocus', ['accepted', 'rejected', 'disabled'])
@pytest.mark.parametrize('key', ['moment0ff', 'moment1', 'pca_sum_ff'])
def test_preview_matches_reference_passed_to_process(tmp_path, monkeypatch, propagation, distinct, skip, autofocus, key):
    reader = input_reader(tmp_path, monkeypatch)
    first, size = (4, 16) if distinct else (0, 8)
    p = settings(spatial_propagation=propagation, registration_ref_first_frame=first,
                 registration_ref_batch_size=size, shack_hartmann_autofocus_batch_size=size,
                 skip_every=skip, shack_hartmann_autofocus=autofocus != 'disabled',
                 registration_image=key, filter2d=True, pca_compute=True, pca_flatfield=True,
                 square=True)
    phase = np.linspace(0, .5, 80, dtype=np.float32).reshape(8, 10)
    def autofocus_result(parameters, frames, output_dict=None, diagnostics=None, **kwargs):
        output_dict.update(shack_hartmann_zernike_coefs=np.array([2 if autofocus == 'rejected' else 1, 0, 0]),
                           shack_hartmann_wavefront_phase=phase)
        return np.exp(-1j * phase)
    monkeypatch.setattr(pipeline, '_process_shack_hartmann', autofocus_result)
    image = pipeline.preview(reader.file_path, copy.deepcopy(p), save_outputs=False)
    assert reader.read_frames.call_count == 1
    assert reader.read_frames.call_args.kwargs == dict(first_frame=first, batch_size=size, skip_every=skip)
    assert image.shape == (8, 10), 'reference remains on the original spatial grid'
    reader.close.assert_called_once()
    references = []
    def shifts(xp, fft, fixed, moving, **kwargs):
        references.append(backend.to_numpy(fixed).copy())
        return 0, 0
    monkeypatch.setattr(pipeline, 'register_images_shifts', shifts)
    monkeypatch.setattr(pipeline, 'apply_register_images_shifts', lambda xp, image, **kwargs: image)
    monkeypatch.setattr(pipeline, 'save_outputs', Mock())
    pipeline.process(reader.file_path, copy.deepcopy(p))
    assert references
    for reference in references:
        np.testing.assert_allclose(image, reference, rtol=2e-6, atol=1e-7)


@pytest.mark.parametrize('key', ['moment0', 'moment0ff', 'moment1', 'moment2', 'gaussian_width',
    'pca_sum_ff', 'band_0_0_200', 'band_1_200_400', 'moment0_range_0_0_300',
    'moment1_range_0_0_300', 'moment0ff_range_0_0_300', '_directional_Doppler_pos',
    '_directional_Doppler_neg', '_color_Doppler_low', '_color_Doppler_high',
    'missing', 'spectrum_line', 'sh_psd', 'pca_sum'])
@pytest.mark.parametrize('welch', [False, True])
def test_targeted_outputs_equal_full_batch(key, welch):
    frames = np.random.default_rng(62).random((16, 8, 10)).astype(np.float32)
    p = settings(registration_image=key, batch_size=16, corner_compensation=True,
                 pca_compute=True, pca_flatfield=True, color_Doppler_image=True,
                 directional_Doppler_image=True, frequency_bands=[[0, 200], [200, 400]],
                 moments_frequency_ranges=[[0, 300]], welch_enabled=welch,
                 welch_batch_size=8, welch_stride=4, welch_windowing='hann',
                 save_spectograms=True, color_Doppler_low_frequency_band=[0, 200],
                 color_Doppler_high_frequency_band=[200, 400])
    full = pipeline._process_batch(p, frames)
    reference = pipeline._compute_reference_image(p, frames)
    np.testing.assert_allclose(reference, pipeline._registration_image(full, p), rtol=2e-6, atol=1e-7)


def unused(*args, **kwargs):
    raise AssertionError('unrelated output was computed')


def test_display_only_moment0_skips_unrelated_work(tmp_path, monkeypatch):
    reader = input_reader(tmp_path, monkeypatch)
    p = settings(shack_hartmann_autofocus=False, pca_compute=True, color_Doppler_image=True,
                 directional_Doppler_image=True, frequency_bands=[[0, 200]],
                 moments_frequency_ranges=[[0, 300]], save_spectograms=True, square=True)
    for name in ('pca_packet_mean', 'gaussian_width', 'directional', 'finish_doppler_images',
                 '_process_one_batch', '_finalize_spatial_result', '_square_spectrum',
                 'register_images_shifts', 'apply_register_images_shifts', 'save_outputs',
                 'plot_phase_with_slopes_rgb'):
        monkeypatch.setattr(pipeline, name, unused)
    original = pipeline.moments
    moment_calls = Mock(wraps=original)
    monkeypatch.setattr(pipeline, 'moments', moment_calls)
    transfer = Mock(wraps=backend.to_numpy)
    monkeypatch.setattr(backend, 'to_numpy', transfer)
    image = pipeline.preview(reader.file_path, p, save_outputs=False)
    assert image.shape == (8, 10)
    assert moment_calls.call_args.args[-1] == [0]
    transfer.assert_called_once()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('flatfield', [False, True])
def test_pca_reference_skips_svd_and_psd(tmp_path, monkeypatch, flatfield):
    reader = input_reader(tmp_path, monkeypatch)
    p = settings(registration_image='pca_sum_ff' if flatfield else 'pca_sum',
                 pca_compute=True, pca_flatfield=flatfield, shack_hartmann_autofocus=False)
    for name in ('svd_filter', 'svd_filter_by_bloc', 'fourier_time_transform',
                 'welch_power_spectrum', 'gaussian_width', 'moments', 'save_outputs'):
        monkeypatch.setattr(pipeline, name, unused)
    assert pipeline.preview(reader.file_path, p, save_outputs=False).shape == (8, 10)


def test_registration_disabled_uses_first_batch_and_separate_autofocus(tmp_path, monkeypatch):
    reader = input_reader(tmp_path, monkeypatch)
    p = settings(image_registration=False, first_frame=16, registration_ref_first_frame=4,
                 registration_ref_batch_size=16, shack_hartmann_autofocus=True)
    def autofocus(parameters, frames, output_dict=None, **kwargs):
        output_dict.update(shack_hartmann_zernike_coefs=np.array([1, 0, 0]),
                           shack_hartmann_wavefront_phase=np.zeros((8, 10)))
        return np.ones((8, 10), dtype=np.complex64)
    monkeypatch.setattr(pipeline, '_process_shack_hartmann', autofocus)
    assert pipeline.preview(reader.file_path, p, save_outputs=False).shape == (8, 10)
    assert [c.kwargs['first_frame'] for c in reader.read_frames.call_args_list] == [16, 4]


def test_autofocus_keeps_phase_without_diagnostic_allocations(monkeypatch):
    p = settings(shack_hartmann_autofocus=True)
    phase = np.linspace(0, .5, 80, dtype=np.float32).reshape(8, 10)
    monkeypatch.setattr(pipeline, 'construct_subapertures_fresnel', lambda *a, **k: np.ones((2, 2, 8, 10)))
    def displacements(*args, diagnostics=None, **kwargs):
        assert diagnostics is None
        return np.zeros((2, 2)), np.zeros((2, 2))
    monkeypatch.setattr(pipeline, 'calculate_displacements', displacements)
    monkeypatch.setattr(pipeline, 'calculate_displacements_graph_laplacian', displacements)
    monkeypatch.setattr(pipeline, 'fit_zernike_fresnel', lambda *a, **k: (np.array([1, 0, 0]), phase))
    monkeypatch.setattr(pipeline, 'plot_phase_with_slopes_rgb', unused)
    reader = SimpleNamespace(read_frames=lambda **k: np.ones((8, 8, 10)))
    correction, coefficients = pipeline._get_autofocus_phase_term(p, reader)
    np.testing.assert_allclose(correction, np.exp(-1j * phase))
    np.testing.assert_equal(coefficients, [1, 0, 0])
    result = {}
    pipeline._process_shack_hartmann(p, np.ones((8, 8, 10)), output_dict=result, collect_diagnostics=False)
    assert set(result) == {'shack_hartmann_zernike_coefs', 'shack_hartmann_wavefront_phase'}


def test_legacy_preview_eigenvalues_have_batch_axis(tmp_path, monkeypatch):
    reader = input_reader(tmp_path, monkeypatch)
    saved = Mock()
    monkeypatch.setattr(pipeline, 'save_outputs', saved)
    pipeline.preview(reader.file_path, settings(shack_hartmann_autofocus=False))
    values = saved.call_args.kwargs['output']['svd_eigenvalues']
    assert values.ndim == 2 and values.shape[0] == 1


def test_saved_preview_preserves_outputs_but_returns_raw_reference(tmp_path, monkeypatch):
    reader = input_reader(tmp_path, monkeypatch)
    p = settings(registration_ref_first_frame=4, registration_ref_batch_size=16,
                 registration_image='moment1', shack_hartmann_autofocus=False, square=True,
                 compute_gaussian_width=True,
                 color_Doppler_image=True, color_Doppler_low_frequency_band=[0, 200],
                 color_Doppler_high_frequency_band=[200, 400])
    expected = pipeline.preview(reader.file_path, copy.deepcopy(p), save_outputs=False)
    saved = Mock()
    monkeypatch.setattr(pipeline, 'save_outputs', saved)
    actual = pipeline.preview(reader.file_path, copy.deepcopy(p))
    np.testing.assert_allclose(actual, expected)
    outputs = saved.call_args.kwargs['output']
    assert {'moment0', 'moment0ff', 'moment1', 'moment2', 'gaussian_width', 'spectrum_line', 'sh_psd'} <= outputs.keys()
    assert outputs['moment0ff'].shape == (10, 10)
    assert actual.shape == (8, 10)


def test_invalid_processing_batch_does_not_block_valid_reference(tmp_path, monkeypatch):
    reader = input_reader(tmp_path, monkeypatch)
    p = settings(first_frame=1000, shack_hartmann_autofocus=False)
    assert pipeline.preview(reader.file_path, p, save_outputs=False).shape == (8, 10)
    reader.close.assert_called_once()


def test_reference_failure_closes_reader(tmp_path, monkeypatch):
    reader = input_reader(tmp_path, monkeypatch)
    monkeypatch.setattr(pipeline, '_compute_reference_image', Mock(side_effect=RuntimeError('reference failed')))
    with pytest.raises(RuntimeError, match='reference failed'):
        pipeline.preview(reader.file_path, settings(shack_hartmann_autofocus=False), save_outputs=False)
    reader.close.assert_called_once()


def test_real_autofocus_reference_matches_process(tmp_path, monkeypatch):
    reader = input_reader(tmp_path, monkeypatch)
    p = settings(shack_hartmann_autofocus=True, shack_hartmann_nx_subap=2,
                 shack_hartmann_ny_subap=2, shack_hartmann_svd_threshold=0,
                 shack_hartmann_graph_laplacian=False, shack_hartmann_pupil_threshold=0,
                 shack_hartmann_autofocus_z4_threshold_rad=None)
    render = Mock(return_value=np.zeros((2, 2, 3), dtype=np.uint8))
    monkeypatch.setattr(pipeline, 'plot_phase_with_slopes_rgb', render)
    image = pipeline.preview(reader.file_path, copy.deepcopy(p), save_outputs=False)
    render.assert_not_called()
    references = []
    def shifts(xp, fft, fixed, moving, **kwargs):
        references.append(fixed.copy())
        return 0, 0
    monkeypatch.setattr(pipeline, 'register_images_shifts', shifts)
    monkeypatch.setattr(pipeline, 'apply_register_images_shifts', lambda xp, image, **k: image)
    monkeypatch.setattr(pipeline, 'save_outputs', Mock())
    pipeline.process(reader.file_path, copy.deepcopy(p))
    render.assert_called_once()
    assert references
    np.testing.assert_allclose(image, references[0], rtol=2e-6, atol=1e-7)


@pytest.mark.parametrize('key', ['moment0ff', 'shack_hartmann_wavefront_phase', 'shack_hartmann_sub_images'])
def test_live_correction_and_selected_diagnostic_reference(tmp_path, monkeypatch, key):
    reader = input_reader(tmp_path, monkeypatch)
    p = settings(shack_hartmann=True, shack_hartmann_autofocus=False, registration_image=key,
                 registration_ref_first_frame=4, registration_ref_batch_size=16)
    phase = np.linspace(0, .5, 80, dtype=np.float32).reshape(8, 10)
    def live(parameters, frames, output_dict=None, collect_diagnostics=True, **kwargs):
        output_dict.update(shack_hartmann_zernike_coefs=np.array([1, 0, 0]),
                           shack_hartmann_wavefront_phase=phase)
        if collect_diagnostics:
            output_dict['shack_hartmann_sub_images'] = np.tile(phase, (2, 2))
        return np.exp(-1j * phase)
    monkeypatch.setattr(pipeline, '_process_shack_hartmann', live)
    image = pipeline.preview(reader.file_path, copy.deepcopy(p), save_outputs=False)
    references = []
    def shifts(xp, fft, fixed, moving, **kwargs):
        references.append(fixed.copy())
        return 0, 0
    monkeypatch.setattr(pipeline, 'register_images_shifts', shifts)
    monkeypatch.setattr(pipeline, 'apply_register_images_shifts', lambda xp, image, **k: image)
    monkeypatch.setattr(pipeline, 'save_outputs', Mock())
    pipeline.process(reader.file_path, copy.deepcopy(p))
    np.testing.assert_allclose(image, references[0], rtol=2e-6, atol=1e-7)


def test_unavailable_key_warns_and_falls_back(tmp_path, monkeypatch):
    reader = input_reader(tmp_path, monkeypatch)
    warn = Mock()
    monkeypatch.setattr(pipeline.logger, 'warning', warn)
    p = settings(registration_image='not_an_image', shack_hartmann_autofocus=False)
    image = pipeline.preview(reader.file_path, p, save_outputs=False)
    warn.assert_called_once_with('Registration image %r unavailable; using moment0ff', 'not_an_image')
    expected = pipeline.preview(reader.file_path, dict(p, registration_image='moment0ff'), save_outputs=False)
    np.testing.assert_array_equal(image, expected)
