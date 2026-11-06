"""Check the complete GUI and shared pipeline logger in an isolated session."""

from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


def test_gui_can_toggle_logs_during_processing_and_logs_worker_errors(tmp_path):
    script = textwrap.dedent(
        """
        import os
        from pathlib import Path
        import sys
        import threading
        import tkinter as tk

        task_dir = Path(sys.argv[1])
        os.environ['APPDATA'] = str(task_dir)
        os.environ['XDG_CONFIG_HOME'] = str(task_dir)
        from holodoppler.logging import configure_logging, get_log_path, logger
        configure_logging(log_path=task_dir / 'shared.log')
        from holodoppler.pipelines import pipelines
        from holodoppler.ui import app

        started, finish = threading.Event(), threading.Event()

        def pipeline(file_path, parameters, progress_callback=None, warning_callback=None):
            logger.debug('Debug from pipeline')
            logger.info('Info from pipeline')
            logger.warning('Warning from pipeline')
            logger.error('Error from pipeline')
            started.set()
            assert finish.wait(5), 'GUI toggle blocked processing'
            return {}

        pipelines['test_logging'] = pipeline
        try:
            ui = app.UI()
        except tk.TclError as exc:
            print('TK_UNAVAILABLE:', exc)
            raise SystemExit(77)
        ui.withdraw()
        # Automatic preview scheduling is exercised in test_ui_previews.
        ui._queue_previews = lambda paths: None
        try:
            ui.session_parameters = {
                'pipeline_name': 'test_logging',
            }
            ui.input_paths = [task_dir / 'recording.holo']
            ui._sync_views()
            ui.run_processing()
            assert started.wait(5)
            assert ui._busy()
            ui.minimal.log_button.invoke()
            ui.update()
            assert ui.log_window.is_visible
            assert not ui.minimal.log_button.instate(['disabled'])
            assert not ui.advanced.log_button.instate(['disabled'])
            ui.advanced.log_button.invoke()
            assert not ui.log_window.is_visible
            logger.info('Message while hidden')
            ui.advanced.log_button.invoke()
            ui.update()
            assert ui.log_window.is_visible
            assert 'Message while hidden' in ui.log_window.text.get('1.0', 'end')
            finish.set()
            ui.worker.join(timeout=5)
            assert not ui._busy()
            while not ui.events.empty():
                ui._handle_event(ui.events.get_nowait())

            def preview_pipeline(file_path, parameters, progress_callback=None, warning_callback=None):
                logger.debug('Preview uses the shared pipeline logger')
                return None

            pipelines['preview_test_logging'] = preview_pipeline
            from holodoppler.cli import preview
            preview(ui.input_paths[0], ui.session_parameters)
            assert not ui._busy()
            while not ui.events.empty():
                ui._handle_event(ui.events.get_nowait())

            def failing_pipeline(file_path, parameters, progress_callback=None, warning_callback=None):
                raise ValueError('Pipeline failure details')

            pipelines['test_logging'] = failing_pipeline
            popups = []
            app.messagebox.showerror = lambda title, message, parent: popups.append(message)
            ui.run_processing()
            ui.worker.join(timeout=5)
            assert not ui._busy()
            while not ui.events.empty():
                ui._handle_event(ui.events.get_nowait())
            ui.log_window._refresh()
            content = ui.log_window.text.get('1.0', 'end-1c')
            saved = get_log_path().read_text(encoding='utf-8')
            assert content == saved
            assert 'Preview uses the shared pipeline logger' in saved
            assert saved.count('Traceback (most recent call last)') == 1
            assert 'ValueError: Pipeline failure details' in saved
            assert str(get_log_path()) in popups[0]

            # Both Stop controls interrupt a file through the progress object.
            for mode in ("minimal", "advanced"):
                entered, release = threading.Event(), threading.Event()
                calls = []
                def cancellable_pipeline(file_path, parameters, progress_callback=None, warning_callback=None):
                    calls.append(file_path)
                    entered.set()
                    assert release.wait(5)
                    progress_callback(1, 10, 'checkpoint')
                    return {}
                pipelines['test_logging'] = cancellable_pipeline
                ui.input_paths = [task_dir / 'first.holo', task_dir / 'second.holo']
                ui._sync_views()
                ui.run_processing()
                assert entered.wait(5)
                while not ui.events.empty():
                    ui._handle_event(ui.events.get_nowait())
                button = ui.minimal.action_button if mode == 'minimal' else ui.advanced.stop_button
                button.invoke()
                assert button.instate(['disabled'])
                assert ui.minimal.status_var.get() == 'Stopping...'
                release.set()
                ui.worker.join(timeout=5)
                assert not ui._busy()
                while not ui.events.empty():
                    ui._handle_event(ui.events.get_nowait())
                assert len(calls) == 1
                assert ui.minimal.status_var.get() == 'Stopped'
                assert ui.minimal.batch_progress['value'] == 0
                assert len(popups) == 1
                assert not ui.advanced.run_button.instate(['disabled'])

            # Starting again clears the previous cancellation request.
            pipelines['test_logging'] = lambda *args, **kwargs: {}
            ui.run_processing()
            ui.worker.join(timeout=5)
            while not ui.events.empty():
                ui._handle_event(ui.events.get_nowait())
            assert not ui.stop_event.is_set()
            assert ui.minimal.status_var.get() == 'Processing complete'
        finally:
            finish.set()
            if ui.worker is not None:
                ui.worker.join(timeout=5)
            ui._on_close()
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode == 77:
        pytest.skip(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
