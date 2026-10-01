"""Runs one input file through its configured pipeline.

The runner owns everything that happens around a pipeline: loading the
configuration, selecting the backend, opening the input, and resolving
parameters that come from the file's metadata. Pipelines therefore receive an
already-open reader and never touch the filesystem themselves.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional, Union

import holodoppler.backend as backend
from holodoppler.config import load_config, resolve_metadata
from holodoppler.pipelines import PIPELINES, names as pipeline_names
from holodoppler.readers import FileReaderFactory

from .context import ExecutionContext, ExecutionMode


def resolve_backend_mode(parameters: dict) -> str:
    """Resolve the backend mode requested by configuration and CLI overrides.

    ``force_numpy`` is the legacy switch that used to be honoured inside the
    pipelines. It is an explicit CPU request, so it takes precedence over
    ``backend``.

    Returns
    -------
    str
        One of ``"cpu"``, ``"gpu"`` or ``"auto"``.

    Raises
    ------
    ValueError
        When ``backend`` is not a recognised backend name.
    """
    if parameters.get("force_numpy", False):
        return "cpu"

    requested = parameters.get("backend")
    if requested is None:
        return "auto"

    return backend.resolve_mode(requested).value


def run_pipeline(
    file_path: Union[str, Path],
    parameters: Any,
    mode: ExecutionMode = "process",
    *,
    progress_callback: Optional[Callable[..., None]] = None,
) -> Any:
    """Run ``file_path`` through the pipeline named by ``parameters``.

    Parameters
    ----------
    file_path:
        Input file. Its extension selects the reader.
    parameters:
        A parameters mapping, or a path to a configuration file.
    mode:
        ``"process"`` for a full run, ``"preview"`` for one reference batch.
    progress_callback:
        Optional progress reporter, passed through to the pipeline.

    Returns
    -------
    Any
        Whatever the pipeline returns.

    Raises
    ------
    BackendNotAvailableError
        When ``gpu`` is requested and CuPy/CUDA is not usable. Raised before any
        file is opened, so a failed GPU request writes no output.
    ValueError
        When ``pipeline_name`` is missing or unknown, or the file format is not
        supported.
    """
    if not isinstance(parameters, dict):
        parameters = load_config(parameters)

    # Select the backend before opening anything.
    context = ExecutionContext(
        backend=backend.set_backend(resolve_backend_mode(parameters)),
        mode=mode,
        progress_callback=progress_callback,
    )

    pipeline_name = parameters.get("pipeline_name")

    if not pipeline_name:
        raise ValueError(
            "Parameters should have a 'pipeline_name' field. "
            f"Available pipeline names: {list(pipeline_names())}"
        )

    pipeline = PIPELINES.get(pipeline_name)

    if pipeline is None:
        raise ValueError(
            f"Unknown pipeline: {pipeline_name!r}. "
            f"Available pipelines: {list(pipeline_names())}"
        )

    with FileReaderFactory.create(file_path) as file:
        print("file header :", file.header)

        config = resolve_metadata(parameters, file)

        if mode == "preview":
            return pipeline.preview(file, config, context)

        return pipeline.process(file, config, context)
