"""
Moment calculations from power spectral density
"""


def moment(xp, A, freqs, n):
    """Calculate nth spectral moment"""
    return xp.sum(A * (freqs[..., xp.newaxis, xp.newaxis] ** n), axis=0)

def moments(xp, A, freqs, ns):
    ns = xp.asarray(ns)
    powers = freqs[:, None] ** ns[None, :]
    result = xp.sum(A[..., None] * powers[:, None, None, :], axis=0)
    return [result[..., i] for i in range(len(ns))]

def moment_khz(xp, A, freqs, n):
    """Calculate nth spectral moment with frequency in kHz"""
    return xp.sum(A * ((freqs[..., xp.newaxis, xp.newaxis] / 1000) ** n), axis=0)


def gaussian_width(xp, psd, sampling_freq):
    """Intrinsic Gaussian FWHM in Hz; match MATLAB's zero-invalid behavior.

    Requires a complete FFT period. No flat-field correction is applied.
    """
    if psd.ndim != 3 or psd.shape[0] < 5:
        raise ValueError("gaussian_width requires a (frequency, height, width) PSD with at least 5 bins")
    if not bool(xp.isfinite(sampling_freq)) or sampling_freq <= 0:
        raise ValueError("gaussian_width requires a finite positive sampling frequency")
    frequencies = xp.fft.fftfreq(psd.shape[0], d=1 / sampling_freq)
    psd = xp.abs(psd).astype(xp.float64)
    first, second = [xp.abs(xp.sum(
        psd * xp.exp(-2j * xp.pi * lag * frequencies / sampling_freq)[:, None, None],
        axis=0)) for lag in (1, 2)]
    spectral_sum = xp.sum(psd, axis=0)
    tolerance = 100 * xp.finfo(xp.float64).eps * spectral_sum
    valid = (xp.isfinite(spectral_sum) & (spectral_sum > 0)
             & xp.isfinite(first) & xp.isfinite(second)
             & (first > tolerance) & (second > tolerance) & (first > second))
    sigma = xp.zeros(first.shape, dtype=xp.float64)
    sigma[valid] = sampling_freq / (xp.pi * xp.sqrt(6)) * xp.sqrt(
        xp.log(first[valid]) - xp.log(second[valid]))
    return 2 * xp.sqrt(2 * xp.log(2)) * sigma
