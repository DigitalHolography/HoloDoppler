"""Flow indices with bounded, disk-backed temporal history and common saving."""
import tempfile
from pathlib import Path
import numpy as np
from holodoppler import backend
from holodoppler.core.pipeline import prepare_input, batch_indices, run_pipeline

class LowMemoryFlow:
    def __init__(self, parameters, directory):
        p = parameters

        self.xp = backend.xp
        self.directory = Path(directory)

        self.ns = int(p.get("lsci_nbh_s", 5))
        self.nt = int(p["batch_size"])

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


def _small_frame(frame, factor):
    frame = np.asarray(backend.to_numpy(frame))
    if frame.ndim != 2:
        raise ValueError("Expected a 2D intensity frame")
    step = max(1, round(1.0 / factor))
    return np.asarray(frame[::step, ::step], dtype=np.float32)


def _run(file_path, parameters, preview_mode=False, progress_callback=None):
    parameters = dict(parameters)
    size = parameters.get("batch_size", parameters.get("lsci_nbh_t", 40))
    parameters.update(batch_size=size, batch_stride=size, lsci_nbh_t=size)
    reader, p = prepare_input(file_path, parameters)
    _keys(p)
    indices = batch_indices(reader, p)
    if not indices:
        return None
    factor = p.get("lsci_resize_factor", .25)
    with tempfile.TemporaryDirectory(prefix="lsci_history_") as directory:
        calculator = LowMemoryFlow(p, directory)
        try:
            def process_batch(frames, reference):
                result = None
                for index, frame in enumerate(frames):
                    result = calculator.add(_small_frame(frame, factor), emit=index == len(frames) - 1)
                return result, reference
            return run_pipeline(reader, p, process_batch, preview=preview_mode,
                preview_key=_keys(p)[0], stateful=True, progress_callback=progress_callback)
        finally:
            calculator.history = None


def preview(file_path, parameters):
    return _run(file_path, parameters, preview_mode=True)


def process(file_path, parameters, progress_callback=None):
    return _run(file_path, parameters, progress_callback=progress_callback)
