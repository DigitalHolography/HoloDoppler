"""HoloDoppler command-line execution module."""

import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from holodoppler.config import load_config
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

    return pipeline_func(
        file_path,
        parameters,
        progress_callback=progress_callback,
        warning_callback=warning_callback,
    )


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
        print(f"Warning: Could not load debug config: {exc}", file=sys.stderr)
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
                    print(
                        f"Warning: Line {line_num} in batch file "
                        f"'{batch_file}': File does not exist: {path}. Skipping.",
                        file=sys.stderr,
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
        print(f"Processing file {idx}/{total}: {file_path.name}")

        try:
            result = _run_pipeline(file_path, parameters.copy(), mode)

            if result is not None:
                print(
                    f"✓ Completed: {file_path.name} "
                    f"(result: {type(result).__name__})"
                )
            else:
                print(f"✓ Completed: {file_path.name} (no result)")

            success_count += 1

        except Exception as exc:
            errors.append((file_path, str(exc)))
            print(f"✗ Failed: {file_path.name} - {exc}", file=sys.stderr)

    print(f"\n{'=' * 50}")
    print(f"Batch processing complete ({mode.value} mode):")
    print(f"  Total files: {total}")
    print(f"  Successful:  {success_count}")
    print(f"  Failed:      {len(errors)}")

    if errors:
        print("\nFailed files:")
        for path, error in errors:
            print(f"  - {path.name}: {error}")

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
    try:
        args = parse_args(argv)

        if args.command == GUI_COMMAND:
            from holodoppler.ui import UI

            UI().mainloop()
            return EXIT_SUCCESS

        config_path = _resolve_config_path(args.config)
        parameters = _apply_cli_overrides(load_config(config_path), args)

        if args.batch is not None:
            print(f"Batch mode activated. Reading files from: {args.batch}")

            mode = (
                PipelineMode.PREVIEW
                if args.command == "preview"
                else PipelineMode.PROCESS
            )

            file_paths = _read_batch_file(args.batch)
            return _batch_process(file_paths, parameters, mode)

        input_path = _resolve_input_path(args.filepath)

        if args.command == "preview":
            result = preview(input_path, parameters)
            action = "Preview"
        else:
            result = process(input_path, parameters)
            action = "Process"

        if result is not None:
            print(f"{action} completed successfully. Result type: {type(result).__name__}")
        else:
            print(f"{action} completed successfully (no result returned)")

        return EXIT_SUCCESS

    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return EXIT_FAILURE
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)

        # Verbose traceback is handled below by the CLI wrapper if needed.
        import traceback

        if argv is None:
            argv = sys.argv[1:]

        if "--verbose" in argv:
            traceback.print_exc(file=sys.stderr)

        return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())