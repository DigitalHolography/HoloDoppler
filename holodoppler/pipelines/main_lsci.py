
"""Ultra-low-memory LSCI: flow indices only.

- Never stores raw video or full-resolution frame history.
- Resizes each frame immediately (default: 4x smaller per dimension).
- Temporal history stored as uint8 on disk, not RAM.
- Processes one frame at a time.
- Writes only requested flow indices directly to disk.
- Uses float32 working arrays.
- Supports CPU and CuPy GPU processing.

Output:
    spatial_flow_index.npy
    temporal_flow_index.npy
    spatiotemporal_flow_index.npy

Set lsci_resize_factor=0.25 for 16x fewer pixels.
Set lsci_history_dtype="float16" for better temporal precision.
"""

import tempfile
from pathlib import Path

import numpy as np
from numpy.lib.format import open_memmap
from scipy.ndimage import zoom
from tqdm import tqdm

from holodoppler import backend
from holodoppler.config import (
    update_from_cine_metadata,
    update_from_holo_footer,
)
from holodoppler.file_reader import get_reader


def _prepare(file_path, parameters):
    p = dict(parameters)

    if p.get("force_numpy", True):
        backend.set_backend("numpy")

    reader = get_reader(file_path)

    if reader.extension == ".holo":
        p = update_from_holo_footer(p, reader.footer)
    elif reader.extension == ".cine":
        p = update_from_cine_metadata(p, reader.header)

    return reader, p


def _read_small(reader, index, factor):
    frame = reader.read_frames(
        first_frame=index,
        batch_size=1,
    )

    if frame.ndim == 3:
        frame = frame[0]

    if frame.ndim != 2:
        raise ValueError("Expected a 2D intensity frame")

    # Transfer only one frame, then downsample immediately.
    frame = np.asarray(backend.to_numpy(frame))

    if factor < 1:
        if factor <= 0:
            raise ValueError("Resize factor must be positive")

        # Strided downsampling avoids a full-resolution float copy.
        step = max(1, round(1.0 / factor))
        frame = frame[::step, ::step]

    return np.asarray(frame, dtype=np.float32)


class LowMemoryFlow:
    def __init__(self, parameters, directory):
        p = parameters

        self.xp = backend.xp
        self.directory = Path(directory)

        self.ns = int(p.get("lsci_nbh_s", 5))
        self.nt = int(p.get("lsci_nbh_t", 40))

        self.spatial = bool(p.get("lsci_enable_spatial", True))
        self.temporal = bool(p.get("lsci_enable_temporal", True))
        self.joint = bool(
            p.get("lsci_enable_spatiotemporal", True)
        )

        self.use_time = self.temporal or self.joint

        self.eps = float(p.get("lsci_eps", 1e-6))
        self.flow_eps = float(p.get("lsci_flow_eps", 1e-4))

        self.mode = p.get("lsci_boundary_mode", "reflect")
        self.cval = float(p.get("lsci_boundary_cval", 0.0))

        if self.ns < 1 or self.ns % 2 != 1:
            raise ValueError("Spatial window must be positive and odd")
        if self.nt < 1:
            raise ValueError("Temporal window must be positive")

        if self.spatial or self.joint:
            if self.xp.__name__.startswith("cupy"):
                from cupyx.scipy.ndimage import uniform_filter
            else:
                from scipy.ndimage import uniform_filter

            self.filter = uniform_filter

        self.history_dtype = np.dtype(
            p.get("lsci_history_dtype", "uint8")
        )

        if self.history_dtype not in (
            np.dtype("uint8"),
            np.dtype("float16"),
        ):
            raise ValueError("History must be uint8 or float16")

        self.shape = None
        self.history = None
        self.sum_t = None
        self.sum2_t = None

        self.count = 0
        self.pos = 0

        # Fixed quantization scale for uint8 history.
        # 255 maps to the intensity maximum.
        self.max_intensity = float(
            p.get("lsci_max_intensity", 65535.0)
        )

        if self.max_intensity <= 0:
            raise ValueError("lsci_max_intensity must be positive")

        self.scale = self.max_intensity / 255.0

    def _initialize(self, shape):
        xp = self.xp
        self.shape = shape

        if not self.use_time:
            return

        self.sum_t = xp.zeros(shape, dtype=xp.float32)
        self.sum2_t = xp.zeros(shape, dtype=xp.float32)

        # Disk-backed ring buffer; does not scale RAM with nt.
        self.history = np.memmap(
            self.directory / "history.dat",
            mode="w+",
            dtype=self.history_dtype,
            shape=(self.nt, *shape),
        )

    def _spatial(self, x):
        if self.ns == 1:
            return x

        return self.filter(
            x,
            size=self.ns,
            mode=self.mode,
            cval=self.cval,
        )

    def _flow(self, mean, mean2):
        xp = self.xp

        # Direct inverse contrast: mean² / variance.
        variance = xp.maximum(
            mean2 - mean * mean, 0.0
        )

        mean_abs = xp.abs(mean)
        mean_sq = mean * mean

        k2 = variance / xp.maximum(
            mean_sq, self.eps * self.eps
        )

        k2 = xp.where(mean_abs > self.eps, k2, 0.0)

        return 1.0 / xp.maximum(k2, self.flow_eps)

    def _encode(self, frame):
        if self.history_dtype == np.uint8:
            return np.clip(
                np.rint(frame / self.scale), 0, 255
            ).astype(np.uint8)

        return frame.astype(np.float16)

    def _decode(self, frame):
        x = self.xp.asarray(frame, dtype=self.xp.float32)

        if self.history_dtype == np.uint8:
            x *= self.scale

        return x

    def add(self, frame, emit=True):
        xp = self.xp

        if self.shape is None:
            self._initialize(frame.shape)

        if frame.shape != self.shape:
            raise ValueError("Frame shape changed")

        output = {}

        x = xp.asarray(frame, dtype=xp.float32)

        if self.spatial and emit:
            mean = self._spatial(x)
            mean2 = self._spatial(x * x)

            output["spatial_flow_index"] = self._flow(
                mean, mean2
            )

            del mean, mean2

        if not self.use_time:
            return output

        # Quantize new frame before updating temporal statistics.
        # This keeps subtraction consistent with stored history.
        encoded = self._encode(frame)
        xq = self._decode(encoded)

        if self.count == self.nt:
            old = self._decode(self.history[self.pos])

            self.sum_t -= old
            self.sum2_t -= old * old

            del old
        else:
            self.count += 1

        self.sum_t += xq
        self.sum2_t += xq * xq

        self.history[self.pos] = encoded
        self.pos = (self.pos + 1) % self.nt

        del encoded, xq

        if not emit:
            return output

        inv_n = np.float32(1.0 / self.count)

        mean_t = self.sum_t * inv_n
        mean2_t = self.sum2_t * inv_n

        if self.temporal:
            output["temporal_flow_index"] = self._flow(
                mean_t, mean2_t
            )

        if self.joint:
            mean_st = self._spatial(mean_t)
            mean2_st = self._spatial(mean2_t)

            output["spatiotemporal_flow_index"] = self._flow(
                mean_st, mean2_st
            )

        return output


def _keys(p):
    keys = []

    if p.get("lsci_enable_spatial", True):
        keys.append("spatial_flow_index")

    if p.get("lsci_enable_temporal", True):
        keys.append("temporal_flow_index")

    if p.get("lsci_enable_spatiotemporal", True):
        keys.append("spatiotemporal_flow_index")

    if not keys:
        raise ValueError("No flow index enabled")

    return keys

import cv2
from PIL import Image
from pathlib import Path
import numpy as np
from tqdm import tqdm
import tempfile

from holodoppler import backend



class FlowWriter:
    """Low-memory PNG/MJPEG writer with adaptive CLAHE contrast."""

    def __init__(self, file_path, parameters, fps=30.0):
        p = parameters

        self.save_png = bool(p.get("lsci_save_png", True))
        self.save_avi = bool(p.get("lsci_save_avi", True))

        self.fps = float(p.get("lsci_output_fps", fps))
        if not np.isfinite(self.fps) or self.fps <= 0:
            self.fps = 30.0

        self.jpeg_quality = int(p.get("lsci_mjpeg_quality", 90))

        # Adaptive contrast settings.
        self.use_clahe = bool(p.get("lsci_adaptive_contrast", True))
        self.clip_limit = float(p.get("lsci_clahe_clip", 2.0))
        self.tile_size = max(1, int(p.get("lsci_clahe_tile", 8)))

        self.clahe = (
            cv2.createCLAHE(
                clipLimit=self.clip_limit,
                tileGridSize=(self.tile_size, self.tile_size),
            )
            if self.use_clahe
            else None
        )

        # Robust per-frame percentile normalization.
        self.low_percentile = float(
            p.get("lsci_contrast_low_percentile", 1.0)
        )
        self.high_percentile = float(
            p.get("lsci_contrast_high_percentile", 99.0)
        )

        if not (
            0 <= self.low_percentile
            < self.high_percentile <= 100
        ):
            raise ValueError("Invalid contrast percentiles")

        source = Path(file_path)
        self.root = source.parent / source.stem
        self.png_dir = self.root / "png"
        self.avi_dir = self.root / "avi"

        if self.save_png:
            self.png_dir.mkdir(parents=True, exist_ok=True)

        if self.save_avi:
            self.avi_dir.mkdir(parents=True, exist_ok=True)

        self.writers = {}

    def _normalize(self, array):
        """Adaptive contrast using percentiles followed by CLAHE."""

        x = np.asarray(
            backend.to_numpy(array),
            dtype=np.float32,
        )

        if x.ndim != 2:
            raise ValueError("Expected 2D flow-index frame")

        # Handle NaN/Inf without changing the input.
        x = np.nan_to_num(
            x,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
            copy=True,
        )

        # Robust scaling reduces the impact of outliers.
        lo, hi = np.percentile(
            x,
            [
                self.low_percentile,
                self.high_percentile,
            ],
        )

        if hi <= lo + 1e-8:
            image = np.zeros(x.shape, dtype=np.uint8)
        else:
            x -= np.float32(lo)
            x *= np.float32(255.0 / (hi - lo))
            np.clip(x, 0, 255, out=x)
            image = x.astype(np.uint8)

        del x

        # Local adaptive histogram equalization.
        if self.clahe is not None:
            image = self.clahe.apply(image)

        return image

    def _get_writer(self, key, width, height):
        if key in self.writers:
            return self.writers[key]

        path = self.avi_dir / f"{key}.avi"

        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*"MJPG"),
            self.fps,
            (width, height),
            isColor=False,
        )

        if not writer.isOpened():
            raise RuntimeError(f"Cannot create AVI: {path}")

        writer.set(
            cv2.VIDEOWRITER_PROP_QUALITY,
            self.jpeg_quality,
        )

        self.writers[key] = writer
        return writer

    def write(self, result, frame_index):
        for key, value in result.items():
            if not key.endswith("_flow_index"):
                continue

            image = self._normalize(value)
            height, width = image.shape

            if self.save_png:
                path = (
                    self.png_dir
                    / f"{key}_{frame_index:06d}.png"
                )

                Image.fromarray(image).save(
                    str(path),
                    format="PNG",
                    compress_level=1,
                )

            if self.save_avi:
                writer = self._get_writer(
                    key, width, height
                )
                writer.write(np.ascontiguousarray(image))

            del image

    def close(self):
        for writer in self.writers.values():
            writer.release()

        self.writers.clear()



def _run(
    file_path,
    parameters,
    preview_mode=False,
    progress_callback=None,
):
    reader, p = _prepare(file_path, parameters)

    factor = float(p.get("lsci_resize_factor", 0.25))

    if not 0 < factor <= 1:
        raise ValueError(
            "lsci_resize_factor must be in (0, 1]"
        )

    first = int(p.get("first_frame", 0))
    end = int(p.get("end_frame", 0))

    if end <= 0:
        end = reader.total_frames

    if not 0 <= first < end <= reader.total_frames:
        raise ValueError("Invalid frame range")

    if preview_mode:
        end = first + 1

    keys = _keys(p)
    total = end - first

    # Use original acquisition FPS when available.
    fps = p.get("fps", p.get("frame_rate", 30.0))

    with tempfile.TemporaryDirectory(
        prefix="lsci_history_"
    ) as tempdir:

        calculator = LowMemoryFlow(p, tempdir)

        writer = FlowWriter(
            file_path=file_path,
            parameters={
                **p,
                "lsci_save_avi": (
                    p.get("lsci_save_avi", True)
                    and not preview_mode
                ),
            },
            fps=fps,
        )

        try:
            # Prime rolling statistics without writing frames.
            if (
                p.get("lsci_prime_temporal", True)
                and calculator.use_time
            ):
                start = max(
                    0,
                    first - calculator.nt + 1,
                )

                for idx in range(start, first):
                    frame = _read_small(
                        reader, idx, factor
                    )
                    calculator.add(frame, emit=False)
                    del frame

            # One-frame-at-a-time processing and saving.
            for i in tqdm(
                range(total),
                desc="Flow index",
            ):
                frame_index = first + i

                frame = _read_small(
                    reader,
                    frame_index,
                    factor,
                )

                result = calculator.add(frame)

                # Only flow indices are saved.
                writer.write(
                    result=result,
                    frame_index=frame_index,
                )

                del result, frame

                if progress_callback is not None:
                    progress_callback((i + 1) / total)

        finally:
            writer.close()
            calculator.history = None

    return str(writer.root)


def preview(file_path, parameters):
    return _run(
        file_path,
        parameters,
        preview_mode=True,
    )


def process(
    file_path,
    parameters,
    progress_callback=None,
):
    return _run(
        file_path,
        parameters,
        preview_mode=False,
        progress_callback=progress_callback,
    )


# Example low-memory settings:
#
# parameters = {
#     "force_numpy": True,
#     "lsci_resize_factor": 0.25,
#     "lsci_nbh_s": 5,
#     "lsci_nbh_t": 40,
#     "lsci_history_dtype": "uint8",
#     "lsci_max_intensity": 65535.0,
#
#     "lsci_enable_spatial": False,
#     "lsci_enable_temporal": False,
#     "lsci_enable_spatiotemporal": True,
#
#     "lsci_save_png": True,
#     "lsci_save_avi": True,
#     "lsci_mjpeg_quality": 90,
#     "lsci_output_fps": 30,
#
#     "lsci_display_min": 0.0,
#     "lsci_display_max": 1000.0,
# }



# Recommended low-RAM configuration:
#
# parameters = {
#     "force_numpy": True,
#     "lsci_resize_factor": 0.25,
#     "lsci_nbh_s": 5,
#     "lsci_nbh_t": 40,
#     "lsci_history_dtype": "uint8",
#     "lsci_max_intensity": 65535.0,
#     "lsci_output_dtype": "float32",
#     "lsci_enable_spatial": False,
#     "lsci_enable_temporal": False,
#     "lsci_enable_spatiotemporal": True,
#     "lsci_prime_temporal": True,
#     "lsci_output_dir": "lsci_flow_output",
# }
#
# Note: uint8 history approximates temporal statistics.
# Set lsci_history_dtype="float16" for better precision,
# or lsci_resize_factor=0.125 for even lower memory.
