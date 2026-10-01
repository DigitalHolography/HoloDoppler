from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def create_holo(
    file_path: str | Path,
    data: np.ndarray,
    version: int = 777,
    bit_depth: int = 8,
    footer: dict | None = None,
) -> dict:
    """Create a minimal synthetic .holo file.

    Parameters
    ----------
    file_path:
        Output .holo path.
    data:
        3D array with shape (frames, height, width).
    version:
        Synthetic HOLO format version.
    bit_depth:
        Supported values are 8, 16, 32 and 64.
    footer:
        Optional JSON footer.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    HEADER_SIZE = 64

    if data.ndim != 3:
        raise ValueError(f"Expected 3D array, got {data.ndim}D array")

    if bit_depth not in (8, 16, 32, 64):
        raise ValueError(f"Unsupported bit_depth: {bit_depth}")

    height, width = data.shape[-2:]
    num_frames = data.shape[0]
    bytes_per_pixel = bit_depth // 8

    frame_size_bytes = height * width * bytes_per_pixel
    data_size = num_frames * frame_size_bytes

    footer_bytes = b""
    if footer is not None:
        try:
            footer_bytes = json.dumps(footer).encode("utf-8")
        except Exception as exc:
            raise ValueError(f"Failed to serialize footer: {exc}") from exc

    total_size = HEADER_SIZE + data_size + len(footer_bytes)

    # HOLO magic number.
    magic_number = b"HOLO"

    header = bytearray(HEADER_SIZE)
    header[0:4] = magic_number
    header[4:6] = version.to_bytes(2, "little")
    header[6:8] = bit_depth.to_bytes(2, "little")
    header[8:12] = width.to_bytes(4, "little")
    header[12:16] = height.to_bytes(4, "little")
    header[16:20] = num_frames.to_bytes(4, "little")
    header[20:28] = total_size.to_bytes(8, "little")
    header[28] = 0

    dtype_map = {
        8: np.uint8,
        16: np.uint16,
        32: np.uint32,
        64: np.uint64,
    }

    data_typed = data.astype(dtype_map[bit_depth], copy=False)

    with file_path.open("wb") as f:
        f.write(header)

        for frame_idx in range(num_frames):
            f.write(data_typed[frame_idx].flatten().tobytes())

        if footer_bytes:
            f.write(footer_bytes)

    return {
        "file_path": str(file_path),
        "version": version,
        "bit_depth": bit_depth,
        "width": width,
        "height": height,
        "num_frames": num_frames,
        "total_size": total_size,
        "has_footer": bool(footer),
    }


def make_test_data(output_dir: str | Path) -> Path:
    """Create the synthetic test .holo file."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    holo_path = output_dir / "test.holo"

    NX = NY = 32
    NT = 64

    rng = np.random.default_rng(12345)
    random_frames = rng.random((NT, NY, NX))

    footer = {
        "compute_settings": {
            "image_rendering": {
                "lambda": 8.520000278622319e-07,
                "propagation_distance": 0.5249999761581421,
                "space_transformation": "FRESNELTR",
            }
        },
        "info": {
            "pixel_pitch": {
                "x": 20e-6,
                "y": 20e-6,
            },
            "camera_fps": 37000,
        },
    }

    create_holo(
        holo_path,
        random_frames,
        version=777,
        bit_depth=8,
        footer=footer,
    )

    return holo_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic HOLO data for tests."
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="temp",
        help="Directory where test.holo will be created.",
    )

    args = parser.parse_args()

    path = make_test_data(args.output_dir)
    print(f"Created synthetic HOLO file: {path}")


if __name__ == "__main__":
    main()