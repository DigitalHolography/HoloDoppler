from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import textwrap
import tomllib
from pathlib import Path


APP_NAME = "HoloDoppler"
APP_EXE_NAME = f"{APP_NAME}.exe"
APP_PUBLISHER = "HoloDoppler"

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
PARAMETERS_DIR = PROJECT_ROOT / "parameters"
PYPROJECT_FILE = PROJECT_ROOT / "pyproject.toml"
VERSION_FILE = PROJECT_ROOT / "version_holodoppler.txt"

DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
PYINSTALLER_WORK_DIR = BUILD_DIR / "pyinstaller"
PYINSTALLER_SPEC_DIR = BUILD_DIR
PAYLOAD_DIR = BUILD_DIR / "installer_payload"
GENERATED_ENTRYPOINT = BUILD_DIR / "_pyinstaller_holodoppler_entry.py"
GENERATED_ISS_FILE = BUILD_DIR / f"{APP_NAME}.iss"

APP_BUILD_DIR = DIST_DIR / APP_NAME
APP_BUILD_EXE = APP_BUILD_DIR / APP_EXE_NAME
LEGACY_ONEFILE_EXE = DIST_DIR / APP_EXE_NAME
INSTALLER_OUTPUT_DIR = DIST_DIR

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

PAYLOAD_EXTRA_DIRS = (
    PARAMETERS_DIR,
)

CUPY_CUDA_DLL_PATTERNS = (
    "cudart64_*.dll",
    "cublas64_*.dll",
    "cublasLt64_*.dll",
    "cufft64_*.dll",
    "cufftw64_*.dll",
    "curand64_*.dll",
    "cusolver64_*.dll",
    "cusolverMg64_*.dll",
    "cusparse64_*.dll",
    "nvfatbin_*.dll",
    "nvJitLink_*.dll",
    "nvrtc64_*.dll",
    "nvrtc-builtins64_*.dll",
)

REQUIRED_CUPY_CUDA_DLL_PATTERNS = (
    "cublas64_*.dll",
    "cublasLt64_*.dll",
    "cufft64_*.dll",
    "curand64_*.dll",
    "cusolver64_*.dll",
    "cusparse64_*.dll",
    "nvJitLink_*.dll",
    "nvrtc64_*.dll",
)

RUNTIME_METADATA_PACKAGES = (
    "holodoppler",
    "cupy-cuda13x",
    "cuda-pathfinder",
    "imageio",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the HoloDoppler Windows installer with PyInstaller and Inno Setup."
    )
    parser.add_argument(
        "--skip-pyinstaller",
        action="store_true",
        help="Reuse dist/HoloDoppler instead of rebuilding it with PyInstaller.",
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
        "--cuda-bin-dir",
        type=Path,
        help=(
            "Optional CUDA bin directory containing CuPy runtime DLLs. "
            "If omitted, CUDA_BIN_DIR, CUDA_PATH, CuPy, and PATH are searched."
        ),
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Build the executable with a visible console window.",
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
    _remove_path(APP_BUILD_DIR)
    _remove_path(LEGACY_ONEFILE_EXE)
    _remove_path(PYINSTALLER_WORK_DIR)
    _remove_path(PYINSTALLER_SPEC_DIR / f"{APP_NAME}.spec")
    _remove_path(GENERATED_ENTRYPOINT)


def _write_pyinstaller_entrypoint() -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    GENERATED_ENTRYPOINT.write_text(
        textwrap.dedent(
            """
            from __future__ import annotations

            import sys

            from holodoppler.cli import main as cli_main
            from holodoppler.ui import UI

            def main() -> int:
                if len(sys.argv) == 1:
                    UI().mainloop()
                    return 0

                return cli_main()

            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ).lstrip(),
        encoding="utf-8",
    )

    return GENERATED_ENTRYPOINT


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = path.resolve()
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(resolved)

    return unique


def _configured_cuda_bin_dirs(explicit_cuda_bin_dir: Path | None) -> list[Path]:
    candidates: list[Path] = []

    if explicit_cuda_bin_dir is not None:
        candidates.append(explicit_cuda_bin_dir.expanduser())

    env_cuda_bin_dir = os.environ.get("CUDA_BIN_DIR")
    if env_cuda_bin_dir:
        candidates.append(Path(env_cuda_bin_dir).expanduser())

    cuda_roots: list[Path] = []
    env_cuda_path = os.environ.get("CUDA_PATH")
    if env_cuda_path:
        cuda_roots.append(Path(env_cuda_path).expanduser())

    try:
        import cupy._environment as cupy_environment

        cuda_path = cupy_environment.get_cuda_path()
    except Exception:
        cuda_path = None

    if cuda_path:
        cuda_roots.append(Path(cuda_path).expanduser())

    for cuda_root in cuda_roots:
        candidates.append(cuda_root / "bin" / "x64")
        candidates.append(cuda_root / "bin")

    return _dedupe_paths(candidates)


def _path_cuda_bin_dirs() -> list[Path]:
    candidates: list[Path] = []

    for path_item in os.environ.get("PATH", "").split(os.pathsep):
        if not path_item:
            continue
        path = Path(path_item).expanduser()
        if "cuda" in str(path).lower() or "nvidia" in str(path).lower():
            candidates.append(path)

    return _dedupe_paths(candidates)


def _candidate_cuda_bin_dirs(explicit_cuda_bin_dir: Path | None) -> list[Path]:
    return _dedupe_paths(
        _configured_cuda_bin_dirs(explicit_cuda_bin_dir) + _path_cuda_bin_dirs()
    )


def _collect_cupy_cuda_dlls(cuda_bin_dirs: list[Path]) -> list[Path]:
    dlls_by_name: dict[str, Path] = {}

    for cuda_bin_dir in cuda_bin_dirs:
        if not cuda_bin_dir.is_dir():
            continue

        for pattern in CUPY_CUDA_DLL_PATTERNS:
            for dll in cuda_bin_dir.glob(pattern):
                if dll.is_file():
                    dlls_by_name.setdefault(dll.name.lower(), dll)

    return sorted(dlls_by_name.values(), key=lambda path: path.name.lower())


def _find_cupy_cuda_dlls(explicit_cuda_bin_dir: Path | None) -> list[Path]:
    configured_dlls = _collect_cupy_cuda_dlls(
        _configured_cuda_bin_dirs(explicit_cuda_bin_dir)
    )
    if configured_dlls:
        return configured_dlls

    return _collect_cupy_cuda_dlls(_path_cuda_bin_dirs())


def _copy_cupy_cuda_dlls(app_dir: Path, explicit_cuda_bin_dir: Path | None) -> None:
    internal_dir = app_dir / "_internal"
    if not internal_dir.is_dir():
        raise FileNotFoundError(f"PyInstaller internal directory not found: {internal_dir}")

    cuda_dlls = _find_cupy_cuda_dlls(explicit_cuda_bin_dir)
    if not cuda_dlls:
        searched = "\n".join(str(path) for path in _candidate_cuda_bin_dirs(explicit_cuda_bin_dir))
        raise FileNotFoundError(
            "Could not find CUDA runtime DLLs for CuPy. Install the matching CUDA Toolkit, "
            "set CUDA_PATH, set CUDA_BIN_DIR, or pass --cuda-bin-dir.\n"
            f"Searched:\n{searched}"
        )

    copied = 0
    for source in cuda_dlls:
        target = internal_dir / source.name
        if target.exists() and target.stat().st_size == source.stat().st_size:
            continue
        shutil.copy2(source, target)
        copied += 1

    print(
        f"CuPy CUDA DLLs checked: {len(cuda_dlls)} found, "
        f"{copied} copied into {internal_dir}"
    )


def _validate_cupy_bundle(app_dir: Path) -> None:
    internal_dir = app_dir / "_internal"
    cupy_dir = internal_dir / "cupy"
    cupyx_dir = internal_dir / "cupyx"

    if not cupy_dir.is_dir():
        raise FileNotFoundError(f"Bundled CuPy package directory not found: {cupy_dir}")
    if not cupyx_dir.is_dir():
        raise FileNotFoundError(f"Bundled CuPy SciPy package directory not found: {cupyx_dir}")

    cupy_extension_count = sum(1 for _ in cupy_dir.rglob("*.pyd"))
    if cupy_extension_count == 0:
        raise RuntimeError(f"No bundled CuPy extension modules found under {cupy_dir}")

    dll_names = [path.name for path in internal_dir.glob("*.dll")]
    missing = [
        pattern
        for pattern in REQUIRED_CUPY_CUDA_DLL_PATTERNS
        if not any(fnmatch.fnmatchcase(name.lower(), pattern.lower()) for name in dll_names)
    ]
    if missing:
        raise RuntimeError(
            "The PyInstaller bundle is missing required CuPy CUDA DLLs: "
            + ", ".join(missing)
        )

    bundled_cuda_dll_count = sum(
        1
        for name in dll_names
        if any(fnmatch.fnmatchcase(name.lower(), pattern.lower()) for pattern in CUPY_CUDA_DLL_PATTERNS)
    )
    print(
        f"CuPy bundle validated: {cupy_extension_count} CuPy extension modules, "
        f"{bundled_cuda_dll_count} CUDA DLLs."
    )


def _normalize_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _metadata_distribution_name(dist_info_dir: Path) -> str | None:
    metadata_file = dist_info_dir / "METADATA"
    if not metadata_file.is_file():
        return None

    for line in metadata_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith("name:"):
            return line.split(":", 1)[1].strip()

    return None


def _validate_runtime_metadata(app_dir: Path) -> None:
    internal_dir = app_dir / "_internal"
    metadata_names = {
        _normalize_distribution_name(name)
        for dist_info_dir in internal_dir.glob("*.dist-info")
        if (name := _metadata_distribution_name(dist_info_dir))
    }
    missing = [
        package
        for package in RUNTIME_METADATA_PACKAGES
        if _normalize_distribution_name(package) not in metadata_names
    ]

    if missing:
        raise RuntimeError(
            "The PyInstaller bundle is missing required package metadata: "
            + ", ".join(missing)
        )

    print(f"Runtime metadata validated: {', '.join(RUNTIME_METADATA_PACKAGES)}.")


def _run_pyinstaller(console: bool, explicit_cuda_bin_dir: Path | None) -> None:
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
        "--specpath",
        PYINSTALLER_SPEC_DIR,
        "--paths",
        SRC_DIR,
        "--collect-submodules",
        "holodoppler",
        "--collect-submodules",
        "cupy",
        "--collect-submodules",
        "cupyx",
        "--collect-submodules",
        "cupy_backends",
        "--collect-submodules",
        "scipy",
        "--collect-submodules",
        "h5py",
        "--collect-submodules",
        "imageio",
        "--collect-submodules",
        "tkinterdnd2",
        "--collect-data",
        "cupy",
        "--collect-data",
        "cupyx",
        "--collect-data",
        "tkinterdnd2",
    ]

    for package in RUNTIME_METADATA_PACKAGES:
        command.extend(("--copy-metadata", package))

    if console:
        command.append("--console")
    else:
        command.append("--windowed")

    command.append(entrypoint)

    _run_command(command)
    _copy_cupy_cuda_dlls(APP_BUILD_DIR, explicit_cuda_bin_dir)
    _validate_cupy_bundle(APP_BUILD_DIR)
    _validate_runtime_metadata(APP_BUILD_DIR)


def _copy_extra_payload_items() -> None:
    for extra_file in PAYLOAD_EXTRA_FILES:
        if extra_file.exists():
            shutil.copy2(extra_file, PAYLOAD_DIR / extra_file.name)

    for extra_dir in PAYLOAD_EXTRA_DIRS:
        if extra_dir.exists():
            target_dir = PAYLOAD_DIR / extra_dir.name
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(extra_dir, target_dir)


def _prepare_payload(explicit_cuda_bin_dir: Path | None) -> None:
    if not APP_BUILD_EXE.is_file():
        raise FileNotFoundError(
            "PyInstaller output not found. Expected "
            f"{APP_BUILD_EXE}. Run without --skip-pyinstaller first."
        )

    _copy_cupy_cuda_dlls(APP_BUILD_DIR, explicit_cuda_bin_dir)
    _validate_cupy_bundle(APP_BUILD_DIR)
    _validate_runtime_metadata(APP_BUILD_DIR)

    if PAYLOAD_DIR.exists():
        shutil.rmtree(PAYLOAD_DIR)

    shutil.copytree(APP_BUILD_DIR, PAYLOAD_DIR)
    _copy_extra_payload_items()
    _validate_cupy_bundle(PAYLOAD_DIR)
    _validate_runtime_metadata(PAYLOAD_DIR)
    print(f"Installer payload staged at {PAYLOAD_DIR}")


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
        DiskSpanning=no
        WizardStyle=modern
        PrivilegesRequired=lowest
        ArchitecturesAllowed=x64compatible
        ArchitecturesInstallIn64BitMode=x64compatible
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
        Name: "{{autoprograms}}\\{{#AppName}}"; Filename: "{{app}}\\{{#AppExeName}}"; WorkingDir: "{{app}}"
        Name: "{{autodesktop}}\\{{#AppName}}"; Filename: "{{app}}\\{{#AppExeName}}"; WorkingDir: "{{app}}"; Tasks: desktopicon

        [Run]
        Filename: "{{app}}\\{{#AppExeName}}"; WorkingDir: "{{app}}"; Description: "Launch {{#AppName}}"; Flags: nowait postinstall skipifsilent
    """

    GENERATED_ISS_FILE.write_text(textwrap.dedent(script).lstrip(), encoding="utf-8")
    return GENERATED_ISS_FILE


def _run_inno_setup(iscc_path: Path, app_version: str) -> None:
    iss_file = _write_inno_script(app_version)
    _run_command([iscc_path, iss_file])


def main() -> None:
    args = _parse_args()
    _ensure_supported_python()

    app_version = _read_version()
    iscc_path = None if args.skip_inno else _find_iscc(args.iscc)

    if not args.skip_pyinstaller:
        _run_pyinstaller(console=args.console, explicit_cuda_bin_dir=args.cuda_bin_dir)

    _prepare_payload(explicit_cuda_bin_dir=args.cuda_bin_dir)

    if args.skip_inno:
        return

    _run_inno_setup(iscc_path, app_version)

    installer_name = INSTALLER_OUTPUT_DIR / f"{APP_NAME}-setup-{app_version}.exe"
    print(f"Installer created at {installer_name}")


if __name__ == "__main__":
    main()
