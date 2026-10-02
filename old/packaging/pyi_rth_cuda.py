from __future__ import annotations

import os
import sys
from pathlib import Path


_cuda_dll_directory = None


def _configure_bundled_cuda() -> None:
    global _cuda_dll_directory

    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    cuda_root = bundle_root / "nvidia" / "cu13"
    cuda_bin = cuda_root / "bin" / "x86_64"
    if not cuda_bin.is_dir():
        return

    os.environ["CUDA_PATH"] = str(cuda_root)
    os.environ["CUDA_HOME"] = str(cuda_root)
    os.environ["PATH"] = f"{cuda_bin}{os.pathsep}{os.environ.get('PATH', '')}"
    if os.name == "nt" and hasattr(os, "add_dll_directory"):
        _cuda_dll_directory = os.add_dll_directory(str(cuda_bin))


_configure_bundled_cuda()
