"""Scientific and IO regressions for the surviving pipeline entrypoints."""
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import h5py
import numpy as np
import pytest
import yaml

from holodoppler import backend, saving
from holodoppler.saving import media as saving_media
from holodoppler.core import pipeline
from holodoppler.pipelines import pipelines


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def cpu_backend():
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    yield
    backend.set_backend(previous)


def parameters(name, **changes):
    p = yaml.safe_load((ROOT / "parameters/default_parameters_default.yaml").read_text())
    p.update(pipeline_name=name, force_numpy=True, batch_size=4, batch_stride=4,
             first_frame=0, end_frame=-1, skip_every=None, numpy_num_workers=2,
             shack_hartmann=False, shack_hartmann_autofocus=False,
             image_registration=False, image_registration_with_ecc=False,
             registration_ref_first_frame=0, registration_ref_batch_size=4,
             registration_flatfield_gw=1, pixel_pitch=[1e-6, 1e-6], z=.1,
             sampling_freq=1000, low_freq=0, high_freq=400,
             svd_threshold=0, svd_remove_dc=False, frequency_bands=[],
             save_spectograms=False, save_averaged_spectrogram=False,
             square=False, pca_range=[0, 2], accumulation=2,
             pca_indices=[[0, 2]], overwrite_option="erase")
    p.update(changes)
    return p


def reader_for(tmp_path, frames):
    calls = []
    def read_frames(first_frame, batch_size, skip_every=None):
        calls.append((first_frame, batch_size, skip_every))
        step = skip_every or 1
        result = frames[first_frame:first_frame + batch_size * step:step].copy()
        return result[0] if len(result) == 1 else result
    reader = SimpleNamespace(file_path=tmp_path / "input.raw", extension=".raw",
                             total_frames=len(frames), read_frames=read_frames)
    return reader, calls


def test_registry_and_imports():
    expected = {"default", "lsci", "pca_accumulation", "sliding_shack_hartmann", "split_apertures"}
    assert set(pipelines) == expected | {f"preview_{name}" for name in expected}
    for name in expected:
        module_name = "sliding_shack_hart" if name == "sliding_shack_hartmann" else name
        module = import_module(f"holodoppler.pipelines.main_{module_name}")
        assert callable(module.process) and callable(module.preview)


@pytest.mark.parametrize("name", ["pca_accumulation", "sliding_shack_hartmann", "split_apertures", "lsci"])
@pytest.mark.parametrize("propagation", ["Fresnel", "AngularSpectrum"])
@pytest.mark.parametrize("registration", [False, True])
def test_streamed_and_buffered_outputs_match(tmp_path, monkeypatch, name, propagation, registration):
    frames = np.random.default_rng(123).uniform(10, 100, (17, 8, 10)).astype(np.float32)
    reader, _ = reader_for(tmp_path, frames)
    monkeypatch.setattr(pipeline, "get_reader", lambda _: reader)
    monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *args: Mock())
    monkeypatch.setattr(saving_media, "save_video", lambda *args, **kwargs: None)
    module_name = "sliding_shack_hart" if name == "sliding_shack_hartmann" else name
    module = import_module(f"holodoppler.pipelines.main_{module_name}")
    p = parameters(name, spatial_propagation=propagation, image_registration=registration)
    if name == "lsci":
        p.update(batch_size=3, batch_stride=2, image_registration=False, lsci_resize_factor=1,
                 lsci_enable_spatial=True, lsci_enable_temporal=True,
                 lsci_enable_spatiotemporal=True, lsci_nbh_s=3, lsci_nbh_t=99,
                 lsci_history_dtype="float16")
    snapshots = []
    for live in (True, False):
        progress = []
        module.process(reader.file_path, {**p, "live_saving": live,
                       "numpy_num_workers": 0 if live else 2},
                       progress_callback=lambda *args: progress.append(args))
        paths = list(tmp_path.rglob("*_output.h5"))
        assert len(paths) == 1
        with h5py.File(paths[0]) as handle:
            data = {key: handle[key][()] for key in handle if key not in
                    {"HD_parameters", "HD_version", "git_commit"}}
        assert data
        expected_count = 2 if name == "pca_accumulation" else 5 if name == "lsci" else 4
        assert all(value.shape[0] == expected_count for value in data.values())
        assert all(np.isfinite(value).all() for value in data.values())
        assert progress[-1][:2] == ((5, 5) if name == "lsci" else (4, 4))
        snapshots.append(data)
    assert snapshots[0].keys() == snapshots[1].keys()
    for key in snapshots[0]:
        np.testing.assert_allclose(snapshots[0][key], snapshots[1][key], rtol=1e-5, atol=1e-5)
    preview = module.preview(reader.file_path, p)
    assert preview.ndim == 2


@pytest.mark.parametrize("accumulation,expected", [(1, [0, 1, 2, 3, 4]), (2, [.5, 2.5, 4]), (8, [2])])
def test_pca_means_and_partial_group(tmp_path, monkeypatch, accumulation, expected):
    from holodoppler.pipelines import main_pca_accumulation as pca
    frames = np.arange(5, dtype=np.float32)[:, None, None] * np.ones((5, 3, 4), np.float32)
    reader, _ = reader_for(tmp_path, frames)
    monkeypatch.setattr(pipeline, "get_reader", lambda _: reader)
    monkeypatch.setattr(pca, "_process_one_batch", lambda p, frames, PROJ_reg=None, phase_term=None:
                        ({"PROJ": frames[0], "PROJff": frames[0], "registration": frames[0, 0, :2]}, PROJ_reg))
    saved = []
    monkeypatch.setattr(pipeline, "save_outputs", lambda **kwargs: saved.append(kwargs) or tmp_path)
    p = parameters("pca_accumulation", batch_size=1, batch_stride=1, pca_range=[0, 1],
                   accumulation=accumulation, live_saving=False)
    pca.process(reader.file_path, p)
    result = saved[-1]["output"]
    np.testing.assert_allclose(result["PROJ"][:, 0, 0], expected)
    np.testing.assert_allclose(result["registration"][:, 0], expected)
    assert result["PROJ"].shape == (len(expected), 3, 4)
    assert pca.preview(reader.file_path, p)[0, 0] == pytest.approx(expected[0])
    if accumulation > 1:
        assert saved[0]["parameters"]["output_fps"] == 1000 / accumulation


def test_sliding_history_includes_only_current_window(monkeypatch):
    from holodoppler.pipelines import main_sliding_shack_hart as sliding
    captured = []
    monkeypatch.setattr(sliding, "construct_subapertures_fresnel", lambda xp, fft, frames, *args:
                        np.full((2, 2, 3, 3), frames[0, 0, 0], np.float32))
    def displacements(xp, fft, images, **kwargs):
        captured.append(images.copy())
        return np.zeros((2, 2)), np.zeros((2, 2))
    monkeypatch.setattr(sliding, "calculate_displacements", displacements)
    monkeypatch.setattr(sliding, "_process_batch", lambda p, frames, phase_term, output_dict: None)
    p = parameters("sliding_shack_hartmann", shack_hartmann=True,
                   sh_time_accumulation=2, shack_hartmann_zernike_fit=False,
                   shack_hartmann_graph_laplacian=False)
    history = []
    for value in (1, 2, 3):
        sliding._process_one_batch(p, np.full((4, 8, 10), value), U_buffer=history)
    assert len(history) == 2
    assert [images[0, 0, 0, 0] for images in captured] == [1, 3, 5]


@pytest.mark.parametrize("method", ["Fresnel", "AngularSpectrum"])
def test_quadrants_cover_odd_pupil_and_accept_phase(method):
    from holodoppler.pipelines import main_split_apertures as split
    frames = np.random.default_rng(45).random((4, 7, 9)).astype(np.float32)
    coverage = np.zeros((7, 9), int)
    for ys, xs in split.make_quadrant_indices((7, 9)):
        coverage[slice(*ys), slice(*xs)] += 1
    assert np.all(coverage == 1)
    output = {}
    split._process_batch(parameters("split_apertures", spatial_propagation=method),
                         frames, phase_term=np.ones((7, 9), np.complex64), output_dict=output)
    assert output["M0"].shape == (7, 9)
    assert output["NW_M0"].shape == output["SE_M0"].shape == (4, 5)


def test_skip_and_reference_bounds(tmp_path):
    reader, calls = reader_for(tmp_path, np.ones((12, 3, 4)))
    p = parameters("pca_accumulation", first_frame=1, batch_size=3, batch_stride=3, skip_every=2)
    assert list(pipeline.batch_indices(reader, p)) == [1, 4, 7]
    assert pipeline.read_reference(reader, p, 1, 3, "Registration").shape == (3, 3, 4)
    assert calls[-1] == (1, 3, 2)
    with pytest.raises(ValueError, match="Registration"):
        pipeline.read_reference(reader, p, 9, 3, "Registration")


@pytest.mark.parametrize("skip,expected,starts", [(1, [6, 37.5, 96], [1, 4, 7]), (2, [3.375, 13.5], [1, 4])])
def test_lsci_full_batches_and_forced_window(tmp_path, monkeypatch, skip, expected, starts):
    from holodoppler.pipelines import main_lsci as lsci
    frames = np.arange(10, dtype=np.float32)[:, None, None] * np.ones((10, 3, 4))
    reader, calls = reader_for(tmp_path, frames)
    monkeypatch.setattr(pipeline, "get_reader", lambda _: reader)
    saved = []
    monkeypatch.setattr(pipeline, "save_outputs", lambda **kw: saved.append(kw) or tmp_path)
    p = parameters("lsci", batch_size=3, batch_stride=99, first_frame=1, end_frame=10,
                   skip_every=skip, live_saving=False, lsci_nbh_s=1, lsci_nbh_t=99,
                   lsci_resize_factor=1, lsci_history_dtype="float16",
                   lsci_enable_spatial=False, lsci_enable_temporal=True,
                   lsci_enable_spatiotemporal=False)
    assert lsci.process(reader.file_path, p) == str(tmp_path)
    assert calls == [(start, 3, skip) for start in starts]
    result = saved[0]["output"]["temporal_flow_index"]
    np.testing.assert_allclose(result[:, 0, 0], expected, rtol=1e-5)
    effective = saved[0]["parameters"]
    assert effective["lsci_nbh_t"] == effective["batch_size"] == effective["batch_stride"] == 3
    assert p["batch_stride"] == p["lsci_nbh_t"] == 99
    preview = lsci.preview(reader.file_path, p)
    np.testing.assert_allclose(preview, expected[0], rtol=1e-5)


@pytest.mark.parametrize("name", ["default", "lsci", "pca_accumulation", "sliding_shack_hartmann", "split_apertures"])
@pytest.mark.parametrize("changes,match", [
    ({"live_saving": "yes"}, "live_saving"),
    ({"numpy_num_workers": "two"}, "numpy_num_workers"),
    ({"skip_every": 0}, "skip_every"),
    ({"pixel_pitch": "use_holovibes"}, "pixel_pitch"),
])
def test_all_pipelines_use_main_validation(tmp_path, monkeypatch, name, changes, match):
    reader, _ = reader_for(tmp_path, np.ones((4, 3, 4), np.float32))
    monkeypatch.setattr(pipeline, "get_reader", lambda _: reader)
    with pytest.raises((ValueError, TypeError), match=match):
        pipeline.prepare_input(reader.file_path, parameters(name, **changes))


def test_ui_uses_canonical_presets():
    from holodoppler.ui.paths import parameters_dir
    from holodoppler.ui.settings_store import SettingsStore
    assert parameters_dir() == ROOT / "parameters"
    assert SettingsStore()._default_parameter_sources() == sorted(
        (ROOT / "parameters").glob("*.yaml"), key=lambda path: path.name.lower())


def test_profiles_follow_default_order_and_comments():
    def shared_comments(text):
        return {line.split(":", 1)[0]: line.split("#", 1)[1].strip() if "#" in line else ""
                for line in text.splitlines() if line and not line[0].isspace()
                and not line.startswith("#") and ":" in line}
    default = (ROOT / "parameters/default_parameters_default.yaml").read_text()
    order = list(yaml.safe_load(default))
    comments = shared_comments(default)
    for path in (ROOT / "parameters").glob("*.yaml"):
        text = path.read_text()
        keys = [key for key in yaml.safe_load(text) if key in order]
        assert keys == sorted(keys, key=order.index), path.name
        for key, comment in shared_comments(text).items():
            if key in comments:
                assert comment == comments[key], (path.name, key)


def test_lsci_profile_links_temporal_window_to_batch_size():
    text = (ROOT / "parameters/default_parameters_lsci.yaml").read_text()
    for size in (1, 16, 40):
        p = yaml.safe_load(text.replace("&lsci_batch_size 40", f"&lsci_batch_size {size}"))
        assert p["batch_size"] == p["batch_stride"] == p["lsci_nbh_t"] == size


@pytest.mark.parametrize("failure", ["processing", "saving"])
def test_shared_runner_closes_partial_output_on_failure(tmp_path, monkeypatch, failure):
    reader, _ = reader_for(tmp_path, np.ones((3, 3, 4), np.float32))
    destinations = []
    class Destination(saving.OutputClass):
        def __init__(self, *args, **kwargs):
            self.finalized = None
            super().__init__(*args, **kwargs)
            destinations.append(self)
        def add_batch(self, result, index):
            if index == 1 and failure == "saving":
                raise RuntimeError("saving failed")
            return super().add_batch(result, index)
        def close(self, *, finalize=True):
            self.finalized = finalize
            return super().close(finalize=finalize)
    monkeypatch.setattr(pipeline, "OutputClass", Destination)
    monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *args: Mock())
    completed = 0
    def process_batch(frames, reference):
        nonlocal completed
        if completed == 1 and failure == "processing":
            raise RuntimeError("processing failed")
        completed += 1
        return {"PROJ": frames[0]}, reference
    p = parameters("pca_accumulation", batch_size=1, batch_stride=1, numpy_num_workers=0)
    with pytest.raises(RuntimeError, match=f"{failure} failed"):
        pipeline.run_pipeline(reader, p, process_batch)
    assert destinations[0]._closed
    assert not destinations[0]._h5.id.valid
    assert destinations[0].finalized is False


def test_stateful_processor_ignores_cpu_worker_setting(tmp_path, monkeypatch):
    reader, _ = reader_for(tmp_path, np.arange(5, dtype=np.float32)[:, None, None] * np.ones((5, 3, 4)))
    running_total = 0
    saved = []
    monkeypatch.setattr(pipeline, "save_outputs", lambda **kw: saved.append(kw) or tmp_path)
    def process_batch(frames, reference):
        nonlocal running_total
        running_total += frames[0, 0, 0]
        return {"PROJ": np.full((3, 4), running_total)}, reference
    p = parameters("pca_accumulation", batch_size=1, batch_stride=1,
                   live_saving=False, numpy_num_workers=8)
    pipeline.run_pipeline(reader, p, process_batch, stateful=True)
    np.testing.assert_allclose(saved[0]["output"]["PROJ"][:, 0, 0], [0, 1, 3, 6, 10])


@pytest.mark.parametrize("live", [False, True])
def test_pca_ecc_runs_after_averaging_before_resizing(tmp_path, monkeypatch, live):
    from holodoppler.pipelines import main_pca_accumulation as pca
    frames = np.arange(3, dtype=np.float32)[:, None, None] * np.ones((3, 3, 4))
    reader, _ = reader_for(tmp_path, frames)
    monkeypatch.setattr(pipeline, "get_reader", lambda _: reader)
    monkeypatch.setattr(saving.OutputClass, "_open_video", lambda *args: Mock())
    monkeypatch.setattr(saving_media, "save_video", lambda *args, **kwargs: None)
    monkeypatch.setattr(pca, "_process_one_batch", lambda p, frames, PROJ_reg=None, phase_term=None:
                        ({"PROJ": frames[0], "PROJff": frames[0]}, PROJ_reg))
    def estimate(images, **kwargs):
        assert images.shape == (2, 3, 4)
        np.testing.assert_allclose(images[:, 0, 0], [.5, 2])
        return np.repeat(np.eye(2, 3)[None], 2, axis=0)
    monkeypatch.setattr(pipeline, "register_with_ecc", estimate)
    monkeypatch.setattr(pipeline, "apply_ecc_registration", lambda values, *args, **kwargs: values + 10)
    p = parameters("pca_accumulation", batch_size=1, batch_stride=1, pca_range=[0, 1],
                   accumulation=2, square=True, image_registration_with_ecc=True, live_saving=live)
    pca.process(reader.file_path, p)
    with h5py.File(next(tmp_path.rglob("*_output.h5"))) as handle:
        assert handle["PROJ"].shape == (2, 4, 4)
        np.testing.assert_allclose(handle["PROJ"][:, 0, 0], [10.5, 12])
        assert handle["registration_ecc"].shape == (2, 2, 3)


@pytest.mark.parametrize("name", ["pca_accumulation", "sliding_shack_hart", "split_apertures"])
@pytest.mark.parametrize("method", ["Fresnel", "AngularSpectrum"])
def test_live_wavefront_fitting_on_numpy(name, method, monkeypatch):
    module = import_module(f"holodoppler.pipelines.main_{name}")
    p = parameters("sliding_shack_hartmann" if name == "sliding_shack_hart" else name,
                   shack_hartmann=True, spatial_propagation=method,
                   shack_hartmann_nx_subap=2, shack_hartmann_ny_subap=2,
                   shack_hartmann_svd_threshold=0, shack_hartmann_graph_laplacian=False,
                   shack_hartmann_pupil_threshold=0, shack_hartmann_zernike_fit_modes=[4])
    if name == "sliding_shack_hart":
        monkeypatch.setattr(module, "plot_phase_with_slopes_rgb", lambda *args: np.zeros((4, 5, 3), np.uint8))
    frames = np.random.default_rng(94).uniform(1, 100, (4, 8, 10)).astype(np.float32)
    result, _ = module._process_one_batch(p, frames)
    assert "shack_hartmann_zernike_coefs" in result
    assert result["shack_hartmann_wavefront_phase"].shape == (8, 10)
