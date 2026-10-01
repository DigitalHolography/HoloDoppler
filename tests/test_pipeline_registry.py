"""Pins the pipeline registry.

Pipeline names are declared explicitly in ``holodoppler/pipelines/registry.py``
and the shipped parameter presets reference them, so the name set is pinned
here. Renaming a pipeline module must not silently rename a pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from holodoppler.pipelines import PIPELINES, SPECS, Pipeline, create, names, spec


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARAMETERS_DIR = PROJECT_ROOT / "parameters"
DEFAULTS_DIR = PROJECT_ROOT / "holodoppler" / "ui" / "defaults"

# The exact pipeline names shipped today.
GOLDEN_PIPELINES = (
    "simple",
    "sliding_shack_hartmann",
    "sh_avg",
)


def test_registry_names_are_pinned() -> None:
    assert names() == GOLDEN_PIPELINES, (
        "The registered pipeline names changed. Every parameter preset that "
        "references a pipeline by name must be updated with them.\n"
        f"expected: {GOLDEN_PIPELINES}\n"
        f"actual:   {names()}"
    )


def test_registry_exposes_one_instance_per_name() -> None:
    assert set(PIPELINES) == set(GOLDEN_PIPELINES)

    for name, pipeline in PIPELINES.items():
        assert isinstance(pipeline, Pipeline), f"{name} is not a Pipeline"
        assert pipeline.name == name, (
            f"{name}: the instance declares name={pipeline.name!r}"
        )


def test_specs_and_names_agree() -> None:
    assert tuple(item.name for item in SPECS) == names()

    for item in SPECS:
        assert spec(item.name) is item


def test_create_returns_a_fresh_instance_of_the_registered_class() -> None:
    first = create("simple")
    second = create("simple")

    assert type(first) is type(second)
    assert first is not second
    assert first.name == "simple"


def test_unknown_pipeline_raises_a_helpful_error() -> None:
    with pytest.raises(KeyError) as excinfo:
        spec("does_not_exist")

    message = str(excinfo.value)
    assert "Unknown pipeline" in message
    assert "simple" in message


def test_registry_does_not_derive_names_from_filenames() -> None:
    """The module name and the pipeline name are allowed to differ."""
    assert spec("sliding_shack_hartmann").module == "main_sliding_shack_hart"
    assert "sliding_shack_hart" not in PIPELINES


def test_every_pipeline_declares_whether_it_supports_preview() -> None:
    for name, pipeline in PIPELINES.items():
        supported = pipeline.supports_preview()
        assert isinstance(supported, bool), f"{name}: supports_preview is not a bool"
        assert supported, f"{name} does not implement preview()"


@pytest.mark.parametrize(
    "preset_path",
    sorted(PARAMETERS_DIR.glob("*.yaml")),
    ids=lambda path: path.name,
)
def test_repository_presets_reference_registered_pipelines(preset_path: Path) -> None:
    name = yaml.safe_load(preset_path.read_text(encoding="utf-8"))["pipeline_name"]

    assert name in PIPELINES, (
        f"{preset_path.name} references {name!r}, which is not a registered "
        f"pipeline. Available: {list(names())}"
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
        assert name in PIPELINES, (
            f"{path.name} references {name!r}, which is not a registered pipeline"
        )
        checked += 1

    assert checked > 0
