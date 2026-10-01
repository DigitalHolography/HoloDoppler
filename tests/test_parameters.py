"""Parameter-file compatibility.

The shipped parameter files are treated as compatibility fixtures: they must
keep loading, keep resolving to a known pipeline, and keep resolving to an
explicit backend mode. Nothing here rewrites them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from holodoppler.config import load_config
from holodoppler.execution.runner import resolve_backend_mode
from holodoppler.pipelines import PIPELINES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARAMETERS_DIR = PROJECT_ROOT / "parameters"
DEFAULTS_DIR = PROJECT_ROOT / "holodoppler" / "ui" / "defaults"

PARAMETER_FILES = sorted(PARAMETERS_DIR.glob("*.yaml")) + sorted(
    PARAMETERS_DIR.glob("*.json")
)

VALID_MODES = frozenset({"cpu", "gpu", "auto"})

# Pre-existing divergence between the two shipped copies of the sh_avg preset.
# ``build_installer.py`` compares these and therefore fails today. Reported, not
# fixed, by this PR.
SH_AVG_KEYS_ONLY_IN_PARAMETERS = frozenset(
    {
        "contrast",
        "contrast_gamma",
        "contrast_low_max_percent",
        "filter2d",
        "filter2d_low",
        "image_registration_with_ecc",
        "registration_ecc_min_threshold",
        "registration_ecc_radius",
        "registration_radius",
        "registration_ref_batch_size",
        "registration_ref_first_frame",
        "registration_sub_pixel",
        "shack_hartmann_autofocus",
    }
)


def _read_parameter_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)


def test_parameter_files_are_present() -> None:
    """Guard against a rename silently turning the whole module into a no-op."""
    assert PARAMETER_FILES, f"No parameter files found in {PARAMETERS_DIR}"


@pytest.mark.parametrize("path", PARAMETER_FILES, ids=lambda p: p.name)
def test_parameter_file_loads(path: Path) -> None:
    parameters = load_config(path)

    assert isinstance(parameters, dict)
    assert "pipeline_name" in parameters, f"{path.name} has no pipeline_name"
    assert isinstance(parameters["pipeline_name"], str)


@pytest.mark.parametrize("path", PARAMETER_FILES, ids=lambda p: p.name)
def test_parameter_file_pipeline_is_registered(path: Path) -> None:
    name = load_config(path)["pipeline_name"]

    assert name in PIPELINES, (
        f"{path.name} references unknown pipeline {name!r}. "
        f"Available: {sorted(PIPELINES)}"
    )


@pytest.mark.parametrize("path", PARAMETER_FILES, ids=lambda p: p.name)
def test_parameter_file_resolves_to_a_valid_backend_mode(path: Path) -> None:
    parameters = load_config(path)

    mode = resolve_backend_mode(parameters)

    assert mode in VALID_MODES


def test_parameters_without_a_backend_key_default_to_auto() -> None:
    """The compatibility default is 'auto', matching historical behaviour."""
    checked = 0

    for path in PARAMETER_FILES:
        parameters = load_config(path)
        if parameters.get("backend") is not None:
            continue
        if parameters.get("force_numpy", False):
            continue

        assert resolve_backend_mode(parameters) == "auto"
        checked += 1

    assert checked > 0, "No parameter file exercised the default backend path"


def test_offline_preset_pins_the_cpu_backend() -> None:
    """``force_numpy: true`` is an explicit CPU request in a shipped preset."""
    parameters = load_config(PARAMETERS_DIR / "default_parameters_simple_offline.yaml")

    assert parameters.get("force_numpy") is True
    assert resolve_backend_mode(parameters) == "cpu"


@pytest.mark.parametrize(
    "backend_value, expected",
    [
        ("cpu", "cpu"),
        ("numpy", "cpu"),
        ("gpu", "gpu"),
        ("cupy", "gpu"),
        ("cupyRAM", "gpu"),
        ("auto", "auto"),
    ],
)
def test_explicit_backend_values_resolve(backend_value: str, expected: str) -> None:
    assert resolve_backend_mode({"backend": backend_value}) == expected


def test_loading_parameter_files_does_not_modify_them() -> None:
    """Compatibility fixtures must be read-only from the loader's perspective."""
    before = {path.name: path.read_bytes() for path in PARAMETER_FILES}

    for path in PARAMETER_FILES:
        load_config(path)

    after = {path.name: path.read_bytes() for path in PARAMETER_FILES}

    assert before == after


def test_sh_avg_parameters_and_ui_defaults_desync_is_documented() -> None:
    """Pin the pre-existing divergence that breaks ``build_installer.py``.

    When the two copies are brought back into sync this pin must be removed.
    """
    repository = _read_parameter_file(PARAMETERS_DIR / "default_parameters_sh_avg.yaml")
    bundled = _read_parameter_file(DEFAULTS_DIR / "default_parameters_sh_avg.yaml")

    only_in_repository = set(repository) - set(bundled)
    only_in_bundled = set(bundled) - set(repository)
    differing = {
        key for key in set(repository) & set(bundled) if repository[key] != bundled[key]
    }

    assert only_in_repository == SH_AVG_KEYS_ONLY_IN_PARAMETERS, (
        "The sh_avg desync changed shape. Update SH_AVG_KEYS_ONLY_IN_PARAMETERS "
        "or remove this pin if the copies were synchronised."
    )
    assert only_in_bundled == set()
    assert differing == set()


def test_repository_parameter_files_have_a_bundled_default() -> None:
    """``build_installer.py`` requires every repository preset to be bundled."""
    bundled_names = {path.name for path in DEFAULTS_DIR.iterdir() if path.is_file()}

    for path in PARAMETER_FILES:
        assert path.name in bundled_names, (
            f"{path.name} has no bundled default; the installer build would fail"
        )
