import json
import inspect
from pathlib import Path
import queue
import threading

import h5py
import numpy as np

from holodoppler import cli
from holodoppler.pipelines.main_spectral_cube import _create_h5
from holodoppler.saving import (
    H5_OUTPUT_PATH_PARAMETER,
    _save_h5_2,
)
from holodoppler.ui.settings_store import _with_spectral_cube_defaults
from holodoppler.ui import app as ui_app
from holodoppler.ui.advanced import AdvancedView
from holodoppler.ui.minimal import MinimalView
from holodoppler.utils import load_config


class _SpectralReader:
    frame_shape = (8, 10)
    file_path = Path("recording.holo")


def test_lazy_pipeline_registry_accepts_warning_callbacks():
    signature = inspect.signature(cli.pipelines["spectral_cube"])

    assert "warning_callback" in signature.parameters


def test_primary_h5_name_has_no_output_suffix(tmp_path):
    target_dir = tmp_path / "recording_HD"
    (target_dir / "h5").mkdir(parents=True)
    parameters = {"pipeline_name": "simple"}

    _save_h5_2(
        target_dir,
        {"M0": np.ones((1, 2, 2), dtype=np.float64)},
        parameters,
    )

    expected = target_dir / "h5" / "recording_HD.h5"
    assert expected.is_file()
    assert not (target_dir / "h5" / "recording_HD_output.h5").exists()
    assert parameters[H5_OUTPUT_PATH_PARAMETER] == str(expected)
    with h5py.File(expected, "r") as handle:
        assert handle["moment0"].dtype == np.float32
        saved_parameters = handle["HD_parameters"][()].decode()
        assert H5_OUTPUT_PATH_PARAMETER not in saved_parameters


def test_spectral_h5_is_appended_below_spectrograms(tmp_path):
    path = tmp_path / "recording_HD.h5"
    with h5py.File(path, "w") as handle:
        handle.create_dataset("moment0", data=np.ones((1, 2, 2)))

    parameters = {
        "pipeline_name": "simple",
        "sampling_freq": 1_000.0,
        "batch_size": 4,
        "f_bins": 2,
        "svd_threshold": 39,
        "spectral_cube_enabled": True,
        "spectral_cube_settings": {"f_bins": 2},
        "spectral_endpoints_phase_bins": 16,
    }
    handle, spectrograms, *_datasets = _create_h5(
        path,
        _SpectralReader(),
        parameters,
        np.array([0, 4], dtype=np.int64),
    )
    assert spectrograms.name == "/spectrograms"
    handle.close()

    with h5py.File(path, "r") as handle:
        assert "moment0" in handle
        assert "spectrograms/longtimes" in handle
        assert "spectrograms/longtimes/S" in handle
        assert "spectrograms/longtimes/S0" in handle
        assert "spectrograms/longtimes/L" in handle
        assert "longtimes" not in handle
        assert "spectrograms/HD_parameters" not in handle
        assert "spectrograms/HD_version" not in handle
        assert "spectrograms/spectral_cube_parameters" in handle
        spectral_parameters = json.loads(
            handle["spectrograms/spectral_cube_parameters"][()].decode()
        )
        assert spectral_parameters == {
            "sampling_freq": 1_000.0,
            "batch_size": 4,
            "f_bins": 2,
            "spectral_endpoints_phase_bins": 16,
        }


def test_process_runs_spectral_cube_by_default_with_independent_settings(
    monkeypatch, tmp_path
):
    calls = []
    progress = []
    h5_path = tmp_path / "recording_HD.h5"

    def primary(file_path, parameters, progress_callback=None):
        calls.append(("primary", file_path, dict(parameters)))
        parameters[H5_OUTPUT_PATH_PARAMETER] = str(h5_path)
        progress_callback(1, 2, "Batch 1/2")
        return {"M0": np.ones((1, 2, 2))}

    def spectral(
        file_path,
        parameters,
        progress_callback=None,
        warning_callback=None,
    ):
        calls.append(("spectral", file_path, dict(parameters)))
        progress_callback(1, 2, "Spectral window 1/2")
        warning_callback("cardiac_pulse_not_detected", "No pulse")
        return h5_path

    monkeypatch.setitem(cli.pipelines, "test_primary", primary)
    monkeypatch.setitem(cli.pipelines, "spectral_cube", spectral)
    parameters = {
        "pipeline_name": "test_primary",
        "batch_size": 1_024,
        "sampling_freq": 50_000.0,
        "spectral_cube_settings": {"batch_size": 128, "f_bins": 64},
    }

    warnings = []
    result = cli.process(
        "recording.holo",
        parameters,
        progress_callback=lambda completed, total, message: progress.append(
            (completed, total, message)
        ),
        warning_callback=lambda code, message: warnings.append((code, message)),
    )

    assert list(result) == ["M0"]
    assert [call[0] for call in calls] == ["primary", "spectral"]
    spectral_parameters = calls[1][2]
    assert spectral_parameters["pipeline_name"] == "spectral_cube"
    assert spectral_parameters["batch_size"] == 128
    assert spectral_parameters["batch_stride"] == 256
    assert spectral_parameters["f_bins"] == 64
    assert spectral_parameters["sampling_freq"] == 50_000.0
    assert spectral_parameters[H5_OUTPUT_PATH_PARAMETER] == str(h5_path)
    assert progress == [
        (1, 2, "Primary pipeline: Batch 1/2"),
        (1, 2, "Spectral cube: Spectral window 1/2"),
    ]
    assert warnings == [("cardiac_pulse_not_detected", "No pulse")]


class _ProgressValue:
    def __init__(self):
        self.value = None

    def configure(self, *, value):
        self.value = value

    def set(self, value):
        self.value = value


def test_ui_file_progress_displays_pipeline_message():
    for view_type in (MinimalView, AdvancedView):
        view = view_type.__new__(view_type)
        view.current_file_name = "recording.holo"
        view.file_progress = _ProgressValue()
        view.file_progress_var = _ProgressValue()

        view.set_file_progress(1, 2, "Spectral cube: Spectral window 1/2")

        assert view.file_progress.value == 50
        assert view.file_progress_var.value == (
            "recording.holo: Spectral cube: Spectral window 1/2"
        )


def test_process_can_explicitly_disable_default_spectral_cube(monkeypatch):
    calls = []

    def primary(file_path, parameters):
        calls.append("primary")
        return {}

    def spectral(file_path, parameters):
        calls.append("spectral")

    monkeypatch.setitem(cli.pipelines, "test_primary", primary)
    monkeypatch.setitem(cli.pipelines, "spectral_cube", spectral)

    cli.process(
        "recording.holo",
        {"pipeline_name": "test_primary", "spectral_cube_enabled": False},
    )

    assert calls == ["primary"]


def test_ui_adds_spectral_controls_to_existing_main_profiles():
    parameters = _with_spectral_cube_defaults({"pipeline_name": "simple"})

    assert parameters["spectral_cube_enabled"] is True
    assert parameters["spectral_cube_settings"] == {}


def test_simple_preset_enables_spectral_cube_by_default():
    parameters = load_config(
        Path(__file__).parents[1] / "parameters" / "default_parameters_simple.yaml"
    )

    assert parameters["pipeline_name"] == "simple"
    assert parameters["spectral_cube_enabled"] is True


def test_ui_batch_continues_and_summarizes_files_without_a_pulse(monkeypatch):
    paths = [Path("first.holo"), Path("second.holo")]
    processed = []

    def fake_process(
        file_path,
        parameters,
        progress_callback=None,
        warning_callback=None,
    ):
        processed.append(Path(file_path))
        if Path(file_path).name == "first.holo":
            warning_callback("cardiac_pulse_not_detected", "No pulse")
        return {}

    class Worker:
        events = queue.Queue()
        stop_event = threading.Event()

        @staticmethod
        def _first_m0_frame(_results):
            return None

    monkeypatch.setattr(ui_app, "process", fake_process)
    worker = Worker()

    ui_app.UI._process_worker(worker, paths, {"pipeline_name": "simple"})
    events = []
    while not worker.events.empty():
        events.append(worker.events.get_nowait())

    assert processed == paths
    progress_events = [event for event in events if event["kind"] == "batch_progress"]
    assert progress_events[0]["pulse_not_detected"] is True
    assert progress_events[1]["pulse_not_detected"] is False
    summary = next(
        event for event in events if event["kind"] == "pulse_detection_summary"
    )
    assert summary["paths"] == [paths[0]]

    class Minimal:
        def set_batch_progress(self, _completed, _total):
            return None

    class Advanced:
        completed = []
        pulse_not_detected = []

        def set_file_completed(self, index):
            self.completed.append(index)

        def set_file_pulse_not_detected(self, index):
            self.pulse_not_detected.append(index)

        def set_batch_progress(self, _completed, _total):
            return None

    class Handler:
        minimal = Minimal()
        advanced = Advanced()
        statuses = []

        def _set_status(self, message):
            self.statuses.append(message)

    handler = Handler()
    ui_app.UI._handle_event(handler, progress_events[0])
    assert handler.advanced.pulse_not_detected == [1]
    assert handler.advanced.completed == []

    popups = []
    monkeypatch.setattr(
        ui_app.messagebox,
        "showwarning",
        lambda title, message, parent: popups.append((title, message)),
    )
    ui_app.UI._handle_event(handler, summary)
    assert "first.holo" in popups[0][1]
