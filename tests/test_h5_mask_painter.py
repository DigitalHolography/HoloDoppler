"""Mask geometry and external HDF5 contract, without launching the GUI."""
import importlib.util
from pathlib import Path

import h5py
import numpy as np
import pytest


spec = importlib.util.spec_from_file_location(
    'h5_mask_painter', Path(__file__).resolve().parents[1] / 'scripts/h5_mask_painter.py')
painter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(painter)


def test_recording_and_folder_discovery(tmp_path):
    folder = tmp_path / 'sample' / 'sample_HD' / 'h5'
    folder.mkdir(parents=True)
    for name in ('b.h5', 'a.h5'):
        with h5py.File(folder / name, 'w'):
            pass
    expected = tmp_path / 'sample' / 'sample_DV' / 'h5' / 'sample_DV.h5'
    for path in (tmp_path / 'sample.holo', folder.parent.parent, folder.parent, folder, folder / 'a.h5'):
        source, output = painter.resolve_input(path)
        assert source == folder / 'a.h5'
        assert output == expected


def test_background_priority_axis_and_nonfinite(tmp_path):
    path = tmp_path / 'input.h5'
    values = np.arange(60, dtype=float).reshape(3, 4, 5)
    values[0, 0, 0] = np.nan
    with h5py.File(path, 'w') as handle:
        handle['moment0'] = np.zeros_like(values)
        handle['nested/moment0ff'] = values
    background, name = painter.load_background(path)
    assert name == 'nested/moment0ff'
    np.testing.assert_allclose(background, np.nanmean(values, axis=0))
    with h5py.File(path, 'a') as handle:
        del handle['nested']
    np.testing.assert_array_equal(painter.load_background(path)[0], np.zeros((4, 5)))


def test_invalid_moment(tmp_path):
    path = tmp_path / 'invalid.h5'
    with h5py.File(path, 'w') as handle:
        handle['moment0'] = np.zeros((4, 5))
    with pytest.raises(ValueError, match='NT, NY, NX'):
        painter.load_background(path)


def test_continuous_brush_and_edges():
    mask = np.zeros((8, 15), np.float32)
    painter.paint_segment(mask, (1, 3), (12, 3), 1, .7)
    np.testing.assert_allclose(mask[3, 1:13], .7)
    assert not mask[0].any()
    painter.paint_segment(mask, (5, 3), (8, 3), 1, 0)
    assert not mask[3, 5:9].any()
    painter.paint_segment(mask, (-1, 0), (-1, 0), 2, 1)
    assert mask[0, 0] == 1
    assert mask[-1, -1] == 0


def test_export_roundtrip_and_dv_contract(tmp_path):
    shape = (8, 13)  # Non-square to detect accidental transposes.
    masks = {name: np.zeros(shape, np.float32) for name in painter.MASK_PATHS}
    masks['Artery'][2, 9] = .8
    masks['Vein'][6, 4] = 1
    masks['Optic disc'][1:5, 7:12] = 1
    path, source = tmp_path / 'dv.h5', tmp_path / 'hd.h5'
    with h5py.File(path, 'w') as handle:
        handle['unrelated/data'] = 42
        handle['segmentation/Retina/labeled_vessels'] = np.ones(shape)
    painter.save_masks(path, masks, source, 'moment0ff')
    with h5py.File(path, 'r') as handle:
        assert handle['unrelated/data'][()] == 42
        assert handle['provenance/manual'][()]
        assert handle.attrs['manual']
        assert 'segmentation/Retina/labeled_vessels' not in handle
        for name, key in painter.MASK_PATHS.items():
            assert handle[key].shape == shape
            assert handle[key].dtype == np.dtype(bool)
            np.testing.assert_array_equal(handle[key], masks[name] > .5)
        retina = handle['segmentation/Retina']
        assert retina['vessel_segmentation_logits'][2, 9] == np.float32(.8)
        assert retina['vessel_mask'][6, 4]
        disc = handle['segmentation/OpticDisc']
        np.testing.assert_array_equal(disc['center'], [9, 2.5])
        assert disc['width'][()] == 4
        assert disc['height'][()] == 3
    restored = painter.load_masks(path, shape)
    for name in masks:
        np.testing.assert_array_equal(restored[name], masks[name])
    masks['Optic disc'].fill(0)
    painter.save_masks(path, masks, source, 'moment0')
    with h5py.File(path, 'r') as handle:
        assert 'segmentation/OpticDisc/center' not in handle
    with pytest.raises(ValueError, match='differ'):
        painter.save_masks(source, masks, source, 'moment0')


def test_failed_save_preserves_existing_output(tmp_path, monkeypatch):
    path = tmp_path / 'dv.h5'
    with h5py.File(path, 'w') as handle:
        handle['sentinel'] = 17
    masks = {name: np.zeros((4, 7), np.float32) for name in painter.MASK_PATHS}

    def fail_replace(*args):
        raise PermissionError('File locked')

    monkeypatch.setattr(painter.os, 'replace', fail_replace)
    with pytest.raises(PermissionError):
        painter.save_masks(path, masks, tmp_path / 'source.h5', 'moment0')
    with h5py.File(path, 'r') as handle:
        assert handle['sentinel'][()] == 17
    assert list(tmp_path.iterdir()) == [path]
