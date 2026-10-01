"""Every registered pipeline runs end to end through the runner.

The registry advertises three pipelines, so each one is executed here. Without
this, a pipeline could be registered, listed in the UI and accepted by the CLI
while being unable to run at all.

The shipped presets target a full acquisition (thousands of frames). The
synthetic fixture is 64 frames of 32x32, so a few settings have to be brought
within it. Nothing else is changed:

* ``batch_size``/``batch_stride`` must fit in the fixture, otherwise the
  pipelines compute zero batches and return before writing anything;
* ``registration_ref_batch_size`` must fit as well;
* ``image_registration_with_ecc`` is disabled because the ECC path uses
  ``ProcessPoolExecutor``, which needs OS pipes that some sandboxes deny.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from holodoppler.config import load_config
from holodoppler.execution.runner import run_pipeline
from holodoppler.pipelines import names


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARAMETERS_DIR = PROJECT_ROOT / "parameters"

#: pipeline name -> the preset that is shipped for it.
PRESETS = {
    "simple": "default_parameters_simple.yaml",
    "sliding_shack_hartmann": "default_parameters_sliding_shack_hart.yaml",
    "sh_avg": "default_parameters_sh_avg.yaml",
}

FIXTURE_SIZE = 64

COMMON_OVERRIDES = {
    "batch_size": FIXTURE_SIZE,
    "batch_stride": FIXTURE_SIZE,
    "registration_ref_batch_size": FIXTURE_SIZE,
    "image_registration_with_ecc": False,
}


def _fixture_parameters(name: str) -> dict:
    parameters = load_config(PARAMETERS_DIR / PRESETS[name])
    parameters.update(COMMON_OVERRIDES)
    return parameters


def test_every_registered_pipeline_has_a_preset() -> None:
    """A registered pipeline with no preset cannot be run or reviewed."""
    assert set(names()) == set(PRESETS), (
        "the registry and the preset list disagree. "
        f"registry={sorted(names())} presets={sorted(PRESETS)}"
    )


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_pipeline_runs_and_writes_hdf5(holo_case, name: str) -> None:
    parameters = _fixture_parameters(name)

    run_pipeline(holo_case.holo, parameters)

    assert holo_case.h5_path.exists(), (
        f"the {name!r} pipeline reported success but wrote no HDF5 output"
    )
