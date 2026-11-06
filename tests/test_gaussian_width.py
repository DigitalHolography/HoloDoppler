import numpy as np
import pytest
from holodoppler.core.moments import gaussian_width

def test_periodic_gaussian_fwhm_with_center_and_baseline():
    fs, sigma = 800, 70
    f = np.fft.fftfreq(256, 1/fs)
    psd = sum(np.exp(-.5*((f-110+k*fs)/sigma)**2) for k in range(-5, 6))
    psd = (3*psd+17)[:, None, None].astype(np.complex128)
    expected = 2*np.sqrt(2*np.log(2))*sigma
    np.testing.assert_allclose(gaussian_width(np, psd, fs), expected, rtol=1e-10)

@pytest.mark.parametrize("value", [0., 1., np.nan, np.inf])
def test_invalid_returns_zero(value):
    assert (gaussian_width(np, np.full((8, 2, 2), value), 800) == 0).all()

def test_too_few_bins():
    with pytest.raises(ValueError, match="at least 5"):
        gaussian_width(np, np.ones((4, 2, 2)), 800)
