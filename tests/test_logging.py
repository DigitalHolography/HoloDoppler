import io
import logging
from logging.handlers import RotatingFileHandler
import multiprocessing
import runpy
import subprocess
import sys
import threading
from types import ModuleType, SimpleNamespace

import pytest

from holodoppler import logging as app_logging


@pytest.fixture
def isolated_logging(monkeypatch, tmp_path):
    """Keep application handlers and exception hooks isolated from other tests."""
    logger = app_logging.logger
    previous_handlers = logger.handlers[:]
    previous_level = logger.level
    previous_propagate = logger.propagate
    logger.handlers = []
    monkeypatch.setattr(app_logging, "_configured", False)
    monkeypatch.setattr(app_logging, "_log_path", None)
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    monkeypatch.setattr(threading, "excepthook", threading.excepthook)
    try:
        yield tmp_path / "logs" / "holodoppler.log"
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        logger.handlers = previous_handlers
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate


def test_configuration_is_idempotent_and_preserves_gui_handlers(isolated_logging, monkeypatch):
    console = io.StringIO()
    monkeypatch.setattr(sys, "stderr", console)
    received = []

    class GuiHandler(logging.Handler):
        def emit(self, record):
            received.append(record.getMessage())

    gui_handler = GuiHandler()
    app_logging.logger.addHandler(gui_handler)
    first = app_logging.configure_logging(log_path=isolated_logging)
    original_handlers = first.handlers[:]
    second = app_logging.configure_logging(log_path=isolated_logging.with_name("other.log"))
    second.info("One message")

    assert first is second is app_logging.logger
    assert second.handlers == original_handlers
    assert gui_handler in second.handlers
    assert received == ["One message"]
    assert console.getvalue().count("One message") == 1
    assert isolated_logging.read_text(encoding="utf-8").count("One message") == 1
    assert app_logging.get_log_path() == isolated_logging


def test_all_levels_and_tracebacks_match_in_console_and_file(isolated_logging, monkeypatch):
    console = io.StringIO()
    monkeypatch.setattr(sys, "stderr", console)
    logger = app_logging.configure_logging(log_path=isolated_logging)

    logger.debug("Batch %s", 4)
    logger.info("Processing café recording")
    logger.warning("Skipped one frame")
    logger.error("Input missing")
    try:
        raise ValueError("Cannot read recording")
    except ValueError:
        logger.exception("Processing failed")

    contents = isolated_logging.read_text(encoding="utf-8")
    assert console.getvalue() == contents
    for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
        assert f"| {level}" in contents
    assert "Batch 4" in contents
    assert "café" in contents
    assert "Traceback (most recent call last):" in contents
    assert "ValueError: Cannot read recording" in contents
    assert contents.count("Processing failed") == 1


@pytest.mark.parametrize("frozen", [False, True])
def test_windowed_runs_keep_all_levels_and_supply_writable_streams(
    isolated_logging, monkeypatch, frozen
):
    with monkeypatch.context() as windowed:
        windowed.setattr(sys, "frozen", frozen, raising=False)
        windowed.setattr(sys, "stdout", None)
        windowed.setattr(sys, "stderr", None)
        logger = app_logging.configure_logging(log_path=isolated_logging)
        app_logging.ensure_standard_streams()
        fallback_streams = (sys.stdout, sys.stderr)
        try:
            for stream in fallback_streams:
                stream.write("tqdm and native libraries can safely write here\n")
                stream.flush()
            for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR):
                logger.log(level, "Windowed message %s", logging.getLevelName(level))
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], RotatingFileHandler)
        finally:
            for stream in fallback_streams:
                stream.close()

    contents = isolated_logging.read_text(encoding="utf-8")
    for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
        assert f"Windowed message {level}" in contents


def test_closed_console_stream_is_replaced(isolated_logging, monkeypatch):
    old_console = io.StringIO()
    monkeypatch.setattr(sys, "stderr", old_console)
    logger = app_logging.configure_logging(log_path=isolated_logging)
    old_console.close()
    new_console = io.StringIO()
    monkeypatch.setattr(sys, "stderr", new_console)

    logger.info("Console replaced")

    assert "Console replaced" in new_console.getvalue()
    assert "Console replaced" in isolated_logging.read_text(encoding="utf-8")


def test_uncaught_exception_hooks_record_tracebacks_once(isolated_logging):
    app_logging.configure_logging(log_path=isolated_logging)
    try:
        raise RuntimeError("Unexpected failure")
    except RuntimeError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sys.excepthook(exc_type, exc_value, exc_traceback)
        threading.excepthook(
            SimpleNamespace(
                exc_type=exc_type,
                exc_value=exc_value,
                exc_traceback=exc_traceback,
                thread=SimpleNamespace(name="processing-worker"),
            )
        )
    threading.excepthook(SimpleNamespace(exc_type=SystemExit))

    contents = isolated_logging.read_text(encoding="utf-8")
    assert contents.count("| ERROR") == 2
    assert contents.count("RuntimeError: Unexpected failure") == 2
    assert "Unhandled exception in thread processing-worker" in contents
    assert "SystemExit" not in contents


def test_file_rotation_bounds_history(isolated_logging, monkeypatch):
    monkeypatch.setattr(app_logging, "MAX_LOG_BYTES", 250)
    monkeypatch.setattr(app_logging, "LOG_BACKUP_COUNT", 2)
    logger = app_logging.configure_logging(log_path=isolated_logging)
    for index in range(30):
        logger.debug("Batch %02d: %s", index, "x" * 80)

    files = list(isolated_logging.parent.glob("holodoppler.log*"))
    assert sorted(path.name for path in files) == [
        "holodoppler.log", "holodoppler.log.1", "holodoppler.log.2"
    ]
    assert all(path.stat().st_size <= 250 for path in files)
    assert "Batch 29" in isolated_logging.read_text(encoding="utf-8")


def _log_from_spawned_worker(log_queue):
    app_logging.configure_worker_logging(log_queue)
    # Processing entrypoints may configure again; the queue must be preserved.
    app_logging.configure_logging()
    app_logging.logger.debug("Worker diagnostic")
    try:
        raise ValueError("Worker exception")
    except ValueError:
        app_logging.logger.exception("Worker failed")


def test_spawned_workers_share_parent_file_console_and_gui(isolated_logging, monkeypatch):
    console = io.StringIO()
    monkeypatch.setattr(sys, "stderr", console)
    logger = app_logging.configure_logging(log_path=isolated_logging)
    received = []

    class GuiHandler(logging.Handler):
        def emit(self, record):
            received.append((record.levelno, record.getMessage()))

    logger.addHandler(GuiHandler())
    with app_logging.worker_logging_queue() as log_queue:
        process = multiprocessing.Process(
            target=_log_from_spawned_worker, args=(log_queue,)
        )
        process.start()
        process.join(timeout=20)
        if process.is_alive():
            process.terminate()
            process.join()
            pytest.fail("Logging worker did not finish")
        assert process.exitcode == 0

    contents = isolated_logging.read_text(encoding="utf-8")
    assert contents == console.getvalue()
    assert contents.count("Worker diagnostic") == 1
    assert contents.count("Worker failed") == 1
    assert "ValueError: Worker exception" in contents
    assert [level for level, _message in received] == [logging.DEBUG, logging.ERROR]


def test_generated_release_launcher_uses_shared_entrypoint(isolated_logging, monkeypatch):
    import build_installer

    monkeypatch.setattr(build_installer, "BUILD_DIR", isolated_logging.parent)
    monkeypatch.setattr(
        build_installer, "GENERATED_ENTRYPOINT", isolated_logging.parent / "launcher.py"
    )
    entrypoint = build_installer._write_pyinstaller_entrypoint()
    app_logging.configure_logging(log_path=isolated_logging)
    fake_cli = ModuleType("holodoppler.cli")

    def cli_main():
        app_logging.logger.info("Shared CLI entrypoint called")
        return 7

    fake_cli.main = cli_main
    monkeypatch.setitem(sys.modules, "holodoppler.cli", fake_cli)
    monkeypatch.setattr(sys, "argv", ["HoloDoppler.exe", "process"])
    freeze_calls = []
    monkeypatch.setattr(multiprocessing, "freeze_support", lambda: freeze_calls.append(True))

    with pytest.raises(SystemExit) as result:
        runpy.run_path(str(entrypoint), run_name="__main__")

    assert result.value.code == 7
    assert freeze_calls == [True]
    assert "Shared CLI entrypoint called" in isolated_logging.read_text(encoding="utf-8")
    source = entrypoint.read_text(encoding="utf-8")
    assert "runtime.log" not in source
    assert "holodoppler-error.log" not in source


def test_log_path_uses_version_and_does_not_import_gui(isolated_logging, monkeypatch):
    # Check the path before configuration, with no dependency on UI paths.
    monkeypatch.setattr(app_logging, "get_version", lambda: "0.7.1")
    path = app_logging.get_log_path()
    assert path.parts[-4:] == ("HoloDoppler", "0.7.1", "logs", "holodoppler.log")
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import holodoppler.logging; assert 'holodoppler.ui' not in sys.modules",
        ],
        check=True,
        capture_output=True,
        timeout=10,
    )


def test_cli_configuration_errors_reach_the_shared_log(isolated_logging, monkeypatch):
    from holodoppler.cli import command

    app_logging.configure_logging(log_path=isolated_logging)
    missing_config = isolated_logging.parent / "missing.yaml"
    monkeypatch.setattr(
        command,
        "parse_args",
        lambda _argv: SimpleNamespace(command="process", config=missing_config),
    )

    assert command.main([]) == command.EXIT_FAILURE

    contents = isolated_logging.read_text(encoding="utf-8")
    assert "| ERROR" in contents
    assert contents.count("Config file does not exist") == 1
    assert str(missing_config) in contents
