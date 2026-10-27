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
from holodoppler.logging import logger
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


def prepare_input(file_path, parameters, *, copy_parameters=True):
    """Resolve input metadata, optionally preserving legacy in-place resolution."""
    if copy_parameters:
        parameters = dict(parameters)
    backend.set_backend(parameters.get("backend", "auto"))
    reader = get_reader(file_path)
    if reader.extension in {".holo", ".cine"}:
        logger.debug("File header: %s", getattr(reader, "header", None))
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


def prepare_result(result, parameters):
    prepared = {}
    for key, value in result.items():
        if value is None:
            continue
        if parameters.get("square", False) and value.ndim == 2:
            size = max(value.shape)
            value = resize_frames(backend.xp, backend.zoom, backend.to_backend(value), size, size)
        prepared[key] = backend.to_numpy(value)
    return prepared


_MANAGED_DESTINATION = object()


def store_batch_result(output, key, value, index, total):
    """Allocate temporal output once, preserving its first shape and dtype."""
    value = backend.to_numpy(value)
    if key not in output:
        output[key] = np.empty((total, *value.shape), dtype=value.dtype)
    if output[key].shape[1:] != value.shape:
        raise ValueError(
            f"Output {key!r} changed shape from {output[key].shape[1:]} "
            f"to {value.shape} at batch {index}."
        )
    output[key][index] = value


def save_result_bundle(reader, parameters, output, *, preview=False):
    return save_outputs(
        file_reader=reader, output=output, parameters=parameters,
        **({"custom_relative_path": "preview"} if preview else {}),
        num_saving_workers=parameters.get("num_saving_workers", 0),
        saving_queue_depth=parameters.get("saving_queue_depth"),
    )


class _OutputSession:
    """Own temporal storage and ordered writes; static values have no time axis."""

    def __init__(self, reader, parameters, total, *, preview=False, preallocate=False,
                 destination=_MANAGED_DESTINATION):
        self.reader = reader
        self.parameters = parameters
        self.total = total
        self.preview = preview
        self.preallocate = preallocate
        self.buffered = (preview or destination is None
                         or not parameters.get("live_saving", True)
                         or parameters.get("image_registration_with_ecc", False))
        self.output = {}
        self.count = 0
        self.context = (OutputClass(reader, parameters)
                        if destination is _MANAGED_DESTINATION
                        and parameters.get("live_saving", True) and not preview
                        else nullcontext(None if destination is _MANAGED_DESTINATION
                                         else destination))

    def __enter__(self):
        self.destination = self.context.__enter__()
        return self

    def __exit__(self, *exc):
        return self.context.__exit__(*exc)

    def add(self, result):
        if self.buffered:
            for key, value in result.items():
                if self.preallocate:
                    store_batch_result(self.output, key, value, self.count, self.total)
                else:
                    self.output.setdefault(key, []).append(value)
        else:
            self.destination.add_batch(result, self.count)
        self.count += 1

    def complete(self):
        if self.buffered and not self.preallocate:
            self.output = {key: np.stack(values) for key, values in self.output.items()}

    def finish(self, static):
        if self.destination is not None:
            if self.buffered:
                for index in range(self.count):
                    self.destination.add_batch(
                        {key: value[index] for key, value in self.output.items()}, index)
            for key, value in static.items():
                self.destination.write_static(key, backend.to_numpy(value))
            return str(self.destination.target_dir)
        output = ({key: value[0] for key, value in self.output.items()}
                  if self.preview else dict(self.output))
        output.update(static)
        return str(save_result_bundle(self.reader, self.parameters, output,
                                      preview=self.preview))


def _register_output(output, parameters, preview_key, ecc_keys, ecc_key_predicate,
                     progress_callback):
    logger.info("Running Registration ECC algo:")
    registration = register_with_ecc(
        output[preview_key], radius=parameters.get("registration_ecc_radius", .8),
        iterations=300, eps=1e-6, progress_callback=progress_callback,
        ecc_min_threshold=parameters.get("registration_ecc_min_threshold", .7),
    )
    for key, value in output.items():
        if ecc_key_predicate is not None:
            selected = ecc_key_predicate(key)
        else:
            spatial = value.ndim == 3 and not key.startswith("shack_hartmann_")
            selected = ((ecc_keys is None and spatial)
                        or (ecc_keys is not None and key in ecc_keys) or "band_" in key)
        if selected:
            output[key] = apply_ecc_registration(value, registration, background="mean")
    output["registration_ecc"] = registration
    logger.info("Registration calculated.")


def run_pipeline(reader, parameters, process_batch, *, preview=False,
                 preview_key="moment0ff", reference=None, static=None,
                 stateful=False, accumulation=1, ecc_keys=None, progress_callback=None,
                 indices=None, prepare_batch=None, consume_batch=None,
                 finalize_result=None, ecc_key_predicate=None, static_factory=None,
                 preallocate=False, destination=_MANAGED_DESTINATION):
    """Run the shared ordered processing, accumulation, ECC and saving lifecycle.

    ``prepare_batch`` runs before download on the compute stream (or CPU workers).
    ``consume_batch`` runs on the caller before accumulation. Only this caller
    owns group sums. ``finalize_result`` replaces generic spatial preparation:
    with ECC it runs on one corrected backend batch at a time; otherwise it runs
    after ``prepare_batch`` before download. ``static_factory`` receives
    the number of completed input batches once processing and accumulation finish.

    A supplied destination remains caller-owned; otherwise this function owns
    the saving context, including aborting partial output on failure.
    ``preallocate`` requires stable temporal keys, shapes and dtypes across outputs.
    """
    indices = batch_indices(reader, parameters) if indices is None else indices
    if not indices:
        return None
    if preview:
        indices = indices[:accumulation]
    saving_parameters = dict(parameters)
    if accumulation > 1:
        saving_parameters["output_frame_stride"] = parameters["batch_stride"] * accumulation
        if "output_fps" in parameters:
            saving_parameters["output_fps"] = calculate_fps(parameters) / accumulation
        elif isinstance(parameters.get("sampling_freq"), (int, float)):
            saving_parameters["output_fps"] = (
                parameters["sampling_freq"] / saving_parameters["output_frame_stride"]
            )
        else:
            saving_parameters["output_fps"] = calculate_fps(parameters) / accumulation
    ecc_enabled = parameters.get("image_registration_with_ecc", False) and not preview
    total = (len(indices) + accumulation - 1) // accumulation
    sums = {}
    count = completed = 0

    def prepare(result):
        if prepare_batch is not None:
            result = prepare_batch(result)
        if finalize_result is not None and not ecc_enabled:
            result = finalize_result(result)
        return result

    with _OutputSession(reader, saving_parameters, total, preview=preview,
                        preallocate=preallocate, destination=destination) as session:
        def emit():
            nonlocal count
            result = {key: value if count == 1 else value / count for key, value in sums.items()}
            if finalize_result is None:
                preparation = {**parameters, "square": False} if ecc_enabled else parameters
                result = prepare_result(result, preparation)
            session.add(result)
            count = 0
            sums.clear()

        def consume(index, result):
            nonlocal count, completed
            if consume_batch is not None:
                result = consume_batch(result)
            for key, value in result.items():
                if value is None:
                    continue
                value = backend.to_numpy(value)
                if key in sums:
                    sums[key] += value
                else:
                    sums[key] = value.copy()
            count += 1
            completed += 1
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
            prepare_result=prepare if prepare_batch is not None or finalize_result is not None else None,
        )
        if count:
            emit()
        session.complete()
        # Resolve device aggregates before ECC needs backend space for corrected
        # batches. Static arrays never participate in temporal registration.
        static_output = dict(static or {})
        if static_factory is not None:
            static_output.update(static_factory(completed))
        if ecc_enabled:
            _register_output(session.output, parameters, preview_key, ecc_keys,
                             ecc_key_predicate, progress_callback)
            if finalize_result is not None:
                finished = {}
                for index in range(session.count):
                    current = {key: backend.to_backend(value[index])
                               for key, value in session.output.items()}
                    for key, value in finalize_result(current).items():
                        store_batch_result(finished, key, value, index, total)
                session.output = finished
            elif parameters.get("square", False):
                for key, value in session.output.items():
                    if key != "registration_ecc" and value.ndim == 3:
                        size = max(value.shape[-2:])
                        session.output[key] = backend.to_numpy(resize_frames(
                            backend.xp, backend.zoom, backend.to_backend(value), size, size))
        target_dir = session.finish(static_output)
        if preview:
            return session.output[preview_key][0]
        return target_dir
