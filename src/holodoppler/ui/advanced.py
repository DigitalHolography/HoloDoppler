from __future__ import annotations

from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from .image_utils import array_to_photo_image
from .settings_store import SettingsStore
from .theme import configure_plain_widget
from .widgets import RawJsonDialog, SettingsEditor


class AdvancedView(ttk.Frame):
    def __init__(self, master: tk.Misc, controller: object, store: SettingsStore, *, theme: str) -> None:
        super().__init__(master, padding=16)
        self.controller = controller
        self.store = store
        self.theme = theme
        self.status_var = tk.StringVar(value="Ready")
        self.preview_file_var = tk.StringVar()
        self.parameter_var = tk.StringVar()
        self.parameter_paths: dict[str, Path] = {}
        self.preview_image: tk.PhotoImage | None = None
        self._build()
        self.refresh_parameter_choices()

    @property
    def input_list_widget(self) -> tk.Listbox:
        return self.input_list

    @property
    def preview_target(self) -> ttk.Frame:
        return self.preview_frame

    def refresh_inputs(self, paths: list[Path]) -> None:
        self.input_list.delete(0, "end")
        for path in paths:
            self.input_list.insert("end", str(path))
        names = [path.name for path in paths]
        self.preview_combo.configure(values=names)
        if paths:
            self.preview_combo.current(0)
            self.preview_file_var.set(names[0])
        else:
            self.preview_file_var.set("")
            self.preview_label.configure(text="Load inputs to preview files.", image="")

    def set_busy(self, busy: bool, can_run: bool) -> None:
        state = "disabled" if busy else "normal"
        self.load_input_button.configure(state=state)
        self.clear_button.configure(state=state)
        self.import_button.configure(state=state)
        self.load_settings_button.configure(state=state)
        self.save_button.configure(state=state)
        self.save_as_button.configure(state=state)
        self.new_button.configure(state=state)
        self.raw_button.configure(state=state)
        self.preview_button.configure(state="disabled" if busy else "normal")
        self.run_button.configure(state="disabled" if busy or not can_run else "normal")
        self.stop_button.configure(state="normal" if busy else "disabled")

    def set_status(self, message: str) -> None:
        self.status_var.set(message)

    def set_current_file(self, index: int, total: int, path: Path) -> None:
        self.status_var.set(f"Processing {index}/{total}: {path.name}")
        self.file_progress.configure(value=0)

    def set_file_progress(self, completed: int, total: int) -> None:
        value = 0 if total <= 0 else max(0, min(100, completed / total * 100))
        self.file_progress.configure(value=value)

    def set_batch_progress(self, completed: int, total: int) -> None:
        value = 0 if total <= 0 else max(0, min(100, completed / total * 100))
        self.batch_progress.configure(value=value)

    def reset_progress(self) -> None:
        self.file_progress.configure(value=0)
        self.batch_progress.configure(value=0)

    def show_preview(self, path: Path, array: object) -> None:
        image = array_to_photo_image(array, (760, 460), self)
        if image is None:
            self.preview_image = None
            self.preview_label.configure(text=f"No preview available for {path.name}", image="")
            return
        self.preview_image = image
        self.preview_label.configure(image=image, text="")
        self.status_var.set(f"Preview loaded: {path.name}")

    def refresh_parameter_choices(self, *, load_selected: bool = False) -> None:
        files = self.store.parameter_files()
        self.parameter_paths = {path.name: path for path in files}
        self.parameter_combo.configure(values=list(self.parameter_paths))

        selected = self.store.selected_parameters_path()
        label = selected.name if selected.name in self.parameter_paths else self.store.current_parameters_label()
        self.parameter_var.set(label)
        try:
            data = self.store.load_selected_parameters() if load_selected else self.store.load_current_parameters()
            self.editor.load(data)
        except ValueError as exc:
            self.status_var.set(str(exc))

    def selected_preview_path(self) -> Path | None:
        index = self.preview_combo.current()
        paths = getattr(self.controller, "input_paths", [])
        if index < 0 or index >= len(paths):
            selection = self.input_list.curselection()
            if selection:
                index = selection[0]
        if 0 <= index < len(paths):
            return paths[index]
        return None

    def current_editor_values(self) -> dict:
        return self.editor.values()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        toolbar.columnconfigure(6, weight=1)

        self.load_input_button = ttk.Button(toolbar, text="Load input", command=self.controller.open_inputs_dialog)
        self.load_input_button.grid(row=0, column=0, padx=(0, 6))
        self.clear_button = ttk.Button(toolbar, text="Clear", command=self.controller.clear_inputs)
        self.clear_button.grid(row=0, column=1, padx=(0, 12))
        self.run_button = ttk.Button(toolbar, text="Run", command=self.controller.run_processing, style="Accent.TButton")
        self.run_button.grid(row=0, column=2, padx=(0, 6))
        self.stop_button = ttk.Button(toolbar, text="Stop", command=self.controller.stop_processing, state="disabled")
        self.stop_button.grid(row=0, column=3, padx=(0, 18))
        ttk.Label(toolbar, textvariable=self.status_var, style="Muted.TLabel").grid(row=0, column=6, sticky="e")

        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, sticky="nsew")
        self._build_inputs_preview_tab(notebook)
        self._build_settings_tab(notebook)

    def _build_inputs_preview_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=12)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=2)
        frame.rowconfigure(0, weight=1)
        notebook.add(frame, text="Inputs & Preview")

        list_panel = ttk.LabelFrame(frame, text="Inputs", padding=8)
        list_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(0, weight=1)

        list_frame = ttk.Frame(list_panel)
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.input_list = tk.Listbox(list_frame, activestyle="none", height=12)
        configure_plain_widget(self.input_list, self.theme)
        self.input_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.input_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.input_list.configure(yscrollcommand=scrollbar.set)
        self.input_list.bind("<<ListboxSelect>>", self._sync_preview_selection_from_list)

        preview_panel = ttk.LabelFrame(frame, text="Preview", padding=8)
        preview_panel.grid(row=0, column=1, sticky="nsew")
        preview_panel.columnconfigure(0, weight=1)
        preview_panel.rowconfigure(1, weight=1)

        controls = ttk.Frame(preview_panel)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        controls.columnconfigure(1, weight=1)
        ttk.Button(controls, text="Previous", command=self._select_previous_preview).grid(row=0, column=0, padx=(0, 6))
        self.preview_combo = ttk.Combobox(controls, textvariable=self.preview_file_var, state="readonly")
        self.preview_combo.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        self.preview_combo.bind("<<ComboboxSelected>>", self._sync_list_from_preview_selection)
        ttk.Button(controls, text="Next", command=self._select_next_preview).grid(row=0, column=2, padx=(0, 6))
        self.preview_button = ttk.Button(controls, text="Preview", command=self._preview_selected, style="Accent.TButton")
        self.preview_button.grid(row=0, column=3)

        self.preview_frame = ttk.Frame(preview_panel, style="Preview.TFrame", padding=12)
        self.preview_frame.grid(row=1, column=0, sticky="nsew")
        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_frame.rowconfigure(0, weight=1)
        self.preview_label = ttk.Label(self.preview_frame, text="Load inputs to preview files.", anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="nsew")

        progress = ttk.Frame(preview_panel)
        progress.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        progress.columnconfigure(0, weight=1)
        self.file_progress = ttk.Progressbar(progress, maximum=100, mode="determinate")
        self.file_progress.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.batch_progress = ttk.Progressbar(progress, maximum=100, mode="determinate")
        self.batch_progress.grid(row=1, column=0, sticky="ew")

    def _build_settings_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=12)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        notebook.add(frame, text="Settings")

        controls = ttk.Frame(frame)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="Settings").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.parameter_combo = ttk.Combobox(controls, textvariable=self.parameter_var, state="readonly")
        self.parameter_combo.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.parameter_combo.bind("<<ComboboxSelected>>", self._select_parameter)
        self.import_button = ttk.Button(controls, text="Import JSON", command=self._import_parameters)
        self.import_button.grid(row=0, column=2, padx=(0, 6))
        self.new_button = ttk.Button(controls, text="New custom", command=self._new_custom)
        self.new_button.grid(row=0, column=3, padx=(0, 6))
        self.load_settings_button = ttk.Button(controls, text="Load", command=self._load_current, style="Accent.TButton")
        self.load_settings_button.grid(row=0, column=4, padx=(0, 6))
        self.save_button = ttk.Button(controls, text="Save", command=self._save_current)
        self.save_button.grid(row=0, column=5, padx=(0, 6))
        self.save_as_button = ttk.Button(controls, text="Save as", command=self._save_as)
        self.save_as_button.grid(row=0, column=6, padx=(0, 6))
        self.raw_button = ttk.Button(controls, text="Edit JSON", command=self._edit_raw_json)
        self.raw_button.grid(row=0, column=7)

        self.editor = SettingsEditor(frame, theme=self.theme)
        self.editor.grid(row=1, column=0, sticky="nsew")

    def _sync_preview_selection_from_list(self, _event: tk.Event) -> None:
        selection = self.input_list.curselection()
        if selection:
            self.preview_combo.current(selection[0])

    def _sync_list_from_preview_selection(self, _event: tk.Event) -> None:
        index = self.preview_combo.current()
        if index >= 0:
            self.input_list.selection_clear(0, "end")
            self.input_list.selection_set(index)
            self.input_list.see(index)

    def _select_previous_preview(self) -> None:
        values = self.preview_combo.cget("values")
        if not values:
            return
        index = max(0, self.preview_combo.current() - 1)
        self.preview_combo.current(index)
        self._sync_list_from_preview_selection(tk.Event())

    def _select_next_preview(self) -> None:
        values = self.preview_combo.cget("values")
        if not values:
            return
        index = min(len(values) - 1, self.preview_combo.current() + 1)
        self.preview_combo.current(index)
        self._sync_list_from_preview_selection(tk.Event())

    def _preview_selected(self) -> None:
        path = self.selected_preview_path()
        if path is None:
            messagebox.showinfo("Preview", "Load an input file first.", parent=self)
            return
        self.controller.preview_path(path)

    def _select_parameter(self, _event: tk.Event) -> None:
        path = self.parameter_paths.get(self.parameter_var.get())
        if path is not None:
            self.controller.select_parameter_file(path)

    def _import_parameters(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Import parameter JSON",
            filetypes=[("JSON parameters", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.controller.import_parameter_file(Path(path))

    def _new_custom(self) -> None:
        name = simpledialog.askstring("New custom settings", "Name", parent=self)
        if not name:
            return
        try:
            data = self.current_editor_values()
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc), parent=self)
            return
        self.controller.save_parameters_as(name, data)

    def _load_current(self) -> None:
        try:
            data = self.current_editor_values()
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc), parent=self)
            return
        self.controller.load_session_parameters(data)

    def _save_current(self) -> None:
        try:
            data = self.current_editor_values()
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc), parent=self)
            return
        self.controller.save_current_parameters(data)

    def _save_as(self) -> None:
        name = simpledialog.askstring("Save settings as", "Name", parent=self)
        if not name:
            return
        try:
            data = self.current_editor_values()
        except ValueError as exc:
            messagebox.showerror("Invalid settings", str(exc), parent=self)
            return
        self.controller.save_parameters_as(name, data)

    def _edit_raw_json(self) -> None:
        try:
            data = self.current_editor_values()
        except ValueError:
            data = self.store.load_current_parameters()

        RawJsonDialog(
            self,
            title="Edit settings JSON",
            data=data,
            theme=self.theme,
            on_apply=self.editor.load,
        )
