"""Exercise real notebook bindings and window layout in isolated GUI sessions."""

from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


def test_mode_reveal_waits_once_for_actual_geometry_changes(monkeypatch):
    from fractions import Fraction
    from types import MethodType, SimpleNamespace

    from holodoppler.ui import app

    clock, serial, restored = [0], [0], []
    pending = {}

    def after(delay_ms, callback):
        serial[0] += 1
        timer = f"after{serial[0]}"
        pending[timer] = (clock[0] + delay_ms, serial[0], callback)
        return timer

    def advance(target_ms):
        for _ in range(100):
            if not pending:
                break
            timer = min(pending, key=lambda name: pending[name][:2])
            when, _, callback = pending[timer]
            if when > target_ms:
                break
            del pending[timer]
            clock[0] = when
            callback()
        else:
            raise AssertionError("Reveal callbacks never settled")
        clock[0] = target_ms

    signature = [("initial geometry",)]
    mode = SimpleNamespace(
        _mode_switch_alpha=1.0,
        _mode_switch_after_id=None,
        _mode_switch_layout=None,
        _mode_switch_layout_changed_at=0.0,
        _mode_layout_signature=lambda: signature[0],
        after=after,
        after_idle=lambda callback: after(0, callback),
        after_cancel=lambda timer: pending.pop(timer, None),
        attributes=lambda *args: restored.append(clock[0]),
    )
    for name in (
        "_on_mode_layout", "_cancel_mode_reveal", "_schedule_mode_reveal",
        "_queue_mode_reveal", "_finish_mode_layout", "_reveal_mode_if_stable",
        "_reveal_mode",
    ):
        setattr(mode, name, MethodType(getattr(app.UI, name), mode))
    monkeypatch.setattr(app, "time", SimpleNamespace(
        monotonic=lambda: Fraction(clock[0], 1000),
    ))
    quiet = app._MODE_SWITCH_SETTLE_MS

    mode._schedule_mode_reveal()
    advance(0)
    assert mode._mode_switch_layout == signature[0], "Initial snapshot was delayed"
    advance(quiet - 1)
    mode._on_mode_layout(None)  # Duplicate Configure must not restart the wait.
    advance(quiet)
    assert restored == [quiet]

    mode._mode_switch_alpha = 1.0
    mode._schedule_mode_reveal()
    advance(quiet)
    changed_at = quiet + quiet // 2
    advance(changed_at)
    signature[0] = ("changed geometry",)
    mode._on_mode_layout(None)
    advance(quiet * 2)
    assert mode._mode_switch_alpha == 1.0, "Revealed before changed layout settled"
    advance(changed_at + quiet)
    assert restored == [quiet, changed_at + quiet]


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_mode_switch_hides_layout_and_restores_window(tmp_path, theme):
    script = textwrap.dedent(
        """
        import math
        import os
        from pathlib import Path
        import sys
        import time
        import tkinter as tk
        from tkinter import ttk
        import _tkinter

        task_dir = Path(sys.argv[1])
        os.environ['APPDATA'] = str(task_dir)
        os.environ['XDG_CONFIG_HOME'] = str(task_dir)
        from holodoppler.ui import app

        app.SettingsStore.theme = lambda self: sys.argv[2]
        try:
            display_probe = tk.Tk()
        except tk.TclError as exc:
            print('TK_UNAVAILABLE:', exc)
            raise SystemExit(77)
        display_probe.destroy()
        ui = app.UI()

        closed = False
        try:
            errors = []
            ui.report_callback_exception = lambda *args: errors.append(args)

            def settle():
                deadline = time.monotonic() + 3
                visible_since = None
                while True:
                    ui.update()
                    if ui._mode_switch_alpha is None:
                        if visible_since is None:
                            visible_since = time.monotonic()
                        elif time.monotonic() - visible_since >= 0.25:
                            break
                    else:
                        visible_since = None
                    assert time.monotonic() < deadline, 'Window stayed transparent'
                    time.sleep(0.005)
                assert not errors, errors
                assert ui._mode_switch_after_id is None
                assert math.isclose(float(ui.attributes('-alpha')), 0.8)
                if reveal_geometry:
                    before, after = reveal_geometry[-1], visible_geometry()
                    moved = {
                        name: (before.get(name), after.get(name))
                        for name in before.keys() | after.keys()
                        if before.get(name) != after.get(name)
                    }
                    assert not moved, ('Widgets moved after reveal', moved)

            def layout_without_timers():
                flags = _tkinter.WINDOW_EVENTS | _tkinter.IDLE_EVENTS | _tkinter.DONT_WAIT
                while ui.tk.dooneevent(flags):
                    pass

            ui.update()
            ui.attributes('-alpha', 0.8)
            minimal_size = (ui.winfo_width(), ui.winfo_height())
            layouts = []
            visible_layouts = []
            reveal_geometry = []
            progress_updates = []
            handle_event = ui._handle_event

            def visible_geometry():
                geometry = {}
                def visit(widget):
                    if widget.winfo_toplevel() != ui:
                        return
                    if widget.winfo_viewable():
                        geometry[str(widget)] = widget.winfo_geometry()
                    for child in widget.winfo_children():
                        visit(child)
                visit(ui)
                return geometry

            attributes = ui.attributes
            def record_reveal(*args):
                if len(args) == 2 and args[0] == '-alpha' and float(args[1]) > 0:
                    reveal_geometry.append(visible_geometry())
                return attributes(*args)
            ui.attributes = record_reveal

            def record_progress(event):
                if event.get('kind') == 'file_progress':
                    progress_updates.append(float(ui.attributes('-alpha')))
                handle_event(event)

            ui._handle_event = record_progress

            def record_layout(event):
                widget = event.widget
                if widget.winfo_toplevel() == ui and widget.winfo_viewable():
                    alpha = float(ui.attributes('-alpha'))
                    layouts.append(alpha)
                    if alpha > 0 and reveal_geometry[-1].get(str(widget)) != widget.winfo_geometry():
                        visible_layouts.append((str(widget), widget.winfo_geometry()))

            ui.bind('<Configure>', record_layout, add='+')
            ui.bind('<Map>', record_layout, add='+')

            def switch(action, index):
                layouts.clear()
                visible_layouts.clear()
                action()
                assert ui.notebook.index('current') == index
                assert float(ui.attributes('-alpha')) == 0.0
                # The event loop must remain responsive while layout is hidden.
                heartbeat = []
                ui.after(0, lambda: heartbeat.append(float(ui.attributes('-alpha'))))
                settle()
                assert heartbeat == [0.0]
                assert layouts and not visible_layouts, visible_layouts
                assert ui.active_tab_name == ('advanced' if index else 'minimal')
                assert ui.store.active_tab() == ui.active_tab_name
                if index == 1:
                    # Explicitly include the Ready label and every top toolbar
                    # button in the geometry captured before opacity returns.
                    toolbar = ui.advanced.load_input_button.master
                    assert all(str(widget) in reveal_geometry[-1]
                               for widget in (toolbar, *toolbar.winfo_children()))

            # Python selections must hide the old page before window resizing.
            switch(lambda: ui.notebook.select(1), 1)
            assert ui.winfo_width() >= minimal_size[0]

            # Exercise the actual ttk mouse class binding, including themed tabs.
            def click_tab(index):
                for y in range(4, 64, 4):
                    for x in range(4, ui.notebook.winfo_width(), 4):
                        try:
                            hit = ui.notebook.index('@%d,%d' % (x, y))
                        except tk.TclError:
                            continue
                        if hit == index:
                            ui.notebook.event_generate('<ButtonPress-1>', x=x, y=y)
                            ui.notebook.event_generate('<ButtonRelease-1>', x=x, y=y)
                            return
                raise AssertionError('Could not find notebook tab')

            switch(lambda: click_tab(0), 0)
            assert (ui.winfo_width(), ui.winfo_height()) == minimal_size

            ui.notebook.focus_force()
            ui.update()
            switch(lambda: ui.notebook.event_generate('<KeyPress-Right>'), 1)
            assert ui.focus_get() == ui.notebook
            switch(lambda: ui.notebook.select(0), 0)

            # Settings has deeper layouts than Inputs & Preview. Preselect it
            # while hidden, then verify every visible descendant after reveal.
            nested = next(child for child in ui.advanced.winfo_children()
                          if isinstance(child, ttk.Notebook))
            nested.select(1)
            ui.update()
            switch(lambda: ui.notebook.select(1), 1)
            switch(lambda: ui.notebook.select(0), 0)
            nested.select(0)
            ui.update()

            # A late child-only layout must postpone reveal even when the root,
            # mode notebook and selected page have unchanged geometry.
            layouts.clear()
            visible_layouts.clear()
            ui.notebook.select(1)
            layout_without_timers()
            outer = {str(w): w.winfo_geometry()
                     for w in (ui, ui.notebook, ui.advanced)}
            delayed = []
            def delayed_toolbar_layout():
                delayed.append(float(ui.attributes('-alpha')))
                ui.advanced.clear_button.grid_configure(padx=(24, 12))
            ui.after(80, delayed_toolbar_layout)
            settle()
            assert delayed == [0.0], 'Child layout started after the window was shown'
            assert outer == {str(w): w.winfo_geometry()
                             for w in (ui, ui.notebook, ui.advanced)}
            assert not visible_layouts, visible_layouts
            switch(lambda: ui.notebook.select(0), 0)
            ui.advanced.clear_button.grid_configure(padx=(0, 12))
            ui.update()

            # Queries, repeated selections and disabled tabs must not hide anything.
            ui.notebook.select()
            ui.notebook.select(0)
            ui.notebook.tab(1, state='disabled')
            ui.notebook.select(1)
            ui.update()
            assert ui.notebook.index('current') == 0
            assert ui._mode_switch_alpha is None
            assert math.isclose(float(ui.attributes('-alpha')), 0.8)
            ui.notebook.tab(1, state='normal')

            # A second switch cancels the pending reveal and preserves opacity.
            ui.notebook.select(1)
            layout_without_timers()
            stale_timer = ui._mode_switch_after_id
            assert stale_timer is not None
            ui.notebook.select(0)
            assert stale_timer not in ui.tk.splitlist(ui.tk.call('after', 'info'))
            assert math.isclose(ui._mode_switch_alpha, 0.8)
            settle()
            assert (ui.winfo_width(), ui.winfo_height()) == minimal_size

            # Back-to-back selections must also size the final page correctly.
            ui.notebook.select(1)
            ui.notebook.select(0)
            settle()
            assert (ui.winfo_width(), ui.winfo_height()) == minimal_size

            # A busy callback can leave both a due reveal and pending layout.
            # The reveal must still wait until that layout has been processed.
            layouts.clear()
            ui.notebook.select(1)
            layout_without_timers()
            ui.geometry('1100x700')
            ui.tk.call('after', app._MODE_SWITCH_SETTLE_MS + 30)
            settle()
            assert layouts and not visible_layouts, visible_layouts
            switch(lambda: ui.notebook.select(0), 0)

            if ui.tk.call('tk', 'windowingsystem') == 'win32':
                ui.state('zoomed')
                ui.update()
                switch(lambda: ui.notebook.select(1), 1)
                assert ui.state() == 'zoomed'
                switch(lambda: ui.notebook.select(0), 0)
                ui.state('normal')
                ui.update()
                assert (ui.winfo_width(), ui.winfo_height()) == minimal_size

            # Continuous worker text updates must not prevent a mode revealing.
            # Progress labels may resize afterward; the toolbar must stay fixed.
            progress_updates.clear()
            messages, feed_timer = [], [None]
            def feed_progress():
                message = 'working' if len(messages) % 2 else 'Processing a long batch ' * 5
                messages.append(message)
                ui.events.put({'kind': 'file_progress', 'completed': 1, 'total': 2,
                               'message': message})
                feed_timer[0] = ui.after(20, feed_progress)

            ui.notebook.select(1)
            feed_progress()
            deadline = time.monotonic() + 3
            try:
                while ui._mode_switch_alpha is not None:
                    ui.update()
                    if ui._mode_switch_alpha is not None:
                        assert not progress_updates, 'Worker events applied while hidden'
                    assert time.monotonic() < deadline, 'Progress updates prevented reveal'
                    time.sleep(0.005)
            finally:
                ui.after_cancel(feed_timer[0])
            assert len(messages) >= 3
            toolbar = ui.advanced.load_input_button.master
            toolbar_before = {str(w): reveal_geometry[-1][str(w)]
                              for w in (toolbar, *toolbar.winfo_children())}
            visible_until = time.monotonic() + 0.25
            while True:
                ui.update()
                assert toolbar_before == {str(w): w.winfo_geometry()
                                          for w in (toolbar, *toolbar.winfo_children())}
                caught_up = (ui.events.empty()
                             and ui.minimal.file_progress_var.get().endswith(messages[-1])
                             and ui.advanced.file_progress_var.get().endswith(messages[-1]))
                if caught_up and time.monotonic() >= visible_until:
                    break
                assert time.monotonic() < deadline, 'Queued progress was not delivered'
                time.sleep(0.005)
            assert progress_updates and all(math.isclose(alpha, 0.8)
                                            for alpha in progress_updates)
            assert ui.minimal.file_progress.cget('value') == 50
            assert ui.advanced.file_progress.cget('value') == 50
            switch(lambda: ui.notebook.select(0), 0)

            apply_size = ui._apply_window_size
            def fail_resize(_mode):
                raise RuntimeError('Cannot resize')
            ui._apply_window_size = fail_resize
            try:
                ui._begin_mode_switch(1)
            except RuntimeError as exc:
                assert str(exc) == 'Cannot resize'
            else:
                raise AssertionError('Resize error was suppressed')
            finally:
                ui._apply_window_size = apply_size
            settle()

            ui.notebook.select(1)
            layout_without_timers()
            pending_timer = ui._mode_switch_after_id
            assert pending_timer is not None
            ui._on_close()
            closed = True
            assert ui._mode_switch_after_id is None
            assert pending_timer not in ui.tk.splitlist(ui.tk.call('after', 'info'))
        finally:
            if not closed:
                ui._on_close()
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path), theme],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode == 77:
        pytest.skip(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
