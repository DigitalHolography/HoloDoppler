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


def gaussian_width(xp, psd, sampling_freq, frequency_range=None):
    """Gaussian spectral width in Hz from the magnitudes of two Fourier integrals."""
    frequencies = xp.fft.fftfreq(psd.shape[0], d=1 / sampling_freq)
    if frequency_range is not None:
        low, high = frequency_range
        selected = (xp.abs(frequencies) >= low) & (xp.abs(frequencies) <= high)
        if not bool(xp.any(selected)):
            raise ValueError("gaussian_width_range selects no FFT bins")
        frequencies = frequencies[selected]
        psd = psd[selected]
    integrals = [xp.abs(xp.tensordot(
        xp.exp(-2j * xp.pi * lag * frequencies / sampling_freq), psd,
        axes=(0, 0))) for lag in (1, 2)]
    first, second = integrals
    valid = (first > 0) & (second > 0) & xp.isfinite(first) & xp.isfinite(second)
    log_ratio = xp.log(xp.where(valid, first, 1)) - xp.log(xp.where(valid, second, 1))
    valid &= log_ratio >= 0
    return xp.where(valid, sampling_freq / xp.pi * xp.sqrt(xp.maximum(log_ratio, 0) / 3), xp.nan)
