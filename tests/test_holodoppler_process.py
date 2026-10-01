"""End-to-end smoke test for the ``holodoppler process`` CLI.

This runs the real console entry point against synthetic data, through
``python -m holodoppler`` so it does not depend on the console script being on
``PATH``, and verifies that the expected HDF5 datasets are produced.

The parameter file used by the ``holo_case`` fixture disables the
multiprocessing-based ECC registration, which needs OS-level pipes. Everything
else in the pipeline is exercised unchanged.
"""

from __future__ import annotations

import h5py


def test_process_cli_creates_expected_h5(holo_case, run_cli) -> None:
    """Run ``holodoppler process "test.holo" "params.yaml"`` end to end."""
    # Each test gets its own directory, so a stale output file cannot make this
    # test pass.
    assert not holo_case.h5_path.exists()

    # Use the same relative paths a user would use from the input directory.
    result = run_cli(
        ["process", holo_case.holo.name, holo_case.params.name],
        cwd=holo_case.directory,
    )

    assert result.returncode == 0, (
        f"holodoppler process failed.\n"
        f"command: holodoppler process \"{holo_case.holo.name}\" "
        f"\"{holo_case.params.name}\"\n\n"
        f"stdout:\n{result.stdout}\n\n"
        f"stderr:\n{result.stderr}"
    )

    assert holo_case.h5_path.exists(), (
        "holodoppler process completed successfully, but the expected output "
        f"was not created:\n{holo_case.h5_path}\n\n"
        f"stdout:\n{result.stdout}\n\n"
        f"stderr:\n{result.stderr}"
    )

    with h5py.File(holo_case.h5_path, "r") as h5:
        required_datasets = (
            "/moment0",
            "/moment1",
            "/moment2",
        )

        for dataset_path in required_datasets:
            assert dataset_path in h5, (
                f"Missing required dataset {dataset_path} "
                f"in {holo_case.h5_path}. "
                f"Available top-level entries: {list(h5.keys())}"
            )

            dataset = h5[dataset_path]

            assert dataset.size > 0, (
                f"Dataset {dataset_path} exists but is empty."
            )
