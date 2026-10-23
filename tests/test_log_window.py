"""Exercise actual Tk widgets and logging from a processing thread."""

import logging
from pathlib import Path
import threading
import tkinter as tk
from types import SimpleNamespace

import pytest

from holodoppler.logging import DATE_FORMAT, LOG_FORMAT, logger
from holodoppler.ui.advanced import AdvancedView
from holodoppler.ui.log_window import LogWindow
from holodoppler.ui.minimal import MinimalView


@pytest.fixture(scope="module")
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk display unavailable: {exc}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def log_viewer(tk_root, request):
    root = tk_root
    handlers, level, propagate = logger.handlers[:], logger.level, logger.propagate
    logger.handlers = []
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    viewer = LogWindow(root, theme=getattr(request, "param", "dark"))
    try:
        yield root, viewer
    finally:
        viewer.close()
        for child in root.winfo_children():
            child.destroy()
        logger.handlers = handlers
        logger.setLevel(level)
        logger.propagate = propagate


@pytest.mark.parametrize("log_viewer", ("dark", "light"), indirect=True)
def test_worker_logs_are_retained_while_hidden_with_shared_format_and_colors(log_viewer):
    root, viewer = log_viewer
    records = [
        logging.LogRecord("holodoppler", level, __file__, 1, "message %s", (level,), None)
        for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)
    ]

    def process():
        for record in records:
            logger.handle(record)
        try:
            raise ValueError("processing failed")
        except ValueError:
            logger.exception("Exception details")

    worker = threading.Thread(target=process)
    worker.start()
    worker.join(timeout=2)
    assert not worker.is_alive(), "Logging must not wait for the GUI event loop"
    assert viewer.window is None
    assert not viewer.is_visible

    viewer.toggle()
    root.update()
    content = viewer.text.get("1.0", "end-1c")
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    for record in records:
        assert formatter.format(record) in content
    assert "Traceback (most recent call last)" in content
    assert "ValueError: processing failed" in content
    assert len({viewer.text.tag_cget(level, "foreground") for level in
                ("DEBUG", "INFO", "WARNING", "ERROR")}) == 4
    traceback_index = viewer.text.search("ValueError: processing failed", "1.0")
    assert "ERROR" in viewer.text.tag_names(traceback_index)
    assert viewer.text.cget("state") == "disabled"


def test_close_window_hides_and_reopen_includes_new_records(log_viewer):
    root, viewer = log_viewer
    viewer.toggle()
    root.update()
    original_window = viewer.window
    # Use the actual window-manager close callback, which must only hide it.
    root.tk.call(viewer.window.protocol("WM_DELETE_WINDOW"))
    assert not viewer.is_visible
    logger.warning("Arrived while the log window was hidden")
    viewer.toggle()
    root.update()
    assert viewer.is_visible
    assert viewer.window is original_window
    assert "Arrived while the log window was hidden" in viewer.text.get("1.0", "end")


def test_history_is_bounded_and_visible_updates_are_batched(log_viewer):
    root, viewer = log_viewer
    # Deliberately exceed both the bounded history and a single render batch.
    for number in range(2200):
        logger.debug("History entry %04d", number)
    assert len(viewer._handler.records) == 2000
    viewer.toggle()
    assert viewer._last_sequence == 400  # oldest 200 retained entries rendered
    assert "History entry 0000" not in viewer.text.get("1.0", "end")
    for _ in range(9):
        viewer._refresh()
    assert viewer._last_sequence == 2200
    assert "History entry 2199" in viewer.text.get("1.0", "end")


def test_scrolling_back_does_not_jump_to_new_logs(log_viewer):
    root, viewer = log_viewer
    for number in range(100):
        logger.info("Scrollable entry %d", number)
    viewer.toggle()
    root.update()
    viewer.text.yview_moveto(0)
    root.update()
    assert viewer.text.yview()[1] < 0.99
    logger.info("New message while reading older logs")
    viewer._refresh()
    root.update()
    assert viewer.text.yview()[0] == 0


@pytest.mark.parametrize("view_type", (MinimalView, AdvancedView))
def test_log_button_remains_usable_while_processing(log_viewer, view_type):
    root, viewer = log_viewer
    noop = lambda *args, **kwargs: None
    controller = SimpleNamespace(
        logo_image=None,
        worker_kind="process",
        open_inputs_dialog=noop,
        clear_inputs=noop,
        run_processing=noop,
        stop_processing=noop,
        toggle_logs=viewer.toggle,
    )
    if view_type is MinimalView:
        view = view_type(root, controller)
    else:
        store = SimpleNamespace(
            parameter_files=lambda: [],
            selected_parameters_path=lambda: Path("default.json"),
            current_parameters_label=lambda: "default.json",
            load_current_parameters=lambda: {},
        )
        view = view_type(root, controller, store, theme="dark")
    view.set_busy(True, can_run=True)
    assert not view.log_button.instate(["disabled"])
    view.log_button.invoke()
    assert viewer.is_visible
    view.log_button.invoke()
    assert not viewer.is_visible
    view.set_busy(False, can_run=False)
    assert not view.log_button.instate(["disabled"])


def test_close_detaches_handler_and_timer(log_viewer):
    root, viewer = log_viewer
    viewer.toggle()
    handler, timer, window = viewer._handler, viewer._after_id, viewer.window
    viewer.close()
    viewer.close()  # cleanup is safe after an earlier close
    assert handler not in logger.handlers
    assert timer not in root.tk.call("after", "info")
    assert not window.winfo_exists()
    assert not viewer.is_visible
    logger.info("Logged after viewer cleanup")
    assert not handler.records
