"""Tests for the execution context seam.

``ExecutionContext`` is how core code reaches the array module without reading
the process-global backend directly.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

import holodoppler.backend as backend
from holodoppler.execution import ExecutionContext


class _FakeCupyModule:
    """Hashable NumPy-backed stand-in for ``cupy``."""

    def __init__(self) -> None:
        self.asarray = np.asarray
        self.asnumpy = np.asarray
        self.ndarray = np.ndarray
        self.float32 = np.float32
        self.zeros = np.zeros


@pytest.fixture(autouse=True)
def _reset_backend_after_test():
    """Leave the process backend unselected so tests cannot leak state."""
    yield
    backend.reset_backend()


@pytest.fixture
def fake_gpu(monkeypatch: pytest.MonkeyPatch) -> _FakeCupyModule:
    """Make the backend believe a usable GPU is present."""
    stub = _FakeCupyModule()
    modules = backend._CupyModules(
        cp=stub,
        fft=np.fft,
        ndi=np,
        gaussian_filter=np.zeros,
        zoom=np.zeros,
        linalg=np.linalg,
    )

    monkeypatch.setattr(backend, "_backend", None)
    monkeypatch.setattr(backend, "_cupy_state", lambda: "usable")
    monkeypatch.setattr(backend, "_cupy_modules", lambda: modules)

    return stub


# ---------------------------------------------------------------------------
# Backend identity
# ---------------------------------------------------------------------------

def test_cpu_context_reports_numpy() -> None:
    context = ExecutionContext.from_backend("cpu")

    assert context.backend_name == "numpy"
    assert context.requested_mode == "cpu"
    assert context.is_gpu is False
    assert context.array_module is np
    assert context.xp is np
    assert context.fft is not None
    assert context.linalg is not None


def test_default_context_is_auto() -> None:
    """No explicit selector means ``auto``, matching the historical default."""
    context = ExecutionContext.from_backend()

    assert context.requested_mode == "auto"


def test_gpu_context_reports_cupy(fake_gpu) -> None:
    context = ExecutionContext.from_backend("gpu")

    assert context.backend_name == "cupy"
    assert context.is_gpu is True
    assert context.array_module is fake_gpu


def test_gpu_context_fails_loudly_when_cuda_is_unusable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(backend, "_backend", None)
    monkeypatch.setattr(backend, "_cupy_state", lambda: "unusable")

    with pytest.raises(backend.BackendNotAvailableError):
        ExecutionContext.from_backend("gpu")


def test_current_follows_the_selected_backend() -> None:
    backend.set_backend("cpu")

    assert ExecutionContext.current().array_module is np


# ---------------------------------------------------------------------------
# Array conversion
# ---------------------------------------------------------------------------

def test_to_backend_and_to_numpy_round_trip_on_cpu() -> None:
    context = ExecutionContext.from_backend("cpu")

    converted = context.to_backend([1, 2, 3])
    assert isinstance(converted, np.ndarray)

    restored = context.to_numpy(converted)
    assert isinstance(restored, np.ndarray)
    np.testing.assert_array_equal(restored, [1, 2, 3])


def test_to_backend_uses_the_context_backend_not_the_global(fake_gpu) -> None:
    """A context must not consult the process-global backend for conversions."""
    context = ExecutionContext.from_backend("gpu")

    # Switch the process backend out from under the context.
    backend.set_backend("cpu")

    assert context.is_gpu is True
    assert context.array_module is fake_gpu
    assert isinstance(context.to_backend([1, 2]), np.ndarray)


# ---------------------------------------------------------------------------
# Value semantics
# ---------------------------------------------------------------------------

def test_context_is_frozen() -> None:
    context = ExecutionContext.from_backend("cpu")

    with pytest.raises(dataclasses.FrozenInstanceError):
        context.mode = "preview"  # type: ignore[misc]


def test_with_mode_returns_a_copy() -> None:
    context = ExecutionContext.from_backend("cpu")

    preview = context.with_mode("preview")

    assert preview is not context
    assert preview.mode == "preview"
    assert context.mode == "process"
    assert preview.array_module is context.array_module


def test_progress_callback_is_carried() -> None:
    def progress(*args):
        return None

    context = ExecutionContext.from_backend(
        "cpu",
        mode="preview",
        progress_callback=progress,
    )

    assert context.mode == "preview"
    assert context.progress_callback is progress


def test_context_has_no_unused_callback_or_debug_fields() -> None:
    """Keep the context to what is actually used.

    ``warning_callback`` and ``save_debug`` were removed: no bundled pipeline
    consumed either, so they only suggested a channel that did not exist.
    """
    fields = {field.name for field in dataclasses.fields(ExecutionContext)}

    assert fields == {"backend", "mode", "progress_callback"}


def test_defaults_match_the_current_cli_behaviour() -> None:
    context = ExecutionContext.from_backend("cpu")

    assert context.mode == "process"
    assert context.progress_callback is None
