"""HoloDoppler command-line interface.

``parser`` understands arguments, ``commands`` turns them into calls on
:mod:`holodoppler.execution`. The public names are re-exported here.
"""

from __future__ import annotations

from .commands import EXIT_FAILURE, EXIT_SUCCESS, main, preview, process
from .parser import build_main_parser


__all__ = [
    "EXIT_FAILURE",
    "EXIT_SUCCESS",
    "build_main_parser",
    "main",
    "preview",
    "process",
]
