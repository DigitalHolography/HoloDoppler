"""Temporal smoothing is confined to encoded video, including streaming tails."""
from types import SimpleNamespace
from unittest.mock import Mock

import h5py
import numpy as np
import pytest
from PIL import Image
from scipy.ndimage import gaussian_filter1d

from holodoppler.saving import media, session
from holodoppler.saving.default_output import DefaultOutput


def reference(frames, sigma):
    return np.rint(gaussian_filter1d(frames, sigma, axis=0, mode="nearest",
                                   output=np.float64)).clip(0, 255).astype(np.uint8)


@pytest.mark.parametrize("count", [1, 2, 17])
@pytest.mark.parametrize("sigma", [0, 0.1, 0.7, 2])
def test_stream_filter_edges_and_bounded_storage(count, sigma):
    frames = np.random.default_rng(7).integers(0, 256, (count, 6, 8, 3), dtype=np.uint8)
    temporal = media._TemporalGaussian(sigma)
    actual = []
    for frame in frames:
        actual.extend(temporal.append(frame))
        assert len(temporal.frames) <= 2 * temporal.radius + 1
    actual.extend(temporal.finish())
    np.testing.assert_array_equal(actual, reference(frames, sigma) if sigma else frames)


@pytest.mark.parametrize("output_class", [session.OutputClass, DefaultOutput])
@pytest.mark.parametrize("workers", [0, 2])
@pytest.mark.parametrize("color", [False, True])
def test_stream_video_blur_preserves_h5_and_png(tmp_path, monkeypatch, output_class, workers, color):
    name = "color_Doppler_image" if color and output_class is DefaultOutput else "moment0"
    frames = np.random.default_rng(3).integers(
        0, 256, (11, 6, 8, 3) if color else (11, 6, 8), dtype=np.uint8)
    original = frames.copy()
    results = []
    for sigma in (0, 1):
        writers = {fmt: Mock() for fmt in ("avi", "mp4")}
        monkeypatch.setattr(output_class, "_open_video", lambda self, name, fmt: writers[fmt])
        p = {"video_temporal_sigma": sigma, "num_saving_workers": workers,
             "outputs": {name: ["h5", "avi", "mp4"],
                         name + "_time_projection": ["png"]}}
        with output_class(SimpleNamespace(file_path=tmp_path / "input.raw"), p,
                          custom_path=tmp_path / str(sigma)) as out:
            for t, frame in enumerate(frames):
                out.add(name, frame, t)
        with h5py.File(next(out.target_dir.glob("h5/*.h5"))) as h5:
            np.testing.assert_array_equal(h5[name], original)
        png = next(out.target_dir.glob("png/*.png"))
        with Image.open(png) as image:
            average = np.array(image)
        encoded = {fmt: np.stack([call.args[0] for call in writer.append_data.call_args_list])
                   for fmt, writer in writers.items()}
        results.append((encoded, average))
        for writer in writers.values():
            writer.close.assert_called_once()
    for fmt in ("avi", "mp4"):
        np.testing.assert_array_equal(results[1][0][fmt], reference(results[0][0][fmt], 1))
    np.testing.assert_array_equal(results[0][1], results[1][1])
    np.testing.assert_array_equal(frames, original)


@pytest.mark.parametrize("workers", [None, 0, 2])
def test_buffered_video_blur_preserves_h5(tmp_path, monkeypatch, workers):
    frames = np.random.default_rng(9).random((7, 6, 8)).astype(np.float32)
    original = frames.copy()
    encoded = {}
    monkeypatch.setattr(media, "save_video_imageio",
                        lambda path, data, fps, codec: encoded.setdefault(path.suffix, data.copy()))
    target = session.save_outputs(SimpleNamespace(file_path=tmp_path / "input.raw"),
        {"moment0": frames}, {"video_temporal_sigma": 1},
        custom_path=tmp_path / "output", num_saving_workers=workers)
    expected = reference(media.video_to_uint8(original), 1)
    for fmt in (".avi", ".mp4"):
        np.testing.assert_array_equal(encoded[fmt], expected)
    with h5py.File(next(target.glob("h5/*.h5"))) as h5:
        np.testing.assert_array_equal(h5["moment0"], original)
    np.testing.assert_array_equal(frames, original)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, None, "1"])
def test_invalid_sigma(value):
    from holodoppler.config import validate_main_parameters

    with pytest.raises((TypeError, ValueError), match="video_temporal_sigma"):
        validate_main_parameters({"video_temporal_sigma": value})


def test_abort_discards_pending_frames(tmp_path):
    writer = Mock()
    stream = media.MediaStream(tmp_path, "moment0", lambda fmt: writer,
                               formats=("avi",), video_temporal_sigma=1)
    stream.append(np.zeros((6, 8), np.uint8))
    stream.close(finalize=False)
    writer.append_data.assert_not_called()
    writer.close.assert_called_once()
    assert not stream.temporal_filter.frames

