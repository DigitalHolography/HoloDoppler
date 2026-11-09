"""Explicit saving contracts, independent of legacy filename heuristics."""
from types import SimpleNamespace
from unittest.mock import Mock

import h5py
import numpy as np
import pytest

from holodoppler.saving.default_output import (
    DefaultOutput, computation_parameters, selected_formats, validate_outputs,
)


def reader(tmp_path):
    return SimpleNamespace(file_path=tmp_path / "input.raw")


@pytest.mark.parametrize("rules", [None, [], {"a": "h5"}, {"a": ["jpeg"]}, {"../a": []}])
def test_invalid_rules(rules):
    with pytest.raises((TypeError, ValueError)):
        validate_outputs({"outputs": rules})


def test_precedence():
    p = {"outputs": {"*": ["h5"], "moment*": ["avi"], "moment0": []}}
    assert selected_formats(p, "moment0") == set()
    assert selected_formats(p, "moment1") == {"avi"}
    assert selected_formats(p, "other") == {"h5"}


@pytest.mark.parametrize("workers", [0, 2])
def test_projection_only_and_csv(tmp_path, workers):
    p = {"outputs": {"moment0_time_projection": ["h5", "png"], "registration": ["csv"]},
         "num_saving_workers": workers}
    with DefaultOutput(reader(tmp_path), p) as out:
        for i in range(3):
            out.add_batch({"moment0": np.full((4, 6), i + 1., dtype=np.float32),
                           "registration": np.array([i, -i])}, i)
    with h5py.File(next(out.target_dir.glob("h5/*.h5"))) as h5:
        assert "moment0" not in h5
        np.testing.assert_array_equal(h5["moment0_time_projection"], 2.)
    assert (out.target_dir / "png/moment0_time_projection.png").exists()
    assert not (out.target_dir / "png/moment0.png").exists()
    np.testing.assert_array_equal(np.loadtxt(out.target_dir / "csv/registration.csv", delimiter=","),
                                  [[0, 0], [1, -1], [2, -2]])


@pytest.mark.parametrize("fmt", ["avi", "mp4"])
def test_independent_video_formats(tmp_path, monkeypatch, fmt):
    writer = Mock()
    open_video = Mock(return_value=writer)
    monkeypatch.setattr(DefaultOutput, "_open_video", lambda self, name, selected: open_video(selected))
    with DefaultOutput(reader(tmp_path), {"outputs": {"moment0": [fmt]}}) as out:
        out.add("moment0", np.ones((4, 6)), 0)
    open_video.assert_called_once_with(fmt)
    writer.append_data.assert_called_once()
    writer.close.assert_called_once()
    assert not list((out.target_dir / "png").glob("*.png"))


def test_incompatible_warns_once_and_preserves_h5(tmp_path, monkeypatch):
    warning = Mock()
    monkeypatch.setattr("holodoppler.saving.default_output.logger.warning", warning)
    with DefaultOutput(reader(tmp_path), {"outputs": {"spectrograms": ["h5", "avi", "csv"]}}) as out:
        for i in range(2):
            out.add("spectrograms", np.ones((8, 4, 3)), i)
    assert warning.call_count == 2
    with h5py.File(next(out.target_dir.glob("h5/*.h5"))) as h5:
        assert h5["spectrograms"].shape == (2, 8, 4, 3)


def test_cancel_skips_projection(tmp_path):
    out = DefaultOutput(reader(tmp_path), {"outputs": {"moment0_time_projection": ["h5"]}})
    out.add("moment0", np.ones((4, 6)), 0)
    out.close(finalize=False)
    out.close()
    with h5py.File(next(out.target_dir.glob("h5/*.h5"))) as h5:
        assert "moment0_time_projection" not in h5


def test_optional_computation_and_reference():
    p = computation_parameters({"outputs": {"pca_sum_time_projection": ["png"]},
                                "image_registration": True, "registration_image": "gaussian_width"})
    assert p["pca_compute"] and p["compute_gaussian_width"]
    assert not p["color_Doppler_image"]
    assert not p["save_spectograms"]
    assert not p["shack_hartmann"]


@pytest.mark.parametrize("live", [True, False])
@pytest.mark.parametrize("ecc", [True, False])
@pytest.mark.parametrize("workers", [0, 2])
def test_pipeline_modes(tmp_path, monkeypatch, live, ecc, workers):
    from holodoppler.pipelines import main_default as pipeline
    from test_default_pipeline_contract import parameters
    from holodoppler import backend
    backend.set_backend("numpy")
    p = parameters(live_saving=live, image_registration_with_ecc=ecc,
                   numpy_num_workers=0, num_saving_workers=workers,
                   outputs={"moment0": ["h5"], "moment0_time_projection": ["h5"]})
    monkeypatch.setattr(pipeline, "_process_one_batch", lambda *a, **kw:
                        ({"moment0": np.ones((4, 6)), "moment0ff": np.ones((4, 6))}, None))
    monkeypatch.setattr(pipeline, "register_with_ecc", lambda *a, **kw: np.zeros((2, 2)))
    monkeypatch.setattr(pipeline, "apply_ecc_registration", lambda images, *a, **kw: images * 2)
    source = reader(tmp_path)
    source.read_frames = lambda **kw: np.ones((8, 4, 6))
    with DefaultOutput(source, p) as out:
        pipeline._process_to_output(source, p, [0, 8], out, None)
    with h5py.File(next(out.target_dir.glob("h5/*.h5"))) as h5:
        assert h5["moment0"].shape == (2, 4, 6)
        np.testing.assert_array_equal(h5["moment0_time_projection"], 2 if ecc else 1)


@pytest.mark.parametrize("preview", [False, True])
def test_real_default_entrypoint(tmp_path, monkeypatch, preview):
    from holodoppler.pipelines import main_default as pipeline
    from test_default_pipeline_contract import parameters
    p = parameters(outputs={"moment0_time_projection": ["h5", "png"],
                            "static_pc_sum": ["h5"], "dynamic_pc_sum": ["h5"],
                            "svd_eigenvalues": ["h5", "csv"],
                            "spectrograms": ["h5"], "averaged_spectrogram": ["h5"]},
                   numpy_num_workers=0, spectrogram_resize_shape=[4, 6],
                   spectrogram_frequency_binning=2)
    source = reader(tmp_path)
    frames = np.random.default_rng(42).normal(size=(16, 4, 6)).astype(np.float32)
    source.extension = ".raw"
    source.total_frames = len(frames)
    source.read_frames = lambda first_frame, batch_size, **kw: frames[first_frame:first_frame+batch_size]
    monkeypatch.setattr(pipeline, "get_reader", lambda _: source)
    if preview:
        pipeline.preview(source.file_path, p)
    else:
        pipeline.process(source.file_path, p)
    with h5py.File(next(tmp_path.rglob("*_output.h5"))) as h5:
        count = 1 if preview else 2
        assert h5["svd_eigenvalues"].shape == (count, 8)
        assert h5["static_pc_sum"].shape == (count, 4, 6)
        assert h5["dynamic_pc_sum"].shape == (count, 4, 6)
        csv = next(tmp_path.rglob("svd_eigenvalues.csv"))
        np.testing.assert_allclose(np.loadtxt(csv, delimiter=",", ndmin=2), h5["svd_eigenvalues"])
        assert "moment0" not in h5
        assert h5["moment0_time_projection"].shape == (4, 6)
        assert h5["spectrograms"].shape[0] == (1 if preview else 2)
        assert h5["averaged_spectrogram"].shape == (8, 4, 6)


@pytest.mark.parametrize("shape", [(4, 6), (8, 4, 3)])
def test_spatial_data_cannot_be_csv(tmp_path, monkeypatch, shape):
    warning = Mock()
    monkeypatch.setattr("holodoppler.saving.default_output.logger.warning", warning)
    name = "moment0" if len(shape) == 2 else "spectrograms"
    with DefaultOutput(reader(tmp_path), {"outputs": {name: ["csv"]}}) as out:
        out.add(name, np.ones(shape), 0)
    warning.assert_called_once()
    assert not list((out.target_dir / "csv").glob("*.csv"))


def test_unavailable_dataset_warning(tmp_path, monkeypatch):
    warning = Mock()
    monkeypatch.setattr("holodoppler.saving.default_output.logger.warning", warning)
    with DefaultOutput(reader(tmp_path), {"outputs": {"typo": ["h5"]}}):
        pass
    warning.assert_called_once()


def test_writer_failure_does_not_finalize_projection(tmp_path, monkeypatch):
    def fail(*args):
        raise OSError("encoder failed")
    monkeypatch.setattr(DefaultOutput, "_open_video", fail)
    p = {"outputs": {"moment0": ["avi"], "moment0_time_projection": ["h5"]}}
    with pytest.raises(OSError, match="encoder failed"):
        with DefaultOutput(reader(tmp_path), p) as out:
            out.add("moment0", np.ones((4, 6)), 0)
    with h5py.File(next(out.target_dir.glob("h5/*.h5"))) as h5:
        assert "moment0_time_projection" not in h5
