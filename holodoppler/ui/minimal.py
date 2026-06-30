from __future__ import annotations

from pathlib import Path

import tkinter as tk
from tkinter import ttk

from .constants import APP_NAME


class MinimalView(ttk.Frame):
    def __init__(self, master: tk.Misc, controller: object) -> None:
        super().__init__(master, padding=22)
        self.controller = controller
        self.file_count_var = tk.StringVar(value="No input selected")
        self.file_detail_var = tk.StringVar(value="Drop a .holo, .cine, or .txt list here.")
        self.status_var = tk.StringVar(value="Ready")
        self.current_file_var = tk.StringVar(value="")
        self.file_progress_var = tk.StringVar(value="File progress")
        self.batch_progress_var = tk.StringVar(value="Batch progress")
        self._build()

    @property
    def drop_target(self) -> ttk.Frame:
        return self.drop_frame

    def refresh_inputs(self, paths: list[Path]) -> None:
        if not paths:
            self.file_count_var.set("No input selected")
            self.file_detail_var.set("Drop a .holo, .cine, or .txt list here.")
            self.current_file_var.set("")
            self._set_batch_visible(False)
            return

        self.file_count_var.set(f"{len(paths)} input file{'s' if len(paths) != 1 else ''} selected")
        self.file_detail_var.set(str(paths[0]) if len(paths) == 1 else f"First file: {paths[0]}")
        self._set_batch_visible(len(paths) > 1)

    def set_parameter_label(self, _label: str) -> None:
        return

    def set_busy(self, busy: bool, can_run: bool) -> None:
        self.load_button.configure(state="disabled" if busy else "normal")
        is_processing = busy and getattr(self.controller, "worker_kind", None) == "process"

        if is_processing:
            self.action_button.configure(
                text="Stop",
                command=self.controller.stop_processing,
                state="normal",
                style="TButton",
            )
            return

        self.action_button.configure(
            text="Run",
            command=self.controller.run_processing,
            state="disabled" if busy or not can_run else "normal",
            style="Accent.TButton",
        )

    def set_status(self, message: str) -> None:
        self.status_var.set(message)

    def reset_progress(self) -> None:
        self.file_progress.configure(value=0)
        self.batch_progress.configure(value=0)
        self.file_progress_var.set("File progress")
        self.batch_progress_var.set("Batch progress")

    def set_current_file(self, index: int, total: int, path: Path) -> None:
        self.current_file_var.set(f"{index}/{total}: {path.name}")
        self.file_progress_var.set("File progress")
        self.file_progress.configure(value=0)

    def set_file_progress(self, completed: int, total: int) -> None:
        percent = 0 if total <= 0 else max(0, min(100, completed / total * 100))
        self.file_progress.configure(value=percent)
        self.file_progress_var.set(f"File progress: {completed}/{total}" if total > 0 else "File progress")

    def set_batch_progress(self, completed: int, total: int) -> None:
        percent = 0 if total <= 0 else max(0, min(100, completed / total * 100))
        self.batch_progress.configure(value=percent)
        self.batch_progress_var.set(f"Batch progress: {completed}/{total}" if total > 1 else "Batch progress")

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(6, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text=APP_NAME, font=("Segoe UI", 30, "bold"), anchor="center").grid(
            row=0, column=0, sticky="ew"
        )
        logo = getattr(self.controller, "logo_image", None)
        if logo is not None:
            ttk.Label(header, image=logo, anchor="center").grid(row=1, column=0, sticky="ew", pady=(10, 0))

        self.load_button = ttk.Button(self, text="Load input", command=self.controller.open_inputs_dialog)
        self.load_button.grid(row=1, column=0, pady=(0, 12))

        self.drop_frame = ttk.Frame(self, style="Drop.TFrame", padding=16)
        self.drop_frame.grid(row=2, column=0, sticky="ew", padx=56, pady=(0, 16))
        self.drop_frame.columnconfigure(0, weight=1)

        ttk.Label(self.drop_frame, textvariable=self.file_count_var, style="Section.TLabel", anchor="center").grid(
            row=0, column=0, sticky="ew", pady=(0, 4)
        )
        ttk.Label(self.drop_frame, textvariable=self.file_detail_var, anchor="center", wraplength=540).grid(
            row=1, column=0, sticky="ew"
        )

        self.action_button = ttk.Button(self, text="Run", command=self.controller.run_processing, style="Accent.TButton")
        self.action_button.grid(row=3, column=0, pady=(0, 12))

        progress = ttk.Frame(self)
        progress.grid(row=4, column=0, sticky="ew", padx=56)
        progress.columnconfigure(0, weight=1)

        ttk.Label(progress, textvariable=self.current_file_var, style="Muted.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        ttk.Label(progress, textvariable=self.file_progress_var).grid(row=1, column=0, sticky="w")
        self.file_progress = ttk.Progressbar(progress, maximum=100, mode="determinate")
        self.file_progress.grid(row=2, column=0, sticky="ew", pady=(4, 10))

        self.batch_frame = ttk.Frame(progress)
        self.batch_frame.grid(row=3, column=0, sticky="ew")
        self.batch_frame.columnconfigure(0, weight=1)
        ttk.Label(self.batch_frame, textvariable=self.batch_progress_var).grid(row=0, column=0, sticky="w")
        self.batch_progress = ttk.Progressbar(self.batch_frame, maximum=100, mode="determinate")
        self.batch_progress.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self._set_batch_visible(False)

        ttk.Label(self, textvariable=self.status_var, style="Muted.TLabel", anchor="center").grid(
            row=5, column=0, sticky="ew", pady=(16, 0)
        )

    def _set_batch_visible(self, visible: bool) -> None:
        if visible:
            self.batch_frame.grid()
        else:
            self.batch_frame.grid_remove()
