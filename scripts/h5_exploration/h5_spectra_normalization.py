"""Shared normalization for stored FFT-order H5 power spectra."""
import numpy as np


PSD_NORMALIZATION = 'density'
NORMALIZATIONS = ('none', 'num_freq', 'num_freq_squared', 'density', 'unit_area', 'peak')


def effective_sampling_frequency(parameters):
    """Apply frame skipping only through fs_eff = sampling_freq / skip_every."""
    skip_value = parameters.get('skip_every', 1)
    skip = float(1 if skip_value is None else skip_value)
    if not np.isfinite(skip) or skip <= 0 or skip != int(skip):
        raise ValueError('skip_every must be a positive integer (or null).')
    fs_eff = float(parameters['sampling_freq']) / skip
    if not np.isfinite(fs_eff) or fs_eff <= 0:
        raise ValueError('sampling_freq must be finite and positive.')
    return fs_eff, skip


def normalization_divisor(normalization, num_freq, fs_eff, non_dc_sum, non_dc_peak):
    """N includes DC; shape statistics exclude DC. No extra skip compensation."""
    if normalization == 'none':
        return 1.0
    if normalization == 'num_freq':
        return num_freq
    if normalization == 'num_freq_squared':
        return num_freq**2
    if normalization == 'density':
        return num_freq * fs_eff
    if normalization == 'unit_area':
        return non_dc_sum * (fs_eff / num_freq)
    if normalization == 'peak':
        return non_dc_peak
    raise ValueError(f'Unknown normalization: {normalization!r}')


def normalize_spectrum(mean, fs_eff, normalization=PSD_NORMALIZATION):
    """Normalize a spatial mean in FFT order, retaining DC until display."""
    mean = np.asarray(mean, dtype=np.float64)
    non_dc = mean[1:]
    divisor = normalization_divisor(
        normalization, mean.size, fs_eff, non_dc.sum(),
        non_dc.max() if non_dc.size else 0.0)
    return mean / (divisor if divisor != 0 else 1)
