from __future__ import annotations

import json
import queue
import sys
import threading
from pathlib import Path

import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from holodoppler.cli import preview, process

APP_NAME = "HoloDoppler"
SUPPORTED = {".holo", ".cine", ".txt"}
DEFAULT_CONFIG = Path("./parameters/default_parameters_debug.json")


def _ensure_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
    return app


class UI(QtWidgets.QMainWindow):
    def __init__(self):
        self._app = _ensure_app()
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(800, 720)
        self.setMinimumSize(700, 600)
        self.setAcceptDrops(True)

        self.paths: list[Path] = []
        self.config_path = DEFAULT_CONFIG
        self.q: queue.Queue[tuple[str, object]] = queue.Queue()
        self.stop = threading.Event()
        self.worker: threading.Thread | None = None

        self._setup_theme()
        self._build()
        self._set_status("Ready - drop .holo/.cine/.txt anywhere")

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._poll)
        self.timer.start(50)

    def mainloop(self) -> int:
        self.show()
        return self._app.exec()

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _setup_theme(self) -> None:
        self._app.setStyle("Fusion")

        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#1e1e1e"))
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#f0f0f0"))
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor("#252526"))
        palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor("#2d2d2d"))
        palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor("#f0f0f0"))
        palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor("#2d2d2d"))
        palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor("#f0f0f0"))
        palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#0a5c8e"))
        palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#ffffff"))
        self._app.setPalette(palette)

        pg.setConfigOptions(antialias=True, imageAxisOrder="row-major")

        self.setStyleSheet(
            """
            QWidget {
                background: #1e1e1e;
                color: #f0f0f0;
                font-size: 10pt;
            }
            QPlainTextEdit, QLineEdit {
                background: #252526;
                color: #e0e0e0;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit[readOnly="true"] {
                background: #3c3c3c;
            }
            QPushButton {
                background: #2d2d2d;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 7px 12px;
            }
            QPushButton:hover {
                background: #3c3c3c;
            }
            QPushButton:disabled {
                color: #7a7a7a;
                background: #252526;
                border-color: #333333;
            }
            QPushButton#accentButton {
                background: #0a5c8e;
                border-color: #0f6ba3;
                color: white;
                font-weight: 600;
            }
            QPushButton#accentButton:hover {
                background: #0f6ba3;
            }
            QGroupBox {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-top: 14px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QProgressBar {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                height: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #0a5c8e;
                border-radius: 3px;
            }
            """
        )

    # ------------------------------------------------------------------
    # UI build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        central = QtWidgets.QWidget(self)
        central.setAcceptDrops(True)
        self.setCentralWidget(central)

        main = QtWidgets.QGridLayout(central)
        main.setContentsMargins(15, 15, 15, 15)
        main.setHorizontalSpacing(10)
        main.setVerticalSpacing(10)
        main.setColumnStretch(1, 1)
        main.setRowStretch(2, 1)

        title_font = QtGui.QFont()
        title_font.setBold(True)

        files_label = QtWidgets.QLabel("Input files")
        files_label.setFont(title_font)
        files_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        main.addWidget(files_label, 0, 0)

        self.filelist_text = QtWidgets.QPlainTextEdit()
        self.filelist_text.setReadOnly(True)
        self.filelist_text.setAcceptDrops(False)
        self.filelist_text.setMinimumHeight(105)
        self.filelist_text.setPlainText("No files selected")
        main.addWidget(self.filelist_text, 0, 1)

        open_btn = QtWidgets.QPushButton("Open files")
        open_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon))
        open_btn.clicked.connect(self.open_files)
        main.addWidget(open_btn, 0, 2, alignment=QtCore.Qt.AlignmentFlag.AlignTop)

        config_label = QtWidgets.QLabel("Config JSON")
        config_label.setFont(title_font)
        config_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        main.addWidget(config_label, 1, 0)

        self.config_edit = QtWidgets.QLineEdit(str(DEFAULT_CONFIG))
        self.config_edit.setReadOnly(True)
        main.addWidget(self.config_edit, 1, 1)

        config_btn = QtWidgets.QPushButton("Change")
        config_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
        config_btn.clicked.connect(self.choose_config)
        main.addWidget(config_btn, 1, 2, alignment=QtCore.Qt.AlignmentFlag.AlignTop)

        preview_group = QtWidgets.QGroupBox("Preview")
        preview_layout = QtWidgets.QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        main.addWidget(preview_group, 2, 0, 1, 3)

        self.preview_plot = pg.PlotWidget()
        self.preview_plot.setBackground("#111111")
        self.preview_plot.setMenuEnabled(False)
        self.preview_plot.hideAxis("left")
        self.preview_plot.hideAxis("bottom")
        self.preview_viewbox = self.preview_plot.getViewBox()
        self.preview_viewbox.setAspectLocked(True)
        self.preview_viewbox.invertY(True)
        self.preview_item = pg.ImageItem()
        self.preview_plot.addItem(self.preview_item)
        self.preview_message = pg.TextItem(
            "Drop files or select input",
            anchor=(0.5, 0.5),
            color="#b8b8b8",
        )
        self.preview_plot.addItem(self.preview_message)
        self.preview_viewbox.setRange(xRange=(-1, 1), yRange=(-1, 1), padding=0)
        preview_layout.addWidget(self.preview_plot)

        buttons = QtWidgets.QHBoxLayout()
        buttons.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main.addLayout(buttons, 3, 0, 1, 3)

        self.run_btn = QtWidgets.QPushButton("RUN")
        self.run_btn.setObjectName("accentButton")
        self.run_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton))
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self.run)
        buttons.addWidget(self.run_btn)

        self.stop_btn = QtWidgets.QPushButton("STOP")
        self.stop_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaStop))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_work)
        buttons.addWidget(self.stop_btn)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        main.addWidget(self.progress, 4, 0, 1, 3)

        self.status_label = QtWidgets.QLabel()
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        status_font = self.status_label.font()
        status_font.setItalic(True)
        status_font.setPointSize(max(status_font.pointSize() - 1, 8))
        self.status_label.setFont(status_font)
        main.addWidget(self.status_label, 5, 0, 1, 3)

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def open_files(self) -> None:
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open input files",
            "",
            "HoloDoppler inputs (*.holo *.cine *.txt);;All files (*)",
        )
        if paths:
            self._set_paths([Path(p) for p in paths])

    def _set_paths(self, paths: list[Path]) -> None:
        out: list[Path] = []
        for path in paths:
            suffix = path.suffix.lower()
            if suffix == ".txt":
                out += self._read_txt(path)
            elif suffix in {".holo", ".cine"}:
                out.append(path)

        self.paths = [path.resolve() for path in out if path.exists()]
        self._update_filelist_display()
        self.run_btn.setEnabled(bool(self.paths) and not self._busy())

        if self.paths:
            self._set_status(f"Loaded {len(self.paths)} file(s)")
            self._start_preview(self.paths[0])
        else:
            self._set_status("No valid input")
            self._set_preview_message("No preview")

    def _update_filelist_display(self) -> None:
        if self.paths:
            self.filelist_text.setPlainText("\n".join(str(path) for path in self.paths))
        else:
            self.filelist_text.setPlainText("No files selected")

    def _read_txt(self, path: Path) -> list[Path]:
        base = path.parent
        res: list[Path] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip().strip('"')
            if not line or line.startswith("#"):
                continue
            candidate = Path(line)
            res.append(candidate if candidate.is_absolute() else base / candidate)
        return res

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _start_preview(self, path: Path) -> None:
        if self._busy():
            return
        self.stop.clear()
        self._set_busy(True, "Loading preview...")
        self.worker = threading.Thread(target=self._preview_worker, args=(path,), daemon=True)
        self.worker.start()

    def _preview_worker(self, path: Path) -> None:
        try:
            params = self._load_params()
            img = preview(str(path), params)
            self.q.put(("img", img))
        except Exception as exc:
            self.q.put(("err", str(exc)))
        finally:
            self.q.put(("done", None))

    def _show_preview(self, arr: object) -> None:
        image = self._prepare_preview_array(arr)
        if image is None:
            self._set_preview_message("Preview not available")
            return

        self.preview_message.setVisible(False)
        self.preview_item.setVisible(True)

        if image.ndim == 2:
            self.preview_item.setImage(image, autoLevels=False, levels=(0, 255))
            height, width = image.shape
        else:
            self.preview_item.setImage(image, autoLevels=False)
            height, width = image.shape[:2]

        self.preview_item.setRect(QtCore.QRectF(0, 0, width, height))
        self.preview_viewbox.setRange(xRange=(0, width), yRange=(0, height), padding=0.02)

    def _prepare_preview_array(self, arr: object):
        if arr is None:
            return None

        import numpy as np

        if hasattr(arr, "get"):
            arr = arr.get()

        image = np.asarray(arr).squeeze()
        if image.ndim not in {2, 3}:
            return None

        if image.ndim == 3 and image.shape[-1] not in {3, 4}:
            return None

        if image.dtype == np.uint8:
            return np.ascontiguousarray(image)

        image = image.astype("float32", copy=False)
        finite = np.isfinite(image)
        if not finite.any():
            return np.zeros(image.shape, dtype=np.uint8)

        mn = float(np.nanmin(image[finite]))
        mx = float(np.nanmax(image[finite]))
        if mx > mn:
            image = (image - mn) * 255.0 / (mx - mn)
        else:
            image = np.zeros_like(image)

        image = np.nan_to_num(image, nan=0.0, posinf=255.0, neginf=0.0)
        return np.ascontiguousarray(image.clip(0, 255).astype(np.uint8))

    def _set_preview_message(self, text: str) -> None:
        self.preview_item.clear()
        self.preview_item.setVisible(False)
        self.preview_message.setText(text)
        self.preview_message.setVisible(True)
        self.preview_message.setPos(0, 0)
        self.preview_viewbox.setRange(xRange=(-1, 1), yRange=(-1, 1), padding=0)

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def run(self) -> None:
        if self._busy():
            return
        self.stop.clear()
        self._set_busy(True, "Running...")
        self.worker = threading.Thread(target=self._run_worker, daemon=True)
        self.worker.start()

    def _run_worker(self) -> None:
        try:
            params = self._load_params()
            for index, path in enumerate(self.paths, 1):
                if self.stop.is_set():
                    self.q.put(("status", "Stopped"))
                    return
                self.q.put(("status", f"Processing {index}/{len(self.paths)}"))
                print(f"Processing {path} with parameters:")
                process(str(path), params)
            self.q.put(("status", "Done"))
        except Exception as exc:
            import traceback

            print(traceback.format_exc())
            self.q.put(("err", str(exc)))
        finally:
            self.q.put(("done", None))

    def stop_work(self) -> None:
        self.stop.set()
        self._set_status("Stopping after current file...")

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def choose_config(self) -> None:
        initial_dir = self.config_path.parent if self.config_path.parent.exists() else Path.cwd()
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select JSON config",
            str(initial_dir),
            "JSON config (*.json);;All files (*)",
        )
        if path:
            self.config_path = Path(path)
            self.config_edit.setText(str(self.config_path))

    def _load_params(self) -> dict:
        if not self.config_path.exists():
            return {}
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # Drag and drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if self._paths_from_mime(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if self._paths_from_mime(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        paths = self._paths_from_mime(event.mimeData())
        if paths:
            self._set_paths(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _paths_from_mime(self, mime: QtCore.QMimeData) -> list[Path]:
        paths: list[Path] = []

        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    path = Path(url.toLocalFile())
                    if path.suffix.lower() in SUPPORTED:
                        paths.append(path)

        if not paths and mime.hasText():
            for line in mime.text().splitlines():
                value = line.strip().strip('"')
                if value.startswith("file:///"):
                    value = QtCore.QUrl(value).toLocalFile()
                if value:
                    path = Path(value)
                    if path.suffix.lower() in SUPPORTED:
                        paths.append(path)

        return paths

    # ------------------------------------------------------------------
    # Queue polling and busy state
    # ------------------------------------------------------------------

    def _poll(self) -> None:
        try:
            while True:
                kind, value = self.q.get_nowait()
                if kind == "img":
                    self._show_preview(value)
                elif kind == "err":
                    self._set_status("Error")
                    self._set_preview_message(str(value))
                elif kind == "status":
                    self._set_status(str(value))
                elif kind == "done":
                    self._set_busy(False)
        except queue.Empty:
            pass

    def _set_busy(self, busy: bool, status: str = "Ready") -> None:
        if busy:
            self._set_status(status)
            self.progress.setRange(0, 0)
            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:
            self.progress.setRange(0, 1)
            self.progress.setValue(0)
            self.run_btn.setEnabled(bool(self.paths))
            self.stop_btn.setEnabled(False)

    def _busy(self) -> bool:
        return self.worker is not None and self.worker.is_alive()

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.stop.set()
        event.accept()


def run_ui() -> int:
    return UI().mainloop()


if __name__ == "__main__":
    raise SystemExit(run_ui())
