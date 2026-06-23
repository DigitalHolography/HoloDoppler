import argparse
import json
from pathlib import Path
from typing import Any

from .utils import load_config
from .pipelines import pipelines


def preview(file_path, parameters: dict):
    if not isinstance(parameters, dict):
        parameters = load_config(parameters)
    
    if "pipeline_name" not in parameters:
        raise ValueError("parameters should have a 'pipeline_name' field")

    pipeline_name = "preview_" + parameters.get("pipeline_name")

    pipeline_func = pipelines.get(pipeline_name)
    if pipeline_func is None:
        raise ValueError(f"Unknown pipeline preview, looking for: {pipeline_name}")
    
    return pipeline_func(file_path, parameters)


def process(file_path, parameters: dict):
    if not isinstance(parameters, dict):
        parameters = load_config(parameters)

    if "pipeline_name" not in parameters:
        raise ValueError("parameters should have a 'pipeline_name' field")

    pipeline_name = parameters.get("pipeline_name", "moments_main_pipeline")
    
    pipeline_func = pipelines.get(pipeline_name)
    if pipeline_func is None:
        raise ValueError(f"Unknown pipeline: {pipeline_name}")

    return pipeline_func(file_path, parameters)


def _existing_file(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"File does not exist: {path}")
    return path


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON file: {path}\n{exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Config JSON must contain an object at top level: {path}")
    return data


def _get_debug_config() -> dict:
    debug_paths_file = Path(".debug_paths.json")
    if debug_paths_file.exists():
        with open(debug_paths_file, "r") as f:
            return json.load(f)
    return {}


def _resolve_paths(args: argparse.Namespace, command: str) -> tuple[Path, Path]:
    debug_config = _get_debug_config()

    if args.filepath is None:
        holofilepath = debug_config.get("HOLOFILEPATH")
        if not holofilepath:
            raise SystemExit(
                "Error: No input file provided and HOLOFILEPATH not found in .debug_paths.json"
            )
        input_path = Path(holofilepath)
        if not input_path.exists():
            raise SystemExit(f"Error: HOLOFILEPATH '{input_path}' does not exist")
    else:
        input_path = args.filepath

    if args.config is None:
        config_path = Path("parameters/default_parameters_debug.json")
        if not config_path.exists():
            raise SystemExit(
                "Error: No config file provided and parameters/default_parameters_debug.json not found"
            )
    else:
        config_path = args.config

    return input_path, config_path


def _apply_cli_overrides(parameters: dict, args: argparse.Namespace) -> dict:
    """Apply CLI overrides to the parameters dictionary."""
    parameters = parameters.copy()  # Don't modify original
    
    # Handle --tictoc flag
    if args.tictoc:
        parameters["tictoc"] = True
    
    # Handle --debug flag
    if args.debug:
        parameters["debug"] = True
    
    # Handle --backend flag
    if args.backend is not None:
        parameters["backend"] = args.backend
    
    # Handle dynamic flags (--optionA, --optionB, etc.)
    if hasattr(args, 'dynamic_options'):
        for option, value in args.dynamic_options.items():
            parameters[option] = value
    
    return parameters


def _build_preview_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="holodoppler preview",
        description="HoloDoppler preview mode.",
    )
    parser.add_argument(
        "filepath",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Input file path. Uses HOLOFILEPATH from .debug_paths.json if not provided.",
    )
    parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Config file path. Uses parameters/default_parameters_debug.json if not provided.",
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
    
    return parser


def _build_process_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="holodoppler process",
        description="HoloDoppler process mode.",
    )
    parser.add_argument(
        "filepath",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Input file path. Uses HOLOFILEPATH from .debug_paths.json if not provided.",
    )
    parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Config file path. Uses parameters/default_parameters_debug.json if not provided.",
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
    
    return parser


def _add_dynamic_option(parser: argparse.ArgumentParser, option_name: str):
    """Add a dynamic option that can be used as a flag or with a value."""
    # Remove leading hyphens if present
    clean_name = option_name.lstrip('-')
    
    # Create a new argument that can be either store_true or store
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        f"--{clean_name}",
        action="store_true",
        help=f"Force '{clean_name}': true in parameters.",
    )
    group.add_argument(
        f"--{clean_name}-value",
        dest=clean_name,
        type=str,
        help=f"Force '{clean_name}' to specified value in parameters.",
    )


def _parse_dynamic_options(parser: argparse.ArgumentParser, args: list, known_options: set) -> tuple[argparse.Namespace, list]:
    """Parse dynamic options that aren't predefined."""
    dynamic_args = {}
    remaining_args = []
    i = 0
    
    while i < len(args):
        arg = args[i]
        if arg.startswith('--') and arg[2:] not in known_options:
            # This is a dynamic option
            option_name = arg[2:]
            
            # Check if next argument is a value (doesn't start with --)
            if i + 1 < len(args) and not args[i + 1].startswith('--'):
                # Has value
                dynamic_args[option_name] = args[i + 1]
                i += 2
            else:
                # No value, treat as boolean flag
                dynamic_args[option_name] = True
                i += 1
        else:
            remaining_args.append(arg)
            i += 1
    
    return dynamic_args, remaining_args


def main() -> int:
    # Create main parser with subparsers
    main_parser = argparse.ArgumentParser(
        prog="holodoppler",
        description="HoloDoppler command-line tools.",
    )
    subparsers = main_parser.add_subparsers(dest="command", required=True, help="Command to execute")
    
    # Preview subcommand
    preview_parser = subparsers.add_parser("preview", help="Run in preview mode")
    preview_parser.add_argument(
        "filepath",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Input file path. Uses HOLOFILEPATH from .debug_paths.json if not provided.",
    )
    preview_parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Config file path. Uses parameters/default_parameters_debug.json if not provided.",
    )
    preview_parser.add_argument(
        "--tictoc",
        action="store_true",
        help="Force 'tictoc': true in parameters.",
    )
    preview_parser.add_argument(
        "--debug",
        action="store_true",
        help="Force 'debug': true in parameters.",
    )
    preview_parser.add_argument(
        "--backend",
        type=str,
        help="Force 'backend' to specified value in parameters.",
    )
    
    # Process subcommand
    process_parser = subparsers.add_parser("process", help="Run in process mode")
    process_parser.add_argument(
        "filepath",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Input file path. Uses HOLOFILEPATH from .debug_paths.json if not provided.",
    )
    process_parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Config file path. Uses parameters/default_parameters_debug.json if not provided.",
    )
    process_parser.add_argument(
        "--tictoc",
        action="store_true",
        help="Force 'tictoc': true in parameters.",
    )
    process_parser.add_argument(
        "--debug",
        action="store_true",
        help="Force 'debug': true in parameters.",
    )
    process_parser.add_argument(
        "--backend",
        type=str,
        help="Force 'backend' to specified value in parameters.",
    )
    
    # Parse known args first
    args, remaining_args = main_parser.parse_known_args()
    
    # Define known options for each command
    known_options = {'tictoc', 'debug', 'backend', 'filepath', 'config'}
    
    # Parse dynamic options from remaining arguments
    dynamic_options, _ = _parse_dynamic_options(main_parser, remaining_args, known_options)
    
    # Store dynamic options in args
    args.dynamic_options = dynamic_options
    
    # Resolve input and config paths
    input_path, config_path = _resolve_paths(args, args.command)
    
    # Load config parameters
    parameters = load_config(config_path)
    
    # Apply CLI overrides
    parameters = _apply_cli_overrides(parameters, args)
    
    # Execute appropriate command
    if args.command == "preview":
        preview(input_path, parameters)
    elif args.command == "process":
        process(input_path, parameters)
    
    return 0


# Alternative implementation using a simpler approach with flags that accept optional values
class _StoreTrueOrValue(argparse.Action):
    """Custom action that stores True if no value provided, otherwise stores the value."""
    
    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            setattr(namespace, self.dest, True)
        else:
            setattr(namespace, self.dest, values)


def main_simple() -> int:
    """
    Simplified main function using a single parser with nargs='?' for options.
    Usage examples:
        holodoppler preview input.h5 config.json --optionA --optionB value --optionC
    """
    parser = argparse.ArgumentParser(
        prog="holodoppler",
        description="HoloDoppler command-line tools.",
    )
    parser.add_argument(
        "command",
        choices=["preview", "process"],
        help="Command to execute."
    )
    parser.add_argument(
        "filepath",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Input file path. Uses HOLOFILEPATH from .debug_paths.json if not provided.",
    )
    parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Config file path. Uses parameters/default_parameters_debug.json if not provided.",
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
    
    # Parse known args
    args, unknown = parser.parse_known_args()
    
    # Parse dynamic options (--optionA, --optionB value, etc.)
    dynamic_options = {}
    i = 0
    while i < len(unknown):
        arg = unknown[i]
        if arg.startswith('--'):
            option_name = arg[2:]
            # Check if next arg is a value (doesn't start with --)
            if i + 1 < len(unknown) and not unknown[i + 1].startswith('--'):
                dynamic_options[option_name] = unknown[i + 1]
                i += 2
            else:
                dynamic_options[option_name] = True
                i += 1
        else:
            i += 1
    
    # Resolve paths
    if args.filepath is None:
        debug_config = _get_debug_config()
        holofilepath = debug_config.get("HOLOFILEPATH")
        if not holofilepath:
            raise SystemExit("Error: No input file provided and HOLOFILEPATH not found in .debug_paths.json")
        input_path = Path(holofilepath)
        if not input_path.exists():
            raise SystemExit(f"Error: HOLOFILEPATH '{input_path}' does not exist")
    else:
        input_path = args.filepath
    
    if args.config is None:
        config_path = Path("parameters/default_parameters_debug.json")
        if not config_path.exists():
            raise SystemExit("Error: No config file provided and parameters/default_parameters_debug.json not found")
    else:
        config_path = args.config
    
    # Load and modify parameters
    parameters = load_config(config_path)
    
    if args.tictoc:
        parameters["tictoc"] = True
    if args.debug:
        parameters["debug"] = True
    if args.backend is not None:
        parameters["backend"] = args.backend
    
    # Apply dynamic options
    for option_name, value in dynamic_options.items():
        parameters[option_name] = value
    
    # Execute
    if args.command == "preview":
        preview(input_path, parameters)
    else:  # process
        process(input_path, parameters)
    
    return 0


if __name__ == "__main__":
    main()