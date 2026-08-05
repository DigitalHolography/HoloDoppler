import numpy as np

from holodoppler.multidimensional import build_field_representations


def test_representations_preserve_shape_dtype_and_center_log_amplitude():
    rng = np.random.default_rng(1)
    amplitude = (1.0 + 0.1 * rng.random((64, 5, 6))).astype(np.float32)
    phase = rng.normal(scale=0.2, size=(64, 5, 6)).astype(np.float32)
    H = (amplitude * np.exp(1j * phase)).astype(np.complex64)

    result = build_field_representations(H)

    assert result.H.shape == H.shape
    assert result.log_amplitude.shape == H.shape
    assert result.phase_phasor.shape == H.shape
    assert result.log_amplitude.dtype == np.float32
    assert result.phase_phasor.dtype == np.complex64
    np.testing.assert_allclose(result.log_amplitude.mean(axis=0), 0, atol=2e-7)
    np.testing.assert_allclose(
        np.abs(result.phase_phasor[:, result.valid_mask]), 1, atol=2e-7
    )


def test_explicit_mask_is_applied_to_derived_representations():
    H = np.ones((32, 4, 4), dtype=np.complex64)
    mask = np.ones((4, 4), dtype=bool)
    mask[0, 0] = False

    result = build_field_representations(H, valid_mask=mask)

    assert not result.valid_mask[0, 0]
    assert np.all(result.log_amplitude[:, 0, 0] == 0)
    assert np.all(result.phase_phasor[:, 0, 0] == 0)
