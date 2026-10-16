"""Application version shared by the UI, CLI, and saved outputs."""
import sys
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def get_version() -> str:
    if not getattr(sys, "frozen", False):
        pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        try:
            value = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
            if isinstance(value, str) and value:
                return value
        except (OSError, ValueError, KeyError):
            pass
    try:
        return version("holodoppler")
    except PackageNotFoundError:
        return "unfound"
