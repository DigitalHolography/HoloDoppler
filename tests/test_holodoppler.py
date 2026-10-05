from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import h5py
import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_SCRIPT = PROJECT_ROOT / "scripts" / "make_synthetic_test_data.py"

TEST_ROOT = PROJECT_ROOT / "temp"
HOLO_PATH = TEST_ROOT / "test.holo"
PARAMS_PATH = TEST_ROOT / "tmp.yaml"
OUTPUT_PATH = TEST_ROOT / "test" / "test_HD" / "h5" / "test_HD_output.h5"


def _create_params_file() -> None:
    """Create the minimal processing parameter file used by the CLI test.

    Keep this aligned with the actual holodoppler process parameter schema.
    """
    PARAMS_PATH.parent.mkdir(parents=True, exist_ok=True)

    params = {
        "pipeline_name": "simple",
        # optional backend management
        "use_parallel": True,  # use parallel workers cores or not (cupy or numpy)
        "numpy_num_workers": 8,  # in numpy mode, the number of parallel workers to be used
        # Core parameters
        "batch_size": 64,
        "first_frame": 0,
        "batch_stride": 64,
        "end_frame": -1,  # -1 means process all frames
        # Propagation parameters
        "spatial_propagation": "Fresnel",  # Options: "Fresnel" or "AngularSpectrum"
        "z": "use_holovibes",  # Propagation distance in meters
        "wavelength": 852.0e-9,  # Wavelength in meters
        "pixel_pitch": "use_holovibes",  # Pixel pitch in meters [y, x]
        # Fresnel specific
        "Fresnel_use_ouput_kernel": False,  # Use output kernel for Fresnel transform
        # Filtering 2D frequencies
        "filter2d": False,
        "filter2d_low": 0.03,
        # SVD filtering
        "svd_threshold": 2,
        "svd_filter_mode": "number_of_values",  # Options: "number_of_values", "amplitude_threshold"
        "svd_remove_dc": True,
        # Temporal transformation
        "temporal_transformation": "FourierTransform",  # Options: "FourierTransform" or None
        "sampling_freq": "use_holovibes",  # Sampling frequency in Hz
        "low_freq": 6000,  # Low frequency cutoff in Hz
        "high_freq": 18300,  # High frequency cutoff in Hz "use_holovibes" sampling_freq/2
        # Frequency bands for different cutoffs of the psd in Hz. It will give the average of the psd in the symmetric frequency range
        "frequency_bands": [
            [3000, 9000],
            [9000, 18000],
        ],
        # Image registration
        "registration_flatfield_gw": 35.0,  # Gaussian width for flatfield normalization
        # Image registration Live
        "image_registration": False,
        "registration_ref_first_frame": 0,
        "registration_ref_batch_size": 512,
        "registration_radius": 0.8,
        "registration_sub_pixel": True,
        # Advanced Image registration
        "image_registration_with_ecc": True,  # uses the first computed frame as reference
        "registration_ecc_radius": 0.8,
        "registration_ecc_min_threshold": 0.7,
        # Corner compensation
        "corner_compensation": False,
        # Image resizing
        "square": True,
        # Image contrast
        "contrast": False,
        "contrast_low_max_percent": [
            0.5,
            99.5,
        ],  # Applied only to rendered avi/png/report outputs, not raw h5.
        "contrast_gamma": 1.0,
        # Shack-Hartmann wavefront sensing
        "shack_hartmann_autofocus": True,  # Enable Shack-Hartmann processing only on the batch defined by registration_ref_first_frame and batch_size and use it for the correction of following batch
        "shack_hartmann": False,  # Enable Live (every batch) Shack-Hartmann processing
        "shack_hartmann_nx_subap": 5,  # Number of subapertures in X
        "shack_hartmann_ny_subap": 5,  # Number of subapertures in Y
        "shack_hartmann_svd_threshold": 10,
        "shack_hartmann_pupil_threshold": 1.5,  # Rejection of the side sub images if they are too
        "shack_hartmann_deviation_threshold": 10.0,  # Max displacement accepted in number of the std
        "shack_hartmann_shifts_pixel_range_threshold": 1000.0,  # Max displacement accepted in pixels
        "shack_hartmann_graph_laplacian": True,  # Use graph Laplacian method
        "shack_hartmann_zernike_fit": True,  # Other option is shack_hartmann_southwell_integration but not really implemented yet because it is not stable
        "shack_hartmann_zernike_fit_modes": [
            4,
            5,
            6,
        ],  # Number of the Zernike modes to use in the fit in Null ordering
    }

    with PARAMS_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(params, f, sort_keys=False)


def _create_synthetic_holo() -> None:
    """Create test.holo using the repository's synthetic-data generator."""
    if not SYNTHETIC_SCRIPT.exists():
        pytest.fail(
            f"Missing synthetic test-data generator: {SYNTHETIC_SCRIPT}"
        )

    result = subprocess.run(
        [
            sys.executable,
            str(SYNTHETIC_SCRIPT),
            str(TEST_ROOT),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        "Failed to create synthetic test data.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    assert HOLO_PATH.exists(), (
        f"Synthetic-data script completed successfully, "
        f"but {HOLO_PATH} was not created."
    )


@pytest.fixture(scope="session")
def cli_test_data() -> tuple[Path, Path]:
    """Prepare isolated input files for the CLI integration test."""
    TEST_ROOT.mkdir(parents=True, exist_ok=True)

    _create_synthetic_holo()
    _create_params_file()

    return HOLO_PATH, PARAMS_PATH


def test_process_cli_creates_expected_h5(cli_test_data: tuple[Path, Path]) -> None:
    """Test:

        holodoppler process "test.holo" "params.yaml"

    and verify that the expected HDF5 datasets are produced.
    """
    holo_path, params_path = cli_test_data

    # Remove an old result so a stale HDF5 file cannot make the test pass.
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()

    # The command intentionally uses the same relative paths as a user would
    # use from the temporary test directory.
    result = subprocess.run(
        [
            "holodoppler",
            "process",
            holo_path.name,
            params_path.name,
        ],
        cwd=TEST_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        "holodoppler process failed.\n"
        f"command: holodoppler process "
        f'"{holo_path.name}" "{params_path.name}"\n\n'
        f"stdout:\n{result.stdout}\n\n"
        f"stderr:\n{result.stderr}"
    )

    assert OUTPUT_PATH.exists(), (
        "holodoppler process completed successfully, "
        f"but expected output was not created:\n{OUTPUT_PATH}\n\n"
        f"stdout:\n{result.stdout}\n\n"
        f"stderr:\n{result.stderr}"
    )

    with h5py.File(OUTPUT_PATH, "r") as h5:
        required_datasets = (
            "/moment0",
            "/moment1",
            "/moment2",
        )

        for dataset_path in required_datasets:
            assert dataset_path in h5, (
                f"Missing required dataset {dataset_path} "
                f"in {OUTPUT_PATH}. "
                f"Available top-level entries: {list(h5.keys())}"
            )

            dataset = h5[dataset_path]

            assert dataset.size > 0, (
                f"Dataset {dataset_path} exists but is empty."
            )
