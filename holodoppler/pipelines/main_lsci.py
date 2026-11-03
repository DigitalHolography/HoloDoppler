"""Sliding space?time speckle contrast and common saving."""
from contextlib import nullcontext

import numpy as np

from holodoppler import backend
from holodoppler.config import update_from_cine_metadata, update_from_holo_footer
from holodoppler.core.batching import calculate_batch_indices
from holodoppler.core.image_utils import resize_frames
from holodoppler.core.processing import run_batches
from holodoppler.core.progress import check_cancelled
from holodoppler.core.registration import apply_ecc_registration, register_with_ecc
from holodoppler.file_reader import get_reader
from holodoppler.saving import OutputClass, save_outputs

def _validate(p):
    from numbers import Integral
    for key, default in (("lsci_time_window_size", 5), ("lsci_time_window_stride", 64),
                         ("lsci_pixel_window_size", 5)):
        value = p.setdefault(key, default)
        if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
            raise ValueError(f"{key} must be a positive integer")
    if p["lsci_pixel_window_size"] % 2 != 1:
        raise ValueError("lsci_pixel_window_size must be odd")
    if p.get("lsci_pixel_window_boundary_mode", "reflect") not in {
        "reflect", "constant", "nearest", "mirror", "wrap"}:
        raise ValueError("Unsupported lsci_pixel_window_boundary_mode")
    for key, default in (("lsci_pixel_window_boundary_cval", 0.0),):
        value = p.setdefault(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
            raise ValueError(f"{key} must be finite")


def _contrast(frames, p):
    xp = backend.xp
    if backend.is_gpu:
        from cupyx.scipy.ndimage import uniform_filter
    else:
        from scipy.ndimage import uniform_filter
    frames = xp.asarray(frames, dtype=xp.float64)
    if frames.ndim == 2:
        frames = frames[None, ...]
    mean = frames.mean(axis=0)
    second = (frames * frames).mean(axis=0)
    size = p["lsci_pixel_window_size"]
    if size > 1:
        mode = p.get("lsci_pixel_window_boundary_mode", "reflect")
        cval = p["lsci_pixel_window_boundary_cval"]
        mean = uniform_filter(mean, size=size, mode=mode, cval=cval)
        second = uniform_filter(second, size=size, mode=mode, cval=cval * cval)
    std = xp.sqrt(xp.maximum(second - mean * mean, 0))
    ratio = std / xp.maximum(mean, 1e-6)
    low, high = xp.percentile(ratio, [1, 99])
    ratio = xp.clip(ratio, low, high)
    return {"STD": std.astype(xp.float32), "MEAN": mean.astype(xp.float32),
            "RATIO": ratio.astype(xp.float32)}


def _run_batches(reader, p, indices, preview_mode,
                 progress_callback, save_output):
    check_cancelled(progress_callback)
    if preview_mode:
        indices = indices[:1]
    preview_key = "RATIO"
    buffered = preview_mode or not p.get("live_saving", True) or p.get(
        "image_registration_with_ecc", False)
    output = {}
    emitted = 0
    context = (OutputClass(reader, p)
               if p.get("live_saving", True) and not preview_mode else nullcontext(None))
    with context as destination:
        def process_batch(frames, reference):
            return _contrast(frames, p), reference

        def square(value):
            if p.get("square", False):
                size = max(value.shape[-2:])
                value = resize_frames(backend.xp, backend.zoom,
                                      backend.to_backend(value), size, size)
            return backend.to_numpy(value)

        def consume(index, result):
            nonlocal emitted
            result = {key: backend.to_numpy(value) for key, value in result.items()}
            if not (p.get("image_registration_with_ecc", False) and not preview_mode):
                result = {key: square(value) for key, value in result.items()}
            if buffered:
                for key, value in result.items():
                    output.setdefault(key, []).append(value)
            else:
                destination.add_batch(result, emitted)
            emitted += 1

        run_batches(
            reader, indices, p["batch_size"], process_batch, consume,
            registration_enabled=p.get("image_registration", False),
            workers=p.get("numpy_num_workers", 8), cupy_async=p.get("cupy_async", True),
            cupy_prefetch_depth=p.get("cupy_prefetch_depth", 4),
            skip_every=p.get("skip_every"), progress_callback=progress_callback,
        )
        check_cancelled(progress_callback)
        if buffered:
            output = {key: np.stack(values) for key, values in output.items()}
            if p.get("image_registration_with_ecc", False) and not preview_mode:
                registration = register_with_ecc(
                    output[preview_key], radius=p.get("registration_ecc_radius", .8),
                    iterations=300, eps=1e-6, progress_callback=progress_callback,
                    ecc_min_threshold=p.get("registration_ecc_min_threshold", .7),
                )
                for key, value in output.items():
                    check_cancelled(progress_callback)
                    output[key] = square(apply_ecc_registration(
                        value, registration, background="mean"))
                output["registration_ecc"] = registration
            if destination is not None:
                for index in range(emitted):
                    check_cancelled(progress_callback)
                    destination.add_batch({key: value[index] for key, value in output.items()}, index)
            elif not preview_mode or save_output:
                check_cancelled(progress_callback)
                target_dir = save_outputs(
                    file_reader=reader,
                    output=({key: value[0] for key, value in output.items()}
                            if preview_mode else output),
                    parameters=p, custom_relative_path="preview" if preview_mode else None,
                    num_saving_workers=p.get("num_saving_workers", 0),
                    saving_queue_depth=p.get("saving_queue_depth"),
                )
        check_cancelled(progress_callback)
        if preview_mode:
            return output[preview_key][0]
        return str(destination.target_dir if destination is not None else target_dir)


def _run(file_path, parameters, preview_mode=False, progress_callback=None, *, save_output=True):
    parameters = dict(parameters)
    _validate(parameters)
    parameters["batch_size"] = parameters["lsci_time_window_size"]
    parameters["batch_stride"] = parameters["lsci_time_window_stride"]
    parameters["output_frame_stride"] = parameters["lsci_time_window_stride"]
    backend.set_backend(parameters.get("backend", "auto"))
    reader = get_reader(file_path)
    p = parameters
    if reader.extension == ".holo":
        p = update_from_holo_footer(p, reader.footer)
    elif reader.extension == ".cine":
        p = update_from_cine_metadata(p, reader.header)
    indices = calculate_batch_indices(
        p["first_frame"], p.get("end_frame", 0), p["batch_size"],
        p["batch_stride"], reader.total_frames, skip_every=p.get("skip_every"),
    )
    if not indices:
        return None
    return _run_batches(reader, p, indices, preview_mode, progress_callback, save_output)


def preview(file_path, parameters, *, save_outputs=True):
    return _run(file_path, parameters, preview_mode=True, save_output=save_outputs)


def process(file_path, parameters, progress_callback=None):
    return _run(file_path, parameters, progress_callback=progress_callback)
