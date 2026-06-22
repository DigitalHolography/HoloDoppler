from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import textwrap
import tomllib
from datetime import datetime, timezone
from pathlib import Path


APP_NAME = "HoloDoppler"
APP_EXE_NAME = f"{APP_NAME}.exe"
APP_PUBLISHER = "HoloDoppler"

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
PYPROJECT_FILE = PROJECT_ROOT / "pyproject.toml"
VERSION_FILE = PROJECT_ROOT / "version_holodoppler.txt"

DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
PYINSTALLER_WORK_DIR = BUILD_DIR / APP_NAME
PAYLOAD_DIR = BUILD_DIR / "installer_payload"
SMOKE_INSTALL_DIR = BUILD_DIR / "installer_smoke_install"
SMOKE_WORK_DIR = BUILD_DIR / "installer_smoke_workspace"
GENERATED_ENTRYPOINT = BUILD_DIR / "_pyinstaller_holodoppler_entry.py"
GENERATED_ISS_FILE = BUILD_DIR / f"{APP_NAME}.iss"
CUDA_RUNTIME_HOOK = PROJECT_ROOT / "packaging" / "pyi_rth_cuda.py"

INSTALLER_OUTPUT_DIR = DIST_DIR
DIST_APP_DIR = DIST_DIR / APP_NAME
DIST_EXE = DIST_APP_DIR / APP_EXE_NAME

EXAMPLES_DIR = PROJECT_ROOT / "examples"
EXAMPLE_HOLO = EXAMPLES_DIR / "HoloDoppler_example.holo"
EXAMPLE_PARAMETERS = EXAMPLES_DIR / "example_parameters.json"

INNO_SETUP_CANDIDATES = (
    Path.home() / "AppData" / "Local" / "Programs" / "Inno Setup 6" / "ISCC.exe",
    Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
)

PAYLOAD_EXTRA_FILES = (
    PROJECT_ROOT / "LICENSE",
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "pyproject.toml",
    VERSION_FILE,
)

FROZEN_METADATA_DISTRIBUTIONS = (
    "holodoppler",
    "imageio",
    "cupy-cuda13x",
    "cuda-pathfinder",
    "nvidia-cublas",
    "nvidia-cuda-nvrtc",
    "nvidia-cuda-runtime",
    "nvidia-cufft",
    "nvidia-curand",
    "nvidia-cusolver",
    "nvidia-cusparse",
    "nvidia-nvjitlink",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the HoloDoppler Windows installer with PyInstaller and Inno Setup."
    )
    parser.add_argument(
        "--skip-pyinstaller",
        action="store_true",
        help="Reuse dist/HoloDoppler.exe instead of rebuilding it with PyInstaller.",
    )
    parser.add_argument(
        "--skip-inno",
        action="store_true",
        help="Build and stage the PyInstaller payload without compiling an installer.",
    )
    parser.add_argument(
        "--iscc",
        type=Path,
        help="Optional full path to ISCC.exe.",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Build the executable with a visible console window.",
    )
    parser.add_argument(
        "--verify-installer",
        action="store_true",
        help="Install the generated setup silently, run preview/process smoke tests, then uninstall it.",
    )
    return parser.parse_args()


def _ensure_supported_python() -> None:
    required = (3, 13)
    if sys.version_info < required:
        version = ".".join(str(part) for part in sys.version_info[:3])
        raise SystemExit(
            f"build_installer.py must run with Python {required[0]}.{required[1]} or newer. "
            f"Current interpreter: {sys.executable} ({version})."
        )


def _read_version() -> str:
    if PYPROJECT_FILE.exists():
        data = tomllib.loads(PYPROJECT_FILE.read_text(encoding="utf-8"))
        version = data.get("project", {}).get("version")
        if isinstance(version, str) and version.strip():
            return version.strip()

    if VERSION_FILE.exists():
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
        if version:
            return version

    raise RuntimeError(f"Could not read version from {PYPROJECT_FILE} or {VERSION_FILE}")


def _find_iscc(explicit_path: Path | None) -> Path:
    candidates: list[Path] = []

    if explicit_path is not None:
        candidates.append(explicit_path.expanduser())

    env_override = os.environ.get("INNO_SETUP_COMPILER")
    if env_override:
        candidates.append(Path(env_override).expanduser())

    for command_name in ("iscc.exe", "iscc"):
        resolved = shutil.which(command_name)
        if resolved:
            candidates.append(Path(resolved))

    candidates.extend(INNO_SETUP_CANDIDATES)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    searched = "\n".join(str(path) for path in candidates if path)
    raise FileNotFoundError(
        "Could not find ISCC.exe. Set INNO_SETUP_COMPILER, pass --iscc, "
        "or add Inno Setup 6 to PATH.\n"
        f"Searched:\n{searched}"
    )


def _run_command(command: list[str | Path]) -> None:
    cmd = [str(part) for part in command]
    print(f"> {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    print(result.stdout)

    if result.returncode != 0:
        raise SystemExit(f"Command failed with exit code {result.returncode}")


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _clean_pyinstaller_outputs() -> None:
    _remove_path(DIST_APP_DIR)
    _remove_path(DIST_EXE)
    _remove_path(PYINSTALLER_WORK_DIR)
    _remove_path(PROJECT_ROOT / f"{APP_NAME}.spec")
    _remove_path(GENERATED_ENTRYPOINT)


def _write_pyinstaller_entrypoint() -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    GENERATED_ENTRYPOINT.write_text(
        textwrap.dedent(
            """
            from __future__ import annotations

            import sys
            import traceback
            from pathlib import Path

            from holodoppler.cli import main as cli_main
            from holodoppler.ui import UI

            def main() -> int:
                if len(sys.argv) == 1:
                    UI().mainloop()
                    return 0

                return cli_main()

            if __name__ == "__main__":
                try:
                    raise SystemExit(main())
                except SystemExit:
                    raise
                except Exception:
                    details = traceback.format_exc()
                    if sys.stderr is not None:
                        print(details, file=sys.stderr)
                    if len(sys.argv) > 1:
                        Path.cwd().joinpath("holodoppler-error.log").write_text(
                            details, encoding="utf-8"
                        )
                        raise SystemExit(1)
                    raise
            """
        ).lstrip(),
        encoding="utf-8",
    )

    return GENERATED_ENTRYPOINT


def _run_pyinstaller(console: bool) -> None:
    if not SRC_DIR.exists():
        raise SystemExit(f"Package source directory not found: {SRC_DIR}")

    _clean_pyinstaller_outputs()
    entrypoint = _write_pyinstaller_entrypoint()

    command: list[str | Path] = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        APP_NAME,
        "--workpath",
        PYINSTALLER_WORK_DIR,
        "--distpath",
        DIST_DIR,
        "--paths",
        SRC_DIR,
        "--runtime-hook",
        CUDA_RUNTIME_HOOK,
        "--hidden-import",
        "graphlib",
        "--collect-submodules",
        "cupy",
        "--collect-submodules",
        "cupyx",
        "--collect-submodules",
        "cupy_backends",
        "--collect-data",
        "tkinterdnd2",
        "--collect-data",
        "sv_ttk",
        "--collect-data",
        "holodoppler",
        "--collect-data",
        "cupy",
        "--collect-all",
        "nvidia",
    ]

    for distribution in FROZEN_METADATA_DISTRIBUTIONS:
        command.extend(["--copy-metadata", distribution])

    if console:
        command.append("--console")
    else:
        command.append("--windowed")

    command.append(entrypoint)

    _run_command(command)


def _prepare_payload() -> None:
    if not DIST_EXE.is_file():
        raise FileNotFoundError(
            "PyInstaller output not found. Expected "
            f"{DIST_EXE}. Run without --skip-pyinstaller first."
        )

    if PAYLOAD_DIR.exists():
        shutil.rmtree(PAYLOAD_DIR)

    if not EXAMPLE_HOLO.is_file() or not EXAMPLE_PARAMETERS.is_file():
        raise FileNotFoundError(
            "Release examples are missing. Run scripts/generate_example_holo.py first."
        )

    shutil.copytree(DIST_APP_DIR, PAYLOAD_DIR)
    shutil.copytree(EXAMPLES_DIR, PAYLOAD_DIR / "examples")

    for extra_file in PAYLOAD_EXTRA_FILES:
        if extra_file.exists():
            shutil.copy2(extra_file, PAYLOAD_DIR / extra_file.name)


def _iss_string(value: str | Path) -> str:
    return str(value).replace('"', '""')


def _version_info_version(app_version: str) -> str:
    numeric_parts: list[str] = []

    for part in app_version.replace("-", ".").replace("+", ".").split("."):
        if not part.isdigit():
            break
        numeric_parts.append(part)

    if not numeric_parts:
        numeric_parts.append("0")

    return ".".join((numeric_parts + ["0", "0", "0", "0"])[:4])


def _write_inno_script(app_version: str) -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    INSTALLER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    script = f"""
        #define AppName "{_iss_string(APP_NAME)}"
        #define AppExeName "{_iss_string(APP_EXE_NAME)}"
        #define AppVersion "{_iss_string(app_version)}"
        #define VersionInfoVersion "{_iss_string(_version_info_version(app_version))}"
        #define AppPublisher "{_iss_string(APP_PUBLISHER)}"
        #define PayloadDir "{_iss_string(PAYLOAD_DIR)}"
        #define OutputDir "{_iss_string(INSTALLER_OUTPUT_DIR)}"

        [Setup]
        AppId={{#AppName}}-7C3E24DA-5E1F-4E4E-91F1-91D62A0F1B18
        AppName={{#AppName}}
        AppVersion={{#AppVersion}}
        AppVerName={{#AppName}} {{#AppVersion}}
        AppPublisher={{#AppPublisher}}
        DefaultDirName={{localappdata}}\\Programs\\{{#AppName}}
        DefaultGroupName={{#AppName}}
        DisableProgramGroupPage=yes
        OutputDir={{#OutputDir}}
        OutputBaseFilename={{#AppName}}-setup-{{#AppVersion}}
        Compression=lzma2
        SolidCompression=yes
        WizardStyle=modern
        PrivilegesRequired=lowest
        UninstallDisplayIcon={{app}}\\{{#AppExeName}}
        VersionInfoCompany={{#AppPublisher}}
        VersionInfoDescription={{#AppName}} installer
        VersionInfoVersion={{#VersionInfoVersion}}

        [Tasks]
        Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

        [Dirs]
        Name: "{{userappdata}}\\{{#AppName}}"; Flags: uninsneveruninstall
        Name: "{{userappdata}}\\{{#AppName}}\\logs"; Flags: uninsneveruninstall

        [Files]
        Source: "{{#PayloadDir}}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

        [Icons]
        Name: "{{autoprograms}}\\{{#AppName}}"; Filename: "{{app}}\\{{#AppExeName}}"
        Name: "{{autodesktop}}\\{{#AppName}}"; Filename: "{{app}}\\{{#AppExeName}}"; Tasks: desktopicon

        [Run]
        Filename: "{{app}}\\{{#AppExeName}}"; Description: "Launch {{#AppName}}"; Flags: nowait postinstall skipifsilent
    """

    GENERATED_ISS_FILE.write_text(textwrap.dedent(script).lstrip(), encoding="utf-8")
    return GENERATED_ISS_FILE


def _run_inno_setup(iscc_path: Path, app_version: str) -> None:
    iss_file = _write_inno_script(app_version)
    _run_command([iscc_path, iss_file])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_release_smoke_test(executable: Path, examples_dir: Path) -> list[Path]:
    if not executable.is_file():
        raise FileNotFoundError(f"Installed executable not found: {executable}")

    _remove_path(SMOKE_WORK_DIR)
    SMOKE_WORK_DIR.mkdir(parents=True)
    sample = SMOKE_WORK_DIR / EXAMPLE_HOLO.name
    parameters = SMOKE_WORK_DIR / EXAMPLE_PARAMETERS.name
    shutil.copy2(examples_dir / EXAMPLE_HOLO.name, sample)
    shutil.copy2(examples_dir / EXAMPLE_PARAMETERS.name, parameters)

    commands = (
        [executable, "preview", sample, parameters],
        [executable, "process", sample, parameters],
    )
    for command in commands:
        result = subprocess.run(
            [str(part) for part in command],
            cwd=SMOKE_WORK_DIR,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
        )
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0:
            raise RuntimeError(
                f"Release smoke test failed with exit code {result.returncode}: "
                f"{' '.join(str(part) for part in command)}"
            )

    output_dir = SMOKE_WORK_DIR / EXAMPLE_HOLO.stem / f"{EXAMPLE_HOLO.stem}_HD"
    expected = [
        SMOKE_WORK_DIR / "debug_outputs" / "debug_M0.png",
        output_dir / "h5" / f"{output_dir.name}_output.h5",
        output_dir / "json" / "parameters_holodoppler.json",
        output_dir / "png" / "moment_0.png",
    ]
    missing = [path for path in expected if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(
            "Release smoke test did not create the expected files:\n"
            + "\n".join(str(path) for path in missing)
        )
    return expected


def _verify_installer(installer_path: Path) -> None:
    _remove_path(SMOKE_INSTALL_DIR)
    SMOKE_INSTALL_DIR.mkdir(parents=True)

    install_command = [
        installer_path,
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/SP-",
        "/TASKS=",
        f"/DIR={SMOKE_INSTALL_DIR}",
    ]

    try:
        _run_command(install_command)
        verified_files = _run_release_smoke_test(
            SMOKE_INSTALL_DIR / APP_EXE_NAME,
            SMOKE_INSTALL_DIR / "examples",
        )
        report = DIST_DIR / "release-verification.txt"
        report.write_text(
            "\n".join(
                [
                    f"verified_at_utc={datetime.now(timezone.utc).isoformat()}",
                    f"installer={installer_path.name}",
                    f"installer_sha256={_sha256(installer_path)}",
                    f"python={sys.version.split()[0]}",
                    "tests=preview,process",
                    *(f"verified_output={path.relative_to(SMOKE_WORK_DIR)}" for path in verified_files),
                    "result=PASS",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        print(f"Installed release verification passed. Report: {report}")
    finally:
        uninstaller = SMOKE_INSTALL_DIR / "unins000.exe"
        if uninstaller.is_file():
            _run_command(
                [uninstaller, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"]
            )
        _remove_path(SMOKE_INSTALL_DIR)


def main() -> None:
    args = _parse_args()
    _ensure_supported_python()

    app_version = _read_version()
    iscc_path = None if args.skip_inno else _find_iscc(args.iscc)

    if not args.skip_pyinstaller:
        _run_pyinstaller(console=args.console)
        _run_release_smoke_test(DIST_EXE, EXAMPLES_DIR)

    _prepare_payload()

    if args.skip_inno:
        print(f"Installer payload staged at {PAYLOAD_DIR}")
        return

    _run_inno_setup(iscc_path, app_version)

    installer_name = INSTALLER_OUTPUT_DIR / f"{APP_NAME}-setup-{app_version}.exe"
    if args.verify_installer:
        _verify_installer(installer_name)
    print(f"Installer created at {installer_name}")


if __name__ == "__main__":
    main()
