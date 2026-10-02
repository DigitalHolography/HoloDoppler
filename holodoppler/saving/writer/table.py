"""Text, CSV, JSON and YAML writers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import yaml

from holodoppler.saving.format.normalize import to_serializable
from holodoppler.saving.paths import ensure_directory, is_csv_h5_output

if TYPE_CHECKING:
    from holodoppler.saving.report import WriteTally


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
        - numpy 1-D / 2-D arrays
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


def save_json(path: Path, value: Any, tally: "WriteTally | None" = None) -> None:
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

    if tally is not None:
        tally.record_json()


def save_yaml(path: Path, value: Any, tally: "WriteTally | None" = None) -> None:
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

    if tally is not None:
        tally.record_yaml()


def save_csv_outputs(
    target_dir: Path,
    output: dict[str, Any],
    tally: "WriteTally | None" = None,
) -> list[str]:
    """
    Save coefs/registration outputs to CSV.

    Failures are counted in ``tally``; the caller reports them once.

    Returns the output names that should also be stored in HDF5.
    """
    csv_dir = ensure_directory(Path(target_dir) / "csv")
    h5_names = []

    for name, value in output.items():
        if value is None or not is_csv_h5_output(name):
            continue

        h5_names.append(name)

        try:
            path = csv_dir / f"{name}.csv"
            save_csv(path, value)

            if tally is not None:
                tally.record_csv()
        except Exception:
            if tally is not None:
                tally.record_failure()

    return h5_names
