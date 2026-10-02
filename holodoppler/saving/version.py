"""Version stamping for saved output bundles."""

from __future__ import annotations

import subprocess
from pathlib import Path

from holodoppler.get_version import get_version


def get_git_version() -> str:
    """Return the current Git commit, or a fallback string."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        OSError,
    ):
        return "Not Available"


def save_version_files(target_dir: Path) -> None:
    """Save version.txt and git_version.txt."""
    target_dir = Path(target_dir)
    version = f"py{get_version()}"
    git_commit = get_git_version()

    (target_dir / "version.txt").write_text(
        version + "\n",
        encoding="utf-8",
    )
    (target_dir / "git_version.txt").write_text(
        f"Git commit: {git_commit}\n"
        f"Version: {version}\n",
        encoding="utf-8",
    )
