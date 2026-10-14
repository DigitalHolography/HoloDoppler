"""GPU-friendly speckle metrics for holodoppler .holo / .cine readers.

Each saved metric has shape (T, H, W), including preview (T=1).
The temporal window is causal, and uses available frames during warm-up.

Parameters (all optional):
    lsci_enable_spatial=True         Compute local spatial contrast.
    lsci_enable_temporal=True        Compute per-pixel temporal contrast.
    lsci_enable_spatiotemporal=True  Compute contrast over space AND time.
                                      Independent of the two switches above.
    lsci_nbh_s=5                     Odd spatial window side length.
    lsci_nbh_t=40                    Temporal window length in frames.
    lsci_boundary_mode='reflect'    scipy.ndimage boundary handling.
    lsci_boundary_cval=0.0          Value outside image when mode='constant'.
    lsci_eps=1e-6                   Prevent division by near-zero mean.
    lsci_flow_eps=1e-4              Floor on K^2 for inverse contrast.
    lsci_save_raw=True              Save raw input intensity frames.
    lsci_save_mean=True             Save neighborhood mean outputs.
    lsci_save_std=True              Save neighborhood std outputs.
    lsci_save_variance=True         Save neighborhood variance outputs.
    lsci_save_flow_index=True       Save inverse-squared-contrast proxies.
    lsci_save_cv_aliases=False      Save redundant *_coefficient_of_variation.
    lsci_output_dtype='float32'     Saved array dtype: float32 or float64.
    lsci_prime_temporal=True        In process(), read up to N-1 earlier
                                    frames to prime the temporal window.
    force_numpy=False               Select CPU backend instead of CuPy.
    first_frame=0                   Inclusive frame index.
    end_frame=0                     Exclusive frame index, 0 means EOF.

Output keys (only enabled groups and requested auxiliary metrics are emitted):
    raw_frame                       Raw input intensity.
    spatial_lsci                    2D local K = std(I) / abs(mean(I)).
    spatial_mean                    Mean intensity in the spatial window.
    spatial_std                     Population std in the spatial window.
    spatial_variance                Population variance in spatial window.
    spatial_flow_index              1/max(spatial_lsci**2, flow_eps).
    temporal_lsci                   Causal per-pixel K over recent frames.
    temporal_mean                   Per-pixel temporal average intensity.
    temporal_std                    Per-pixel temporal population std.
    temporal_variance               Per-pixel temporal population variance.
    temporal_flow_index             1/max(temporal_lsci**2, flow_eps).
    spatiotemporal_lsci             K across spatial pixels AND time frames.
    spatiotemporal_mean             Joint spatial + temporal mean intensity.
    spatiotemporal_std              Joint spatial + temporal population std.
    spatiotemporal_variance         Joint spatial + temporal variance.
    spatiotemporal_flow_index       1/max(spatiotemporal_lsci**2, flow_eps).
    *_coefficient_of_variation      Optional duplicates of spatial/temporal K.

Contrast-based flow indices are qualitative proxies, not calibrated flow.
"""

from collections import defaultdict, deque

import numpy as np
from tqdm import tqdm

from holodoppler import backend
from holodoppler.config import update_from_cine_metadata, update_from_holo_footer
from holodoppler.file_reader import get_reader
from holodoppler.saving import save_outputs


def _uniform_filter():
    if backend.xp.__name__.startswith("cupy"):
        from cupyx.scipy.ndimage import uniform_filter
    else:
        from scipy.ndimage import uniform_filter
    return uniform_filter


def _read_frame(reader, index):
    """Accept either (H,W) or (1,H,W) returned by reader.read_frames."""
    frame = reader.read_frames(first_frame=index, batch_size=1)
    if frame.ndim == 3 and frame.shape[0] == 1:
        frame = frame[0]
    if frame.ndim != 2:
        raise ValueError(f"Expected (H,W) or (1,H,W), got {frame.shape}")
    return backend.to_backend(frame).astype(backend.xp.float32, copy=False)


def _check_settings(p):
    ns = int(p.get("lsci_nbh_s", 5))
    nt = int(p.get("lsci_nbh_t", 40))
    if ns < 1 or ns % 2 != 1:
        raise ValueError("lsci_nbh_s must be a positive odd integer")
    if nt < 1:
        raise ValueError("lsci_nbh_t must be a positive integer")
    if float(p.get("lsci_eps", 1e-6)) <= 0:
        raise ValueError("lsci_eps must be positive")
    if float(p.get("lsci_flow_eps", 1e-4)) <= 0:
        raise ValueError("lsci_flow_eps must be positive")
    if p.get("lsci_output_dtype", "float32") not in ("float32", "float64"):
        raise ValueError("lsci_output_dtype must be 'float32' or 'float64'")
    return ns, nt


class SpeckleAccumulator:
    """Streaming array-backend LSCI; no per-pixel Python loops.

    Disabled contrast families incur no filtering/rolling-state work unless
    needed by the independent spatiotemporal calculation.
    Uses population variance (ddof=0) and a causal temporal window.
    """

    def __init__(self, parameters):
        p = parameters
        self.xp = backend.xp
        self.ns, self.nt = _check_settings(p)
        self.spatial = bool(p.get("lsci_enable_spatial", True))
        self.temporal = bool(p.get("lsci_enable_temporal", True))
        self.joint = bool(p.get("lsci_enable_spatiotemporal", True))
        self.keep_raw = bool(p.get("lsci_save_raw", True))
        self.save_mean = bool(p.get("lsci_save_mean", True))
        self.save_std = bool(p.get("lsci_save_std", True))
        self.save_var = bool(p.get("lsci_save_variance", True))
        self.save_flow = bool(p.get("lsci_save_flow_index", True))
        self.save_aliases = bool(p.get("lsci_save_cv_aliases", False))
        self.eps = float(p.get("lsci_eps", 1e-6))
        self.flow_eps = float(p.get("lsci_flow_eps", 1e-4))
        self.mode = p.get("lsci_boundary_mode", "reflect")
        self.cval = float(p.get("lsci_boundary_cval", 0.0))
        self.use_time = self.temporal or self.joint
        self.filter2d = _uniform_filter() if self.spatial or self.joint else None
        self.window = deque()
        self.sum_t = None
        self.sum2_t = None
        self.image_shape = None

    def _spatial_mean(self, x):
        if self.ns == 1:
            return x
        return self.filter2d(x, size=(self.ns, self.ns),
                             mode=self.mode, cval=self.cval)

    def _calculate(self, mean, second_moment):
        xp = self.xp
        variance = xp.maximum(second_moment - mean * mean, 0)
        std = xp.sqrt(variance)
        # xp.where still evaluates both branches; safe denominator avoids NaNs.
        safe_mean = xp.maximum(xp.abs(mean), self.eps)
        contrast = xp.where(xp.abs(mean) > self.eps, std / safe_mean, 0)
        return contrast, mean, std, variance

    def _emit(self, out, prefix, stats):
        k, mean, std, var = stats
        out[prefix + "_lsci"] = k  # Speckle contrast K = std / |mean|.
        if self.save_mean:
            out[prefix + "_mean"] = mean  # Window-averaged intensity.
        if self.save_std:
            out[prefix + "_std"] = std  # Population standard deviation.
        if self.save_var:
            out[prefix + "_variance"] = var  # Population intensity variance.
        if self.save_flow:
            # Relative inverse squared contrast; not calibrated perfusion.
            out[prefix + "_flow_index"] = 1.0 / self.xp.maximum(k * k, self.flow_eps)
        if self.save_aliases and prefix in ("spatial", "temporal"):
            # Coefficient of variation is identically the reported LSCI K.
            out[prefix + "_coefficient_of_variation"] = k

    def add(self, frame):
        xp = self.xp
        x = backend.to_backend(frame).astype(xp.float32, copy=False)
        if x.ndim != 2:
            raise ValueError(f"Expected 2D raw frame, received shape {x.shape}")
        if self.image_shape is None:
            self.image_shape = x.shape
        elif x.shape != self.image_shape:
            raise ValueError(f"Image dimensions changed: {self.image_shape} -> {x.shape}")

        out = {}
        if self.keep_raw:
            out["raw_frame"] = x  # Sensor intensity of the current frame.

        if self.spatial:
            # Moments within the (ns x ns) neighborhood of this frame.
            s_mean = self._spatial_mean(x)
            s_mean2 = self._spatial_mean(x * x)
            self._emit(out, "spatial", self._calculate(s_mean, s_mean2))

        if self.use_time:
            # O(H*W) rolling sums, independent of temporal window length.
            if self.sum_t is None:
                self.sum_t = xp.zeros_like(x)
                self.sum2_t = xp.zeros_like(x)
            if len(self.window) >= self.nt:
                old = self.window.popleft()
                self.sum_t -= old
                self.sum2_t -= old * old
            self.window.append(x.copy())
            self.sum_t += x
            self.sum2_t += x * x
            n = len(self.window)
            t_mean = self.sum_t / n
            t_mean2 = self.sum2_t / n

            if self.temporal:
                # Per-pixel contrast using the last <= nt frames.
                self._emit(out, "temporal", self._calculate(t_mean, t_mean2))

            if self.joint:
                # Joint moments over all pixels in local space-time window.
                st_mean = self._spatial_mean(t_mean)
                st_mean2 = self._spatial_mean(t_mean2)
                self._emit(out, "spatiotemporal",
                           self._calculate(st_mean, st_mean2))
        return out


def _prepare_reader(file_path, parameters):
    p = dict(parameters)
    if p.get("force_numpy", False):
        backend.set_backend("numpy")
    reader = get_reader(file_path)
    if reader.extension == ".holo":
        p = update_from_holo_footer(p, reader.footer)
    elif reader.extension == ".cine":
        p = update_from_cine_metadata(p, reader.header)
    _check_settings(p)
    return reader, p


def _append_results(output, result, dtype):
    # Move each frame's outputs to host; GPU history stays bounded by nt frames.
    for key, value in result.items():
        output[key].append(np.asarray(backend.to_numpy(value), dtype=dtype))


def _stack_results(output):
    return {key: np.stack(values, axis=0) for key, values in output.items()}


def _prime(calculator, reader, start, first):
    """Include preceding frames when temporal contrast is enabled."""
    if not calculator.use_time:
        return
    for idx in range(max(0, first - calculator.nt + 1), first):
        calculator.add(_read_frame(reader, idx))


def preview(file_path, parameters):
    reader, p = _prepare_reader(file_path, parameters)
    first = int(p.get("first_frame", 0))
    if not 0 <= first < reader.total_frames:
        raise ValueError("first_frame outside the file")
    calc = SpeckleAccumulator(p)
    if p.get("lsci_prime_temporal", True):
        _prime(calc, reader, 0, first)
    result = calc.add(_read_frame(reader, first))
    dtype = np.dtype(p.get("lsci_output_dtype", "float32"))
    output = {k: np.asarray(backend.to_numpy(v), dtype=dtype)[None, ...]
              for k, v in result.items()}
    if not output:
        raise ValueError("No outputs enabled; enable a metric or lsci_save_raw")
    save_outputs(file_reader=reader, output=output, parameters=p,
                 custom_relative_path="preview")
    # Preserve the original API (array rather than dict).
    return output.get("raw_frame", next(iter(output.values())))


def process(file_path, parameters, progress_callback=None):
    reader, p = _prepare_reader(file_path, parameters)
    first = int(p.get("first_frame", 0))
    end = int(p.get("end_frame", 0))
    if end <= 0:
        end = reader.total_frames
    if not 0 <= first <= end <= reader.total_frames:
        raise ValueError("Expected 0 <= first_frame <= end_frame <= total_frames")
    if first == end:
        return {}

    calc = SpeckleAccumulator(p)
    if p.get("lsci_prime_temporal", True):
        _prime(calc, reader, 0, first)

    output = defaultdict(list)
    dtype = np.dtype(p.get("lsci_output_dtype", "float32"))
    total = end - first
    for index in tqdm(range(total), desc="LSCI processing"):
        # Use the current frame index, not the undefined `i`.
        frame = _read_frame(reader, first + index)
        _append_results(output, calc.add(frame), dtype)
        if progress_callback is not None:
            progress_callback((index + 1) / total)

    if not output:
        raise ValueError("No outputs enabled; enable a metric or lsci_save_raw")
    stacked = _stack_results(output)
    save_outputs(file_reader=reader, output=stacked, parameters=p)
    return stacked
