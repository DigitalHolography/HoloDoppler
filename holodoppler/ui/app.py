from __future__ import annotations

import copy
import queue
import threading
from pathlib import Path
from typing import Any, Callable

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    DND_FILES = "DND_Files"
    TkinterDnD = None

from holodoppler.cli import preview, process
from holodoppler.logging import configure_logging, get_log_path, logger

from .advanced import AdvancedView
from .constants import APP_NAME
from .file_selection import expand_input_paths
from .image_utils import load_photo
from .log_window import LogWindow
from .minimal import MinimalView
from .paths import logo_path, get_package_version
from .settings_store import SettingsStore
from .theme import apply_theme


BaseTk = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk

_WINDOW_MINSIZES = {
    "minimal": (640, 500),
    "advanced": (980, 640),
}
_MODE_SWITCH_SETTLE_MS = 120


class _ModeNotebook(ttk.Notebook):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.before_select: Callable[[int], None] | None = None
        # Tk maps the selected page before <<NotebookTabChanged>> is handled.
        # Intercept the widget command so mouse, keyboard and Python selections
        # all prepare the window before that first layout.
        self._original_command = self._w + "_original"
        self.tk.call("rename", self._w, self._original_command)
        before_select = self._register(self._before_tab_select)
        # Keep widget errors in Tcl: theme palette updates deliberately catch
        # unsupported options. Python forwarding leaves a pending exception.
        self.tk.call(
            "interp", "alias", "", self._w, "", "apply",
            (("original", "before_select", "args"), """
                if {[llength $args] == 2 && [lindex $args 0] eq "select"} {
                    set index [$original index [lindex $args 1]]
                    set current [$original index current]
                    if {$index != $current && [$original tab $index -state] eq "normal"} {
                        $before_select $index
                    }
                }
                tailcall $original {*}$args
            """),
            self._original_command, before_select,
        )
        self._tclCommands.append(self._w)

    def _before_tab_select(self, index: str) -> None:
        if self.before_select is not None:
            self.before_select(int(index))


class UI(BaseTk):
    def __init__(self) -> None:
        configure_logging()
        super().__init__()
        self.withdraw()
        self.attributes("-alpha", 0.0)
        self.title(APP_NAME + get_package_version())

        self.store = SettingsStore()
        self.store.initialize()
        self.session_parameters = self.store.load_current_parameters()
        self.active_tab_name = self.store.active_tab()
        self.theme_name = self.store.theme()
        self.sun_valley_enabled = apply_theme(self, self.theme_name)
        self.log_window = LogWindow(self, theme=self.theme_name)

        self.logo_image = load_photo(logo_path(), (92, 92), self)
        self.icon_image = load_photo(logo_path(), (256, 256), self)
        if self.icon_image is not None:
            self.iconphoto(True, self.icon_image)

        self.input_paths: list[Path] = []
        self.events: queue.Queue[dict[str, Any]] = queue.Queue()
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.worker_kind: str | None = None
        self.poll_after_id: str | None = None

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._register_drop_targets()
        self._sync_views()
        self._preload_views()
        self._mode_switch_alpha: float | None = None
        self._mode_switch_after_id: str | None = None
        self._mode_switch_layout: tuple[tuple[str, str, int, int], ...] | None = None
        self.notebook.before_select = self._begin_mode_switch
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.bind("<Configure>", self._on_mode_layout, add="+")
        self.bind("<Map>", self._on_mode_layout, add="+")
        self.attributes("-alpha", 1.0)
        self.poll_after_id = self.after(60, self._poll_events)

    def toggle_logs(self) -> None:
        self.log_window.toggle()

    def report_callback_exception(self, exc_type, exc_value, exc_traceback) -> None:
        logger.error("GUI action failed", exc_info=(exc_type, exc_value, exc_traceback))
        self._handle_event({"kind": "error", "message": str(exc_value)})

    def open_inputs_dialog(self) -> None:
        selected = filedialog.askopenfilenames(
            parent=self,
            title="Load HoloDoppler input",
            initialdir=self.store.last_input_dir(),
            filetypes=[
                ("HoloDoppler inputs", "*.holo *.cine *.txt"),
                ("Hologram files", "*.holo"),
                ("Input lists", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        if selected:
            self.set_input_paths([Path(path) for path in selected])

    def clear_inputs(self) -> None:
        if self._busy():
            return
        self.input_paths = []
        self._sync_views()
        self._set_status("Inputs cleared")

    def set_input_paths(self, paths: list[Path]) -> None:
        selection = expand_input_paths(paths)
        self.input_paths = list(dict.fromkeys([*self.input_paths, *selection.paths]))
        if self.input_paths:
            self.store.set_last_input_dir(self.input_paths[-1].parent)
            self.store.remember_inputs(self.input_paths)
        self._sync_views()

        if selection.paths and selection.rejected:
            self._set_status(f"Loaded {len(self.input_paths)} input file(s); ignored {len(selection.rejected)} unsupported or missing path(s).")
        elif selection.paths:
            self._set_status(f"Loaded {len(self.input_paths)} input file(s)")
        else:
            self._set_status("No supported input files found")

    def run_processing(self) -> None:
        if self._busy():
            return
        if not self.input_paths:
            messagebox.showinfo("Run", "Drop a folder or load a .holo, .cine, or .txt input list first.", parent=self)
            return

        try:
            parameters = copy.deepcopy(self.session_parameters)
        except Exception as exc:
            logger.exception("Could not load processing settings")
            messagebox.showerror("Settings", str(exc), parent=self)
            return

        self.stop_event.clear()
        self._start_worker(
            kind="process",
            target=self._process_worker,
            args=(list(self.input_paths), parameters),
        )

    def stop_processing(self) -> None:
        if self.worker_kind == "process":
            self.stop_event.set()
            logger.info("Stopping after the current file finishes")
            self._set_status("Stopping after the current file finishes")

    def preview_path(self, path: Path) -> None:
        if self._busy():
            return
        try:
            parameters = copy.deepcopy(self.session_parameters)
        except Exception as exc:
            logger.exception("Could not load preview settings")
            messagebox.showerror("Settings", str(exc), parent=self)
            return
        self._start_worker(
            kind="preview",
            target=self._preview_worker,
            args=(path, parameters),
        )

    def select_parameter_file(self, path: Path) -> None:
        try:
            selected_path = self.store.select_parameters(path)
            data = self.store.load_parameters(selected_path)
            self.store.save_loaded_parameters(data)
        except Exception as exc:
            logger.exception("Could not select settings: %s", path)
            messagebox.showerror("Settings", str(exc), parent=self)
            return
        self.session_parameters = copy.deepcopy(data)
        self.advanced.refresh_parameter_choices(load_selected=True)
        self.minimal.set_parameter_label(self.store.current_parameters_label())
        self._set_status(f"Loaded settings: {selected_path.name}")

    def import_parameter_file(self, path: Path) -> None:
        try:
            imported_path = self.store.import_parameters(path)
            data = self.store.load_parameters(imported_path)
            self.store.save_loaded_parameters(data)
        except Exception as exc:
            logger.exception("Could not import settings: %s", path)
            messagebox.showerror("Settings", str(exc), parent=self)
            return
        self.session_parameters = copy.deepcopy(data)
        self.advanced.refresh_parameter_choices(load_selected=True)
        self.minimal.set_parameter_label(self.store.current_parameters_label())
        self._set_status(f"Imported and loaded settings: {imported_path.name}")

    def load_session_parameters(self, data: dict[str, Any], status_message: str | None = None) -> None:
        try:
            self.store.save_loaded_parameters(data)
        except Exception as exc:
            logger.exception("Could not load session settings")
            messagebox.showerror("Settings", str(exc), parent=self)
            return
        self.session_parameters = copy.deepcopy(data)
        self._set_status(status_message or f"Loaded settings: {self.store.current_parameters_label()}")

    def save_current_parameters(self, data: dict[str, Any]) -> None:
        try:
            saved_path = self.store.save_current_parameters(data)
            self.store.save_loaded_parameters(data)
        except Exception as exc:
            logger.exception("Could not save settings")
            messagebox.showerror("Settings", str(exc), parent=self)
            return
        self.session_parameters = copy.deepcopy(data)
        self.advanced.refresh_parameter_choices(load_selected=True)
        self.minimal.set_parameter_label(self.store.current_parameters_label())
        self._set_status(f"Saved settings: {saved_path.name}")

    def save_parameters_as(self, name: str, data: dict[str, Any]) -> None:
        try:
            saved_path = self.store.save_parameters_as(name, data)
            self.store.save_loaded_parameters(data)
        except Exception as exc:
            logger.exception("Could not save settings as %s", name)
            messagebox.showerror("Settings", str(exc), parent=self)
            return
        self.session_parameters = copy.deepcopy(data)
        self.advanced.refresh_parameter_choices(load_selected=True)
        self.minimal.set_parameter_label(self.store.current_parameters_label())
        self._set_status(f"Saved settings: {saved_path.name}")

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.notebook = _ModeNotebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.minimal = MinimalView(self.notebook, self)
        self.advanced = AdvancedView(self.notebook, self, self.store, theme=self.theme_name)
        self.notebook.add(self.minimal, text="Minimal")
        self.notebook.add(self.advanced, text="Advanced")
        self.notebook.select(1 if self.active_tab_name == "advanced" else 0)

    def _preload_views(self) -> None:
        # Map every page while transparent so Tk finishes its first layout
        # before the user can see it. A withdrawn window does not map children.
        self.update_idletasks()
        self.notebook.configure(width=self.minimal.winfo_reqwidth(), height=self.minimal.winfo_reqheight())
        self.update_idletasks()
        # Measure once while the requested size is current. During a rapid
        # switch Tk may not have processed the previous size request yet.
        self._notebook_chrome = (
            self.notebook.winfo_reqwidth() - int(self.notebook.cget("width")),
            self.notebook.winfo_reqheight() - int(self.notebook.cget("height")),
        )
        for tab_name, view in (("minimal", self.minimal), ("advanced", self.advanced)):
            self.notebook.select(view)
            self._apply_window_size(tab_name)
            self.deiconify()
            self.update()
            self._preload_notebooks(view)

        self.notebook.select(self.advanced if self.active_tab_name == "advanced" else self.minimal)
        self._apply_window_size(self.active_tab_name)
        self.update()

    def _preload_notebooks(self, parent: tk.Misc) -> None:
        for child in parent.winfo_children():
            if isinstance(child, ttk.Notebook):
                selected = child.select()
                for page in child.tabs():
                    child.select(page)
                    self.update()
                child.select(selected)
                self.update()
            self._preload_notebooks(child)

    def _register_drop_targets(self) -> None:
        if not DND_AVAILABLE:
            self._set_status("Drag and drop unavailable; install tkinterdnd2 to enable it")
            return

        for widget in (self, self.minimal.drop_target, self.advanced.input_list_widget, self.advanced.preview_target):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event: tk.Event) -> None:
        dropped = [Path(path) for path in self.tk.splitlist(event.data)]
        if dropped:
            self.set_input_paths(dropped)

    def _start_worker(self, *, kind: str, target: Any, args: tuple[Any, ...]) -> None:
        if self._busy():
            return
        self.worker_kind = kind
        self.worker = threading.Thread(target=target, args=args, daemon=True)
        self.worker.start()
        self._sync_views()

    def _process_worker(self, paths: list[Path], parameters: dict[str, Any]) -> None:
        total_files = len(paths)
        pulse_not_detected_paths: list[Path] = []
        self.events.put({"kind": "process_started", "total": total_files})
        try:
            for index, path in enumerate(paths, start=1):
                if self.stop_event.is_set():
                    self.events.put({"kind": "status", "message": "Stopped"})
                    break

                self.events.put({"kind": "file_started", "index": index, "total": total_files, "path": path})

                def on_progress(completed: int, total: int, message: str = "") -> None:
                    self.events.put(
                        {
                            "kind": "file_progress",
                            "completed": completed,
                            "total": total,
                            "message": message,
                        }
                    )

                pulse_not_detected = False

                def on_warning(code: str, _message: str) -> None:
                    nonlocal pulse_not_detected
                    if code == "cardiac_pulse_not_detected":
                        pulse_not_detected = True

                results = process(
                    str(path),
                    copy.deepcopy(parameters),
                    progress_callback=on_progress,
                    warning_callback=on_warning,
                )
                if pulse_not_detected:
                    pulse_not_detected_paths.append(path)
                image = self._first_m0_frame(results)
                del results
                self.events.put({"kind": "processed_preview", "path": path, "image": image})
                completion_message = (
                    "File complete (pulse not detected)"
                    if pulse_not_detected
                    else "File complete"
                )
                self.events.put(
                    {
                        "kind": "file_progress",
                        "completed": 1,
                        "total": 1,
                        "message": completion_message,
                    }
                )
                self.events.put(
                    {
                        "kind": "batch_progress",
                        "completed": index,
                        "total": total_files,
                        "pulse_not_detected": pulse_not_detected,
                    }
                )

            else:
                if pulse_not_detected_paths:
                    self.events.put(
                        {
                            "kind": "pulse_detection_summary",
                            "paths": pulse_not_detected_paths,
                        }
                    )
                else:
                    self.events.put({"kind": "status", "message": "Processing complete"})
        except Exception as exc:
            logger.exception("Processing failed")
            self.events.put({"kind": "error", "message": str(exc)})
        finally:
            self.events.put({"kind": "worker_done"})

    @staticmethod
    def _first_m0_frame(results: object) -> object | None:
        if not isinstance(results, dict):
            return None

        import numpy as np

        for name in (
            "M0",
            "moment_0",
            "moment0",
            "M0ff",
            "moment_0_ff",
            "moment0ff",
            "Projection",
            "Projectionff",
        ):
            if name not in results:
                continue
            frame = np.asarray(results[name])
            if frame.size == 0:
                continue
            if np.iscomplexobj(frame):
                frame = np.abs(frame)
            while frame.ndim > 2:
                frame = frame[0]
            if frame.ndim == 2:
                return frame.copy()
        return None

    def _preview_worker(self, path: Path, parameters: dict[str, Any]) -> None:
        self.events.put({"kind": "preview_started", "path": path})
        try:
            image = preview(str(path), parameters)
            self.events.put({"kind": "preview_result", "path": path, "image": image})
        except Exception as exc:
            logger.exception("Preview failed: %s", path)
            self.events.put({"kind": "error", "message": str(exc)})
        finally:
            self.events.put({"kind": "worker_done"})

    def _poll_events(self) -> None:
        # The worker keeps running, but its queued text/image updates can
        # change requested sizes continuously. Apply them after the mode is
        # visible so they cannot keep the layout from ever becoming stable.
        if self._mode_switch_alpha is None:
            try:
                while True:
                    event = self.events.get_nowait()
                    self._handle_event(event)
            except queue.Empty:
                pass
        self.poll_after_id = self.after(60, self._poll_events)

    def _handle_event(self, event: dict[str, Any]) -> None:
        kind = event.get("kind")
        if kind == "process_started":
            self.minimal.reset_progress()
            self.advanced.reset_progress()
            self._set_status("Processing started")
        elif kind == "file_started":
            index = int(event["index"])
            total = int(event["total"])
            path = event["path"]
            self.minimal.set_current_file(index, total, path)
            self.advanced.set_current_file(index, total, path)
            self._set_status(f"Processing {index}/{total}: {path.name}")
        elif kind == "file_progress":
            completed = int(event["completed"])
            total = int(event["total"])
            message = str(event.get("message") or "")
            self.minimal.set_file_progress(completed, total, message)
            self.advanced.set_file_progress(completed, total, message)
        elif kind == "batch_progress":
            completed = int(event["completed"])
            total = int(event["total"])
            self.minimal.set_batch_progress(completed, total)
            if event.get("pulse_not_detected", False):
                self.advanced.set_file_pulse_not_detected(completed)
            else:
                self.advanced.set_file_completed(completed)
            self.advanced.set_batch_progress(completed, total)
        elif kind == "processed_preview":
            self.advanced.show_processed_preview(event["path"], event.get("image"))
        elif kind == "preview_started":
            path = event["path"]
            self._set_status(f"Loading preview: {path.name}")
        elif kind == "preview_result":
            self.advanced.show_preview(event["path"], event["image"])
        elif kind == "status":
            self._set_status(str(event["message"]))
        elif kind == "pulse_detection_summary":
            paths = [Path(path) for path in event.get("paths", [])]
            self._set_status(
                f"Processing complete; pulse not detected in {len(paths)} file(s)"
            )
            file_list = "\n".join(f"- {path}" for path in paths)
            messagebox.showwarning(
                "Cardiac pulse not detected",
                "No valid cardiac pulse was detected in:\n\n"
                f"{file_list}\n\n"
                "All other results, including long-time spectrograms, were saved.",
                parent=self,
            )
        elif kind == "error":
            log_path = get_log_path()
            self._set_status("Error")
            message = str(event.get("message", "Unknown error"))
            if log_path is not None:
                message = f"{message}\n\nLog: {log_path}"
            messagebox.showerror("HoloDoppler", message, parent=self)
        elif kind == "worker_done":
            self.worker = None
            self.worker_kind = None
            self._sync_views()

    def _sync_views(self) -> None:
        busy = self._busy()
        can_run = bool(self.input_paths)
        self.minimal.refresh_inputs(self.input_paths)
        self.advanced.refresh_inputs(self.input_paths)
        self.minimal.set_parameter_label(self.store.current_parameters_label())
        self.minimal.set_busy(busy, can_run)
        self.advanced.set_busy(busy, can_run)

    def _set_status(self, message: str) -> None:
        self.minimal.set_status(message)
        self.advanced.set_status(message)

    def _busy(self) -> bool:
        return self.worker is not None and self.worker.is_alive()

    def _begin_mode_switch(self, index: int) -> None:
        # Keep the window mapped so Tk can lay out and paint the new page,
        # but hide both the old page's resize and the new page's first redraw.
        if self._mode_switch_alpha is None:
            self._mode_switch_alpha = float(self.attributes("-alpha"))
            self.attributes("-alpha", 0.0)
        self._cancel_mode_reveal()
        self._mode_switch_layout = None
        try:
            self._apply_window_size("advanced" if index == 1 else "minimal")
        except Exception:
            self._reveal_mode()
            raise

    def _on_mode_layout(self, _event: tk.Event) -> None:
        # Grid/notebook layouts can settle from the outside in: buttons may
        # still move after their top-level page has stopped changing. The root
        # bind tag receives all its descendants, but not separate log/dialog
        # windows. Progressbar redraws do not generate these geometry events.
        if self._mode_switch_alpha is not None:
            self._schedule_mode_reveal()

    def _cancel_mode_reveal(self) -> None:
        if self._mode_switch_after_id is not None:
            self.after_cancel(self._mode_switch_after_id)
            self._mode_switch_after_id = None

    def _schedule_mode_reveal(self) -> None:
        self._cancel_mode_reveal()
        self._mode_switch_after_id = self.after(_MODE_SWITCH_SETTLE_MS, self._queue_mode_reveal)

    def _queue_mode_reveal(self) -> None:
        # A busy callback can make the timer due before pending layout events
        # are handled. Allow an idle layout pass and then another event-loop
        # turn for the native resize events generated by that layout.
        self._mode_switch_after_id = self.after_idle(self._finish_mode_layout)

    def _finish_mode_layout(self) -> None:
        layout = self._mode_layout_signature()
        if layout != self._mode_switch_layout:
            # A quiet outer window does not imply a finished nested layout.
            # Require unchanged actual AND requested sizes across a complete
            # quiet interval, allowing further grid passes to finish hidden.
            self._mode_switch_layout = layout
            self._schedule_mode_reveal()
        else:
            self._mode_switch_after_id = self.after(0, self._reveal_mode_if_stable)

    def _mode_layout_signature(self) -> tuple[tuple[str, str, int, int], ...]:
        layout = []
        pending: list[tk.Misc] = [self]
        while pending:
            widget = pending.pop()
            if widget.winfo_toplevel() != self or not widget.winfo_viewable():
                continue
            layout.append((
                str(widget), widget.winfo_geometry(),
                widget.winfo_reqwidth(), widget.winfo_reqheight(),
            ))
            pending.extend(widget.winfo_children())
        return tuple(layout)

    def _reveal_mode_if_stable(self) -> None:
        if self._mode_layout_signature() != self._mode_switch_layout:
            self._schedule_mode_reveal()
        else:
            self._reveal_mode()

    def _reveal_mode(self) -> None:
        self._cancel_mode_reveal()
        if self._mode_switch_alpha is not None:
            self.attributes("-alpha", self._mode_switch_alpha)
            self._mode_switch_alpha = None
        self._mode_switch_layout = None

    def _on_tab_changed(self, _event: tk.Event) -> None:
        if self._mode_switch_alpha is not None:
            self._schedule_mode_reveal()
        new_tab = self._current_tab_name()
        if new_tab == self.active_tab_name:
            return

        self.active_tab_name = new_tab
        self.store.save_active_tab(new_tab)

    def _current_tab_name(self) -> str:
        return "advanced" if self.notebook.index("current") == 1 else "minimal"

    def _apply_window_size(self, tab_name: str) -> None:
        view = self.advanced if tab_name == "advanced" else self.minimal
        # Notebook normally requests the largest of all its pages. Use only
        # this mode's content so the advanced controls do not enlarge minimal.
        chrome_width, chrome_height = self._notebook_chrome
        content_width, content_height = view.winfo_reqwidth(), view.winfo_reqheight()
        self.notebook.configure(width=content_width, height=content_height)

        available_width = max(1, self.winfo_screenwidth() - 40)
        available_height = max(1, self.winfo_screenheight() - 80)
        min_width, min_height = _WINDOW_MINSIZES[tab_name]
        min_width = min(min_width, available_width)
        min_height = min(min_height, available_height)
        width = min(max(content_width + chrome_width, min_width), available_width)
        height = min(max(content_height + chrome_height, min_height), available_height)
        self.minsize(min_width, min_height)
        self.geometry(f"{width}x{height}")

    def _on_close(self) -> None:
        self.store.save_active_tab(self.active_tab_name)
        self._cancel_mode_reveal()
        if self.poll_after_id is not None:
            try:
                self.after_cancel(self.poll_after_id)
            except tk.TclError:
                pass
            self.poll_after_id = None
        self.log_window.close()
        self.destroy()


def main() -> int:
    UI().mainloop()
    return 0
