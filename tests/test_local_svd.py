import numpy as np
import pytest
from holodoppler.core.filtering import svd_filter, svd_filter_by_bloc
from unittest.mock import Mock


@pytest.mark.parametrize('stride, starts', [(1, [0, 1, 2, 3, 4, 5]),
                                           (2, [0, 2, 4, 5]), (3, [0, 3, 5])])
def test_stride_matches_reference_and_covers_edges(stride, starts):
    data = np.random.default_rng(8).normal(size=(4, 8, 8)).astype(complex)
    expected = np.zeros_like(data)
    weights = np.zeros((8, 8))
    for y in starts:
        for x in starts:
            patch = data[:, y:y+3, x:x+3]
            u, s, vh = np.linalg.svd(patch.reshape(4, -1).T, full_matrices=False)
            s[0] = 0
            expected[:, y:y+3, x:x+3] += ((u*s)@vh).T.reshape(patch.shape)
            weights[y:y+3, x:x+3] += 1
    solver = Mock()
    solver.eigh = Mock(wraps=np.linalg.eigh)
    actual = svd_filter_by_bloc(np, solver, data, 3, 1, svd_filter_by_bloc_window_stride=stride)
    assert solver.eigh.call_count == 1
    assert np.all(weights > 0)
    np.testing.assert_allclose(actual, expected/weights, atol=1e-13)


@pytest.mark.parametrize('stride', [0, -1, 1.5, True, None, 4])
def test_invalid_stride(stride):
    with pytest.raises((TypeError, ValueError), match='svd_filter_by_bloc_window_stride'):
        svd_filter_by_bloc(np, np.linalg, np.ones((4, 8, 8)), 3,
                           svd_filter_by_bloc_window_stride=stride)

@pytest.mark.parametrize('parallel,budget', [(False, .001), (False, None), (True, 8)])
@pytest.mark.parametrize('dc', [False, True])
@pytest.mark.parametrize('rank', [0, 1, 20])
def test_local_matches_reference(dc, rank, parallel, budget):
    rng = np.random.default_rng(12)
    data = rng.normal(size=(4, 4, 5)) + 1j*rng.normal(size=(4, 4, 5))
    original = data.copy()
    work = data - data.mean(axis=0) if dc else data
    expected = np.zeros_like(data)
    weights = np.zeros(data.shape[1:])
    for y in range(3):
        for x in range(4):
            patch = work[:, y:y+2, x:x+2]
            u, s, vh = np.linalg.svd(patch.reshape(4, -1).T, full_matrices=False)
            s[:rank] = 0
            expected[:, y:y+2, x:x+2] += ((u*s)@vh).T.reshape(patch.shape)
            weights[y:y+2, x:x+2] += 1
    actual = svd_filter_by_bloc(np, np.linalg, data, 2, rank, dc, svd_filter_by_bloc_parallel=parallel,
                                svd_filter_by_bloc_mib_block_size=budget)
    np.testing.assert_allclose(actual, expected/weights, atol=1e-13)
    np.testing.assert_array_equal(data, original)

@pytest.mark.parametrize('local', [False, True])
def test_zero_threshold_dc(local):
    data = np.arange(60, dtype=float).reshape(3,4,5).astype(complex)
    if local:
        actual = svd_filter_by_bloc(np, np.linalg, data, 2, 0, True)
    else:
        actual = svd_filter(np, np.linalg, data, 0, remove_dc=True)
    np.testing.assert_allclose(actual, data-data.mean(axis=0))


@pytest.mark.parametrize('parallel', [False, True])
@pytest.mark.parametrize('dtype', [np.complex64, np.complex128])
def test_cupy_complex_overlap_accumulation(parallel, dtype):
    cp = pytest.importorskip('cupy')
    try:
        if cp.cuda.runtime.getDeviceCount() == 0:
            pytest.skip('No CUDA device')
    except cp.cuda.runtime.CUDARuntimeError as exc:
        pytest.skip(f'CUDA unavailable: {exc}')
    rng = np.random.default_rng(81)
    data = (rng.normal(size=(6, 7, 8)) + 1j*rng.normal(size=(6, 7, 8))).astype(dtype)
    options = dict(window_size=3, threshold=1, remove_dc=True,
                   svd_filter_by_bloc_window_stride=2,
                   svd_filter_by_bloc_parallel=parallel,
                   svd_filter_by_bloc_mib_block_size=.001)
    expected = svd_filter_by_bloc(np, np.linalg, data, **options)
    actual = svd_filter_by_bloc(cp, cp.linalg, cp.asarray(data), **options)
    tolerance = 2e-5 if dtype == np.complex64 else 1e-12
    np.testing.assert_allclose(cp.asnumpy(actual), expected, atol=tolerance, rtol=tolerance)
