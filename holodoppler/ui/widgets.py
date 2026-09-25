from __future__ import annotations

import json
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Callable

import yaml

from .theme import configure_plain_widget


PIPELINE_PARAMETER_KEY = "pipeline_name"


@dataclass
class ParameterField:
    key: str
    original: Any
    value: Any
    item_id: str


class SettingsEditor(ttk.Frame):
    GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "Processing",
            (
                "pipeline_name",
                "batch_size",
                "batch_stride",
                "accumulation",
                "time_window",
                "time_stride",
                "time_slide",
                "sh_time_accumulation",
                "num_workers",
                "first_frame",
                "end_frame",
            ),
        ),
        ("Optics", ("wavelength", "pixel_pitch", "spatial_propagation", "zero_padding", "z")),
        ("Registration", ("image_registration", "image_registration_type", "registration_", "apply_registration")),
        ("Shack-Hartmann", ("shack_hartmann",)),
        ("Spectrograms", ("spectral_cube_enabled", "spectral_cube_settings")),
        (
            "Frequency",
            (
                "temporal_transformation",
                "time_transform",
                "sampling_freq",
                "low_freq",
                "high_freq",
                "frequency_bands",
                "f_bins",
                "spectral_cube_signal_",
                "spectral_cube_corner_",
                "spectral_endpoints_",
                "filter2d",
                "pca_",
                "svd_",
            ),
        ),
        (
            "Output",
            (
                "saving_to_folder",
                "square",
                "transpose",
                "flip_x",
                "flip_y",
                "contrast",
                "smoothing",
                "debug",
            ),
        ),
    )

    CHOICES: dict[str, tuple[str, ...]] = {
        "spatial_propagation": ("Fresnel", "AngularSpectrum", "None"),
        "image_registration_type": ("translation_rotation_scale", "translation"),
        "temporal_transformation": ("FourierTransform", "None"),
        "shack_hartmann_graph_ref": ("central_sub_ap", "ref_from_registration", "none"),
    }

    def __init__(self, master: tk.Misc, *, theme: str, on_apply: Callable[[dict[str, Any]], None] | None = None) -> None:
        super().__init__(master)
        self.theme = theme
        self.on_apply = on_apply
        self.fields: dict[str, ParameterField] = {}
        self.selected_key: str | None = None
        self.value_variable: tk.Variable | None = None
        self.value_text: tk.Text | None = None
        self._build()

    def load(self, parameters: dict[str, Any]) -> None:
        self.fields = {
            key: ParameterField(key=key, original=value, value=value, item_id="")
            for key, value in parameters.items()
        }
        self._rebuild_tree()

    def values(self) -> dict[str, Any]:
        self._apply_current_editor(silent=True)
        return {key: field.value for key, field in self.fields.items()}

    def _rebuild_tree(self, preferred_key: str | None = None) -> None:
        self.tree.delete(*self.tree.get_children())
        self.selected_key = None
        for field in self.fields.values():
            field.item_id = ""

        visible_keys = self._visible_parameter_keys()
        grouped = self._group_parameters(
            {
                key: field.value
                for key, field in self.fields.items()
                if key in visible_keys
            }
        )
        first_item: str | None = None
        preferred_item: str | None = None
        for group_name, items in grouped.items():
            group_id = self.tree.insert(
                "",
                "end",
                text=group_name,
                values=("",),
                open=True,
                tags=("group",),
            )
            for key, value in items:
                item_id = self.tree.insert(
                    group_id,
                    "end",
                    text=key,
                    values=(self._display_field_value(key, value),),
                    tags=("parameter",),
                )
                self.fields[key].item_id = item_id
                first_item = first_item or item_id
                if key == preferred_key:
                    preferred_item = item_id

        self._clear_editor("Select a parameter to edit it.")
        selected_item = preferred_item or first_item
        if selected_item is not None:
            self.tree.selection_set(selected_item)
            self.tree.focus(selected_item)
            self.tree.see(selected_item)
            self._show_selected_editor()

    def _visible_parameter_keys(self) -> set[str]:
        parameters = {key: field.value for key, field in self.fields.items()}
        return {
            key
            for key in self.fields
            if parameter_is_visible(key, parameters)
        }

    def _add_parameter(self) -> None:
        key = simpledialog.askstring(
            "Add parameter",
            "Parameter name",
            parent=self,
        )
        if key is None:
            return
        key = key.strip()
        if not key:
            messagebox.showerror("Invalid parameter", "The parameter name cannot be empty.", parent=self)
            return
        if key in self.fields:
            messagebox.showerror("Invalid parameter", f"{key!r} already exists.", parent=self)
            return

        raw_value = simpledialog.askstring(
            "Add parameter",
            "Value (YAML or JSON syntax)",
            initialvalue="null",
            parent=self,
        )
        if raw_value is None:
            return
        try:
            value = parse_parameter_value(raw_value)
        except ValueError as exc:
            messagebox.showerror("Invalid parameter value", str(exc), parent=self)
            return

        self.fields[key] = ParameterField(key=key, original=value, value=value, item_id="")
        self._rebuild_tree(preferred_key=key)
        if self.on_apply is not None:
            self.on_apply({name: field.value for name, field in self.fields.items()})

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0, minsize=260)
        self.rowconfigure(0, weight=1)

        table_frame = ttk.Frame(self)
        table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(1, weight=1)

        table_controls = ttk.Frame(table_frame)
        table_controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(
            table_controls,
            text="Add parameter",
            command=self._add_parameter,
        ).pack(side="left")
        ttk.Label(
            table_controls,
            text="Values accept YAML or JSON syntax",
            style="Muted.TLabel",
        ).pack(side="left", padx=(10, 0))

        self.tree = ttk.Treeview(table_frame, columns=("value",), show=("tree", "headings"), selectmode="browse")
        self.tree.heading("#0", text="Parameter")
        self.tree.heading("value", text="Value")
        self.tree.column("#0", minwidth=220, width=360, stretch=True)
        self.tree.column("value", minwidth=220, width=420, stretch=True)
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._focus_editor)
        self.tree.tag_configure("group", font=("Segoe UI", 10, "bold"))

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        y_scroll.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=y_scroll.set)

        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        x_scroll.grid(row=2, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=x_scroll.set)

        self.editor_frame = ttk.LabelFrame(self, text="Value", padding=8)
        self.editor_frame.grid(row=0, column=1, sticky="nsew")
        self.editor_frame.configure(width=260)
        self.editor_frame.grid_propagate(False)
        self.editor_frame.columnconfigure(0, weight=1)
        self.editor_frame.rowconfigure(1, weight=1)

        self.selected_label = ttk.Label(
            self.editor_frame,
            text="Select a parameter to edit it.",
            style="Muted.TLabel",
            wraplength=220,
        )
        self.selected_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.editor_host = ttk.Frame(self.editor_frame)
        self.editor_host.grid(row=1, column=0, sticky="nsew")
        self.editor_host.columnconfigure(0, weight=1)
        self.editor_host.rowconfigure(0, weight=1)

        self.apply_button = ttk.Button(self.editor_frame, text="Apply", command=self._apply_current_editor)
        self.apply_button.grid(row=2, column=0, sticky="e", pady=(10, 0))
        self.apply_button.configure(state="disabled")

    def _on_tree_select(self, _event: tk.Event) -> None:
        try:
            self._apply_current_editor(silent=True)
        except ValueError:
            pass
        self._show_selected_editor()

    def _show_selected_editor(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self._clear_editor("Select a parameter to edit it.")
            return

        item_id = selection[0]
        key = self.tree.item(item_id, "text")
        if key not in self.fields:
            self._clear_editor("Select a parameter row to edit it.")
            return

        field = self.fields[key]
        self.selected_key = key
        self.selected_label.configure(text=key)
        self.apply_button.configure(state="normal")
        self._clear_editor_controls()

        value = field.value
        if isinstance(field.original, bool):
            variable = tk.BooleanVar(value=bool(value))
            control = ttk.Checkbutton(self.editor_host, text="Enabled", variable=variable)
            self.value_variable = variable
        elif self._has_choices(key):
            pairs = list(self._choice_pairs(key))
            raw_value = str(value)
            if raw_value not in {choice_value for choice_value, _label in pairs}:
                pairs.append((raw_value, raw_value))
            variable = tk.StringVar(value=self._choice_label_for_value(key, raw_value, pairs=pairs))
            state = "readonly" if key == PIPELINE_PARAMETER_KEY else "normal"
            control = ttk.Combobox(
                self.editor_host,
                textvariable=variable,
                values=tuple(label for _choice_value, label in pairs),
                state=state,
            )
            self.value_variable = variable
        elif isinstance(field.original, (list, dict)):
            control = ScrolledText(self.editor_host, height=6, wrap="word", font=("Consolas", 10))
            configure_plain_widget(control, self.theme)
            control.insert("1.0", json.dumps(value, indent=2))
            self.value_text = control
        else:
            variable = tk.StringVar(value=self._display_value(value))
            control = ttk.Entry(self.editor_host, textvariable=variable)
            control.bind("<Return>", lambda _event: self._apply_current_editor())
            self.value_variable = variable

        sticky = "nsew" if isinstance(field.original, (list, dict)) else "new"
        control.grid(row=0, column=0, sticky=sticky)
        control.focus_set()

    def _apply_current_editor(self, silent: bool = False) -> None:
        if self.selected_key is None or self.selected_key not in self.fields:
            return

        field = self.fields[self.selected_key]
        visible_before = self._visible_parameter_keys()
        try:
            field.value = self._editor_value(field)
            field.original = field.value
        except ValueError as exc:
            if silent:
                raise ValueError(f"{field.key}: {exc}") from exc
            messagebox.showerror("Invalid settings", f"{field.key}: {exc}", parent=self)
            return
        if visible_before != self._visible_parameter_keys():
            self._rebuild_tree(preferred_key=field.key)
        elif field.item_id:
            self.tree.set(field.item_id, "value", self._display_field_value(field.key, field.value))
        if not silent and self.on_apply is not None:
            self.on_apply({key: item.value for key, item in self.fields.items()})

    def _editor_value(self, field: ParameterField) -> Any:
        original = field.original
        if self.value_text is not None:
            raw_text = self.value_text.get("1.0", "end").strip()
            return parse_parameter_value(raw_text)

        if isinstance(original, bool):
            return bool(self.value_variable.get()) if self.value_variable is not None else original

        raw_value = str(self.value_variable.get()).strip() if self.value_variable is not None else ""
        if self._has_choices(field.key):
            return self._choice_value_for_label(field.key, raw_value)
        return parse_parameter_value(raw_value)

    def _clear_editor(self, message: str) -> None:
        self.selected_key = None
        self.selected_label.configure(text=message)
        self.apply_button.configure(state="disabled")
        self._clear_editor_controls()

    def _clear_editor_controls(self) -> None:
        for child in self.editor_host.winfo_children():
            child.destroy()
        self.value_variable = None
        self.value_text = None

    def _focus_editor(self, _event: tk.Event) -> None:
        for child in self.editor_host.winfo_children():
            child.focus_set()
            break

    def _display_value(self, value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        if isinstance(value, (list, dict)):
            return json.dumps(value, separators=(",", ":"))
        return str(value)

    def _display_field_value(self, key: str, value: Any) -> str:
        if key == PIPELINE_PARAMETER_KEY:
            return self._choice_label_for_value(key, str(value))
        return self._display_value(value)

    def _has_choices(self, key: str) -> bool:
        return key == PIPELINE_PARAMETER_KEY or key in self.CHOICES

    def _choice_pairs(self, key: str) -> tuple[tuple[str, str], ...]:
        if key == PIPELINE_PARAMETER_KEY:
            return _pipeline_choice_pairs()
        return tuple((value, value) for value in self.CHOICES[key])

    def _choice_label_for_value(
        self,
        key: str,
        value: str,
        pairs: list[tuple[str, str]] | tuple[tuple[str, str], ...] | None = None,
    ) -> str:
        for choice_value, label in pairs or self._choice_pairs(key):
            if choice_value == value:
                return label
        return value

    def _choice_value_for_label(self, key: str, label: str) -> str:
        for choice_value, choice_label in self._choice_pairs(key):
            if choice_label == label or choice_value == label:
                return choice_value
        return label

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


def parse_parameter_value(raw_text: str) -> Any:
    """Parse one editor value using the YAML/JSON scalar rules."""
    if not raw_text.strip():
        return ""
    try:
        return yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML/JSON value: {exc}") from exc


def parameter_is_visible(key: str, parameters: dict[str, Any]) -> bool:
    """Return whether a parameter is relevant under the current feature toggles."""
    if key.startswith("registration_ecc_"):
        return not _setting_is_off(parameters, "image_registration_with_ecc")
    if key.startswith("registration_") or key in {
        "image_registration_type",
        "batch_size_registration",
        "apply_registration",
    }:
        return not _setting_is_off(parameters, "image_registration")
    if key.startswith("filter2d_"):
        return not _setting_is_off(parameters, "filter2d")
    if key.startswith("contrast_"):
        return not _setting_is_off(parameters, "contrast")
    if key == "spectral_cube_settings":
        return not _setting_is_off(parameters, "spectral_cube_enabled")
    if key.startswith("svd_") and key != "svd_filtering":
        return not _setting_is_off(parameters, "svd_filtering")
    if key.startswith("shack_hartmann_") and key != "shack_hartmann_autofocus":
        controllers = [
            parameters[name]
            for name in ("shack_hartmann", "shack_hartmann_autofocus")
            if name in parameters
        ]
        return not controllers or any(bool(value) for value in controllers)
    return True


def _setting_is_off(parameters: dict[str, Any], key: str) -> bool:
    return key in parameters and parameters[key] is False


def _pipeline_choice_pairs() -> tuple[tuple[str, str], ...]:
    try:
        from holodoppler.pipelines import pipelines
    except Exception:
        return (("sliding_shack_hartmann", "Sliding Shack-Hartmann"),)

    preview_targets = {
        name.removeprefix("preview_")
        for name in pipelines
        if name.startswith("preview_")
    }
    process_names = sorted(name for name in pipelines if not name.startswith("preview_"))
    preferred_order = [
        "simple",
        "sliding",
        "sliding_shack_hartmann",
        "split_apertures",
        "pca_accumulation",
        "sh_avg",
        "simple_numpy",
        "main",
    ]
    ordered_names = [
        name for name in preferred_order if name in process_names
    ] + [
        name for name in process_names if name not in preferred_order
    ]

    return tuple(
        (
            name,
            _pipeline_label(name, supports_preview=name in preview_targets),
        )
        for name in ordered_names
    )


def _pipeline_label(name: str, *, supports_preview: bool) -> str:
    labels = {
        "sliding_shack_hartmann": "Sliding Shack-Hartmann",
        "sliding": "Sliding",
        "simple": "Simple",
        "simple_numpy": "Simple (CPU multiprocessing)",
        "split_apertures": "Split apertures",
        "pca_accumulation": "PCA accumulation",
        "sh_avg": "Shack-Hartmann average",
        "main": "Legacy moments main",
        "moments_main_pipeline": "Moments main pipeline",
    }
    label = labels.get(name, name.replace("_", " ").strip().title())
    if not supports_preview:
        label = f"{label} (process only)"
    return label


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
        ttk.Button(
            button_row,
            text="Apply YAML / JSON",
            command=self._apply,
            style="Accent.TButton",
        ).pack(side="right", padx=(0, 8))

        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.editor.focus_set()

    def _apply(self) -> None:
        try:
            data = yaml.safe_load(self.editor.get("1.0", "end"))
        except yaml.YAMLError as exc:
            messagebox.showerror("Invalid YAML / JSON", str(exc), parent=self)
            return
        if not isinstance(data, dict):
            messagebox.showerror(
                "Invalid YAML / JSON",
                "The root value must be an object/mapping.",
                parent=self,
            )
            return
        self.on_apply(data)
        self.destroy()
