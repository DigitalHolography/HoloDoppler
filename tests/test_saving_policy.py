"""Format selection is shared by static, buffered, and streaming exports."""
from types import SimpleNamespace
from unittest.mock import Mock

import h5py
import numpy as np
from PIL import Image
import pytest

from holodoppler import saving
from holodoppler.saving import data, media, policy
from holodoppler.get_version import get_version


@pytest.mark.parametrize("name, shape, static, temporal", [
    ("moment0", (6, 8), {"h5", "png"}, {"h5", "avi", "mp4", "png"}),
    ("moment0", (2, 6, 8), {"h5", "avi", "mp4", "png"}, {"h5"}),
    ("spectrum_line", (8,), {"h5"}, {"h5"}),
    ("averaged_spectrogram", (6, 8), {"h5"}, {"h5"}),
    ("averaged_spectrogram", (16, 6, 8), {"h5"}, {"h5"}),
    ("NW_moment0", (6, 8), {"h5", "png"}, {"h5", "avi", "mp4", "png"}),
    ("spatial_flow_index", (6, 8), {"h5", "png"}, {"h5", "avi", "mp4", "png"}),
    ("band_0", (6, 8), {"h5", "png"}, {"h5", "avi", "mp4", "png"}),
    ("registration", (2, 3), {"h5", "csv"}, {"h5", "csv"}),
    ("shack_hartmann_zernike_coefs", (3,), {"h5", "csv"}, {"h5", "csv"}),
    ("shack_hartmann_shifts", (2, 3, 2), {"h5", "csv"}, {"h5", "csv"}),
    ("shack_hartmann_autofocus_shifts", (2, 3, 2, 3, 2), {"h5", "csv"}, {"h5", "csv"}),
    ("color_Doppler_image", (6, 8, 3), {"png"}, {"avi", "mp4", "png"}),
    ("directional_Doppler_image", (2, 6, 8, 3), {"avi", "mp4", "png"}, set()),
    ("diagnostic", (6, 8), {"png"}, {"avi", "mp4", "png"}),
    ("unknown", (8,), set(), set()),
])
def test_output_formats(name, shape, static, temporal):
    value = np.zeros(shape, dtype=np.float32)
    assert policy.output_formats(name, value) == static
    assert policy.output_formats(name, value, temporal=True) == temporal


@pytest.mark.parametrize("mode, workers", [("legacy", None), ("bundle", 0), ("bundle", 2), ("stream", 0), ("stream", 2)])
def test_all_saving_paths_share_formats(tmp_path, monkeypatch, mode, workers):
    monkeypatch.setattr(data, "get_git_version", lambda: "test")
    monkeypatch.setattr(media, "save_video", lambda *args, **kwargs: None)
    monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *args: Mock())
    reader = SimpleNamespace(file_path=tmp_path / "input.raw", extension=".raw")
    moment = np.ones((2, 6, 8), dtype=np.float32)
    moment[:, 0, :3] = [np.nan, np.inf, -np.inf]
    rgb = np.full((2, 6, 8, 3), .25, dtype=np.float32)
    shifts = np.full((2, 2, 3, 2), np.nan, dtype=np.float32)
    reference = np.full((2, 3, 2, 3, 2), np.nan, dtype=np.float32)
    temporal = dict(moment0=moment, color_Doppler_image=rgb,
                    directional_Doppler_image=rgb, shack_hartmann_shifts=shifts)
    parameters = {"num_saving_workers": workers or 0}
    if mode == "stream":
        with saving.OutputClass(reader, parameters, custom_path=tmp_path / "output") as destination:
            for t in range(2):
                destination.add_batch({name: value[t] for name, value in temporal.items()}, t)
            destination.write_static("shack_hartmann_autofocus_shifts", reference)
        target = destination.target_dir
    else:
        target = saving.save_outputs(
            reader, dict(temporal, shack_hartmann_autofocus_shifts=reference),
            parameters, custom_path=tmp_path / "output", num_saving_workers=workers)
    with h5py.File(next(target.rglob("*.h5"))) as handle:
        assert "color_Doppler_image" not in handle
        assert "directional_Doppler_image" not in handle
        np.testing.assert_equal(handle["moment0"][:], moment)
        np.testing.assert_equal(handle["shack_hartmann_shifts"][:], shifts)
        np.testing.assert_equal(handle["shack_hartmann_autofocus_shifts"][:], reference)
        assert handle["HD_version"][()] == f"py{get_version()}".encode()
        assert handle["git_commit"][()] == b"test"
    for name, value in (("shack_hartmann_shifts", shifts), ("shack_hartmann_autofocus_shifts", reference)):
        np.testing.assert_equal(np.loadtxt(target / "csv" / f"{name}.csv", delimiter=",").reshape(value.shape), value)
        assert not (target / "png" / f"{name}.png").exists()
    for name in ("color_Doppler_image", "directional_Doppler_image"):
        with Image.open(target / "png" / f"{name}.png") as image:
            np.testing.assert_equal(np.asarray(image), np.full((6, 8, 3), 64, dtype=np.uint8))


@pytest.mark.parametrize("mode, workers", [("legacy", None), ("bundle", 0), ("bundle", 2), ("stream", 0), ("stream", 2)])
def test_averaged_spectrogram_is_hdf5_only(tmp_path, monkeypatch, mode, workers):
    monkeypatch.setattr(data, "get_git_version", lambda: "test")
    video = Mock()
    monkeypatch.setattr(media, "save_video", video)
    reader = SimpleNamespace(file_path=tmp_path / "input.raw", extension=".raw")
    average = np.arange(16 * 6 * 8, dtype=np.float32).reshape(16, 6, 8)
    if mode == "stream":
        with saving.OutputClass(reader, {"num_saving_workers": workers},
                                custom_path=tmp_path / "output") as destination:
            destination.write_static("averaged_spectrogram", average)
        target = destination.target_dir
    else:
        target = saving.save_outputs(reader, {"averaged_spectrogram": average},
                                     custom_path=tmp_path / "output", num_saving_workers=workers)
    with h5py.File(next(target.rglob("*.h5"))) as handle:
        np.testing.assert_array_equal(handle["averaged_spectrogram"][:], average)
    video.assert_not_called()
    assert list(media.media_jobs(target, "averaged_spectrogram", average, 10)) == []
    for fmt in ("avi", "mp4", "png"):
        assert not list((target / fmt).iterdir())


def test_encoder_open_failure_closes_partial_media_and_hdf5(tmp_path, monkeypatch):
    writer = Mock()
    def open_video(self, name, fmt):
        if fmt == "mp4":
            raise OSError("cannot open mp4")
        return writer
    monkeypatch.setattr(saving.OutputClass, "_open_video", open_video)
    reader = SimpleNamespace(file_path=tmp_path / "input.raw")
    output = saving.OutputClass(reader, custom_path=tmp_path / "output")
    with pytest.raises(OSError, match="cannot open mp4"):
        output.add("moment0", np.ones((6, 8), np.float32), 0)
    writer.close.assert_called_once()
    assert not output._h5.id.valid
    assert not list(output.target_dir.rglob("*.png"))


@pytest.mark.parametrize("mode", ["legacy", "bundle", "stream", "static"])
@pytest.mark.parametrize("selected", [None, [], "MEAN", ["RATIO", "STD"]])
@pytest.mark.parametrize("compression", [None, 0, 4, 9])
def test_optional_contrast_h5(tmp_path, monkeypatch, mode, selected, compression):
    monkeypatch.setattr(data, "get_git_version", lambda: "test")
    monkeypatch.setattr(media, "save_video", lambda *a, **kw: None)
    monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *a: Mock())
    reader = SimpleNamespace(file_path=tmp_path / "input.raw", extension=".raw")
    parameters = {"h5compression": compression}
    if selected is not None:
        parameters["h5_datasets"] = selected
    frame = np.arange(48, dtype=np.float32).reshape(6, 8)
    outputs = {name: np.stack([frame, frame + 1]) for name in ("MEAN", "RATIO", "STD")}
    outputs["registration"] = np.zeros((2, 2), np.float32)
    if mode in {"stream", "static"}:
        with saving.OutputClass(reader, parameters, custom_path=tmp_path / "out") as dest:
            if mode == "static":
                for name, value in outputs.items():
                    dest.write_static(name, value)
            else:
                for t in range(2):
                    dest.add_batch({name: value[t] for name, value in outputs.items()}, t)
        target = dest.target_dir
    else:
        target = saving.save_outputs(reader, outputs, parameters,
                                     custom_path=tmp_path / "out",
                                     num_saving_workers=0 if mode == "bundle" else None)
    expected = {selected} if isinstance(selected, str) else set(selected or [])
    with h5py.File(next(target.rglob("*.h5"))) as handle:
        for name in ("MEAN", "RATIO", "STD"):
            assert (name in handle) == (name in expected)
            if name in expected:
                np.testing.assert_equal(handle[name][:], outputs[name])
                assert handle[name].compression == (None if compression is None else "gzip")
                assert handle[name].compression_opts == compression
                if mode == "stream":
                    assert handle[name].chunks == (1, *frame.shape)
        assert handle["registration"].compression is None
    assert (target / "png/MEAN.png").exists()


@pytest.mark.parametrize("level", [-1, 10, True, 1.5, "gzip"])
def test_invalid_h5_compression_level(tmp_path, level):
    path = tmp_path / "invalid.h5"
    with pytest.raises((TypeError, ValueError), match="h5compression"):
        data.Hdf5Writer(path, {"h5compression": level})
    assert not path.exists()


def test_default_h5_selection_unchanged():
    parameters = {"pipeline_name": "default", "h5_datasets": []}
    for name in ("moment0", "moment0ff", "moment1", "moment2", "registration"):
        assert policy.save_to_hdf5(name, parameters)


@pytest.mark.parametrize("level", ["omitted", None, 0, 1, 4, 9])
@pytest.mark.parametrize("streaming", [False, True])
def test_default_pipeline_h5_compression(tmp_path, level, streaming):
    parameters = {"pipeline_name": "default"}
    if level != "omitted":
        parameters["h5compression"] = level
    frames = np.arange(2 * 6 * 8, dtype=np.float32).reshape(2, 6, 8)
    average = np.ones((16, 6, 8), dtype=np.float32)
    path = tmp_path / "output.h5"
    with data.Hdf5Writer(path, parameters, git_commit="test") as writer:
        if streaming:
            for t, frame in enumerate(frames):
                writer.append("moment0", frame, t)
        else:
            writer.write_static("moment0", frames)
        writer.write_static("averaged_spectrogram", average)
        writer.write_static("scalar", np.array(3.0))
    compressed = isinstance(level, int) and level > 0
    with h5py.File(path) as handle:
        for name, expected in (("moment0", frames), ("averaged_spectrogram", average)):
            np.testing.assert_array_equal(handle[name][:], expected)
            assert handle[name].compression == ("gzip" if compressed else None)
            assert handle[name].compression_opts == (level if compressed else None)
        if streaming:
            assert handle["moment0"].chunks == (1, 6, 8)
        assert handle["scalar"].compression is None
        assert handle["HD_parameters"].compression is None
