#!/usr/bin/env python3

import argparse
from pathlib import Path

import cv2
import numpy as np
import pandas as pd


def load_transforms(csv_path):
    """Load per-frame ECC affine transforms from CSV."""

    df = pd.read_csv(csv_path)

    required_columns = [
        "translation_x_px",
        "translation_y_px",
        "affine_a",
        "affine_b",
        "affine_c",
        "affine_d",
    ]

    missing = [c for c in required_columns if c not in df.columns]

    if missing:
        raise ValueError(f"Missing CSV columns: {missing}")

    transforms = []

    for _, row in df.iterrows():

        M = np.array(
            [
                [
                    row["affine_a"],
                    row["affine_b"],
                    row["translation_x_px"],
                ],
                [
                    row["affine_c"],
                    row["affine_d"],
                    row["translation_y_px"],
                ],
            ],
            dtype=np.float32,
        )

        transforms.append(M)

    return transforms


def register_video(video_path, output_path, transforms):
    """Apply ECC affine transforms to a video."""

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print(f"ERROR: Could not open {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"\nProcessing: {video_path.name}")
    print(f"  Resolution : {width} x {height}")
    print(f"  FPS        : {fps}")
    print(f"  Frames     : {frame_count}")
    print(f"  Transforms : {len(transforms)}")

    if len(transforms) < frame_count:
        print(
            f"WARNING: CSV contains only {len(transforms)} transforms "
            f"for {frame_count} video frames."
        )

    fourcc = cv2.VideoWriter_fourcc(*"XVID")

    writer = cv2.VideoWriter(
        str(output_path),
        fourcc,
        fps,
        (width, height),
    )

    if not writer.isOpened():
        cap.release()
        raise RuntimeError(
            f"Could not create output video: {output_path}"
        )

    frame_idx = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        if frame_idx >= len(transforms):
            print(
                f"WARNING: No transform for frame {frame_idx}. "
                "Stopping."
            )
            break

        M = transforms[frame_idx]

        # ---------------------------------------------------------
        # ECC convention:
        #
        # The transform describes the relationship between the
        # current frame and the reference/template frame.
        #
        # Invert it before applying with the normal OpenCV
        # warpAffine convention.
        # ---------------------------------------------------------

        M_inv = cv2.invertAffineTransform(M)

        registered = cv2.warpAffine(
            frame,
            M_inv,
            (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )

        writer.write(registered)

        frame_idx += 1

        if frame_idx % 100 == 0:
            print(
                f"  Frame {frame_idx}/{frame_count}",
                end="\r",
            )

    cap.release()
    writer.release()

    print(f"\n  Saved: {output_path}")
    print(f"  Written frames: {frame_idx}")


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Apply per-frame ECC affine registration from CSV "
            "to AVI files."
        )
    )

    parser.add_argument(
        "csv",
        type=Path,
        help="Path to the registration CSV file",
    )

    args = parser.parse_args()

    csv_path = args.csv.resolve()

    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV not found: {csv_path}"
        )

    parent_folder = csv_path.parent

    print(f"CSV:    {csv_path}")
    print(f"Folder: {parent_folder}")

    transforms = load_transforms(csv_path)

    print(
        f"Loaded {len(transforms)} affine transforms."
    )

    # Only original AVI files.
    # Already registered files are ignored.
    avi_files = sorted(
        p
        for p in parent_folder.iterdir()
        if p.is_file()
        and p.suffix.lower() == ".avi"
        and "registered" not in p.name.lower()
    )

    if not avi_files:
        print("No AVI files found.")
        return

    print(
        f"Found {len(avi_files)} AVI file(s)."
    )

    for video_path in avi_files:

        output_path = video_path.with_name(
            video_path.stem + "_registered.avi"
        )

        register_video(
            video_path,
            output_path,
            transforms,
        )

    print("\nDone.")


if __name__ == "__main__":
    main()