"""Shared application locations and shipped parameter initialization."""

import os
import re
import shutil
import sys
import sysconfig
from pathlib import Path

from holodoppler.get_version import get_version

APP_NAME = "HoloDoppler"
APPDATA_SLUG = APP_NAME
DEFAULT_PARAMETERS_NAME = "default_parameters_default.yaml"
LOADED_PARAMETERS_NAME = "loaded_parameters.json"
APP_SETTINGS_NAME = "app_settings.json"
PARAMETER_SUFFIXES = {".json", ".yaml", ".yml"}
SUPPORTED_INPUT_EXTENSIONS = {".holo", ".cine"}
SUPPORTED_LIST_EXTENSIONS = {".txt"}
SUPPORTED_IMPORT_EXTENSIONS = SUPPORTED_INPUT_EXTENSIONS | SUPPORTED_LIST_EXTENSIONS


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repository_parameters_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "parameters"
    source = project_root() / "parameters"
    if (project_root() / "pyproject.toml").is_file() and source.is_dir():
        return source
    return Path(sysconfig.get_path("data")) / "share" / APP_NAME / "parameters"


def appdata_root() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def app_settings_dir() -> Path:
    version_dir = re.sub(r"[^A-Za-z0-9_.-]+", "_", get_version()).strip("._")
    return appdata_root() / APPDATA_SLUG / (version_dir or "unfound")


def initialize_parameters() -> Path:
    """Seed missing presets only, preserving user profiles and working edits."""
    source = repository_parameters_dir()
    if not source.is_dir():
        raise FileNotFoundError(f"Shipped parameters directory not found: {source}")
    base = app_settings_dir()
    if not base.exists():
        roots = [appdata_root()]
        if os.name != "nt" and sys.platform != "darwin":
            roots.append(Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"))
        candidates = [root / slug / name for root in roots
                      for slug in (APPDATA_SLUG, "holodopplerpython")
                      for name in (base.name, "current_version")]
        for candidate in candidates:
            if candidate != base and candidate.is_dir():
                shutil.copytree(candidate, base)
                break
    target = base / "parameters"
    target.mkdir(parents=True, exist_ok=True)
    for preset in source.iterdir():
        destination = target / preset.name
        if preset.is_file() and preset.suffix.lower() in PARAMETER_SUFFIXES and not destination.exists():
            shutil.copy2(preset, destination)
    default = target / DEFAULT_PARAMETERS_NAME
    if not default.is_file():
        raise FileNotFoundError(f"Default parameters not found: {default}")
    return target


def default_parameters_path() -> Path:
    return initialize_parameters() / DEFAULT_PARAMETERS_NAME
