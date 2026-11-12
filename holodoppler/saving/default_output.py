"""Explicit output selection for the default pipeline; legacy writers stay unchanged."""
from fnmatch import fnmatchcase

import numpy as np

from holodoppler.logging import logger
from . import data, media
from .session import OutputClass

PROJECTION = "_time_projection"
FORMATS = {"h5", "avi", "mp4", "csv", "png"}


def validate_outputs(parameters):
    if "outputs" not in parameters:
        return
    rules = parameters["outputs"]
    if not isinstance(rules, dict):
        raise TypeError("outputs must map dataset names or glob patterns to format lists")
    for name, formats in rules.items():
        if (not isinstance(name, str) or not name or name in {".", ".."}
                or any(c in name for c in '/\\:')):
            raise ValueError(f"Invalid outputs dataset name: {name!r}")
        if not isinstance(formats, (list, tuple)):
            raise TypeError(f"outputs[{name!r}] must be a format list")
        if any(not isinstance(fmt, str) or fmt not in FORMATS for fmt in formats):
            raise ValueError(f"outputs[{name!r}] supports only {sorted(FORMATS)}")


def selected_formats(parameters, name):
    rules = parameters.get("outputs", {})
    if name in rules:
        return frozenset(rules[name])
    result = ()
    for pattern, formats in rules.items():
        if fnmatchcase(name, pattern):
            result = formats
    return frozenset(result)


def needed(parameters, name):
    reference_needed = (name == parameters.get("registration_image", "moment0ff") and
                        (parameters.get("image_registration") or
                         parameters.get("image_registration_with_ecc")))
    return bool(reference_needed or selected_formats(parameters, name) or
                selected_formats(parameters, name + PROJECTION))


def dataset_kind(name):
    """Semantic registry: frequency/spatial axes must never masquerade as RGB."""
    if name.endswith(PROJECTION):
        return dataset_kind(name[:-len(PROJECTION)])
    if name in {"spectrograms", "averaged_spectrogram", "sh_psd", "eigen_spectrogram"}:
        return "spectrum"
    if name in {"spectrum_line", "svd_eigenvalues", "svd_dc_spatial"} or any(token in name for token in ("registration", "coefs", "shifts", "flow_index")):
        return "table"
    if name in {"color_Doppler_image", "directional_Doppler_image", "shack_hartmann_autofocus_wavefront_color_image"}:
        return "color"
    return "image"


def computation_parameters(parameters):
    """Resolve optional computation while retaining registration dependencies."""
    if "outputs" not in parameters:
        return parameters
    validate_outputs(parameters)
    result = dict(parameters)
    reference = parameters.get("registration_image", "moment0ff")
    registration = parameters.get("image_registration", False) or parameters.get("image_registration_with_ecc", False)
    for flag, names in {
        "compute_gaussian_width": ("gaussian_width",),
        "pca_compute": ("pca_sum_ff" if parameters.get("pca_flatfield") else "pca_sum",),
        "color_Doppler_image": ("color_Doppler_image",),
        "directional_Doppler_image": ("directional_Doppler_image",),
        "shack_hartmann": ("shack_hartmann_sub_images", "shack_hartmann_shifts",
                            "shack_hartmann_zernike_coefs", "shack_hartmann_wavefront_phase"),
        "save_spectograms": ("spectrograms",),
        "save_averaged_spectrogram": ("averaged_spectrogram",),
    }.items():
        result[flag] = any(needed(parameters, name) or (registration and reference == name) for name in names)
    return result


class DefaultOutput(OutputClass):
    """Ordered numerical output with independent format and projection selection."""

    def __init__(self, file_reader, parameters, **kwargs):
        validate_outputs(parameters)
        self._projections = {}
        self._png_rows = {}
        self._seen = set()
        self._warned = set()
        super().__init__(file_reader, parameters, save_to_h5=any(
            "h5" in formats for formats in parameters["outputs"].values()), **kwargs)

    def _formats(self, name, value, temporal):
        self._seen.add(name)
        kind = dataset_kind(name)
        allowed = {"h5"}
        if kind == "table" and value.ndim <= (1 if temporal else 2):
            allowed.add("csv")
        if (value.ndim in ((1,) if temporal else (1, 2))
                and not np.iscomplexobj(value)):
            allowed.add("png")
        image = ((kind == "image" and value.ndim == 2) or
                 (kind == "color" and value.ndim == 3 and value.shape[-1] in (3, 4)))
        if image and not np.iscomplexobj(value):
            allowed.update(("avi", "mp4") if temporal else ("png",))
        requested = selected_formats(self.parameters, name)
        for fmt in sorted(requested - allowed):
            if (name, fmt) not in self._warned:
                logger.warning("Cannot save dataset %r (shape=%s, kind=%s) as %s: incompatible format for its axes/type; skipping export", name, value.shape, kind, fmt)
                self._warned.add((name, fmt))
        return requested & allowed

    def add_batch(self, outputs, t):
        # Drop unused intermediates before the scheduler copies host arrays.
        super().add_batch({name: value for name, value in outputs.items()
                           if needed(self.parameters, name)}, t)

    def _write_add(self, name, value, t):
        projection = name + PROJECTION
        if selected_formats(self.parameters, projection):
            if name not in self._projections:
                dtype = np.complex128 if np.iscomplexobj(value) else np.float64
                self._projections[name] = (np.zeros_like(value, dtype=dtype), 0)
            total, count = self._projections[name]
            total += value
            self._projections[name] = (total, count + 1)
        formats = self._formats(name, value, True)
        if "png" in formats:
            # Keep batch rows until finalization; the producer may reuse its array.
            self._png_rows.setdefault(name, []).append(value.copy())
        if "h5" in formats:
            self._hdf5_writer.append(name, value, t)
        state = self._streams.setdefault(name, {"csv": None, "media": None})
        if "csv" in formats:
            if state["csv"] is None:
                state["csv"] = data.CsvStream(self.target_dir / "csv" / f"{name}.csv")
            state["csv"].append(value)
        videos = formats & {"avi", "mp4"}
        if videos:
            if state["media"] is None:
                state["media"] = media.MediaStream(self.target_dir, name,
                    lambda fmt: self._open_video(name, fmt), formats=sorted(videos), save_average=False)
            state["media"].append(value)

    def _write_static(self, name, value):
        formats = self._formats(name, value, False)
        if "h5" in formats:
            self._hdf5_writer.write_static(name, value)
        if "csv" in formats:
            data.save_csv(self.target_dir / "csv" / f"{name}.csv", np.atleast_1d(value))
        if "png" in formats:
            value = np.atleast_2d(value)
            if name.endswith(PROJECTION):
                media._save_average_png(self.target_dir / "png" / f"{name}.png", value,
                                       self.parameters.get("resize_averaged_images", False))
            else:
                media.save_image_png(self.target_dir / "png" / f"{name}.png", value)

    def close(self, *, finalize=True):
        if self._closed:
            return
        try:
            if self._scheduler:
                self._scheduler.close(cancel=not finalize)
            if finalize:
                for name, rows in self._png_rows.items():
                    media.save_image_png(self.target_dir / "png" / f"{name}.png",
                                         np.stack(rows))
                for name, (total, count) in self._projections.items():
                    self._write_static(name + PROJECTION, total / count)
                for name, formats in self.parameters["outputs"].items():
                    if formats and not any(c in name for c in "*?[") and name not in self._seen:
                        logger.warning("Requested output dataset %r is unknown or unavailable with current processing settings", name)
        except BaseException:
            super().close(finalize=False)
            raise
        finally:
            self._projections.clear()
            self._png_rows.clear()
        super().close(finalize=finalize)
