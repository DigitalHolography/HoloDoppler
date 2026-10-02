"""Shared fixtures for the HoloDoppler test suite.

The suite deliberately avoids the multiprocessing-based ECC registration path:
``register_with_ecc`` uses ``ProcessPoolExecutor``, which needs OS-level pipes
that are unavailable in some sandboxed environments. The processing tests
therefore disable ECC and rely on everything else in the pipeline.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterable

import pytest
import yaml
import h5py


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = PROJECT_ROOT / "tests"
TEMP_ROOT = PROJECT_ROOT / "temp"
CASES_ROOT = TEMP_ROOT / "cases"
PARAMETERS_DIR = PROJECT_ROOT / "parameters"
DEFAULTS_DIR = PROJECT_ROOT / "holodoppler" / "defaults"
SYNTHETIC_SCRIPT = PROJECT_ROOT / "scripts" / "make_synthetic_test_data.py"


# ---------------------------------------------------------------------------
# Processing parameters
# ---------------------------------------------------------------------------
#
# Mirrors parameters/default_parameters_simple.yaml as used by the CLI, with
# the two switches that make a test run deterministic and sandbox-friendly:
#
#   image_registration_with_ecc: False   avoids ProcessPoolExecutor
#   use_parallel:                False   avoids thread-pool timing jitter
#
# Nothing else is changed, so the pipeline exercises its real code paths.

BASE_PARAMETERS: dict[str, Any] = {
    "pipeline_name": "simple",
    "use_parallel": False,
    "numpy_num_workers": 8,
    "batch_size": 64,
    "first_frame": 0,
    "batch_stride": 64,
    "end_frame": -1,
    "spatial_propagation": "Fresnel",
    "z": "use_holovibes",
    "wavelength": 852.0e-9,
    "pixel_pitch": "use_holovibes",
    "Fresnel_use_ouput_kernel": False,
    "filter2d": False,
    "filter2d_low": 0.03,
    "svd_threshold": 2,
    "svd_filter_mode": "number_of_values",
    "svd_remove_dc": True,
    "temporal_transformation": "FourierTransform",
    "sampling_freq": "use_holovibes",
    "low_freq": 6000,
    "high_freq": 18300,
    "frequency_bands": [[3000, 9000], [9000, 18000]],
    "registration_flatfield_gw": 35.0,
    "image_registration": False,
    "registration_ref_first_frame": 0,
    "registration_ref_batch_size": 512,
    "registration_radius": 0.8,
    "registration_sub_pixel": True,
    "image_registration_with_ecc": False,
    "registration_ecc_radius": 0.8,
    "registration_ecc_min_threshold": 0.7,
    "corner_compensation": False,
    "square": True,
    "contrast": False,
    "contrast_low_max_percent": [0.5, 99.5],
    "contrast_gamma": 1.0,
    "shack_hartmann_autofocus": True,
    "shack_hartmann": False,
    "shack_hartmann_nx_subap": 5,
    "shack_hartmann_ny_subap": 5,
    "shack_hartmann_svd_threshold": 10,
    "shack_hartmann_pupil_threshold": 1.5,
    "shack_hartmann_deviation_threshold": 10.0,
    "shack_hartmann_shifts_pixel_range_threshold": 1000.0,
    "shack_hartmann_graph_laplacian": True,
    "shack_hartmann_zernike_fit": True,
    "shack_hartmann_zernike_fit_modes": [4, 5, 6],
}


def write_parameters(path: Path, **overrides: Any) -> Path:
    """Write a parameter file based on :data:`BASE_PARAMETERS`."""
    parameters = dict(BASE_PARAMETERS)
    parameters.update(overrides)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(parameters, sort_keys=False),
        encoding="utf-8",
    )

    return path


def output_directory_for(input_path: Path) -> Path:
    """Return the output directory the pipeline derives from ``input_path``."""
    return input_path.parent / input_path.stem / f"{input_path.stem}_HD"


def h5_output_path_for(input_path: Path) -> Path:
    """Return the HDF5 file the pipeline derives from ``input_path``.

    The pipeline names the file after the *output directory*
    (``{stem}_HD//h5/{stem}_HD_output.h5``).
    """
    stem = f"{input_path.stem}_HD"
    return output_directory_for(input_path) / "h5" / f"{stem}_output.h5"


# ---------------------------------------------------------------------------
# Synthetic data
# ---------------------------------------------------------------------------

def _load_synthetic_generator():
    """Import ``scripts/make_synthetic_test_data.py`` as a module."""
    if not SYNTHETIC_SCRIPT.exists():
        raise FileNotFoundError(
            f"Missing synthetic test-data generator: {SYNTHETIC_SCRIPT}"
        )

    spec = importlib.util.spec_from_file_location(
        "make_synthetic_test_data",
        SYNTHETIC_SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def create_synthetic_holo(target_dir: Path) -> Path:
    """Create ``test.holo`` inside ``target_dir`` using the repository generator."""
    target_dir.mkdir(parents=True, exist_ok=True)

    generator = _load_synthetic_generator()
    holo_path = generator.make_test_data(target_dir)

    if not Path(holo_path).exists():
        raise AssertionError(
            f"Synthetic-data generator did not create {holo_path}"
        )

    return Path(holo_path)


def _case_name(request: pytest.FixtureRequest) -> str:
    """Build a filesystem-safe directory name from a test node id."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", request.node.name)


def _fresh_case_dir(request: pytest.FixtureRequest) -> Path:
    """Return a clean, writable per-test directory inside the workspace.

    The directory is wiped once per test so the suite is re-runnable and a file
    produced by an earlier run can never make an assertion pass.
    """
    cached = getattr(request.node, "_holodoppler_case_dir", None)
    if cached is not None:
        return cached

    directory = CASES_ROOT / _case_name(request)

    if directory.exists():
        shutil.rmtree(directory, ignore_errors=True)

    directory.mkdir(parents=True, exist_ok=True)
    request.node._holodoppler_case_dir = directory

    return directory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def case_dir(request: pytest.FixtureRequest) -> Path:
    """A writable per-test directory inside the workspace.

    The workspace copy is used instead of pytest's ``tmp_path`` so that the
    suite also runs under sandboxes that only permit writes inside the project.
    """
    return _fresh_case_dir(request)


@pytest.fixture
def holo_case(request: pytest.FixtureRequest) -> SimpleNamespace:
    """Provide an isolated ``test.holo`` and parameter file for one test.

    Returns an object with ``directory``, ``holo``, ``params``, ``output_dir``
    and ``h5_path`` attributes.
    """
    directory = _fresh_case_dir(request)

    holo_path = create_synthetic_holo(directory)
    params_path = write_parameters(directory / "params.yaml")

    return SimpleNamespace(
        directory=directory,
        holo=holo_path,
        params=params_path,
        output_dir=output_directory_for(holo_path),
        h5_path=h5_output_path_for(holo_path),
    )


@pytest.fixture
def run_cli() -> Callable[..., "subprocess.CompletedProcess[str]"]:
    """Run the real CLI entry point in a subprocess.

    Uses ``python -m holodoppler`` so the test does not depend on the console
    script being present on ``PATH``.
    """

    def _run(args: Iterable[Any], cwd: Path) -> "subprocess.CompletedProcess[str]":
        return subprocess.run(
            [sys.executable, "-m", "holodoppler", *(str(arg) for arg in args)],
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )

    return _run

