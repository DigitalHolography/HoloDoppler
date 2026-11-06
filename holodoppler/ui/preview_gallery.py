"""Scrollable, responsive file preview cards."""
import tkinter as tk
from tkinter import ttk

from .image_utils import array_to_photo_image
from .theme import plain_widget_colors


class PreviewGallery(ttk.Frame):
    def __init__(self, master, *, theme, on_select, on_retry):
        super().__init__(master)
        self.on_select = on_select
        self.on_retry = on_retry
        self.colors = plain_widget_colors(theme)
        self.cards = {}
        self.selected_path = None
        self.columns = 0
        self.tooltip = None
        self.tooltip_after = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, width=560, height=360, highlightthickness=0,
                                background=self.colors["bg"])
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.content = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window(0, 0, window=self.content, anchor="nw")
        self.empty = ttk.Label(self.content, text="Load inputs to preview files.", anchor="center")
        self.empty.grid(row=0, column=0, padx=12, pady=30)
        self.content.bind("<Configure>", self._content_changed)
        self.canvas.bind("<Configure>", self._resize)
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.content.bind("<MouseWheel>", self._wheel)

    def _content_changed(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)
        columns = max(1, event.width // 292)
        if columns != self.columns:
            self.columns = columns
            self._layout()

    def _layout(self):
        for i, card in enumerate(self.cards.values()):
            card["frame"].grid(row=i // max(1, self.columns), column=i % max(1, self.columns),
                               padx=5, pady=5, sticky="nw")

    def _wheel(self, event):
        self.canvas.yview_scroll(-int(event.delta / 120) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1), "units")
        return "break"

    def set_paths(self, paths):
        self._hide_tooltip()
        for path in list(self.cards):
            if path not in paths:
                self.cards.pop(path)["frame"].destroy()
        for path in paths:
            if path in self.cards:
                continue
            frame = tk.Frame(self.content, width=280, height=270, background=self.colors["bg"],
                             highlightthickness=2, highlightbackground=self.colors["bg"])
            frame.grid_propagate(False)
            frame.columnconfigure(0, weight=1)
            title = ttk.Label(frame, text=path.name, wraplength=252, anchor="center")
            title.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
            image = ttk.Label(frame, text="Queued…", anchor="center", wraplength=250)
            image.grid(row=1, column=0, sticky="nsew", padx=8)
            frame.rowconfigure(1, weight=1)
            retry = ttk.Button(frame, text="Retry", command=lambda p=path: self.on_retry(p))
            retry.grid(row=2, column=0, pady=5)
            retry.grid_remove()
            self.cards[path] = dict(frame=frame, label=image, retry=retry, image=None, state="queued")
            for widget in (frame, title, image):
                widget.bind("<Button-1>", lambda event, p=path: self.on_select(p))
                widget.bind("<MouseWheel>", self._wheel)
                widget.bind("<Enter>", lambda event, p=path: self._schedule_tooltip(p))
                widget.bind("<Leave>", lambda event: self._hide_tooltip())
        self.cards = {p: self.cards[p] for p in paths}
        if paths:
            self.empty.grid_remove()
        else:
            self.empty.grid()
        self._layout()
        self.select(self.selected_path if self.selected_path in paths else (paths[0] if paths else None))

    def select(self, path, *, reveal=False):
        self.selected_path = path
        for p, card in self.cards.items():
            card["frame"].configure(highlightbackground="#3b91e8" if p == path else self.colors["bg"])
        if reveal and path in self.cards:
            self.update_idletasks()
            frame = self.cards[path]["frame"]
            top, bottom = frame.winfo_y(), frame.winfo_y() + frame.winfo_height()
            visible_top = self.canvas.canvasy(0)
            height = self.canvas.winfo_height()
            total = max(1, self.content.winfo_height())
            if top < visible_top:
                self.canvas.yview_moveto(top / total)
            elif bottom > visible_top + height:
                self.canvas.yview_moveto(max(0, bottom - height) / total)

    def set_state(self, path, state, message=None):
        card = self.cards.get(path)
        if card is None:
            return
        card["state"] = state
        card["image"] = None
        card["label"].configure(image="", text=message or {
            "queued": "Queued…", "computing": "Computing preview…",
            "processing": "Processing…", "empty": "No preview available",
        }.get(state, state))
        if state == "error":
            card["retry"].grid()
        else:
            card["retry"].grid_remove()

    def show(self, path, array):
        if path not in self.cards:
            return
        try:
            image = array_to_photo_image(array, (252, 190), self)
        except Exception as exc:
            self.set_state(path, "error", f"Could not display preview: {exc}")
            return
        if image is None:
            self.set_state(path, "empty")
            return
        card = self.cards[path]
        card["image"] = image
        card["state"] = "ready"
        card["label"].configure(image=image, text="")
        card["retry"].grid_remove()

    def _schedule_tooltip(self, path):
        self._hide_tooltip()
        self.tooltip_after = self.after(500, lambda: self._show_tooltip(path))

    def _show_tooltip(self, path):
        self.tooltip_after = None
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.geometry(f"+{self.winfo_pointerx()+12}+{self.winfo_pointery()+16}")
        ttk.Label(self.tooltip, text=str(path), padding=6).pack()

    def _hide_tooltip(self):
        if self.tooltip_after is not None:
            self.after_cancel(self.tooltip_after)
            self.tooltip_after = None
        if self.tooltip is not None:
            self.tooltip.destroy()
            self.tooltip = None

    def destroy(self):
        self._hide_tooltip()
        super().destroy()
