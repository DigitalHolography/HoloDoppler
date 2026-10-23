"""Shared application logging, using only Python's standard library.

In a processing file, simply use::

    from holodoppler.logging import logger

    logger.info("Processing started")
    logger.debug("Batch size: %s", batch_size)
    logger.warning("Some frames were skipped")
    logger.error("The input file could not be read")

Use ``logger.exception("Processing failed")`` inside an ``except`` block to
include its traceback. Application entrypoints configure the destinations once.
"""

from __future__ import annotations

from contextlib import contextmanager
import logging
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
import multiprocessing
import os
from pathlib import Path
import re
import sys
import threading

from .get_version import get_version


LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3

logger = logging.getLogger("holodoppler")
logger.addHandler(logging.NullHandler())

_configuration_lock = threading.RLock()
_configured = False
_log_path: Path | None = None


def get_log_path() -> Path:
    """Return the shared CLI/GUI log location without importing the GUI."""
    if _log_path is not None:
        return _log_path

    if os.name == "nt":
        base_dir = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        base_dir = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")

    try:
        app_version = get_version()
    except (OSError, ValueError, ImportError):
        app_version = "dev"
    version_dir = re.sub(r"[^A-Za-z0-9_.-]+", "_", app_version).strip("._") or "dev"
    return base_dir / "HoloDoppler" / version_dir / "logs" / "holodoppler.log"


def _stream_is_writable(stream: object) -> bool:
    return (
        stream is not None
        and not getattr(stream, "closed", False)
        and callable(getattr(stream, "write", None))
        and callable(getattr(stream, "flush", None))
    )


class _ConsoleHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        # Embedded callers and test runners may replace and close stderr.
        if not _stream_is_writable(self.stream):
            self.stream = next(
                (stream for stream in (sys.stderr, sys.stdout) if _stream_is_writable(stream)),
                None,
            )
        if self.stream is not None:
            super().emit(record)


def ensure_standard_streams() -> None:
    """Give windowed executables writable streams for tqdm and native libraries.

    Call after logging configuration so these fallback streams are never used
    as console log destinations. Application logs use the shared file instead.
    """
    for name in ("stdout", "stderr"):
        if not _stream_is_writable(getattr(sys, name)):
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))


def _log_unhandled_exception(exc_type, exc_value, exc_traceback) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))


def _log_thread_exception(args) -> None:
    if args.exc_type is SystemExit:
        return
    thread_name = args.thread.name if args.thread is not None else "unknown"
    logger.error(
        "Unhandled exception in thread %s",
        thread_name,
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


def configure_logging(*, log_path: str | Path | None = None) -> logging.Logger:
    """Configure DEBUG and above once, preserving any additional GUI handlers.

    Normal runs and packaged executables use the same rotating UTF-8 log file
    and format. A real console, when available, receives identical messages.
    ``log_path`` is an optional override for embedding or isolated tests.
    """
    global _configured, _log_path

    with _configuration_lock:
        if _configured:
            return logger

        path = Path(log_path).expanduser().resolve() if log_path is not None else get_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        file_handler = RotatingFileHandler(
            path,
            maxBytes=MAX_LOG_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
            errors="backslashreplace",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        console = next(
            (stream for stream in (sys.stderr, sys.stdout) if _stream_is_writable(stream)),
            None,
        )
        if console is not None:
            console_handler = _ConsoleHandler(console)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG)
            logger.addHandler(console_handler)

        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        _log_path = path
        _configured = True
        sys.excepthook = _log_unhandled_exception
        threading.excepthook = _log_thread_exception
        return logger


def configure_worker_logging(log_queue) -> None:
    """Pool initializer: forward worker logs to the parent file, console and GUI."""
    global _configured

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logger.addHandler(QueueHandler(log_queue))
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    _configured = True
    sys.excepthook = _log_unhandled_exception
    threading.excepthook = _log_thread_exception


@contextmanager
def worker_logging_queue():
    """Keep this context open until all workers using its queue have finished."""
    configure_logging()
    log_queue = multiprocessing.Queue()
    listener = QueueListener(log_queue, *logger.handlers, respect_handler_level=True)
    listener.start()
    try:
        yield log_queue
    finally:
        listener.stop()
        log_queue.close()
        log_queue.join_thread()
