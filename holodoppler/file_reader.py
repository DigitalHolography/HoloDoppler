"""
File I/O for .holo and .cine files
"""

import os
import cinereader
from numba import njit, prange
import json
import traceback
from typing import Optional, Iterator, Tuple, List
from dataclasses import dataclass
import mmap
import struct
import numpy as np


@dataclass
class FileHeader:
    """Parsed binary file header information."""

    magic_number: str
    version: int
    bit_depth: int
    width: int
    height: int
    num_frames: int
    total_size: int
    endianness: int  # 0 for little, 1 for big

    @property
    def bytes_per_pixel(self) -> int:
        return self.bit_depth // 8

    @property
    def frame_size_bytes(self) -> int:
        return self.width * self.height * self.bytes_per_pixel

    def get_dtype(self) -> np.dtype:
        """Get numpy dtype based on bit depth and endianness."""
        byte_order = "<" if self.endianness == 0 else ">"
        if self.bit_depth == 8:
            return np.dtype(f"{byte_order}u1")
        elif self.bit_depth == 16:
            return np.dtype(f"{byte_order}u2")
        elif self.bit_depth == 32:
            return np.dtype(f"{byte_order}f4")
        elif self.bit_depth == 64:
            return np.dtype(f"{byte_order}f8")
        else:
            raise ValueError(f"Unsupported bit depth: {self.bit_depth}")

class HoloFileReader:
    """Reader for .holo files with frame/batch iteration capabilities using memory mapping."""

    HEADER_SIZE = 64

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_header: Optional[FileHeader] = None
        self.file_footer: Optional[dict] = None
        self._frame_data: Optional[np.memmap] = None
        self._read_header()
        self._read_footer()

    def _read_header(self) -> FileHeader:
        """Read and parse the 64-byte file header from self.file_path."""
        with open(self.file_path, "rb") as f:
            header_bytes = f.read(self.HEADER_SIZE)

        if len(header_bytes) < self.HEADER_SIZE:
            raise ValueError(
                f"File too small to contain {self.HEADER_SIZE}-byte header"
            )

        self.file_header = FileHeader(
            magic_number=header_bytes[0:4].decode("ascii", errors="replace"),
            version=int.from_bytes(header_bytes[4:6], "little"),
            bit_depth=int.from_bytes(header_bytes[6:8], "little"),
            width=int.from_bytes(header_bytes[8:12], "little"),
            height=int.from_bytes(header_bytes[12:16], "little"),
            num_frames=int.from_bytes(header_bytes[16:20], "little"),
            total_size=int.from_bytes(header_bytes[20:28], "little"),
            endianness=header_bytes[28],
        )
        return self.file_header

    def _read_footer(self) -> dict:
        """Read optional JSON footer from the end of the file."""
        if self.file_header is None:
            self._read_header()

        # Calculate footer offset using header info
        data_end = (
            self.HEADER_SIZE
            + self.file_header.num_frames * self.file_header.frame_size_bytes
        )

        with open(self.file_path, "rb") as f:
            f.seek(data_end)
            footer_bytes = f.read()

        if footer_bytes:
            try:
                self.file_footer = json.loads(footer_bytes.decode("utf-8"))
            except Exception:
                self.file_footer = {}
        else:
            self.file_footer = {}
        return self.file_footer

    @property
    def header(self) -> FileHeader:
        """Lazy-load and return the file header."""
        if self.file_header is None:
            self._read_header()
        return self.file_header

    @property
    def footer(self) -> dict:
        """Lazy-load and return the file footer."""
        if self.file_footer is None:
            self._read_footer()
        return self.file_footer

    def _get_frame_data(self) -> np.memmap:
        """Get memory-mapped view of all frames."""
        if self._frame_data is None:
            self._frame_data = np.memmap(
                self.file_path,
                dtype=self.header.get_dtype(),
                mode="r",
                offset=self.HEADER_SIZE,
                order="C",
                shape=(self.header.num_frames, self.header.height, self.header.width),
            )
        return self._frame_data

    def read_frames(
        self,
        first_frame: int = 0,
        batch_size: int = 1,
        skip_every: Optional[int] = None,
    ) -> np.ndarray:
        """
        Read frames from the memory-mapped file.
        
        Args:
            first_frame: Index of first frame to read (0-based)
            batch_size: Number of frames to read
            skip_every: Read only 1 out of N frames (e.g., 4 = every 4th frame)
            
        Returns:
            numpy array of shape (batch_size, height, width) or (height, width) if batch_size=1
        """
        frames = self._get_frame_data()
        end_frame = first_frame + batch_size * (skip_every or 1)
        
        if skip_every is not None and skip_every > 1:
            indices = np.arange(first_frame, end_frame, skip_every)
            result = frames[indices]
        else:
            result = frames[first_frame:end_frame]
        
        if batch_size == 1 and (skip_every is None or skip_every == 1):
            return result[0]  # Return single frame without extra dimension
        return result

    # ===== CONTEXT MANAGER SUPPORT =====

    def __enter__(self):
        """Enable use as context manager."""
        _ = self.header  # Ensure header is loaded
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up memory-mapped object."""
        if self._frame_data is not None:
            del self._frame_data
            self._frame_data = None

    @property
    def total_frames(self) -> int:
        """Get total number of frames in the file."""
        return self.header.num_frames

    def __repr__(self) -> str:
        if self.file_header is None:
            try:
                _ = self.header
            except Exception:
                return f"HoloFileReader('{self.file_path}') [unreadable]"

        return (
            f"HoloFileReader('{self.file_path}')\n"
            f"  Magic: {self.header.magic_number} v{self.header.version}\n"
            f"  Resolution: {self.header.width}x{self.header.height}\n"
            f"  Bit depth: {self.header.bit_depth}, "
            f"Endianness: {'big' if self.header.endianness == 1 else 'little'}\n"
            f"  Frames: {self.header.num_frames}, "
            f"Size: {self.header.total_size} bytes"
        )


@njit
def _unpack_12bitL(data: bytes, width: int, height: int) -> np.ndarray:
    """Unpacks a 12-bit L byte array into a 2D numpy array of uint16s."""
    byte_array = np.frombuffer(data, dtype=np.uint8)
    image = np.zeros((height, width), dtype=np.uint16)
    for row in range(height):
        for col in prange(0, width, 2):
            idx = (row * width + col) // 2 * 3
            image[row, col] = (byte_array[idx] << 4) | (byte_array[idx + 1] >> 4)
            if col + 1 < width:
                image[row, col + 1] = (
                    (byte_array[idx + 1] & 0b00001111) << 8
                ) | byte_array[idx + 2]
    return image


def unpack_12bitL_vectorized(data: bytes, width: int, height: int) -> np.ndarray:
    # data length must be (width * height * 3) // 2
    byte_array = np.frombuffer(data, dtype=np.uint8)
    # print(byte_array.shape)
    # print((width * height * 3) // 2)
    # Group into 3‑byte chunks
    groups = byte_array.reshape(-1, 3)  # shape (N, 3)
    # First pixel: (byte0 << 4) | (byte1 >> 4)
    pixel0 = (groups[:, 0].astype(np.uint16) << 4) | (groups[:, 1] >> 4)
    # Second pixel: ((byte1 & 0x0F) << 8) | byte2
    pixel1 = ((groups[:, 1] & 0x0F).astype(np.uint16) << 8) | groups[:, 2]
    # Interleave (pixel0, pixel1, pixel0, pixel1, ...)
    pixels = np.empty(len(groups) * 2, dtype=np.uint16)
    pixels[0::2] = pixel0
    pixels[1::2] = pixel1
    return pixels.reshape(height, width)


def unpack_12bitL_batch_to_uint16(
    packed: np.ndarray,
    width: int,
    height: int,
) -> np.ndarray:
    packed = np.asarray(packed, dtype=np.uint8)

    nframes = packed.shape[0]
    n_pixels = width * height
    groups = packed.reshape(nframes, -1, 3)

    out = np.empty((nframes, n_pixels), dtype=np.uint16)

    b0 = groups[:, :, 0].astype(np.uint16)
    b1 = groups[:, :, 1].astype(np.uint16)
    b2 = groups[:, :, 2].astype(np.uint16)

    out[:, 0::2] = (b0 << 4) | (b1 >> 4)
    out[:, 1::2] = ((b1 & 0x0F) << 8) | b2

    return out.reshape(nframes, height, width)


def unpack_12bitL_batch_to_float32(
    packed: np.ndarray,
    width: int,
    height: int,
) -> np.ndarray:
    """
    Vectorized Phantom P12L unpacking across multiple frames.

    Parameters
    ----------
    packed : np.ndarray, shape (nframes, packed_bytes), dtype=uint8
        Packed 12-bit data. Each 3 bytes encode 2 pixels.
    width, height : int

    Returns
    -------
    frames : np.ndarray, shape (nframes, height, width), dtype=float32
    """
    packed = np.asarray(packed, dtype=np.uint8)

    nframes = packed.shape[0]
    n_pixels = width * height
    expected_bytes = (n_pixels * 3) // 2

    if packed.shape[1] != expected_bytes:
        raise ValueError(
            f"Expected {expected_bytes} packed bytes per frame, "
            f"got {packed.shape[1]}"
        )

    if n_pixels % 2 != 0:
        raise ValueError("12-bit packed format requires an even number of pixels")

    groups = packed.reshape(nframes, -1, 3)

    out = np.empty((nframes, n_pixels), dtype=np.float32)

    b0 = groups[:, :, 0].astype(np.uint16)
    b1 = groups[:, :, 1].astype(np.uint16)
    b2 = groups[:, :, 2].astype(np.uint16)

    out[:, 0::2] = (b0 << 4) | (b1 >> 4)
    out[:, 1::2] = ((b1 & 0x0F) << 8) | b2

    return out.reshape(nframes, height, width)


def unpack_12bitL_batch_to_float32_fast(
    packed: np.ndarray,
    width: int,
    height: int,
) -> np.ndarray:
    packed = np.asarray(packed, dtype=np.uint8)

    nframes = packed.shape[0]
    n_pixels = width * height
    groups = packed.reshape(nframes, -1, 3)

    out = np.empty((nframes, n_pixels), dtype=np.float32)

    b0 = groups[:, :, 0].astype(np.uint16)
    b1 = groups[:, :, 1].astype(np.uint16)

    out[:, 0::2] = (b0 << 4) | (b1 >> 4)
    out[:, 1::2] = ((b1 & 0x0F) << 8) | groups[:, :, 2]

    return out.reshape(nframes, height, width)


# def unpack_12bit_to_8bit_vectorized(data: bytes, width: int, height: int) -> np.ndarray:
#     byte_array = np.frombuffer(data, dtype=np.uint8)
#     groups = byte_array.reshape(-1, 3)
#     # pixel0's top 8 bits = byte0
#     pixel0 = groups[:, 0]                                   # uint8
#     # pixel1's top 8 bits = ((byte1 & 0x0F) << 4) | (byte2 >> 4)
#     pixel1 = ((groups[:, 1] & 0x0F) << 4) | (groups[:, 2] >> 4)
#     # Interleave
#     pixels = np.empty(len(groups) * 2, dtype=np.uint8)
#     pixels[0::2] = pixel0
#     pixels[1::2] = pixel1
#     return pixels.reshape(height, width)


@dataclass
class CineMetadata:
    """Parsed .cine file metadata."""

    biHeight: int
    biWidth: int
    biCompression: int
    biSizeImage: int
    TotalImageCount: int
    OffImageOffsets: int
    FirstImageNo: int
    RealBPP: int = 12  # default for Phantom

    # Store any additional metadata from cinereader
    extra: dict = None

    @classmethod
    def from_cinereader_dict(cls, metadata_dict: dict) -> "CineMetadata":
        """Create CineMetadata from cinereader's metadata dict."""
        # Extract known fields, store rest in extra
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
        kwargs = {k: metadata_dict[k] for k in known_fields if k in metadata_dict}
        extra = {k: v for k, v in metadata_dict.items() if k not in known_fields}
        return cls(**kwargs, extra=extra if extra else None)

    @property
    def frame_shape(self) -> tuple:
        """Get frame shape (height, width)."""
        return (self.biHeight, self.biWidth)

    @property
    def num_frames(self) -> int:
        """Total number of frames."""
        return self.TotalImageCount


class CineFileReader:
    """Reader for .cine files - iterator-based, no persistent file handles."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.metadata: Optional[CineMetadata] = None

    def open(self):
        """Compatibility method - does nothing."""
        pass

    def close(self):
        """Compatibility method - does nothing."""
        pass

    def _read_metadata(self) -> CineMetadata:
        """Read metadata from .cine file using cinereader."""
        raw_metadata = dict(cinereader.read_metadata(self.file_path).__dict__)
        self.metadata = CineMetadata.from_cinereader_dict(raw_metadata)
        return self.metadata

    @property
    def header(self) -> CineMetadata:
        """Lazy-load and return the file metadata."""
        if self.metadata is None:
            self._read_metadata()
        return self.metadata

    @property
    def footer(self) -> dict:
        return {}

    def _read_offsets(self, f, first_frame: int, count: int) -> np.ndarray:
        """Read frame offset table entries."""
        md = self.header
        first_frame_corrected = first_frame - md.num_frames + 1 - md.FirstImageNo

        f.seek(md.OffImageOffsets + first_frame_corrected * 8)
        offsets_bytes = f.read(count * 8)

        if len(offsets_bytes) != count * 8:
            raise EOFError(f"Could not read enough frame offsets: requested {count}")

        return np.frombuffer(offsets_bytes, dtype=np.int64)

    def _read_single_frame_mmap(
        self,
        mm: mmap.mmap,
        offset: int,
        compression: int,
        frame_image_size: int,
        w: int,
        h: int,
    ) -> np.ndarray:
        """Read and unpack a single frame from memory-mapped file."""
        if offset == 0:
            raise ValueError("Invalid offset for frame")

        ann_size = struct.unpack_from("I", mm, offset)[0]
        data_start = offset + ann_size

        if compression == 1024:  # 12-bit packed (Phantom P12L)
            # Assuming unpack_12bitL_vectorized or similar function exists
            img = unpack_12bitL_vectorized(
                mm[data_start : data_start + frame_image_size], w, h
            )
        elif compression == 256:  # 10-bit packed
            raise NotImplementedError("10-bit unpacking not implemented")
        else:
            raise NotImplementedError(f"Compression {compression} not supported")

        return img.astype(np.float32)

    def iter_frames(
        self,
        batch_size: int = 1,
        batch_stride: Optional[int] = None,
        skip_every: Optional[int] = None,
        end_frame: Optional[int] = None,
        first_frame: int = 0,
    ) -> Iterator[np.ndarray]:
        """
        Iterator over batches of frames from .cine file.

        Args:
            batch_size: Number of frames per batch (default 1 for single frames)
            batch_stride: Stride between batch starts (default: batch_size)
            skip_every: Read only 1 out of N frames
            end_frame: Index of last frame to take into account in the file
            first_frame: Index of first frame to read (0-based)

        Yields:
            numpy arrays of shape (batch_size, height, width) or (height, width) if batch_size=1

        Example:
            reader = CineFileReader("video.cine")
            for batch in reader.read_frames(batch_size=16, batch_stride=8):
                gpu_process(batch)
        """
        if batch_stride is None:
            batch_stride = batch_size

        md = self.header
        h, w = md.biHeight, md.biWidth
        compression = md.biCompression
        frame_image_size = md.biSizeImage

        if end_frame is None:
            end_frame = md.num_frames

        total_available = end_frame - first_frame

        with open(self.file_path, "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                buffer = []
                frames_in_buffer = 0
                frames_since_last_batch = 0
                batches_yielded = 0
                total_frames_encountered = 0
                frames_read = 0

                for frame_idx in range(total_available):

                    # Apply frame skipping
                    total_frames_encountered += 1
                    if skip_every is not None and skip_every > 1:
                        if (total_frames_encountered - 1) % skip_every != 0:
                            continue

                    # Handle striding between batches
                    if frames_in_buffer == 0:
                        frames_since_last_batch += 1
                        if frames_since_last_batch < batch_stride and len(buffer) > 0:
                            frames_read += 1
                            continue

                    # Read frame offset and data
                    current_frame = first_frame + frame_idx
                    try:
                        offsets = self._read_offsets(f, current_frame, 1)
                        img = self._read_single_frame_mmap(
                            mm, offsets[0], compression, frame_image_size, w, h
                        )
                    except (EOFError, ValueError):
                        break  # End of available frames

                    frames_read += 1
                    buffer.append(img)
                    frames_in_buffer += 1

                    if frames_in_buffer == batch_size:
                        # Yield batch
                        if batch_size == 1:
                            yield buffer[0]
                        else:
                            yield np.stack(buffer, axis=0)

                        batches_yielded += 1

                        # Prepare for next batch
                        if batch_stride < batch_size:
                            overlap = batch_size - batch_stride
                            buffer = buffer[-overlap:] if overlap > 0 else []
                            frames_in_buffer = len(buffer)
                        else:
                            buffer = []
                            frames_in_buffer = 0

                        frames_since_last_batch = 0

    def read_selected_frames(self, indices: List[int]) -> Iterator[np.ndarray]:
        """
        Read specific frame indices (random access).

        Args:
            indices: List of 0-based frame indices to read

        Yields:
            numpy arrays of shape (height, width)
        """
        md = self.header
        h, w = md.biHeight, md.biWidth
        compression = md.biCompression
        frame_image_size = md.biSizeImage

        with open(self.file_path, "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                for idx in sorted(indices):
                    if idx >= md.num_frames:
                        continue
                    try:
                        offsets = self._read_offsets(f, idx, 1)
                        img = self._read_single_frame_mmap(
                            mm, offsets[0], compression, frame_image_size, w, h
                        )
                        yield img
                    except (EOFError, ValueError):
                        continue

    def read_frames(
        self,
        first_frame: int = 0,
        batch_size: int = 1,
        skip_every: Optional[int] = None,
    ) -> np.ndarray:
        return next(
            self.iter_frames(
                batch_size=batch_size, skip_every=skip_every, first_frame=first_frame
            )
        )

    # ===== FAST BATCH READING (preserved from original for performance) =====

    def read_frames_batch(self, first_frame: int, frame_batchsize: int) -> np.ndarray:
        """
        Fast batch read of consecutive frames (preserved from original API).

        Returns:
            np.ndarray, shape (frame_batchsize, height, width), dtype=np.float32
        """
        md = self.header
        h, w = md.biHeight, md.biWidth
        compression = md.biCompression
        frame_image_size = md.biSizeImage

        with open(self.file_path, "rb") as f:
            offsets = self._read_offsets(f, first_frame, frame_batchsize)

            if compression != 1024:
                raise NotImplementedError(
                    "Only Phantom P12L 12-bit packed compression=1024 supported"
                )

            packed = np.empty((frame_batchsize, frame_image_size), dtype=np.uint8)

            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                for i, img_start in enumerate(offsets):
                    ann_size = struct.unpack_from("I", mm, img_start)[0]
                    data_start = img_start + ann_size

                    packed[i] = np.frombuffer(
                        mm, dtype=np.uint8, count=frame_image_size, offset=data_start
                    )

            frames = unpack_12bitL_batch_to_uint16(packed, w, h)
            return frames.astype(np.float32)

    # ===== CONTEXT MANAGER SUPPORT =====

    def __enter__(self):
        _ = self.header  # Ensure metadata is loaded
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def frame_shape(self) -> tuple:
        """Get the shape of individual frames (height, width)."""
        return self.header.frame_shape

    @property
    def total_frames(self) -> int:
        """Get total number of frames in the file."""
        return self.header.num_frames

    def __repr__(self) -> str:
        if self.metadata is None:
            try:
                _ = self.header
            except Exception:
                return f"CineFileReader('{self.file_path}') [unreadable]"

        return (
            f"CineFileReader('{self.file_path}')\n"
            f"  Resolution: {self.header.biWidth}x{self.header.biHeight}\n"
            f"  Frames: {self.header.num_frames}\n"
            f"  Compression: {self.header.biCompression}"
        )


class FileReaderFactory:
    """Factory to create appropriate file reader"""

    @staticmethod
    def create(file_path):
        _, ext = os.path.splitext(file_path)

        if ext == ".holo":
            reader = HoloFileReader(file_path)
        elif ext == ".cine":
            reader = CineFileReader(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        reader.ext = ext
        return reader
