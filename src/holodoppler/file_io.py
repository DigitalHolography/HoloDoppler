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

class HoloFileReader:
    """Reader for .holo files"""

    HEADER_SIZE = 64

    def __init__(self, file_path):
        self.file_path = file_path
        self.fid = None
        self.file_header = None
        self.file_footer = None

    def open(self):
        if self.fid is not None:
            self.close()
        self.fid = open(self.file_path, "rb")
        self._read_header()
        self._read_footer()

    def close(self):
        if self.fid is not None:
            self.fid.close()
            self.fid = None

    def _read_header(self):
        header = self.fid.read(self.HEADER_SIZE)
        self.file_header = {
            "magic_number": "".join(list(map(chr, header[0:4]))),
            "version": int.from_bytes(header[4:6], "little"),
            "bit_depth": int.from_bytes(header[6:8], "little"),
            "width": int.from_bytes(header[8:12], "little"),
            "height": int.from_bytes(header[12:16], "little"),
            "num_frames": int.from_bytes(header[16:20], "little"),
            "total_size": int.from_bytes(header[20:28], "little"),
            "endianness": header[28],
        }

    def _read_footer(self):
        w, h = self.file_header["width"], self.file_header["height"]
        num_frames = self.file_header["num_frames"]
        offset = w * h * num_frames + self.HEADER_SIZE
        self.fid.seek(offset)
        footer_bytes = self.fid.read()
        if footer_bytes:
            try:
                self.file_footer = json.loads(footer_bytes.decode("utf-8"))
            except Exception:
                self.file_footer = {}
        else:
            self.file_footer = {}

    def read_frames(self, first_frame, frame_size):
        """Read frames from .holo file (returns numpy array)"""
        try:
            byte_begin = (
                self.HEADER_SIZE
                + self.file_header["width"]
                * self.file_header["height"]
                * first_frame
                * self.file_header["bit_depth"]
                // 8
            )
            byte_size = (
                self.file_header["width"]
                * self.file_header["height"]
                * frame_size
                * self.file_header["bit_depth"]
                // 8
            )

            self.fid.seek(byte_begin)
            raw_bytes = self.fid.read(byte_size)

            if self.file_header["bit_depth"] == 8:
                utyp = np.uint8
            elif self.file_header["bit_depth"] == 16:
                utyp = np.uint16
            else:
                raise RuntimeError("Unsupported bit depth")

            if self.file_header["endianness"] == 1:
                utyp = utyp.newbyteorder("<")

            out = np.frombuffer(raw_bytes, dtype=utyp)
            out = out.reshape(
                (frame_size, self.file_header["height"], self.file_header["width"]),
                order="C",
            )
            return out
        except Exception:
            traceback.print_exc()
            return None

    def get_np_memmap(self):
        return np.memmap(self.file_path, offset=64, order="C", shape= (self.file_header["num_frames"],self.file_header["height"],self.file_header["width"]))
    

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
        print(self.metadata)

    def close(self):
        if self.fid is not None:
            self.fid.close()
            self.file_path = None
            self.metadata = None
            self.fid = None
            
    

    def read_frames(self, first_frame, frame_batchsize):
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
        frame_image_size = md['biSizeImage']  # bytes of raw pixel data per frame

        
        print(first_frame)
        
        offset_table_pos = md['OffImageOffsets']
        first_frame_corrected = first_frame - md['FirstImageNo']
        
        print(first_frame_corrected)
        
        self.fid.seek(offset_table_pos + first_frame_corrected * 8)
        image_start = struct.unpack("q", self.fid.read(8))[0]
        if image_start == 0:
            raise ValueError("image_start is null")
        
        print(image_start)

        self.fid.seek(image_start)
        annotationSize = struct.unpack("I", self.fid.read(4))[0]  # unit32, 4bytes
        if annotationSize == 0:
            raise ValueError("annotationSize is null")
        
        print(annotationSize)

        self.fid.seek(image_start + annotationSize)

        img = np.frombuffer(
            self.fid.read(md['biSizeImage']),
                dtype={8: np.uint8, 10: "u2", 12: np.uint16, 0: np.uint16}[
                md['RealBPP']
            ],
        )

        img = unpack_12bitL_vectorized(img, w, h)

        plt.imshow(img)
        plt.show()
        
        self.fid.seek(offset_table_pos + first_frame_corrected * 8)
        offsets_bytes = self.fid.read(frame_batchsize * 8)
        
        if len(offsets_bytes) != frame_batchsize * 8:
            raise EOFError("Could not read enough frame offsets")
        offsets = struct.unpack(f'{frame_batchsize}q', offsets_bytes)
        
        print(offsets[0])

        frames = np.empty((frame_batchsize, h, w), dtype=np.float32)

        with mmap.mmap(self.fid.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for i, img_start in enumerate(offsets):
                if img_start == 0:
                    raise ValueError(f"Invalid offset for frame {first_frame + i}")

                # Read annotation size (4 bytes) at img_start
                ann_size = struct.unpack('I', mm[img_start:img_start+4])[0]
                print(ann_size)
                
                
                
                # Image data starts after the annotation
                data_start = img_start + 4 + ann_size
                data_end = data_start + frame_image_size

                raw = np.frombuffer(mm[data_start:data_end], dtype=np.uint8)

                if compression == 256:          # 10-bit packed
                    img = _unpack_10bit(raw, w, h)
                    img = md['LUT_P10'][img].astype(np.uint16)
                elif compression == 1024:       # 12-bit packed (Phantom P12L)
                    img = _unpack_12bitL(raw, w, h)
                else:
                    dtype = np.uint8 if md['biBitCount'] == 8 else np.uint16
                    img = np.frombuffer(raw, dtype=dtype).reshape(h, w)[::-1]
                    
                plt.imshow(img)
                plt.show()

                frames[i] = img.astype(np.float32)  # optionally / max_val if needed

        return frames
            
    # def read_frames(self, first_frame, frame_size):
    #     """Custom version of frame reading implemented home for not compressed cine frames"""
    #     fId = self.fid
    #     fId.seek(self.metadata["OffImageOffsets"] + 0 * 8)
    #     print(fId.read(8))

    #     image_start = s.unpack("q", fId.read(8))[0]
    #     if image_start == 0:
    #         raise ValueError("image_start is null")

    #     fId.seek(image_start)
    #     annotationSize = s.unpack("I", fId.read(4))[0]  # unit32, 4bytes
    #     if annotationSize == 0:
    #         raise ValueError("annotationSize is null")

    #     fId.seek(image_start + annotationSize)

    #     img = np.frombuffer(
    #         fId.read(metadata.biSizeImage),
    #         dtype={8: np.uint8, 10: "u2", 12: np.uint16, 0: np.uint16}[
    #             metadata.RealBPP
    #         ],
    #     )

    #     if metadata.biCompression == 256:  # 10bit / P10 compressed
    #         img = _unpack_10bit(img, metadata.biWidth, metadata.biHeight)
    #         img = metadata.LUT_P10[img].astype(np.uint16)
    #     elif metadata.biCompression == 1024:  # P12L compressed
    #         img = _unpack_12bitL(img, metadata.biWidth, metadata.biHeight)
    #     else:
    #         img = img.reshape(metadata.biHeight, metadata.biWidth)[::-1]

    #     return img.astype(np.float32)
        
    def read_frames_cinereader(self, first_frame, frame_size):
        _, images, _ = cinereader.read(
            self.file_path, self.metadata.FirstImageNo + first_frame, frame_size
        )
        return np.stack(images, axis=0).astype(np.float32)


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
