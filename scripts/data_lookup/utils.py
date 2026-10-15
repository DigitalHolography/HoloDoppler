from pathlib import Path

def find_hd_folders(holo_paths):
    """
    Find an HD folder associated with each .holo file.

    Example:
        /data/sample.holo
        /data/sample_data/ScanHD

    Returns:
        dict[str, str | None]
    """
    result = {}

    for file_path in holo_paths:
        file_path = Path(file_path)
        hd_folder = None

        if file_path.is_file():
            parent = file_path.parent
            stem = file_path.stem

            for sibling in sorted(parent.iterdir()):
                if sibling.is_dir() and sibling.name.startswith(stem):
                    for folder in sorted(sibling.iterdir()):
                        if folder.is_dir() and folder.name.endswith("HD"):
                            hd_folder = str(folder)
                            break

                if hd_folder is not None:
                    break

        result[str(file_path)] = hd_folder

    return result
def read_existing_paths(txt_path):
    """
    Read file paths from a TXT file.
    Return only paths pointing to existing files.
    """
    txt_path = Path(txt_path)

    with txt_path.open("r", encoding="utf-8") as f:
        paths = [line.strip() for line in f if line.strip()]

    return [p for p in paths if Path(p).is_file()]

def list_files(folder_path):
    """
    Return paths of files directly inside a folder.
    Does not search subfolders.
    """
    folder = Path(folder_path)

    if not folder.is_dir():
        return []

    return [
        str(p)
        for p in sorted(folder.iterdir())
        if p.is_file()
    ]

import re

def find_preview_images(hd_folders, pattern):
    """
    Search inside:
        HD_folder/preview/png/

    Return the first filename matching the regex.

    Args:
        hd_folders: dict[file_path -> HD_folder or None]
        pattern: regex for matching filenames

    Returns:
        dict[file_path -> image_path or None]
    """
    regex = re.compile(pattern)
    result = {}

    for file_path, hd_folder in hd_folders.items():
        match_path = None

        if hd_folder is not None:
            png_folder = Path(hd_folder) / "preview" / "png"

            if png_folder.is_dir():
                for image in sorted(png_folder.iterdir()):
                    if image.is_file() and regex.search(image.name):
                        match_path = str(image)
                        break

        result[file_path] = match_path

    return result

import math
import matplotlib.pyplot as plt
from PIL import Image

def plot_holo_montage(
    holo_paths,
    pattern=r".*\.png$",
    ncols=4,
    figsize_per_image=(4, 4),
    save_path=None
):
    """
    Find preview images for .holo files and plot a montage.

    Args:
        holo_paths: list of .holo file paths
        pattern: regex to select preview images
        ncols: number of montage columns
        figsize_per_image: (width, height) per image
        save_path: optional output image path

    Returns:
        dict[file_path -> preview_image_path or None]
    """

    hd_folders = find_hd_folders(holo_paths)
    preview_images = find_preview_images(hd_folders, pattern)

    valid_images = [
        (file_path, image_path)
        for file_path, image_path in preview_images.items()
        if image_path is not None
    ]

    if not valid_images:
        print("No preview images found.")
        return preview_images

    ncols = max(1, ncols)
    nrows = math.ceil(len(valid_images) / ncols)

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(
            figsize_per_image[0] * ncols,
            figsize_per_image[1] * nrows
        ),
        squeeze=False
    )

    for ax in axes.flat:
        ax.axis("off")

    for ax, (file_path, image_path) in zip(
        axes.flat, valid_images
    ):
        try:
            with Image.open(image_path) as img:
                ax.imshow(img.convert("RGB"))

            ax.set_title(
                Path(file_path).stem,
                fontsize=10
            )

        except (OSError, ValueError) as e:
            ax.text(
                0.5, 0.5,
                f"Error:\n{e}",
                ha="center",
                va="center",
                transform=ax.transAxes
            )

    plt.tight_layout()

    if save_path is not None:
        fig.savefig(
            save_path,
            dpi=200,
            bbox_inches="tight"
        )

    plt.show()

    return preview_images