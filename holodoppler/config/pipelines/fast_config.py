"""Resolved and validated configuration for the fast pipeline."""

from dataclasses import dataclass, fields
from math import isfinite
from numbers import Integral, Real
from pathlib import Path

from holodoppler.core.batching import calculate_batch_indices
from holodoppler.saving.default_output import validate_outputs
from holodoppler.saving.media import validate_video_temporal_sigma
from holodoppler.saving.scheduler import _saving_options

FFT_MAPS = ("moment0", "moment1", "moment2", "moment0ff")
PCA_MAPS = ("pca_sum", "pca_sum_ff")
PLACEHOLDERS = ("use_holovibes", "use_metadata")


def _integer(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def _number(value, name, *, signed=False):
    if (isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value)
            or (value == 0 if signed else value <= 0)):
        raise ValueError(f"Invalid or unresolved {name}: {value!r}")
    return float(value)


def _range(bounds, size, name):
    if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
        raise ValueError(f"{name} must contain [start, end]")
    start = _integer(bounds[0], name, 0)
    end = _integer(bounds[1], name, start + 1)
    if end > size:
        raise ValueError(f"{name} end must be <= time_window ({size})")
    return start, end


def _metadata_value(reader, name):
    try:
        if reader.extension == ".holo":
            footer = reader.footer
            if name in ("z", "wavelength"):
                return footer["compute_settings"]["image_rendering"][
                    "propagation_distance" if name == "z" else "lambda"]
            info = footer["info"]
            if name == "sampling_freq":
                return info["camera_fps"]
            if name == "pixel_pitch":
                pitch = info["pixel_pitch"]
                return (pitch["y"] * 1e-6, pitch["x"] * 1e-6)
        elif reader.extension == ".cine":
            extra = reader.header.extra
            if name == "sampling_freq":
                return extra["FrameRate"]
            if name == "pixel_pitch":
                return (1 / extra["biYPelsPerMeter"], 1 / extra["biXPelsPerMeter"])
    except (AttributeError, KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"Cannot resolve metadata placeholder for {name}") from exc
    raise ValueError(f"Cannot resolve metadata placeholder for {name}")


@dataclass(frozen=True, init=False)
class FastConfig:
    """A fixed, placeholder-free snapshot of settings for one recording."""

    pipeline_name: str
    backend: str
    first_frame: int
    end_frame: int
    z: float
    wavelength: float
    pixel_pitch: tuple[float, float]
    sampling_freq: float
    image_registration: bool
    shack_hartmann_autofocus: bool
    time_window: int
    accu: int
    mode: str
    frequency_ranges: tuple
    pca_index_range: tuple
    svd_filter: int
    outputs: tuple
    h5compression: int | None
    output_frame_stride: int
    output_fps: float
    custom_path: str | None
    custom_relative_path: str | None
    overwrite_option: str
    num_saving_workers: int
    saving_queue_depth: int | None
    video_temporal_sigma: float
    resize_averaged_images: bool
    h5_datasets: tuple

    def __init__(self):
        raise TypeError("Use FastConfig.from_parameters(parameters, reader)")

    @classmethod
    def from_parameters(cls, parameters, reader):
        p = dict(parameters)
        for name, value in p.items():
            if isinstance(value, str) and value in PLACEHOLDERS:
                p[name] = _metadata_value(reader, name)
        size = _integer(p.get("time_window", 64), "time_window", 1)
        accu = _integer(p.get("accu", 1), "accu", 1)
        mode = p.get("mode", "fft")
        if mode not in ("fft", "pca"):
            raise ValueError("mode must be fft or pca")
        for key in ("image_registration", "shack_hartmann_autofocus", "resize_averaged_images"):
            if not isinstance(p.get(key, False), bool):
                raise ValueError(f"{key} must be a boolean")
        svd = p.get("svd_filter", 0)
        if isinstance(svd, bool) or not isinstance(svd, Integral) or abs(svd) >= size:
            raise ValueError("svd_filter must be an integer with abs(svd_filter) < time_window")
        if mode == "pca" and svd:
            raise ValueError("svd_filter is only available in FFT mode")
        ranges = p.get("frequency_ranges", [[0, size]])
        if mode == "fft" and (not isinstance(ranges, (list, tuple)) or not ranges):
            raise ValueError("frequency_ranges must contain at least one [start, end] range")
        ranges = tuple(_range(pair, size, "frequency_ranges") for pair in ranges) if mode == "fft" else ()
        pca_range = _range(p.get("pca_index_range", [0, min(size, 16)]), size, "pca_index_range") if mode == "pca" else ()
        pitch = p.get("pixel_pitch")
        if isinstance(pitch, Real) and not isinstance(pitch, bool):
            pitch = (pitch, pitch)
        if not isinstance(pitch, (list, tuple)) or len(pitch) != 2:
            raise ValueError(f"Invalid or unresolved pixel_pitch: {pitch!r}")
        pitch = tuple(_number(v, "pixel_pitch") for v in pitch)
        sampling = _number(p.get("sampling_freq"), "sampling_freq")
        first = _integer(p.get("first_frame", 0), "first_frame", 0)
        end = p.get("end_frame", -1)
        calculate_batch_indices(first, end, size * accu, size * accu, reader.total_frames)
        outputs = p.get("outputs", {name: ["h5"] for name in (FFT_MAPS if mode == "fft" else PCA_MAPS)})
        validate_outputs({"outputs": outputs})
        compression = p.get("h5compression", 0)
        if compression is not None and (isinstance(compression, bool) or not isinstance(compression, Integral) or not 0 <= compression <= 9):
            raise ValueError("h5compression must be an integer from 0 to 9 or null")
        workers = p.get("num_saving_workers", 0)
        depth = p.get("saving_queue_depth")
        _saving_options(workers, depth)
        sigma = validate_video_temporal_sigma(p.get("video_temporal_sigma", 0))
        option = p.get("overwrite_option", "overwrite")
        if option not in ("overwrite", "erase", "archive_old"):
            raise ValueError(f"Unknown overwrite_option: {option}")
        custom = p.get("custom_path")
        relative = p.get("custom_relative_path")
        if custom is not None and not Path(custom).expanduser().is_absolute():
            raise ValueError("custom_path must be an absolute path")
        if relative is not None and (Path(relative).is_absolute() or ".." in Path(relative).parts):
            raise ValueError("custom_relative_path must stay within the output directory")
        datasets = p.get("h5_datasets") or ()
        if not isinstance(datasets, (tuple, list)) or any(not isinstance(x, str) for x in datasets):
            raise ValueError("h5_datasets must be a sequence of strings")
        if p.get("shack_hartmann_autofocus", False) and min(reader.frame_shape) < 5:
            raise ValueError("Fast autofocus requires both image dimensions to be at least 5")
        backend_name = p.get("backend", "auto")
        if not isinstance(backend_name, str) or backend_name.lower() not in ("auto", "numpy", "np", "cpu", "cupy", "cp", "gpu"):
            raise ValueError(f"Invalid backend: {backend_name!r}")
        values = ("fast", backend_name, first, int(end),
                   _number(p.get("z"), "z", signed=True), _number(p.get("wavelength", 852e-9), "wavelength"),
                   pitch, sampling, p.get("image_registration", False), p.get("shack_hartmann_autofocus", False),
                   size, accu, mode, ranges, pca_range, int(svd),
                   tuple((name, tuple(formats)) for name, formats in outputs.items()), compression,
                   size * accu, sampling / (size * accu), str(custom) if custom is not None else None,
                   str(relative) if relative is not None else None, option, workers, depth, sigma,
                   p.get("resize_averaged_images", False), tuple(datasets))
        config = object.__new__(cls)
        for field, value in zip(fields(cls), values):
            object.__setattr__(config, field.name, value)
        return config

    def as_dict(self):
        """Return a detached dictionary for existing shared saving utilities."""
        result = {field.name: getattr(self, field.name) for field in fields(self)}
        result["outputs"] = {name: list(formats) for name, formats in self.outputs}
        return result

    def get(self, name, default=None):
        return getattr(self, name, default)

    def __getitem__(self, name):
        return getattr(self, name)
