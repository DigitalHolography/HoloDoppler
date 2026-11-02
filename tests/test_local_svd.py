import numpy as np
import pytest
from holodoppler.core.filtering import svd_filter, svd_filter_by_bloc

@pytest.mark.parametrize('dc', [False, True])
@pytest.mark.parametrize('rank', [0, 1, 20])
def test_local_matches_reference(dc, rank):
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
    actual = svd_filter_by_bloc(np, np.linalg, data, 2, rank, dc)
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
