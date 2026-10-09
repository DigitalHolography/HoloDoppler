from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .constants import SUPPORTED_INPUT_EXTENSIONS, SUPPORTED_LIST_EXTENSIONS


@dataclass(frozen=True)
class InputSelection:
    paths: list[Path]
    rejected: list[Path]


def expand_input_paths(raw_paths: list[str | Path]) -> InputSelection:
    accepted: list[Path] = []
    rejected: list[Path] = []
    seen: set[Path] = set()

    for raw_path in raw_paths:
        path = Path(raw_path).expanduser()
        suffix = path.suffix.lower()
        if path.is_dir():
            _append_holo_directory(path, accepted, rejected, seen)
        elif suffix in SUPPORTED_LIST_EXTENSIONS:
            for listed_path in _read_list_file(path):
                _append_input_path(listed_path, accepted, rejected, seen)
        else:
            _append_input_path(path, accepted, rejected, seen)

    return InputSelection(paths=accepted, rejected=rejected)


def _append_holo_directory(
    directory: Path,
    accepted: list[Path],
    rejected: list[Path],
    seen: set[Path],
) -> None:
    try:
        holo_files = sorted(
            (
                path
                for path in directory.resolve().rglob("*")
                if path.is_file() and path.suffix.lower() == ".holo"
            ),
            key=lambda path: str(path).casefold(),
        )
    except OSError:
        rejected.append(directory)
        return

    if not holo_files:
        rejected.append(directory)
        return

    for path in holo_files:
        _append_input_path(path, accepted, rejected, seen)


def _append_input_path(
    path: Path,
    accepted: list[Path],
    rejected: list[Path],
    seen: set[Path],
) -> None:
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        rejected.append(path)
        return

    if resolved.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS or not resolved.is_file():
        rejected.append(path)
        return

    if resolved not in seen:
        accepted.append(resolved)
        seen.add(resolved)


def _read_list_file(path: Path) -> list[Path]:
    if not path.is_file():
        return [path]

    base_dir = path.parent
    result: list[Path] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip().strip('"').strip("'")
        if not line or line.startswith("#"):
            continue
        listed_path = Path(line)
        result.append(listed_path if listed_path.is_absolute() else base_dir / listed_path)
    return result
