"""HoloDoppler command-line interface module."""

import argparse
import copy
import inspect
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

from .utils import load_config
from .pipelines import pipelines

# ============================================================================
# CONSTANTS
# ============================================================================
DEFAULT_PARAMETERS_PATH: Path = Path("parameters/default_parameters_simple.yaml")
DEFAULT_SPECTRAL_PARAMETERS_PATH = (
    Path(__file__).parent / "ui" / "defaults" / "default_parameters_spectral_cube.yaml"
)
DEBUG_CONFIG_FILENAME: str = ".debug_paths.json"
GUI_COMMAND: str = "gui"
PREVIEW_PREFIX: str = "preview_"
BATCH_MODE: str = "batch"

# Known CLI options that shouldn't be treated as dynamic
KNOWN_CLI_OPTIONS: set = {
    "tictoc",
    "debug",
    "backend",
    "filepath",
    "config",
    "batch",
    "command",
}

# Exit codes
EXIT_SUCCESS: int = 0
EXIT_FAILURE: int = 1


class AppMode(str, Enum):
    """Application execution modes."""

    GUI = "gui"
    CLI = "cli"


class PipelineMode(str, Enum):
    """Pipeline execution modes."""

    PREVIEW = "preview"
    PROCESS = "process"


# ============================================================================
# CORE PIPELINE EXECUTION
# ============================================================================
def _run_pipeline(
    file_path: Path,
    parameters: Union[dict, Path, str],
    mode: PipelineMode,
    *,
    progress_callback=None,
    warning_callback=None,
    save_debug=None,
) -> Any:
    """
    Execute a pipeline with the given parameters.

    Args:
        file_path: Path to the input file
        parameters: Either a parameters dict or a path to a config file
        mode: Pipeline mode (preview or process)

    Returns:
        The result from the pipeline function

    Raises:
        ValueError: If pipeline_name is missing or pipeline is unknown
        SystemExit: If config file cannot be loaded
    """
    # Convert parameters to dict if needed
    if not isinstance(parameters, dict):
        parameters = load_config(parameters)

    # Validate parameters
    if "pipeline_name" not in parameters:
        raise ValueError(
            "Parameters should have a 'pipeline_name' field. "
            f"Available pipeline names: {list(pipelines.keys())}"
        )

    # Determine pipeline name based on mode
    pipeline_name: str
    if mode == PipelineMode.PREVIEW:
        pipeline_name = f"{PREVIEW_PREFIX}{parameters['pipeline_name']}"
    else:  # PipelineMode.PROCESS
        pipeline_name = parameters["pipeline_name"]

    # Get and validate pipeline function
    pipeline_func: Optional[Callable] = pipelines.get(pipeline_name)
    if pipeline_func is None:
        available_pipelines = [
            p for p in pipelines.keys() if not p.startswith(PREVIEW_PREFIX)
        ]
        preview_pipelines = [
            p.replace(PREVIEW_PREFIX, "")
            for p in pipelines.keys()
            if p.startswith(PREVIEW_PREFIX)
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

    # Execute pipeline
    return _call_pipeline(
        pipeline_func,
        file_path,
        parameters,
        progress_callback=progress_callback,
        warning_callback=warning_callback,
        save_debug=save_debug,
    )


def _call_pipeline(pipeline_func, file_path, parameters, **options):
    """Pass UI options supported by the selected pipeline, including older ones."""
    signature = inspect.signature(pipeline_func)
    accepts_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )
    kwargs = {
        name: value
        for name, value in options.items()
        if value is not None and (accepts_kwargs or name in signature.parameters)
    }
    return pipeline_func(file_path, parameters, **kwargs)


def preview(
    file_path: Path,
    parameters: Union[dict, Path, str],
    save_debug: bool = True,
) -> Any:
    """
    Run in preview mode.

    Args:
        file_path: Path to the input file
        parameters: Either a parameters dict or a path to a config file
        save_debug: Save preview outputs to disk when True

    Returns:
        The result from the preview pipeline
    """
    return _run_pipeline(
        file_path, parameters, PipelineMode.PREVIEW, save_debug=save_debug
    )


def _spectral_cube_parameters(parameters: dict) -> dict:
    """Keep spectral temporal settings independent from the primary pipeline."""
    from .saving import H5_OUTPUT_PATH_PARAMETER

    shared = {
        "first_frame", "end_frame", "spatial_propagation", "z", "wavelength",
        "pixel_pitch", "Fresnel_use_ouput_kernel", "filter2d", "filter2d_low",
        "sampling_freq", "corner_compensation", "contrast",
        "contrast_low_max_percent", "contrast_gamma", "saving_to_folder",
        "f_bins", H5_OUTPUT_PATH_PARAMETER,
    }
    spectral_parameters = load_config(DEFAULT_SPECTRAL_PARAMETERS_PATH)
    for name, value in parameters.items():
        if (
            name in shared
            or name.startswith("spectral_endpoints_")
            or name.startswith("shack_hartmann")
            or (
                name.startswith("spectral_cube_")
                and name not in {"spectral_cube_enabled", "spectral_cube_settings"}
            )
        ):
            spectral_parameters[name] = copy.deepcopy(value)

    overrides = parameters.get("spectral_cube_settings")
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        raise ValueError("spectral_cube_settings must be an object")
    spectral_parameters.update(copy.deepcopy(overrides))
    spectral_parameters["pipeline_name"] = "spectral_cube"
    # Append to the HDF5 actually saved by the primary pipeline.
    if H5_OUTPUT_PATH_PARAMETER in parameters:
        spectral_parameters[H5_OUTPUT_PATH_PARAMETER] = parameters[H5_OUTPUT_PATH_PARAMETER]
    return spectral_parameters


def process(
    file_path: Path,
    parameters: Union[dict, Path, str],
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    warning_callback: Optional[Callable[[str, str], None]] = None,
) -> Any:
    """
    Run in process mode.

    Args:
        file_path: Path to the input file
        parameters: Either a parameters dict or a path to a config file
        progress_callback: Receive completed count, total count, and progress text
        warning_callback: Receive a warning code and message without stopping processing

    Returns:
        The result from the process pipeline
    """
    from .saving import H5_OUTPUT_PATH_PARAMETER

    if not isinstance(parameters, dict):
        parameters = load_config(parameters)

    enabled = parameters.get("spectral_cube_enabled", True)
    if isinstance(enabled, str):
        enabled = enabled.strip().lower() not in {"0", "false", "no", "off"}
    runs_spectral_cube = parameters.get("pipeline_name") != "spectral_cube" and bool(enabled)

    def stage_progress(stage):
        if progress_callback is None:
            return None

        def report(completed, total, message=""):
            progress_callback(completed, total, f"{stage}: {message}" if message else stage)

        return report

    parameters.pop(H5_OUTPUT_PATH_PARAMETER, None)
    try:
        result = _run_pipeline(
            file_path,
            parameters,
            PipelineMode.PROCESS,
            progress_callback=(
                stage_progress("Primary pipeline") if runs_spectral_cube else progress_callback
            ),
            warning_callback=warning_callback,
        )
        if runs_spectral_cube:
            _run_pipeline(
                file_path,
                _spectral_cube_parameters(parameters),
                PipelineMode.PROCESS,
                progress_callback=stage_progress("Spectral cube"),
                warning_callback=warning_callback,
            )
        return result
    finally:
        parameters.pop(H5_OUTPUT_PATH_PARAMETER, None)


# ============================================================================
# PATH RESOLUTION
# ============================================================================
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


# ============================================================================
# BATCH PROCESSING
# ============================================================================
def _read_batch_file(batch_file: Path) -> List[Path]:
    """
    Read a text file containing file paths (one per line).

    Args:
        batch_file: Path to the batch file

    Returns:
        List of resolved Path objects

    Raises:
        SystemExit: If file cannot be read or no valid paths found
    """
    paths: List[Path] = []
    try:
        with batch_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                path = Path(line).expanduser().resolve()
                if not path.is_file():
                    print(
                        f"Warning: Line {line_num} in batch file '{batch_file}': "
                        f"File does not exist: {path}. Skipping.",
                        file=sys.stderr,
                    )
                    continue
                paths.append(path)
    except OSError as e:
        raise SystemExit(f"Error reading batch file '{batch_file}': {e}")

    if not paths:
        raise SystemExit(
            f"No valid file paths found in batch file: {batch_file}\n"
            f"Please ensure the file contains at least one valid .holo path."
        )

    return paths


def _batch_process(
    file_paths: List[Path], parameters: dict, mode: PipelineMode
) -> None:
    """
    Process multiple files in batch mode (side-effect only).

    This function prints progress and results to stdout/stderr but doesn't
    return results to avoid memory issues with large batches.

    Args:
        file_paths: List of input file paths
        parameters: Parameters dict to use for all files
        mode: Pipeline mode (preview or process)
    """
    results_count: int = 0
    errors: List[Tuple[Path, str]] = []

    # Sequential processing
    total = len(file_paths)
    for idx, file_path in enumerate(file_paths, 1):
        print(f"Processing file {idx}/{total}: {file_path.name}")
        try:
            # Copy parameters to avoid cross-file contamination
            params_copy = parameters.copy()

            # Execute pipeline
            result = _run_pipeline(file_path, params_copy, mode)

            # Optionally log result summary if needed
            if result is not None:
                result_type = type(result).__name__
                print(f"✓ Completed: {file_path.name} (result: {result_type})")
            else:
                print(f"✓ Completed: {file_path.name} (no result)")

            results_count += 1

        except Exception as e:
            errors.append((file_path, str(e)))
            print(f"✗ Failed: {file_path.name} - {e}", file=sys.stderr)

    # Summary
    print(f"\n{'='*50}")
    print(f"Batch processing complete ({mode.value} mode):")
    print(f"  Total files: {len(file_paths)}")
    print(f"  Successful:  {results_count}")
    print(f"  Failed:      {len(errors)}")

    if errors:
        print("\nFailed files:")
        for path, error in errors:
            print(f"  - {path.name}: {error}")


# ============================================================================
# ARGUMENT PARSING
# ============================================================================
def _existing_file(value: str) -> Path:
    """Validate that a file path exists."""
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"File does not exist: {path}")
    return path


def _parse_dynamic_options(
    args: List[str], known_options: set
) -> Tuple[Dict[str, Union[bool, str]], List[str]]:
    """
    Parse dynamic options that aren't predefined.

    Args:
        args: List of command-line arguments
        known_options: Set of known option names

    Returns:
        Tuple of (dynamic_options dict, remaining_args list)
    """
    dynamic_options: Dict[str, Union[bool, str]] = {}
    remaining_args: List[str] = []
    i = 0

    while i < len(args):
        arg = args[i]
        if arg.startswith("--") and arg[2:] not in known_options:
            # This is a dynamic option
            option_name = arg[2:]

            # Check if next argument is a value (doesn't start with --)
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                # Has value
                dynamic_options[option_name] = args[i + 1]
                i += 2
            else:
                # No value, treat as boolean flag
                dynamic_options[option_name] = True
                i += 1
        else:
            remaining_args.append(arg)
            i += 1

    return dynamic_options, remaining_args


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

    backend = getattr(args, "backend", None)
    if backend is not None:
        parameters["backend"] = backend

    # Handle dynamic flags (--optionA, --optionB, etc.)
    dynamic_options = getattr(args, "dynamic_options", {})
    for option, value in dynamic_options.items():
        parameters[option] = value

    return parameters


# ============================================================================
# MAIN PARSER BUILDERS
# ============================================================================
def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to a parser."""
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Prints the full traceback in case of error.",
    )
    parser.add_argument(
        "--tictoc",
        action="store_true",
        help="Force 'tictoc': true in parameters.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Force 'debug': true in parameters.",
    )
    parser.add_argument(
        "--backend",
        type=str,
        help="Force 'backend' to specified value in parameters.",
    )


def _add_file_arguments(parser: argparse.ArgumentParser) -> None:
    """Add file path arguments to a parser."""
    parser.add_argument(
        "filepath",
        type=_existing_file,
        nargs="?",
        default=None,
        help=(
            "Input file path (.holo file). "
            f"Uses HOLOFILEPATH from {DEBUG_CONFIG_FILENAME} if not provided. "
            "Ignored if --batch is used."
        ),
    )
    parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",
        default=None,
        help=(
            f"Config file path. Uses {DEFAULT_PARAMETERS_PATH} if not provided. "
            "Ignored if --batch is used (config must be specified as a file)."
        ),
    )


def _add_batch_argument(parser: argparse.ArgumentParser) -> None:
    """Add batch processing argument to a parser."""
    parser.add_argument(
        "--batch",
        type=_existing_file,
        metavar="BATCH_FILE",
        help=(
            "Path to a text file containing .holo file paths (one per line) "
            "for batch processing. Lines starting with '#' are ignored."
        ),
    )


def _add_dynamic_options_note(parser: argparse.ArgumentParser) -> None:
    """Add note about dynamic options to parser help."""
    parser.epilog = (
        "Dynamic Options:\n"
        "  Any --option can be passed to override parameters. Use:\n"
        "    --option        to set boolean True\n"
        "    --option value  to set string value\n"
        "  Example: --threshold 0.5 --verbose --output-dir ./results"
    )


def _build_main_parser() -> argparse.ArgumentParser:
    """Build the main argument parser with subparsers."""
    main_parser = argparse.ArgumentParser(
        prog="holodoppler",
        description="HoloDoppler: Holographic Doppler signal processing toolkit.",
        epilog=(
            "Examples:\n"
            "  holodoppler preview input.h5 config.yaml\n"
            "  holodoppler process input.h5 config.yaml --debug --threshold 0.5\n"
            "  holodoppler preview --batch file_list.txt config.yaml\n"
            "  holodoppler gui                     # Launch GUI application\n"
            "\n"
            "For more information, visit: https://github.com/yourusername/holodoppler"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = main_parser.add_subparsers(
        dest="command",
        required=True,
        help="Command to execute. Use 'holodoppler <command> -h' for help.",
    )

    # Preview subcommand
    preview_parser = subparsers.add_parser(
        "preview",
        help="Run in preview mode (first batch of frames for quick inspection)",
        description="HoloDoppler preview mode - generates quick previews for data inspection.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_file_arguments(preview_parser)
    _add_common_arguments(preview_parser)
    _add_batch_argument(preview_parser)
    _add_dynamic_options_note(preview_parser)

    # Process subcommand
    process_parser = subparsers.add_parser(
        "process",
        help="Run in process mode (full processing)",
        description="HoloDoppler process mode - generates full-quality processed data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _add_file_arguments(process_parser)
    _add_common_arguments(process_parser)
    _add_batch_argument(process_parser)
    _add_dynamic_options_note(process_parser)

    # GUI subcommand (no additional arguments)
    gui_parser = subparsers.add_parser(
        "gui",
        help="Launch the graphical user interface",
        description="Launch HoloDoppler's GUI application.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gui_parser.set_defaults(command=GUI_COMMAND)

    return main_parser


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
    parser = _build_main_parser()

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

    try:
        # Resolve config path
        config_path = _resolve_config_path(args.config)

        # Load parameters
        parameters = load_config(config_path)

        # Apply CLI overrides
        parameters = _apply_cli_overrides(parameters, args)

        # ===== BATCH PROCESSING =====
        if args.batch:
            print(f"Batch mode activated. Reading files from: {args.batch}")
            mode = (
                PipelineMode.PREVIEW
                if args.command == "preview"
                else PipelineMode.PROCESS
            )

            # Read files from batch file
            file_paths = _read_batch_file(args.batch)

            # Process in batch mode (side-effect only)
            _batch_process(file_paths=file_paths, parameters=parameters, mode=mode)
            return EXIT_SUCCESS

        # ===== SINGLE FILE PROCESSING =====
        # Resolve input path
        input_path = _resolve_input_path(args.filepath)

        # Execute appropriate command
        if args.command == "preview":
            result = preview(input_path, parameters)
            if result is not None:
                print(
                    f"Preview completed successfully. Result type: {type(result).__name__}"
                )
            else:
                print("Preview completed successfully (no result returned)")
        else:  # args.command == "process"
            result = process(input_path, parameters)
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
