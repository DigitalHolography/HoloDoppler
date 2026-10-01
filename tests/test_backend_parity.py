"""Numerical parity between the NumPy and CuPy backends.

The backend abstraction must be the *same scientific operation* on either
backend, not decorative API wrapping. These tests are skipped unless a working
CUDA device is actually available.
"""

from __future__ import annotations

import numpy as np
import pytest

import holodoppler.backend as backend


cupy = pytest.importorskip("cupy", reason="CuPy is not installed")

requires_cuda = pytest.mark.skipif(
    backend._cupy_state() != "usable",
    reason="CuPy is installed but CUDA is not usable",
)


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(20240517)
    return rng.random((8, 8)).astype(np.float32)


def _as(xp, array: np.ndarray):
    return xp.asarray(array)


@requires_cuda
def test_backend_selection_reports_cupy() -> None:
    manager = backend.set_backend("gpu")

    assert manager.actual == "cupy"
    assert manager.mode is backend.BackendMode.GPU
    assert manager.is_gpu is True
    assert manager.xp is cupy


@requires_cuda
def test_from_numpy_round_trip(sample: np.ndarray) -> None:
    backend.set_backend("gpu")

    on_gpu = backend.to_backend(sample)
    assert isinstance(on_gpu, cupy.ndarray)

    back = backend.to_numpy(on_gpu)
    assert isinstance(back, np.ndarray)
    np.testing.assert_array_equal(back, sample)


@requires_cuda
def test_fft2_round_trip_matches_numpy(sample: np.ndarray) -> None:
    backend.set_backend("gpu")
    gpu_result = backend.to_numpy(
        backend.fft.ifft2(backend.fft.fft2(backend.to_backend(sample)))
    )

    backend.set_backend("cpu")
    cpu_result = backend.xp.fft.ifft2(backend.xp.fft.fft2(sample))

    np.testing.assert_allclose(gpu_result, cpu_result, rtol=1e-5, atol=1e-6)


@requires_cuda
def test_gaussian_filter_matches_numpy(sample: np.ndarray) -> None:
    backend.set_backend("gpu")
    gpu_result = backend.to_numpy(
        backend.gaussian_filter(backend.to_backend(sample), sigma=1.5)
    )

    backend.set_backend("cpu")
    cpu_result = backend.gaussian_filter(sample, sigma=1.5)

    np.testing.assert_allclose(gpu_result, cpu_result, rtol=1e-4, atol=1e-5)


@requires_cuda
def test_zoom_matches_numpy(sample: np.ndarray) -> None:
    backend.set_backend("gpu")
    gpu_result = backend.to_numpy(
        backend.zoom(backend.to_backend(sample), 2.0, order=1)
    )

    backend.set_backend("cpu")
    cpu_result = backend.zoom(sample, 2.0, order=1)

    np.testing.assert_allclose(gpu_result, cpu_result, rtol=1e-4, atol=1e-5)


@requires_cuda
def test_linalg_eigh_matches_numpy(sample: np.ndarray) -> None:
    # eigh needs a Hermitian input.
    hermitian = (sample + sample.T).astype(np.float64)

    backend.set_backend("gpu")
    gpu_values, gpu_vectors = backend.linalg.eigh(backend.to_backend(hermitian))

    backend.set_backend("cpu")
    cpu_values, cpu_vectors = backend.linalg.eigh(hermitian)

    np.testing.assert_allclose(
        backend.to_numpy(gpu_values), cpu_values, rtol=1e-6, atol=1e-8
    )
    # Eigenvectors are defined up to sign.
    np.testing.assert_allclose(
        np.abs(backend.to_numpy(gpu_vectors)), np.abs(cpu_vectors),
        rtol=1e-6, atol=1e-8,
    )


@requires_cuda
def test_elliptical_mask_matches_numpy() -> None:
    from holodoppler.core.arrays import elliptical_mask

    elliptical_mask.cache_clear()

    backend.set_backend("gpu")
    gpu_mask = backend.to_numpy(elliptical_mask(16, 16, 0.6))

    backend.set_backend("cpu")
    cpu_mask = elliptical_mask(16, 16, 0.6)

    np.testing.assert_array_equal(gpu_mask, cpu_mask)

    elliptical_mask.cache_clear()


@requires_cuda
def test_gpu_output_is_not_cached_for_cpu() -> None:
    from holodoppler.core.arrays import elliptical_mask

    elliptical_mask.cache_clear()

    backend.set_backend("gpu")
    gpu_mask = elliptical_mask(16, 16, 0.6)
    assert isinstance(gpu_mask, cupy.ndarray)

    backend.set_backend("cpu")
    cpu_mask = elliptical_mask(16, 16, 0.6)

    assert isinstance(cpu_mask, np.ndarray)
    assert cpu_mask is not gpu_mask

    elliptical_mask.cache_clear()
