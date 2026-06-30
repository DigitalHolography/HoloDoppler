from __future__ import annotations

import argparse
import hashlib
import json
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
APPDATA_SLUG = "holodopplerpython"

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
PARAMETERS_DIR = PROJECT_ROOT / "parameters"
DEFAULTS_DIR = SRC_DIR / "holodoppler" / "ui" / "defaults"
APP_ICON_SOURCE = SRC_DIR / "holodoppler" / "ui" / "assets" / "logo.png"
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
GENERATED_ICON_FILE = BUILD_DIR / "holodoppler.ico"
CUDA_RUNTIME_HOOK = PROJECT_ROOT / "packaging" / "pyi_rth_cuda.py"

INSTALLER_OUTPUT_DIR = DIST_DIR
DIST_APP_DIR = DIST_DIR / APP_NAME
DIST_EXE = DIST_APP_DIR / APP_EXE_NAME
PAYLOAD_PARAMETERS_DIR = PAYLOAD_DIR / "parameters"

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
    "numpy",
    "scipy",
    "matplotlib",
    "h5py",
    "opencv-python",
    "pillow",
    "tkinterdnd2",
    "sv-ttk",
    "cinereader",
    "lblprof",
    "tqdm",
    "dask",
    "PyYAML",
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

FROZEN_HIDDEN_IMPORTS = (
    "graphlib",
    "matplotlib.backends.backend_agg",
    "matplotlib.backends.backend_tkagg",
)

FROZEN_SUBMODULE_COLLECTIONS = (
    "holodoppler",
    "matlab_imresize",
    "cupy",
    "cupyx",
    "cupy_backends",
    "scipy",
    "h5py",
    "imageio",
    "cv2",
    "cinereader",
    "tkinterdnd2",
    "sv_ttk",
    "PIL",
    "matplotlib",
    "lblprof",
    "dask",
    "yaml",
)

FROZEN_DATA_COLLECTIONS = (
    "holodoppler",
    "cupy",
    "matplotlib",
    "tkinterdnd2",
    "sv_ttk",
    "PIL",
    "imageio",
    "dask",
)

FROZEN_BINARY_COLLECTIONS = (
    "cupy",
    "cv2",
    "h5py",
    "scipy",
)

FROZEN_ALL_COLLECTIONS = (
    "nvidia",
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
        help="Install the generated setup silently, optionally run smoke tests, then uninstall it.",
    )
    parser.add_argument(
        "--smoke-holo",
        type=Path,
        help="Optional real .holo/.cine input used for preview/process smoke tests.",
    )
    parser.add_argument(
        "--smoke-parameters",
        type=Path,
        help="Parameter JSON used with --smoke-holo for preview/process smoke tests.",
    )
    return parser.parse_args()


def _resolve_smoke_inputs(args: argparse.Namespace) -> tuple[Path, Path] | None:
    holo_path = args.smoke_holo
    parameters_path = args.smoke_parameters

    if holo_path is None and parameters_path is None:
        return None

    if holo_path is None or parameters_path is None:
        raise SystemExit("--smoke-holo and --smoke-parameters must be provided together.")

    resolved_holo = holo_path.expanduser().resolve()
    resolved_parameters = parameters_path.expanduser().resolve()
    missing = [
        path for path in (resolved_holo, resolved_parameters)
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(
            "Smoke test input file not found:\n"
            + "\n".join(str(path) for path in missing)
        )

    return resolved_holo, resolved_parameters


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


def _ensure_icon() -> Path:
    if not APP_ICON_SOURCE.is_file():
        raise FileNotFoundError(f"Application logo not found: {APP_ICON_SOURCE}")

    if (
        GENERATED_ICON_FILE.is_file()
        and GENERATED_ICON_FILE.stat().st_mtime >= APP_ICON_SOURCE.stat().st_mtime
    ):
        return GENERATED_ICON_FILE

    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required to generate the Windows .ico file.") from exc

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.open(APP_ICON_SOURCE).convert("RGBA")
    image.save(
        GENERATED_ICON_FILE,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    return GENERATED_ICON_FILE


def _parameter_preset_files() -> list[Path]:
    if not DEFAULTS_DIR.is_dir():
        raise FileNotFoundError(f"Bundled defaults directory not found: {DEFAULTS_DIR}")

    files = sorted(DEFAULTS_DIR.glob("*.json"), key=lambda item: item.name.lower())
    if not files:
        raise FileNotFoundError(f"No bundled parameter JSON files found in {DEFAULTS_DIR}")
    return files


def _validate_parameter_presets() -> None:
    if not PARAMETERS_DIR.is_dir():
        return

    bundled_by_name = {path.name: path for path in _parameter_preset_files()}
    repository_files = sorted(PARAMETERS_DIR.glob("*.json"), key=lambda item: item.name.lower())
    missing = [path.name for path in repository_files if path.name not in bundled_by_name]
    mismatched = [
        path.name
        for path in repository_files
        if path.name in bundled_by_name and _read_json_file(path) != _read_json_file(bundled_by_name[path.name])
    ]
    if missing or mismatched:
        details = []
        if missing:
            details.append("missing from src/holodoppler/ui/defaults: " + ", ".join(missing))
        if mismatched:
            details.append("different from parameters/: " + ", ".join(mismatched))
        raise RuntimeError("Bundled parameter presets are not in sync: " + "; ".join(details))


def _copy_parameter_presets(target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for source_path in _parameter_preset_files():
        shutil.copy2(source_path, target_dir / source_path.name)


def _copy_installer_parameters(target_dir: Path) -> None:
    if PARAMETERS_DIR.is_dir():
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(PARAMETERS_DIR, target_dir)
        return

    _copy_parameter_presets(target_dir)


def _read_json_file(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


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

            import os
            import sys
            import traceback
            from pathlib import Path

            _stdio_log = None


            def _stream_is_writable(stream: object) -> bool:
                return stream is not None and hasattr(stream, "write")


            def _configure_standard_streams() -> None:
                global _stdio_log

                if _stream_is_writable(sys.stdout) and _stream_is_writable(sys.stderr):
                    return

                try:
                    from importlib.metadata import version
                    app_version = version("holodoppler")
                except Exception:
                    app_version = "dev"

                appdata = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
                log_dir = appdata / "holodopplerpython" / app_version / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                _stdio_log = (log_dir / "runtime.log").open("a", encoding="utf-8", buffering=1)
                _stdio_log.write("\\n--- HoloDoppler runtime started ---\\n")

                if not _stream_is_writable(sys.stdout):
                    sys.stdout = _stdio_log
                if not _stream_is_writable(sys.stderr):
                    sys.stderr = _stdio_log


            _configure_standard_streams()

            from holodoppler.cli import main as cli_main
            from holodoppler.ui import UI

            def main() -> int:
                if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] == "gui"):
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

    _validate_parameter_presets()
    icon_file = _ensure_icon()
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
        "--icon",
        icon_file,
        "--runtime-hook",
        CUDA_RUNTIME_HOOK,
    ]

    for hidden_import in FROZEN_HIDDEN_IMPORTS:
        command.extend(["--hidden-import", hidden_import])

    for package in FROZEN_SUBMODULE_COLLECTIONS:
        command.extend(["--collect-submodules", package])

    for package in FROZEN_DATA_COLLECTIONS:
        command.extend(["--collect-data", package])

    for package in FROZEN_BINARY_COLLECTIONS:
        command.extend(["--collect-binaries", package])

    for package in FROZEN_ALL_COLLECTIONS:
        command.extend(["--collect-all", package])

    for distribution in FROZEN_METADATA_DISTRIBUTIONS:
        command.extend(["--copy-metadata", distribution])

    if console:
        command.append("--console")
    else:
        command.append("--windowed")

    command.append(entrypoint)

    _run_command(command)


def _prepare_payload() -> None:
    _validate_parameter_presets()

    if not DIST_EXE.is_file():
        raise FileNotFoundError(
            "PyInstaller output not found. Expected "
            f"{DIST_EXE}. Run without --skip-pyinstaller first."
        )

    if PAYLOAD_DIR.exists():
        shutil.rmtree(PAYLOAD_DIR)

    shutil.copytree(DIST_APP_DIR, PAYLOAD_DIR)
    _copy_installer_parameters(PAYLOAD_PARAMETERS_DIR)

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
    icon_file = _ensure_icon()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    INSTALLER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    script = f"""
        #define AppBaseName "{_iss_string(APP_NAME)}"
        #define AppExeName "{_iss_string(APP_EXE_NAME)}"
        #define AppVersion "{_iss_string(app_version)}"
        #define AppShortcutName "{_iss_string(f"{APP_NAME} {app_version}")}"
        #define VersionInfoVersion "{_iss_string(_version_info_version(app_version))}"
        #define AppPublisher "{_iss_string(APP_PUBLISHER)}"
        #define AppDataSlug "{_iss_string(APPDATA_SLUG)}"
        #define PayloadDir "{_iss_string(PAYLOAD_DIR)}"
        #define ParametersDir "{_iss_string(PARAMETERS_DIR)}"
        #define OutputDir "{_iss_string(INSTALLER_OUTPUT_DIR)}"
        #define AppIcon "{_iss_string(icon_file)}"

        [Setup]
        AppId={{#AppBaseName}}-{{#AppVersion}}-7C3E24DA-5E1F-4E4E-91F1-91D62A0F1B18
        AppName={{#AppShortcutName}}
        AppVersion={{#AppVersion}}
        AppVerName={{#AppShortcutName}}
        AppPublisher={{#AppPublisher}}
        DefaultDirName={{localappdata}}\\Programs\\{{#AppBaseName}}\\{{#AppVersion}}
        DefaultGroupName={{#AppShortcutName}}
        DisableProgramGroupPage=yes
        OutputDir={{#OutputDir}}
        OutputBaseFilename={{#AppBaseName}}-setup-{{#AppVersion}}
        Compression=lzma2
        SolidCompression=yes
        WizardStyle=modern
        PrivilegesRequired=lowest
        SetupIconFile={{#AppIcon}}
        UninstallDisplayName={{#AppShortcutName}}
        UninstallDisplayIcon={{app}}\\{{#AppExeName}}
        VersionInfoCompany={{#AppPublisher}}
        VersionInfoDescription={{#AppShortcutName}} installer
        VersionInfoVersion={{#VersionInfoVersion}}

        [Tasks]
        Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

        [Dirs]
        Name: "{{userappdata}}\\{{#AppDataSlug}}\\{{#AppVersion}}"; Flags: uninsneveruninstall
        Name: "{{userappdata}}\\{{#AppDataSlug}}\\{{#AppVersion}}\\logs"; Flags: uninsneveruninstall
        Name: "{{userappdata}}\\{{#AppDataSlug}}\\{{#AppVersion}}\\parameters"; Flags: uninsneveruninstall

        [Files]
        Source: "{{#PayloadDir}}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
        Source: "{{#ParametersDir}}\\*"; DestDir: "{{userappdata}}\\{{#AppDataSlug}}\\{{#AppVersion}}\\parameters"; Flags: ignoreversion onlyifdoesntexist recursesubdirs createallsubdirs uninsneveruninstall

        [Icons]
        Name: "{{autoprograms}}\\{{#AppShortcutName}}"; Filename: "{{app}}\\{{#AppExeName}}"; WorkingDir: "{{app}}"; IconFilename: "{{app}}\\{{#AppExeName}}"
        Name: "{{autodesktop}}\\{{#AppShortcutName}}"; Filename: "{{app}}\\{{#AppExeName}}"; WorkingDir: "{{app}}"; IconFilename: "{{app}}\\{{#AppExeName}}"; Tasks: desktopicon

        [Run]
        Filename: "{{app}}\\{{#AppExeName}}"; Description: "Launch {{#AppShortcutName}}"; WorkingDir: "{{app}}"; Flags: nowait postinstall skipifsilent
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


def _run_release_smoke_test(
    executable: Path,
    source_holo: Path,
    source_parameters: Path,
) -> list[Path]:
    if not executable.is_file():
        raise FileNotFoundError(f"Installed executable not found: {executable}")

    _remove_path(SMOKE_WORK_DIR)
    SMOKE_WORK_DIR.mkdir(parents=True)
    sample = SMOKE_WORK_DIR / source_holo.name
    parameters = SMOKE_WORK_DIR / source_parameters.name
    shutil.copy2(source_holo, sample)
    shutil.copy2(source_parameters, parameters)

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

    output_dir = SMOKE_WORK_DIR / sample.stem / f"{sample.stem}_HD"
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


def _verify_appdata_parameters(app_version: str) -> list[Path]:
    appdata = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    parameters_dir = appdata / APPDATA_SLUG / app_version / "parameters"
    expected = sorted(path.name for path in PARAMETERS_DIR.iterdir() if path.is_file())
    missing = [name for name in expected if not (parameters_dir / name).is_file()]
    if missing:
        raise RuntimeError(
            "Installer did not seed the expected AppData parameter files:\n"
            + "\n".join(str(parameters_dir / name) for name in missing)
        )
    return [parameters_dir / name for name in expected]


def _verify_installer(
    installer_path: Path,
    app_version: str,
    smoke_inputs: tuple[Path, Path] | None,
) -> None:
    _remove_path(SMOKE_INSTALL_DIR)
    SMOKE_INSTALL_DIR.mkdir(parents=True)
    install_dir = SMOKE_INSTALL_DIR / app_version

    install_command = [
        installer_path,
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/SP-",
        "/TASKS=",
        f"/DIR={install_dir}",
    ]

    try:
        _run_command(install_command)
        verified_files: list[Path] = []
        verified_parameters = _verify_appdata_parameters(app_version)
        tests = ["install"]
        if smoke_inputs is not None:
            verified_files = _run_release_smoke_test(
                install_dir / APP_EXE_NAME,
                *smoke_inputs,
            )
            tests.extend(["preview", "process"])

        report = DIST_DIR / "release-verification.txt"
        report.write_text(
            "\n".join(
                [
                    f"verified_at_utc={datetime.now(timezone.utc).isoformat()}",
                    f"installer={installer_path.name}",
                    f"installer_sha256={_sha256(installer_path)}",
                    f"python={sys.version.split()[0]}",
                    f"tests={','.join(tests)}",
                    *(f"verified_output={path.relative_to(SMOKE_WORK_DIR)}" for path in verified_files),
                    *(f"verified_parameter={path}" for path in verified_parameters),
                    "result=PASS",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        print(f"Installed release verification passed. Report: {report}")
    finally:
        uninstaller = install_dir / "unins000.exe"
        if uninstaller.is_file():
            _run_command(
                [uninstaller, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"]
            )
        _remove_path(SMOKE_INSTALL_DIR)


def main() -> None:
    args = _parse_args()
    _ensure_supported_python()

    app_version = _read_version()
    smoke_inputs = _resolve_smoke_inputs(args)
    iscc_path = None if args.skip_inno else _find_iscc(args.iscc)

    if not args.skip_pyinstaller:
        _run_pyinstaller(console=args.console)

    if smoke_inputs is not None:
        _run_release_smoke_test(DIST_EXE, *smoke_inputs)

    _prepare_payload()

    if args.skip_inno:
        print(f"Installer payload staged at {PAYLOAD_DIR}")
        return

    _run_inno_setup(iscc_path, app_version)

    installer_name = INSTALLER_OUTPUT_DIR / f"{APP_NAME}-setup-{app_version}.exe"
    if args.verify_installer:
        _verify_installer(installer_name, app_version, smoke_inputs)
    print(f"Installer created at {installer_name}")


if __name__ == "__main__":
    main()
