"""Frontend-independent pipeline dispatch and batch execution.

Callers own their parameters. Pipelines must not mutate supplied mappings.
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Union

from holodoppler.config import load_config
from holodoppler.logger import logger, log_mapping
from holodoppler.pipelines import pipelines

PREVIEW_PREFIX = "preview_"


class PipelineMode(str, Enum):
    """Application pipeline modes."""

    PREVIEW = "preview"
    PROCESS = "process"


def _run_pipeline(
    file_path: Path,
    parameters: Union[dict, Path, str],
    mode: PipelineMode,
    *,
    progress_callback=None,
    warning_callback=None,
) -> Any:
    """Execute a pipeline with the given parameters."""
    if not isinstance(parameters, dict):
        parameters = load_config(parameters)

    if "pipeline_name" not in parameters:
        raise ValueError(
            "Parameters should have a 'pipeline_name' field. "
            f"Available pipeline names: {list(pipelines.keys())}"
        )

    if mode == PipelineMode.PREVIEW:
        pipeline_name = f"{PREVIEW_PREFIX}{parameters['pipeline_name']}"
    else:
        pipeline_name = parameters["pipeline_name"]

    pipeline_func: Optional[Callable] = pipelines.get(pipeline_name)

    if pipeline_func is None:
        available_pipelines = [
            name for name in pipelines if not name.startswith(PREVIEW_PREFIX)
        ]
        preview_pipelines = [
            name[len(PREVIEW_PREFIX):]
            for name in pipelines
            if name.startswith(PREVIEW_PREFIX)
        ]

        if mode == PipelineMode.PREVIEW:
            error_msg = (
                f"Unknown preview pipeline: '{pipeline_name}'.\n"
                f"Available preview pipelines: {preview_pipelines}\n"
                f"Available process pipelines: {available_pipelines}"
            )
        else:
            error_msg = (
                f"Unknown pipeline: '{pipeline_name}'.\n"
                f"Available pipelines: {available_pipelines}"
            )

        raise ValueError(error_msg)

    logger.info("%s: %s", mode.value.capitalize(), file_path)
    log_mapping("Parameters", parameters)

    def on_warning(code, message):
        logger.warning("%s: %s", code, message)
        if warning_callback is not None:
            warning_callback(code, message)

    result = pipeline_func(
        file_path,
        parameters,
        progress_callback=progress_callback,
        warning_callback=on_warning,
    )
    logger.info("%s complete: %s", mode.value.capitalize(), file_path)
    return result


def preview(file_path: Path, parameters: Union[dict, Path, str]) -> Any:
    """Run the preview pipeline."""
    return _run_pipeline(file_path, parameters, PipelineMode.PREVIEW)


def process(
    file_path: Path,
    parameters: Union[dict, Path, str],
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    warning_callback: Optional[Callable[[str, str], None]] = None,
) -> Any:
    """Run the process pipeline."""
    return _run_pipeline(
        file_path,
        parameters,
        PipelineMode.PROCESS,
        progress_callback=progress_callback,
        warning_callback=warning_callback,
    )


@dataclass
class BatchSummary:
    completed: int = 0
    errors: list[tuple[Path, str]] = field(default_factory=list)
    stopped: bool = False


def run_batch(file_paths, parameters, mode=PipelineMode.PROCESS, *,
              progress_callback=None, warning_callback=None, event_callback=None,
              result_callback=None, should_stop=None, tracebacks=False):
    """Run files sequentially, releasing results after their callback consumes them.

    Events use the UI queue's file_started, file_failed, and batch_progress
    dictionaries. Callbacks run synchronously; frontends own thread dispatch.
    """
    summary = BatchSummary()
    total = len(file_paths)

    def emit(kind, **fields):
        if event_callback is not None:
            event_callback(dict(kind=kind, **fields))

    for index, file_path in enumerate(file_paths, 1):
        if should_stop is not None and should_stop():
            summary.stopped = True
            logger.info("Stopped before the next file")
            break
        path = Path(file_path)
        emit("file_started", index=index, total=total, path=path)
        logger.info("File %s/%s: %s", index, total, path.name)
        pulse_not_detected = False

        def on_warning(code, message):
            nonlocal pulse_not_detected
            if code == "cardiac_pulse_not_detected":
                pulse_not_detected = True
            if warning_callback is not None:
                warning_callback(code, message)

        failed = False
        try:
            result = _run_pipeline(path, parameters, mode,
                                   progress_callback=progress_callback,
                                   warning_callback=on_warning)
            if result_callback is not None:
                result_callback(path, result)
            del result
            summary.completed += 1
        except Exception as exc:
            failed = True
            summary.errors.append((path, str(exc)))
            logger.error("Failed: %s: %s", path, exc, exc_info=tracebacks)
            emit("file_failed", path=path, message=str(exc))
        emit("batch_progress", completed=index, total=total, failed=failed,
             pulse_not_detected=pulse_not_detected)
    logger.info("Batch %s: %s successful, %s failed%s", mode.value,
                summary.completed, len(summary.errors), ", stopped" if summary.stopped else "")
    return summary


