from __future__ import annotations

import os
import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .constants import APPDATA_SLUG, DEFAULT_PARAMETERS_NAME


def project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "parameters").is_dir():
            return parent
    return Path.cwd()


def get_package_version() -> str:
    pyproject = project_root() / "pyproject.toml"
    if pyproject.is_file():
        for line in pyproject.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("version"):
                _key, _separator, value = stripped.partition("=")
                version_value = value.strip().strip('"').strip("'")
                if version_value:
                    return version_value

    try:
        return version("holodoppler")
    except PackageNotFoundError:
        pass
    return "dev"


def appdata_root() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def app_settings_dir() -> Path:
    version_dir = re.sub(r"[^A-Za-z0-9_.-]+", "_", get_package_version()).strip("._")
    return appdata_root() / APPDATA_SLUG / (version_dir or "dev")


def legacy_app_settings_dir() -> Path:
    return appdata_root() / APPDATA_SLUG / "current_version"


def parameters_dir() -> Path:
    """Locate presets from the checkout, installed package, or frozen application."""
    if getattr(sys, "frozen", False):
        candidates = [Path(sys.executable).resolve().parent / "parameters"]
        bundle = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        candidates.extend((bundle / "parameters", bundle / "holodoppler" / "parameters"))
    else:
        package = Path(__file__).resolve().parents[1]
        candidates = [package.parent / "parameters", package / "parameters"]
    for candidate in candidates:
        if (candidate / DEFAULT_PARAMETERS_NAME).is_file():
            return candidate
    raise FileNotFoundError("Parameter presets not found. Expected parameters/ in: "
                            + ", ".join(str(path) for path in candidates))


def logo_path() -> Path | None:
    candidates = (
        Path(__file__).resolve().parent / "assets" / "logo.png",
        project_root() / "logo.png",
        project_root() / "holodoppler_logo.png",
    )
    for path in candidates:
        if path.is_file():
            return path
    return None
