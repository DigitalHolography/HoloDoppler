"""Release smoke checks must distinguish absent GPUs from incomplete bundles."""

import json
from types import SimpleNamespace

import pytest

from holodoppler import _frozen_smoke as smoke


class CUDARuntimeError(Exception):
    def __init__(self, status):
        self.status = status


def runtime(result):
    def count():
        if isinstance(result, Exception):
            raise result
        return result
    return SimpleNamespace(cuda=SimpleNamespace(runtime=SimpleNamespace(
        getDeviceCount=count, CUDARuntimeError=CUDARuntimeError)))


def test_gpu_skip_only_for_absent_driver_or_device(monkeypatch):
    assert smoke._no_gpu_reason(runtime(0))
    assert smoke._no_gpu_reason(runtime(1)) is None
    assert smoke._no_gpu_reason(runtime(CUDARuntimeError(100)))
    monkeypatch.setattr(smoke, "_cuda_driver_device_count", lambda: None)
    assert smoke._no_gpu_reason(runtime(CUDARuntimeError(35)))
    monkeypatch.setattr(smoke, "_cuda_driver_device_count", lambda: 1)
    with pytest.raises(CUDARuntimeError):
        smoke._no_gpu_reason(runtime(CUDARuntimeError(35)))
    with pytest.raises(CUDARuntimeError):
        smoke._no_gpu_reason(runtime(CUDARuntimeError(803)))
    with pytest.raises(OSError, match="cudart"):
        smoke._no_gpu_reason(runtime(OSError("missing cudart DLL")))


def test_report_survives_failure_and_missing_windowed_stdout(tmp_path, monkeypatch):
    def broken():
        raise ImportError("a required library is missing")

    def no_gpu():
        raise smoke._SkipCheck("No CUDA device")

    monkeypatch.setattr(smoke, "_CHECKS", (
        ("broken", broken), ("gpu", no_gpu), ("later_check", lambda: "ran")))
    monkeypatch.setattr(smoke.sys, "stdout", None)
    path = tmp_path / "report.json"
    assert smoke.main(path) == 1
    report = json.loads(path.read_text(encoding="utf-8"))
    assert not report["ok"]
    assert report["checks"]["broken"]["status"] == "failed"
    assert "ImportError" in report["checks"]["broken"]["traceback"]
    assert report["checks"]["gpu"]["status"] == "skipped"
    assert report["checks"]["later_check"]["detail"] == "ran"


def test_skipped_gpu_does_not_fail_cpu_release(tmp_path, monkeypatch):
    def no_gpu():
        raise smoke._SkipCheck("No CUDA device")

    monkeypatch.setattr(smoke, "_CHECKS", (("cpu", lambda: "passed"), ("gpu", no_gpu)))
    path = tmp_path / "report.json"
    assert smoke.main(path) == 0
    assert json.loads(path.read_text(encoding="utf-8"))["ok"]
