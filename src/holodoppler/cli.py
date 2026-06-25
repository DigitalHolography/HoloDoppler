from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable


DEFAULT_PARAMETERS_NAME = "default_parameters_debug.json"


def preview(
    file_path: str | Path,
    parameters: dict[str, Any] | str | Path,
    tictoc: bool = False,
    save_debug: bool = True,
) -> Any:
    params = _load_parameters(parameters)
    if tictoc:
        params["tictoc"] = True

    pipeline_name = "preview_" + _pipeline_name(params)
    pipeline_func = _pipelines().get(pipeline_name)
    if pipeline_func is None:
        raise ValueError(f"Unknown preview pipeline: {pipeline_name}")

    return _call_pipeline(
        pipeline_func,
        file_path,
        params,
        save_debug=save_debug,
    )


def process(
    file_path: str | Path,
    parameters: dict[str, Any] | str | Path,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> Any:
    params = _load_parameters(parameters)
    pipeline_name = _pipeline_name(params)
    pipeline_func = _pipelines().get(pipeline_name)
    if pipeline_func is None:
        raise ValueError(f"Unknown pipeline: {pipeline_name}")

    return _call_pipeline(
        pipeline_func,
        file_path,
        params,
        progress_callback=progress_callback,
    )


def _call_pipeline(
    pipeline_func: Callable[..., Any],
    file_path: str | Path,
    parameters: dict[str, Any],
    **kwargs: Any,
) -> Any:
    signature = inspect.signature(pipeline_func)
    accepted_kwargs = {
        name: value
        for name, value in kwargs.items()
        if name in signature.parameters
    }
    return pipeline_func(file_path, parameters, **accepted_kwargs)


def _pipelines() -> dict[str, Callable[..., Any]]:
    from .pipelines import pipelines

    return pipelines


def _pipeline_name(parameters: dict[str, Any]) -> str:
    pipeline_name = parameters.get("pipeline_name", "moments_main_pipeline")
    if not isinstance(pipeline_name, str) or not pipeline_name:
        raise ValueError("parameters should have a non-empty 'pipeline_name' field")
    return pipeline_name


def _load_parameters(parameters: dict[str, Any] | str | Path) -> dict[str, Any]:
    loaded = _load_config(parameters)
    if not isinstance(loaded, dict):
        raise ValueError("parameters must resolve to a dictionary")
    return loaded


def _load_config(config: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(config, dict):
        return _list_to_tuple(config.copy())

    config_path = Path(config)
    with config_path.open("r", encoding="utf-8-sig") as file:
        if config_path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError as exc:
                raise SystemExit("PyYAML is required to load YAML configuration files.") from exc
            data = yaml.safe_load(file)
        else:
            data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Config must contain an object at top level: {config_path}")
    return _list_to_tuple(data)


def _list_to_tuple(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _list_to_tuple(item) for key, item in value.items()}
    if isinstance(value, list):
        return tuple(_list_to_tuple(item) for item in value)
    return value


def _existing_file(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"File does not exist: {path}")
    return path


def _default_config_path() -> Path | None:
    package_defaults = Path(__file__).resolve().parent / "ui" / "defaults"
    candidates = (
        Path("parameters") / DEFAULT_PARAMETERS_NAME,
        Path("parameters") / "default_parameters.yaml",
        package_defaults / DEFAULT_PARAMETERS_NAME,
    )
    for path in candidates:
        if path.is_file():
            return path
    return None


def _resolve_config_path(explicit_path: Path | None) -> Path:
    if explicit_path is not None:
        return explicit_path

    default_path = _default_config_path()
    if default_path is not None:
        return default_path

    raise SystemExit(
        "Error: No config file provided and no default configuration was found "
        "in ./parameters or bundled defaults."
    )


def _get_debug_config() -> dict[str, Any]:
    debug_paths_file = Path(".debug_paths.json")
    if not debug_paths_file.is_file():
        return {}
    try:
        data = json.loads(debug_paths_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid .debug_paths.json:\n{exc}") from exc
    return data if isinstance(data, dict) else {}


def _resolve_input_path(explicit_path: Path | None) -> Path:
    if explicit_path is not None:
        return explicit_path

    holofilepath = _get_debug_config().get("HOLOFILEPATH")
    if not holofilepath:
        raise SystemExit(
            "Error: No input file provided and HOLOFILEPATH not found in .debug_paths.json"
        )

    input_path = Path(str(holofilepath)).expanduser().resolve()
    if not input_path.is_file():
        raise SystemExit(f"Error: HOLOFILEPATH '{input_path}' does not exist")
    return input_path


def _coerce_cli_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _parse_dynamic_options(args: list[str], known_options: set[str]) -> dict[str, Any]:
    dynamic_args: dict[str, Any] = {}
    index = 0

    while index < len(args):
        arg = args[index]
        if not arg.startswith("--"):
            index += 1
            continue

        option_name = arg[2:]
        if option_name in known_options:
            index += 1
            continue

        if index + 1 < len(args) and not args[index + 1].startswith("--"):
            dynamic_args[option_name] = _coerce_cli_value(args[index + 1])
            index += 2
        else:
            dynamic_args[option_name] = True
            index += 1

    return dynamic_args


def _apply_cli_overrides(parameters: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    params = parameters.copy()

    if getattr(args, "tictoc", False):
        params["tictoc"] = True
    if getattr(args, "debug", False):
        params["debug"] = True
    if getattr(args, "backend", None) is not None:
        params["backend"] = args.backend

    for option, value in getattr(args, "dynamic_options", {}).items():
        params[option] = value

    return params


def _read_batch_file(batch_file: Path) -> list[Path]:
    paths: list[Path] = []
    base_dir = batch_file.parent

    try:
        lines = batch_file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SystemExit(f"Error reading batch file '{batch_file}': {exc}") from exc

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip().strip('"')
        if not line or line.startswith("#"):
            continue

        path = Path(line).expanduser()
        if not path.is_absolute():
            path = base_dir / path
        path = path.resolve()

        if not path.is_file():
            print(
                f"Warning: Line {line_number} in batch file '{batch_file}': "
                f"file does not exist: {path}. Skipping.",
                file=sys.stderr,
            )
            continue
        paths.append(path)

    if not paths:
        raise SystemExit(f"No valid file paths found in batch file: {batch_file}")
    return paths


def _batch_process(
    file_paths: list[Path],
    parameters: dict[str, Any],
    command: str,
) -> tuple[list[tuple[Path, Any]], list[tuple[Path, str]]]:
    results: list[tuple[Path, Any]] = []
    errors: list[tuple[Path, str]] = []
    runner = preview if command == "preview" else process

    for index, file_path in enumerate(file_paths, start=1):
        print(f"Processing file {index}/{len(file_paths)}: {file_path.name}")
        try:
            result = runner(file_path, parameters.copy())
        except Exception as exc:
            errors.append((file_path, str(exc)))
            print(f"Failed: {file_path.name} - {exc}", file=sys.stderr)
            continue
        results.append((file_path, result))
        print(f"Completed: {file_path.name}")

    print("")
    print("=" * 50)
    print("Batch processing complete:")
    print(f"  Total files: {len(file_paths)}")
    print(f"  Successful:  {len(results)}")
    print(f"  Failed:      {len(errors)}")

    if errors:
        print("")
        print("Failed files:")
        for path, error in errors:
            print(f"  - {path}: {error}")

    return results, errors


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "filepath",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Input file path. Uses HOLOFILEPATH from .debug_paths.json if omitted.",
    )
    parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Config JSON/YAML path. Uses bundled default parameters if omitted.",
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
        help="Force 'backend' to the specified value in parameters.",
    )
    parser.add_argument(
        "--batch",
        type=_existing_file,
        metavar="BATCH_FILE",
        help="Text file containing input paths, one per line.",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="holodoppler",
        description="HoloDoppler command-line tools.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    preview_parser = subparsers.add_parser("preview", help="Run in preview mode.")
    _add_common_arguments(preview_parser)

    process_parser = subparsers.add_parser("process", help="Run full processing.")
    _add_common_arguments(process_parser)

    return parser


def main() -> int:
    parser = _build_parser()
    args, remaining_args = parser.parse_known_args()
    known_options = {"tictoc", "debug", "backend", "batch"}
    args.dynamic_options = _parse_dynamic_options(remaining_args, known_options)

    config_path = _resolve_config_path(args.config)
    parameters = _apply_cli_overrides(_load_config(config_path), args)

    if args.batch is not None:
        print(f"Batch mode activated. Reading files from: {args.batch}")
        _batch_process(_read_batch_file(args.batch), parameters, args.command)
        return 0

    input_path = _resolve_input_path(args.filepath)
    if args.command == "preview":
        preview(input_path, parameters)
    else:
        process(input_path, parameters)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
