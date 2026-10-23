"""Shared file setup and ordered output handling for processing pipelines."""

from contextlib import nullcontext

import numpy as np

from holodoppler import backend
from holodoppler.config import update_from_cine_metadata, update_from_holo_footer
from holodoppler.config.validation import validate_main_parameters
from holodoppler.core.batching import calculate_batch_indices
from holodoppler.core.image_utils import resize_frames
from holodoppler.core.processing import run_batches
from holodoppler.core.registration import apply_ecc_registration, register_with_ecc
from holodoppler.file_reader import get_reader
from holodoppler.saving import OutputClass, save_outputs, calculate_fps


def frame_stack(frames):
    return frames[None, ...] if frames.ndim == 2 else frames


def validate_reference_batch(reader, first, size, label, skip_every=None):
    try:
        indices = calculate_batch_indices(first, 0, size, size, reader.total_frames,
                                          skip_every=skip_every)
        if not indices:
            raise ValueError("no complete batch fits")
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{label} batch (first_frame={first}, batch_size={size}) "
            f"cannot fit within {reader.total_frames} file frames: {exc}"
        ) from exc


def prepare_input(file_path, parameters):
    parameters = dict(parameters)
    if parameters.get("force_numpy", False):
        backend.set_backend("numpy")
    reader = get_reader(file_path)
    if reader.extension == ".holo":
        parameters = update_from_holo_footer(parameters, reader.footer)
    elif reader.extension == ".cine":
        parameters = update_from_cine_metadata(parameters, reader.header)
    validate_main_parameters(parameters)
    return reader, parameters


def batch_indices(reader, parameters):
    return calculate_batch_indices(
        parameters["first_frame"], parameters.get("end_frame", 0),
        parameters["batch_size"], parameters["batch_stride"], reader.total_frames,
        skip_every=parameters.get("skip_every"),
    )


def read_reference(reader, parameters, first, size, label):
    validate_reference_batch(reader, first, size, label, parameters.get("skip_every"))
    return backend.to_backend(frame_stack(reader.read_frames(
        first_frame=first, batch_size=size, skip_every=parameters.get("skip_every"),
    ))).astype(backend.xp.float32, copy=False)


def output_name(name):
    return {"M0": "moment0", "M0ff": "moment0ff",
            "M1": "moment1", "M2": "moment2"}.get(name, name)


def prepare_result(result, parameters):
    prepared = {}
    for key, value in result.items():
        if value is None:
            continue
        if parameters.get("square", False) and value.ndim == 2:
            size = max(value.shape)
            value = resize_frames(backend.xp, backend.zoom, backend.to_backend(value), size, size)
        prepared[output_name(key)] = backend.to_numpy(value)
    return prepared


def run_pipeline(reader, parameters, process_batch, *, preview=False,
                 preview_key="moment0ff", reference=None, static=None,
                 stateful=False, accumulation=1, ecc_keys=None, progress_callback=None):
    """Consume batches in order, averaging groups before output and optional ECC.

    Stateful processors run without CPU workers. CUDA compute calls remain ordered
    on the shared runner's single compute stream. Only the caller owns group sums.
    """
    indices = batch_indices(reader, parameters)
    if not indices:
        return None
    if preview:
        indices = indices[:accumulation]
    saving_parameters = dict(parameters)
    if accumulation > 1:
        # Keep the acquisition stride in metadata and explicitly describe output cadence.
        saving_parameters["output_frame_stride"] = parameters["batch_stride"] * accumulation
        if "output_fps" in parameters:
            saving_parameters["output_fps"] = calculate_fps(parameters) / accumulation
        elif isinstance(parameters.get("sampling_freq"), (int, float)):
            saving_parameters["output_fps"] = (
                parameters["sampling_freq"] / saving_parameters["output_frame_stride"]
            )
        else:
            saving_parameters["output_fps"] = calculate_fps(parameters) / accumulation
    buffered = preview or not parameters.get("live_saving", True) or parameters.get(
        "image_registration_with_ecc", False)
    output, sums = {}, {}
    count = emitted = 0
    static = static or {}

    context = (OutputClass(reader, saving_parameters)
               if parameters.get("live_saving", True) and not preview else nullcontext(None))
    with context as destination:
        def emit():
            nonlocal count, emitted
            result = {key: value if count == 1 else value / count for key, value in sums.items()}
            # ECC estimates motion on the original spatial grid, before resizing.
            preparation = ({**parameters, "square": False}
                           if parameters.get("image_registration_with_ecc", False) and not preview
                           else parameters)
            result = prepare_result(result, preparation)
            if buffered:
                for key, value in result.items():
                    output.setdefault(key, []).append(value)
            else:
                destination.add_batch(result, emitted)
            emitted += 1
            count = 0
            sums.clear()

        def consume(index, result):
            nonlocal count
            for key, value in result.items():
                if value is None:
                    continue
                value = backend.to_numpy(value)
                if key in sums:
                    sums[key] += value
                else:
                    sums[key] = value.copy()
            count += 1
            if count == accumulation:
                emit()

        run_batches(
            reader, indices, parameters["batch_size"], process_batch, consume,
            registration_ref=reference,
            registration_enabled=parameters.get("image_registration", False),
            workers=0 if stateful else parameters.get("numpy_num_workers", 8),
            cupy_async=parameters.get("cupy_async", True),
            cupy_prefetch_depth=parameters.get("cupy_prefetch_depth", 4),
            skip_every=parameters.get("skip_every"), progress_callback=progress_callback,
        )
        if count:
            emit()
        if buffered:
            output = {key: np.stack(values) for key, values in output.items()}
            if parameters.get("image_registration_with_ecc", False) and not preview:
                registration = register_with_ecc(
                    output[preview_key], radius=parameters.get("registration_ecc_radius", .8),
                    iterations=300, eps=1e-6, progress_callback=progress_callback,
                    ecc_min_threshold=parameters.get("registration_ecc_min_threshold", .7),
                )
                for key in output:
                    spatial = output[key].ndim == 3 and not key.startswith("shack_hartmann_")
                    if ((ecc_keys is None and spatial)
                            or (ecc_keys is not None and key in ecc_keys) or "band_" in key):
                        output[key] = apply_ecc_registration(output[key], registration, background="mean")
                if parameters.get("square", False):
                    for key, value in output.items():
                        if value.ndim == 3:
                            size = max(value.shape[-2:])
                            output[key] = backend.to_numpy(resize_frames(
                                backend.xp, backend.zoom, backend.to_backend(value), size, size))
                output["registration_ecc"] = registration
            if destination is not None:
                for index in range(emitted):
                    destination.add_batch({key: value[index] for key, value in output.items()}, index)
            else:
                to_save = ({key: value[0] for key, value in output.items()}
                           if preview else dict(output))
                to_save.update(static)
                target_dir = save_outputs(
                    file_reader=reader, output=to_save, parameters=saving_parameters,
                    custom_relative_path="preview" if preview else None,
                    num_saving_workers=parameters.get("num_saving_workers", 0),
                    saving_queue_depth=parameters.get("saving_queue_depth"),
                )
        if destination is not None:
            for key, value in static.items():
                destination.write_static(key, backend.to_numpy(value))
        if preview:
            return output[preview_key][0]
        return str(destination.target_dir if destination is not None else target_dir)
