"""Common reader abstraction and factory.

Reader classes are resolved lazily by :class:`FileReaderFactory` so that this
module does not depend on the concrete readers, which in turn import it.
"""

from __future__ import annotations

import importlib
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Sequence

import numpy as np


class FileReader(ABC):
    """Common array-based interface for supported file readers.

    Readers are intentionally not iterable. Callers explicitly request the
    frames they need through ``read_frames`` or ``read_selected_frames``.
    """

    extension: str = ""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self.file_path = Path(file_path)

    def open(self) -> "FileReader":
        """Compatibility hook; readers are usable without calling ``open``."""
        return self

    def close(self) -> None:
        pass

    def __enter__(self) -> "FileReader":
        return self.open()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    @property
    @abstractmethod
    def frame_shape(self) -> tuple[int, int]:
        """Shape of one frame as ``(height, width)``."""

    @property
    @abstractmethod
    def total_frames(self) -> int:
        """Total number of frames in the file."""

    @property
    @abstractmethod
    def header(self) -> Any:
        """Parsed file header / metadata."""

    @property
    @abstractmethod
    def dtype(self) -> np.dtype:
        """NumPy dtype of a single frame as returned by this reader."""

    @property
    def footer(self) -> dict[str, Any]:
        return {}

    @abstractmethod
    def read_frames(
        self,
        first_frame: int = 0,
        batch_size: int = 1,
        skip_every: int | None = None,
    ) -> np.ndarray:
        """Read a batch of frames as an ndarray."""

    @abstractmethod
    def read_selected_frames(self, indices: Sequence[int]) -> np.ndarray:
        """Read selected frame indices as a stacked ndarray."""

    def _validate_read_request(
        self,
        first_frame: int,
        batch_size: int,
        skip_every: int | None,
    ) -> None:
        if first_frame < 0:
            raise ValueError("first_frame must be >= 0")
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if skip_every is not None and skip_every <= 0:
            raise ValueError("skip_every must be > 0")


class FileReaderFactory:
    """Create a reader from the file extension."""

    #: file extension -> (sub-module name, class name)
    _READERS: dict[str, tuple[str, str]] = {
        ".holo": ("holo", "HoloFileReader"),
        ".cine": ("cine", "CineFileReader"),
    }

    @staticmethod
    def supported_extensions() -> list[str]:
        """Return the supported file extensions."""
        return sorted(FileReaderFactory._READERS)

    @staticmethod
    def create(file_path: str | os.PathLike[str]) -> "FileReader":
        """Return the reader matching ``file_path``'s extension.

        Extension matching is case-insensitive.
        """
        path = Path(file_path)
        entry = FileReaderFactory._READERS.get(path.suffix.lower())

        if entry is None:
            supported = ", ".join(FileReaderFactory.supported_extensions())
            raise ValueError(
                f"Unsupported file extension '{path.suffix}'. "
                f"Supported extensions: {supported}"
            )

        module_name, class_name = entry
        module = importlib.import_module(f".{module_name}", package=__package__)

        return getattr(module, class_name)(path)


def get_reader(file_path: str | os.PathLike[str]) -> FileReader:
    """Return the reader matching a file path's extension.

    Extension matching is case-insensitive, so ``.HOLO`` and ``.CINE`` work as
    well as their lowercase forms.

    Parameters
    ----------
    file_path:
        Path to a ``.holo`` or ``.cine`` file.

    Returns
    -------
    FileReader
        ``HoloFileReader`` or ``CineFileReader``.

    Raises
    ------
    ValueError
        When the extension is not supported.

    Examples
    --------
    >>> reader = get_reader("acquisition.holo")
    >>> frames = reader.read_frames(first_frame=0, batch_size=8)
    """
    return FileReaderFactory.create(file_path)
