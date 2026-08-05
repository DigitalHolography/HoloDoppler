import numpy as np

from holodoppler.multidimensional import (
    energy_normalized_tapers,
    normalized_coherence,
    representation_coupling,
    spectral_estimate_nbytes,
    spectral_estimate_shape,
    symmetric_frequency_band,
    temporal_spectral_estimates,
)


def test_dpss_tapers_have_unit_discrete_energy():
    windows = energy_normalized_tapers(32, number_of_tapers=4)
    assert windows.shape == (4, 32)
    np.testing.assert_allclose(np.sum(windows**2, axis=1), 1, atol=1e-12)


def test_spectral_estimates_keep_existing_unshifted_frequency_order():
    H = np.ones((64, 3, 5), dtype=np.complex64)
    result = temporal_spectral_estimates(
        H,
        32_000,
        block_length=32,
        number_of_tapers=4,
    )

    assert result.SH.shape == (8, 32, 3, 5)
    np.testing.assert_array_equal(result.frequencies, np.fft.fftfreq(32, 1 / 32_000))
    assert result.frequencies[0] == 0
    assert result.frequencies[1] > 0
    assert result.frequencies[-1] < 0
    assert result.SH.dtype == np.complex64


def test_spectral_storage_can_be_estimated_before_allocation():
    shape = spectral_estimate_shape((64, 3, 5), block_length=32)
    assert shape == (8, 32, 3, 5)
    assert spectral_estimate_nbytes((64, 3, 5)) == np.prod(shape) * 8


def test_identical_spectral_signals_have_unit_coherence():
    rng = np.random.default_rng(2)
    H = (
        rng.standard_normal((64, 2, 3))
        + 1j * rng.standard_normal((64, 2, 3))
    ).astype(np.complex64)
    estimates = temporal_spectral_estimates(H, 40_000).SH

    coupling = representation_coupling(estimates, estimates)

    np.testing.assert_allclose(coupling.coherence[coupling.valid_mask], 1, atol=2e-6)


def test_coherence_rejects_one_estimate():
    array = np.ones((4, 2, 3), dtype=np.float32)
    try:
        normalized_coherence(
            array.astype(np.complex64),
            array,
            array,
            number_of_estimates=1,
        )
    except ValueError as error:
        assert "at least two" in str(error)
    else:
        raise AssertionError("One-estimate coherence should have raised ValueError.")


def test_symmetric_band_preserves_bin_order():
    frequencies = np.fft.fftfreq(32, 1 / 32_000)
    mask = symmetric_frequency_band(frequencies, 6_000, 14_000)
    selected = frequencies[mask]
    assert np.all((np.abs(selected) > 6_000) & (np.abs(selected) < 14_000))
    assert selected[0] > 0
    assert selected[-1] < 0


def test_coupling_frequency_mask_excludes_dc_without_discarding_raw_cross_spectrum():
    estimates = np.ones((4, 32, 2, 3), dtype=np.complex64)
    frequency_mask = np.ones(32, dtype=bool)
    frequency_mask[0] = False

    coupling = representation_coupling(
        estimates,
        estimates,
        frequency_mask=frequency_mask,
    )

    assert np.all(np.isnan(coupling.coherence[0]))
    np.testing.assert_allclose(coupling.cross_spectrum[0], 1)
    np.testing.assert_allclose(coupling.coherence[1:], 1)
