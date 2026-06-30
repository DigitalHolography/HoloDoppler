"""
Moment calculations from power spectral density
"""


def moment(xp, A, freqs, n):
    """Calculate nth spectral moment"""
    return xp.sum(A * (freqs[..., xp.newaxis, xp.newaxis] ** n), axis=0)


def cast_moment_outputs_float32(xp, output_dict):
    """Keep main moment outputs in float32 for memory and H5 size."""
    for key in ("M0", "M0ff", "M1", "M2"):
        value = output_dict.get(key)
        if value is not None:
            output_dict[key] = value.astype(xp.float32, copy=False)
    return output_dict


def moment_khz(xp, A, freqs, n):
    """Calculate nth spectral moment with frequency in kHz"""
    return xp.sum(A * ((freqs[..., xp.newaxis, xp.newaxis] / 1000) ** n), axis=0)
