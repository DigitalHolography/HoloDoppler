"""Persistent export of caller-selected multidimensional results."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ._backend import asnumpy


def _write_group(group: Any, arrays: Mapping[str, Any], compression: str | None) -> None:
    for name, value in arrays.items():
        if isinstance(value, Mapping):
            _write_group(group.create_group(name), value, compression)
        else:
            data = asnumpy(value)
            dataset_compression = compression if data.ndim > 0 else None
            group.create_dataset(
                name,
                data=data,
                compression=dataset_compression,
            )


def save_analysis_h5(
    path: str | Path,
    arrays: Mapping[str, Any],
    *,
    metadata: Mapping[str, Any] | None = None,
    compression: str | None = "gzip",
    overwrite: bool = False,
) -> Path:
    """Save explicitly selected arrays and JSON-serializable metadata to HDF5.

    Existing files are protected unless ``overwrite=True`` is explicit.
    """

    import h5py

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w" if overwrite else "x") as handle:
        _write_group(handle, arrays, compression)
        if metadata is not None:
            handle.attrs["metadata_json"] = json.dumps(metadata, sort_keys=True)
        handle.attrs["axis_convention"] = (
            "H[t,...,y,x]; SH[e,f,...,y,x]; temporal frequencies unshifted"
        )
    return path
