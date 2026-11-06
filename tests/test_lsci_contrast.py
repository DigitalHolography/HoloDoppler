import numpy as np
import pytest
from scipy.ndimage import uniform_filter
from holodoppler import backend
from holodoppler.pipelines.main_lsci import _contrast, _validate

@pytest.mark.parametrize("time", [1, 3])
@pytest.mark.parametrize("mode", ["reflect", "constant", "nearest", "mirror", "wrap"])
def test_joint_statistics(time, mode):
    backend.set_backend("numpy")
    p = dict(lsci_pixel_window_size=3, lsci_pixel_window_boundary_mode=mode,
             lsci_pixel_window_boundary_cval=2.)
    _validate(p)
    frames = np.arange(time * 20).reshape(time, 4, 5).astype(float)
    result = _contrast(frames, p)
    mean = uniform_filter(frames, size=(time, 3, 3), mode=mode, cval=2.)[time // 2]
    second = uniform_filter(frames ** 2, size=(time, 3, 3), mode=mode, cval=4.)[time // 2]
    std = np.sqrt(np.maximum(second - mean ** 2, 0))
    np.testing.assert_allclose(result["MEAN"], mean, rtol=1e-6)
    np.testing.assert_allclose(result["STD"], std, rtol=1e-6)
    ratio = std / np.maximum(mean, 1e-6)
    low, high = np.percentile(ratio, [1, 99])
    np.testing.assert_allclose(result["RATIO"], np.clip(ratio, low, high), rtol=1e-6)

@pytest.mark.parametrize("value", [0., 20.])
def test_constant(value):
    backend.set_backend("numpy")
    p = {}; _validate(p)
    result = _contrast(np.full((5, 8, 9), value), p)
    assert not result["STD"].any()
    assert not result["RATIO"].any()


def test_ratio_clips_tails_and_ignores_legacy_epsilon():
    backend.set_backend("numpy")
    p = {"lsci_pixel_window_size": 1, "lsci_eps": 1000.}
    _validate(p)
    delta = np.linspace(0., .9, 100).reshape(10, 10)
    frames = np.stack([1 - delta, 1 + delta])
    result = _contrast(frames, p)
    low, high = np.percentile(delta, [1, 99])
    np.testing.assert_allclose(result["RATIO"], np.clip(delta, low, high), atol=1e-7)
    np.testing.assert_allclose(result["STD"], delta, atol=1e-7)
    np.testing.assert_allclose(result["MEAN"], 1.)
