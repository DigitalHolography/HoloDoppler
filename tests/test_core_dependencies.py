import ast
import inspect
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import linalg, ndimage

from holodoppler.core import filtering, image_utils as images, propagation


def test_imports_do_not_load_backend():
    code = '''
import sys
from holodoppler.core import filtering, image_utils
assert 'holodoppler.backend' not in sys.modules
import numpy as np
from scipy import linalg, ndimage
filtering.svd_filter(np, linalg, np.ones((3, 2, 2)), 1)
image_utils.resize_frames(np, ndimage.zoom, np.ones((2, 2)), 4, 4)
assert 'holodoppler.backend' not in sys.modules
'''
    subprocess.run([sys.executable, '-c', code], check=True, capture_output=True, text=True)


@pytest.mark.parametrize('mode,threshold', [('number_of_values', 0), ('number_of_values', 2),
    ('number_of_values', 10), ('amplitude_threshold', 20.), ('relative_amplitude_threshold', .5)])
@pytest.mark.parametrize('remove_dc', [False, True])
def test_svd_matches_projection(mode, threshold, remove_dc):
    rng = np.random.default_rng(15)
    data = rng.normal(size=(5, 3, 4)) + 1j * rng.normal(size=(5, 3, 4))
    work = data - data.mean(axis=0) if remove_dc else data
    matrix = work.reshape(5, -1).T
    cov = matrix.conj().T @ matrix
    cov += np.finfo(cov.real.dtype).eps * np.trace(cov).real / 5 * np.eye(5)
    values, vectors = linalg.eigh(cov)
    values, vectors = values[::-1], vectors[:, ::-1]
    mask = np.arange(5) < threshold if mode == 'number_of_values' else (
        values > threshold if mode == 'amplitude_threshold' else values / values[0] > threshold)
    removed = vectors[:, mask]
    expected = (matrix - (matrix @ removed) @ removed.conj().T).T.reshape(data.shape)
    actual = filtering.svd_filter(np, linalg, data, threshold, mode, remove_dc)
    np.testing.assert_allclose(actual, expected, atol=1e-13)
    debug = filtering.svd_filter(np, linalg, data, threshold, mode, remove_dc, debug=True)
    assert len(debug) == 7
    np.testing.assert_allclose(debug[0], actual)
    np.testing.assert_allclose(debug[4], cov)
    if remove_dc:
        np.testing.assert_allclose(debug[-1], data.mean(axis=0))
    else:
        assert debug[-1] is None
    assert filtering.svd_filter(np, linalg, data, -1) is data


def test_gaussian_and_temporal_filter_dependencies():
    values = np.arange(24., dtype=float).reshape(3, 2, 4) + 1
    np.testing.assert_allclose(images.gaussian_flatfield(values, 1, ndimage.gaussian_filter),
                               values / ndimage.gaussian_filter(values, 1))
    np.testing.assert_allclose(images.temporal_gaussian_filter(np, ndimage.gaussian_filter, values, 1, axis=1),
                               ndimage.gaussian_filter(values, sigma=[0, 1, 0]))
    assert images.temporal_gaussian_filter(np, None, values, 0) is values


def test_mask_cache_distinguishes_array_modules():
    class ArrayModule:
        ogrid = np.ogrid
        zeros = staticmethod(np.zeros)
    xp1, xp2 = ArrayModule(), ArrayModule()
    images.elliptical_mask.cache_clear()
    first = images.elliptical_mask(xp1, 6, 8, .8)
    assert images.elliptical_mask(xp1, 6, 8, .8) is first
    assert images.elliptical_mask(xp2, 6, 8, .8) is not first
    np.testing.assert_array_equal(images.elliptical_mask(np, 6, 8, .8), first)
    assert not images.elliptical_mask(np, 6, 8, 0).any()


@pytest.mark.parametrize('shape', [(3, 4), (2, 3, 4)])
def test_padding_and_crop(shape):
    data = np.arange(np.prod(shape)).reshape(shape)
    padded = images.pad_array_centrally(np, data, (8, 9))
    np.testing.assert_array_equal(images.crop_array_centrally(padded, (3, 4)), data)
    with pytest.raises(ValueError): images.pad_array_centrally(np, data, 2)
    with pytest.raises(ValueError): images.pad_array_centrally(np, data, (8,))


@pytest.mark.parametrize('shape', [(3, 4), (2, 3, 4)])
@pytest.mark.parametrize('order', [0, 1, 3])
def test_resize(shape, order):
    data = np.arange(np.prod(shape), dtype=float).reshape(shape)
    factors = (2, 2) if len(shape) == 2 else (1, 2, 2)
    np.testing.assert_allclose(images.resize_frames(np, ndimage.zoom, data, 6, 8, order=order),
                               ndimage.zoom(data, factors, order=order), atol=1e-12)
    with pytest.raises(ValueError): images.resize_frames(np, ndimage.zoom, np.ones(3), 6, 8)


@pytest.mark.parametrize('builder', [propagation.build_fresnel_kernel_in,
    propagation.build_fresnel_kernel_out, propagation.build_angular_kernel])
def test_propagation_kernel_padding(builder):
    args = (np, .1, (1e-6, 1e-6), 852e-9, 3, 4)
    plain = builder(*args)
    padded = builder(*args, zero_padding=(7, 8))
    np.testing.assert_array_equal(images.crop_array_centrally(padded, (3, 4)), plain)
    assert padded.shape[-2:] == (7, 8)


def test_migrated_call_signatures():
    functions = {name: getattr(images, name) for name in ['gaussian_flatfield', 'temporal_gaussian_filter',
        'elliptical_mask', 'pad_array_centrally', 'resize_frames']}
    functions['svd_filter'] = filtering.svd_filter
    for path in Path('holodoppler').rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in functions:
                if any(isinstance(arg, ast.Starred) for arg in node.args): continue
                inspect.signature(functions[node.func.id]).bind(
                    *[None for arg in node.args], **{kw.arg: None for kw in node.keywords})


def test_default_pipeline_processing_and_spectrogram_resize():
    from holodoppler import backend
    from holodoppler.pipelines import main_default
    backend.set_backend('numpy')
    frames = np.random.default_rng(10).random((8, 4, 6)).astype(np.float32)
    params = dict(spatial_propagation='Fresnel', z=.1, pixel_pitch=(1e-6, 1e-6), wavelength=852e-9,
        Fresnel_use_ouput_kernel=False, svd_threshold=1, svd_filter_mode='number_of_values',
        svd_remove_dc=False, temporal_transformation='FourierTransform', sampling_freq=1000,
        low_freq=0, high_freq=500, registration_flatfield_gw=1, frequency_bands=[(0, 400)],
        save_spectograms=True, save_averaged_spectrogram=True, spectrogram_resize_shape=(4, 4),
        spectrogram_resize_order=1, spectrogram_frequency_start=0., spectrogram_frequency_end=.5,
        spectrogram_frequency_binning=2)
    result = main_default._process_batch(params, frames)
    assert result['M0'].shape == (4, 6)
    assert all(np.isfinite(value).all() for value in result.values())
    output = {}
    main_default._append_numpy_results(output, result, params, 0, 1)
    assert output['spectrograms'].shape == (1, 4, 4, 4)
    assert isinstance(output['spectrograms'], np.ndarray)


def test_optional_cuda_parity():
    # Isolate CUDA initialization/JIT so a stalled runtime cannot hang the suite.
    code = r"""
import sys
import numpy as np
from scipy import linalg, ndimage
from holodoppler.core import filtering, image_utils as images
try:
    import cupy as cp
    if cp.cuda.runtime.getDeviceCount() == 0:
        sys.exit(77)
    cp.zeros(1)
except Exception:
    sys.exit(77)
from cupyx.scipy import ndimage as cndi
data = np.random.default_rng(42).normal(size=(4, 3, 4))
device = cp.asarray(data)
expected = filtering.svd_filter(np, linalg, data, 1)
np.testing.assert_allclose(cp.asnumpy(filtering.svd_filter(cp, cp.linalg, device, 1)), expected, atol=1e-12)
resized = images.resize_frames(cp, cndi.zoom, device, 6, 8, order=1)
assert isinstance(resized, cp.ndarray)
np.testing.assert_allclose(cp.asnumpy(resized), images.resize_frames(np, ndimage.zoom, data, 6, 8, order=1), atol=1e-12)
"""
    try:
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        pytest.skip('CUDA parity check exceeded 30 seconds')
    if result.returncode == 77:
        pytest.skip('CUDA unavailable')
    assert result.returncode == 0, result.stdout + result.stderr
