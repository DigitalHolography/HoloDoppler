"""Non-destructive checks before replacing existing results."""
from __future__ import annotations

import ctypes
import os
from pathlib import Path


def _check_windows_access(path: Path) -> None:
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD,
                       wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    # DELETE access, all sharing modes, OPEN_EXISTING, directory/reparse flags.
    handle = create(str(path.absolute()), 0x10000, 7, None, 3,
                    0x02000000 | 0x00200000, None)
    if handle == ctypes.c_void_p(-1).value:
        code = ctypes.get_last_error()
        if code in (5, 32, 33):
            raise PermissionError(code, "Cannot replace existing results; close any "
                                  "application using this path and check permissions", str(path))
        raise OSError(code, ctypes.FormatError(code), str(path))
    close(handle)


def check_output_access(path: str | Path) -> None:
    """Check an existing tree before erase/archive without changing its contents.

    Windows probes delete/rename access. Other platforms check directory
    permissions, where open files normally do not prevent removal. Links and
    junctions are checked but never traversed. This is best effort: access can
    change between this check and the subsequent filesystem operation.
    """
    path = Path(path)
    path.lstat()  # Do not silently skip missing or inaccessible entries.
    if os.name == "nt":
        _check_windows_access(path)
    elif not os.access(path.parent, os.W_OK | os.X_OK):
        raise PermissionError(13, "Cannot replace results: parent directory is inaccessible", str(path))
    if path.is_symlink() or path.is_junction():
        return
    if path.is_dir():
        if os.name != "nt" and not os.access(path, os.R_OK | os.W_OK | os.X_OK):
            raise PermissionError(13, "Cannot traverse or modify results directory", str(path))
        for child in path.iterdir():
            check_output_access(child)
