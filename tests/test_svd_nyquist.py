"""Nyquist mode rejection and its interaction with existing SVD selection."""
import numpy as np
import pytest

from holodoppler.core.filtering import svd_filter


def source_modes(nt):
    bins = np.roll(np.fft.fftfreq(nt) * nt, 5)
    modes = np.exp(2j * np.pi * np.arange(nt)[:, None] * bins / nt) / np.sqrt(nt)
    energy = np.arange(nt, 0, -1)
    return (modes * np.sqrt(energy)).reshape(nt, 1, nt), bins, energy


@pytest.mark.parametrize("nt", [31, 32])
@pytest.mark.parametrize("mode,threshold", [
    ("number_of_values", 0), ("number_of_values", 8),
    ("amplitude_threshold", 25), ("effective_rank", 0),
    ("participation_ratio", 0), ("energy_fraction", 0),
])
@pytest.mark.parametrize("weighted", [False, True])
def test_nyquist_combines_rejection_and_preserves_spectra(nt, mode, threshold, weighted):
    source, bins, energy = source_modes(nt)
    original = source.copy()
    options = dict(filter_mode=mode, effective_rank_multiplier=.1,
                   participation_ratio_multiplier=.1, energy_fraction=.1,
                   eigenvalue_weighting=weighted)
    keys = ("eigen_spectrogram", "svd_eigenvalues", "pc_sum_static", "pc_sum_dynamic")
    baseline_summary = dict.fromkeys(keys)
    baseline_diagnostic = {}
    baseline = svd_filter(np, np.linalg, source, threshold, summary=baseline_summary,
                          diagnostic=baseline_diagnostic, **options)
    count = baseline_diagnostic["removed_features"].shape[-1]
    contaminated = np.exp(-.5 * ((nt / 2 - np.abs(bins)) / 2)**2) >= .5
    rejected = contaminated | (np.arange(nt) < count)
    expected = source.copy()
    expected[:, :, rejected] = 0
    summary = dict.fromkeys(keys)
    diagnostic = {}
    actual = svd_filter(np, np.linalg, source, threshold, summary=summary,
                        diagnostic=diagnostic, remove_nyquist_modes=True,
                        block_size_mib=.001, **options)
    np.testing.assert_allclose(actual, expected, atol=1e-12)
    np.testing.assert_array_equal(source, original)
    for key in keys[:2]:
        np.testing.assert_allclose(summary[key], baseline_summary[key], atol=1e-12)
    amplitudes = np.sqrt(energy) * (energy if weighted else 1)
    np.testing.assert_allclose(summary["pc_sum_static"], (amplitudes * rejected)[None], atol=1e-11)
    np.testing.assert_allclose(summary["pc_sum_dynamic"], (amplitudes * ~rejected)[None], atol=1e-11)
    assert diagnostic["removed_features"].shape[-1] == rejected.sum()
    np.testing.assert_array_equal(diagnostic["rejected_modes"], rejected)
    removed = diagnostic["eigenvectors"][:, rejected].conj() @ diagnostic["removed_features"][0].T
    np.testing.assert_allclose(removed, (source - actual).reshape(nt, nt), atol=1e-12)
    np.testing.assert_allclose(diagnostic["kept_data"], expected, atol=1e-12)
    # Detection must not depend on requesting numerical exports.
    without_summary = svd_filter(np, np.linalg, source, threshold,
                                 remove_nyquist_modes=True, **options)
    np.testing.assert_allclose(without_summary, expected, atol=1e-12)


@pytest.mark.parametrize("threshold", [-1, 0])
def test_nyquist_bypass_and_disabled(threshold):
    source, _, _ = source_modes(32)
    baseline = svd_filter(np, np.linalg, source, threshold)
    result = svd_filter(np, np.linalg, source, threshold, remove_nyquist_modes=False)
    np.testing.assert_array_equal(result, baseline)
    if threshold < 0:
        for summary in (None, {"eigen_spectrogram": None}):
            assert svd_filter(np, np.linalg, source, threshold,
                              remove_nyquist_modes=True, summary=summary) is source


@pytest.mark.parametrize("width,fraction", [(1., .5), (2., .9), (3., .25)])
def test_nyquist_width_and_cutoff(width, fraction):
    source, bins, _ = source_modes(32)
    rejected = np.exp(-.5 * ((16 - np.abs(bins)) / width)**2) >= fraction
    expected = source.copy()
    expected[:, :, rejected] = 0
    result = svd_filter(np, np.linalg, source, 0, remove_nyquist_modes=True,
                        nyquist_width_bins=width, nyquist_energy_fraction=fraction)
    np.testing.assert_allclose(result, expected, atol=1e-12)


@pytest.mark.parametrize("fraction", [.25, .75])
def test_nyquist_scores_fraction_of_whole_mode_power(fraction):
    time = np.arange(32)
    nyquist = np.exp(-1j * np.pi * time) / np.sqrt(32)
    dc = np.ones(32) / np.sqrt(32)
    modes = np.column_stack((np.sqrt(fraction) * nyquist + np.sqrt(1 - fraction) * dc,
                             np.sqrt(1 - fraction) * nyquist - np.sqrt(fraction) * dc))
    source = (modes * [3, 1]).reshape(32, 1, 2)
    expected = source.copy()
    expected[:, :, 0 if fraction > .5 else 1] = 0
    actual = svd_filter(np, np.linalg, source, 0, remove_nyquist_modes=True)
    np.testing.assert_allclose(actual, expected, atol=1e-12)
