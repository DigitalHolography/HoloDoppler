"""CLI tests: real argument parsing, real pipeline, real exit codes.

These tests execute the actual entry point in a subprocess so that argument
parsing, configuration loading, backend selection, reader selection, the
pipeline and the exit status are all covered together.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import holodoppler.backend as backend
from holodoppler.cli import _resolve_backend_mode


# The GPU-failure tests rely on CUDA being unusable. On a machine with a
# working GPU they would take the success path, so they are skipped there.
CUDA_USABLE = backend._cupy_state() == "usable"

requires_no_cuda = pytest.mark.skipif(
    CUDA_USABLE,
    reason="A working CUDA device is present; the GPU backend would succeed",
)


def _output_dir(input_path: Path) -> Path:
    return input_path.parent / input_path.stem / f"{input_path.stem}_HD"


def _h5_path(input_path: Path) -> Path:
    stem = f"{input_path.stem}_HD"
    return _output_dir(input_path) / "h5" / f"{stem}_output.h5"


def _normalized(text: str) -> str:
    """Collapse whitespace so wrapped argparse help stays matchable."""
    return " ".join(text.split())


def _report(result) -> str:
    return (
        f"command: {' '.join(result.args)}\n"
        f"exit code: {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

def test_process_help_documents_each_backend_mode(holo_case, run_cli) -> None:
    result = run_cli(["process", "--help"], cwd=holo_case.directory)

    assert result.returncode == 0, _report(result)

    help_text = _normalized(result.stdout)

    assert "{cpu,gpu,auto}" in help_text
    assert "use CPU only" in help_text
    assert "require a working CUDA/CuPy backend" in help_text
    assert "use GPU when available, otherwise CPU" in help_text


# ---------------------------------------------------------------------------
# Explicit CPU
# ---------------------------------------------------------------------------

def test_explicit_cpu_runs_and_writes_expected_datasets(holo_case, run_cli) -> None:
    result = run_cli(
        ["process", holo_case.holo, holo_case.params, "--backend", "cpu"],
        cwd=holo_case.directory,
    )

    assert result.returncode == 0, _report(result)
    assert "Process completed successfully" in result.stdout

    h5_path = _h5_path(holo_case.holo)
    assert h5_path.exists(), _report(result)

    import h5py

    with h5py.File(h5_path, "r") as h5:
        for name in ("moment0", "moment1", "moment2"):
            assert name in h5, f"missing {name}; got {sorted(h5.keys())}"
            assert h5[name].size > 0


def test_no_backend_flag_defaults_to_auto(holo_case, run_cli) -> None:
    result = run_cli(
        ["process", holo_case.holo, holo_case.params],
        cwd=holo_case.directory,
    )

    assert result.returncode == 0, _report(result)
    assert _h5_path(holo_case.holo).exists(), _report(result)


# ---------------------------------------------------------------------------
# Explicit GPU must fail loudly and write nothing
# ---------------------------------------------------------------------------

@requires_no_cuda
def test_explicit_gpu_fails_without_writing_output(holo_case, run_cli) -> None:
    output_dir = _output_dir(holo_case.holo)
    assert not output_dir.exists()

    result = run_cli(
        ["process", holo_case.holo, holo_case.params, "--backend", "gpu"],
        cwd=holo_case.directory,
    )

    assert result.returncode != 0, _report(result)
    assert "GPU backend requested" in result.stderr, _report(result)
    assert "Use --backend cpu or --backend auto" in result.stderr, _report(result)

    # The whole point: no silent GPU -> CPU fallback, and no claimed success.
    assert "Process completed successfully" not in result.stdout
    assert not output_dir.exists(), (
        "GPU mode must fail before any output is written; "
        f"found {output_dir}"
    )


@requires_no_cuda
def test_legacy_cupy_ram_is_treated_as_gpu(holo_case, run_cli) -> None:
    result = run_cli(
        ["process", holo_case.holo, holo_case.params, "--backend", "cupyRAM"],
        cwd=holo_case.directory,
    )

    assert result.returncode != 0, _report(result)
    assert "GPU backend requested" in result.stderr, _report(result)
    assert not _output_dir(holo_case.holo).exists()


def test_unknown_backend_is_rejected(holo_case, run_cli) -> None:
    result = run_cli(
        ["process", holo_case.holo, holo_case.params, "--backend", "bogus"],
        cwd=holo_case.directory,
    )

    assert result.returncode != 0, _report(result)
    assert "Unknown backend" in result.stderr, _report(result)
    assert not _output_dir(holo_case.holo).exists()


# ---------------------------------------------------------------------------
# Batch exit status
# ---------------------------------------------------------------------------

@pytest.fixture
def batch_case(holo_case):
    """Provide two good inputs, one missing input and a batch writer."""
    good1 = holo_case.directory / "good1.holo"
    good2 = holo_case.directory / "good2.holo"
    shutil.copyfile(holo_case.holo, good1)
    shutil.copyfile(holo_case.holo, good2)

    missing = holo_case.directory / "missing.holo"

    def write_batch(name: str, entries) -> Path:
        batch_file = holo_case.directory / name
        batch_file.write_text(
            "\n".join(str(entry) for entry in entries) + "\n",
            encoding="utf-8",
        )
        return batch_file

    return {
        "case": holo_case,
        "good1": good1,
        "good2": good2,
        "missing": missing,
        "write_batch": write_batch,
    }


def test_batch_all_success_returns_zero(batch_case, run_cli) -> None:
    batch = batch_case["write_batch"](
        "all_good.txt", [batch_case["good1"], batch_case["good2"]]
    )

    result = run_cli(
        ["process", "--batch", batch, batch_case["case"].params],
        cwd=batch_case["case"].directory,
    )

    assert result.returncode == 0, _report(result)
    assert _h5_path(batch_case["good1"]).exists()
    assert _h5_path(batch_case["good2"]).exists()


def test_batch_with_one_missing_entry_returns_nonzero_and_keeps_going(
    batch_case, run_cli
) -> None:
    batch = batch_case["write_batch"](
        "mixed.txt",
        [batch_case["good1"], batch_case["missing"], batch_case["good2"]],
    )

    result = run_cli(
        ["process", "--batch", batch, batch_case["case"].params],
        cwd=batch_case["case"].directory,
    )

    assert result.returncode != 0, _report(result)

    # Jobs listed after the failure must still have been attempted.
    assert _h5_path(batch_case["good1"]).exists(), _report(result)
    assert _h5_path(batch_case["good2"]).exists(), _report(result)

    assert "1/3 jobs failed" in result.stdout, _report(result)


def test_batch_all_failures_returns_nonzero(batch_case, run_cli) -> None:
    broken = batch_case["case"].directory / "broken.holo"
    broken.write_bytes(b"HOLO")

    batch = batch_case["write_batch"](
        "all_bad.txt", [batch_case["missing"], broken]
    )

    result = run_cli(
        ["process", "--batch", batch, batch_case["case"].params],
        cwd=batch_case["case"].directory,
    )

    assert result.returncode != 0, _report(result)
    assert "Failed:      2" in result.stdout, _report(result)


def test_batch_of_only_missing_entries_returns_nonzero(batch_case, run_cli) -> None:
    batch = batch_case["write_batch"]("missing.txt", [batch_case["missing"]])

    result = run_cli(
        ["process", "--batch", batch, batch_case["case"].params],
        cwd=batch_case["case"].directory,
    )

    assert result.returncode != 0, _report(result)
    assert "does not exist" in result.stderr, _report(result)


def test_empty_batch_file_returns_nonzero(batch_case, run_cli) -> None:
    batch = batch_case["write_batch"]("empty.txt", [])
    # Only comments: still no jobs.
    batch.write_text("# nothing here\n", encoding="utf-8")

    result = run_cli(
        ["process", "--batch", batch, batch_case["case"].params],
        cwd=batch_case["case"].directory,
    )

    assert result.returncode != 0, _report(result)
    assert "No valid file paths found" in result.stderr, _report(result)


# ---------------------------------------------------------------------------
# Backend resolution used by the CLI boundary
# ---------------------------------------------------------------------------

def test_absent_backend_resolves_to_auto() -> None:
    assert _resolve_backend_mode({}) == "auto"
    assert _resolve_backend_mode({"backend": "auto"}) == "auto"


@pytest.mark.parametrize(
    "value, expected",
    [
        ("cpu", "cpu"),
        ("numpy", "cpu"),
        ("gpu", "gpu"),
        ("cupy", "gpu"),
        ("cupyRAM", "gpu"),
        ("auto", "auto"),
    ],
)
def test_backend_parameter_values_resolve(value: str, expected: str) -> None:
    assert _resolve_backend_mode({"backend": value}) == expected


def test_force_numpy_takes_precedence_over_backend() -> None:
    assert _resolve_backend_mode({"backend": "gpu", "force_numpy": True}) == "cpu"
    assert _resolve_backend_mode({"force_numpy": True}) == "cpu"


def test_unknown_backend_parameter_raises() -> None:
    with pytest.raises(ValueError):
        _resolve_backend_mode({"backend": "nonsense"})
