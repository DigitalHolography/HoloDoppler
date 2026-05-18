from __future__ import annotations

import sys


class _NullTextStream:
    encoding = "utf-8"
    errors = "replace"

    def write(self, text: str) -> int:
        return len(text)

    def flush(self) -> None:
        return None

    def readline(self) -> str:
        return ""

    def isatty(self) -> bool:
        return False


def ensure_standard_streams() -> None:
    """Provide safe stdout/stderr streams in PyInstaller windowed builds."""

    if sys.stdout is None:
        sys.stdout = _NullTextStream()
    if sys.stderr is None:
        sys.stderr = _NullTextStream()
    if sys.stdin is None:
        sys.stdin = _NullTextStream()
