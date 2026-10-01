"""Reader for HoloVibes ``.holo`` files."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .base import FileReader


@dataclass(frozen=True)
class FileHeader:
    """Parsed binary .holo file header."""

    magic_number: str
    version: int
    bit_depth: int
    width: int
    height: int
    num_frames: int
    total_size: int
    endianness: int  # 0 = little-endian, 1 = big-endian

    @property
    def frame_shape(self) -> tuple[int, int]:
        return self.height, self.width

    @property
    def bytes_per_pixel(self) -> int:
        if self.bit_depth not in (8, 16, 32, 64):
            raise ValueError(f"Unsupported bit depth: {self.bit_depth}")
        return self.bit_depth // 8

    @property
    def frame_size_bytes(self) -> int:
        return self.width * self.height * self.bytes_per_pixel

    def get_dtype(self) -> np.dtype:
        byte_order = "<" if self.endianness == 0 else ">"

        dtype_by_bit_depth = {
            8: np.dtype(f"{byte_order}u1"),
            16: np.dtype(f"{byte_order}u2"),
            32: np.dtype(f"{byte_order}f4"),
            64: np.dtype(f"{byte_order}f8"),
        }

        try:
            return dtype_by_bit_depth[self.bit_depth]
        except KeyError as exc:
            raise ValueError(f"Unsupported bit depth: {self.bit_depth}") from exc


class HoloFileReader(FileReader):
    """Reader for ``.holo`` files using NumPy memmap for frame data."""

    HEADER_SIZE = 64
    extension = ".holo"

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        super().__init__(file_path)
        self._header: FileHeader | None = None
        self._footer: dict[str, Any] | None = None
        self._frame_data: np.memmap | None = None

    @property
    def header(self) -> FileHeader:
        if self._header is None:
            self._header = self._read_header()
        return self._header

    @property
    def footer(self) -> dict[str, Any]:
        if self._footer is None:
            self._footer = self._read_footer()
        return self._footer

    @property
    def frame_shape(self) -> tuple[int, int]:
        return self.header.frame_shape

    @property
    def total_frames(self) -> int:
        return self.header.num_frames

    @property
    def dtype(self) -> np.dtype:
        return self.header.get_dtype()

    def open(self) -> "HoloFileReader":
        self._get_memmap()
        return self

    def close(self) -> None:
        if self._frame_data is None:
            return

        mmap_handle = getattr(self._frame_data, "_mmap", None)
        if mmap_handle is not None and not mmap_handle.closed:
            mmap_handle.close()
        self._frame_data = None

    def _read_header(self) -> FileHeader:
        with self.file_path.open("rb") as file:
            data = file.read(self.HEADER_SIZE)

        if len(data) < self.HEADER_SIZE:
            raise ValueError(
                f"File too small to contain {self.HEADER_SIZE}-byte header: {self.file_path}"
            )

        return FileHeader(
            magic_number=data[0:4].decode("ascii", errors="replace"),
            version=int.from_bytes(data[4:6], "little"),
            bit_depth=int.from_bytes(data[6:8], "little"),
            width=int.from_bytes(data[8:12], "little"),
            height=int.from_bytes(data[12:16], "little"),
            num_frames=int.from_bytes(data[16:20], "little"),
            total_size=int.from_bytes(data[20:28], "little"),
            endianness=data[28],
        )

    def _read_footer(self) -> dict[str, Any]:
        data_end = self.HEADER_SIZE + self.header.num_frames * self.header.frame_size_bytes

        with self.file_path.open("rb") as file:
            file.seek(data_end)
            footer_bytes = file.read()

        if not footer_bytes:
            return {}

        try:
            return json.loads(footer_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}

    def _get_memmap(self) -> np.memmap:
        """Return the only data-access mechanism used by the .holo reader."""
        if self._frame_data is None:
            self._frame_data = np.memmap(
                self.file_path,
                dtype=self.header.get_dtype(),
                mode="r",
                offset=self.HEADER_SIZE,
                shape=(
                    self.header.num_frames,
                    self.header.height,
                    self.header.width,
                ),
                order="C",
            )
        return self._frame_data

    def read_frames(
        self,
        first_frame: int = 0,
        batch_size: int = 1,
        skip_every: int | None = None,
    ) -> np.ndarray:
        self._validate_read_request(first_frame, batch_size, skip_every)

        step = 1 if skip_every is None else skip_every
        indices = first_frame + np.arange(batch_size) * step

        if np.any(indices >= self.total_frames):
            raise IndexError(
                f"Requested frames exceed file bounds: "
                f"first={first_frame}, batch_size={batch_size}, step={step}, "
                f"total_frames={self.total_frames}"
            )

        frames = self._get_memmap()[indices]
        frames = np.asarray(frames)

        return frames[0] if batch_size == 1 else frames

    def read_selected_frames(self, indices: Sequence[int]) -> np.ndarray:
        if not indices:
            return np.empty((0, *self.frame_shape), dtype=self.header.get_dtype())

        indices_array = np.asarray(indices, dtype=np.int64)
        if np.any(indices_array < 0) or np.any(indices_array >= self.total_frames):
            raise IndexError("All frame indices must be within [0, total_frames).")

        frames = np.asarray(self._get_memmap()[indices_array])
        return frames[0] if frames.shape[0] == 1 else frames

    def __repr__(self) -> str:
        try:
            header = self.header
        except Exception:
            return f"HoloFileReader('{self.file_path}') [unreadable]"

        return (
            f"HoloFileReader('{self.file_path}')\n"
            f"  Magic: {header.magic_number} v{header.version}\n"
            f"  Resolution: {header.width}x{header.height}\n"
            f"  Bit depth: {header.bit_depth}, "
            f"Endianness: {'big' if header.endianness else 'little'}\n"
            f"  Frames: {header.num_frames}, Size: {header.total_size} bytes"
        )
