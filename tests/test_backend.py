"""Backend contract tests.

``cpu`` must be CPU-only, ``gpu`` must fail loudly when CUDA is unusable, and
``auto`` is the only mode allowed to fall back to NumPy.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import holodoppler.backend as backend
from holodoppler.core.arrays import (
    elliptical_mask,
    pad_array_centrally,
    stretchlimcp,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class _FakeCupyModule:
    """Hashable NumPy-backed stand-in for the ``cupy`` module.

    Real array modules are hashable, so the stub must be too: backend identity
    participates in cache keys.
    """

    def __init__(self) -> None:
        self.zeros = np.zeros
        self.ogrid = np.ogrid
        self.asarray = np.asarray
        self.asnumpy = np.asarray
        self.ndarray = np.ndarray
        self.float32 = np.float32
        self.float64 = np.float64
        self.newaxis = None
        self.pi = np.pi
        self.nan = np.nan


def _stub_modules() -> "backend._CupyModules":
    """A NumPy-backed stand-in for the CuPy module bundle."""
    return backend._CupyModules(
        cp=_FakeCupyModule(),
        fft=np.fft,
        ndi=np,
        gaussian_filter=np.zeros,
        zoom=np.zeros,
        linalg=np.linalg,
    )


@pytest.fixture
def backend_env(monkeypatch: pytest.MonkeyPatch):
    """Return a callable that installs a simulated CuPy state.

    ``state`` is ``"absent"``, ``"unusable"`` or ``"usable"``.
    """

    def configure(state: str) -> SimpleNamespace:
        modules = _stub_modules()

        monkeypatch.setattr(backend, "_backend", None)
        monkeypatch.setattr(backend, "_cupy_state", lambda: state)
        monkeypatch.setattr(
            backend,
            "_cupy_report",
            lambda: (state, "simulated detail" if state == "unusable" else None),
        )

        if state == "usable":
            monkeypatch.setattr(backend, "_cupy_modules", lambda: modules)

        return modules.cp

    yield configure

    monkeypatch.setattr(backend, "_backend", None)


# ---------------------------------------------------------------------------
# Import behaviour
# ---------------------------------------------------------------------------

def _run_python(code: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )


def test_importing_backend_does_not_import_or_probe_cupy() -> None:
    """Importing the package must not pay for, or require, CuPy."""
    result = _run_python(
        "import sys\n"
        "import holodoppler.backend\n"
        "assert 'cupy' not in sys.modules, 'CuPy must be imported lazily'\n"
        "print('ok')\n"
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
    assert result.stderr == "", (
        "Importing the backend must not print anything; "
        f"got stderr: {result.stderr!r}"
    )


def test_cpu_mode_works_with_cupy_unavailable() -> None:
    """``cpu`` must never import CuPy, even implicitly."""
    result = _run_python(
        "import sys, types\n"
        "class Blocker:\n"
        "    def find_spec(self, fullname, path=None, target=None):\n"
        "        if fullname.split('.')[0] in {'cupy', 'cupyx'}:\n"
        "            raise ImportError('blocked: ' + fullname)\n"
        "        return None\n"
        "sys.meta_path.insert(0, Blocker())\n"
        "\n"
        "import numpy as np\n"
        "import holodoppler.backend as backend\n"
        "\n"
        "backend.set_backend('cpu')\n"
        "manager = backend.get_backend()\n"
        "assert manager.mode is backend.BackendMode.CPU\n"
        "assert manager.actual == 'numpy'\n"
        "assert backend.xp is np\n"
        "assert backend.is_gpu is False\n"
        "assert 'cupy' not in sys.modules\n"
        "print('ok')\n"
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


def test_gpu_mode_without_cupy_raises_a_backend_error() -> None:
    """A missing CuPy must surface as a backend error, not an ImportError."""
    result = _run_python(
        "import sys\n"
        "class Blocker:\n"
        "    def find_spec(self, fullname, path=None, target=None):\n"
        "        if fullname.split('.')[0] in {'cupy', 'cupyx'}:\n"
        "            raise ImportError('blocked: ' + fullname)\n"
        "        return None\n"
        "sys.meta_path.insert(0, Blocker())\n"
        "\n"
        "import holodoppler.backend as backend\n"
        "\n"
        "backend.set_backend('cpu')\n"
        "\n"
        "try:\n"
        "    backend.set_backend('gpu')\n"
        "except backend.BackendNotAvailableError as exc:\n"
        "    message = str(exc)\n"
        "    assert 'GPU backend requested' in message, message\n"
        "    assert '--backend cpu' in message, message\n"
        "else:\n"
        "    raise AssertionError('gpu mode must fail when CuPy is absent')\n"
        "\n"
        "backend.set_backend('auto')\n"
        "assert backend.get_backend().actual == 'numpy'\n"
        "print('ok')\n"
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


# ---------------------------------------------------------------------------
# Mode matrix
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "cupy_state, mode, expected_actual, should_raise",
    [
        # CPU is always available and never depends on CuPy.
        ("absent", "cpu", "numpy", False),
        ("unusable", "cpu", "numpy", False),
        ("usable", "cpu", "numpy", False),
        # AUTO is the only mode allowed to fall back.
        ("absent", "auto", "numpy", False),
        ("unusable", "auto", "numpy", False),
        ("usable", "auto", "cupy", False),
        # GPU must fail rather than silently using the CPU.
        ("absent", "gpu", None, True),
        ("unusable", "gpu", None, True),
        ("usable", "gpu", "cupy", False),
    ],
)
def test_mode_matrix(
    backend_env,
    cupy_state: str,
    mode: str,
    expected_actual: str | None,
    should_raise: bool,
) -> None:
    backend_env(cupy_state)

    if should_raise:
        with pytest.raises(backend.BackendNotAvailableError):
            backend.set_backend(mode)
        return

    manager = backend.set_backend(mode)

    assert manager.actual == expected_actual
    assert manager.requested.value == mode or mode == "auto"


def test_requested_and_actual_are_distinguishable(backend_env) -> None:
    """``auto`` falling back must not erase the requested mode."""
    backend_env("absent")

    manager = backend.set_backend("auto")

    assert manager.requested is backend.BackendMode.AUTO
    assert manager.mode is backend.BackendMode.AUTO
    assert manager.actual == "numpy"
    assert manager.is_numpy is True
    assert manager.is_gpu is False


def test_gpu_failure_message_is_actionable(backend_env) -> None:
    backend_env("unusable")

    with pytest.raises(backend.BackendNotAvailableError) as excinfo:
        backend.set_backend("gpu")

    message = str(excinfo.value)

    assert message == backend.GPU_UNAVAILABLE_MESSAGE
    assert "CuPy/CUDA could not be initialized" in message
    assert "Use --backend cpu or --backend auto" in message
    # The error is ours, not an import failure leaking through.
    assert isinstance(excinfo.value, backend.BackendError)
    assert not isinstance(excinfo.value, ModuleNotFoundError)


# ---------------------------------------------------------------------------
# Mode parsing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "value, expected",
    [
        (None, backend.BackendMode.AUTO),
        ("cpu", backend.BackendMode.CPU),
        ("CPU", backend.BackendMode.CPU),
        ("numpy", backend.BackendMode.CPU),
        ("np", backend.BackendMode.CPU),
        ("gpu", backend.BackendMode.GPU),
        ("cupy", backend.BackendMode.GPU),
        ("cp", backend.BackendMode.GPU),
        ("cupyRAM", backend.BackendMode.GPU),
        ("cupyram", backend.BackendMode.GPU),
        ("auto", backend.BackendMode.AUTO),
        (backend.BackendMode.GPU, backend.BackendMode.GPU),
    ],
)
def test_resolve_mode_accepts_canonical_and_legacy_values(value, expected) -> None:
    assert backend.resolve_mode(value) is expected


@pytest.mark.parametrize("value", ["", "bogus", "gpu2", "numpyRAM "])
def test_resolve_mode_rejects_unknown_values(value: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        backend.resolve_mode(value)

    assert "Unknown backend" in str(excinfo.value)
    assert "Use 'cpu', 'gpu' or 'auto'" in str(excinfo.value)


def test_legacy_cupy_ram_requires_a_real_gpu(backend_env) -> None:
    """``cupyRAM`` means "use the GPU", so it must fail without one."""
    backend_env("absent")

    with pytest.raises(backend.BackendNotAvailableError):
        backend.set_backend("cupyRAM")


# ---------------------------------------------------------------------------
# Selection semantics
# ---------------------------------------------------------------------------

def test_set_backend_is_idempotent_and_does_not_reprobe(backend_env) -> None:
    backend_env("usable")

    calls: list[int] = []
    real_state = backend._cupy_state

    def counting_state() -> str:
        calls.append(1)
        return real_state()

    backend._cupy_state = counting_state  # type: ignore[assignment]
    try:
        first = backend.set_backend("gpu")
        probes_after_first = len(calls)

        second = backend.set_backend("gpu")

        assert second is first
        assert len(calls) == probes_after_first
    finally:
        backend._cupy_state = real_state  # type: ignore[assignment]


def test_module_aliases_track_the_selected_backend(backend_env) -> None:
    """``backend.xp``/``backend.is_gpu`` must be live, not frozen snapshots."""
    backend_env("absent")

    backend.set_backend("cpu")
    assert backend.xp is np
    assert backend.is_gpu is False

    stub = backend_env("usable")
    backend.set_backend("gpu")
    assert backend.is_gpu is True
    assert backend.xp is stub

    backend_env("absent")
    backend.set_backend("cpu")
    assert backend.xp is np
    assert backend.is_gpu is False


def test_to_backend_and_to_numpy_round_trip_on_cpu(backend_env) -> None:
    backend_env("absent")
    backend.set_backend("cpu")

    converted = backend.to_backend([1, 2, 3])
    assert isinstance(converted, np.ndarray)

    restored = backend.to_numpy(converted)
    assert isinstance(restored, np.ndarray)
    np.testing.assert_array_equal(restored, [1, 2, 3])


def test_to_backend_and_to_numpy_round_trip_on_gpu(backend_env) -> None:
    backend_env("usable")
    backend.set_backend("gpu")

    converted = backend.to_backend([1, 2, 3])
    assert isinstance(converted, np.ndarray)

    restored = backend.to_numpy(converted)
    assert isinstance(restored, np.ndarray)
    np.testing.assert_array_equal(restored, [1, 2, 3])


# ---------------------------------------------------------------------------
# AUTO fallback messaging
# ---------------------------------------------------------------------------

def test_auto_is_silent_when_cupy_is_absent(backend_env, capsys) -> None:
    backend_env("absent")

    backend.set_backend("auto")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_auto_explains_a_degraded_cuda_runtime(backend_env, capsys) -> None:
    backend_env("unusable")

    backend.set_backend("auto")

    captured = capsys.readouterr()
    assert "not usable" in captured.err
    assert "simulated detail" in captured.err


# ---------------------------------------------------------------------------
# Backend-dependent caches
# ---------------------------------------------------------------------------

def test_cpu_mask_is_not_reused_after_switching_to_gpu(backend_env) -> None:
    elliptical_mask.cache_clear()

    backend_env("absent")
    backend.set_backend("cpu")
    cpu_mask = elliptical_mask(8, 8, 0.5)

    # The cache must still do its job within one backend.
    assert elliptical_mask(8, 8, 0.5) is cpu_mask

    backend_env("usable")
    backend.set_backend("gpu")
    gpu_mask = elliptical_mask(8, 8, 0.5)

    assert gpu_mask is not cpu_mask

    # Switching back must return the original CPU mask, not the GPU one.
    backend_env("absent")
    backend.set_backend("cpu")

    assert elliptical_mask(8, 8, 0.5) is cpu_mask

    elliptical_mask.cache_clear()


def test_gpu_mask_is_not_reused_after_switching_to_cpu(backend_env) -> None:
    elliptical_mask.cache_clear()

    backend_env("usable")
    backend.set_backend("gpu")
    gpu_mask = elliptical_mask(8, 8, 0.5)

    assert elliptical_mask(8, 8, 0.5) is gpu_mask

    backend_env("absent")
    backend.set_backend("cpu")
    cpu_mask = elliptical_mask(8, 8, 0.5)

    assert cpu_mask is not gpu_mask

    elliptical_mask.cache_clear()


# ---------------------------------------------------------------------------
# Backend consumers in utils
# ---------------------------------------------------------------------------

def test_pad_array_centrally_accepts_the_legacy_xp_argument() -> None:
    """The propagation kernels pass a third positional argument."""
    data = np.zeros((4, 4), dtype=np.float32)

    assert pad_array_centrally(data, (6, 6), np).shape == (6, 6)
    assert pad_array_centrally(data, (6, 6)).shape == (6, 6)
    assert pad_array_centrally(data, 6).shape == (6, 6)


def test_stretchlimcp_follows_the_active_backend(backend_env) -> None:
    backend_env("absent")
    backend.set_backend("cpu")

    low, high = stretchlimcp(np.arange(10, dtype=np.float64), 10, 90)

    assert float(low) <= float(high)


def test_fresnel_transform_without_padding_runs() -> None:
    """The un-padded propagation path keeps working with backend arrays."""
    from holodoppler.core.propagation import fresnel_transform

    frames = np.random.default_rng(3).random((2, 8, 8)).astype(np.complex64)

    result = fresnel_transform(
        np, np.fft, frames, 0.1, (2e-5, 2e-5), 852e-9
    )

    assert result.shape == (2, 8, 8)
