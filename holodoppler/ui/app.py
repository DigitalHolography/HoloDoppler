from __future__ import annotations

import copy
import queue
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

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

from .advanced import AdvancedView
from .constants import APP_NAME
from .file_selection import expand_input_paths
from .image_utils import load_photo
from .minimal import MinimalView
from .paths import logo_path
from .settings_store import DEFAULT_WINDOW_MINSIZES, SettingsStore
from .theme import apply_theme


BaseTk = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk


class UI(BaseTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)

        self.store = SettingsStore()
        self.store.initialize()
        self.session_parameters = self.store.load_current_parameters()
        self.active_tab_name = self.store.active_tab()
        self.theme_name = self.store.theme()
        self.sun_valley_enabled = apply_theme(self, self.theme_name)

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
        self._apply_window_state(self.active_tab_name)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._register_drop_targets()
        self._sync_views()
        self.poll_after_id = self.after(60, self._poll_events)

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
        self.input_paths = selection.paths
        if self.input_paths:
            self.store.set_last_input_dir(self.input_paths[0].parent)
            self.store.remember_inputs(self.input_paths)
        self._sync_views()

        if selection.paths and selection.rejected:
            self._set_status(f"Loaded {len(selection.paths)} input file(s); ignored {len(selection.rejected)} unsupported or missing path(s).")
        elif selection.paths:
            self._set_status(f"Loaded {len(selection.paths)} input file(s)")
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
            self._set_status("Stopping after the current file finishes")

    def preview_path(self, path: Path) -> None:
        if self._busy():
            return
        try:
            parameters = copy.deepcopy(self.session_parameters)
        except Exception as exc:
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
            messagebox.showerror("Settings", str(exc), parent=self)
            return
        self.session_parameters = copy.deepcopy(data)
        self._set_status(status_message or f"Loaded settings: {self.store.current_parameters_label()}")

    def save_current_parameters(self, data: dict[str, Any]) -> None:
        try:
            saved_path = self.store.save_current_parameters(data)
            self.store.save_loaded_parameters(data)
        except Exception as exc:
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
            messagebox.showerror("Settings", str(exc), parent=self)
            return
        self.session_parameters = copy.deepcopy(data)
        self.advanced.refresh_parameter_choices(load_selected=True)
        self.minimal.set_parameter_label(self.store.current_parameters_label())
        self._set_status(f"Saved settings: {saved_path.name}")

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.minimal = MinimalView(self.notebook, self)
        self.advanced = AdvancedView(self.notebook, self, self.store, theme=self.theme_name)
        self.notebook.add(self.minimal, text="Minimal")
        self.notebook.add(self.advanced, text="Advanced")
        self.notebook.select(1 if self.active_tab_name == "advanced" else 0)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

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

                process(str(path), copy.deepcopy(parameters), progress_callback=on_progress)
                self.events.put({"kind": "file_progress", "completed": 1, "total": 1, "message": "File complete"})
                self.events.put({"kind": "batch_progress", "completed": index, "total": total_files})

            else:
                self.events.put({"kind": "status", "message": "Processing complete"})
        except Exception as exc:
            self.events.put({"kind": "error", "message": str(exc), "traceback": traceback.format_exc()})
        finally:
            self.events.put({"kind": "worker_done"})

    def _preview_worker(self, path: Path, parameters: dict[str, Any]) -> None:
        self.events.put({"kind": "preview_started", "path": path})
        try:
            image = preview(str(path), parameters, save_debug=False)
            self.events.put({"kind": "preview_result", "path": path, "image": image})
        except Exception as exc:
            self.events.put({"kind": "error", "message": str(exc), "traceback": traceback.format_exc()})
        finally:
            self.events.put({"kind": "worker_done"})

    def _poll_events(self) -> None:
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
            self.advanced.set_batch_progress(completed, total)
        elif kind == "preview_started":
            path = event["path"]
            self._set_status(f"Loading preview: {path.name}")
        elif kind == "preview_result":
            self.advanced.show_preview(event["path"], event["image"])
        elif kind == "status":
            self._set_status(str(event["message"]))
        elif kind == "error":
            log_path = self._write_error_log(str(event.get("traceback", "")))
            self._set_status("Error")
            message = str(event.get("message", "Unknown error"))
            if log_path is not None:
                message = f"{message}\n\nLog: {log_path}"
            messagebox.showerror("HoloDoppler", message, parent=self)
        elif kind == "worker_done":
            self.worker = None
            self.worker_kind = None
            self._sync_views()

    def _write_error_log(self, details: str) -> Path | None:
        if not details:
            return None
        try:
            log_dir = self.store.base_dir / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "ui-errors.log"
            timestamp = datetime.now().isoformat(timespec="seconds")
            with log_path.open("a", encoding="utf-8") as file:
                file.write(f"\n[{timestamp}]\n{details}\n")
            return log_path
        except OSError:
            return None

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

    def _on_tab_changed(self, _event: tk.Event) -> None:
        new_tab = self._current_tab_name()
        if new_tab == self.active_tab_name:
            return

        self.store.save_window_geometry(self.active_tab_name, self.geometry())
        self.active_tab_name = new_tab
        self.store.save_active_tab(new_tab)
        self._apply_window_state(new_tab)

    def _current_tab_name(self) -> str:
        return "advanced" if self.notebook.index("current") == 1 else "minimal"

    def _apply_window_state(self, tab_name: str) -> None:
        width, height = DEFAULT_WINDOW_MINSIZES.get(tab_name, DEFAULT_WINDOW_MINSIZES["minimal"])
        self.minsize(width, height)
        self.geometry(self.store.window_geometry(tab_name))

    def _on_close(self) -> None:
        self.store.save_window_state(self.active_tab_name, self.geometry())
        if self.poll_after_id is not None:
            try:
                self.after_cancel(self.poll_after_id)
            except tk.TclError:
                pass
            self.poll_after_id = None
        self.destroy()


def main() -> int:
    UI().mainloop()
    return 0
