from __future__ import annotations

import json
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Callable

from .theme import configure_plain_widget


class ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, *, theme: str) -> None:
        super().__init__(master)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        if theme == "light":
            self.canvas.configure(background="#f5f5f5")
        else:
            self.canvas.configure(background="#1f1f1f")

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_content_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _bind_mousewheel(self, _event: tk.Event) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event: tk.Event) -> None:
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-event.delta / 120), "units")


@dataclass
class ParameterField:
    key: str
    original: Any
    variable: tk.Variable | None = None
    text: tk.Text | None = None


class SettingsEditor(ttk.Frame):
    GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("Processing", ("batch_size", "batch_stride", "accumulation", "first_frame", "end_frame")),
        ("Optics", ("wavelength", "pixel_pitch", "spatial_propagation", "zero_padding", "z")),
        ("Registration", ("image_registration", "image_registration_type", "registration_", "apply_registration")),
        ("Shack-Hartmann", ("shack_hartmann",)),
        ("Frequency", ("temporal_transformation", "sampling_freq", "low_freq", "high_freq", "frequency_bands", "svd_threshold")),
        ("Output", ("square", "transpose", "flip_x", "flip_y", "debug")),
    )

    CHOICES: dict[str, tuple[str, ...]] = {
        "spatial_propagation": ("Fresnel", "AngularSpectrum", "None"),
        "image_registration_type": ("translation_rotation_scale", "translation"),
        "temporal_transformation": ("FourierTransform", "None"),
        "shack_hartmann_graph_ref": ("central_sub_ap", "ref_from_registration", "none"),
    }

    def __init__(self, master: tk.Misc, *, theme: str) -> None:
        super().__init__(master)
        self.theme = theme
        self.fields: dict[str, ParameterField] = {}
        self.scrollable = ScrollableFrame(self, theme=theme)
        self.scrollable.pack(fill="both", expand=True)

    def load(self, parameters: dict[str, Any]) -> None:
        for child in self.scrollable.content.winfo_children():
            child.destroy()
        self.fields.clear()

        grouped = self._group_parameters(parameters)
        for row, (group_name, items) in enumerate(grouped.items()):
            frame = ttk.LabelFrame(self.scrollable.content, text=group_name, padding=10)
            frame.grid(row=row, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))
            frame.columnconfigure(1, weight=1)
            for field_row, (key, value) in enumerate(items):
                ttk.Label(frame, text=key).grid(row=field_row, column=0, sticky="w", padx=(0, 12), pady=4)
                self._build_field(frame, field_row, key, value)

        self.scrollable.content.columnconfigure(0, weight=1)

    def values(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, field in self.fields.items():
            try:
                result[key] = self._field_value(field)
            except ValueError as exc:
                raise ValueError(f"{key}: {exc}") from exc
        return result

    def _build_field(self, parent: ttk.Frame, row: int, key: str, value: Any) -> None:
        field = ParameterField(key=key, original=value)
        if isinstance(value, bool):
            variable = tk.BooleanVar(value=value)
            control = ttk.Checkbutton(parent, variable=variable)
            field.variable = variable
        elif key in self.CHOICES:
            variable = tk.StringVar(value=str(value))
            control = ttk.Combobox(parent, textvariable=variable, values=self.CHOICES[key], state="normal")
            field.variable = variable
        elif isinstance(value, (list, dict)):
            control = ScrolledText(parent, height=3, wrap="word", font=("Consolas", 10))
            configure_plain_widget(control, self.theme)
            control.insert("1.0", json.dumps(value))
            field.text = control
        else:
            variable = tk.StringVar(value=str(value))
            control = ttk.Entry(parent, textvariable=variable)
            field.variable = variable

        control.grid(row=row, column=1, sticky="ew", pady=4)
        self.fields[key] = field

    def _field_value(self, field: ParameterField) -> Any:
        original = field.original
        if field.text is not None:
            raw_text = field.text.get("1.0", "end").strip()
            value = json.loads(raw_text or "null")
            if not isinstance(value, type(original)):
                raise ValueError(f"expected {type(original).__name__}")
            return value

        if isinstance(original, bool):
            return bool(field.variable.get()) if field.variable is not None else original

        raw_value = str(field.variable.get()).strip() if field.variable is not None else ""
        if isinstance(original, int):
            return int(float(raw_value))
        if isinstance(original, float):
            return float(raw_value)
        if original is None:
            return json.loads(raw_value)
        return raw_value

    def _group_parameters(self, parameters: dict[str, Any]) -> dict[str, list[tuple[str, Any]]]:
        grouped: dict[str, list[tuple[str, Any]]] = {name: [] for name, _patterns in self.GROUPS}
        grouped["Other"] = []

        for key, value in parameters.items():
            group_name = self._group_for_key(key)
            grouped[group_name].append((key, value))

        return {name: items for name, items in grouped.items() if items}

    def _group_for_key(self, key: str) -> str:
        for group_name, patterns in self.GROUPS:
            for pattern in patterns:
                if key == pattern or key.startswith(pattern):
                    return group_name
        return "Other"


class RawJsonDialog(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str,
        data: dict[str, Any],
        theme: str,
        on_apply: Callable[[dict[str, Any]], None],
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.geometry("720x560")
        self.minsize(560, 420)
        self.on_apply = on_apply

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.editor = ScrolledText(self, wrap="none", font=("Consolas", 10), undo=True)
        configure_plain_widget(self.editor, theme)
        self.editor.insert("1.0", json.dumps(data, indent=2))
        self.editor.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        button_row = ttk.Frame(self, padding=(12, 0, 12, 12))
        button_row.grid(row=1, column=0, sticky="ew")
        ttk.Button(button_row, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(button_row, text="Apply JSON", command=self._apply, style="Accent.TButton").pack(side="right", padx=(0, 8))

        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.editor.focus_set()

    def _apply(self) -> None:
        try:
            data = json.loads(self.editor.get("1.0", "end"))
        except json.JSONDecodeError as exc:
            messagebox.showerror("Invalid JSON", str(exc), parent=self)
            return
        if not isinstance(data, dict):
            messagebox.showerror("Invalid JSON", "The root value must be an object.", parent=self)
            return
        self.on_apply(data)
        self.destroy()
