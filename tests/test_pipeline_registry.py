"""Pins the pipeline registry keys.

The registry derives its keys from module filenames
(``pipelines/__init__.py``), and the shipped parameter presets reference those
keys. A file rename therefore silently renames a pipeline, so the key set is
pinned here before any reorganisation touches ``holodoppler/pipelines/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from holodoppler.pipelines import pipelines


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARAMETERS_DIR = PROJECT_ROOT / "parameters"
DEFAULTS_DIR = PROJECT_ROOT / "holodoppler" / "ui" / "defaults"

# The exact registry keys shipped today.
GOLDEN_PROCESS_PIPELINES = frozenset(
    {
        "sh_avg",
        "simple",
        "sliding_shack_hartmann",
    }
)


def _process_keys() -> set[str]:
    return {key for key in pipelines if not key.startswith("preview_")}


def test_process_pipeline_keys_are_unchanged() -> None:
    assert _process_keys() == set(GOLDEN_PROCESS_PIPELINES), (
        "The registry keys changed. Renaming a module in holodoppler/pipelines/ "
        "renames its pipeline, which breaks every preset that references it.\n"
        f"missing: {sorted(GOLDEN_PROCESS_PIPELINES - _process_keys())}\n"
        f"added:   {sorted(_process_keys() - GOLDEN_PROCESS_PIPELINES)}"
    )


def test_every_pipeline_has_a_preview_equivalent() -> None:
    preview_keys = {key for key in pipelines if key.startswith("preview_")}

    assert preview_keys == {f"preview_{key}" for key in GOLDEN_PROCESS_PIPELINES}


def test_sliding_pipeline_key_is_not_the_filename() -> None:
    """``main_sliding_shack_hart`` is aliased to ``sliding_shack_hartmann``.

    Renaming the module to ``sliding_shack_hart.py`` would drop the alias and
    silently rename the pipeline.
    """
    assert "sliding_shack_hartmann" in pipelines
    assert "sliding_shack_hart" not in pipelines


@pytest.mark.parametrize(
    "preset_path",
    sorted(PARAMETERS_DIR.glob("*.yaml")),
    ids=lambda path: path.name,
)
def test_repository_presets_reference_registered_pipelines(preset_path: Path) -> None:
    name = yaml.safe_load(preset_path.read_text(encoding="utf-8"))["pipeline_name"]

    assert name in pipelines, (
        f"{preset_path.name} references {name!r}, which is not a registry key. "
        f"Available: {sorted(_process_keys())}"
    )


def test_bundled_presets_reference_registered_pipelines() -> None:
    """Every bundled preset must name a registered pipeline.

    Four bundled presets are known to be stale and are pinned separately in
    ``tests/test_known_issues.py``; this test covers the rest so a rename cannot
    quietly invalidate more of them.
    """
    stale = {
        "default_parameters_debug_angularsp.json",
        "default_parameters_debug_of_choroid.json",
        "default_parameters_simple_numpy.yaml",
        "default_parameters_sliding.yaml",
    }

    checked = 0

    for path in sorted(DEFAULTS_DIR.iterdir()):
        if not path.is_file() or path.name in stale:
            continue

        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"}:
            payload = yaml.safe_load(text)
        else:
            payload = json.loads(text)

        name = payload.get("pipeline_name")
        assert name in pipelines, (
            f"{path.name} references {name!r}, which is not a registry key"
        )
        checked += 1

    assert checked > 0
