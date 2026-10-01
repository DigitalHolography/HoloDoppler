"""Loading processing parameters from disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import yaml


def load_config(
    config_path,
):
    """Load a YAML or JSON configuration.

    Lists are recursively converted to tuples.

    Parameters
    ----------
    config_path:
        Path to a YAML/JSON configuration file or an existing dictionary.

    Returns
    -------
    dict
        Configuration dictionary with lists converted to tuples.
    """
    if isinstance(config_path, Mapping):
        config = dict(config_path)

    else:
        config_path = Path(
            config_path
        )

        with config_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            suffix = config_path.suffix.lower()

            if suffix in {".yaml", ".yml"}:
                config = yaml.safe_load(file)

            elif suffix == ".json":
                config = json.load(file)

            else:
                raise ValueError(
                    f"Unsupported configuration format: "
                    f"{config_path.suffix!r}. "
                    "Expected .json, .yaml or .yml."
                )

    def list_to_tuple(value):
        if isinstance(value, dict):
            return {
                key: list_to_tuple(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return tuple(
                list_to_tuple(item)
                for item in value
            )

        return value

    return list_to_tuple(config)
