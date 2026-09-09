#!/usr/bin/env python3

import argparse
from pathlib import Path

import cv2
import numpy as np


def calculate_video_average(video_path):
    """Calculate the pixel-wise temporal average of one video."""

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print(f"ERROR: Could not open {video_path}")
        return

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    sum_image = None
    n_frames = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        # Initialize using the first frame
        if sum_image is None:
            sum_image = np.zeros(
                frame.shape,
                dtype=np.float64,
            )

        # Accumulate in float64
        sum_image += frame.astype(np.float64)
        n_frames += 1

        if n_frames % 100 == 0:
            print(
                f"  {video_path.name}: "
                f"{n_frames}/{frame_count} frames",
                end="\r",
            )

    cap.release()

    if n_frames == 0:
        print(f"ERROR: No frames found in {video_path}")
        return

    # Calculate temporal mean
    average_image = sum_image / n_frames

    # Convert to 8-bit image for PNG
    average_image = np.clip(
        average_image,
        0,
        255,
    ).astype(np.uint8)

    # Output filename
    output_path = video_path.with_name(
        video_path.stem + "_average.png"
    )

    success = cv2.imwrite(
        str(output_path),
        average_image,
    )

    if not success:
        print(f"ERROR: Could not save {output_path}")
        return

    print(
        f"  {video_path.name}: "
        f"{n_frames} frames -> {output_path.name}"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Calculate a temporal average PNG for each "
            'AVI file containing "registered" in its name.'
        )
    )

    parser.add_argument(
        "folder",
        type=Path,
        help="Folder containing the AVI files",
    )

    args = parser.parse_args()

    folder = args.folder.resolve()

    if not folder.is_dir():
        raise NotADirectoryError(
            f"Not a directory: {folder}"
        )

    # Select only AVI files containing "registered"
    avi_files = sorted(
        p
        for p in folder.iterdir()
        if p.is_file()
        and p.suffix.lower() == ".avi"
        and "registered" in p.name.lower()
    )

    if not avi_files:
        print(
            f'No AVI files containing "registered" found in {folder}'
        )
        return

    print(f"Found {len(avi_files)} registered AVI file(s).\n")

    for video_path in avi_files:
        calculate_video_average(video_path)

    print("\nDone.")


if __name__ == "__main__":
    main()