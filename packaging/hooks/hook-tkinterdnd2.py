"""Bundle tkdnd for this process architecture, including Tcl 8 and Tcl 9.

tkinterdnd2 chooses the Tcl ABI when the window is created. Keep both ABI
variants, where provided, so newer Python builds do not lose drag and drop.
Other operating systems and CPU architectures are never used by this build.
"""

import os
from pathlib import Path
import platform

from PyInstaller.utils.hooks import get_package_paths, logger


def _collect_platform_subdirs(system, machine):
    if system == "Windows":
        # Match tkinterdnd2: the host CPU can differ from the Python process.
        machine = os.environ.get("PROCESSOR_ARCHITECTURE", machine)

    platforms = {
        "Windows": {"AMD64": "win-x64", "ARM64": "win-arm64", "x86": "win-x86"},
        "Linux": {"x86_64": "linux-x64", "aarch64": "linux-arm64"},
        "Darwin": {"x86_64": "osx-x64", "arm64": "osx-arm64"},
    }
    directory = platforms.get(system, {}).get(machine)
    suffix = {"Windows": "*.dll", "Linux": "*.so", "Darwin": "*.dylib"}.get(system)
    if directory is None or suffix is None:
        logger.warning("hook-tkinterdnd2: unsupported platform (%s, %s)", system, machine)
        return [], []

    _, package_dir = get_package_paths("tkinterdnd2")
    package_dir = Path(package_dir)
    datas, binaries = [], []
    for name in (directory, f"{directory}-tcl9"):
        source_dir = package_dir / "tkdnd" / name
        destination = str(Path("tkinterdnd2") / "tkdnd" / name)
        datas.extend((str(path), destination) for path in sorted(source_dir.glob("*.tcl")))
        binaries.extend((str(path), destination) for path in sorted(source_dir.glob(suffix)))

    if not binaries:
        logger.warning("hook-tkinterdnd2: no tkdnd library found for %s", directory)
    return datas, binaries


datas, binaries = _collect_platform_subdirs(platform.system(), platform.machine())
