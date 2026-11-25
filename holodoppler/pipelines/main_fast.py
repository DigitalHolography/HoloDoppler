"""Contiguous Fresnel processing with device-side image accumulation."""

from math import isfinite
from numbers import Integral, Real
from time import perf_counter
from types import SimpleNamespace

import numpy as np

from holodoppler import backend
from holodoppler.core.batching import calculate_batch_indices
from holodoppler.core.filtering import fourier_time_transform
from holodoppler.core.image_utils import gaussian_flatfield
from holodoppler.core.pipeline import prepare_input
from holodoppler.core.processing import run_batches
from holodoppler.core.progress import check_cancelled
from holodoppler.core.propagation import build_fresnel_kernel_in, ensure_yx_pixel_pitch, fresnel_transform
from holodoppler.core.registration import apply_register_images_shifts, register_images_shifts
from holodoppler.core.shack_hartmann import calculate_displacements_graph_laplacian
from holodoppler.core.zernike import fit_zernike_fresnel
from holodoppler.logging import logger
from holodoppler.saving.default_output import DefaultOutput, validate_outputs

FFT_MAPS = ("moment0", "moment1", "moment2", "moment0ff")
PCA_MAPS = ("pca_sum", "pca_sum_ff")


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


def _frequency_slices(ranges, size):
    if not isinstance(ranges, (list, tuple)) or not ranges:
        raise ValueError("frequency_ranges must contain at least one [start, end] range")
    merged = []
    for start, end in sorted(_range(pair, size, "frequency_ranges") for pair in ranges):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    return tuple(slice(start, end) for start, end in merged)


def _temporal_reducer(parameters, size):
    xp, fft = backend.xp, backend.fft
    svd = parameters.get("svd_filter", 0)
    if isinstance(svd, bool) or not isinstance(svd, Integral) or abs(svd) >= size:
        raise ValueError("svd_filter must be an integer with abs(svd_filter) < time_window")
    if parameters.get("mode", "fft") == "pca":
        if svd:
            raise ValueError("svd_filter is only available in FFT mode")
        start, end = _range(parameters.get("pca_index_range", [0, min(size, 16)]),
                            size, "pca_index_range")

        def reduce_pca(field, *, image_only=False):
            pixels = field.reshape(size, -1).T
            _, vectors = xp.linalg.eigh(pixels.conj().T @ pixels)
            projected = pixels @ vectors[:, start:end]
            return (xp.abs(projected).sum(axis=1).reshape(field.shape[1:]),)

        return reduce_pca

    parts = _frequency_slices(parameters.get("frequency_ranges", [[0, size]]), size)
    frequencies = fft.fftfreq(size, 1 / parameters["sampling_freq"]).astype(xp.float32)
    weights = (frequencies, frequencies ** 2)

    def reduce_fft(field, *, image_only=False):
        if svd:
            pixels = field.reshape(size, -1).T
            _, vectors = xp.linalg.eigh(pixels.conj().T @ pixels)
            rejected = vectors[:, -svd:] if svd > 0 else vectors[:, :-svd]
            pixels -= (pixels @ rejected) @ rejected.conj().T
            field = pixels.T.reshape(field.shape)
        spectrum = fourier_time_transform(xp, fft, field)
        maps = [xp.zeros(field.shape[1:], dtype=xp.float32)
                for _ in range(1 if image_only else 3)]
        for part in parts:
            power = xp.abs(spectrum[part])
            xp.square(power, out=power)
            maps[0] += power.sum(axis=0)
            if not image_only:
                for image, weight in zip(maps[1:], weights):
                    image += (weight[part] @ power.reshape(power.shape[0], -1)).reshape(image.shape)
        return maps

    return reduce_fft


def _subimages(frames, kernel, reduce_temporal):
    xp, fft = backend.xp, backend.fft
    nt, ny, nx = frames.shape
    sy, sx = ny // 5, nx // 5
    y0, x0 = (ny - 5 * sy) // 2, (nx - 5 * sx) // 2
    ys, xs = slice(y0, y0 + 5 * sy), slice(x0, x0 + 5 * sx)
    cropped = frames[:, ys, xs] * kernel[:, ys, xs]
    tiles = cropped.reshape(nt, 5, sy, 5, sx).transpose(1, 3, 0, 2, 4)
    fields = fft.fftshift(fft.fft2(tiles, axes=(-2, -1)), axes=(-2, -1))
    images = xp.empty((5, 5, sy, sx), dtype=xp.float32)
    for y in range(5):
        for x in range(5):
            images[y, x] = reduce_temporal(fields[y, x], image_only=True)[0]
    return images


def _autofocus(reader, starts, size, kernel, reducer, parameters, progress):
    xp, fft = backend.xp, backend.fft
    cached = {}
    total = None
    for start in starts:
        check_cancelled(progress)
        raw = reader.read_frames(first_frame=start, batch_size=size)
        cached[start] = raw
        images = _subimages(backend.to_backend(raw.reshape(size, *reader.frame_shape)),
                            kernel, reducer)
        if total is None:
            total = images
        else:
            total += images
    ny, nx = reader.frame_shape
    shifts_y, shifts_x = calculate_displacements_graph_laplacian(
        xp, fft, total / len(starts), pupil_threshold=1.5,
    )
    valid = xp.isfinite(shifts_y) & xp.isfinite(shifts_x)
    if int(valid.sum()) >= 3:
        shifts_y = xp.where(valid, shifts_y, xp.nan)
        shifts_x = xp.where(valid, shifts_x, xp.nan)
        coefs, phase = fit_zernike_fresnel(
            xp, ny, nx, *parameters["pixel_pitch"], parameters["wavelength"],
            shifts_y, shifts_x, (4, 5, 6),
        )
        if bool(xp.isfinite(coefs).all()) and bool(xp.isfinite(phase).all()):
            if abs(float(coefs[0])) <= 1.5:
                return kernel * xp.exp(-1j * phase), cached
    logger.warning("Fast Shack-Hartmann autofocus rejected the fit. Using the base Fresnel kernel.")
    return kernel, cached


def _run(file_path, parameters, *, preview=False, save=True, progress_callback=None):
    reader, p = prepare_input(file_path, parameters)
    with reader:
        return _run_prepared(reader, p, preview, save, progress_callback)


def _run_prepared(reader, p, preview, save, progress_callback):
    check_cancelled(progress_callback)
    size = _integer(p.get("time_window", 64), "time_window", 1)
    accu = _integer(p.get("accu", 1), "accu", 1)
    mode = p.get("mode", "fft")
    if mode not in ("fft", "pca"):
        raise ValueError("mode must be fft or pca")
    for key in ("image_registration", "shack_hartmann_autofocus"):
        if not isinstance(p.get(key, False), bool):
            raise ValueError(f"{key} must be a boolean")
    p["sampling_freq"] = _number(p.get("sampling_freq"), "sampling_freq")
    p["z"] = _number(p.get("z"), "z", signed=True)
    p["wavelength"] = _number(p.get("wavelength", 852e-9), "wavelength")
    pitch = p.get("pixel_pitch")
    if isinstance(pitch, bool) or not isinstance(pitch, (list, tuple, Real)):
        raise ValueError(f"Invalid or unresolved pixel_pitch: {pitch!r}")
    pitch = ensure_yx_pixel_pitch(float(pitch) if isinstance(pitch, Real) else pitch)
    if len(pitch) != 2:
        raise ValueError("pixel_pitch must be a scalar or [y, x]")
    p["pixel_pitch"] = tuple(_number(value, "pixel_pitch") for value in pitch)
    p["output_frame_stride"] = size * accu
    p["output_fps"] = p["sampling_freq"] / p["output_frame_stride"]
    p.setdefault("h5compression", 0)

    names = FFT_MAPS if mode == "fft" else PCA_MAPS
    flat_name = names[-1]
    p.setdefault("outputs", {name: ["h5"] for name in names})
    validate_outputs(p)
    reducer = _temporal_reducer(p, size)
    groups = calculate_batch_indices(
        p.get("first_frame", 0), p.get("end_frame", -1), size * accu, size * accu,
        reader.total_frames,
    )
    if not groups:
        logger.warning("Fast found no complete accumulation group.")
        return None
    if preview:
        groups = groups[:1]
    starts = range(groups.start, groups.start + len(groups) * size * accu, size)
    try:
        buffers = {name: np.empty((len(groups), *reader.frame_shape), dtype=np.float32)
                   for name in names}
    except MemoryError as exc:
        raise MemoryError("Cannot allocate Fast output maps in RAM. Reduce the frame range or increase accu.") from exc

    compute_start = perf_counter()
    xp, fft = backend.xp, backend.fft
    kernel = build_fresnel_kernel_in(xp, p["z"], p["pixel_pitch"], p["wavelength"], *reader.frame_shape)
    cached = {}
    if p.get("shack_hartmann_autofocus"):
        if min(reader.frame_shape) < 5:
            raise ValueError("Fast autofocus requires both image dimensions to be at least 5")
        kernel, cached = _autofocus(reader, starts[:accu], size, kernel, reducer, p,
                                    progress_callback)

    def read_frames(*, first_frame, batch_size):
        if first_frame in cached:
            return cached.pop(first_frame)
        return reader.read_frames(first_frame=first_frame, batch_size=batch_size)

    count = 0
    sums = None

    def compute(frames, reference):
        nonlocal count, sums
        field = fresnel_transform(xp, fft, frames, p["z"], p["pixel_pitch"], p["wavelength"],
                                  use_output_kernel=False, input_kernel=kernel, center=False)
        maps = reducer(field)
        if sums is None:
            sums = maps
        else:
            for total, image in zip(sums, maps):
                total += image
        count += 1
        if count < accu:
            return {}, reference

        averages = (total / accu if accu > 1 else total for total in sums)
        result = {name: fft.fftshift(image) for name, image in zip(names, averages)}
        count, sums = 0, None
        registration = p.get("image_registration", False)
        flat = gaussian_flatfield(result[names[0]], 35.0, backend.gaussian_filter)
        result[flat_name] = flat
        if registration:
            if reference is None:
                reference = flat
            else:
                dy, dx = register_images_shifts(xp, fft, reference, flat, radius=.8, sub_pixel=True)
                shifted = apply_register_images_shifts(
                    xp, xp.stack(tuple(result.values())), shift_y=dy, shift_x=dx, fft=fft,
                )
                result = dict(zip(result, shifted))
        return result, reference

    def consume(index, result):
        for name, image in result.items():
            buffers[name][index // accu] = backend.to_numpy(image)

    run_batches(SimpleNamespace(read_frames=read_frames), starts, size, compute, consume,
                progress_callback=progress_callback, cupy_prefetch_depth=3)
    check_cancelled(progress_callback)
    elapsed = perf_counter() - compute_start
    logger.info("Fast computed %d images from %d frames in %.2f s (%.1f frames/s)",
                len(groups), len(starts) * size, elapsed, len(starts) * size / elapsed)
    target = None
    if save:
        save_start = perf_counter()
        with DefaultOutput(reader, p, custom_relative_path="preview" if preview else None) as writer:
            target = str(writer.target_dir)
            for index in range(len(groups)):
                check_cancelled(progress_callback)
                if preview:
                    for name, images in buffers.items():
                        writer.write_static(name, images[index])
                else:
                    writer.add_batch({name: images[index] for name, images in buffers.items()}, index)
        logger.info("Fast exported %d images in %.2f s", len(groups), perf_counter() - save_start)
    if preview:
        return buffers["moment0ff" if mode == "fft" else "pca_sum"][0]
    return target


def process(file_path, parameters, progress_callback=None):
    return _run(file_path, parameters, progress_callback=progress_callback)


def preview(file_path, parameters, *, save_outputs=True, progress_callback=None):
    return _run(file_path, parameters, preview=True, save=save_outputs,
                progress_callback=progress_callback)
