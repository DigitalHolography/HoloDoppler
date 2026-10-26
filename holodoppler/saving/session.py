"""Output destinations and orchestration for streaming and complete bundles."""
from __future__ import annotations

import re
import shutil
import tempfile
import time
from numbers import Integral
from pathlib import Path
from typing import Any

import numpy as np

from holodoppler.logging import logger
from . import data, media, policy, scheduler


def create_directories(
    target_dir: Path,
) -> None:
    """Create the output directory structure."""
    target_dir = Path(target_dir)

    subdirectories = [
        "png",
        "avi",
        "mp4",
        "json",
        "csv",
        "yaml",
        "h5"
    ]

    for directory in subdirectories:
        data.ensure_directory(target_dir / directory)


def get_default_output_path(
    file_path: str | Path,
    mode: int = 0,
) -> Path:
    """
    Generate the standard output directory.

    mode 0:
        {base_name}/{base_name}_HD

    mode 1:
        {base_name}_HD_{index}

    mode 2:
        {base_name}/{base_name}_HD_{index}
    """
    path = Path(file_path)
    base_name = path.stem

    if mode not in (0, 1, 2):
        raise ValueError("mode must be 0, 1, or 2")

    if mode == 0:
        return path.parent / base_name / f"{base_name}_HD"

    indices = []
    search_directories = [
        path.parent,
        path.parent / base_name,
    ]

    for directory in search_directories:
        if not directory.exists():
            continue

        for subdir in directory.iterdir():
            if not subdir.is_dir():
                continue

            match = re.search(
                rf"^{re.escape(base_name)}_HD_(\d+)$",
                subdir.name,
            )
            if match:
                indices.append(int(match.group(1)))

    new_index = max(indices) + 1 if indices else 0

    if mode == 1:
        return path.parent / f"{base_name}_HD_{new_index}"

    return path.parent / base_name / f"{base_name}_HD_{new_index}"


def calculate_fps(
    parameters: dict[str, Any] | None,
    default_fps: float = 30.0,
    maximum_fps: float = 65.0,
) -> float:
    """Calculate output FPS with safe fallbacks."""

    # Existing profiles keep the historical display rate. Pipelines that change
    # temporal cadence can supply an explicit rate without changing other videos.
    value = (parameters or {}).get("output_fps", default_fps)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or value <= 0:
        raise ValueError("output_fps must be a finite positive number")
    return float(value)


def _prepare_output_directory(file_reader, parameters, custom_path, custom_relative_path):
    """Resolve and prepare a destination once, before any writers are opened."""
    if custom_path is not None and custom_relative_path is not None:
        raise ValueError("custom_path and custom_relative_path cannot be used together")
    default_path = get_default_output_path(file_reader.file_path)
    if custom_path is None:
        custom_path = parameters.get("custom_path")
    if custom_path is not None:
        target = Path(custom_path).expanduser()
        if not target.is_absolute():
            raise ValueError("custom_path must be an absolute path")
    else:
        if custom_relative_path is None:
            custom_relative_path = parameters.get("custom_relative_path")
        relative = Path(custom_relative_path or "")
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("custom_relative_path must stay within the output directory")
        target = default_path / relative
    option = parameters.get("overwrite_option", "overwrite")
    if option not in {"overwrite", "erase", "archive_old"}:
        raise ValueError(f"Unknown overwrite_option: {option}")
    if target.exists():
        if option == "archive_old":
            archive = data.ensure_directory(target.parent / "archive")
            destination = archive / target.name
            number = 1
            while destination.exists():
                destination = archive / f"{target.name} (#{number})"
                number += 1
            shutil.move(str(target), str(destination))
        elif option == "erase":
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
    create_directories(target)
    for directory in [target, *(target / name for name in
                      ("avi", "mp4", "h5", "png", "csv", "json", "yaml"))]:
        with tempfile.TemporaryFile(dir=directory) as probe:
            probe.write(b"HoloDoppler")
            probe.flush()
    return target


class OutputClass:
    """Append ordered batch results to AVI, MP4 and HDF5 with bounded memory.

    ``add(name, value, t)`` accepts one NumPy result at batch index ``t``.
    Use as a context manager to finalize videos and average PNGs reliably.
    Each name starts at index zero and keeps the same shape and dtype.
    Floating-point video levels are fixed from the first frame; HDF5 retains
    numerical values using the same selection and conversions as save_outputs.
    ``num_saving_workers`` defaults to zero (synchronous); positive values
    overlap saving with processing. ``saving_queue_depth`` counts outstanding
    batches, including active writes, and defaults to twice the worker count.
    Submit from one producer thread. Queued inputs are copied before returning;
    close waits for accepted work and reports background errors.
    Output files are partial if processing or writing fails.

    Example::

        with OutputClass(reader, parameters) as output:
            output.add("moment0", first_image, 0)
            output.add("moment0", second_image, 1)
    """

    def __init__(self, file_reader, parameters=None, custom_path=None,
                 custom_relative_path=None, save_to_h5=True):
        self.parameters = parameters or {}
        self.num_saving_workers, self.saving_queue_depth = scheduler._saving_options(
            self.parameters.get("num_saving_workers", 0),
            self.parameters.get("saving_queue_depth"))
        self.target_dir = _prepare_output_directory(
            file_reader, self.parameters, custom_path, custom_relative_path)
        self.fps = calculate_fps(self.parameters)
        self._streams = {}
        self._hdf5_writer = None
        self._scheduler = None
        self._accepted = {}
        self._closing = False
        self._closed = False
        try:
            data.save_metadata(self.target_dir, file_reader, self.parameters)
            if save_to_h5:
                path = self.target_dir / "h5" / f"{self.target_dir.name}_output.h5"
                self._hdf5_writer = data.Hdf5Writer(path, self.parameters)
            if self.num_saving_workers:
                self._scheduler = scheduler._SavingScheduler(
                    self.num_saving_workers, self.saving_queue_depth)
        except BaseException:
            self.close(finalize=False)
            raise

    # Compatibility accessors; policy and conversion are owned by their modules.
    _h5_selected = staticmethod(policy.save_to_hdf5)
    _h5_value = staticmethod(data.h5_value)

    @property
    def _h5(self):
        return None if self._hdf5_writer is None else self._hdf5_writer.file

    def _validate(self, name, value):
        if self._closed or self._closing:
            raise RuntimeError("OutputClass is closed")
        if (not isinstance(name, str) or not name or name in {".", ".."}
                or any(c in name for c in '/\\:')
                or name in {"HD_parameters", "HD_version", "git_commit"}):
            raise ValueError(f"Invalid output name: {name!r}")
        value = np.asarray(value)
        if value.dtype.kind not in "biufc" or value.size == 0:
            raise ValueError("Outputs must be nonempty numerical arrays")
        return value

    def _open_video(self, name, fmt):
        return media.open_video(self.target_dir, name, fmt, self.fps)

    def add(self, name: str, value: np.ndarray, t: int) -> None:
        """Append one output; a standalone call consumes one queue slot."""
        self.add_batch({name: value}, t)

    def add_batch(self, outputs: dict[str, np.ndarray], t: int) -> None:
        """Append a whole batch under one queue slot, copying queued inputs."""
        self._submit(outputs, t, static=False)

    def write_static(self, name: str, value: np.ndarray) -> None:
        """Save an aggregate or diagnostic without adding a batch dimension."""
        self._submit({name: value}, None, static=True)

    def _submit(self, outputs, t, *, static):
        if self._closed or self._closing:
            raise RuntimeError("OutputClass is closed")
        values = {}
        for name, value in outputs.items():
            value = self._validate(name, value)
            previous = self._accepted.get(name)
            if static:
                if previous is not None:
                    raise ValueError(f"Output {name!r} has already been written")
            else:
                if previous is not None and previous["static"]:
                    raise ValueError(f"Output {name!r} was already written as static data")
                expected = previous["count"] if previous else 0
                if isinstance(t, bool) or not isinstance(t, Integral) or t != expected:
                    raise ValueError(f"Output {name!r} expected batch index {expected}, got {t}")
                if previous and (value.shape != previous["shape"] or value.dtype != previous["dtype"]):
                    raise ValueError(f"Output {name!r} changed shape or dtype at batch {t}")
            values[name] = value

        def make_jobs():
            snapshots = {name: value.copy() if self._scheduler else value
                         for name, value in values.items()}
            jobs = []
            for name, value in snapshots.items():
                self._accepted[name] = dict(static=static, count=0 if static else t + 1,
                                            shape=value.shape, dtype=value.dtype)
                callback = self._write_static if static else self._write_add
                args = (name, value) if static else (name, value, t)
                jobs.append((name, callback, args))
            return jobs

        try:
            if self._scheduler:
                self._scheduler.submit(make_jobs)
            else:
                for name, callback, args in make_jobs():
                    callback(*args)
        except BaseException:
            self.close(finalize=False)
            raise

    def _write_add(self, name, value, t):
        formats = policy.output_formats(name, value, temporal=True)
        if self._hdf5_writer is not None and "h5" in formats:
            self._hdf5_writer.append(name, value, t)
        state = self._streams.setdefault(name, {"csv": None, "media": None})
        if "csv" in formats:
            if state["csv"] is None:
                state["csv"] = data.CsvStream(self.target_dir / "csv" / f"{name}.csv")
            state["csv"].append(value)
        elif "avi" in formats:
            if state["media"] is None:
                state["media"] = media.MediaStream(
                    self.target_dir, name, lambda fmt: self._open_video(name, fmt))
            state["media"].append(value)

    def _write_static(self, name, value):
        formats = policy.output_formats(name, value)
        if self._hdf5_writer is not None and "h5" in formats:
            self._hdf5_writer.write_static(name, value)
        if "csv" in formats:
            data.save_csv(self.target_dir / "csv" / f"{name}.csv", value)
        else:
            for callback, args, kwargs in media.media_jobs(self.target_dir, name, value, self.fps):
                callback(*args, **kwargs)

    def close(self, *, finalize: bool = True) -> None:
        if self._closed:
            return
        report_errors = finalize
        self._closing = True
        errors = []
        worker_error = None
        if self._scheduler:
            try:
                self._scheduler.close(cancel=not finalize)
            except BaseException as exc:
                worker_error = exc
        finalize = finalize and worker_error is None
        self._closed = True
        for state in self._streams.values():
            for kind, writer in state.items():
                if writer is not None:
                    try:
                        if kind == "media":
                            writer.close(finalize=finalize)
                        else:
                            writer.close()
                    except Exception as exc:
                        errors.append(exc)
        if self._hdf5_writer is not None:
            try:
                self._hdf5_writer.close()
            except Exception as exc:
                errors.append(exc)
        self._streams.clear()
        self._accepted.clear()
        if worker_error is not None and report_errors:
            raise worker_error
        if errors and finalize:
            raise RuntimeError("Failed to finalize output files") from errors[0]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close(finalize=exc_type is None)


def save_outputs(
    file_reader: Any,
    output: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    custom_path: str | Path | None = None,
    custom_relative_path: str | Path | None = None,
    save_to_h5: bool = True,
    *,
    num_saving_workers: int | None = None,
    saving_queue_depth: int | None = None,
) -> Path:
    """Save a complete HoloDoppler output bundle.

    custom_path:
        Absolute path used directly as the output directory.

    custom_relative_path:
        Path relative to the default *_HD output directory.

    num_saving_workers:
        None preserves legacy video scheduling; zero saves sequentially.
        Positive values share a bounded thread pool across output formats.
    """
    start_time = time.time()
    parameters = parameters or {}
    if num_saving_workers is not None:
        num_saving_workers, saving_queue_depth = scheduler._saving_options(
            num_saving_workers, saving_queue_depth)

    target_dir = _prepare_output_directory(
        file_reader, parameters, custom_path, custom_relative_path)

    logger.info(f"Saving output bundle to: {target_dir}")

    # FPS.
    fps = calculate_fps(
        parameters=parameters,
    )

    if num_saving_workers is not None:
        scheduler._run_saving_jobs(
            _bundle_saving_jobs(target_dir, file_reader, output, parameters, fps, save_to_h5),
            num_saving_workers, saving_queue_depth)
        print(f"Saving completed in {time.time() - start_time:.1f} seconds")
        return target_dir

    # Retain the legacy video scheduling default for callers without worker options.
    scheduler.save_videos_parallel(
        target_dir,
        output,
        fps=fps,
        video_formats=("avi","mp4"),
        writer="imageio",
    )

    media.save_pngs(
        target_dir,
        output,
    )

    data.save_csv_outputs(target_dir, output)

    data.save_metadata(
        target_dir,
        file_reader=file_reader,
        parameters=parameters,
    )

    if save_to_h5:
        h5_names = [name for name in output if policy.save_to_hdf5(name)]

        data.save_h5(
            target_dir,
            output,
            parameters=parameters,
            save_only_list=h5_names,
            git_commit=data.get_git_version(),
        )

    logger.info(f"Saving completed in {time.time() - start_time:.1f} seconds")
    return target_dir


def _bundle_saving_jobs(target_dir, file_reader, output, parameters, fps, save_to_h5):
    """Independent jobs sharing read-only arrays; a single job owns HDF5."""
    for name, value in output.items():
        if not isinstance(value, np.ndarray):
            continue
        if policy.is_csv_output(name):
            yield data.save_csv, (target_dir / "csv" / f"{name}.csv", value), {}
            continue
        yield from media.media_jobs(target_dir, name, value, fps)
    yield data.save_metadata, (target_dir,), {"file_reader": file_reader, "parameters": parameters}
    if save_to_h5:
        yield data.save_h5, (target_dir, output), {
            "parameters": parameters,
            "save_only_list": [name for name in output if policy.save_to_hdf5(name)],
            "git_commit": data.get_git_version(),
        }
