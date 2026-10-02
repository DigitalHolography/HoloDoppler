"""HDF5 writer for numerical pipeline outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

import h5py
import numpy as np

from holodoppler.get_version import get_version
from holodoppler.saving.format.normalize import to_serializable
from holodoppler.saving.paths import ensure_directory
from holodoppler.saving.version import get_git_version

if TYPE_CHECKING:
    from holodoppler.saving.report import WriteTally


def save_h5(
    target_dir: Path,
    data_map: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    save_only_list: Iterable[str] | None = None,
    h5_file_name=None,
    git_commit: str | None = None,
    tally: "WriteTally | None" = None,
) -> Path:
    """
    Save numerical output data to HDF5.

    Only ``save_only_list`` entries that are NumPy arrays are stored; floating
    point data is cast to ``float32`` with NaN/Inf zeroed so the file stays
    readable by downstream tools.
    """
    target_dir = Path(target_dir)
    h5_dir = ensure_directory(target_dir / "h5")

    if h5_file_name is None:
        target_name = target_dir.name or "output"
    else:
        target_name = h5_file_name
    h5_path = h5_dir / f"{target_name}_output.h5"

    selected = None if save_only_list is None else set(save_only_list)

    with h5py.File(h5_path, "w") as h5:

        for name, value in data_map.items():

            if selected is not None and name not in selected:
                continue

            if value is None:
                continue

            if not isinstance(value, np.ndarray):
                continue

            # HDF5 should preserve useful numerical precision.
            if np.issubdtype(value.dtype, np.floating):
                value_to_save = np.nan_to_num(
                    value,
                    nan=0.0,
                    posinf=0.0,
                    neginf=0.0,
                ).astype(np.float32)

            else:
                value_to_save = value

            h5.create_dataset(
                name,
                data=value_to_save,
                compression=None,
            )

        if parameters is not None:
            h5.create_dataset(
                "HD_parameters",
                data=json.dumps(
                    to_serializable(parameters),
                    ensure_ascii=False,
                ),
            )

        h5.create_dataset(
            "HD_version",
            data=f"py{get_version()}",
        )

        h5.create_dataset(
            "git_commit",
            data=f"{git_commit or get_git_version()}",
        )

        h5.attrs["git_commit"] = git_commit or get_git_version()
        h5.attrs["version"] = f"py{get_version()}"

    if tally is not None:
        tally.record_h5()

    return h5_path
