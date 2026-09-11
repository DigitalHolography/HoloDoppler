from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


# ============================================================
# Configuration
# ============================================================

APP_NAME = "HoloDoppler"
APP_VERSION = "0.7.1"
APP_EXE_NAME = "HoloDoppler.exe"

ROOT = Path(__file__).resolve().parent

VENV_DIR = ROOT / ".build-venv"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
INSTALLER_DIR = ROOT / "installer"

PYINSTALLER_NAME = APP_NAME

# Main Python entry point
ENTRY_POINT = ROOT / "holodoppler" / "__main__.py"

# Files/directories that should be included in the final application.
ASSETS_DIR = ROOT / "holodoppler" / "ui" / "assets"
DEFAULTS_DIR = ROOT / "holodoppler" / "ui" / "defaults"


# ============================================================
# Utilities
# ============================================================

def run(
    command: list[str],
    *,
    cwd: Path | None = None,
) -> None:
    """Run a command and stop on failure."""

    print()
    print(">" + " ".join(f' "{x}"' if " " in x else f" {x}" for x in command))

    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: "
            f"{command[0]}"
        )


def remove(path: Path) -> None:
    """Remove a file or directory if it exists."""

    if not path.exists():
        return

    print(f"Removing {path}")

    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def find_inno_setup() -> Path:
    """Locate Inno Setup's ISCC.exe."""

    candidates = [
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    ]

    # Check PATH as well.
    path_iscc = shutil.which("ISCC.exe")
    if path_iscc:
        return Path(path_iscc)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "\n"
        "Inno Setup was not found.\n\n"
        "Install Inno Setup 6 and run this script again.\n"
        "https://jrsoftware.org/isinfo.php\n"
    )


def python_executable() -> Path:
    """Return the Python executable inside the build venv."""

    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"

    return VENV_DIR / "bin" / "python"


# ============================================================
# Virtual environment
# ============================================================

def create_build_environment() -> Path:
    print()
    print("=" * 70)
    print("Creating build environment")
    print("=" * 70)

    python = python_executable()

    if not python.exists():
        print(f"Creating virtual environment: {VENV_DIR}")

        run(
            [
                sys.executable,
                "-m",
                "venv",
                str(VENV_DIR),
            ]
        )

    return python


def install_dependencies(python: Path) -> None:
    print()
    print("=" * 70)
    print("Installing build dependencies")
    print("=" * 70)

    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "setuptools",
            "wheel",
        ]
    )

    # Install the project itself.
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "-e",
            str(ROOT),
        ]
    )

    # PyInstaller is needed to create the executable.
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "pyinstaller>=6.0",
        ]
    )


# ============================================================
# PyInstaller
# ============================================================

def build_executable(python: Path) -> Path:
    print()
    print("=" * 70)
    print("Building HoloDoppler executable")
    print("=" * 70)

    if not ENTRY_POINT.exists():
        raise FileNotFoundError(
            f"Entry point not found:\n{ENTRY_POINT}"
        )

    remove(BUILD_DIR)
    remove(DIST_DIR)

    command = [
        str(python),
        "-m",
        "PyInstaller",

        "--noconfirm",
        "--clean",

        # Directory-based application.
        # This is considerably more reliable for large scientific
        # Python applications than --onefile.
        "--onedir",

        "--name",
        PYINSTALLER_NAME,

        # Collect packages that commonly need hidden modules/data.
        "--collect-all",
        "holodoppler",

        "--collect-all",
        "numpy",

        "--collect-all",
        "scipy",

        "--collect-all",
        "matplotlib",

        "--collect-all",
        "cv2",

        "--collect-all",
        "cupy",

        # Include the actual entry point.
        str(ENTRY_POINT),
    ]

    # Add UI resources explicitly.
    if ASSETS_DIR.exists():
        command += [
            "--add-data",
            f"{ASSETS_DIR};holodoppler/ui/assets",
        ]

    if DEFAULTS_DIR.exists():
        command += [
            "--add-data",
            f"{DEFAULTS_DIR};holodoppler/ui/defaults",
        ]

    run(command, cwd=ROOT)

    application_dir = DIST_DIR / APP_NAME

    if not application_dir.exists():
        raise RuntimeError(
            f"PyInstaller did not create:\n{application_dir}"
        )

    exe = application_dir / APP_EXE_NAME

    if not exe.exists():
        # PyInstaller may use the spec name for the executable.
        alternatives = list(application_dir.glob("*.exe"))

        if len(alternatives) == 1:
            exe = alternatives[0]
        else:
            raise RuntimeError(
                "Could not find the generated application executable."
            )

    print()
    print(f"Application created:")
    print(f"  {exe}")

    return application_dir


# ============================================================
# Inno Setup
# ============================================================

def create_inno_script(application_dir: Path) -> Path:
    print()
    print("=" * 70)
    print("Creating Inno Setup configuration")
    print("=" * 70)

    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)

    iss_path = ROOT / "HoloDoppler.iss"

    # Escape paths for Inno Setup.
    source_dir = str(application_dir).replace("\\", "/")

    # Optional application icon.
    icon_file = ROOT / "holodoppler" / "ui" / "assets" / "icon.ico"

    icon_section = ""

    if icon_file.exists():
        icon_path = str(icon_file).replace("\\", "/")

        icon_section = f"""
SetupIconFile={icon_path}
"""

    iss = f"""; Automatically generated by build_installer.py

#define MyAppName "{APP_NAME}"
#define MyAppVersion "{APP_VERSION}"
#define MyAppPublisher "HoloDoppler"
#define MyAppExeName "{APP_EXE_NAME}"

[Setup]
AppId={{{{A8D8C8A6-2E5B-4A3E-9D8C-7B4E3F2A1C90}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}

DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}

OutputDir={str(INSTALLER_DIR).replace("\\", "/")}
OutputBaseFilename=HoloDoppler-{APP_VERSION}-Setup

Compression=lzma2
SolidCompression=yes

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

PrivilegesRequired=admin

WizardStyle=modern

UninstallDisplayIcon={{app}}\\{{#MyAppExeName}}

{icon_section}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\\French.isl"

[Tasks]
Name: "desktopicon"; \
    Description: "Create a desktop shortcut"; \
    GroupDescription: "Additional shortcuts:"; \
    Flags: unchecked

[Files]
Source: "{source_dir}/*"; \
    DestDir: "{{app}}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\HoloDoppler"; \
    Filename: "{{app}}\\{{#MyAppExeName}}"

Name: "{{autodesktop}}\\HoloDoppler"; \
    Filename: "{{app}}\\{{#MyAppExeName}}"; \
    Tasks: desktopicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; \
    Description: "Launch HoloDoppler"; \
    Flags: nowait postinstall skipifsilent
"""

    iss_path.write_text(
        iss,
        encoding="utf-8",
    )

    print(f"Inno Setup script:")
    print(f"  {iss_path}")

    return iss_path


def build_installer(iss_path: Path) -> Path:
    print()
    print("=" * 70)
    print("Building Windows installer")
    print("=" * 70)

    iscc = find_inno_setup()

    print(f"Using Inno Setup:")
    print(f"  {iscc}")

    run(
        [
            str(iscc),
            str(iss_path),
        ],
        cwd=ROOT,
    )

    installer = (
        INSTALLER_DIR
        / f"HoloDoppler-{APP_VERSION}-Setup.exe"
    )

    if not installer.exists():
        installers = list(INSTALLER_DIR.glob("*.exe"))

        if len(installers) == 1:
            installer = installers[0]
        else:
            raise RuntimeError(
                "Inno Setup finished, but the installer executable "
                "could not be located."
            )

    return installer


# ============================================================
# Main
# ============================================================

def main() -> int:
    print()
    print("=" * 70)
    print("HoloDoppler Windows Installer Builder")
    print("=" * 70)

    if os.name != "nt":
        print()
        print("ERROR: This script must be run on Windows.")
        return 1

    try:
        # Make sure Inno Setup exists before doing the expensive
        # Python dependency installation.
        inno = find_inno_setup()

        print()
        print(f"Inno Setup found:")
        print(f"  {inno}")

        # 1. Create isolated build environment.
        python = create_build_environment()

        # 2. Install project + dependencies + PyInstaller.
        install_dependencies(python)

        # 3. Build the actual Windows application.
        application_dir = build_executable(python)

        # 4. Generate Inno Setup configuration.
        iss_path = create_inno_script(application_dir)

        # 5. Build the final installer.exe.
        installer = build_installer(iss_path)

        print()
        print("=" * 70)
        print("BUILD SUCCESSFUL")
        print("=" * 70)

        print()
        print("Application:")
        print(f"  {application_dir}")

        print()
        print("Installer:")
        print(f"  {installer}")

        print()
        print("You can now distribute:")
        print(f"  {installer}")

        return 0

    except KeyboardInterrupt:
        print()
        print("Build cancelled.")
        return 130

    except Exception as exc:
        print()
        print("=" * 70)
        print("BUILD FAILED")
        print("=" * 70)
        print()
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())