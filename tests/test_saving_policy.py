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
    ("averaged_spectrogram", (6, 8), {"h5", "png"}, {"h5", "avi", "mp4", "png"}),
    ("NW_moment0", (6, 8), {"h5", "png"}, {"h5", "avi", "mp4", "png"}),
    ("spatial_flow_index", (6, 8), {"h5", "png"}, {"h5", "avi", "mp4", "png"}),
    ("band_0", (6, 8), {"h5", "png"}, {"h5", "avi", "mp4", "png"}),
    ("registration", (2, 3), {"h5", "csv"}, {"h5", "csv"}),
    ("shack_hartmann_zernike_coefs", (3,), {"h5", "csv"}, {"h5", "csv"}),
    ("shack_hartmann_shifts", (2, 3, 2), {"h5", "csv"}, {"h5", "csv"}),
    ("autofocus_shack_hartmann_shifts", (2, 3, 2, 3, 2), {"h5", "csv"}, {"h5", "csv"}),
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
            destination.write_static("autofocus_shack_hartmann_shifts", reference)
        target = destination.target_dir
    else:
        target = saving.save_outputs(
            reader, dict(temporal, autofocus_shack_hartmann_shifts=reference),
            parameters, custom_path=tmp_path / "output", num_saving_workers=workers)
    with h5py.File(next(target.rglob("*.h5"))) as handle:
        assert "color_Doppler_image" not in handle
        assert "directional_Doppler_image" not in handle
        np.testing.assert_equal(handle["moment0"][:], moment)
        np.testing.assert_equal(handle["shack_hartmann_shifts"][:], shifts)
        np.testing.assert_equal(handle["autofocus_shack_hartmann_shifts"][:], reference)
        assert handle["HD_version"][()] == f"py{get_version()}".encode()
        assert handle["git_commit"][()] == b"test"
    for name, value in (("shack_hartmann_shifts", shifts), ("autofocus_shack_hartmann_shifts", reference)):
        np.testing.assert_equal(np.loadtxt(target / "csv" / f"{name}.csv", delimiter=",").reshape(value.shape), value)
        assert not (target / "png" / f"{name}.png").exists()
    for name in ("color_Doppler_image", "directional_Doppler_image"):
        with Image.open(target / "png" / f"{name}.png") as image:
            np.testing.assert_equal(np.asarray(image), np.full((6, 8, 3), 64, dtype=np.uint8))


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
