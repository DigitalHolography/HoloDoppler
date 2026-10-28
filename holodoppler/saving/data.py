"""Numerical formats, metadata serialization, and HDF5/CSV resource ownership."""
from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import asdict, is_dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Iterable

import h5py
import numpy as np
import yaml

from holodoppler.get_version import get_version
from holodoppler.logging import logger
from . import policy


def ensure_directory(path: Path) -> Path:
    """Create a directory and report useful Windows filesystem diagnostics."""
    path = Path(path)

    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        absolute_path = path.resolve(strict=False)

        logger.debug(
            "Could not create directory %s (absolute=%s, cwd=%s, exists=%s, "
            "is_directory=%s, is_file=%s, parent=%s, parent_exists=%s): %s",
            path, absolute_path, Path.cwd(), absolute_path.exists(),
            absolute_path.is_dir(), absolute_path.is_file(),
            absolute_path.parent, absolute_path.parent.exists(), exc,
        )

        raise

    return path


def json_default(value: Any) -> Any:
    """Convert common scientific Python objects into JSON-compatible values."""
    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        return asdict(value)

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def to_serializable(value: Any) -> Any:
    """Recursively convert Python/NumPy objects into json/yaml savable objects."""
    if isinstance(value, dict):
        return {str(k): to_serializable(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [to_serializable(v) for v in value]

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        return to_serializable(asdict(value))

    return value


def save_txt(path: Path, value: Any) -> None:
    """Save arbitrary text or a string representation."""
    path = Path(path)
    ensure_directory(path.parent)

    if isinstance(value, str):
        text = value
    else:
        text = str(value)

    path.write_text(text, encoding="utf-8")


def save_csv(path: Path, value: Any) -> None:
    """
    Save CSV data.

    Supported inputs:
        - list of dictionaries
        - list/tuple of rows
        - numpy arrays (axes after the first are flattened into columns)
        - pandas-like objects exposing to_csv()
    """
    path = Path(path)
    ensure_directory(path.parent)

    if hasattr(value, "to_csv"):
        value.to_csv(path, index=False)
        return

    if isinstance(value, np.ndarray):
        value = np.asarray(value)

        if value.ndim == 1:
            value = value[:, None]

        if value.ndim > 2:
            value = value.reshape(value.shape[0], -1)

        if value.ndim != 2:
            raise ValueError(
                f"CSV numpy data must be 1-D or 2-D, got {value.shape}"
            )

        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerows(value.tolist())

        return

    if isinstance(value, (list, tuple)):
        if not value:
            path.write_text("", encoding="utf-8")
            return

        with path.open("w", newline="", encoding="utf-8") as handle:

            if all(isinstance(row, dict) for row in value):
                fieldnames = []
                for row in value:
                    for key in row:
                        if key not in fieldnames:
                            fieldnames.append(key)

                writer = csv.DictWriter(
                    handle,
                    fieldnames=fieldnames,
                )
                writer.writeheader()
                writer.writerows(value)

            else:
                writer = csv.writer(handle)
                writer.writerows(value)

        return

    raise TypeError(
        f"Unsupported CSV data type: {type(value).__name__}"
    )


def save_json(path: Path, value: Any) -> None:
    """Save a Python object as JSON."""
    path = Path(path)
    ensure_directory(path.parent)

    serializable = to_serializable(value)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(
            serializable,
            handle,
            indent=4,
            ensure_ascii=False,
        )


def save_yaml(path: Path, value: Any) -> None:
    """Save a Python object as YAML."""
    path = Path(path)
    ensure_directory(path.parent)

    serializable = to_serializable(value)

    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            serializable,
            handle,
            sort_keys=False,
            allow_unicode=True,
        )


def save_json_and_yaml(json_path: Path, yaml_path: Path, value: Any) -> None:
    """Save a Python object as YAML and JSON."""
    save_json(json_path, value)
    save_yaml(yaml_path, value)


def save_h5(
    target_dir: Path,
    data_map: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    save_only_list: Iterable[str] | None = None,
    h5_file_name = None,
    git_commit: str | None = None,
) -> Path:
    """
    Save numerical output data to HDF5.
    """
    target_dir = Path(target_dir)
    h5_dir = ensure_directory(target_dir / "h5")

    if h5_file_name is None:
        target_name = target_dir.name or "output"
    else:
        target_name = h5_file_name
    h5_path = h5_dir / f"{target_name}_output.h5"

    selected = None if save_only_list is None else set(save_only_list)

    logger.info(f"Saving H5: {h5_path}")

    with Hdf5Writer(h5_path, parameters, git_commit=git_commit) as writer:
        for name, value in data_map.items():
            if selected is not None and name not in selected:
                continue
            if isinstance(value, np.ndarray):
                writer.write_static(name, value)

    size_gb = h5_path.stat().st_size / (1024**3)

    logger.info("H5 saved: %s (%.2f GB)", h5_path, size_gb)

    return h5_path


def get_git_version() -> str:
    """Return the current Git commit, or a fallback string."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        OSError,
    ):
        return "Not Available"


def save_version_files(target_dir: Path) -> None:
    """Save version.txt and git_version.txt."""
    target_dir = Path(target_dir)
    version = f"py{get_version()}"
    git_commit = get_git_version()

    (target_dir / "version.txt").write_text(
        version + "\n",
        encoding="utf-8",
    )
    (target_dir / "git_version.txt").write_text(
        f"Git commit: {git_commit}\n"
        f"Version: {version}\n",
        encoding="utf-8",
    )


def save_metadata(
    target_dir: Path,
    file_reader: Any = None,
    parameters: dict[str, Any] | None = None,
) -> None:
    """Save generic and HoloVibes-specific metadata."""
    target_dir = Path(target_dir)
    json_dir = ensure_directory(target_dir / "json")
    yaml_dir = ensure_directory(target_dir / "yaml")

    if parameters is not None:
        save_json_and_yaml(
            json_dir / "parameters_holodoppler.json",
            yaml_dir / "parameters_holodoppler.yaml",
            parameters,
        )

    if file_reader is not None:
        if getattr(file_reader, "extension", None) == ".holo":
            footer = getattr(file_reader, "footer", None)
            if footer is not None:
                save_json_and_yaml(
                    json_dir / "holovibes_footer.json",
                    yaml_dir / "holovibes_footer.yaml",
                    footer,
                )

            header = getattr(file_reader, "header", None)
            if header is not None:
                if is_dataclass(header):
                    header = asdict(header)
                save_json_and_yaml(
                    json_dir / "holovibes_header.json",
                    yaml_dir / "holovibes_header.yaml",
                    header,
                )
        if getattr(file_reader, "extension", None) == ".cine":
            header = getattr(file_reader, "header", None)
            if header is not None:
                if is_dataclass(header):
                    header = asdict(header)
                save_json_and_yaml(
                    json_dir / "cine_metadata.json",
                    yaml_dir / "cine_metadata.yaml",
                    header,
                )

    save_version_files(target_dir)


def save_csv_outputs(
    target_dir: Path,
    output: dict[str, Any]
    ):
    """
    Save coefs/registration outputs to CSV.

    Returns the output names that should also be stored in HDF5.
    """
    csv_dir = ensure_directory(Path(target_dir) / "csv")

    for name, value in output.items():
        if value is None or not policy.is_csv_output(name):
            continue
        try:
            path = csv_dir / f"{name}.csv"
            save_csv(path, value)
            logger.info(f"Saved CSV: {path}")
        except Exception as exc:
            logger.exception(f"Failed to save CSV {name}: {exc}")


def h5_value(value: np.ndarray) -> np.ndarray:
    """Keep numerical invalid values while retaining float32 HDF5 storage."""
    if np.issubdtype(value.dtype, np.floating):
        return value.astype(np.float32)
    return value


class Hdf5Writer:
    """Own one HDF5 file and serialize all dataset writes with its lock."""

    def __init__(self, path: Path, parameters=None, *, git_commit=None):
        path = Path(path)
        ensure_directory(path.parent)
        self.lock = Lock()
        self.file = h5py.File(path, "w")
        try:
            commit = git_commit or get_git_version()
            version = f"py{get_version()}"
            if parameters is not None:
                self.file.create_dataset("HD_parameters", data=json.dumps(
                    to_serializable(parameters), ensure_ascii=False))
            self.file.create_dataset("HD_version", data=version)
            self.file.create_dataset("git_commit", data=commit)
            self.file.attrs["git_commit"] = commit
            self.file.attrs["version"] = version
        except BaseException:
            self.file.close()
            raise

    def append(self, name: str, value: np.ndarray, t: int) -> None:
        value = h5_value(value)
        with self.lock:
            if t == 0:
                self.file.create_dataset(name, shape=(0, *value.shape),
                                         maxshape=(None, *value.shape), dtype=value.dtype)
            dataset = self.file[name]
            dataset.resize(t + 1, axis=0)
            dataset[t] = value
            self.file.flush()

    def write_static(self, name: str, value: np.ndarray) -> None:
        with self.lock:
            self.file.create_dataset(name, data=h5_value(value))
            self.file.flush()

    def close(self) -> None:
        with self.lock:
            self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


class CsvStream:
    """Own one CSV stream, writing a flattened row per temporal batch."""

    def __init__(self, path: Path):
        self.handle = Path(path).open("w", newline="", encoding="utf-8")
        self.writer = csv.writer(self.handle)

    def append(self, value: np.ndarray) -> None:
        self.writer.writerow(value.reshape(-1).tolist())
        self.handle.flush()

    def close(self) -> None:
        self.handle.close()
