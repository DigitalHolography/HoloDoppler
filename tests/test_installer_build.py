"""Build reports and release verification must describe the actual artifacts."""

from contextlib import nullcontext
import hashlib
import json
import multiprocessing
import runpy
import subprocess
import sys
import types

import pytest

import build_installer


def test_size_report_counts_payload_bytes_and_hashes_installer(tmp_path, monkeypatch):
    payload = tmp_path / "payload"
    dist = tmp_path / "dist"
    dist.mkdir()
    contents = {
        "HoloDoppler.exe": b"launcher",
        "_internal/numpy/core.pyd": b"numpy-runtime",
        "_internal/nvidia/cuda/runtime.dll": b"cuda-runtime",
        "_internal/nvidia/cublas/library.dll": b"blas",
        "_internal/python314.dll": b"python",
        "parameters/default.yaml": b"pipeline_name: default\n",
        **{f"_internal/numpy/data/{index:02}.bin": bytes(index) for index in range(22)},
    }
    for name, data in contents.items():
        path = payload / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (payload / "empty_directory").mkdir()
    installer = dist / "HoloDoppler-setup-test.exe"
    installer.write_bytes(b"compressed installer bytes\x00\xff")
    monkeypatch.setattr(build_installer, "PAYLOAD_DIR", payload)
    monkeypatch.setattr(build_installer, "DIST_DIR", dist)
    monkeypatch.setattr(build_installer, "FROZEN_METADATA_DISTRIBUTIONS", ("numpy", "cupy-cuda13x"))
    monkeypatch.setattr(build_installer, "version", {"numpy": "1.2.3", "cupy-cuda13x": "4.5.6"}.__getitem__)

    output = build_installer._write_size_report("test", installer)
    report = json.loads(output.read_text(encoding="utf-8"))

    assert report["app_version"] == "test"
    assert report["payload_bytes"] == sum(map(len, contents.values()))
    assert report["payload_file_count"] == len(contents)
    assert report["package_bytes"] == {
        "HoloDoppler.exe": len(contents["HoloDoppler.exe"]),
        "numpy": sum(len(data) for name, data in contents.items() if name.startswith("_internal/numpy/")),
        "nvidia": sum(len(data) for name, data in contents.items() if name.startswith("_internal/nvidia/")),
        "python314.dll": len(contents["_internal/python314.dll"]),
        "parameters": len(contents["parameters/default.yaml"]),
    }
    expected_largest = sorted(contents.items(), key=lambda item: (-len(item[1]), item[0]))[:20]
    assert report["largest_files"] == [
        {"path": name, "bytes": len(data)} for name, data in expected_largest
    ]
    assert report["distributions"] == {"numpy": "1.2.3", "cupy-cuda13x": "4.5.6"}
    assert report["installer"] == installer.name
    assert report["installer_bytes"] == len(installer.read_bytes())
    assert report["installer_sha256"] == hashlib.sha256(installer.read_bytes()).hexdigest()


def test_frozen_verification_requires_a_fresh_report_even_after_success_exit(tmp_path, monkeypatch):
    executable = tmp_path / "HoloDoppler.exe"
    report = tmp_path / "verification.json"
    report.write_text('{"ok": true}', encoding="utf-8")

    def run(command, **kwargs):
        assert command == [str(executable), "--self-test", str(report)]
        assert kwargs["cwd"] == executable.parent
        assert not report.exists(), "A stale result must not verify the current executable."
        return subprocess.CompletedProcess(command, 0, "application output", "diagnostic output")

    monkeypatch.setattr(build_installer.subprocess, "run", run)
    with pytest.raises(RuntimeError, match="did not write its verification report") as failure:
        build_installer._verify_frozen_app(executable, report)
    assert "application output" in str(failure.value)
    assert "diagnostic output" in str(failure.value)


@pytest.mark.parametrize("exit_code,ok", [(0, False), (1, True), (1, False), (0, "true")])
def test_frozen_verification_rejects_failed_process_or_report(tmp_path, monkeypatch, exit_code, ok):
    report = tmp_path / "verification.json"

    def run(command, **kwargs):
        report.write_text(json.dumps({"ok": ok, "checks": {}}), encoding="utf-8")
        return subprocess.CompletedProcess(command, exit_code)

    monkeypatch.setattr(build_installer.subprocess, "run", run)
    with pytest.raises(RuntimeError, match="verification failed"):
        build_installer._verify_frozen_app(tmp_path / "HoloDoppler.exe", report)


def test_frozen_verification_returns_successful_check_details(tmp_path, monkeypatch):
    report = tmp_path / "verification.json"
    checks = {"ok": True, "checks": {"cpu": {"status": "passed"}, "gpu": {"status": "skipped"}}}

    def run(command, **kwargs):
        report.write_text(json.dumps(checks), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(build_installer.subprocess, "run", run)
    assert build_installer._verify_frozen_app(tmp_path / "HoloDoppler.exe", report) == checks


@pytest.mark.parametrize("missing_output", [None, "preview", "h5", "parameters", "png"])
def test_release_smoke_checks_current_outputs_for_each_pipeline(tmp_path, monkeypatch, missing_output):
    executable = tmp_path / "HoloDoppler.exe"
    executable.touch()
    source_holo = tmp_path / "sample.holo"
    source_holo.write_bytes(b"source hologram")
    source_parameters = tmp_path / "parameters.yaml"
    source_parameters.write_text("pipeline_name: lsci\n", encoding="utf-8")
    work = tmp_path / "workspace"
    work.mkdir()
    stale_file = work / "stale-output.png"
    stale_file.write_bytes(b"previous release")
    monkeypatch.setattr(build_installer, "SMOKE_WORK_DIR", work)
    output_dir = work / "sample" / "sample_HD"
    outputs = {
        "preview": output_dir / "preview" / "h5" / "preview_output.h5",
        "h5": output_dir / "h5" / "sample_HD_output.h5",
        "parameters": output_dir / "json" / "parameters_holodoppler.json",
        "png": output_dir / "png" / "contrast.png",
    }
    commands = []

    def run(command, **kwargs):
        assert kwargs["cwd"] == work
        assert not stale_file.exists(), "Prior outputs must not satisfy current verification."
        assert (work / source_holo.name).read_bytes() == source_holo.read_bytes()
        assert (work / source_parameters.name).read_bytes() == source_parameters.read_bytes()
        assert command == [str(executable), command[1], str(work / source_holo.name), str(work / source_parameters.name)]
        commands.append(command[1])
        created = ("preview",) if command[1] == "preview" else ("h5", "parameters", "png")
        for name in created:
            if name != missing_output:
                outputs[name].parent.mkdir(parents=True, exist_ok=True)
                outputs[name].write_bytes(b"new output")
        return subprocess.CompletedProcess(command, 0, stdout="")

    monkeypatch.setattr(build_installer.subprocess, "run", run)

    if missing_output is None:
        verified = build_installer._run_release_smoke_test(executable, source_holo, source_parameters)
        assert set(verified) == set(outputs.values())
        assert outputs["png"].name == "contrast.png"
    else:
        with pytest.raises(RuntimeError, match="Release smoke test did not create"):
            build_installer._run_release_smoke_test(executable, source_holo, source_parameters)
    assert commands == ["preview", "process"]


@pytest.mark.parametrize("arguments,expected_route", [
    (["--self-test", "verification.json"], "self-test"),
    (["preview", "sample.holo", "parameters.yaml"], "app"),
])
def test_generated_launcher_routes_self_test_and_normal_commands(tmp_path, monkeypatch, arguments, expected_route):
    monkeypatch.setattr(build_installer, "BUILD_DIR", tmp_path)
    monkeypatch.setattr(build_installer, "GENERATED_ENTRYPOINT", tmp_path / "entry.py")
    events = []
    monkeypatch.setattr(multiprocessing, "freeze_support", lambda: events.append("freeze_support"))
    app = types.ModuleType("holodoppler.__main__")
    smoke = types.ModuleType("holodoppler._frozen_smoke")

    def app_main():
        events.append(("app", sys.argv[1:]))
        return 12

    def smoke_main(report):
        events.append(("self-test", report))
        return 12

    app.main = app_main
    smoke.main = smoke_main
    monkeypatch.setitem(sys.modules, "holodoppler.__main__", app)
    monkeypatch.setitem(sys.modules, "holodoppler._frozen_smoke", smoke)
    entrypoint = build_installer._write_pyinstaller_entrypoint()
    monkeypatch.setattr(sys, "argv", [str(entrypoint), *arguments])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(entrypoint), run_name="__main__")

    assert exit_info.value.code == 12
    expected_argument = "verification.json" if expected_route == "self-test" else arguments
    assert events == ["freeze_support", (expected_route, expected_argument)]


@pytest.fixture
def installer_verification(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    dist.mkdir()
    installer = dist / "setup.exe"
    installer.write_bytes(b"installer")
    install_root = tmp_path / "installed"
    work = tmp_path / "workspace"
    monkeypatch.setattr(build_installer, "DIST_DIR", dist)
    monkeypatch.setattr(build_installer, "SMOKE_INSTALL_DIR", install_root)
    monkeypatch.setattr(build_installer, "SMOKE_WORK_DIR", work)
    commands = []

    def run(command):
        commands.append(command)
        if command[0] == installer:
            target = install_root / "test"
            target.mkdir(parents=True)
            (target / "HoloDoppler.exe").touch()
            (target / "unins000.exe").touch()

    monkeypatch.setattr(build_installer, "_run_command", run)
    return installer, install_root, dist, commands


@pytest.mark.parametrize("with_smoke_inputs", [False, True])
def test_installer_verification_runs_installed_self_test_before_writing_pass(
    installer_verification, monkeypatch, with_smoke_inputs,
):
    installer, install_root, dist, commands = installer_verification
    report = dist / "release-verification.txt"
    events = []

    def verify(executable, json_report):
        assert executable == install_root / "test" / "HoloDoppler.exe"
        assert executable.is_file()
        assert json_report == dist / "release-self-test.json"
        assert not report.exists()
        events.append("self-test")
        return {"ok": True, "checks": {
            "cpu": {"status": "passed"},
            "gpu": {"status": "skipped"},
            "exports": {"status": "passed"},
        }}

    def verify_parameters(version):
        assert events == ["self-test"]
        events.append("parameters")
        return [dist / "appdata" / "default.yaml"]

    def smoke(executable, *inputs):
        assert events == ["self-test", "parameters"]
        assert inputs == smoke_inputs
        events.append("smoke")
        return [build_installer.SMOKE_WORK_DIR / "output.png"]

    monkeypatch.setattr(build_installer, "_verify_frozen_app", verify)
    monkeypatch.setattr(build_installer, "_verify_appdata_parameters", verify_parameters)
    monkeypatch.setattr(build_installer, "_run_release_smoke_test", smoke)
    smoke_inputs = (dist / "sample.holo", dist / "parameters.yaml") if with_smoke_inputs else None

    build_installer._verify_installer(installer, "test", smoke_inputs)

    values = dict(line.split("=", 1) for line in report.read_text(encoding="utf-8").splitlines())
    assert values["result"] == "PASS"
    assert values["tests"].split(",") == ["install", "cpu", "exports", *(["preview", "process"] if with_smoke_inputs else [])]
    assert values["installer_sha256"] == hashlib.sha256(installer.read_bytes()).hexdigest()
    if with_smoke_inputs:
        assert values["verified_output"] == "output.png"
    assert commands[0][0] == installer
    assert commands[1][0] == install_root / "test" / "unins000.exe"
    assert not install_root.exists()


def test_failed_installer_verification_removes_stale_pass_and_uninstalls(installer_verification, monkeypatch):
    installer, install_root, dist, commands = installer_verification
    report = dist / "release-verification.txt"
    report.write_text("result=PASS\n", encoding="utf-8")

    def verify(*args):
        raise RuntimeError("frozen export failed")

    def unexpected_parameters(*args):
        pytest.fail("Parameter checks must not run after frozen verification fails.")

    monkeypatch.setattr(build_installer, "_verify_frozen_app", verify)
    monkeypatch.setattr(build_installer, "_verify_appdata_parameters", unexpected_parameters)

    with pytest.raises(RuntimeError, match="frozen export failed"):
        build_installer._verify_installer(installer, "test", None)

    assert not report.exists()
    assert commands[-1][0] == install_root / "test" / "unins000.exe"
    assert not install_root.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Installer registrations use the Windows registry.")
def test_installer_verification_checks_both_registry_hives_and_views(monkeypatch):
    import winreg

    calls = []

    def missing_key(hive, name, reserved, access):
        calls.append((hive, name, reserved, access))
        raise FileNotFoundError(name)

    monkeypatch.setattr(winreg, "OpenKey", missing_key)
    build_installer._ensure_verification_target_available("test")

    assert [(hive, access) for hive, _, _, access in calls] == [
        (hive, winreg.KEY_READ | view)
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
        for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY)
    ]
    expected_name = (
        "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\"
        f"HoloDoppler-test-{build_installer.APP_ID_SUFFIX}_is1"
    )
    assert all(name == expected_name and reserved == 0 for _, name, reserved, _ in calls)


@pytest.mark.skipif(sys.platform != "win32", reason="Installer registrations use the Windows registry.")
def test_existing_installation_aborts_verification_before_cleanup_or_install(installer_verification, monkeypatch):
    import winreg

    installer, install_root, dist, commands = installer_verification
    install_root.mkdir()
    sentinel = install_root / "keep-existing-file"
    sentinel.write_bytes(b"existing data")
    report = dist / "release-verification.txt"
    report.write_text("existing verification\n", encoding="utf-8")

    def open_key(hive, name, reserved, access):
        if hive == winreg.HKEY_LOCAL_MACHINE and access == winreg.KEY_READ | winreg.KEY_WOW64_64KEY:
            return nullcontext()
        raise FileNotFoundError(name)

    monkeypatch.setattr(winreg, "OpenKey", open_key)
    with pytest.raises(RuntimeError, match="already installed"):
        build_installer._verify_installer(installer, "test", None)

    assert commands == []
    assert sentinel.read_bytes() == b"existing data"
    assert report.read_text(encoding="utf-8") == "existing verification\n"
