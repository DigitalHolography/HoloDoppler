import numpy as np
import pytest
from holodoppler.core.moments import gaussian_width

@pytest.mark.parametrize("band", [None, [100, 300]])
def test_matches_integral_sums(band):
    fs = 800
    f = np.fft.fftfreq(16, 1/fs)
    psd = np.random.default_rng(2).uniform(.1, 2, (16, 3, 5))
    mask = np.ones(16, bool) if band is None else ((abs(f) >= band[0]) & (abs(f) <= band[1]))
    a, b = [abs(np.sum(psd[mask] * np.exp(-2j*np.pi*k*f[mask]/fs)[:, None, None], axis=0)) for k in (1, 2)]
    ratio = np.log(a/b)
    expected = np.where(ratio >= 0, fs/np.pi*np.sqrt(np.maximum(ratio, 0)/3), np.nan)
    np.testing.assert_allclose(gaussian_width(np, psd, fs, band), expected)

def test_zero_and_empty_band():
    with np.errstate(all="raise"):
        assert np.isnan(gaussian_width(np, np.zeros((8, 2, 2)), 800)).all()
    with pytest.raises(ValueError, match="no FFT bins"):
        gaussian_width(np, np.ones((8, 2, 2)), 800, [1, 2])
