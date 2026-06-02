from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .utils import load_config
from .pipelines import pipelines


def preview(file_path, parameters: dict, tictoc=False):
    if not isinstance(parameters, dict):
        parameters = load_config(parameters)

    pipeline_name = parameters.get("pipeline_name", "preview_moments_main_pipeline")
    if "preview" not in pipeline_name:
        print(ValueError("Please use preview pipeline for preview"))
        pipeline_name = "preview_moments_main_pipeline"

    pipeline_func = pipelines.get(pipeline_name)
    if pipeline_func is None:
        raise ValueError(f"Unknown pipeline: {pipeline_name}")

    return pipeline_func(file_path, parameters)


def process(file_path, parameters: dict):
    if not isinstance(parameters, dict):
        parameters = load_config(parameters)

    pipeline_name = parameters.get("pipeline_name", "process_moments_main_pipeline")
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


def _resolve_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    debug_config = _get_debug_config()

    if args.input is None:
        holofilepath = debug_config.get("HOLOFILEPATH")
        if not holofilepath:
            raise SystemExit(
                "Error: No input file provided and HOLOFILEPATH not found in .debug_paths.json"
            )
        input_path = Path(holofilepath)
        if not input_path.exists():
            raise SystemExit(f"Error: HOLOFILEPATH '{input_path}' does not exist")
    else:
        input_path = args.input

    if args.config is None:
        config_path = Path("parameters/default_parameters_debug.json")
        if not config_path.exists():
            raise SystemExit(
                "Error: No config file provided and parameters/default_parameters_debug.json not found"
            )
    else:
        config_path = args.config

    return input_path, config_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="holodoppler",
        description="HoloDoppler command-line tools.",
    )
    parser.add_argument(
        "input",
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
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    input_path, config_path = _resolve_paths(args)

    debug_config = _get_debug_config()
    
    process(input_path, config_path)

    return 0