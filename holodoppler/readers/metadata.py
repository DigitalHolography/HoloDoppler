"""Normalised metadata containers for the supported acquisition formats."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CineMetadata:
    """Relevant metadata from a Phantom .cine file."""

    biHeight: int
    biWidth: int
    biCompression: int
    biSizeImage: int
    TotalImageCount: int
    OffImageOffsets: int
    FirstImageNo: int
    RealBPP: int = 12
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_cinereader_dict(cls, metadata: dict[str, Any]) -> "CineMetadata":
        known_fields = {
            "biHeight",
            "biWidth",
            "biCompression",
            "biSizeImage",
            "TotalImageCount",
            "OffImageOffsets",
            "FirstImageNo",
            "RealBPP",
        }
        kwargs = {key: metadata[key] for key in known_fields if key in metadata}
        extra = {key: value for key, value in metadata.items() if key not in known_fields}
        return cls(**kwargs, extra=extra)

    @property
    def frame_shape(self) -> tuple[int, int]:
        return self.biHeight, self.biWidth

    @property
    def num_frames(self) -> int:
        return self.TotalImageCount
