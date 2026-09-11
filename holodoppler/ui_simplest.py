from __future__ import annotations

import contextlib
import io
import queue
import threading
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from holodoppler.cli import process
from holodoppler.utils import load_config


APP_NAME = "HoloDoppler"

SUPPORTED = {".holo", ".cine", ".txt"}
INPUT_FILETYPES = [
    ("HoloDoppler inputs", "*.holo *.cine *.txt"),
    ("Holo files", "*.holo"),
    ("Cine files", "*.cine"),
    ("File lists", "*.txt"),
    ("All files", "*.*"),
]

DEFAULT_CONFIG = Path("./parameters/default_parameters_simple.yaml")


# ---------------------------------------------------------------------------
# Drag & Drop
# ---------------------------------------------------------------------------

try:
    from tkinterdnd2 import TkinterDnD

    DND_AVAILABLE = True
    BaseWindow = TkinterDnD.Tk
except ImportError:
    DND_AVAILABLE = False
    BaseWindow = tk.Tk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class QueueWriter(io.TextIOBase):
    """
    File-like object used with redirect_stdout/redirect_stderr.

    tqdm frequently writes using '\\r' instead of '\\n'. We turn those
    updates into normal console messages so they behave reasonably inside
    a Tkinter Text widget.
    """

    def __init__(self, output_queue: queue.Queue, stream_name: str):
        super().__init__()
        self.output_queue = output_queue
        self.stream_name = stream_name
        self._buffer = ""

    def write(self, text: str) -> int:
        if not text:
            return 0

        self._buffer += text

        # tqdm uses carriage returns to update the same line.
        while "\n" in self._buffer or "\r" in self._buffer:
            newline_pos = self._buffer.find("\n")
            carriage_pos = self._buffer.find("\r")

            positions = [
                p for p in (newline_pos, carriage_pos)
                if p >= 0
            ]

            if not positions:
                break

            pos = min(positions)
            line = self._buffer[:pos]
            self._buffer = self._buffer[pos + 1:]

            line = line.strip()

            if line:
                self.output_queue.put(
                    ("console", f"[{self.stream_name}] {line}")
                )

        return len(text)

    def flush(self) -> None:
        if self._buffer.strip():
            self.output_queue.put(
                ("console", f"[{self.stream_name}] {self._buffer.strip()}")
            )
            self._buffer = ""


class ConsoleRedirect:
    """
    Redirect both stdout and stderr while keeping the original streams
    available if needed.
    """

    def __init__(self, output_queue: queue.Queue):
        self.stdout = QueueWriter(output_queue, "OUT")
        self.stderr = QueueWriter(output_queue, "ERR")

    def __enter__(self):
        self._stdout_cm = contextlib.redirect_stdout(self.stdout)
        self._stderr_cm = contextlib.redirect_stderr(self.stderr)

        self._stdout_cm.__enter__()
        self._stderr_cm.__enter__()

        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.stdout.flush()
        self.stderr.flush()

        self._stderr_cm.__exit__(exc_type, exc_value, tb)
        self._stdout_cm.__exit__(exc_type, exc_value, tb)


# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------

class HoloDopplerUI(BaseWindow):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("980x760")
        self.minsize(820, 650)

        self.paths: list[Path] = []

        self.config_path = DEFAULT_CONFIG
        self.config_var = tk.StringVar(value=str(DEFAULT_CONFIG))

        self.status_var = tk.StringVar(value="Ready")
        self.status_detail_var = tk.StringVar(
            value="Add one or more .holo, .cine or .txt files."
        )

        self.q: queue.Queue = queue.Queue()

        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None

        self._closing = False
        self._dnd_enabled = False

        self._setup_theme()
        self._build_ui()
        self._enable_dnd()

        self.after(50, self._poll_queue)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _setup_theme(self):
        style = ttk.Style(self)

        try:
            self.tk.call("source", "sun-valley.tcl")
            self.tk.call("set_theme", "dark")
        except Exception:
            try:
                style.theme_use("clam")
            except Exception:
                pass

            bg = "#1e1e1e"
            panel = "#252526"
            fg = "#eeeeee"
            muted = "#aaaaaa"
            accent = "#087fbd"

            self.configure(background=bg)

            style.configure(
                ".",
                background=bg,
                foreground=fg,
                font=("TkDefaultFont", 10),
            )

            style.configure(
                "TFrame",
                background=bg,
            )

            style.configure(
                "Card.TFrame",
                background=panel,
            )

            style.configure(
                "TLabel",
                background=bg,
                foreground=fg,
            )

            style.configure(
                "Muted.TLabel",
                background=bg,
                foreground=muted,
            )

            style.configure(
                "Title.TLabel",
                background=bg,
                foreground=fg,
                font=("TkDefaultFont", 16, "bold"),
            )

            style.configure(
                "Section.TLabel",
                background=bg,
                foreground=fg,
                font=("TkDefaultFont", 10, "bold"),
            )

            style.configure(
                "TButton",
                padding=(10, 6),
            )

            style.configure(
                "Accent.TButton",
                background=accent,
                foreground="white",
                padding=(14, 7),
            )

            style.map(
                "Accent.TButton",
                background=[
                    ("active", "#0b91d5"),
                    ("disabled", "#444444"),
                ],
            )

            style.configure(
                "Danger.TButton",
                padding=(10, 6),
            )

            style.configure(
                "TEntry",
                padding=5,
            )

        self.option_add("*Font", ("TkDefaultFont", 10))

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        outer = ttk.Frame(self, padding=18)
        outer.pack(fill="both", expand=True)

        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)
        outer.rowconfigure(4, weight=1)

        # --------------------------------------------------------------
        # Header
        # --------------------------------------------------------------

        header = ttk.Frame(outer)
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 15),
        )

        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text=APP_NAME,
            style="Title.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            header,
            text="Batch processing",
            style="Muted.TLabel",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 0),
        )

        # --------------------------------------------------------------
        # INPUT SECTION
        # --------------------------------------------------------------

        input_frame = ttk.LabelFrame(
            outer,
            text="  Input files  ",
            padding=12,
        )
        input_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 12),
        )

        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(1, weight=1)

        # Drop area
        self.drop_label = ttk.Label(
            input_frame,
            text=(
                "Drop .holo, .cine or .txt files here\n"
                "(.txt files are treated as one file path per line)"
            ),
            anchor="center",
            justify="center",
        )
        self.drop_label.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 10),
        )

        # Scrollable file list
        list_container = ttk.Frame(input_frame)
        list_container.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(0, 10),
        )

        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)

        self.file_canvas = tk.Canvas(
            list_container,
            highlightthickness=0,
            borderwidth=0,
            background="#252526",
        )
        self.file_canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar = ttk.Scrollbar(
            list_container,
            orient="vertical",
            command=self.file_canvas.yview,
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.file_canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.file_rows_frame = tk.Frame(
            self.file_canvas,
            background="#252526",
        )

        self.file_window = self.file_canvas.create_window(
            (0, 0),
            window=self.file_rows_frame,
            anchor="nw",
        )

        self.file_rows_frame.bind(
            "<Configure>",
            self._on_file_frame_configure,
        )

        self.file_canvas.bind(
            "<Configure>",
            self._on_file_canvas_configure,
        )

        # Buttons
        file_buttons = ttk.Frame(input_frame)
        file_buttons.grid(
            row=1,
            column=1,
            sticky="ns",
        )

        ttk.Button(
            file_buttons,
            text="📂  Add files",
            command=self.open_files,
        ).pack(
            fill="x",
            pady=(0, 8),
        )

        ttk.Button(
            file_buttons,
            text="＋  Add folder",
            command=self.open_folder,
        ).pack(
            fill="x",
            pady=(0, 8),
        )

        ttk.Button(
            file_buttons,
            text="Clear list",
            command=self.clear_files,
        ).pack(
            fill="x",
        )

        # --------------------------------------------------------------
        # CONFIGURATION
        # --------------------------------------------------------------

        config_frame = ttk.LabelFrame(
            outer,
            text="  Configuration  ",
            padding=12,
        )
        config_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            pady=(0, 12),
        )

        config_frame.columnconfigure(0, weight=1)

        config_entry = ttk.Entry(
            config_frame,
            textvariable=self.config_var,
            state="readonly",
        )
        config_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 10),
        )

        self.config_button = ttk.Button(
            config_frame,
            text="⚙  Change",
            command=self.choose_config,
        )
        self.config_button.grid(
            row=0,
            column=1,
        )

        ttk.Label(
            config_frame,
            text="JSON / YAML configuration used by HoloDoppler.",
            style="Muted.TLabel",
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(7, 0),
        )

        # --------------------------------------------------------------
        # CONSOLE
        # --------------------------------------------------------------

        console_frame = ttk.LabelFrame(
            outer,
            text="  Console output  ",
            padding=8,
        )
        console_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            pady=(0, 12),
        )

        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)

        self.console = ScrolledText(
            console_frame,
            height=10,
            wrap="word",
            relief="flat",
            borderwidth=0,
            background="#111111",
            foreground="#dddddd",
            insertbackground="#ffffff",
            font=("TkFixedFont", 9),
        )
        self.console.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.console.config(state="disabled")

        # --------------------------------------------------------------
        # STATUS / ACTIONS
        # --------------------------------------------------------------

        bottom = ttk.Frame(outer)
        bottom.grid(
            row=4,
            column=0,
            sticky="ew",
        )

        bottom.columnconfigure(0, weight=1)

        status_frame = ttk.Frame(bottom)
        status_frame.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        status_frame.columnconfigure(1, weight=1)

        self.status_indicator = tk.Label(
            status_frame,
            text="●",
            font=("TkDefaultFont", 13),
            background=self.cget("background"),
            foreground="#6aa84f",
        )
        self.status_indicator.grid(
            row=0,
            column=0,
            padx=(0, 8),
        )

        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("TkDefaultFont", 10, "bold"),
        ).grid(
            row=0,
            column=1,
            sticky="w",
        )

        ttk.Label(
            status_frame,
            textvariable=self.status_detail_var,
            style="Muted.TLabel",
        ).grid(
            row=1,
            column=1,
            sticky="w",
            pady=(2, 0),
        )

        # Buttons
        actions = ttk.Frame(bottom)
        actions.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
            padx=(15, 0),
        )

        self.run_btn = ttk.Button(
            actions,
            text="▶  RUN",
            command=self.run,
            state="disabled",
            style="Accent.TButton",
        )
        self.run_btn.pack(
            side="left",
            padx=(0, 8),
        )

        self.stop_btn = ttk.Button(
            actions,
            text="■  STOP",
            command=self.stop_work,
            state="disabled",
        )
        self.stop_btn.pack(
            side="left",
        )

        # Progress bar
        self.progress = ttk.Progressbar(
            bottom,
            mode="indeterminate",
        )
        self.progress.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(12, 0),
        )

        self._rebuild_file_list()

    # ------------------------------------------------------------------
    # File list scrolling
    # ------------------------------------------------------------------

    def _on_file_frame_configure(self, _event=None):
        self.file_canvas.configure(
            scrollregion=self.file_canvas.bbox("all")
        )

    def _on_file_canvas_configure(self, event):
        self.file_canvas.itemconfigure(
            self.file_window,
            width=event.width,
        )

    # ------------------------------------------------------------------
    # File handling
    # ------------------------------------------------------------------

    def open_files(self):
        if self._busy():
            return

        paths = filedialog.askopenfilenames(
            title="Select HoloDoppler input files",
            filetypes=INPUT_FILETYPES,
        )

        if paths:
            self._add_paths(Path(p) for p in paths)

    def open_folder(self):
        if self._busy():
            return

        folder = filedialog.askdirectory(
            title="Select folder containing HoloDoppler files"
        )

        if not folder:
            return

        folder_path = Path(folder)

        paths = [
            p
            for p in sorted(folder_path.iterdir())
            if p.is_file() and p.suffix.lower() in {".holo", ".cine", ".txt"}
        ]

        if paths:
            self._add_paths(paths)
        else:
            self._set_status(
                "Ready",
                "No supported files found in selected folder.",
                "warning",
            )

    def _add_paths(self, paths):
        """
        Add files without creating duplicates.

        TXT files are expanded into individual input files.
        """

        new_paths: list[Path] = []

        for path in paths:
            path = Path(path)

            if not path.exists():
                self._append_console(
                    f"[WARN] File does not exist: {path}"
                )
                continue

            suffix = path.suffix.lower()

            if suffix == ".txt":
                new_paths.extend(self._read_txt(path))

            elif suffix in {".holo", ".cine"}:
                new_paths.append(path)

            else:
                self._append_console(
                    f"[WARN] Ignoring unsupported file: {path}"
                )

        existing = {p.resolve() for p in self.paths}

        added = 0

        for path in new_paths:
            try:
                resolved = path.resolve()
            except Exception:
                resolved = path.absolute()

            if not resolved.exists():
                self._append_console(
                    f"[WARN] File does not exist: {resolved}"
                )
                continue

            if resolved.suffix.lower() not in {".holo", ".cine"}:
                self._append_console(
                    f"[WARN] Ignoring unsupported input: {resolved}"
                )
                continue

            if resolved not in existing:
                self.paths.append(resolved)
                existing.add(resolved)
                added += 1

        self._rebuild_file_list()

        if self.paths:
            self.run_btn["state"] = "normal"

            self._set_status(
                "Ready",
                f"{len(self.paths)} file(s) queued"
                + (f" — added {added}" if added else ""),
                "ready",
            )
        else:
            self.run_btn["state"] = "disabled"

    def _read_txt(self, path: Path) -> list[Path]:
        """
        Read a text file containing one input file per line.

        Relative paths are resolved relative to the .txt file itself.
        """

        result: list[Path] = []
        base = path.parent

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception as exc:
            self._append_console(
                f"[ERROR] Could not read file list {path}: {exc}"
            )
            return result

        for line_number, line in enumerate(lines, 1):
            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            # Allow paths surrounded by quotes.
            if (
                len(line) >= 2
                and line[0] == '"'
                and line[-1] == '"'
            ):
                line = line[1:-1]

            candidate = Path(line)

            if not candidate.is_absolute():
                candidate = base / candidate

            if candidate.suffix.lower() not in {".holo", ".cine"}:
                self._append_console(
                    f"[WARN] {path}:{line_number}: "
                    f"unsupported input: {candidate}"
                )
                continue

            if not candidate.exists():
                self._append_console(
                    f"[WARN] {path}:{line_number}: "
                    f"file does not exist: {candidate}"
                )
                continue

            result.append(candidate)

        return result

    def remove_file(self, index: int):
        if self._busy():
            return

        if 0 <= index < len(self.paths):
            removed = self.paths.pop(index)

            self._append_console(
                f"[INFO] Removed: {removed}"
            )

        self._rebuild_file_list()

        if self.paths:
            self.run_btn["state"] = "normal"
            self._set_status(
                "Ready",
                f"{len(self.paths)} file(s) queued",
                "ready",
            )
        else:
            self.run_btn["state"] = "disabled"
            self._set_status(
                "Ready",
                "No input files.",
                "ready",
            )

    def clear_files(self):
        if self._busy():
            return

        if not self.paths:
            return

        self.paths.clear()
        self._rebuild_file_list()

        self.run_btn["state"] = "disabled"

        self._set_status(
            "Ready",
            "Input list cleared.",
            "ready",
        )

    def _rebuild_file_list(self):
        for child in self.file_rows_frame.winfo_children():
            child.destroy()

        if not self.paths:
            label = tk.Label(
                self.file_rows_frame,
                text="No files queued",
                anchor="center",
                background="#252526",
                foreground="#888888",
                padx=12,
                pady=16,
            )
            label.pack(
                fill="x",
            )
            return

        for index, path in enumerate(self.paths):
            self._create_file_row(index, path)

        self.file_rows_frame.update_idletasks()

    def _create_file_row(self, index: int, path: Path):
        row = tk.Frame(
            self.file_rows_frame,
            background="#252526",
        )
        row.pack(
            fill="x",
            padx=5,
            pady=2,
        )

        row.columnconfigure(1, weight=1)

        number = tk.Label(
            row,
            text=f"{index + 1:02d}",
            width=3,
            anchor="e",
            background="#252526",
            foreground="#777777",
        )
        number.grid(
            row=0,
            column=0,
            padx=(4, 8),
        )

        name = tk.Label(
            row,
            text=path.name,
            anchor="w",
            background="#252526",
            foreground="#eeeeee",
        )
        name.grid(
            row=0,
            column=1,
            sticky="ew",
        )

        directory = tk.Label(
            row,
            text=str(path.parent),
            anchor="w",
            background="#252526",
            foreground="#888888",
        )
        directory.grid(
            row=1,
            column=1,
            sticky="ew",
        )

        remove_button = ttk.Button(
            row,
            text="✕",
            width=3,
            command=lambda i=index: self.remove_file(i),
        )
        remove_button.grid(
            row=0,
            column=2,
            rowspan=2,
            padx=(8, 4),
        )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def choose_config(self):
        if self._busy():
            return

        path = filedialog.askopenfilename(
            title="Select HoloDoppler configuration",
            filetypes=[
                ("JSON / YAML", "*.json *.yml *.yaml"),
                ("All files", "*.*"),
            ],
            initialdir=(
                self.config_path.parent
                if self.config_path.parent.exists()
                else Path.cwd()
            ),
        )

        if not path:
            return

        self.config_path = Path(path)
        self.config_var.set(str(self.config_path))

        self._set_status(
            "Ready",
            f"Configuration selected: {self.config_path.name}",
            "ready",
        )

    def _load_params(self):
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file does not exist:\n"
                f"{self.config_path}"
            )

        return load_config(self.config_path)

    # ------------------------------------------------------------------
    # Drag & Drop
    # ------------------------------------------------------------------

    def _enable_dnd(self):
        if not DND_AVAILABLE:
            self._append_console(
                "[INFO] Drag & drop unavailable. "
                "Install tkinterdnd2 to enable it."
            )
            return

        try:
            self.drop_target_register("DND_Files")

            self.dnd_bind(
                "<<Drop>>",
                self._on_drop,
            )

            self._dnd_enabled = True

            self.drop_label.configure(
                text=(
                    "Drop .holo, .cine or .txt files here\n"
                    "or use “Add files”"
                )
            )

        except Exception as exc:
            self._append_console(
                f"[WARN] Drag & drop initialization failed: {exc}"
            )

    def _on_drop(self, event):
        if self._busy():
            return

        try:
            dropped = self.tk.splitlist(event.data)
            self._add_paths(Path(p) for p in dropped)
        except Exception as exc:
            self._append_console(
                f"[ERROR] Could not process dropped files: {exc}"
            )

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def run(self):
        if self._busy():
            return

        if not self.paths:
            messagebox.showwarning(
                APP_NAME,
                "Add at least one input file before running.",
            )
            return

        try:
            # Validate configuration BEFORE starting the worker.
            self._load_params()
        except Exception as exc:
            messagebox.showerror(
                "Configuration error",
                str(exc),
            )
            self._append_console(
                f"[ERROR] Configuration validation failed: {exc}"
            )
            return

        self.stop_event.clear()

        self._set_busy(
            True,
            "Processing",
            f"Starting batch of {len(self.paths)} file(s)...",
        )

        self._append_console("")
        self._append_console("=" * 72)
        self._append_console(
            f"[INFO] Starting HoloDoppler batch — {len(self.paths)} file(s)"
        )
        self._append_console(
            f"[INFO] Configuration: {self.config_path}"
        )
        self._append_console("=" * 72)

        self.worker = threading.Thread(
            target=self._run_worker,
            name="HoloDopplerWorker",
            daemon=True,
        )
        self.worker.start()

    def _run_worker(self):
        completed = 0
        failed = 0

        try:
            params = self._load_params()

            total = len(self.paths)

            for index, path in enumerate(self.paths, 1):

                if self.stop_event.is_set():
                    self.q.put(
                        (
                            "status",
                            "Stopped",
                            f"Stopped before processing {path.name}.",
                        )
                    )
                    return

                self.q.put(
                    (
                        "status",
                        "Processing",
                        f"File {index} / {total}: {path.name}",
                    )
                )

                self.q.put(
                    (
                        "console",
                        "",
                    )
                )

                self.q.put(
                    (
                        "console",
                        f"[INFO] Processing {index}/{total}: {path}",
                    )
                )

                try:
                    # Redirect both streams so anything printed by the
                    # HoloDoppler processing code appears in the UI.
                    with ConsoleRedirect(self.q):
                        process(str(path), params)

                    completed += 1

                    self.q.put(
                        (
                            "console",
                            f"[OK] Completed: {path.name}",
                        )
                    )

                except Exception as exc:
                    failed += 1

                    self.q.put(
                        (
                            "console",
                            f"[ERROR] Failed: {path.name}",
                        )
                    )

                    self.q.put(
                        (
                            "console",
                            f"[ERROR] {type(exc).__name__}: {exc}",
                        )
                    )

                    # Keep the GUI alive and continue with the next file.
                    self.q.put(
                        (
                            "console",
                            traceback.format_exc(),
                        )
                    )

                    self.q.put(
                        (
                            "status",
                            "Processing",
                            f"{path.name} failed — continuing with next file.",
                        )
                    )

            if self.stop_event.is_set():
                self.q.put(
                    (
                        "status",
                        "Stopped",
                        f"Completed {completed}/{total} file(s).",
                    )
                )
            elif failed:
                self.q.put(
                    (
                        "status",
                        "Completed with errors",
                        f"{completed} succeeded, {failed} failed.",
                    )
                )
            else:
                self.q.put(
                    (
                        "status",
                        "Ready",
                        f"Completed successfully — {completed} file(s).",
                    )
                )

        except Exception as exc:
            self.q.put(
                (
                    "fatal",
                    f"{type(exc).__name__}: {exc}",
                )
            )

            self.q.put(
                (
                    "console",
                    traceback.format_exc(),
                )
            )

        finally:
            self.q.put(("done", None))

    def stop_work(self):
        if not self._busy():
            return

        self.stop_event.set()

        self.stop_btn["state"] = "disabled"

        self._set_status(
            "Stopping",
            "The current file cannot be force-killed safely. "
            "Stopping after the current process() call returns.",
            "warning",
        )

        self._append_console(
            "[INFO] Stop requested — waiting for current file to finish..."
        )

    # ------------------------------------------------------------------
    # Queue / UI thread
    # ------------------------------------------------------------------

    def _poll_queue(self):
        try:
            while True:
                message = self.q.get_nowait()

                kind = message[0]

                if kind == "console":
                    self._append_console(message[1])

                elif kind == "status":
                    self._set_status(
                        message[1],
                        message[2],
                        self._status_kind(message[1]),
                    )

                elif kind == "fatal":
                    self._set_status(
                        "Error",
                        message[1],
                        "error",
                    )

                    self._append_console(
                        f"[FATAL] {message[1]}"
                    )

                    messagebox.showerror(
                        APP_NAME,
                        message[1],
                    )

                elif kind == "done":
                    self._set_busy(False)

        except queue.Empty:
            pass

        if not self._closing:
            self.after(50, self._poll_queue)

    def _append_console(self, text: str):
        self.console.config(state="normal")

        self.console.insert(
            tk.END,
            text + "\n",
        )

        # Prevent the console from growing forever.
        # Keep roughly the most recent 10,000 lines.
        try:
            line_count = int(
                self.console.index("end-1c").split(".")[0]
            )

            if line_count > 10000:
                self.console.delete(
                    "1.0",
                    "1000.0",
                )
        except Exception:
            pass

        self.console.see(tk.END)
        self.console.config(state="disabled")

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def _status_kind(self, status: str) -> str:
        status_lower = status.lower()

        if "error" in status_lower:
            return "error"

        if "stop" in status_lower or "warning" in status_lower:
            return "warning"

        if status_lower == "processing":
            return "processing"

        return "ready"

    def _set_status(
        self,
        status: str,
        detail: str = "",
        kind: str = "ready",
    ):
        self.status_var.set(status)
        self.status_detail_var.set(detail)

        colors = {
            "ready": "#6aa84f",
            "processing": "#3d85c6",
            "warning": "#e69138",
            "error": "#cc0000",
        }

        self.status_indicator.configure(
            foreground=colors.get(kind, "#6aa84f")
        )

    def _set_busy(
        self,
        busy: bool,
        status: str = "Ready",
        detail: str = "",
    ):
        if busy:
            self._set_status(
                status,
                detail,
                "processing",
            )

            self.progress.start(10)

            self.run_btn["state"] = "disabled"
            self.stop_btn["state"] = "normal"

            self.config_button["state"] = "disabled"

        else:
            self.progress.stop()

            self.run_btn["state"] = (
                "normal" if self.paths else "disabled"
            )

            self.stop_btn["state"] = "disabled"
            self.config_button["state"] = "normal"

            # Do not overwrite a more useful final status.
            if self.status_var.get() == "Processing":
                self._set_status(
                    "Ready",
                    f"{len(self.paths)} file(s) queued.",
                    "ready",
                )

    def _busy(self) -> bool:
        return (
            self.worker is not None
            and self.worker.is_alive()
        )

    # ------------------------------------------------------------------
    # Closing
    # ------------------------------------------------------------------

    def _on_close(self):
        if self._busy():
            answer = messagebox.askyesno(
                APP_NAME,
                (
                    "Processing is still running.\n\n"
                    "Do you want to request a stop and close the window?"
                ),
            )

            if not answer:
                return

            self.stop_event.set()

            # We deliberately do not destroy the window immediately.
            # The worker may still be inside process().
            self._set_status(
                "Stopping",
                "Waiting for the current operation to finish...",
                "warning",
            )

            self._wait_for_worker_close()
            return

        self._closing = True
        self.destroy()

    def _wait_for_worker_close(self):
        if self._busy():
            self.after(
                100,
                self._wait_for_worker_close,
            )
            return

        self._closing = True
        self.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = HoloDopplerUI()
    app.mainloop()