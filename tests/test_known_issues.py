"""Pins for known problems that this PR deliberately does not fix.

These tests assert the *current, broken* state on purpose. If someone repairs
one of these areas, the corresponding pin will start failing, which is the
signal to update or delete it.
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

import pytest
import yaml

import numpy as np

import holodoppler.backend as backend
from holodoppler.pipelines import pipelines
from holodoppler.propagation import fresnel_transform


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = PROJECT_ROOT / "holodoppler"
PIPELINES_DIR = PACKAGE_DIR / "pipelines"
DEFAULTS_DIR = PACKAGE_DIR / "ui" / "defaults"


# ---------------------------------------------------------------------------
# Frozen pipelines
# ---------------------------------------------------------------------------

FROZEN_PIPELINES = ("main_pca_accumulation", "main_spectral_cube", "main_split_apertures")

# The exact modules that still import CuPy directly. They are the same frozen
# pipelines, so "no CuPy knowledge outside backend.py" is met for every
# reachable code path but not yet for the frozen three.
FROZEN_DIRECT_CUPY_MODULES = frozenset(
    {
        "pipelines/main_pca_accumulation.py",
        "pipelines/main_spectral_cube.py",
        "pipelines/main_split_apertures.py",
    }
)


@pytest.mark.parametrize("module_name", FROZEN_PIPELINES)
def test_frozen_pipelines_are_registered_but_not_importable(module_name: str) -> None:
    """Frozen as broken by decision, not by accident.

    The registry advertises them and parameter files reference them, but the
    modules call ``saving``/``utils``/``propagation`` APIs that no longer exist.
    """
    registry_key = module_name.removeprefix("main_")
    assert registry_key in pipelines

    with pytest.raises(ImportError):
        importlib.import_module(f"holodoppler.pipelines.{module_name}")


def test_frozen_pipelines_fail_on_missing_saving_or_utils_apis() -> None:
    """Record *why* the frozen pipelines are broken."""
    import holodoppler.saving as saving
    import holodoppler.utils as utils

    assert not hasattr(saving, "_create_directories")
    assert not hasattr(saving, "save_preview_images")
    assert not hasattr(saving, "H5_OUTPUT_PATH_PARAMETER")
    assert not hasattr(utils, "update_from_footer")
    assert not hasattr(utils, "temporal_gaussian")


def test_direct_cupy_imports_are_confined_to_the_frozen_pipelines() -> None:
    """``backend.py`` is the only supported place for CuPy knowledge."""
    pattern = re.compile(r"^\s*(?:import|from)\s+cupyx?\b", re.MULTILINE)

    offenders = set()

    for path in sorted(PACKAGE_DIR.rglob("*.py")):
        if path.name == "backend.py":
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            offenders.add(path.relative_to(PACKAGE_DIR).as_posix())

    assert offenders == FROZEN_DIRECT_CUPY_MODULES, (
        "Direct CuPy usage changed. Either move it into backend.py or update "
        "FROZEN_DIRECT_CUPY_MODULES."
    )


# ---------------------------------------------------------------------------
# Shipped presets
# ---------------------------------------------------------------------------

LEGACY_BACKEND_PRESETS = {
    "default_parameters_debug.json": "cupyRAM",
    "default_parameters_debug_angularsp.json": "cupyRAM",
    "default_parameters_debug_of_choroid.json": "cupy",
}

STALE_PIPELINE_PRESETS = {
    "default_parameters_debug_angularsp.json": "main",
    "default_parameters_debug_of_choroid.json": "main",
    "default_parameters_simple_numpy.yaml": "simple_numpy",
    "default_parameters_sliding.yaml": "sliding",
}


def _read_preset(name: str) -> dict:
    path = DEFAULTS_DIR / name
    text = path.read_text(encoding="utf-8")

    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)

    return json.loads(text)


@pytest.mark.parametrize(
    "name, value", sorted(LEGACY_BACKEND_PRESETS.items())
)
def test_shipped_presets_still_use_legacy_backend_names(name: str, value: str) -> None:
    """Untouched by design: repairs here would change shipped GUI behaviour."""
    assert _read_preset(name)["backend"] == value

    # Accepted, and interpreted strictly as "use the GPU".
    assert backend.resolve_mode(value) is backend.BackendMode.GPU


@pytest.mark.parametrize("name, stale_name", sorted(STALE_PIPELINE_PRESETS.items()))
def test_shipped_presets_reference_unregistered_pipelines(
    name: str, stale_name: str
) -> None:
    """Four bundled presets name pipelines that do not exist."""
    assert _read_preset(name)["pipeline_name"] == stale_name
    assert stale_name not in pipelines, (
        f"{stale_name!r} became a registered pipeline; update or remove this pin"
    )


def test_pipeline_registry_keeps_dead_alias_configuration() -> None:
    """The registry still maps a module that was removed."""
    from holodoppler.pipelines import _PIPELINE_ALIASES, _PIPELINE_FUNCTIONS

    dead_module = "main_pipeline_xp_on_ram_dp"

    assert dead_module in _PIPELINE_ALIASES
    assert dead_module in _PIPELINE_FUNCTIONS
    assert not (PIPELINES_DIR / f"{dead_module}.py").exists()
    assert _PIPELINE_ALIASES[dead_module] == "main"
    assert "main" not in pipelines


# ---------------------------------------------------------------------------
# Packaging
# ---------------------------------------------------------------------------

def test_fresnel_zero_padding_path_is_frozen_broken() -> None:
    """The padded Fresnel branch cannot work, and fixing it is out of scope.

    ``fresnel_transform`` builds the input kernel at the *unpadded* size and
    only then pads the frames, so the multiply cannot broadcast. The
    ``pad_array_centrally`` signature mismatch that previously masked this as a
    ``TypeError`` is fixed, but reordering the kernel construction would change
    numerical behaviour and is therefore left for a dedicated PR.
    """
    frames = np.random.default_rng(5).random((2, 8, 8)).astype(np.complex64)

    with pytest.raises(ValueError):
        fresnel_transform(
            np,
            np.fft,
            frames,
            0.1,
            (2e-5, 2e-5),
            852e-9,
            zero_padding=16,
        )


def test_cupy_is_still_a_hard_dependency_in_packaging_metadata() -> None:
    """This PR makes the *code* CuPy-optional; packaging is a follow-up."""
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "cupy" in pyproject
