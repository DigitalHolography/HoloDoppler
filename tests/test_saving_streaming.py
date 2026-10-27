"""Streaming output contracts and a real bundled-FFmpeg round trip."""
from types import SimpleNamespace
from unittest.mock import Mock

import h5py
import numpy as np
from PIL import Image
import pytest

from holodoppler.core import pipeline as lifecycle
from holodoppler import saving
from holodoppler.saving import data as saving_data
from holodoppler.saving import media as saving_media
from holodoppler.saving import session as saving_session
from holodoppler.pipelines import main_default


@pytest.fixture
def output_factory(tmp_path, monkeypatch):
    monkeypatch.setattr(saving_data, "save_metadata", lambda *args: None)
    monkeypatch.setattr(saving_data, "get_git_version", lambda: "test")
    reader = SimpleNamespace(file_path=tmp_path / "input.raw")

    def create(**kwargs):
        return saving.OutputClass(reader, custom_path=tmp_path / "output", **kwargs)

    return create


def test_append_formats_and_fixed_range(output_factory, monkeypatch):
    videos = {}

    def open_video(self, name, fmt):
        writer = Mock()
        videos[name, fmt] = writer
        return writer

    monkeypatch.setattr(saving.OutputClass, "_open_video", open_video)
    first = np.linspace(10, 20, 35, dtype=np.float32).reshape(5, 7)
    with output_factory() as output:
        output.add("moment0", first, 0)
        output.add("moment0", first + 10, 1)
        output.add("registration", np.array([1., 2.]), 0)
        output.add("registration", np.array([3., 4.]), 1)
        output.add("spectrograms", np.ones((8, 5, 7), np.float32), 0)
        output.write_static("shack_hartmann_autofocus_zernike_coefs", np.array([4., 5.]))
        output.write_static("diagnostic", np.zeros((5, 7, 3), np.uint8))
        # HDF5 receives data during add, before the writer is closed.
        np.testing.assert_equal(output._h5["moment0"][:], [first, first + 10])
    output.close()
    for fmt in ("avi", "mp4"):
        writer = videos["moment0", fmt]
        assert writer.append_data.call_count == 2
        frame0, frame1 = [call.args[0] for call in writer.append_data.call_args_list]
        assert frame0.shape == (6, 8, 3)
        assert frame0[0, 0, 0] == 0
        assert frame0[4, 6, 0] == 255
        assert np.all(frame1[:5, :7] == 255)
        writer.close.assert_called_once()
    assert set(videos) == {("moment0", "avi"), ("moment0", "mp4")}
    with h5py.File(output.target_dir / "h5/output_output.h5") as h5:
        assert h5["moment0"].shape == (2, 5, 7)
        assert h5["spectrograms"].shape == (1, 8, 5, 7)
        assert h5["shack_hartmann_autofocus_zernike_coefs"].shape == (2,)
        assert h5["git_commit"][()] == b"test"
        assert "HD_parameters" in h5 and "HD_version" in h5
    assert (output.target_dir / "csv/registration.csv").read_text().splitlines() == [
        "1.0,2.0", "3.0,4.0"]
    with Image.open(output.target_dir / "png/moment0.png") as image:
        np.testing.assert_equal(np.array(image), saving.cast_png_data(first + 5))


@pytest.mark.parametrize("option", ["overwrite", "erase", "archive_old"])
def test_overwrite_options(output_factory, tmp_path, option):
    target = tmp_path / "output"
    target.mkdir()
    (target / "old.txt").write_text("old")
    archive = tmp_path / "archive/output"
    archive.mkdir(parents=True)
    with output_factory(parameters={"overwrite_option": option}) as output:
        assert all((output.target_dir / name).is_dir() for name in
                   ("avi", "mp4", "h5", "png", "json", "yaml", "csv"))
    assert (target / "old.txt").exists() == (option == "overwrite")
    if option == "archive_old":
        assert (tmp_path / "archive/output (#1)/old.txt").read_text() == "old"


def test_invalid_option_before_creating_destination(output_factory, tmp_path):
    with pytest.raises(ValueError, match="overwrite_option"):
        output_factory(parameters={"overwrite_option": "invalid"})
    assert not (tmp_path / "output").exists()


def test_directory_access_probe(output_factory, monkeypatch):
    monkeypatch.setattr(saving_session.tempfile, "TemporaryFile", Mock(side_effect=PermissionError("locked")))
    with pytest.raises(PermissionError, match="locked"):
        output_factory()


@pytest.mark.parametrize("option", ["overwrite", "erase", "archive_old"])
def test_target_is_file(output_factory, tmp_path, option):
    target = tmp_path / "output"
    target.write_text("old")
    if option == "overwrite":
        with pytest.raises(OSError):
            output_factory(parameters={"overwrite_option": option})
    else:
        with output_factory(parameters={"overwrite_option": option}):
            assert target.is_dir()


def test_invalid_add_is_rejected_before_writing(output_factory):
    with output_factory() as output:
        output.add("spectrum_line", np.ones(8, np.float32), 0)
        for value, t in [(np.ones(8, np.float32), 0),
                         (np.ones(8, np.float32), 2),
                         (np.ones(9, np.float32), 1),
                         (np.ones(8, np.float64), 1)]:
            with pytest.raises(ValueError):
                output.add("spectrum_line", value, t)
            assert output._h5["spectrum_line"].shape == (1, 8)
        with pytest.raises(ValueError):
            output.add("../escape", np.ones(8), 0)
    with pytest.raises(RuntimeError, match="closed"):
        output.add("spectrum_line", np.ones(8), 1)


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.float32])
def test_integer_and_nonfinite_normalization(output_factory, monkeypatch, dtype):
    writer = Mock()
    monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *args: writer)
    value = np.zeros((6, 8), dtype=dtype)
    if dtype == np.float32:
        value[0, :3] = [np.nan, np.inf, -np.inf]
    else:
        value[0, 0] = np.iinfo(dtype).max
    with output_factory() as output:
        output.add("moment0", value, 0)
        frame = writer.append_data.call_args.args[0]
        assert frame.dtype == np.uint8
        assert np.isfinite(frame).all()
        assert frame[0, 0, 0] == (0 if dtype == np.float32 else 255)
        np.testing.assert_equal(output._h5["moment0"][0], value)


def test_encoder_failure_releases_resources(output_factory, monkeypatch):
    avi, mp4 = Mock(), Mock()
    mp4.append_data.side_effect = OSError("encoding failed")
    monkeypatch.setattr(saving.OutputClass, "_open_video",
                        lambda self, name, fmt: avi if fmt == "avi" else mp4)
    output = output_factory()
    with pytest.raises(OSError, match="encoding failed"):
        output.add("moment0", np.ones((6, 8), np.float32), 0)
    avi.close.assert_called_once()
    mp4.close.assert_called_once()
    assert not output._h5.id.valid
    output.close()


def test_h5_failure_releases_open_encoders(output_factory, monkeypatch):
    writers = []

    def open_video(*args):
        writer = Mock()
        writers.append(writer)
        return writer

    monkeypatch.setattr(saving.OutputClass, "_open_video", open_video)
    output = output_factory()
    output.add("moment0", np.ones((6, 8), np.float32), 0)
    monkeypatch.setattr(h5py.Dataset, "resize", Mock(side_effect=OSError("disk full")))
    with pytest.raises(OSError, match="disk full"):
        output.add("moment0", np.ones((6, 8), np.float32), 1)
    assert not output._h5.id.valid
    assert all(writer.close.call_count == 1 for writer in writers)


def test_real_encoder_round_trip(output_factory):
    import imageio.v2 as imageio

    with output_factory() as output:
        for t in range(3):
            frame = np.arange(17 * 19, dtype=np.float32).reshape(17, 19) + t
            output.add("moment0", frame, t)
    for fmt in ("avi", "mp4"):
        with imageio.get_reader(str(output.target_dir / fmt / f"moment0.{fmt}")) as reader:
            frames = list(reader.iter_data())
        assert len(frames) == 3
        assert frames[0].shape == (18, 20, 3)


@pytest.mark.parametrize("ecc", [False, True])
@pytest.mark.parametrize("gpu", [False, True])
def test_pipeline_streaming_and_ecc_order(tmp_path, monkeypatch, ecc, gpu):
    from holodoppler import backend

    monkeypatch.setattr(backend, "is_gpu", gpu)
    monkeypatch.setattr(backend, "to_numpy", np.asarray)
    monkeypatch.setattr(backend, "clear_gpu_memory", lambda: None)
    monkeypatch.setattr(main_default, "_get_autofocus_phase_term", lambda *args, **kw: (None, None))
    destination = Mock()
    calls = []
    destination.add.side_effect = lambda name, value, t: calls.append((name, value.copy(), t))
    destination.add_batch.side_effect = lambda outputs, t: [
        destination.add(name, value, t) for name, value in outputs.items()]

    def batches(reader, indices, batch_size, process, consume, **kwargs):
        for t in range(2):
            result = {name: np.full((6, 8), t, np.float32)
                      for name in ("moment0", "moment0ff", "moment1", "moment2")}
            result["sh_psd"] = np.full((8, 6, 8), 1 + 2 * t, np.float32)
            if gpu:
                result = kwargs["prepare_result"](result)
                assert "sh_psd" not in result
                assert "averaged_spectrogram" not in result
            consume(t, result)
            assert len(calls) == (0 if ecc else 4 * (t + 1))

    monkeypatch.setattr(lifecycle, "run_batches", batches)
    monkeypatch.setattr(lifecycle, "register_with_ecc", lambda *args, **kw: np.zeros((2, 2, 3)))
    monkeypatch.setattr(lifecycle, "apply_ecc_registration", lambda value, *args, **kw: value + 10)
    main_default._process_to_output(None, dict(batch_size=4, first_frame=0,
        image_registration=False, image_registration_with_ecc=ecc,
        save_averaged_spectrogram=True),
        [0, 4], destination, None)
    moments = [call for call in calls if call[0] == "moment0"]
    assert [call[2] for call in moments] == [0, 1]
    np.testing.assert_equal(moments[0][1], np.full((6, 8), 10 if ecc else 0))
    aggregate = destination.write_static.call_args_list[0]
    assert aggregate.args[0] == "averaged_spectrogram"
    np.testing.assert_equal(aggregate.args[1], np.full((8, 6, 8), 2))


@pytest.mark.parametrize("ecc", [False, True])
@pytest.mark.parametrize("live_saving", [True, False, None])
@pytest.mark.parametrize("workers", [0, 2])
def test_default_process_h5_with_square_and_spectrograms(tmp_path, monkeypatch, ecc, live_saving, workers):
    from holodoppler import backend
    import yaml
    from pathlib import Path

    # Run actual batch processing and HDF5 saving; video encoding has its own round trip.
    monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *args: Mock())
    monkeypatch.setattr(saving_media, "save_video", lambda *args, **kwargs: None)
    streaming_output = Mock(wraps=saving.OutputClass)
    bundle_output = Mock(wraps=saving.save_outputs)
    monkeypatch.setattr(lifecycle, "OutputClass", streaming_output)
    monkeypatch.setattr(lifecycle, "save_outputs", bundle_output)
    frames = np.random.default_rng(11).random((16, 12, 18)).astype(np.float32)
    reader = SimpleNamespace(file_path=tmp_path / "input.raw", extension=".raw",
        total_frames=16, read_frames=lambda first_frame, batch_size, skip_every=None:
        frames[first_frame:first_frame + batch_size * (skip_every or 1):skip_every or 1].copy())
    monkeypatch.setattr(lifecycle, "get_reader", lambda path: reader)
    params = yaml.safe_load((Path(__file__).resolve().parents[1] /
        "parameters/default_parameters_default.yaml").read_text())
    params.update(backend="numpy", batch_size=8, batch_stride=8, first_frame=0,
        end_frame=-1, numpy_num_workers=1, shack_hartmann_autofocus=False,
        shack_hartmann=False, image_registration=True, registration_ref_first_frame=0,
        registration_ref_batch_size=8, image_registration_with_ecc=ecc,
        pixel_pitch=(1e-6, 1e-6), z=0.1, sampling_freq=1000,
        low_freq=0, high_freq=400, svd_threshold=1, registration_flatfield_gw=1,
        frequency_bands=[[0, 400]], spectrogram_resize_shape=[6, 8],
        spectrogram_frequency_binning=2, square=True, num_saving_workers=workers)
    if live_saving is None:
        params.pop("live_saving", None)
    else:
        params["live_saving"] = live_saving
    # Test the buffering/correction path without depending on ECC convergence for noise.
    monkeypatch.setattr(lifecycle, "register_with_ecc", lambda *args, **kwargs:
                        np.repeat(np.eye(2, 3)[None], 2, axis=0))
    monkeypatch.setattr(lifecycle, "apply_ecc_registration", lambda value, *args, **kwargs: value)
    main_default.process(reader.file_path, params)
    assert streaming_output.call_count == (0 if live_saving is False else 1)
    assert bundle_output.call_count == (1 if live_saving is False else 0)
    if live_saving is False:
        assert bundle_output.call_args.kwargs["num_saving_workers"] == workers
    target = saving.get_default_output_path(reader.file_path)
    with h5py.File(target / "h5" / f"{target.name}_output.h5") as h5:
        assert h5["moment0"].shape == (2, 18, 18)
        assert h5["spectrograms"].shape == (2, 4, 6, 8)
        assert h5["averaged_spectrogram"].shape == (8, 18, 18)
        assert h5["registration"].shape == (2, 2)
        assert np.isfinite(h5["moment0"][:]).all()
    backend.set_backend("numpy")


def test_nonlive_saving_happens_after_all_batches(monkeypatch):
    from holodoppler import backend

    monkeypatch.setattr(backend, "to_numpy", np.asarray)
    monkeypatch.setattr(backend, "clear_gpu_memory", lambda: None)
    monkeypatch.setattr(main_default, "_get_autofocus_phase_term", lambda *args, **kwargs: (None, None))
    save = Mock()
    monkeypatch.setattr(lifecycle, "save_outputs", save)

    def batches(reader, indices, batch_size, process, consume, **kwargs):
        for t in range(2):
            consume(t, {"moment0": np.full((6, 8), t, np.float32)})
            save.assert_not_called()

    monkeypatch.setattr(lifecycle, "run_batches", batches)
    main_default._process_to_output(None, dict(batch_size=4, first_frame=0,
        live_saving=False, image_registration=False), [0, 4], None, None)
    save.assert_called_once()
    np.testing.assert_equal(save.call_args.kwargs["output"]["moment0"],
                            np.stack([np.zeros((6, 8)), np.ones((6, 8))]))


@pytest.mark.parametrize("value", ["false", "true", 0, 1, None])
def test_live_saving_requires_boolean(value):
    from holodoppler.config import validate_main_parameters

    with pytest.raises(TypeError, match="live_saving.*boolean"):
        validate_main_parameters({"live_saving": value})
