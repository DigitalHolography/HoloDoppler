"""
Holodoppler - Holographic Doppler processing library
"""

from .runtime import ensure_standard_streams

ensure_standard_streams()

from .Holodoppler import Holodoppler

__version__ = "0.1.0"
__all__ = ["Holodoppler"]
