"""
Moment calculations from power spectral density
"""


def moment(xp, A, freqs, n):
    """Calculate nth spectral moment"""
    return xp.sum(A * (freqs[..., xp.newaxis, xp.newaxis] ** n), axis=0)

def moment_khz(xp, A, freqs, n):
    """Calculate nth spectral moment with frequency in kHz"""
    return xp.sum(A * ((freqs[..., xp.newaxis, xp.newaxis] / 1000) ** n), axis=0)