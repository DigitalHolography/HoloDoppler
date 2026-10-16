"""Frontend-independent execution, logging, and user profile contracts."""

import importlib
import io
import logging
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from holodoppler import execution, paths
from holodoppler.cli import command
from holodoppler.cli.parser import parse_args
from holodoppler.config.resolver import update_from_cine_metadata, update_from_holo_footer
from holodoppler.logger import _Formatter, configure_logging, logger


@pytest.fixture
def captured_log(monkeypatch):
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(_Formatter())
    monkeypatch.setattr(logger, "handlers", [handler])
    return output


def test_dispatch_forwards_original_parameters_and_callbacks(monkeypatch, captured_log):
    parameters = dict(pipeline_name="example", nested={"values": [1, 2]})
    result = object()
    progress = Mock()
    warning = Mock()

    def pipeline(path, supplied, **callbacks):
        assert supplied is parameters
        callbacks["progress_callback"](1, 2, "batch")
        callbacks["warning_callback"]("code", "message")
        return result

    monkeypatch.setitem(execution.pipelines, "example", pipeline)
    assert execution.process(Path("input.holo"), parameters, progress, warning) is result
    progress.assert_called_once_with(1, 2, "batch")
    warning.assert_called_once_with("code", "message")
    assert "[warning] [holodoppler.execution] code: message" in captured_log.getvalue()
    assert f"Starting process: file={Path('input.holo').resolve()}" in captured_log.getvalue()


def test_preview_and_unknown_pipeline(monkeypatch):
    pipeline = Mock(return_value="image")
    monkeypatch.setitem(execution.pipelines, "preview_example", pipeline)
    assert execution.preview("input.holo", {"pipeline_name": "example"}) == "image"
    with pytest.raises(ValueError, match="Unknown pipeline"):
        execution.process("input.holo", {"pipeline_name": "does_not_exist"})
    with pytest.raises(ValueError, match="pipeline_name"):
        execution.process("input.holo", {})


def test_batch_continues_and_reports_failures(monkeypatch, captured_log):
    parameters = {"pipeline_name": "example"}
    visited, results, events = [], [], []

    def pipeline(path, supplied, **kwargs):
        assert supplied is parameters
        visited.append(path)
        if path.name == "bad.holo":
            raise ValueError("broken file")
        kwargs["warning_callback"]("cardiac_pulse_not_detected", "No pulse")
        return path.name

    monkeypatch.setitem(execution.pipelines, "example", pipeline)
    files = [Path("bad.holo"), Path("good.holo")]
    summary = execution.run_batch(files, parameters, event_callback=events.append,
                                  result_callback=lambda path, result: results.append(result))
    assert visited == files
    assert results == ["good.holo"]
    assert summary.completed == 1
    assert summary.errors == [(files[0], "broken file")]
    assert not summary.stopped
    progress = [event for event in events if event["kind"] == "batch_progress"]
    assert progress[0]["failed"]
    assert progress[1]["pulse_not_detected"]
    assert "Traceback" not in captured_log.getvalue()


def test_batch_stops_between_files(monkeypatch):
    results = []
    monkeypatch.setitem(execution.pipelines, "example", Mock(return_value=None))
    summary = execution.run_batch([Path("a.holo"), Path("b.holo")],
                                  {"pipeline_name": "example"},
                                  result_callback=lambda *args: results.append(args),
                                  should_stop=lambda: bool(results))
    assert summary.completed == 1
    assert summary.stopped


def test_metadata_resolution_does_not_leak_between_files():
    supplied = {"sampling_freq": "use_holovibes", "z": "use_holovibes"}

    def footer(fps, z):
        return {"compute_settings": {"image_rendering": {"propagation_distance": z}},
                "info": {"camera_fps": fps}}

    assert update_from_holo_footer(supplied, footer(100, 1))["sampling_freq"] == 100
    second = update_from_holo_footer(supplied, footer(200, 2))
    assert second == {"sampling_freq": 200, "z": 2}
    assert supplied == {"sampling_freq": "use_holovibes", "z": "use_holovibes"}
    cine = {"sampling_freq": "use_metadata"}
    assert update_from_cine_metadata(cine, SimpleNamespace(extra={"FrameRate": 50}))["sampling_freq"] == 50
    assert cine["sampling_freq"] == "use_metadata"


def test_structured_logging_levels_and_tracebacks(captured_log):
    handlers = list(logger.handlers)
    configure_logging()
    configure_logging()
    assert logger.handlers == handlers
    logger.info("Metadata: %s", {"camera": {"fps": 100}, "shape": (2, 3)})
    logger.warning("Careful")
    try:
        raise ValueError("failure")
    except ValueError:
        logger.error("Failed", exc_info=True)
    lines = captured_log.getvalue().splitlines()
    assert all(re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[(info|warning|error)\] \[holodoppler\] ", line) for line in lines)
    assert sum("Metadata:" in line for line in lines) == 1
    assert any("Metadata: {'camera': {'fps': 100}, 'shape': (2, 3)}" in line for line in lines)
    assert any("[error] [holodoppler] Traceback" in line for line in lines)


def test_windowed_logging(monkeypatch):
    import sys
    monkeypatch.setattr(logger, "handlers", [])
    monkeypatch.setattr(sys, "stderr", None)
    configure_logging()
    logger.info("No console")
    logger.error("No console")


def test_tracebacks_flag_and_gui_parser():
    assert parse_args(["process", "--tracebacks"]).tracebacks
    assert not parse_args(["preview"]).tracebacks
    assert parse_args(["gui"]).command == "gui"


@pytest.mark.parametrize("tracebacks", [False, True])
def test_cli_failure_exit_and_traceback_option(tmp_path, monkeypatch, captured_log, tracebacks):
    file = tmp_path / "input.holo"
    file.touch()
    config = tmp_path / "config.yaml"
    config.write_text("pipeline_name: example\n")
    monkeypatch.setitem(execution.pipelines, "example", Mock(side_effect=ValueError("bad input")))
    argv = ["process", str(file), str(config)] + (["--tracebacks"] if tracebacks else [])
    assert command.main(argv) == 1
    assert ("Traceback" in captured_log.getvalue()) is tracebacks
    batch = tmp_path / "batch.txt"
    batch.write_text(str(file))
    assert command.main(["process", "--batch", str(batch), str(config)] +
                        (["--tracebacks"] if tracebacks else [])) == 1


@pytest.fixture
def user_profiles(tmp_path, monkeypatch):
    shipped = tmp_path / "shipped"
    shipped.mkdir()
    (shipped / paths.DEFAULT_PARAMETERS_NAME).write_text("pipeline_name: default\n")
    base = tmp_path / "user" / "HoloDoppler" / "1.2"
    monkeypatch.setattr(paths, "appdata_root", lambda: tmp_path / "user")
    monkeypatch.setattr(paths, "app_settings_dir", lambda: base)
    monkeypatch.setattr(paths, "repository_parameters_dir", lambda: shipped)
    return base, shipped


def test_profiles_seed_once_and_share_cli_ui_default(user_profiles, monkeypatch):
    from holodoppler.ui import settings_store
    base, shipped = user_profiles
    monkeypatch.setattr(settings_store, "app_settings_dir", lambda: base)
    default = paths.default_parameters_path()
    default.write_text("pipeline_name: custom\n")
    (shipped / "new.yaml").write_text("pipeline_name: example\n")
    store = settings_store.SettingsStore()
    store.initialize()
    assert command._resolve_config_path(None) == store.selected_parameters_path() == default
    assert store.load_selected_parameters() == {"pipeline_name": "custom"}
    assert (store.parameters_dir / "new.yaml").is_file()
    store.save_loaded_parameters({"pipeline_name": "working"})
    store.save_parameters_as("mine", {"pipeline_name": "mine"})
    store.initialize()
    assert store.load_current_parameters() == {"pipeline_name": "working"}
    assert store.load_selected_parameters() == {"pipeline_name": "mine"}
    assert (shipped / paths.DEFAULT_PARAMETERS_NAME).read_text() == "pipeline_name: default\n"


def test_legacy_slug_migration_preserves_edits(user_profiles):
    base, _ = user_profiles
    old = base.parents[1] / "holodopplerpython" / base.name
    (old / "parameters").mkdir(parents=True)
    (old / "parameters" / paths.DEFAULT_PARAMETERS_NAME).write_text("pipeline_name: edited\n")
    (old / "app_settings.json").write_text('{"theme": "light"}')
    paths.initialize_parameters()
    assert (base / "parameters" / paths.DEFAULT_PARAMETERS_NAME).read_text() == "pipeline_name: edited\n"
    assert (base / "app_settings.json").is_file()
    assert old.is_dir()


def test_missing_default_is_an_error(user_profiles):
    _, shipped = user_profiles
    (shipped / paths.DEFAULT_PARAMETERS_NAME).unlink()
    with pytest.raises(FileNotFoundError, match="Default parameters"):
        paths.default_parameters_path()


def test_linux_data_directory_and_legacy_config_migration(tmp_path, monkeypatch):
    # Override paths.os rather than changing os.name process-wide (pathlib uses it).
    monkeypatch.setattr(paths, "os", SimpleNamespace(name="posix", environ={
        "XDG_DATA_HOME": str(tmp_path / "data"), "XDG_CONFIG_HOME": str(tmp_path / "config")}))
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setattr(paths, "get_version", lambda: "1.2")
    assert paths.app_settings_dir() == tmp_path / "data" / "HoloDoppler" / "1.2"
    old = tmp_path / "config" / "holodopplerpython" / "1.2"
    old.mkdir(parents=True)
    (old / "app_settings.json").write_text('{"theme":"light"}')
    paths.initialize_parameters()
    assert (paths.app_settings_dir() / "app_settings.json").read_text() == '{"theme":"light"}'


def test_windows_data_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "os", SimpleNamespace(name="nt", environ={"APPDATA": str(tmp_path)}))
    monkeypatch.setattr(paths, "get_version", lambda: "unfound")
    assert paths.app_settings_dir() == tmp_path / "HoloDoppler" / "unfound"


def test_installed_and_frozen_parameters_locations(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "project_root", lambda: tmp_path / "not_a_checkout")
    monkeypatch.setattr(paths.sysconfig, "get_path", lambda _: str(tmp_path))
    assert paths.repository_parameters_dir() == tmp_path / "share" / "HoloDoppler" / "parameters"
    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths.sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    assert paths.repository_parameters_dir() == tmp_path / "bundle" / "parameters"


def test_version_unfound(monkeypatch):
    module = importlib.import_module("holodoppler.get_version")
    monkeypatch.setattr(module.sys, "frozen", True, raising=False)
    monkeypatch.setattr(module, "version", Mock(side_effect=module.PackageNotFoundError))
    assert module.get_version() == "unfound"


def test_ui_worker_continues_and_summarizes_errors(monkeypatch):
    import queue
    import threading
    from holodoppler.ui.app import UI

    visited = []

    def pipeline(path, supplied, **kwargs):
        visited.append(path.name)
        if path.name == "bad.holo":
            raise ValueError("bad input")
        return {"image": True}

    monkeypatch.setitem(execution.pipelines, "example", pipeline)
    controller = SimpleNamespace(events=queue.Queue(), stop_event=threading.Event(),
                                 _first_m0_frame=lambda result: "preview")
    UI._process_worker(controller, [Path("bad.holo"), Path("good.holo")],
                       {"pipeline_name": "example"})
    assert visited == ["bad.holo", "good.holo"]
    events = list(controller.events.queue)
    assert events[-1]["kind"] == "worker_done"
    assert any(event["kind"] == "processed_preview" and event["image"] == "preview" for event in events)
    summary = next(event for event in events if event["kind"] == "batch_failed")
    assert summary["errors"] == [(Path("bad.holo"), "bad input")]


def test_ui_worker_cancellation_and_preview(monkeypatch):
    import queue
    import threading
    from holodoppler.ui.app import UI

    controller = SimpleNamespace(events=queue.Queue(), stop_event=threading.Event(),
                                 _first_m0_frame=lambda result: None)
    controller.stop_event.set()
    pipeline = Mock(return_value="image")
    monkeypatch.setitem(execution.pipelines, "example", pipeline)
    monkeypatch.setitem(execution.pipelines, "preview_example", pipeline)
    UI._process_worker(controller, [Path("a.holo")], {"pipeline_name": "example"})
    pipeline.assert_not_called()
    assert any(event.get("message") == "Stopped" for event in controller.events.queue)
    UI._preview_worker(controller, Path("a.holo"), {"pipeline_name": "example"})
    assert any(event["kind"] == "preview_result" and event["image"] == "image"
               for event in controller.events.queue)


def test_packaging_uses_canonical_profiles(monkeypatch, tmp_path):
    import build_installer

    build_installer._validate_parameter_presets()
    monkeypatch.setattr(build_installer, "GENERATED_ENTRYPOINT", tmp_path / "entry.py")
    monkeypatch.setattr(build_installer, "BUILD_DIR", tmp_path)
    entry = build_installer._write_pyinstaller_entrypoint()
    compile(entry.read_text(), str(entry), "exec")
    assert "holodopplerpython" not in entry.read_text()
    command_lines = []
    monkeypatch.setattr(build_installer, "_ensure_icon", lambda: tmp_path / "logo.ico")
    monkeypatch.setattr(build_installer, "_clean_pyinstaller_outputs", lambda: None)
    monkeypatch.setattr(build_installer, "_run_command", command_lines.append)
    build_installer._run_pyinstaller(console=True)
    command_line = command_lines[0]
    data_arg = command_line[command_line.index("--add-data") + 1]
    assert str(build_installer.PARAMETERS_DIR) in data_arg
    assert data_arg.endswith("parameters")


@pytest.mark.parametrize("gpu", [False, True])
@pytest.mark.parametrize("fail", [False, True])
def test_processing_summaries_surround_bar(monkeypatch, captured_log, gpu, fail):
    import numpy as np
    from tqdm import tqdm
    from holodoppler import backend
    from holodoppler.core import processing

    monkeypatch.setattr(backend, "is_gpu", gpu)
    monkeypatch.setattr(backend, "get_backend_name", lambda: "cupy" if gpu else "numpy")
    monkeypatch.setattr(backend, "to_backend", np.asarray)
    monkeypatch.setattr(backend, "xp", np)
    monkeypatch.setattr(processing, "tqdm", lambda **kwargs: tqdm(file=captured_log, **kwargs))
    times = iter([10.0, 12.5])
    monkeypatch.setattr(processing, "perf_counter", lambda: next(times))

    def process(frames, reference):
        if fail and frames[0, 0, 0] == 1:
            raise ValueError("compute failed")
        return {"value": frames}, reference

    def gpu_batches(reader, indices, size, process_batch, consume, reference, prepare, depth):
        # Exercise the async branch and its early return without requiring CUDA.
        consume(0, {"value": np.ones((1, 2, 2))})
        if fail:
            raise ValueError("compute failed")
        consume(1, {"value": np.ones((1, 2, 2))})
        return reference

    monkeypatch.setattr(processing, "_run_cupy_batches", gpu_batches)
    reader = SimpleNamespace(file_path=Path("input.holo"),
                             read_frames=lambda **kwargs: np.full((1, 2, 2), kwargs["first_frame"]))

    def run():
        processing.run_batches(reader, [0, 1], 1, process, lambda *args: None)

    if fail:
        with pytest.raises(ValueError, match="compute failed"):
            run()
    else:
        run()
    output = captured_log.getvalue()
    status = "failed" if fail else "complete"
    assert output.index("Starting batch processing") < output.index("Processing (")
    assert output.rindex("Processing (") < output.index(f"Batch processing {status}:")
    assert "elapsed=2.500s" in output
    assert f"completed={1 if fail else 2}/2" in output
    assert "[holodoppler.core.processing]" in output


def test_saving_uses_module_logger(tmp_path, captured_log, capsys):
    import json
    import numpy as np
    import h5py
    import yaml
    from holodoppler import saving

    saving.save_json(tmp_path / "params.json", {"batch_size": 4})
    saving.save_yaml(tmp_path / "params.yaml", {"batch_size": 4})
    file = saving.save_h5(tmp_path, {"moment0": np.ones((2, 2))}, git_commit="test")
    assert json.loads((tmp_path / "params.json").read_text()) == {"batch_size": 4}
    assert yaml.safe_load((tmp_path / "params.yaml").read_text()) == {"batch_size": 4}
    with h5py.File(file) as saved:
        np.testing.assert_array_equal(saved["moment0"], np.ones((2, 2)))
    output = captured_log.getvalue()
    assert "[info] [holodoppler.saving] Saved JSON:" in output
    assert "[info] [holodoppler.saving] Saved YAML:" in output
    assert "[info] [holodoppler.saving] H5 saved:" in output
    assert capsys.readouterr().out == ""


def test_saving_errors_use_error_level(tmp_path, captured_log, monkeypatch):
    import numpy as np
    from holodoppler import saving

    monkeypatch.setattr(saving, "save_image_png", Mock(side_effect=OSError("disk full")))
    saving.save_pngs(tmp_path, {"moment0": np.ones((2, 2))})
    assert "[error] [holodoppler.saving] Failed to save PNG moment0: disk full" in captured_log.getvalue()
