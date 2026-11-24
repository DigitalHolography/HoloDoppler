"""Inverse SVD selection keeps the otherwise removed eigenmodes."""
import numpy as np
import pytest

from holodoppler.core.filtering import svd_filter


@pytest.mark.parametrize("mode,threshold,kept", [
    ("number_of_values", 0, 0),
    ("number_of_values", 2, 2),
    ("number_of_values", 9, 4),
    ("amplitude_threshold", 5, 2),
    ("effective_rank", 0, 2),
    ("participation_ratio", 0, 2),
    ("energy_fraction", 0, 2),
])
def test_inverse_keeps_leading_modes(mode, threshold, kept):
    source = np.diag([4., 3., 2., 1.]).reshape(4, 2, 2).astype(complex)
    actual = svd_filter(np, np.linalg, source, threshold, mode,
                        svd_inverse_selection=True, effective_rank_multiplier=.5,
                        participation_ratio_multiplier=.5, energy_fraction=.8)
    expected = source.copy()
    expected[kept:] = 0
    np.testing.assert_allclose(actual, expected, atol=1e-12)


@pytest.mark.parametrize("budget", [None, .0002])
@pytest.mark.parametrize("dc", [False, True])
@pytest.mark.parametrize("nyquist", [False, True])
@pytest.mark.parametrize("weighted", [False, True])
def test_inverse_complements_output_summaries_and_diagnostics(budget, dc, nyquist, weighted):
    rng = np.random.default_rng(51)
    source = (rng.normal(size=(8, 3, 4)) + 1j * rng.normal(size=(8, 3, 4))).swapaxes(1, 2)
    original = source.copy()
    options = dict(block_size_mib=budget, remove_dc=dc, remove_spatial_dc=dc,
                   remove_nyquist_modes=nyquist, nyquist_width_bins=1.,
                   eigenvalue_weighting=weighted)
    summaries = [dict.fromkeys(("pc_sum_static", "pc_sum_dynamic")) for _ in range(2)]
    diagnostics = [{}, {}]
    normal = svd_filter(np, np.linalg, source, 2, summary=summaries[0],
                        diagnostic=diagnostics[0], **options)
    inverse = svd_filter(np, np.linalg, source, 2, svd_inverse_selection=True,
                         summary=summaries[1], diagnostic=diagnostics[1], **options)
    centered = source.copy()
    if dc:
        centered -= centered.mean(axis=0)
        centered -= centered.mean(axis=(1, 2), keepdims=True)
    np.testing.assert_allclose(normal + inverse, centered, atol=1e-12)
    np.testing.assert_array_equal(source, original)
    np.testing.assert_array_equal(diagnostics[1]["rejected_modes"], ~diagnostics[0]["rejected_modes"])
    np.testing.assert_allclose(summaries[1]["pc_sum_static"], summaries[0]["pc_sum_dynamic"], atol=1e-12)
    np.testing.assert_allclose(summaries[1]["pc_sum_dynamic"], summaries[0]["pc_sum_static"], atol=1e-12)
    rejected = diagnostics[1]["rejected_modes"]
    removed = diagnostics[1]["eigenvectors"][:, rejected].conj() @ diagnostics[1]["removed_features"].reshape(-1, rejected.sum()).T
    np.testing.assert_allclose(removed.reshape(source.shape), centered - inverse, atol=1e-12)


@pytest.mark.parametrize("summary", [None, {"pc_sum_static": None}])
def test_inverse_negative_threshold_bypasses(summary):
    source = np.ones((4, 2, 3), dtype=complex)
    assert svd_filter(np, np.linalg, source, -1, svd_inverse_selection=True,
                      remove_dc=True, remove_spatial_dc=True, summary=summary) is source


@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_inverse_requires_boolean(value):
    with pytest.raises(TypeError, match="svd_inverse_selection"):
        svd_filter(np, np.linalg, np.ones((4, 2, 3)), 1, svd_inverse_selection=value)
