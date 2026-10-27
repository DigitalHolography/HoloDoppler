"""Configuration and execution controls for SVD and Shack-Hartmann processing."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
import yaml
from scipy import fft

from holodoppler import backend
from holodoppler.config import validate_main_parameters
from holodoppler.core import filtering, registration
from holodoppler.pipelines import main_default


@pytest.fixture
def parameters():
    params = yaml.safe_load((Path(__file__).resolve().parents[1]
                            / 'parameters/default_parameters_default.yaml').read_text())
    params.update(z=.1, pixel_pitch=(1e-6, 1e-6), sampling_freq=1000,
                  low_freq=0, high_freq=500, svd_threshold=1,
                  registration_flatfield_gw=1, frequency_bands=[],
                  color_Doppler_image=False, directional_Doppler_image=False,
                  save_spectograms=False, save_averaged_spectrogram=False,
                  shack_hartmann_nx_subap=2, shack_hartmann_ny_subap=2,
                  shack_hartmann_zernike_fit=False)
    return params


@pytest.mark.parametrize('key', ['svd_block_size_mib', 'registration_block_size_mib'])
@pytest.mark.parametrize('value', [0, -1, float('nan'), float('inf'), True, 'eight'])
def test_reject_invalid_memory_budgets(parameters, key, value):
    parameters[key] = value
    with pytest.raises((TypeError, ValueError), match=key):
        validate_main_parameters(parameters)


@pytest.mark.parametrize('value', [-1, float('nan'), float('inf'), True, None, 'small'])
def test_reject_invalid_regularization(parameters, value):
    parameters['shack_hartmann_svd_regularization'] = value
    with pytest.raises((TypeError, ValueError), match='shack_hartmann_svd_regularization'):
        validate_main_parameters(parameters)


@pytest.mark.parametrize('value', ['auto', 'threaded', '', True, None, []])
def test_reject_invalid_subaperture_mode(parameters, value):
    parameters['shack_hartmann_sub_aps_process'] = value
    with pytest.raises((TypeError, ValueError), match='shack_hartmann_sub_aps_process'):
        validate_main_parameters(parameters)


@pytest.mark.parametrize('mode', ['sequential', 'parallel'])
@pytest.mark.parametrize('budget', [.125, None])
def test_accept_memory_budgets_and_disabled_regularization(parameters, mode, budget):
    parameters.update(shack_hartmann_sub_aps_process=mode, svd_block_size_mib=budget,
                      registration_block_size_mib=budget, shack_hartmann_svd_regularization=0)
    validate_main_parameters(parameters)
    for key in ('shack_hartmann_sub_aps_process', 'svd_block_size_mib',
                'registration_block_size_mib', 'shack_hartmann_svd_regularization'):
        del parameters[key]
    validate_main_parameters(parameters)


@pytest.mark.parametrize('method', ['Fresnel', 'AngularSpectrum'])
@pytest.mark.parametrize('budget', [.25, None])
def test_default_forwards_subaperture_options(parameters, monkeypatch, method, budget):
    manager = backend.BackendManager('numpy')
    monkeypatch.setattr(backend, 'xp', np)
    monkeypatch.setattr(backend, 'fft', manager.fft)
    parameters.update(spatial_propagation=method, shack_hartmann_sub_aps_process='parallel',
                      svd_block_size_mib=budget, shack_hartmann_svd_regularization=.002)
    constructor = Mock(return_value=np.ones((2, 2, 3, 4), np.float32))
    name = 'construct_subapertures_fresnel' if method == 'Fresnel' else 'construct_subapertures_angular'
    monkeypatch.setattr(main_default, name, constructor)
    monkeypatch.setattr(main_default, 'calculate_displacements_graph_laplacian',
                        lambda *a, **k: (np.zeros((2, 2)), np.zeros((2, 2))))
    assert main_default._process_shack_hartmann(parameters, np.ones((8, 6, 8), np.float32)) is None
    assert constructor.call_args.kwargs == dict(sub_aps_process='parallel',
                                               svd_block_size_mib=budget, svd_regularization=.002)


@pytest.mark.parametrize('budget', [.125, None])
def test_main_svd_and_registration_receive_budgets(parameters, monkeypatch, budget):
    manager = backend.BackendManager('numpy')
    for name in ('xp', 'fft', 'linalg', 'gaussian_filter'):
        monkeypatch.setattr(backend, name, getattr(manager, name))
    parameters.update(svd_block_size_mib=budget, registration_block_size_mib=budget,
                      shack_hartmann_autofocus=False, image_registration=True)
    svd = Mock(wraps=filtering.svd_filter)
    shifts = Mock(wraps=registration.apply_register_images_shifts)
    monkeypatch.setattr(main_default, 'svd_filter', svd)
    monkeypatch.setattr(main_default, 'register_images_shifts', lambda *a, **k: (.25, -.1))
    monkeypatch.setattr(main_default, 'apply_register_images_shifts', shifts)
    frames = np.random.default_rng(15).random((8, 6, 8)).astype(np.float32)
    main_default._process_one_batch(parameters, frames)
    assert svd.call_args.kwargs['block_size_mib'] == budget
    assert shifts.call_count == 4
    assert all(call.kwargs['block_size_mib'] == budget for call in shifts.call_args_list)


@pytest.mark.parametrize('budget', [.001, None])
def test_parallel_svd_uses_one_batched_eigensolve_and_configured_regularization(budget):
    data = (np.random.default_rng(14).random((2, 3, 4, 5, 8)) + 1j).astype(np.complex64)
    original = data.copy()
    eigensolver = Mock(wraps=np.linalg.eigh)
    class ArrayModule:
        linalg = SimpleNamespace(eigh=eigensolver)
        def __getattr__(self, name):
            return getattr(np, name)
    parallel = filtering.svd_filter_batched(ArrayModule(), data, 2, parallel=True, regularization=.25)
    assert eigensolver.call_count == 1
    matrix = data.reshape(6, 20, 8)
    expected_covariance = matrix.conj().swapaxes(-1, -2) @ matrix + .25 * np.eye(8, dtype=np.complex64)
    np.testing.assert_allclose(eigensolver.call_args.args[0], expected_covariance, atol=1e-6)
    sequential = filtering.svd_filter_batched(np, data, 2, regularization=.25, block_size_mib=budget)
    np.testing.assert_allclose(parallel, sequential, atol=2e-5)
    np.testing.assert_array_equal(data, original)


def test_registration_budget_controls_fft_batch_size():
    frames = np.random.default_rng(4).random((7, 32, 48)).astype(np.float32)
    batches = []
    class FFT:
        fftfreq = staticmethod(fft.fftfreq)
        ifft2 = staticmethod(fft.ifft2)
        @staticmethod
        def fft2(values, **kwargs):
            batches.append(len(values))
            return fft.fft2(values, **kwargs)
    small = registration.apply_register_images_shifts(
        np, frames, .25, -.6, fft=FFT(), block_size_mib=32768 / 1024**2)
    assert batches == [2, 2, 2, 1]
    large = registration.apply_register_images_shifts(np, frames, .25, -.6, fft=fft, block_size_mib=8)
    np.testing.assert_allclose(small, large, atol=5e-7, rtol=1e-6)
    batches.clear()
    unlimited = registration.apply_register_images_shifts(
        np, frames, .25, -.6, fft=FFT(), block_size_mib=None)
    assert batches == [len(frames)]
    np.testing.assert_allclose(small, unlimited, atol=5e-7, rtol=1e-6)


@pytest.mark.parametrize('remove_dc', [False, True])
def test_unlimited_svd_matches_blocked_projection(remove_dc):
    data = (np.random.default_rng(7).normal(size=(8, 9, 11)) + 1j).astype(np.complex64)
    # A strided input exercises the pixel-gather path used by subapertures.
    data = data[:, ::2, :]
    gather = Mock(wraps=np.arange)
    class ArrayModule:
        arange = gather
        def __getattr__(self, name):
            return getattr(np, name)
    unlimited = filtering.svd_filter(ArrayModule(), np.linalg, data, 2,
                                     remove_dc=remove_dc, block_size_mib=None)
    gather.assert_called_once_with(0, 5 * 11)
    blocked = filtering.svd_filter(np, np.linalg, data, 2,
                                   remove_dc=remove_dc, block_size_mib=.001)
    np.testing.assert_allclose(unlimited, blocked, atol=3e-5, rtol=3e-5)


def test_profiles_group_memory_controls_under_backend_management():
    root = Path(__file__).resolve().parents[1] / 'parameters'
    keys = ('svd_block_size_mib', 'registration_block_size_mib',
            'shack_hartmann_sub_aps_process')
    for path in root.glob('default_parameters*.yaml'):
        text = path.read_text()
        start = text.index('# backend management')
        end = text.index('# saving management')
        for key in keys:
            if key in yaml.safe_load(text):
                assert text.count(key + ':') == 1, (path.name, key)
                assert start < text.index(key + ':') < end, (path.name, key)
