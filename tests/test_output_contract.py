"""Golden output contract for the ``simple`` pipeline.

This is the regression net for the package reorganisation: the pipeline's
documents are treated as a frozen contract. If a refactor drops, renames or
mistypes an output, this test fails instead of silently shipping a different
HDF5 file.

To update intentionally, run the pipeline and copy the observed inventory into
the constants below.
"""

from __future__ import annotations

import h5py
import numpy as np


# Numerical datasets: name -> expected (dtype, shape).
GOLDEN_ARRAY_DATASETS: dict[str, tuple[np.dtype, tuple[int, ...]]] = {
    # Moments.
    "moment0": (np.dtype(np.float32), (1, 32, 32)),
    "moment0ff": (np.dtype(np.float32), (1, 32, 32)),
    "moment1": (np.dtype(np.float32), (1, 32, 32)),
    "moment2": (np.dtype(np.float32), (1, 32, 32)),
    # Frequency bands, derived from ``frequency_bands`` in the parameters.
    "band_0_3000_9000": (np.dtype(np.float32), (1, 32, 32)),
    "band_1_9000_18000": (np.dtype(np.float32), (1, 32, 32)),
    # Spectral output: one row per batch, one column per frequency bin.
    "spectrum_line": (np.dtype(np.float32), (1, 64)),
    # Shack-Hartmann autofocus coefficients (3 Zernike modes).
    "shack_hartmann_autofocus_zernike_coefs": (np.dtype(np.float32), (3,)),
}

# Metadata datasets stored as strings. Their *contents* are environment
# dependent (git hash, version), so only their presence is asserted.
GOLDEN_STRING_DATASETS = frozenset(
    {
        "HD_parameters",
        "HD_version",
        "git_commit",
    }
)

GOLDEN_ATTRIBUTES = frozenset({"git_commit", "version"})

# Every artifact the pipeline is expected to produce, relative to the
# ``<stem>_HD`` output directory.
GOLDEN_ARTIFACTS = frozenset(
    {
        "avi/band_0_3000_9000.avi",
        "avi/band_1_9000_18000.avi",
        "avi/moment0.avi",
        "avi/moment0ff.avi",
        "avi/moment1.avi",
        "avi/moment2.avi",
        "csv/shack_hartmann_autofocus_zernike_coefs.csv",
        "git_version.txt",
        "h5/test_HD_output.h5",
        "json/holovibes_footer.json",
        "json/holovibes_header.json",
        "json/parameters_holodoppler.json",
        "png/band_0_3000_9000.png",
        "png/band_1_9000_18000.png",
        "png/moment0.png",
        "png/moment0ff.png",
        "png/moment1.png",
        "png/moment2.png",
        "png/spectrum_line.png",
        "version.txt",
    }
)


def test_simple_pipeline_produces_the_golden_artifact_set(holo_case, run_cli) -> None:
    result = run_cli(
        ["process", holo_case.holo.name, holo_case.params.name],
        cwd=holo_case.directory,
    )

    assert result.returncode == 0, (
        f"pipeline failed\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )

    assert holo_case.output_dir.is_dir(), (
        f"expected output directory was not created: {holo_case.output_dir}"
    )

    produced = {
        path.relative_to(holo_case.output_dir).as_posix()
        for path in holo_case.output_dir.rglob("*")
        if path.is_file()
    }

    missing = GOLDEN_ARTIFACTS - produced
    unexpected = produced - GOLDEN_ARTIFACTS

    assert not missing, f"pipeline no longer produces: {sorted(missing)}"
    assert not unexpected, f"pipeline produced unexpected artifacts: {sorted(unexpected)}"


def test_simple_pipeline_produces_the_golden_hdf5_contract(holo_case, run_cli) -> None:
    result = run_cli(
        ["process", holo_case.holo.name, holo_case.params.name],
        cwd=holo_case.directory,
    )

    assert result.returncode == 0, (
        f"pipeline failed\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )

    assert holo_case.h5_path.exists(), f"missing HDF5 output: {holo_case.h5_path}"

    with h5py.File(holo_case.h5_path, "r") as h5:
        string_names = {
            name for name in h5 if h5[name].dtype.kind in {"S", "O", "U"}
        }
        array_names = set(h5.keys()) - string_names

        assert string_names == set(GOLDEN_STRING_DATASETS), (
            "metadata dataset set changed.\n"
            f"missing: {sorted(set(GOLDEN_STRING_DATASETS) - string_names)}\n"
            f"unexpected: {sorted(string_names - set(GOLDEN_STRING_DATASETS))}"
        )

        assert array_names == set(GOLDEN_ARRAY_DATASETS), (
            "numerical dataset set changed.\n"
            f"missing: {sorted(set(GOLDEN_ARRAY_DATASETS) - array_names)}\n"
            f"unexpected: {sorted(array_names - set(GOLDEN_ARRAY_DATASETS))}"
        )

        for name, (dtype, shape) in GOLDEN_ARRAY_DATASETS.items():
            dataset = h5[name]
            assert dataset.dtype == dtype, (
                f"{name}: dtype changed from {dtype} to {dataset.dtype}"
            )
            assert dataset.shape == shape, (
                f"{name}: shape changed from {shape} to {dataset.shape}"
            )

        for attribute in GOLDEN_ATTRIBUTES:
            assert attribute in h5.attrs, f"missing HDF5 attribute {attribute!r}"
