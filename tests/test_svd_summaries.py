"""SVD amplitude summaries, adaptive rank selection, and numerical exports."""
from types import SimpleNamespace

import h5py
import numpy as np
import pytest

from holodoppler.core.filtering import svd_filter
from holodoppler.saving import OutputClass
from holodoppler.saving.default_output import DefaultOutput


@pytest.mark.parametrize("dc", [False, True])
@pytest.mark.parametrize("count", [-1, 0, 2, 5])
@pytest.mark.parametrize("budget", [None, .0002])
@pytest.mark.parametrize("weighted", [False, True])
def test_amplitude_summaries(dc, count, budget, weighted):
    rng = np.random.default_rng(80)
    source = rng.normal(size=(5, 3, 7)) + 1j * rng.normal(size=(5, 3, 7))
    source = source.swapaxes(1, 2)  # noncontiguous input
    centered = source.copy()
    if dc and count >= 0:
        centered -= centered.mean(axis=0)
    matrix = centered.reshape(5, -1)
    values, vectors = np.linalg.eigh(matrix.conj() @ matrix.T)
    vectors = vectors[:, ::-1]
    coefficients = vectors.T @ matrix
    k = max(count, 0)
    summary = dict.fromkeys(("pc_sum_static", "pc_sum_dynamic", "svd_eigenvalues"))
    actual = svd_filter(np, np.linalg, source, count, remove_dc=dc,
                        block_size_mib=budget, summary=summary,
                        eigenvalue_weighting=weighted)
    np.testing.assert_allclose(summary["svd_eigenvalues"], values[::-1], atol=1e-12)
    amplitudes = np.abs(coefficients)
    if weighted:
        amplitudes *= np.maximum(values[::-1], 0)[:, None]
    np.testing.assert_allclose(summary["pc_sum_static"],
                               amplitudes[:k].sum(axis=0).reshape(source.shape[1:]), atol=1e-12)
    np.testing.assert_allclose(summary["pc_sum_dynamic"],
                               amplitudes[k:].sum(axis=0).reshape(source.shape[1:]), atol=1e-12)
    expected = centered - (vectors[:, :k].conj() @ coefficients[:k]).reshape(source.shape)
    np.testing.assert_allclose(actual, expected, atol=1e-12)
    if count < 0:
        assert actual is source


def test_weighting_defaults_to_true():
    data = np.diag([3., 2.]).reshape(2, 1, 2)
    summary = {"pc_sum_static": None, "pc_sum_dynamic": None}
    svd_filter(np, np.linalg, data, 1, summary=summary)
    np.testing.assert_array_equal(summary["pc_sum_static"], [[27., 0.]])
    np.testing.assert_array_equal(summary["pc_sum_dynamic"], [[0., 8.]])


@pytest.mark.parametrize("value", [1, "true", None])
def test_weighting_requires_boolean(value):
    with pytest.raises(TypeError, match="eigenvalue_weighting"):
        svd_filter(np, np.linalg, np.ones((2, 1, 2)), 1, eigenvalue_weighting=value)


@pytest.mark.parametrize("mode,options,k", [
    ("effective_rank", {}, 3),
    ("effective_rank", {"effective_rank_multiplier": .5}, 2),
    ("effective_rank", {"effective_rank_multiplier": 0}, 0),
    ("effective_rank", {"effective_rank_multiplier": 100}, 4),
    ("participation_ratio", {}, 2),
    ("participation_ratio", {"participation_ratio_multiplier": .5}, 1),
    ("participation_ratio", {"participation_ratio_multiplier": 0}, 0),
    ("participation_ratio", {"participation_ratio_multiplier": 100}, 4),
    ("energy_fraction", {}, 2),
    ("energy_fraction", {"energy_fraction": .7}, 1),
    ("energy_fraction", {"energy_fraction": 1}, 3),
])
def test_adaptive_counts(mode, options, k):
    data = np.diag(np.sqrt([7., 2., 1., 0.])).reshape(4, 2, 2)
    actual = svd_filter(np, np.linalg, data, 23, mode, **options)
    expected = data.copy()
    expected[:k] = 0
    np.testing.assert_allclose(actual, expected, atol=1e-12)


@pytest.mark.parametrize("mode", ["effective_rank", "participation_ratio", "energy_fraction"])
def test_zero_energy(mode):
    summary = {"pc_sum_static": None, "pc_sum_dynamic": None}
    data = np.zeros((4, 2, 3), dtype=np.complex64)
    np.testing.assert_array_equal(svd_filter(np, np.linalg, data, 0, mode, summary=summary), data)
    for image in summary.values():
        np.testing.assert_array_equal(image, 0)


@pytest.mark.parametrize("spectrum,k", [([4., 0., 0., 0.], 1),
                                       ([1., 1., 1., 1.], 4)])
def test_participation_ratio_spectral_extremes(spectrum, k):
    data = np.diag(np.sqrt(spectrum)).reshape(4, 2, 2)
    actual = svd_filter(np, np.linalg, data, 23, "participation_ratio")
    expected = data.copy()
    expected[:k] = 0
    np.testing.assert_allclose(actual, expected, atol=1e-12)
    assert svd_filter(np, np.linalg, data, -1, "participation_ratio") is data


@pytest.mark.parametrize("options", [
    {"effective_rank_multiplier": -1}, {"effective_rank_multiplier": np.inf},
    {"effective_rank_multiplier": True}, {"energy_fraction": 0},
    {"energy_fraction": 1.1}, {"energy_fraction": np.nan},
    {"participation_ratio_multiplier": -1}, {"participation_ratio_multiplier": np.inf},
    {"participation_ratio_multiplier": np.nan}, {"participation_ratio_multiplier": True},
    {"participation_ratio_multiplier": "1"},
])
def test_invalid_adaptive_options(options):
    with pytest.raises((ValueError, TypeError)):
        svd_filter(np, np.linalg, np.ones((4, 2, 3)), 1, **options)


@pytest.mark.parametrize("mode", ["effective_rank", "participation_ratio", "energy_fraction"])
def test_gpu_summaries(mode):
    cp = pytest.importorskip("cupy")
    if not cp.cuda.is_available():
        pytest.skip("CUDA device unavailable")
    rng = np.random.default_rng(4)
    data = rng.normal(size=(6, 3, 5)) + 1j * rng.normal(size=(6, 3, 5))
    expected_summary = dict.fromkeys(("pc_sum_static", "pc_sum_dynamic", "svd_eigenvalues"))
    actual_summary = expected_summary.copy()
    expected = svd_filter(np, np.linalg, data, 0, mode, summary=expected_summary)
    actual = svd_filter(cp, cp.linalg, cp.asarray(data), 0, mode, summary=actual_summary)
    np.testing.assert_allclose(cp.asnumpy(actual), expected, atol=1e-10)
    for name, value in actual_summary.items():
        np.testing.assert_allclose(cp.asnumpy(value), expected_summary[name], atol=1e-10)


@pytest.mark.parametrize("explicit", [False, True])
@pytest.mark.parametrize("streaming", [False, True])
def test_eigenvalue_exports(tmp_path, explicit, streaming):
    values = np.array([[9., 3., 1., 0.], [8., 4., 2., 1.]])
    params = {"num_saving_workers": 0}
    cls = OutputClass
    if explicit:
        params["outputs"] = {"svd_eigenvalues": ["h5", "csv"]}
        cls = DefaultOutput
    with cls(SimpleNamespace(file_path=tmp_path / "input.raw"), params) as output:
        if streaming:
            for i, row in enumerate(values):
                output.add_batch({"svd_eigenvalues": row}, i)
        else:
            output.write_static("svd_eigenvalues", values)
    with h5py.File(next(output.target_dir.glob("h5/*.h5"))) as h5:
        np.testing.assert_array_equal(h5["svd_eigenvalues"], values)
    np.testing.assert_array_equal(np.loadtxt(output.target_dir / "csv/svd_eigenvalues.csv", delimiter=","), values)
