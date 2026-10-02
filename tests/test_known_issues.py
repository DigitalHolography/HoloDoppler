"""Pins for known problems that this cleanup deliberately does not fix.

These tests assert the *current, broken or stale* state on purpose. If someone
repairs one of these areas, the corresponding pin starts failing, which is the
signal to update or delete it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

import numpy as np

import holodoppler.backend as backend
from holodoppler.core.propagation import fresnel_transform
from holodoppler.pipelines import PIPELINES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = PROJECT_ROOT / "holodoppler"
DEFAULTS_DIR = PACKAGE_DIR / "defaults"


# ---------------------------------------------------------------------------
# CuPy isolation
# ---------------------------------------------------------------------------

def test_cupy_is_confined_to_the_backend_module() -> None:
    """``backend.py`` is the only module allowed to know about CuPy."""
    pattern = re.compile(r"^\s*(?:import|from)\s+cupyx?\b", re.MULTILINE)

    offenders = set()

    for path in sorted(PACKAGE_DIR.rglob("*.py")):
        if path.name == "backend.py":
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            offenders.add(path.relative_to(PACKAGE_DIR).as_posix())

    assert offenders == set(), (
        "CuPy must only be imported by holodoppler/backend.py, but found: "
        f"{sorted(offenders)}"
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


@pytest.mark.parametrize("name, value", sorted(LEGACY_BACKEND_PRESETS.items()))
def test_shipped_presets_still_use_legacy_backend_names(name: str, value: str) -> None:
    """Untouched by design: repairing these would change shipped preset behaviour."""
    assert _read_preset(name)["backend"] == value

    # Accepted, and interpreted strictly as "use the GPU".
    assert backend.resolve_mode(value) is backend.BackendMode.GPU


@pytest.mark.parametrize("name, stale_name", sorted(STALE_PIPELINE_PRESETS.items()))
def test_shipped_presets_reference_unregistered_pipelines(
    name: str, stale_name: str
) -> None:
    """Four bundled presets name pipelines that do not exist."""
    assert _read_preset(name)["pipeline_name"] == stale_name
    assert stale_name not in PIPELINES, (
        f"{stale_name!r} became a registered pipeline; update or remove this pin"
    )


# ---------------------------------------------------------------------------
# Numerical
# ---------------------------------------------------------------------------

def test_fresnel_zero_padding_path_is_frozen_broken() -> None:
    """The padded Fresnel branch cannot work, and fixing it is out of scope.

    ``fresnel_transform`` builds the input kernel at the *unpadded* size and
    only then pads the frames, so the multiply cannot broadcast. The
    ``pad_array_centrally`` signature mismatch that previously masked this as a
    ``TypeError`` is fixed, but reordering the kernel construction would change
    numerical behaviour and is therefore left alone.
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


# ---------------------------------------------------------------------------
# Packaging
# ---------------------------------------------------------------------------

def test_cupy_is_still_a_hard_dependency_in_packaging_metadata() -> None:
    """The code no longer requires CuPy; the packaging metadata still does.

    Packaging is deliberately frozen for now. When it is updated, this pin
    should be replaced by a test asserting the optional extra exists.
    """
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "cupy" in pyproject
