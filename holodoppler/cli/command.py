"""HoloDoppler command-line execution module."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from holodoppler.config import load_config
from .parser import (
    DEBUG_CONFIG_FILENAME,
    GUI_COMMAND,
    parse_args,
)
from holodoppler.execution import PipelineMode, preview, process, run_batch
from holodoppler.logger import configure_logging, get_logger

from holodoppler.paths import default_parameters_path


logger = get_logger(__name__)


EXIT_SUCCESS = 0
EXIT_FAILURE = 1


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

    return default_parameters_path()


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
                        f"Line {line_num} in batch file "
                        f"'{batch_file}': File does not exist: {path}. Skipping.",
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
    summary = run_batch(file_paths, parameters, mode)
    return EXIT_FAILURE if summary.errors else EXIT_SUCCESS


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
    args = None
    try:
        args = parse_args(argv)

        if args.command == GUI_COMMAND:
            from holodoppler.ui import UI

            UI().mainloop()
            return EXIT_SUCCESS

        config_path = _resolve_config_path(args.config)
        parameters = _apply_cli_overrides(load_config(config_path), args)

        if args.batch is not None:
            logger.info("Reading batch files from: %s", args.batch)

            mode = (
                PipelineMode.PREVIEW
                if args.command == "preview"
                else PipelineMode.PROCESS
            )

            file_paths = _read_batch_file(args.batch)
            summary = run_batch(file_paths, parameters, mode, tracebacks=args.tracebacks)
            return EXIT_FAILURE if summary.errors else EXIT_SUCCESS

        input_path = _resolve_input_path(args.filepath)

        if args.command == "preview":
            preview(input_path, parameters)
        else:
            process(input_path, parameters)

        return EXIT_SUCCESS

    except SystemExit:
        raise
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user.")
        return EXIT_FAILURE
    except Exception as exc:
        logger.error("%s", exc, exc_info=bool(args and args.tracebacks))
        return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())