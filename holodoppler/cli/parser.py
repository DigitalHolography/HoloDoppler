"""Argument parsing for the HoloDoppler command-line interface."""

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union  # noqa: UP035

DEFAULT_PARAMETERS_PATH = Path("parameters/default_parameters_simple.yaml")
DEBUG_CONFIG_FILENAME = ".debug_paths.json"
GUI_COMMAND = "gui"


def _existing_file(value: str) -> Path:
    """Validate that a file path exists."""
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"File does not exist: {path}")
    return path


def _convert_dynamic_value(value: str) -> Union[int, float, str]:
    """Convert numeric strings to int or float; preserve other strings."""
    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        return value


def _parse_dynamic_options(
    args: List[str],
) -> Tuple[Dict[str, Any], List[str]]:
    """Parse unknown --options as flags or key/value pairs."""
    dynamic_options: Dict[str, Any] = {}
    remaining_args: List[str] = []
    i = 0

    while i < len(args):
        arg = args[i]

        if not arg.startswith("--"):
            remaining_args.append(arg)
            i += 1
            continue

        # Support --option=value as well as --option value.
        option = arg[2:]
        if "=" in option:
            name, value = option.split("=", 1)
            dynamic_options[name] = _convert_dynamic_value(value)
            i += 1
        elif i + 1 < len(args) and not args[i + 1].startswith("--"):
            dynamic_options[option] = _convert_dynamic_value(args[i + 1])
            i += 2
        else:
            dynamic_options[option] = True
            i += 1

    return dynamic_options, remaining_args


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add options shared by preview and process."""
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the full traceback in case of error.",
    )
    parser.add_argument(
        "--tictoc",
        action="store_true",
        help="Force 'tictoc' to true in parameters.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Force 'debug' to true in parameters.",
    )
    parser.add_argument(
        "--backend",
        type=str,
        help="Force the backend parameter to the specified value.",
    )


def _add_file_arguments(parser: argparse.ArgumentParser) -> None:
    """Add positional input and configuration file arguments."""
    parser.add_argument(
        "filepath",
        type=_existing_file,
        nargs="?",
        default=None,
        help=(
            "Input file path. Uses HOLOFILEPATH from "
            f"{DEBUG_CONFIG_FILENAME} if omitted. "
            "Ignored when --batch is used."
        ),
    )
    parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",
        default=None,
        help=(
            f"Config file path. Defaults to {DEFAULT_PARAMETERS_PATH}. "
            "In batch mode, specify the config as the only positional argument."
        ),
    )


def _add_batch_argument(parser: argparse.ArgumentParser) -> None:
    """Add the special batch-processing option."""
    parser.add_argument(
        "--batch",
        type=_existing_file,
        metavar="BATCH_FILE",
        help="Text file containing input file paths, one per line.",
    )


def _add_dynamic_options_note(parser: argparse.ArgumentParser) -> None:
    parser.epilog = (
        "Dynamic options:\n"
        "  --option          Sets the parameter to True\n"
        "  --option value    Sets the parameter to a converted value\n"
        "  --option=value    Equivalent key/value syntax\n"
        "  Numeric values are converted to int or float.\n"
        "Example: --threshold 0.5 --batch-size 512 --output-dir ./results"
    )


def _build_main_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    main_parser = argparse.ArgumentParser(
        prog="holodoppler",
        description="HoloDoppler: Holographic Doppler signal processing toolkit.",
        epilog=(
            "Examples:\n"
            "  holodoppler preview input.holo config.yaml\n"
            "  holodoppler process input.holo config.yaml --threshold 0.5\n"
            "  holodoppler preview --batch file_list.txt config.yaml\n"
            "  holodoppler gui"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = main_parser.add_subparsers(
        dest="command",
        required=True,
        help="Command to execute.",
    )

    for command, description in (
        ("preview", "Run preview processing."),
        ("process", "Run full processing."),
    ):
        subparser = subparsers.add_parser(
            command,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        _add_file_arguments(subparser)
        _add_common_arguments(subparser)
        _add_batch_argument(subparser)
        _add_dynamic_options_note(subparser)

    subparsers.add_parser(
        GUI_COMMAND,
        help="Launch the graphical user interface.",
        description="Launch HoloDoppler's GUI application.",
    )

    return main_parser


def parse_args(
    argv: Optional[List[str]] = None,
) -> argparse.Namespace:
    """Parse standard and dynamic CLI arguments."""
    parser = _build_main_parser()
    args, remaining_args = parser.parse_known_args(argv)

    dynamic_options, _ = _parse_dynamic_options(remaining_args)
    args.dynamic_options = dynamic_options

    # In batch mode, a single positional argument is the config file.
    if args.batch is not None and args.config is None and args.filepath is not None:
        args.config = args.filepath
        args.filepath = None

    return args