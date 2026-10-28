"""Autofocus diagnostics stay separate from resized batch outputs."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
from PIL import Image
import pytest
import yaml

from holodoppler import backend, saving
from holodoppler.saving import data as saving_data
from holodoppler.saving import media as saving_media
from holodoppler.pipelines import main_default


@pytest.mark.parametrize("z4", [1.0, 2.0])
@pytest.mark.parametrize("live_saving", [False, True])
@pytest.mark.parametrize("skip_every", [1, 2])
@pytest.mark.parametrize("entrypoint", ["preview", "process"])
@pytest.mark.parametrize("autofocus", [True, False])
def test_autofocus_png(tmp_path, monkeypatch, entrypoint, autofocus, skip_every, z4, live_saving):
    numpy_backend = backend.BackendManager("numpy")
    for name in ("xp", "fft", "zoom", "is_gpu"):
        monkeypatch.setattr(backend, name, getattr(numpy_backend, name))
    monkeypatch.setattr(backend, "get_backend_name", lambda: "numpy")
    monkeypatch.setattr(backend, "clear_gpu_memory", lambda: None)
    monkeypatch.setattr(backend, "to_backend", np.asarray)
    monkeypatch.setattr(backend, "to_numpy", np.asarray)

    defaults = Path(__file__).resolve().parents[1] / "parameters/default_parameters_default.yaml"
    parameters = yaml.safe_load(defaults.read_text(encoding="utf-8"))
    parameters.update(
        live_saving=live_saving, skip_every=skip_every, batch_size=4, batch_stride=4, first_frame=0, end_frame=-1,
        registration_ref_first_frame=0, shack_hartmann_autofocus_batch_size=4,
        shack_hartmann_autofocus=autofocus, spatial_propagation="Fresnel",
        pixel_pitch=[1e-6, 1e-6], wavelength=852e-9, z=0.1,
        sampling_freq=1000, low_freq=100, high_freq=400,
        image_registration=False, image_registration_with_ecc=False,
        filter2d=False, square=True, backend="auto",
        numpy_num_workers=1,
    )
    frames = np.ones((4, 12, 18), dtype=np.float32)
    reader = SimpleNamespace(
        extension=".raw", total_frames=12, file_path=tmp_path / "input.raw",
        read_frames=Mock(side_effect=lambda **kwargs: frames.copy()),
    )
    monkeypatch.setattr(main_default, "get_reader", lambda path: reader)

    phase = np.arange(12 * 18, dtype=np.float32).reshape(12, 18) / 10
    shifts_y = np.array([[1, np.nan], [0, -1]], dtype=np.float32)
    shifts_x = np.array([[0, np.nan], [1, -1]], dtype=np.float32)
    coefs = np.array([z4, 2, 3], dtype=np.float32)
    monkeypatch.setattr(
        main_default, "construct_subapertures_fresnel",
        lambda *args, **kwargs: np.ones((2, 2, 12, 18), dtype=np.float32),
    )
    pair_shifts = np.stack((shifts_y, shifts_x), axis=-1)
    pair_shifts = (pair_shifts[None, None, :, :, :] - pair_shifts[:, :, None, None, :]).astype(np.float32)

    def displacements(*args, diagnostics=None, **kwargs):
        if diagnostics is not None:
            diagnostics["shack_hartmann_shifts"] = pair_shifts.copy()
        return shifts_y, shifts_x

    monkeypatch.setattr(main_default, "calculate_displacements_graph_laplacian", displacements)
    monkeypatch.setattr(
        main_default, "fit_zernike_fresnel", lambda *args: (coefs, phase),
    )
    render = Mock(wraps=main_default.plot_phase_with_slopes_rgb)
    monkeypatch.setattr(main_default, "plot_phase_with_slopes_rgb", render)

    corrections = []

    def process_batch(parameters, frames, registration_ref=None, phase_term=None, **kwargs):
        corrections.append(phase_term)
        return {key: frames[0].copy() for key in ("moment0", "moment0ff", "moment1", "moment2")}, None

    monkeypatch.setattr(main_default, "_process_one_batch", process_batch)
    bundles = []
    monkeypatch.setattr(saving_data, "save_metadata", lambda *args, **kwargs: None)
    monkeypatch.setattr(saving_data, "save_version_files", lambda *args: None)
    monkeypatch.setattr(saving_data, "get_git_version", lambda: "test")
    video_writer = Mock()
    monkeypatch.setattr(saving_media, "save_video", video_writer)

    def save_bundle(**kwargs):
        bundles.append(kwargs["output"])
        assert not list(tmp_path.rglob("*.png"))
        target = tmp_path / kwargs.get("custom_relative_path", "")
        return saving.save_outputs(
            file_reader=kwargs["file_reader"], output=kwargs["output"],
            parameters=kwargs["parameters"], custom_path=target,
        )

    monkeypatch.setattr(main_default, "save_outputs", save_bundle)
    # Process streams through OutputClass; preview still saves a complete bundle.
    if entrypoint == "process":
        class RecordingOutput(saving.OutputClass):
            def __init__(self, file_reader, parameters):
                super().__init__(file_reader, parameters, custom_path=tmp_path)
                bundles.append({})

            def write_static(self, name, value):
                bundles[0][name] = value
                super().write_static(name, value)

        monkeypatch.setattr(main_default, "OutputClass", RecordingOutput)
        monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *args: Mock())
    getattr(main_default, entrypoint)("input.raw", parameters)

    assert len(corrections) == (1 if entrypoint == "preview" else (3 if skip_every == 1 else 2))
    assert all(call.kwargs["skip_every"] == skip_every for call in reader.read_frames.call_args_list)
    plot_key = "shack_hartmann_autofocus_wavefront_color_image"
    pngs = list(tmp_path.rglob(f"{plot_key}.png"))
    assert all(plot_key not in str(call.args[0]) for call in video_writer.call_args_list)
    if autofocus:
        render.assert_called_once()
        for actual, expected in zip(render.call_args.args, (phase, shifts_y, shifts_x)):
            np.testing.assert_equal(actual, expected)
        for correction in corrections:
            if z4 > 1.5:
                assert correction is None
            else:
                np.testing.assert_allclose(correction, np.exp(-1j * phase))
        np.testing.assert_array_equal(
            bundles[0]["shack_hartmann_autofocus_zernike_coefs"], coefs,
        )
        np.testing.assert_equal(bundles[0]["shack_hartmann_autofocus_shifts"], pair_shifts)
        import h5py
        with h5py.File(next(tmp_path.rglob("*.h5"))) as h5:
            np.testing.assert_equal(h5["shack_hartmann_autofocus_shifts"][:], pair_shifts)
        assert len(pngs) == 1
        assert pngs[0].name == "shack_hartmann_autofocus_wavefront_color_image.png"
        assert ("preview" in pngs[0].relative_to(tmp_path).parts) == (entrypoint == "preview")
        with Image.open(pngs[0]) as image:
            assert image.mode == "RGB"
            assert image.size == (2400, 2400)
    else:
        render.assert_not_called()
        assert corrections == [None] * len(corrections)
        assert plot_key not in bundles[0]
        assert not pngs


@pytest.mark.parametrize("shape, expected", [
    ((12, 18), False), ((12, 18, 3), False), ((12, 18, 4), False),
    ((5, 12, 18), True), ((5, 12, 18, 3), True),
])
def test_still_images_are_not_encoded_as_videos(shape, expected):
    assert saving.is_video(np.zeros(shape, dtype=np.uint8)) == expected


def test_skipped_batch_bounds():
    from holodoppler.core.batching import calculate_batch_indices

    assert list(calculate_batch_indices(0, -1, 4, 4, 12, skip_every=2)) == [0, 4]
    assert list(calculate_batch_indices(0, 6, 4, 4, 12, skip_every=2)) == []
