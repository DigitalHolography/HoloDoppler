from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def apply_theme(root: tk.Tk, theme: str = "dark") -> bool:
    style = ttk.Style(root)
    try:
        import sv_ttk

        sv_ttk.set_theme(theme)
        themed = True
    except Exception:
        themed = False
        style.theme_use("clam")
        _configure_fallback_theme(style, theme)

    root.option_add("*Font", ("Segoe UI", 10))
    root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))

    style.configure("Hero.TLabel", font=("Segoe UI", 24, "bold"))
    style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"))
    style.configure("Muted.TLabel", foreground="#6b7280")
    style.configure("Drop.TFrame", borderwidth=1, relief="solid")
    style.configure("Preview.TFrame", borderwidth=1, relief="solid")
    return themed


def plain_widget_colors(theme: str) -> dict[str, str]:
    if theme == "light":
        return {
            "bg": "#ffffff",
            "fg": "#202020",
            "insertbackground": "#202020",
            "selectbackground": "#cde8ff",
            "selectforeground": "#202020",
            "highlightbackground": "#d6d6d6",
        }
    return {
        "bg": "#202020",
        "fg": "#f2f2f2",
        "insertbackground": "#f2f2f2",
        "selectbackground": "#3a6ea5",
        "selectforeground": "#ffffff",
        "highlightbackground": "#3a3a3a",
    }


def configure_plain_widget(widget: tk.Widget, theme: str) -> None:
    colors = plain_widget_colors(theme)
    requested = {
        "background": colors["bg"],
        "foreground": colors["fg"],
        "insertbackground": colors["insertbackground"],
        "selectbackground": colors["selectbackground"],
        "selectforeground": colors["selectforeground"],
        "highlightbackground": colors["highlightbackground"],
        "highlightthickness": 1,
        "borderwidth": 0,
        "relief": "flat",
    }
    supported_options = widget.configure()
    widget.configure(**{key: value for key, value in requested.items() if key in supported_options})


def _configure_fallback_theme(style: ttk.Style, theme: str) -> None:
    if theme == "light":
        background = "#f5f5f5"
        foreground = "#202020"
        field = "#ffffff"
        accent = "#0067c0"
    else:
        background = "#1f1f1f"
        foreground = "#f2f2f2"
        field = "#2d2d2d"
        accent = "#4cc2ff"

    style.configure(".", background=background, foreground=foreground)
    style.configure("TFrame", background=background)
    style.configure("TLabel", background=background, foreground=foreground)
    style.configure("TLabelframe", background=background, foreground=foreground)
    style.configure("TLabelframe.Label", background=background, foreground=foreground)
    style.configure("TEntry", fieldbackground=field, foreground=foreground)
    style.configure("TButton", background=field, foreground=foreground, padding=(10, 6))
    style.configure("Accent.TButton", background=accent, foreground="#ffffff")
    style.map("Accent.TButton", background=[("active", accent)])
