"""Process two generated .holo recordings using the container's default settings."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

import h5py
import numpy as np

from holodoppler import cli


def create_fixture(workspace: Path, config: Path) -> None:
    for folder in ("input", "config", "output"):
        (workspace / folder).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config, workspace / "config" / "parameters.yaml")
    rng = np.random.default_rng(42)
    for index, name in enumerate(("first recording.holo", "second recording.holo")):
        frames = rng.integers(100, 4_000, size=(256, 64, 64), dtype=np.uint16)
        header = bytearray(64)
        header[0:4] = b"HOLO"
        for start, stop, value in (
            (4, 6, 7), (6, 8, 16), (8, 12, 64), (12, 16, 64),
            (16, 20, 256), (20, 28, frames.nbytes),
        ):
            header[start:stop] = value.to_bytes(stop - start, "little")
        footer = {
            "compute_settings": {"image_rendering": {"propagation_distance": 0.1 + index * 0.02}},
            "info": {"pixel_pitch": {"y": 6.5, "x": 6.5}, "camera_fps": 50_000 + index * 1_000},
        }
        path = workspace / "input" / name
        with path.open("wb") as recording:
            recording.write(header)
            recording.write(frames.tobytes())
            recording.write(json.dumps(footer).encode("utf-8"))


def verify_outputs(workspace: Path) -> None:
    outputs = list((workspace / "output").rglob("*.h5"))
    assert len(outputs) == 2, f"Expected two HDF5 outputs, got {outputs}"
    sampling_rates = set()
    for path in outputs:
        with h5py.File(path) as handle:
            assert handle["moment0"].shape == (1, 64, 64)
            assert np.isfinite(handle["moment0"][...]).all()
            metadata = json.loads(handle["HD_parameters"][()].decode())
            sampling_rates.add(metadata["sampling_freq"])
    assert sampling_rates == {50_000, 51_000}, "Acquisition settings leaked between recordings"
    print("Verified two HDF5 outputs with independent recording metadata.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--config", type=Path, default=Path("/config/parameters.yaml"))
    parser.add_argument("--create-only", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--gpu", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify_outputs(args.workspace)
        return
    create_fixture(args.workspace, args.config)
    if args.create_only:
        return
    protected = [args.workspace / "config" / "parameters.yaml", *list((args.workspace / "input").iterdir())]
    fingerprints = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}
    arguments = ["process", "--folder", str(args.workspace / "input"),
                 str(args.workspace / "config" / "parameters.yaml"),
                 "--output-dir", str(args.workspace / "output")]
    if args.gpu:
        arguments.append("--require-gpu")
    assert cli.main(arguments) == 0, "Folder processing failed"
    verify_outputs(args.workspace)
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == value for path, value in fingerprints.items())
    if hasattr(os, "getuid"):
        assert all(path.stat().st_uid == os.getuid() for path in (args.workspace / "output").rglob("*"))
    print("Inputs and settings preserved; results owned by the processing user.")


if __name__ == "__main__":
    main()
