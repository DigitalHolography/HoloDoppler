"""Synthetic H5 checks for the recording comparison app, without starting Tk."""
import importlib.util
import json
from pathlib import Path

import h5py
from matplotlib.figure import Figure
import numpy as np
import pytest


spec = importlib.util.spec_from_file_location(
    'h5_compare_spectra', Path(__file__).resolve().parents[1] / 'scripts/h5_compare_spectra.py')
viewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(viewer)


def make_h5(tmp_path, name='recording', fs=800, skip=1, shape=(8, 2, 3)):
    source = tmp_path / f'{name}.holo'
    source.touch()
    folder = tmp_path / name / f'{name}_HD' / 'h5'
    folder.mkdir(parents=True)
    path = folder / f'{name}_output.h5'
    values = np.arange(np.prod(shape), dtype=float).reshape(shape) + 1
    with h5py.File(path, 'w') as handle:
        handle['HD_parameters'] = json.dumps(dict(sampling_freq=fs, skip_every=skip))
        handle['averaged_spectrogram'] = values
    return source, path, values


@pytest.mark.parametrize('normalization,divisor', [('none', 1), ('num_freq', 8),
                                                ('num_freq_squared', 64), ('density', 3200)])
def test_symmetric_band_and_full_field_mean(tmp_path, normalization, divisor):
    source, path, values = make_h5(tmp_path, skip=2)
    entry = viewer.load_comparison(source, 50, 100, normalization)
    assert entry['path'] == path
    assert entry['fs'] == 400
    # Energy uses raw power across ALL bins, independent of display normalization/band.
    assert entry['energy'] == pytest.approx(values.mean(axis=(1, 2)).sum() / 400)
    assert entry['dc_energy'] == pytest.approx(values[0].mean() / 400)
    # Stored FFT order is [0, 50, 100, 150, -200, -150, -100, -50].
    np.testing.assert_allclose(entry['image'], values[[1, 2, 6, 7]].mean(axis=0) / divisor)
    np.testing.assert_array_equal(entry['frequency'], [-200, -150, -100, -50, 50, 100, 150])
    np.testing.assert_allclose(entry['power'], values.mean(axis=(1, 2))[[4, 5, 6, 7, 1, 2, 3]] / divisor)
    assert entry['selected_bins'] == 4


def test_dc_exclusion_and_different_grids(tmp_path):
    source, path, values = make_h5(tmp_path)
    other, _, _ = make_h5(tmp_path, 'other', fs=600, shape=(5, 3, 1))
    entries = [viewer.load_comparison(p, 0, 10000, 'none') for p in (source, other)]
    np.testing.assert_allclose(entries[0]['image'], values[1:].mean(axis=0))
    assert viewer.resolve_h5(path) == path
    images, spectra = Figure(), Figure()
    viewer.plot_comparisons(entries, images, spectra)
    assert len(spectra.axes[0].lines) == 2
    assert f"E={entries[0]['energy']:.4g}" in spectra.axes[0].lines[0].get_label()
    assert f"E_DC={entries[0]['dc_energy']:.4g}" in spectra.axes[0].lines[0].get_label()
    assert [len(line.get_xdata()) for line in spectra.axes[0].lines] == [7, 4]
    assert [ax.images[0].get_array().shape for ax in images.axes if ax.images] == [(2, 3), (3, 1)]


@pytest.mark.parametrize('skip', [0, -1, 1.5, float('inf')])
def test_invalid_skip(tmp_path, skip):
    source, _, _ = make_h5(tmp_path, skip=skip)
    with pytest.raises(ValueError, match='skip_every'):
        viewer.load_comparison(source, 0, 100)


def test_null_skip_and_empty_band(tmp_path):
    source, _, _ = make_h5(tmp_path, skip=None)
    assert viewer.load_comparison(source, 0, 200)['fs'] == 800
    with pytest.raises(ValueError, match='No nonzero bins'):
        viewer.load_comparison(source, 1, 20)


def test_ambiguous_and_missing_outputs(tmp_path):
    source, path, _ = make_h5(tmp_path)
    (path.parent / 'extra.h5').touch()
    with pytest.raises(ValueError, match='Multiple H5'):
        viewer.resolve_h5(source)
    with pytest.raises(FileNotFoundError, match='H5 folder'):
        viewer.resolve_h5(tmp_path / 'missing.holo')


def test_roi_spectrum_energy_and_clear(tmp_path):
    source, _, values = make_h5(tmp_path, skip=2)
    full = viewer.load_comparison(source, 50, 100, 'none')
    roi = viewer.select_roi(full, (1, 3, 0, 1))
    expected = values[:, 0:1, 1:3].mean(axis=(1, 2))
    np.testing.assert_allclose(roi['power'], expected[roi['order']])
    assert roi['energy'] == pytest.approx(expected.sum() / 400)
    assert roi['dc_energy'] == pytest.approx(expected[0] / 400)
    np.testing.assert_array_equal(roi['image'], full['image'])
    assert full['roi'] is None
    for mode in viewer.NORMALIZATIONS:
        viewer.normalize_entry(roi, mode)
        assert roi['energy'] == pytest.approx(expected.sum() / 400)
    viewer.normalize_entry(roi, 'none')
    restored = viewer.select_roi(roi, None)
    np.testing.assert_allclose(restored['power'], full['power'])
    assert restored['roi'] is None
    images, spectra = Figure(), Figure()
    viewer.plot_comparisons([roi], images, spectra)
    assert 'ROI x[1:3], y[0:1]' in spectra.axes[0].lines[0].get_label()
    assert len(images.axes[0].patches) == 1


def test_roi_clipping_and_no_overlap(tmp_path):
    source, _, values = make_h5(tmp_path)
    full = viewer.load_comparison(source, 0, 400, 'none')
    clipped = viewer.select_roi(full, (-2, 20, 1, 10))
    assert clipped['roi'] == (0, 3, 1, 2)
    np.testing.assert_allclose(clipped['mean'], values[:, 1:2, :].mean(axis=(1, 2)))
    with pytest.raises(ValueError, match='does not overlap'):
        viewer.select_roi(full, (5, 10, 0, 2))


@pytest.mark.parametrize('mode', ['unit_area', 'peak'])
def test_shape_normalization_and_zero_spectra(tmp_path, mode):
    source, path, values = make_h5(tmp_path)
    entry = viewer.load_comparison(source, 0, 400, mode)
    if mode == 'unit_area':
        assert entry['power'].sum() * 100 == pytest.approx(1)
        expected = values[1:].mean(axis=0) / (values[1:].sum(axis=0) * 100)
    else:
        assert entry['power'].max() == pytest.approx(1)
        expected = values[1:].mean(axis=0) / values[1:].max(axis=0)
    np.testing.assert_allclose(entry['image'], expected)
    with h5py.File(path, 'r+') as handle:
        handle['averaged_spectrogram'][:] = 0
    zero = viewer.load_comparison(source, 0, 400, mode)
    np.testing.assert_array_equal(zero['power'], 0)
    np.testing.assert_array_equal(zero['image'], 0)
