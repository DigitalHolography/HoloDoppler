"""A nonmodal, thread-safe viewer for the application's shared log stream."""

from __future__ import annotations

from collections import deque
import logging
import tkinter as tk
from tkinter import ttk

from holodoppler.logging import DATE_FORMAT, LOG_FORMAT, logger

from .theme import configure_plain_widget


_LEVEL_COLORS = {
    "light": {
        "DEBUG": "#626b78",
        "INFO": "#075b99",
        "WARNING": "#855600",
        "ERROR": "#bd2020",
    },
    "dark": {
        "DEBUG": "#a5adba",
        "INFO": "#75caff",
        "WARNING": "#f5c76a",
        "ERROR": "#ff9292",
    },
}


class _LogHistory(logging.Handler):
    """Keep a bounded history; worker threads never call a Tk method."""

    def __init__(self, max_records: int) -> None:
        super().__init__(logging.DEBUG)
        self.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        self.records: deque[tuple[int, str, str]] = deque(maxlen=max_records)
        self.sequence = 0

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            level = (
                "ERROR" if record.levelno >= logging.ERROR else
                "WARNING" if record.levelno >= logging.WARNING else
                "INFO" if record.levelno >= logging.INFO else "DEBUG"
            )
            self.acquire()
            try:
                self.sequence += 1
                self.records.append((self.sequence, message, level))
            finally:
                self.release()
        except Exception:
            self.handleError(record)

    def since(self, sequence: int, limit: int) -> tuple[bool, list[tuple[int, str, str]]]:
        self.acquire()
        try:
            skipped = bool(self.records and sequence < self.records[0][0] - 1)
            records = []
            for record in self.records:
                if record[0] > sequence:
                    records.append(record)
                    if len(records) == limit:
                        break
            return skipped, records
        finally:
            self.release()


class LogWindow:
    """Toggleable log viewer. Construct and call its methods on the Tk thread.

    The handler collects messages even while the window is hidden. Logging from
    processing threads only writes to its locked history; a short Tk timer draws
    batches so processing and the rest of the interface remain responsive.
    """

    def __init__(self, root: tk.Misc, *, theme: str = "dark", max_records: int = 2000) -> None:
        self.root = root
        self.theme = "light" if theme == "light" else "dark"
        self.window: tk.Toplevel | None = None
        self.text: tk.Text | None = None
        self._visible = False
        self._closed = False
        self._last_sequence = 0
        self._handler = _LogHistory(max_records)
        logger.addHandler(self._handler)
        self._after_id = self.root.after(75, self._poll)

    @property
    def is_visible(self) -> bool:
        return self._visible

    def toggle(self) -> None:
        if self._closed:
            return
        if self._visible:
            self.hide()
            return
        if self.window is None:
            self._build()
        self._visible = True
        self.window.deiconify()
        self.window.lift()
        self._refresh()

    def hide(self) -> None:
        self._visible = False
        if self.window is not None:
            self.window.withdraw()

    def close(self) -> None:
        """Detach the handler and timer when the main application closes."""
        if self._closed:
            return
        self._closed = True
        self._visible = False
        logger.removeHandler(self._handler)
        self._handler.close()
        try:
            self.root.after_cancel(self._after_id)
            if self.window is not None:
                self.window.destroy()
        except tk.TclError:
            pass

    def _build(self) -> None:
        self.window = tk.Toplevel(self.root)
        self.window.withdraw()
        self.window.title("HoloDoppler logs")
        self.window.geometry("900x440")
        self.window.minsize(480, 240)
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        self.text = tk.Text(
            self.window,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
            padx=10,
            pady=8,
        )
        configure_plain_widget(self.text, self.theme)
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.window, command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scrollbar.set)
        for level, color in _LEVEL_COLORS[self.theme].items():
            self.text.tag_configure(level, foreground=color)

    def _poll(self) -> None:
        if self._closed:
            return
        if self._visible:
            self._refresh()
        self._after_id = self.root.after(75, self._poll)

    def _refresh(self) -> None:
        skipped, records = self._handler.since(self._last_sequence, limit=200)
        if not records or self.text is None:
            return
        follow = self.text.yview()[1] >= 0.995
        self.text.configure(state="normal")
        if skipped:
            self.text.delete("1.0", "end")
        for sequence, message, level in records:
            self.text.insert("end", message + "\n", level)
            self._last_sequence = sequence
        # Bound the widget as well as the history, including multiline records.
        lines = int(self.text.index("end-1c").split(".")[0])
        if lines > 6000:
            self.text.delete("1.0", f"{lines - 6000 + 1}.0")
        self.text.configure(state="disabled")
        if follow or skipped:
            self.text.see("end")
