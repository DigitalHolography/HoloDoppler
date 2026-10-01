"""Command-line parsing for HoloDoppler.

This module only knows about arguments. It performs no configuration loading and
no processing; :mod:`holodoppler.cli.commands` turns the parsed result into a run.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Union


#: Used when no config file is supplied.
DEFAULT_PARAMETERS_PATH: Path = Path("parameters/default_parameters_simple.yaml")

#: Fallback file that supplies the input path when none is given.
DEBUG_CONFIG_FILENAME: str = ".debug_paths.json"

GUI_COMMAND: str = "gui"

#: Options that are handled by the parser rather than treated as parameter
#: overrides.
KNOWN_CLI_OPTIONS: set = {
    "tictoc",
    "debug",
    "backend",
    "filepath",
    "config",
    "batch",
    "command",
}


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
        metavar="{cpu,gpu,auto}",
        default=None,
        help=(
            "Force the numerical backend. "
            "cpu: use CPU only. "
            "gpu: require a working CUDA/CuPy backend. "
            "auto: use GPU when available, otherwise CPU (default). "
            "Legacy names such as 'cupyRAM' are still accepted."
        ),
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



def build_main_parser() -> argparse.ArgumentParser:
    """Build the main argument parser with subparsers."""
    main_parser = argparse.ArgumentParser(
        prog="holodoppler",
        description="HoloDoppler: Holographic Doppler signal processing toolkit.",
        epilog=(
            "Examples:\n"
            "  holodoppler preview input.holo config.yaml\n"
            "  holodoppler process input.holo config.yaml --debug --threshold 0.5\n"
            "  holodoppler process input.cine config.yaml --backend cpu\n"
            "  holodoppler preview --batch file_list.txt config.yaml\n"
            "  holodoppler gui                     # Launch GUI application\n"
            "\n"
            "For more information, visit: "
            "https://github.com/DigitalHolography/HoloDoppler"
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
