"""One preset source for checkouts, wheels and the Windows installer."""
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

import pytest

import build_installer
from holodoppler.ui import paths, settings_store


ROOT = Path(__file__).resolve().parents[1]
DEFAULT = "default_parameters_default.yaml"


def preset(directory, contents="pipeline_name: default\n"):
    directory.mkdir(parents=True, exist_ok=True)
    file = directory / DEFAULT
    file.write_text(contents, encoding="utf-8")
    return file


def test_checkout_presets_do_not_depend_on_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert paths.parameters_dir() == ROOT / "parameters"


def test_installed_package_presets(tmp_path, monkeypatch):
    package = tmp_path / "site-packages" / "holodoppler"
    monkeypatch.setattr(paths, "__file__", str(package / "ui" / "paths.py"))
    preset(package / "parameters")
    monkeypatch.chdir(tmp_path)
    assert paths.parameters_dir() == package / "parameters"


def test_frozen_presets_prefer_installed_files_then_bundle(tmp_path, monkeypatch):
    installed = tmp_path / "application"
    bundled = tmp_path / "bundle"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(installed / "HoloDoppler.exe"))
    monkeypatch.setattr(sys, "_MEIPASS", str(bundled), raising=False)
    preset(bundled / "parameters")
    monkeypatch.chdir(tmp_path)
    assert paths.parameters_dir() == bundled / "parameters"
    preset(installed / "parameters")
    assert paths.parameters_dir() == installed / "parameters"


def test_missing_presets_report_the_expected_locations(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "__file__", str(tmp_path / "package" / "ui" / "paths.py"))
    with pytest.raises(FileNotFoundError, match="Parameter presets not found"):
        paths.parameters_dir()


def test_ui_seeds_canonical_presets_without_overwriting_user_files(tmp_path, monkeypatch):
    appdata = tmp_path / "settings"
    monkeypatch.setattr(settings_store, "app_settings_dir", lambda: appdata)
    monkeypatch.setattr(settings_store, "legacy_app_settings_dir", lambda: tmp_path / "missing")
    monkeypatch.setattr(settings_store, "get_package_version", lambda: "test")
    custom = preset(appdata / "parameters", "pipeline_name: default\nz: 123\n")
    store = settings_store.SettingsStore()
    store.initialize()
    assert "z: 123" in custom.read_text()
    for source in (ROOT / "parameters").glob("*.yaml"):
        target = store.parameters_dir / source.name
        assert target.is_file()
        if source.name != DEFAULT:
            assert target.read_bytes() == source.read_bytes()


def test_installer_copies_and_validates_the_canonical_presets(tmp_path, monkeypatch):
    source = tmp_path / "source"
    preset(source)
    (source / "custom.json").write_text('{"pipeline_name": "lsci"}')
    (source / "README.md").write_text("Not a preset")
    monkeypatch.setattr(build_installer, "PARAMETERS_DIR", source)
    build_installer._validate_parameter_presets()
    target = tmp_path / "payload" / "parameters"
    build_installer._copy_parameter_presets(target)
    assert {file.name for file in target.iterdir()} == {DEFAULT, "custom.json"}
    for file in target.iterdir():
        assert file.read_bytes() == (source / file.name).read_bytes()
    (source / "bad.yaml").write_text("- invalid\n- parameter object")
    with pytest.raises(ValueError, match="must contain an object"):
        build_installer._validate_parameter_presets()


def test_pyinstaller_collects_current_presets_directly(tmp_path, monkeypatch):
    commands = []
    monkeypatch.setattr(build_installer, "_ensure_icon", lambda: tmp_path / "icon.ico")
    monkeypatch.setattr(build_installer, "_clean_pyinstaller_outputs", lambda: None)
    monkeypatch.setattr(build_installer, "_write_pyinstaller_entrypoint", lambda: tmp_path / "entry.py")
    monkeypatch.setattr(build_installer, "_run_command", commands.append)
    build_installer._run_pyinstaller(console=False)
    command = commands[0]
    added = [command[index + 1] for index, option in enumerate(command) if option == "--add-data"]
    assert added == [f"{file}{os.pathsep}parameters" for file in build_installer._parameter_preset_files()]


def test_wheel_and_source_distribution_include_canonical_presets(tmp_path):
    result = subprocess.run([
        sys.executable, "setup.py", "build", "--build-base", str(tmp_path / "build"),
        "bdist_wheel", "--bdist-dir", str(tmp_path / "bdist"), "--dist-dir", str(tmp_path / "dist"),
        "sdist", "--dist-dir", str(tmp_path / "dist"),
    ], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    sources = list((ROOT / "parameters").glob("*.yaml"))
    saving_sources = list((ROOT / "holodoppler" / "saving").glob("*.py"))
    wheel = next((tmp_path / "dist").glob("*.whl"))
    site = tmp_path / "installed"
    with zipfile.ZipFile(wheel) as archive:
        for source in sources:
            assert archive.read(f"holodoppler/parameters/{source.name}") == source.read_bytes()
        assert "holodoppler/saving.py" not in archive.namelist()
        for source in saving_sources:
            assert archive.read(f"holodoppler/saving/{source.name}") == source.read_bytes()
        archive.extractall(site)
    with tarfile.open(next((tmp_path / "dist").glob("*.tar.gz"))) as archive:
        names = archive.getnames()
        for source in sources:
            name = next(name for name in names if name.endswith(f"/parameters/{source.name}"))
            assert archive.extractfile(name).read() == source.read_bytes()
        for source in saving_sources:
            name = next(name for name in names if name.endswith(f"/holodoppler/saving/{source.name}"))
            assert archive.extractfile(name).read() == source.read_bytes()
    work = tmp_path / "unrelated-working-directory"
    work.mkdir()
    env = {**os.environ, "PYTHONPATH": str(site)}
    check = subprocess.run([
        sys.executable, "-c",
        "from pathlib import Path; from holodoppler.ui.paths import parameters_dir; "
        "from holodoppler.ui.settings_store import SettingsStore; "
        "from holodoppler.saving import OutputClass, save_outputs; "
        "assert OutputClass.__module__ == 'holodoppler.saving.session'; "
        "assert save_outputs.__module__ == 'holodoppler.saving.session'; "
        "import sys; assert parameters_dir() == Path(sys.argv[1]); "
        "assert len(SettingsStore()._default_parameter_sources()) == int(sys.argv[2])",
        str(site / "holodoppler" / "parameters"), str(len(sources)),
    ], cwd=work, env=env, capture_output=True, text=True, timeout=30)
    assert check.returncode == 0, check.stdout + check.stderr
