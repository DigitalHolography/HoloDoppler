"""Numerical fitting checks without starting the Tk application."""
import importlib.util
from pathlib import Path
import threading

import numpy as np
import pytest


spec = importlib.util.spec_from_file_location(
    'h5_roi_spectra', Path(__file__).resolve().parents[1] / 'scripts/h5_roi_spectra.py')
viewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(viewer)


def make_entry():
    n = 128
    frequency = np.fft.fftshift(np.fft.fftfreq(n, 1 / 1280))
    parameters = np.array([[[2, 5, 90], [1, 3, 120]],
                           [[4, 8, 180], [3, 6, 60]]], dtype=float)
    shifted = np.empty((n, 2, 2))
    for row, col in np.ndindex((2, 2)):
        shifted[:, row, col] = viewer.gaussian_model(frequency, *parameters[row, col])
    return dict(spectrum=np.fft.ifftshift(shifted, axes=0), freq=frequency, fs=1280), parameters


@pytest.mark.parametrize('symmetric', [False, True])
@pytest.mark.parametrize('normalization', ['none', 'num_freq', 'density', 'peak', 'unit_area'])
def test_parameter_recovery(symmetric, normalization):
    entry, parameters = make_entry()
    progress = []
    maps = viewer.fit_pixel_maps(entry, 20, 500, symmetric, normalization=normalization,
                                progress=lambda done, total: progress.append((done, total)))
    for row, col in np.ndindex((2, 2)):
        _, normalized, _, _ = viewer.prepare_spectrum(
            entry['spectrum'][:, row, col], entry['freq'], entry['fs'], normalization)
        original = viewer.gaussian_model(entry['freq'][entry['freq'] != 0], *parameters[row, col])
        factor = normalized[0] / original[0]
        np.testing.assert_allclose([maps['K'][row, col], maps['A'][row, col], maps['W'][row, col]],
                                   parameters[row, col] * [factor, factor, 1], rtol=1e-4)
    np.testing.assert_allclose(maps['R²'], 1, atol=1e-9)
    assert progress[-1] == (4, 4)


def test_mask_and_invalid_ranges():
    frequency = np.arange(-5, 6, dtype=float)
    np.testing.assert_array_equal(frequency[viewer.fit_frequency_mask(frequency, 0, 4, True)],
                                  [-4, -3, -2, -1, 1, 2, 3, 4])
    for low, high in [(-1, 5), (3, 3), (4, 2), (0, np.inf), (0, 3), (100, 200)]:
        with pytest.raises(ValueError):
            viewer.fit_frequency_mask(frequency, low, high, True)


@pytest.mark.parametrize('normalization', ['none', 'peak', 'unit_area'])
def test_bad_pixels_and_partial_nonfinite_data(normalization):
    entry, _ = make_entry()
    entry['spectrum'][:, 0, 0] = 2
    entry['spectrum'][:, 0, 1] = np.nan
    entry['spectrum'][5, 1, 0] = np.nan
    maps = viewer.fit_pixel_maps(entry, 20, 500, normalization=normalization)
    for values in maps.values():
        assert np.isnan(values[0]).all()
        assert np.isfinite(values[1]).all()


def test_cancellation():
    entry, _ = make_entry()
    cancel = threading.Event()
    progress = []

    def on_progress(done, total):
        progress.append(done)
        cancel.set()

    assert viewer.fit_pixel_maps(entry, 20, 500, cancel=cancel, progress=on_progress) is None
    assert progress == [1]


def test_insufficient_finite_samples():
    entry, _ = make_entry()
    entry['spectrum'][3:, 0, 0] = np.nan
    maps = viewer.fit_pixel_maps(entry, 20, 500)
    assert all(np.isnan(values[0, 0]) for values in maps.values())


def test_negative_r_squared_is_preserved():
    entry, _ = make_entry()
    entry['spectrum'] *= -1
    maps = viewer.fit_pixel_maps(entry, 20, 500, normalization='none')
    assert (maps['R²'] < 0).all()


def test_solver_failure(monkeypatch):
    entry, _ = make_entry()

    def fail(*args, **kwargs):
        raise RuntimeError('No convergence')

    monkeypatch.setattr(viewer, 'curve_fit', fail)
    maps = viewer.fit_pixel_maps(entry, 20, 500)
    assert all(np.isnan(values).all() for values in maps.values())


def test_r_squared_matches_residuals():
    entry, _ = make_entry()
    rng = np.random.default_rng(5)
    entry['spectrum'] += rng.normal(0, 0.08, entry['spectrum'].shape)
    maps = viewer.fit_pixel_maps(entry, 20, 500, normalization='none')
    mask = viewer.fit_frequency_mask(entry['freq'], 20, 500, True)
    y = np.fft.fftshift(entry['spectrum'], axes=0)[mask, 0, 0]
    predicted = viewer.gaussian_model(entry['freq'][mask],
                                     *[maps[name][0, 0] for name in ('K', 'A', 'W')])
    expected = 1 - np.sum((y - predicted)**2) / np.sum((y - y.mean())**2)
    assert maps['R²'][0, 0] == pytest.approx(expected)
