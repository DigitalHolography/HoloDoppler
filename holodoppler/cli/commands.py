"""CLI commands.

Each command turns parsed arguments into a call on
:mod:`holodoppler.execution`. Argument parsing lives in
:mod:`holodoppler.cli.parser`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from holodoppler.config import load_config
from holodoppler.execution.batch import read_batch_file, run_batch
from holodoppler.execution.runner import run_pipeline

from .parser import (
    DEBUG_CONFIG_FILENAME,
    DEFAULT_PARAMETERS_PATH,
    GUI_COMMAND,
    KNOWN_CLI_OPTIONS,
    _parse_dynamic_options,
    build_main_parser,
)


# Exit codes.
EXIT_SUCCESS: int = 0
EXIT_FAILURE: int = 1


def preview(file_path: Path, parameters: Union[dict, Path, str]) -> Any:
    """
    Run in preview mode.

    Args:
        file_path: Path to the input file
        parameters: Either a parameters dict or a path to a config file

    Returns:
        The result from the preview pipeline
    """
    return run_pipeline(file_path, parameters, "preview")


def process(
    file_path: Path,
    parameters: Union[dict, Path, str],
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Any:
    """
    Run in process mode.

    Args:
        file_path: Path to the input file
        parameters: Either a parameters dict or a path to a config file
        progress_callback: Monitors progress bar, total count, and progress text (for the gui)

    Returns:
        The result from the process pipeline
    """
    return run_pipeline(file_path, parameters, "process", progress_callback=progress_callback)


def _load_debug_config() -> Dict[str, str]:
    """Load debug configuration from .debug_paths.json file."""
    debug_paths_file = Path(DEBUG_CONFIG_FILENAME)
    if debug_paths_file.exists():
        try:
            with debug_paths_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load debug config: {e}", file=sys.stderr)
            return {}
    return {}



def _resolve_input_path(provided_path: Optional[Path]) -> Path:
    """
    Resolve input file path.

    Args:
        provided_path: Path provided via CLI (or None)

    Returns:
        Resolved absolute Path

    Raises:
        SystemExit: If path cannot be resolved or doesn't exist
    """
    if provided_path is not None:
        return provided_path

    # Try debug config
    debug_config = _load_debug_config()
    holofilepath = debug_config.get("HOLOFILEPATH")
    if holofilepath:
        resolved_path = Path(holofilepath).expanduser().resolve()
        if resolved_path.exists():
            return resolved_path

    # No valid path found
    raise SystemExit(
        f"Error: No input file provided.\n"
        f"Please either:\n"
        f"  1. Provide a file path as an argument\n"
        f"  2. Set HOLOFILEPATH in {DEBUG_CONFIG_FILENAME}\n"
        f"  3. Use --batch to process multiple files from a list"
    )



def _resolve_config_path(provided_path: Optional[Path]) -> Path:
    """
    Resolve config file path.

    Args:
        provided_path: Path provided via CLI (or None)

    Returns:
        Resolved absolute Path

    Raises:
        SystemExit: If path cannot be resolved or doesn't exist
    """
    if provided_path is not None:
        if not provided_path.exists():
            raise SystemExit(f"Error: Config file does not exist: {provided_path}")
        return provided_path

    # Try default path
    if DEFAULT_PARAMETERS_PATH.exists():
        return DEFAULT_PARAMETERS_PATH

    # No valid config found
    raise SystemExit(
        f"Error: No config file provided and {DEFAULT_PARAMETERS_PATH} not found.\n"
        f"Please either:\n"
        f"  1. Provide a config file as an argument\n"
        f"  2. Create the default config at {DEFAULT_PARAMETERS_PATH}\n"
        f"  3. Set the HOLOCONFIG environment variable (not yet implemented)"
    )



def _apply_cli_overrides(parameters: dict, args: argparse.Namespace) -> dict:
    """
    Apply CLI overrides to the parameters dictionary.

    Args:
        parameters: Original parameters dict
        args: Parsed command-line arguments

    Returns:
        Modified copy of parameters
    """
    parameters = parameters.copy()  # Don't modify original

    # Handle standard CLI flags
    if getattr(args, "tictoc", False):
        parameters["tictoc"] = True

    if getattr(args, "debug", False):
        parameters["debug"] = True

    backend_value = getattr(args, "backend", None)
    if backend_value is not None:
        parameters["backend"] = backend_value

    # Handle dynamic flags (--optionA, --optionB, etc.)
    dynamic_options = getattr(args, "dynamic_options", {})
    for option, value in dynamic_options.items():
        parameters[option] = value

    return parameters



# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the HoloDoppler CLI.

    Args:
        argv: Optional command-line arguments (for testing)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    if argv is None:
        argv = sys.argv[1:]

    # Quick check for GUI mode
    if argv and argv[0] == GUI_COMMAND:
        # Handle GUI mode - import here to avoid circular imports
        from holodoppler.ui import UI

        UI().mainloop()
        return EXIT_SUCCESS

    # Build parser
    parser = build_main_parser()

    # Parse known args first
    args, remaining_args = parser.parse_known_args(argv)

    # Parse dynamic options from remaining arguments
    dynamic_options, _ = _parse_dynamic_options(remaining_args, KNOWN_CLI_OPTIONS)
    args.dynamic_options = dynamic_options

    # In batch mode there is no input filepath positional.
    # Therefore, if argparse assigned the only positional argument
    # to `filepath`, reinterpret it as the config path.
    if args.batch is not None and args.config is None and args.filepath is not None:
        args.config = args.filepath
        args.filepath = None

    mode = "preview" if args.command == "preview" else "process"

    try:
        # Resolve config path
        config_path = _resolve_config_path(args.config)

        # Load parameters and apply CLI overrides
        parameters = _apply_cli_overrides(load_config(config_path), args)

        # ===== BATCH PROCESSING =====
        if args.batch:
            print(f"Batch mode activated. Reading files from: {args.batch}")

            file_paths, missing = read_batch_file(args.batch)

            batch_result = run_batch(
                file_paths=file_paths,
                parameters=parameters,
                mode=mode,
                missing=missing,
            )

            if batch_result.failures:
                print(
                    f"Error: {batch_result.failed}/{batch_result.total} "
                    f"batch jobs failed.",
                    file=sys.stderr,
                )
                return EXIT_FAILURE

            return EXIT_SUCCESS

        # ===== SINGLE FILE PROCESSING =====
        input_path = _resolve_input_path(args.filepath)

        result = run_pipeline(input_path, parameters, mode)

        if mode == "preview":
            if result is not None:
                print(
                    f"Preview completed successfully. Result type: {type(result).__name__}"
                )
            else:
                print("Preview completed successfully (no result returned)")
        else:
            if result is not None:
                print(
                    f"Process completed successfully. Result type: {type(result).__name__}"
                )
            else:
                print("Process completed successfully (no result returned)")

        return EXIT_SUCCESS

    except SystemExit:
        raise  # Re-raise SystemExit from argparse or our code
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return EXIT_FAILURE
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc(file=sys.stderr)
        return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
