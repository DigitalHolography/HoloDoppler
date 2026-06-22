from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path


HEADER_SIZE = 64


def generate_example(path: Path, width: int = 64, height: int = 64, frames: int = 64) -> None:
    payload = bytearray(width * height * frames)
    offset = 0

    for frame in range(frames):
        phase = 2.0 * math.pi * frame / frames
        center_x = width * (0.5 + 0.12 * math.sin(phase))
        center_y = height * (0.5 + 0.08 * math.cos(phase))
        for y in range(height):
            for x in range(width):
                radius2 = (x - center_x) ** 2 + (y - center_y) ** 2
                envelope = 70.0 * math.exp(-radius2 / (2.0 * (width * 0.14) ** 2))
                fringes = 35.0 * math.sin(0.31 * x + 0.23 * y + 5.0 * phase)
                value = round(110.0 + envelope + fringes)
                payload[offset] = max(0, min(255, value))
                offset += 1

    footer = json.dumps(
        {
            "synthetic": True,
            "generator": "scripts/generate_example_holo.py",
            "description": "Deterministic HoloDoppler installer smoke-test input",
        },
        separators=(",", ":"),
    ).encode("utf-8")

    header = bytearray(HEADER_SIZE)
    header[0:4] = b"HOLO"
    struct.pack_into("<H", header, 4, 1)
    struct.pack_into("<H", header, 6, 8)
    struct.pack_into("<I", header, 8, width)
    struct.pack_into("<I", header, 12, height)
    struct.pack_into("<I", header, 16, frames)
    struct.pack_into("<Q", header, 20, HEADER_SIZE + len(payload) + len(footer))
    header[28] = 0

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + payload + footer)
    print(f"Created {path} ({path.stat().st_size} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a deterministic synthetic .holo file.")
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "examples" / "HoloDoppler_example.holo",
    )
    args = parser.parse_args()
    generate_example(args.output.resolve())


if __name__ == "__main__":
    main()
