"""Reader for Phantom ``.cine`` files."""

from __future__ import annotations

import os
import struct
from typing import Sequence

import numpy as np

from .base import FileReader
from .cine_parser import read_metadata
from .metadata import CineMetadata


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
            raw_metadata = dict(read_metadata(str(self.file_path)).__dict__)
            self._metadata = CineMetadata.from_cinereader_dict(raw_metadata)
        return self._metadata

    @property
    def frame_shape(self) -> tuple[int, int]:
        return self.header.frame_shape

    @property
    def total_frames(self) -> int:
        return self.header.num_frames

    @property
    def dtype(self) -> np.dtype:
        return np.dtype(np.float32)

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
