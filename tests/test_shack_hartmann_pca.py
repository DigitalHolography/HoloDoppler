"""PCA subimages must match magnitude sums and bypass spectral filtering."""
from pathlib import Path

import numpy as np
import pytest
import yaml
from scipy import fft

from holodoppler import backend
from holodoppler.config import validate_main_parameters
from holodoppler.core import shack_hartmann as shack
from holodoppler.core.propagation import build_angular_kernel, build_fresnel_kernel_in
from holodoppler.pipelines import main_default, main_sliding_shack_hart


def reference_subimages(frames, method, bounds, grid=(3, 4)):
    """Use spatial propagation and an independent SVD magnitude oracle."""
    nt, ny, nx = frames.shape
    gy, gx = grid
    sy, sx = ny // gy, nx // gx
    y0, x0 = (ny - gy * sy) // 2, (nx - gx * sx) // 2
    if method == 'Fresnel':
        kernel = build_fresnel_kernel_in(np, .1, (1e-6, 1e-6), 852e-9, ny, nx)
        full = frames * kernel
    else:
        kernel = build_angular_kernel(np, .1, (1e-6, 1e-6), 852e-9, ny, nx)
        full = fft.fft2(frames.astype(np.complex64)) * fft.fftshift(kernel, axes=(-2, -1))
        full = fft.fftshift(full[:, y0:y0 + gy * sy, x0:x0 + gx * sx], axes=(-2, -1))
        y0 = x0 = 0
    images = np.empty((gy, gx, sy, sx), np.float32)
    for y in range(gy):
        for x in range(gx):
            tile = full[:, y0 + y * sy:y0 + (y + 1) * sy,
                        x0 + x * sx:x0 + (x + 1) * sx]
            if method == 'Fresnel':
                propagated = fft.fftshift(fft.fft2(tile), axes=(-2, -1))
            else:
                propagated = fft.ifft2(fft.ifftshift(tile, axes=(-2, -1)))
            vectors, values, _ = np.linalg.svd(propagated.reshape(nt, -1).T, full_matrices=False)
            components = (vectors * values)[:, ::-1][:, bounds[0]:bounds[1]]
            images[y, x] = np.sum(np.abs(components), axis=-1).reshape(sy, sx)
    return images


def forbid_filtering(*args, **kwargs):
    pytest.fail('PCA subimages must bypass SVD filtering and temporal FFT/frequency selection')


@pytest.mark.parametrize('method', ['Fresnel', 'AngularSpectrum'])
@pytest.mark.parametrize('mode', ['sequential', 'parallel'])
@pytest.mark.parametrize('shape', [(17, 22), (18, 24)])
@pytest.mark.parametrize('bounds', [[0, 3], [2, 6], [0, 8]])
def test_pca_subimages_match_svd_oracle_and_skip_filters(monkeypatch, method, mode, shape, bounds):
    rng = np.random.default_rng(84)
    frames = (rng.normal(size=(8, *shape)) + 1j * rng.normal(size=(8, *shape))).astype(np.complex64)
    original = frames.copy()
    expected = reference_subimages(frames, method, bounds)
    monkeypatch.setattr(shack, 'svd_filter_batched', forbid_filtering)
    monkeypatch.setattr(shack, 'symmetric_frequency_slices', forbid_filtering)
    class SpatialFFT:
        def __getattr__(self, name):
            return forbid_filtering if name == 'fft' else getattr(fft, name)
    constructor = (shack.construct_subapertures_fresnel if method == 'Fresnel'
                   else shack.construct_subapertures_angular)
    actual = constructor(
        np, SpatialFFT(), frames, 852e-9, .1, (1e-6, 1e-6),
        None, None, None, None, 4, 3, None,
        sub_aps_process=mode, pca_index_range=bounds, svd_regularization=None)
    assert actual.dtype == np.float32
    np.testing.assert_allclose(actual, expected, rtol=2e-5, atol=2e-5)
    np.testing.assert_array_equal(frames, original)


def parameters(**changes):
    params = yaml.safe_load((Path(__file__).resolve().parents[1]
                            / 'parameters/default_parameters_default.yaml').read_text())
    params.update(z=.1, pixel_pitch=[1e-6, 1e-6], sampling_freq=1000,
                  low_freq=0, high_freq=500, shack_hartmann=True,
                  shack_hartmann_image='pca_sum', shack_hartmann_pca_index_range=[2, 6],
                  shack_hartmann_nx_subap=4, shack_hartmann_ny_subap=3,
                  shack_hartmann_zernike_fit=False, shack_hartmann_graph_laplacian=False,
                  image_registration=False, square=False)
    params.update(changes)
    return params


@pytest.mark.parametrize('method', ['Fresnel', 'AngularSpectrum'])
@pytest.mark.parametrize('mode', ['sequential', 'parallel'])
@pytest.mark.parametrize('sliding', [False, True])
def test_pipeline_uses_pca_subimages(monkeypatch, method, mode, sliding):
    monkeypatch.setattr(backend, 'xp', np)
    monkeypatch.setattr(backend, 'fft', fft)
    frames = np.random.default_rng(86).normal(size=(8, 17, 22)).astype(np.float32)
    expected = reference_subimages(frames, method, [2, 6])
    p = parameters(spatial_propagation=method, shack_hartmann_sub_aps_process=mode)
    module = main_sliding_shack_hart if sliding else main_default
    captured = []
    def displacements(xp, fft, images, **kwargs):
        captured.append(images.copy())
        return np.zeros((3, 4)), np.zeros((3, 4))
    monkeypatch.setattr(module, 'calculate_displacements', displacements)
    monkeypatch.setattr(shack, 'svd_filter_batched', forbid_filtering)
    monkeypatch.setattr(shack, 'symmetric_frequency_slices', forbid_filtering)
    if sliding:
        monkeypatch.setattr(module, '_process_batch', lambda *a, **k: {})
        p['sh_time_accumulation'] = 2
        history = []
        module._process_one_batch(p, frames, U_buffer=history)
        result, _ = module._process_one_batch(p, frames, U_buffer=history)
        expected *= 2
    else:
        result = {}
        module._process_shack_hartmann(p, frames, output_dict=result)
    np.testing.assert_allclose(captured[-1], expected, rtol=2e-5, atol=2e-5)
    montage = expected.transpose(0, 2, 1, 3).reshape(15, 20)
    np.testing.assert_allclose(result['shack_hartmann_sub_images'], montage, rtol=2e-5, atol=2e-5)


@pytest.mark.parametrize('key,value', [
    ('shack_hartmann_image', None), ('shack_hartmann_image', 'pca'),
    ('shack_hartmann_pca_index_range', None), ('shack_hartmann_pca_index_range', [0]),
    ('shack_hartmann_pca_index_range', [True, 4]), ('shack_hartmann_pca_index_range', [0, 2.5]),
    ('shack_hartmann_pca_index_range', [-1, 3]), ('shack_hartmann_pca_index_range', [3, 3]),
    ('shack_hartmann_pca_index_range', [4, 2]),
])
def test_reject_invalid_pca_settings(key, value):
    with pytest.raises((TypeError, ValueError), match=key):
        validate_main_parameters(parameters(**{key: value}))


def test_pca_settings_validate_without_full_image_pca():
    validate_main_parameters(parameters(pca_compute=False))


@pytest.mark.parametrize('constructor', [shack.construct_subapertures_fresnel,
                                       shack.construct_subapertures_angular])
def test_pca_range_must_fit_actual_frame_count(constructor):
    with pytest.raises(ValueError, match='shack_hartmann_pca_index_range.*frame count'):
        constructor(np, fft, np.ones((4, 12, 16), np.float32),
                    852e-9, .1, (1e-6, 1e-6), None, None, None, None,
                    4, 3, None, pca_index_range=[0, 5])


@pytest.mark.parametrize('method', ['Fresnel', 'AngularSpectrum'])
@pytest.mark.parametrize('mode', ['sequential', 'parallel'])
def test_optional_gpu_pca_subimages(method, mode):
    if not backend.cupy_available:
        pytest.skip('CUDA unavailable')
    manager = backend.BackendManager('cupy')
    frames = np.random.default_rng(88).normal(size=(8, 17, 22)).astype(np.float32)
    expected = reference_subimages(frames, method, [2, 6])
    constructor = (shack.construct_subapertures_fresnel if method == 'Fresnel'
                   else shack.construct_subapertures_angular)
    actual = constructor(
        manager.xp, manager.fft, manager.xp.asarray(frames),
        852e-9, .1, (1e-6, 1e-6), None, None, None, None, 4, 3, None,
        sub_aps_process=mode, pca_index_range=[2, 6])
    np.testing.assert_allclose(manager.xp.asnumpy(actual), expected, rtol=1e-3, atol=1e-3)
