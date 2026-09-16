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
