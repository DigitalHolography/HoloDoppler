from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import numpy as np
import os
from .plotting import DebugPlotterManager
from .pipelines import pipelines
import imageio.v3 as iio

from .utils import load_config


def preview(file_path, parameters: dict, tictoc=False) -> None:

    if not type(parameters) == dict:  # if given a path instead of a dict of parameters
        parameters = load_config(parameters)

    # Get pipeline name and parameters
    pipeline_name = parameters.get("pipeline_name", "preview_process_moments")

    if "preview" not in pipeline_name:
        print(ValueError("Please use preview pipeline for preview"))
        pipeline_name = "preview_process_moments"

    # Get the pipeline function
    pipeline_func = pipelines.get(pipeline_name)
    if pipeline_func is None:
        raise ValueError(f"Unknown pipeline: {pipeline_name}")

    # Execute the function
    result = pipeline_func(file_path, parameters)

    return result


def process(file_path, parameters: dict) -> None:

    if not type(parameters) == dict:  # if given a path instead of a dict of parameters
        parameters = load_config(parameters)

    # Get pipeline name and parameters
    pipeline_name = parameters.get("pipeline_name", "process_moments_latest")

    # Get the pipeline function
    pipeline_func = pipelines.get(pipeline_name)
    if pipeline_func is None:
        raise ValueError(f"Unknown pipeline: {pipeline_name}")

    # Execute the function
    result = pipeline_func(file_path, parameters)

    return result


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


def _load_json(path: Path) -> dict:
    """Load and parse JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def _get_debug_config() -> dict:
    """Load debug configuration if it exists."""
    debug_paths_file = Path(".debug_paths.json")
    if debug_paths_file.exists():
        with open(debug_paths_file, "r") as f:
            return json.load(f)
    return {}


def _cmd_preview(args: argparse.Namespace) -> int:
    debug_config = _get_debug_config()

    # Determine input path
    if args.input is None:
        holofilepath = debug_config.get("HOLOFILEPATH")
        if not holofilepath:
            print(
                "Error: No input file provided and HOLOFILEPATH not found in .debug_paths.json"
            )
            return 1
        input_path = Path(holofilepath)
        if not input_path.exists():
            print(f"Error: HOLOFILEPATH '{input_path}' does not exist")
            return 1
    else:
        input_path = args.input

    # Determine config path
    if args.config is None:
        config_path = Path("parameters/default_parameters_debug.json")
        if not config_path.exists():
            print(
                "Error: No config file provided and parameters/default_parameters_debug.json not found"
            )
            return 1
    else:
        config_path = args.config

    preview(input_path, config_path)
    return 0


def _cmd_process(args: argparse.Namespace) -> int:
    debug_config = _get_debug_config()

    # Determine input path
    if args.input is None:
        holofilepath = debug_config.get("HOLOFILEPATH")
        if not holofilepath:
            print(
                "Error: No input file provided and HOLOFILEPATH not found in .debug_paths.json"
            )
            return 1
        input_path = Path(holofilepath)
        if not input_path.exists():
            print(f"Error: HOLOFILEPATH '{input_path}' does not exist")
            return 1
    else:
        input_path = args.input

    # Determine config path
    if args.config is None:
        config_path = Path("parameters/default_parameters_debug.json")
        if not config_path.exists():
            print(
                "Error: No config file provided and parameters/default_parameters_debug.json not found"
            )
            return 1
    else:
        config_path = args.config

    process(input_path, config_path)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="holodoppler",
        description="HoloDoppler command-line tools.",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )

    preview_parser = subparsers.add_parser(
        "preview",
        help="Preview a HoloDoppler input file using a JSON configuration.",
    )
    preview_parser.add_argument(
        "input",
        type=_existing_file,
        nargs="?",  # Make optional
        default=None,
        help="Input file path. If not provided, uses HOLOFILEPATH from .debug_paths.json",
    )
    preview_parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",  # Make optional
        default=None,
        help="JSON configuration file path. If not provided, uses parameters/default_parameters_debug.json",
    )
    preview_parser.set_defaults(func=_cmd_preview)

    process_parser = subparsers.add_parser(
        "process",
        help="Process a HoloDoppler input file using a JSON configuration.",
    )
    process_parser.add_argument(
        "input",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Input file path. If not provided, uses HOLOFILEPATH from .debug_paths.json",
    )
    process_parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",
        default=None,
        help="JSON configuration file path. If not provided, uses parameters/default_parameters_debug.json",
    )
    process_parser.set_defaults(func=_cmd_process)

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return args.func(args)
