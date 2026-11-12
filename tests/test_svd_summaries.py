"""SVD amplitude summaries, adaptive rank selection, and numerical exports."""
from types import SimpleNamespace

import h5py
import numpy as np
import pytest

from holodoppler.core.filtering import svd_filter
from holodoppler.saving import OutputClass
from holodoppler.saving.default_output import DefaultOutput


@pytest.mark.parametrize("temporal_dc", [False, True])
@pytest.mark.parametrize("count", [-1, 0, 2])
@pytest.mark.parametrize("budget", [None, .0002])
@pytest.mark.parametrize("dtype", [np.complex64, np.complex128])
def test_spatial_dc_matches_full_frame_reference(temporal_dc, count, budget, dtype):
    rng = np.random.default_rng(91)
    source = (rng.normal(size=(5, 3, 7)) + 1j * rng.normal(size=(5, 3, 7))).astype(dtype)
    source += np.arange(5)[:, None, None] * (2 + 3j)
    source += np.arange(7)[None, None, :]
    source = source.swapaxes(1, 2)  # Spatial means must also work on strided data.
    original = source.copy()
    centered = source.copy()
    temporal_mean = np.zeros(source.shape[1:], dtype=dtype)
    spatial_mean = None
    if count >= 0:
        if temporal_dc:
            temporal_mean = centered.mean(axis=0)
            centered -= temporal_mean
        spatial_mean = centered.mean(axis=(1, 2))
        centered -= spatial_mean[:, None, None]
    removed_dc = source - centered
    matrix = centered.reshape(5, -1)
    u, _, _ = np.linalg.svd(matrix, full_matrices=False)
    k = max(count, 0)
    expected = (matrix - u[:, :k] @ (u[:, :k].conj().T @ matrix)).reshape(source.shape)
    summary = dict.fromkeys(("svd_dc", "svd_dc_spatial", "svd_eigenvalues"))
    diagnostic = {}
    actual = svd_filter(np, np.linalg, source, count, remove_dc=temporal_dc,
                        remove_spatial_dc=True, summary=summary, diagnostic=diagnostic,
                        block_size_mib=budget)
    np.testing.assert_allclose(actual, expected, atol=2e-5)
    np.testing.assert_array_equal(source, original)
    np.testing.assert_allclose(summary["svd_dc"], np.abs(temporal_mean), atol=2e-5)
    if spatial_mean is None:
        assert summary["svd_dc_spatial"] is None
    else:
        assert summary["svd_dc_spatial"].shape == (source.shape[0],)
        np.testing.assert_allclose(summary["svd_dc_spatial"], np.abs(spatial_mean), atol=2e-5)
    if count < 0:
        assert actual is source
        assert diagnostic["dc"] is None
    else:
        np.testing.assert_allclose(diagnostic["dc"], removed_dc, atol=2e-5)
        np.testing.assert_allclose(diagnostic["covariance"], matrix.conj() @ matrix.T, atol=5e-4)
        # The combined DC and removed SVD modes reconstruct the original input.
        removed = (diagnostic["eigenvectors"][:, :k].conj()
                   @ diagnostic["removed_features"].reshape(-1, k).T
                   if k else np.zeros_like(matrix))
        np.testing.assert_allclose(actual + diagnostic["dc"] + removed.reshape(source.shape),
                                   source, atol=2e-5)


@pytest.mark.parametrize("temporal_dc", [False, True])
def test_dc_summary_without_spatial_removal(temporal_dc):
    source = np.array([[[1 + 2j, 3 - 4j]], [[5 - 2j, 1 + 8j]]])
    summary = {"svd_dc": None, "svd_dc_spatial": "uncomputed"}
    svd_filter(np, np.linalg, source, 0, remove_dc=temporal_dc, summary=summary)
    expected = np.abs(source.mean(axis=0)) if temporal_dc else np.zeros(source.shape[1:])
    np.testing.assert_allclose(summary["svd_dc"], expected)
    assert summary["svd_dc_spatial"] is None


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


@pytest.mark.parametrize("value", [1, "true", None])
def test_spatial_dc_requires_boolean(value):
    with pytest.raises(TypeError, match="remove_spatial_dc"):
        svd_filter(np, np.linalg, np.ones((2, 1, 2)), 0, remove_spatial_dc=value)


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
@pytest.mark.parametrize("spatial_dc", [False, True])
def test_gpu_summaries(mode, spatial_dc):
    cp = pytest.importorskip("cupy")
    if not cp.cuda.is_available():
        pytest.skip("CUDA device unavailable")
    rng = np.random.default_rng(4)
    data = rng.normal(size=(6, 3, 5)) + 1j * rng.normal(size=(6, 3, 5))
    expected_summary = dict.fromkeys(("pc_sum_static", "pc_sum_dynamic", "svd_eigenvalues", "eigen_spectrogram", "svd_dc", "svd_dc_spatial"))
    actual_summary = expected_summary.copy()
    options = dict(remove_dc=True, remove_spatial_dc=spatial_dc, block_size_mib=.0002)
    expected = svd_filter(np, np.linalg, data, 0, mode, summary=expected_summary, **options)
    actual = svd_filter(cp, cp.linalg, cp.asarray(data), 0, mode, summary=actual_summary, **options)
    np.testing.assert_allclose(cp.asnumpy(actual), expected, atol=1e-10)
    for name, value in actual_summary.items():
        if value is None:
            assert expected_summary[name] is None
        else:
            np.testing.assert_allclose(cp.asnumpy(value), expected_summary[name], atol=1e-10)


@pytest.mark.parametrize("explicit", [False, True])
@pytest.mark.parametrize("streaming", [False, True])
@pytest.mark.parametrize("name", ["svd_eigenvalues", "svd_dc_spatial"])
def test_numerical_vector_exports(tmp_path, explicit, streaming, name):
    values = np.array([[9., 3., 1., 0.], [8., 4., 2., 1.]])
    params = {"num_saving_workers": 0}
    cls = OutputClass
    if explicit:
        params["outputs"] = {name: ["h5", "csv"]}
        cls = DefaultOutput
    with cls(SimpleNamespace(file_path=tmp_path / "input.raw"), params) as output:
        if streaming:
            for i, row in enumerate(values):
                output.add_batch({name: row}, i)
        else:
            output.write_static(name, values)
    with h5py.File(next(output.target_dir.glob("h5/*.h5"))) as h5:
        np.testing.assert_array_equal(h5[name], values)
    np.testing.assert_array_equal(np.loadtxt(output.target_dir / "csv" / f"{name}.csv", delimiter=","), values)


@pytest.mark.parametrize("nt", [7, 8])
@pytest.mark.parametrize("threshold", [-1, 0, 2])
def test_eigen_spectrogram_signed_modes(nt, threshold):
    bins = np.roll(np.rint(np.fft.fftfreq(nt) * nt).astype(int), 2)
    modes = np.exp(2j * np.pi * np.arange(nt)[:, None] * bins / nt) / np.sqrt(nt)
    energies = np.arange(nt, 0, -1)
    source = (modes * np.sqrt(energies)).reshape(nt, 1, nt)
    summary = dict.fromkeys(("eigen_spectrogram", "svd_eigenvalues"))
    expected_filtered = svd_filter(np, np.linalg, source, threshold)
    actual = svd_filter(np, np.linalg, source, threshold, summary=summary)
    np.testing.assert_allclose(actual, expected_filtered, atol=1e-12)
    if threshold < 0:
        assert actual is source
    spectrum = summary["eigen_spectrogram"]
    assert spectrum.shape == (nt, nt)
    assert np.isrealobj(spectrum) and np.all(spectrum >= 0)
    frequencies = np.fft.fftshift(np.fft.fftfreq(nt)) * nt
    expected = np.isclose(bins[:, None], frequencies[None, :]).astype(float)
    np.testing.assert_allclose(spectrum, expected, atol=1e-12)
    np.testing.assert_allclose(spectrum.sum(axis=1), 1, atol=1e-12)
    np.testing.assert_allclose(summary["svd_eigenvalues"], energies, atol=1e-12)


@pytest.mark.parametrize("temporal_dc", [False, True])
@pytest.mark.parametrize("spatial_dc", [False, True])
@pytest.mark.parametrize("threshold", [-1, 2])
def test_eigen_spectrogram_resolves_input_power(temporal_dc, spatial_dc, threshold):
    rng = np.random.default_rng(72)
    source = rng.normal(size=(8, 3, 5)) + 1j * rng.normal(size=(8, 3, 5))
    centered = source.copy()
    if threshold >= 0:
        if temporal_dc:
            centered -= centered.mean(axis=0)
        if spatial_dc:
            centered -= centered.mean(axis=(1, 2), keepdims=True)
    summary = dict.fromkeys(("eigen_spectrogram", "svd_eigenvalues"))
    svd_filter(np, np.linalg, source, threshold, summary=summary,
               remove_dc=temporal_dc, remove_spatial_dc=spatial_dc)
    expected = np.fft.fftshift(
        (abs(np.fft.fft(centered, axis=0, norm="ortho"))**2).sum(axis=(1, 2)))
    np.testing.assert_allclose(
        summary["svd_eigenvalues"] @ summary["eigen_spectrogram"], expected, atol=1e-12)
    np.testing.assert_allclose(summary["eigen_spectrogram"].sum(axis=1), 1, atol=1e-12)


def test_eigen_spectrogram_fft_is_optional(monkeypatch):
    def unexpected_fft(*args, **kwargs):
        pytest.fail("Unrequested eigenvector FFT")
    monkeypatch.setattr(np.fft, "fft", unexpected_fft)
    svd_filter(np, np.linalg, np.ones((8, 2, 3)), 2,
               summary={"svd_eigenvalues": None})
