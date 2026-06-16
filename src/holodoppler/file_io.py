"""
File I/O for .holo and .cine files
"""

import os
import json
import numpy as np
import traceback
import cinereader
import struct
import mmap
from numba import njit, prange
import matplotlib.pyplot as plt

import struct
import json
import traceback
import numpy as np
from typing import Optional, Iterator, Tuple, List
from dataclasses import dataclass

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
        byte_order = '<' if self.endianness == 0 else '>'
        if self.bit_depth == 8:
            return np.dtype(f'{byte_order}u1')
        elif self.bit_depth == 16:
            return np.dtype(f'{byte_order}u2')
        elif self.bit_depth == 32:
            return np.dtype(f'{byte_order}f4')
        elif self.bit_depth == 64:
            return np.dtype(f'{byte_order}f8')
        else:
            raise ValueError(f"Unsupported bit depth: {self.bit_depth}")


class HoloFileReader:
    """Reader for .holo files with frame/batch iteration capabilities."""

    HEADER_SIZE = 64

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_header: Optional[FileHeader] = None
        self.file_footer: Optional[dict] = None

    def open(self):
        """Compatibility method - does nothing, kept for backward compatibility."""
        pass

    def close(self):
        """Compatibility method - does nothing, kept for backward compatibility."""
        pass

    def _read_header(self) -> FileHeader:
        """Read and parse the 64-byte file header from self.file_path."""
        with open(self.file_path, "rb") as f:
            header_bytes = f.read(self.HEADER_SIZE)
        
        if len(header_bytes) < self.HEADER_SIZE:
            raise ValueError(f"File too small to contain {self.HEADER_SIZE}-byte header")
        
        self.file_header = FileHeader(
            magic_number=header_bytes[0:4].decode('ascii', errors='replace'),
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
        data_end = self.HEADER_SIZE + self.file_header.num_frames * self.file_header.frame_size_bytes
        
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

    def _get_frame_at_offset(self, f, byte_offset: int) -> Optional[np.ndarray]:
        """Read a single frame at the given byte offset from an open file handle."""
        try:
            f.seek(byte_offset)
            frame_bytes = f.read(self.header.frame_size_bytes)
            if len(frame_bytes) == self.header.frame_size_bytes:
                frame = np.frombuffer(frame_bytes, dtype=self.header.get_dtype())
                return frame.reshape(
                    (self.header.height, self.header.width),
                    order="C"
                )
            return None
        except Exception:
            traceback.print_exc()
            return None

    def read_frames(
        self,
        batch_size: int = 1,
        batch_stride: Optional[int] = None,
        skip_every: Optional[int] = None,
        max_batches: Optional[int] = None,
        first_frame: int = 0,
        num_frames: Optional[int] = None,
    ) -> Iterator[np.ndarray]:
        """
        Iterator over batches of frames with configurable striding and skipping.
        
        Args:
            batch_size: Number of frames per batch (default: 1 for single frames)
            batch_stride: Stride between batch starts (default: batch_size, non-overlapping)
                         Set < batch_size for overlapping batches
            skip_every: Read only 1 out of N frames (e.g., 4 = every 4th frame)
            max_batches: Maximum number of batches to yield
            first_frame: Index of first frame to read (0-based)
            num_frames: Total number of frames to consider (default: all from first_frame)
        
        Yields:
            numpy arrays of shape (batch_size, height, width) or (height, width) if batch_size=1
        
        Example:
            reader = HoloFileReader("data.holo")
            
            # Single frames
            for frame in reader.read_frames(skip_every=4, max_batches=100):
                process(frame)  # frame shape: (height, width)
            
            # Batches with 50% overlap
            for batch in reader.read_frames(batch_size=16, batch_stride=8):
                gpu_process(batch)  # batch shape: (16, height, width)
        """
        if batch_stride is None:
            batch_stride = batch_size
        
        # Calculate frame range
        total_available = self.header.num_frames - first_frame
        if num_frames is not None:
            total_available = min(num_frames, total_available)
        
        frame_start_offset = self.HEADER_SIZE + first_frame * self.header.frame_size_bytes
        
        with open(self.file_path, "rb") as f:
            buffer = []
            frames_in_buffer = 0
            frames_since_last_batch = 0
            batches_yielded = 0
            total_frames_encountered = 0
            
            for frame_idx in range(total_available):
                if max_batches is not None and batches_yielded >= max_batches:
                    return
                
                # Apply frame skipping
                total_frames_encountered += 1
                if skip_every is not None and skip_every > 1:
                    if (total_frames_encountered - 1) % skip_every != 0:
                        continue
                
                # Handle striding between batches
                if frames_in_buffer == 0:
                    frames_since_last_batch += 1
                    if frames_since_last_batch < batch_stride and len(buffer) > 0:
                        continue  # Skip frames in stride gap
                
                # Read frame
                byte_offset = frame_start_offset + frame_idx * self.header.frame_size_bytes
                frame = self._get_frame_at_offset(f, byte_offset)
                if frame is None:
                    break
                
                buffer.append(frame)
                frames_in_buffer += 1
                
                if frames_in_buffer == batch_size:
                    # Yield batch
                    if batch_size == 1:
                        yield buffer[0]  # Return single frame without extra dimension
                    else:
                        yield np.stack(buffer, axis=0)
                    
                    batches_yielded += 1
                    
                    # Prepare for next batch
                    if batch_stride < batch_size:
                        # Keep overlap frames
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
            indices: List of 0-based frame indices to read (will be sorted)
        
        Yields:
            numpy arrays of shape (height, width)
        """
        frame_start = self.HEADER_SIZE
        
        with open(self.file_path, "rb") as f:
            for idx in sorted(indices):
                if idx >= self.header.num_frames:
                    continue
                byte_offset = frame_start + idx * self.header.frame_size_bytes
                frame = self._get_frame_at_offset(f, byte_offset)
                if frame is not None:
                    yield frame

    # ===== CONTEXT MANAGER SUPPORT =====
    
    def __enter__(self):
        """Enable use as context manager (auto-loads header)."""
        _ = self.header  # Ensure header is loaded
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Nothing to clean up since we don't hold file handles."""
        pass
    
    @property
    def frame_shape(self) -> Tuple[int, int]:
        """Get the shape of individual frames (height, width)."""
        return (self.header.height, self.header.width)
    
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

    def get_np_memmap(self) -> np.memmap:
        """Get a memory-mapped view of the frame data.
        
        WARNING: np.memmap will NOT apply frame skipping, striding, or batching.
        It gives you a raw view of all frames in the file.
        
        Also note: memmap dtype must match your data's bit depth and endianness.
        """
        return np.memmap(
            self.file_path,
            dtype=self.header.get_dtype(),
            mode='r',
            offset=self.HEADER_SIZE,
            order='C',
            shape=(
                self.header.num_frames,
                self.header.height,
                self.header.width
            )
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
    groups = byte_array.reshape(-1, 3)          # shape (N, 3)
    # First pixel: (byte0 << 4) | (byte1 >> 4)
    pixel0 = ((groups[:, 0].astype(np.uint16) << 4) | (groups[:, 1] >> 4))
    # Second pixel: ((byte1 & 0x0F) << 8) | byte2
    pixel1 = (((groups[:, 1] & 0x0F).astype(np.uint16) << 8) | groups[:, 2])
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

import mmap
import struct
import numpy as np


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

class CineFileReader:
    """Reader for .cine files"""

    def __init__(self, file_path):
        self.file_path = file_path
        self.fid = None
        self.metadata = None

    def open(self):
        if self.fid is not None:
            self.close()
        self.fid = open(self.file_path, "rb")
        self.metadata = dict(cinereader.read_metadata(self.file_path).__dict__)
        # print(self.metadata)

    def close(self):
        if self.fid is not None:
            self.fid.close()
            self.file_path = None
            self.metadata = None
            self.fid = None
            
    def read_frames_fastest(self, first_frame, frame_batchsize):
        """
        Read a batch of consecutive uncompressed frames as fast as possible.

        Returns
        -------
        np.ndarray, shape (frame_batchsize, height, width), dtype=np.float32
        """
        md = self.metadata

        h = md["biHeight"]
        w = md["biWidth"]
        compression = md["biCompression"]
        frame_image_size = md["biSizeImage"]
        num_frames = md["TotalImageCount"]

        offset_table_pos = md["OffImageOffsets"]
        first_frame_corrected = first_frame - num_frames + 1 - md["FirstImageNo"]

        self.fid.seek(offset_table_pos + first_frame_corrected * 8)
        offsets_bytes = self.fid.read(frame_batchsize * 8)

        if len(offsets_bytes) != frame_batchsize * 8:
            raise EOFError("Could not read enough frame offsets")

        offsets = np.frombuffer(offsets_bytes, dtype=np.int64)

        if compression != 1024:
            raise NotImplementedError(
                f"Only Phantom P12L 12-bit packed compression=1024 is implemented, "
                f"got {compression}"
            )

        packed = np.empty((frame_batchsize, frame_image_size), dtype=np.uint8)

        with mmap.mmap(self.fid.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for i, img_start in enumerate(offsets):
                if img_start == 0:
                    raise ValueError(f"Invalid offset for frame {first_frame + i}")

                ann_size = struct.unpack_from("I", mm, img_start)[0]
                data_start = img_start + ann_size

                packed[i] = np.frombuffer(
                    mm,
                    dtype=np.uint8,
                    count=frame_image_size,
                    offset=data_start,
                )

        frames = unpack_12bitL_batch_to_uint16(packed, w, h)

        return frames
            
    

    def read_frames_fast(self, first_frame, frame_batchsize):
        """
        Read a batch of consecutive uncompressed frames as fast as possible.
        
        Parameters
        ----------
        first_frame : int
            Zero-based index of the first frame to read.
        frame_batchsize : int
            Number of frames to read.
        
        Returns
        -------
        np.ndarray, shape (frame_batchsize, height, width), dtype=np.float32
            Batch of frames, scaled to float32 (0..max_value).
        """
        md = self.metadata
        h, w = md['biHeight'], md['biWidth']
        # bpp = md['RealBPP']          # 12 for this file
        compression = md['biCompression']  # 1024 for 12-bit packed
        frame_image_size = md['biSizeImage']  
        
        num_frames = md['TotalImageCount']
        
        offset_table_pos = md['OffImageOffsets']
        first_frame_corrected = first_frame - num_frames + 1 - md['FirstImageNo']
        
        self.fid.seek(offset_table_pos + first_frame_corrected * 8)
        offsets_bytes = self.fid.read(frame_batchsize * 8)
        
        if len(offsets_bytes) != frame_batchsize * 8:
            raise EOFError("Could not read enough frame offsets")
        offsets = struct.unpack(f'{frame_batchsize}q', offsets_bytes)
        frames = np.empty((frame_batchsize, h, w), dtype=np.float32)
        
        with mmap.mmap(self.fid.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for i, img_start in enumerate(offsets):
                if img_start == 0:
                    raise ValueError(f"Invalid offset for frame {first_frame + i}")
                ann_size = struct.unpack('I', mm[img_start:img_start+4])[0]
                data_start = img_start + ann_size
                data_end = data_start + frame_image_size 

                # raw = np.frombuffer(mm[data_start:data_end], dtype=np.uint16)

                if compression == 256:          # 10-bit packed
                    pass
                    # img = _unpack_10bit(raw, w, h)
                elif compression == 1024:       # 12-bit packed (Phantom P12L)
                    img = unpack_12bitL_vectorized(mm[data_start:data_end], w, h)
                else:
                    pass

                frames[i] = img.astype(np.float32)

        return frames
    
    def read_frames_cinereader(self, first_frame, frame_size):
        _, images, _ = cinereader.read(
            self.file_path, self.metadata['FirstImageNo'] + first_frame, frame_size
        )
        return np.stack(images, axis=0).astype(np.float32)
    
    read_frames = read_frames_fastest
    
    
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
