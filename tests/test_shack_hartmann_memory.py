"""Fresnel autofocus must finish each subaperture before starting the next."""
from contextlib import nullcontext

import numpy as np
import pytest
from scipy import fft

from holodoppler import backend
from holodoppler.core import shack_hartmann as shack
from holodoppler.core.propagation import build_fresnel_kernel_in


ARGS = dict(wavelength=852e-9, z_prop=.1, pixel_pitch=(1e-6, 1e-6),
            low_freq=100, high_freq=450, fs=1000)


def all_subapertures_reference(frames, nx_subaps, ny_subaps, threshold, low=100, high=450):
    """Original simultaneous pipeline, retained as an independent numerical oracle."""
    nt, ny, nx = frames.shape
    sy, sx = ny // ny_subaps, nx // nx_subaps
    y0, x0 = (ny - sy * ny_subaps) // 2, (nx - sx * nx_subaps) // 2
    kernel = build_fresnel_kernel_in(np, .1, (1e-6, 1e-6), 852e-9, ny, nx)
    field = (frames * kernel)[:, y0:y0 + sy * ny_subaps, x0:x0 + sx * nx_subaps]
    tiles = field.reshape(nt, ny_subaps, sy, nx_subaps, sx).transpose(1, 3, 2, 4, 0)
    matrix = tiles.reshape(ny_subaps * nx_subaps, sy * sx, nt)
    if threshold >= 0:
        cov = np.einsum('bpi,bpj->bij', matrix.conj(), matrix)
        cov += 1e-12 * np.eye(nt, dtype=matrix.dtype)
        _, vectors = np.linalg.eigh(cov)
        removed = vectors[:, :, ::-1][:, :, :threshold]
        matrix = matrix - (matrix @ removed) @ removed.conj().transpose(0, 2, 1)
    tiles = matrix.reshape(ny_subaps * nx_subaps, sy, sx, nt).transpose(0, 3, 1, 2)
    spatial = fft.fftshift(fft.fft2(tiles), axes=(-2, -1))
    spectrum = fft.fft(spatial, axis=1)
    freqs = fft.fftfreq(nt, 1 / 1000)
    selected = abs(freqs) > low
    if high is not None:
        selected &= abs(freqs) < high
    with np.errstate(invalid='ignore'):
        power = (abs(spectrum[:, selected]) ** 2).mean(axis=1)
    return power.reshape(ny_subaps, nx_subaps, sy, sx).astype(np.float32)


@pytest.mark.parametrize('mode', ['sequential', 'parallel'])
@pytest.mark.parametrize('nt,shape', [(7, (17, 22)), (8, (18, 24))])
@pytest.mark.parametrize('threshold', [-1, 0, 2, 20])
@pytest.mark.parametrize('band', [(100, 450), (0, None), (500, 600)])
def test_subaperture_modes_match_simultaneous(nt, shape, threshold, band, mode):
    frames = np.random.default_rng(34).random((nt, *shape)).astype(np.float32)
    original = frames.copy()
    args = dict(ARGS, low_freq=band[0], high_freq=band[1])
    with pytest.warns(RuntimeWarning) if band == (500, 600) else nullcontext():
        expected = all_subapertures_reference(frames, 4, 3, threshold, *band)
    actual = shack.construct_subapertures_fresnel(
        np, fft, frames, **args, time_window=nt, nx_subabs=4, ny_subabs=3,
        svd_threshold=threshold, sub_aps_process=mode,
    )
    assert actual.dtype == np.float32
    np.testing.assert_array_equal(frames, original)
    if band == (500, 600):
        assert np.isnan(actual).all()
    else:
        scale = max(float(np.max(abs(expected))), 1)
        assert np.max(abs(actual - expected)) / scale < 1e-4


def test_autofocus_allocations_and_fft_inputs_are_subaperture_sized(monkeypatch):
    nt, ny, nx = 16, 120, 160
    tile_shape = (nt, ny // 5, nx // 5)
    tile_bytes = int(np.prod(tile_shape)) * np.dtype(np.complex64).itemsize
    class BoundedBackend:
        def __getattr__(self, name):
            return getattr(np, name)
        def empty(self, shape, dtype):
            assert int(np.prod(shape)) * np.dtype(dtype).itemsize <= tile_bytes
            return np.empty(shape, dtype=dtype)
    class BoundedFFT:
        def __getattr__(self, name):
            operation = getattr(fft, name)
            def bounded(array, *args, **kwargs):
                assert array.nbytes <= tile_bytes
                return operation(array, *args, **kwargs)
            return bounded
    calls = []
    original_filter = shack.svd_filter_batched
    def single_tile(xp, data, threshold, **kwargs):
        assert data.shape[:2] == (1, 1)
        assert data.nbytes == tile_bytes
        calls.append(data.shape)
        return original_filter(xp, data, threshold, **kwargs)
    monkeypatch.setattr(shack, 'svd_filter_batched', single_tile)
    frames = np.random.default_rng(13).random((nt, ny, nx)).astype(np.float32)
    result = shack.construct_subapertures_fresnel(
        BoundedBackend(), BoundedFFT(), frames, **ARGS, time_window=nt,
        nx_subabs=5, ny_subabs=5, svd_threshold=2,
    )
    assert result.shape == (5, 5, 24, 32)
    assert len(calls) == 25
    assert np.isfinite(result).all()


@pytest.mark.parametrize('mode', ['sequential', 'parallel'])
def test_optional_gpu_autofocus_subaperture_parity(mode):
    if not backend.cupy_available:
        pytest.skip('CUDA unavailable')
    previous = backend.get_backend_name()
    try:
        frames = np.random.default_rng(41).random((8, 18, 24)).astype(np.float32)
        expected = all_subapertures_reference(frames, 4, 3, 2)
        backend.set_backend('cupy')
        actual = shack.construct_subapertures_fresnel(
            backend.xp, backend.fft, backend.to_backend(frames), **ARGS,
            time_window=8, nx_subabs=4, ny_subabs=3, svd_threshold=2, sub_aps_process=mode,
        )
        actual = backend.to_numpy(actual)
        assert np.max(abs(actual - expected)) / max(float(np.max(abs(expected))), 1) < 1e-3
    finally:
        backend.set_backend(previous)


def angular_reference(frames, threshold):
    """Original all-subaperture angular propagation and projection."""
    from holodoppler.core.propagation import build_angular_kernel
    nt, ny, nx = frames.shape
    sy, sx = ny // 3, nx // 4
    y0, x0 = (ny - 3 * sy) // 2, (nx - 4 * sx) // 2
    kernel = build_angular_kernel(np, .1, (1e-6, 1e-6), 852e-9, ny, nx)
    spectrum = fft.fft2(frames.astype(np.complex64)) * fft.fftshift(kernel, axes=(-2, -1))
    spectrum = fft.fftshift(spectrum[:, y0:y0 + 3 * sy, x0:x0 + 4 * sx], axes=(-2, -1))
    tiles = spectrum.reshape(nt, 3, sy, 4, sx).transpose(0, 1, 3, 2, 4)
    field = fft.ifft2(fft.ifftshift(tiles, axes=(-2, -1))).transpose(1, 2, 3, 4, 0)
    matrix = field.reshape(12, sy * sx, nt)
    if threshold >= 0:
        cov = np.einsum('bpi,bpj->bij', matrix.conj(), matrix) + 1e-12 * np.eye(nt, dtype=matrix.dtype)
        _, vectors = np.linalg.eigh(cov)
        selected = vectors[:, :, ::-1][:, :, :threshold]
        matrix = matrix - (matrix @ selected) @ selected.conj().transpose(0, 2, 1)
    field = matrix.reshape(12, sy, sx, nt).transpose(0, 3, 1, 2)
    spectrum = fft.fft(field, axis=1, norm='ortho')
    frequencies = fft.fftfreq(nt, 1 / 1000)
    selected = (abs(frequencies) > 100) & (abs(frequencies) < 450)
    return (abs(spectrum[:, selected]) ** 2).mean(axis=1).reshape(3, 4, sy, sx)


@pytest.mark.parametrize('mode', ['sequential', 'parallel'])
@pytest.mark.parametrize('nt,shape', [(7, (17, 22)), (8, (18, 24))])
@pytest.mark.parametrize('threshold', [-1, 0, 2, 20])
def test_angular_modes_match_original(mode, nt, shape, threshold):
    frames = np.random.default_rng(31).random((nt, *shape)).astype(np.float32)
    original = frames.copy()
    expected = angular_reference(frames, threshold)
    actual = shack.construct_subapertures_angular(
        np, fft, frames, **ARGS, time_window=nt, nx_subabs=4, ny_subabs=3,
        svd_threshold=threshold, sub_aps_process=mode, svd_block_size_mib=.001,
    )
    assert np.max(abs(actual - expected)) / max(float(np.max(abs(expected))), 1) < 1e-4
    np.testing.assert_array_equal(frames, original)
