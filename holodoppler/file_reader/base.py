from __future__ import annotations

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

    def __new__(cls, file_path: str | os.PathLike[str]):
        if cls is FileReader:
            from .cine import CineFileReader
            from .holo import HoloFileReader

            suffix = Path(file_path).suffix.lower()
            readers = {".cine": CineFileReader, ".holo": HoloFileReader}
            try:
                cls = readers[suffix]
            except KeyError as exc:
                raise ValueError(
                    f"Unsupported file extension '{suffix}'. Supported extensions: .cine, .holo"
                ) from exc
        return object.__new__(cls)

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
