"""HoloDoppler command-line execution module."""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from holodoppler.config import load_config
from holodoppler.logging import configure_logging, logger
from .parser import (
    DEFAULT_PARAMETERS_PATH,
    DEBUG_CONFIG_FILENAME,
    GUI_COMMAND,
    parse_args,
)
from holodoppler.pipelines import pipelines


PREVIEW_PREFIX = "preview_"

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


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
    configure_logging()
    action = "Preview" if mode == PipelineMode.PREVIEW else "Processing"
    logger.info("%s started: %s", action, file_path)
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

    logger.debug("Using pipeline: %s", pipeline_name)
    result = pipeline_func(
        file_path,
        parameters,
        progress_callback=progress_callback,
        warning_callback=warning_callback,
    )
    logger.info("%s complete: %s", action, file_path)
    logger.debug("Pipeline result type: %s", type(result).__name__)
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


def _load_debug_config() -> Dict[str, str]:
    """Load paths from .debug_paths.json."""
    debug_paths_file = Path(DEBUG_CONFIG_FILENAME)

    if not debug_paths_file.exists():
        return {}

    try:
        with debug_paths_file.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not load debug config: %s", exc)
        return {}


def _resolve_input_path(provided_path: Optional[Path]) -> Path:
    """Resolve the input file path."""
    if provided_path is not None:
        return provided_path

    holofilepath = _load_debug_config().get("HOLOFILEPATH")

    if holofilepath:
        resolved_path = Path(holofilepath).expanduser().resolve()
        if resolved_path.is_file():
            return resolved_path

    raise SystemExit(
        "Error: No input file provided.\n"
        "Please either:\n"
        "  1. Provide a file path as an argument\n"
        f"  2. Set HOLOFILEPATH in {DEBUG_CONFIG_FILENAME}\n"
        "  3. Use --batch to process multiple files from a list"
    )


def _resolve_config_path(provided_path: Optional[Path]) -> Path:
    """Resolve the configuration file path."""
    if provided_path is not None:
        if not provided_path.is_file():
            raise SystemExit(f"Error: Config file does not exist: {provided_path}")
        return provided_path

    if DEFAULT_PARAMETERS_PATH.is_file():
        return DEFAULT_PARAMETERS_PATH

    raise SystemExit(
        f"Error: No config file provided and {DEFAULT_PARAMETERS_PATH} not found."
    )


def _read_batch_file(batch_file: Path) -> List[Path]:
    """Read and validate input paths from a batch file."""
    paths: List[Path] = []

    try:
        with batch_file.open("r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                path = Path(line).expanduser().resolve()

                if not path.is_file():
                    logger.warning(
                        "Line %s in batch file '%s': File does not exist: %s. Skipping.",
                        line_num, batch_file, path,
                    )
                    continue

                paths.append(path)

    except OSError as exc:
        raise SystemExit(f"Error reading batch file '{batch_file}': {exc}") from exc

    if not paths:
        raise SystemExit(
            f"No valid file paths found in batch file: {batch_file}\n"
            "Please ensure the file contains at least one valid input file."
        )

    return paths


def _batch_process(
    file_paths: List[Path],
    parameters: dict,
    mode: PipelineMode,
) -> int:
    """Process multiple files and return a failure exit code if any fail."""
    success_count = 0
    errors: List[Tuple[Path, str]] = []
    total = len(file_paths)

    for idx, file_path in enumerate(file_paths, 1):
        logger.info("Processing file %s/%s: %s", idx, total, file_path.name)

        try:
            _run_pipeline(file_path, parameters.copy(), mode)
            success_count += 1

        except Exception as exc:
            errors.append((file_path, str(exc)))
            logger.exception("Failed: %s", file_path.name)

    logger.info(
        "Batch processing complete (%s mode): %s total, %s successful, %s failed",
        mode.value, total, success_count, len(errors),
    )

    if errors:
        logger.error("Failed files: %s", ", ".join(path.name for path, _error in errors))

    return EXIT_FAILURE if errors else EXIT_SUCCESS


def _apply_cli_overrides(parameters: dict, args) -> dict:
    """Apply standard and dynamic CLI overrides."""
    parameters = parameters.copy()

    if args.tictoc:
        parameters["tictoc"] = True

    if args.debug:
        parameters["debug"] = True

    if args.backend is not None:
        parameters["backend"] = args.backend

    parameters.update(args.dynamic_options)

    return parameters


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point."""
    configure_logging()
    try:
        args = parse_args(argv)

        if args.command == GUI_COMMAND:
            from holodoppler.ui import UI

            UI().mainloop()
            return EXIT_SUCCESS

        config_path = _resolve_config_path(args.config)
        parameters = _apply_cli_overrides(load_config(config_path), args)

        if args.batch is not None:
            logger.info("Batch mode activated. Reading files from: %s", args.batch)

            mode = (
                PipelineMode.PREVIEW
                if args.command == "preview"
                else PipelineMode.PROCESS
            )

            file_paths = _read_batch_file(args.batch)
            return _batch_process(file_paths, parameters, mode)

        input_path = _resolve_input_path(args.filepath)

        if args.command == "preview":
            preview(input_path, parameters)
        else:
            process(input_path, parameters)

        return EXIT_SUCCESS

    except SystemExit as exc:
        if isinstance(exc.code, str):
            logger.error("%s", exc.code)
            return EXIT_FAILURE
        raise
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user.")
        return EXIT_FAILURE
    except Exception:
        logger.exception("Operation failed")
        return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
