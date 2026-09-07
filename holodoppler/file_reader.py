from __future__ import annotations

import json
import os
import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

import cinereader
import numpy as np


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


@dataclass
class CineMetadata:
    """Relevant metadata from a Phantom .cine file."""

    biHeight: int
    biWidth: int
    biCompression: int
    biSizeImage: int
    TotalImageCount: int
    OffImageOffsets: int
    FirstImageNo: int
    RealBPP: int = 12
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_cinereader_dict(cls, metadata: dict[str, Any]) -> "CineMetadata":
        known_fields = {
            "biHeight",
            "biWidth",
            "biCompression",
            "biSizeImage",
            "TotalImageCount",
            "OffImageOffsets",
            "FirstImageNo",
            "RealBPP",
        }
        kwargs = {key: metadata[key] for key in known_fields if key in metadata}
        extra = {key: value for key, value in metadata.items() if key not in known_fields}
        return cls(**kwargs, extra=extra)

    @property
    def frame_shape(self) -> tuple[int, int]:
        return self.biHeight, self.biWidth

    @property
    def num_frames(self) -> int:
        return self.TotalImageCount


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


def unpack_12bitL_vectorized(
    data: bytes | np.ndarray,
    width: int,
    height: int,
) -> np.ndarray:
    """Unpack one Phantom P12L frame into uint16 pixels."""
    if width * height % 2:
        raise ValueError("12-bit packed format requires an even number of pixels.")

    byte_array = np.frombuffer(data, dtype=np.uint8)
    expected_bytes = (width * height * 3) // 2
    if byte_array.size != expected_bytes:
        raise ValueError(
            f"Expected {expected_bytes} packed bytes, got {byte_array.size}."
        )

    groups = byte_array.reshape(-1, 3)

    pixel0 = (groups[:, 0].astype(np.uint16) << 4) | (groups[:, 1] >> 4)
    pixel1 = (
        ((groups[:, 1] & 0x0F).astype(np.uint16) << 8)
        | groups[:, 2]
    )

    pixels = np.empty(width * height, dtype=np.uint16)
    pixels[0::2] = pixel0
    pixels[1::2] = pixel1
    return pixels.reshape(height, width)


def unpack_12bitL_batch_to_uint16(
    packed: np.ndarray,
    width: int,
    height: int,
) -> np.ndarray:
    """Example helper showing vectorized batch P12L unpacking.

    Kept as an example/utility only; ``CineFileReader`` does not use the
    batch helper internally.
    """
    packed = np.asarray(packed, dtype=np.uint8)
    if packed.ndim != 2:
        raise ValueError("packed must have shape (nframes, packed_bytes)")

    expected_bytes = (width * height * 3) // 2
    if packed.shape[1] != expected_bytes:
        raise ValueError(
            f"Expected {expected_bytes} packed bytes per frame, got {packed.shape[1]}."
        )

    groups = packed.reshape(packed.shape[0], -1, 3)
    b0 = groups[:, :, 0].astype(np.uint16)
    b1 = groups[:, :, 1].astype(np.uint16)
    b2 = groups[:, :, 2].astype(np.uint16)

    out = np.empty((packed.shape[0], width * height), dtype=np.uint16)
    out[:, 0::2] = (b0 << 4) | (b1 >> 4)
    out[:, 1::2] = ((b1 & 0x0F) << 8) | b2
    return out.reshape(packed.shape[0], height, width)


class CineFileReader(FileReader):
    """Reader for Phantom ``.cine`` files using regular file I/O.

    Unlike ``HoloFileReader``, this reader deliberately does not use mmap:
    .cine frames are located through an offset table and are decoded on demand.
    """

    extension = ".cine"

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        super().__init__(file_path)
        self._metadata: CineMetadata | None = None

    @property
    def header(self) -> CineMetadata:
        if self._metadata is None:
            raw_metadata = dict(cinereader.read_metadata(str(self.file_path)).__dict__)
            self._metadata = CineMetadata.from_cinereader_dict(raw_metadata)
        return self._metadata

    @property
    def frame_shape(self) -> tuple[int, int]:
        return self.header.frame_shape

    @property
    def total_frames(self) -> int:
        return self.header.num_frames

    def _read_offsets(
        self,
        file,
        first_frame: int,
        count: int,
    ) -> np.ndarray:
        """Read ``count`` frame offsets using the existing .cine index layout."""
        if count < 0:
            raise ValueError("count must be >= 0")

        md = self.header
        corrected = first_frame - md.num_frames + 1 - md.FirstImageNo
        file.seek(md.OffImageOffsets + corrected * 8)

        raw = file.read(count * 8)
        if len(raw) != count * 8:
            raise EOFError(
                f"Could not read enough frame offsets: requested {count}"
            )

        return np.frombuffer(raw, dtype=np.int64)

    def _read_frame(
        self,
        file,
        offset: int,
    ) -> np.ndarray:
        """Read and decode one frame without memory-mapping the .cine file."""
        md = self.header
        if offset <= 0:
            raise ValueError(f"Invalid frame offset: {offset}")

        file.seek(offset)
        annotation_size_bytes = file.read(4)
        if len(annotation_size_bytes) != 4:
            raise EOFError("Could not read frame annotation size.")

        annotation_size = struct.unpack("I", annotation_size_bytes)[0]
        data_start = offset + annotation_size

        file.seek(data_start)
        packed = file.read(md.biSizeImage)
        if len(packed) != md.biSizeImage:
            raise EOFError(
                f"Could not read complete frame payload: "
                f"expected {md.biSizeImage}, got {len(packed)}"
            )

        if md.biCompression == 1024:
            frame = unpack_12bitL_vectorized(
                packed,
                width=md.biWidth,
                height=md.biHeight,
            )
        elif md.biCompression == 256:
            raise NotImplementedError("10-bit unpacking is not implemented.")
        else:
            raise NotImplementedError(
                f"Unsupported .cine compression: {md.biCompression}"
            )

        return frame.astype(np.float32, copy=False)

    def _read_frames_by_indices(
        self,
        file,
        indices: np.ndarray,
    ) -> list[np.ndarray]:
        frames: list[np.ndarray] = []
        for index in indices:
            offset = self._read_offsets(file, int(index), 1)[0]
            frames.append(self._read_frame(file, int(offset)))
        return frames

    def read_frames(
        self,
        first_frame: int = 0,
        batch_size: int = 1,
        skip_every: int | None = None,
    ) -> np.ndarray:
        self._validate_read_request(first_frame, batch_size, skip_every)

        step = 1 if skip_every is None else skip_every
        indices = first_frame + np.arange(batch_size, dtype=np.int64) * step

        if np.any(indices >= self.total_frames):
            raise IndexError(
                f"Requested frames exceed file bounds: "
                f"first={first_frame}, batch_size={batch_size}, step={step}, "
                f"total_frames={self.total_frames}"
            )

        with self.file_path.open("rb") as file:
            frames = self._read_frames_by_indices(file, indices)

        return frames[0] if batch_size == 1 else np.stack(frames, axis=0)

    def read_selected_frames(self, indices: Sequence[int]) -> np.ndarray:
        if not indices:
            return np.empty((0, *self.frame_shape), dtype=np.float32)

        indices_array = np.asarray(indices, dtype=np.int64)
        if np.any(indices_array < 0) or np.any(indices_array >= self.total_frames):
            raise IndexError("All frame indices must be within [0, total_frames).")

        with self.file_path.open("rb") as file:
            frames = self._read_frames_by_indices(file, indices_array)

        return frames[0] if len(frames) == 1 else np.stack(frames, axis=0)

    def __repr__(self) -> str:
        try:
            header = self.header
        except Exception:
            return f"CineFileReader('{self.file_path}') [unreadable]"

        return (
            f"CineFileReader('{self.file_path}')\n"
            f"  Resolution: {header.biWidth}x{header.biHeight}\n"
            f"  Frames: {header.num_frames}\n"
            f"  Compression: {header.biCompression}"
        )


class FileReaderFactory:
    """Create a reader from the file extension."""

    _READERS = {
        ".holo": HoloFileReader,
        ".cine": CineFileReader,
    }

    @staticmethod
    def create(file_path: str | os.PathLike[str]) -> FileReader:
        path = Path(file_path)
        try:
            reader_cls = FileReaderFactory._READERS[path.suffix.lower()]
        except KeyError as exc:
            supported = ", ".join(sorted(FileReaderFactory._READERS))
            raise ValueError(
                f"Unsupported file extension '{path.suffix}'. "
                f"Supported extensions: {supported}"
            ) from exc

        return reader_cls(path)
