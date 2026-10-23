"""The installer keeps drag and drop for the process CPU and both Tcl ABIs."""

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def hook(tmp_path, monkeypatch):
    pytest.importorskip("PyInstaller")
    path = Path(__file__).resolve().parents[1] / "packaging" / "hooks" / "hook-tkinterdnd2.py"
    spec = importlib.util.spec_from_file_location("_tkinterdnd2_hook", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    package = tmp_path / "tkinterdnd2"
    for name, library in (
        ("win-x64", "tkdnd.dll"), ("win-x86", "tkdnd.dll"),
        ("win-arm64", "tkdnd.dll"), ("linux-x64", "libtkdnd.so"),
        ("osx-arm64", "libtkdnd.dylib"),
    ):
        for abi in ("", "-tcl9"):
            directory = package / "tkdnd" / f"{name}{abi}"
            directory.mkdir(parents=True)
            for filename in (library, "pkgIndex.tcl", "unused.lib"):
                (directory / filename).touch()
    monkeypatch.setattr(module, "get_package_paths", lambda name: (str(tmp_path), str(package)))
    return module, package


@pytest.mark.parametrize("system,host,process,expected", [
    ("Windows", "AMD64", "x86", "win-x86"),
    ("Windows", "ARM64", "AMD64", "win-x64"),
    ("Windows", "ARM64", "ARM64", "win-arm64"),
    ("Linux", "x86_64", "AMD64", "linux-x64"),
    ("Darwin", "arm64", "AMD64", "osx-arm64"),
])
def test_collects_only_process_platform_and_preserves_tcl_abis(hook, monkeypatch, system, host, process, expected):
    module, package = hook
    monkeypatch.setenv("PROCESSOR_ARCHITECTURE", process)
    datas, binaries = module._collect_platform_subdirs(system, host)
    assert len(datas) == len(binaries) == 2
    expected_dirs = {expected, f"{expected}-tcl9"}
    for source, destination in datas + binaries:
        assert Path(source).parent.name in expected_dirs
        assert Path(destination).name == Path(source).parent.name
        assert Path(source).is_relative_to(package)
        assert not source.endswith(".lib")
    assert {Path(source).parent.name for source, _ in binaries} == expected_dirs


def test_older_tkinterdnd_without_tcl9_is_supported(hook):
    module, package = hook
    for path in (package / "tkdnd" / "linux-x64-tcl9").iterdir():
        path.unlink()
    (package / "tkdnd" / "linux-x64-tcl9").rmdir()
    datas, binaries = module._collect_platform_subdirs("Linux", "x86_64")
    assert len(datas) == len(binaries) == 1
    assert Path(binaries[0][0]).parent.name == "linux-x64"
