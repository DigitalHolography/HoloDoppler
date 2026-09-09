#!/usr/bin/env python3

"""
Generate publication-quality EPS + PNG plots from HDF5 + CSV + JSON data.

Expected folder structure:

input_folder/
├── h5/
│   └── first_file.h5
├── avi/
│   └── first_file.csv
└── json/
    └── parameters_holodoppler.json

HDF5 datasets:

    /band_0_15000_18300
        shape: (nt, ny, nx)

    /shack_hartmann_zernike_coefs
        shape: (nt, 3)

CSV columns:

    time_s
    translation_x_px
    translation_y_px
    rotation_deg
    scale
    affine_a
    affine_b
    affine_c
    affine_d
    shear_x
    shear_y
    ECC

JSON:

    {
        "time_stride": ...,
        "sampling_freq": ...
    }

Time is calculated from the JSON parameters:

    dt = time_stride / sampling_freq
    time[i] = i * dt

The CSV time_s column is NOT used.

Plots:

    Fig 1: Scale
    Fig 2: Rotation
    Fig 3: Translation
    Fig 4: Doppler signal
    Fig 5: Z4, Z5, Z6

Output:

    EPS + PNG for every figure.

Features:

    - grayscale only
    - scatter for all signals except Doppler
    - line for Doppler
    - golden-ratio aspect ratio = 1.68
    - alternating gray/white background
    - configurable font size
    - configurable switch delay
    - optional fixed Y limits for every figure
"""

import argparse
import csv
import json
from pathlib import Path

import h5py
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# Configuration
# ============================================================

FONT_SIZE = 14

# aspect ratio
GOLDEN_RATIO = 2.9

# All figures have exactly the same dimensions.
FIGURE_WIDTH = 6.72
FIGURE_HEIGHT = FIGURE_WIDTH / GOLDEN_RATIO


# ============================================================
# Y-axis limits
# ============================================================

# Set to (YMIN, YMAX) to use fixed limits.
# Set to None to let Matplotlib determine the limits automatically.

YLIM_SCALE = None
YLIM_ROTATION = None
YLIM_TRANSLATION = None
YLIM_DOPPLER = None
YLIM_ZERNIKE = None

# Examples:
#
YLIM_SCALE = (0.99, 1.050)
YLIM_ROTATION = (-1.0, 1.0)
YLIM_TRANSLATION = (-18.0, 16.0)
# YLIM_DOPPLER = (0.8, 1.4)
# YLIM_ZERNIKE = (-0.9, 0.3)


# ============================================================
# Alternating background
# ============================================================

# Time in seconds before switching background.
#
# Example with SWITCH_DELAY = 1.0:
#
#   0 - 1 s : white
#   1 - 2 s : gray
#   2 - 3 s : white
#   3 - 4 s : gray
#   ...

SWITCH_DELAY = 2.0

# Grayscale intensity:
#   0 = black
#   1 = white

BACKGROUND_GRAY = 0.92
BACKGROUND_ALPHA = 1.0


# ============================================================
# Doppler disk
# ============================================================

DISK_RADIUS_FRACTION = 0.90


# ============================================================
# Grayscale colors
# ============================================================

COLOR_BLACK = "0.0"
COLOR_MEDIUM = "0.50"
COLOR_LIGHT = "0.70"


# ============================================================
# Plot appearance
# ============================================================

SCATTER_SIZE = 10
SCATTER_ALPHA = 0.75
LINE_WIDTH = 1.5


# ============================================================
# Matplotlib configuration
# ============================================================

def configure_matplotlib(font_size):
    """Configure Matplotlib for publication-quality output."""

    plt.rcParams.update({
        "font.size": font_size,
        "axes.labelsize": font_size,
        "xtick.labelsize": font_size * 0.9,
        "ytick.labelsize": font_size * 0.9,
        "legend.fontsize": font_size * 0.85,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "figure.dpi": 150,
        "savefig.dpi": 300,

        # TrueType fonts in EPS
        "ps.fonttype": 42,

        "axes.unicode_minus": False,
    })


# ============================================================
# File discovery
# ============================================================

def find_first_file(folder, extension):
    """Return the first file with the requested extension."""

    files = sorted(folder.glob(f"*{extension}"))

    if not files:
        raise FileNotFoundError(
            f"No '{extension}' file found in: {folder}"
        )

    return files[0]


# ============================================================
# JSON loading
# ============================================================

def load_json_parameters(json_path):
    """
    Load time_stride and sampling_freq from JSON.
    """

    print(f"Reading JSON: {json_path}")

    with open(json_path, "r") as f:
        data = json.load(f)

    required = [
        "time_stride",
        "sampling_freq",
    ]

    missing = [
        key
        for key in required
        if key not in data
    ]

    if missing:
        raise KeyError(
            "Missing JSON parameters: "
            + ", ".join(missing)
        )

    time_stride = float(
        data["time_stride"]
    )

    sampling_freq = float(
        data["sampling_freq"]
    )

    if time_stride <= 0:
        raise ValueError(
            f"time_stride must be > 0, got "
            f"{time_stride}"
        )

    if sampling_freq <= 0:
        raise ValueError(
            f"sampling_freq must be > 0, got "
            f"{sampling_freq}"
        )

    dt = time_stride / sampling_freq

    print(
        f"time_stride  = {time_stride}"
    )

    print(
        f"sampling_freq = {sampling_freq} Hz"
    )

    print(
        f"time step     = {dt} s"
    )

    return time_stride, sampling_freq, dt


# ============================================================
# Time calculation
# ============================================================

def calculate_time(nt, dt):
    """
    Calculate the time vector.

    Frame 0 is at t = 0.

    Therefore:

        t[i] = i * dt
    """

    return np.arange(
        nt,
        dtype=float,
    ) * dt


# ============================================================
# CSV loading
# ============================================================

def load_registration_csv(csv_path):
    """
    Load registration CSV using only Python's standard library.

    The CSV time_s column is intentionally ignored.
    """

    print(f"Reading CSV: {csv_path}")

    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError(
                "CSV file has no header."
            )

        required_columns = [
            "translation_x_px",
            "translation_y_px",
            "rotation_deg",
            "scale",
        ]

        missing = [
            column
            for column in required_columns
            if column not in reader.fieldnames
        ]

        if missing:
            raise KeyError(
                "Missing CSV columns: "
                + ", ".join(missing)
            )

        data = {
            column: []
            for column in reader.fieldnames
        }

        for row in reader:
            for column in reader.fieldnames:
                value = row[column]

                if value == "":
                    data[column].append(np.nan)
                else:
                    data[column].append(
                        float(value)
                    )

    return {
        column: np.asarray(
            values,
            dtype=float,
        )
        for column, values in data.items()
    }


# ============================================================
# HDF5 loading
# ============================================================

def load_hdf5_data(h5_path):
    """Load band_0_15000_18300 and Zernike datasets."""

    print(f"Reading HDF5: {h5_path}")

    with h5py.File(h5_path, "r") as h5:

        if "/band_0_15000_18300" not in h5:
            raise KeyError(
                "Dataset '/band_0_15000_18300' not found."
            )

        if (
            "/shack_hartmann_zernike_coefs"
            not in h5
        ):
            raise KeyError(
                "Dataset "
                "'/shack_hartmann_zernike_coefs' "
                "not found."
            )

        band_0_15000_18300 = h5[
            "/band_0_15000_18300"
        ][:]

        zernike = h5[
            "/shack_hartmann_zernike_coefs"
        ][:]

    return band_0_15000_18300, zernike


# ============================================================
# Centered disk
# ============================================================

def make_centered_disk(
    ny,
    nx,
    radius_fraction=0.90,
):
    """
    Create a centered circular mask.

    Maximum centered radius:

        min(nx, ny) / 2

    Selected radius:

        radius_fraction * maximum radius
    """

    y, x = np.ogrid[:ny, :nx]

    cx = (nx - 1) / 2.0
    cy = (ny - 1) / 2.0

    max_radius = min(nx, ny) / 2.0

    radius = (
        radius_fraction
        * max_radius
    )

    return (
        (x - cx) ** 2
        + (y - cy) ** 2
        <= radius ** 2
    )


def compute_doppler_signal(
    band_0_15000_18300,
    radius_fraction=0.90,
):
    """
    Average band_0_15000_18300 inside the centered disk.

    Returns one value per time frame.
    """

    if band_0_15000_18300.ndim != 3:
        raise ValueError(
            "Expected band_0_15000_18300 shape "
            "(nt, ny, nx), got "
            f"{band_0_15000_18300.shape}"
        )

    _, ny, nx = band_0_15000_18300.shape

    mask = make_centered_disk(
        ny,
        nx,
        radius_fraction,
    )

    pixels = band_0_15000_18300[:, mask]

    return np.mean(
        pixels,
        axis=1,
    )


# ============================================================
# Figure creation
# ============================================================

def create_figure():
    """
    Create a figure with exactly 1.68 aspect ratio.
    """

    return plt.subplots(
        figsize=(
            FIGURE_WIDTH,
            FIGURE_HEIGHT,
        )
    )


# ============================================================
# Alternating background
# ============================================================

def add_switch_background(
    ax,
    time,
    switch_delay=1.0,
):
    """
    Add alternating gray/white background.

    Starts with white.

    For switch_delay = 1 s:

        0-1 s : white
        1-2 s : gray
        2-3 s : white
        3-4 s : gray
        ...
    """

    if switch_delay <= 0:
        raise ValueError(
            "switch_delay must be > 0."
        )

    if len(time) == 0:
        return

    t_min = float(
        np.min(time)
    )

    t_max = float(
        np.max(time)
    )

    if t_max <= t_min:
        return

    first_boundary = (
        np.floor(
            t_min / switch_delay
        )
        * switch_delay
    )

    boundaries = np.arange(
        first_boundary,
        t_max + switch_delay,
        switch_delay,
    )

    for i in range(
        len(boundaries) - 1
    ):

        left = boundaries[i]
        right = boundaries[i + 1]

        state = (
            int(
                np.floor(
                    left / switch_delay
                )
            )
            % 2
        )

        # State 1 = gray
        if state == 1:
            ax.axvspan(
                max(left, t_min),
                min(right, t_max),
                facecolor=str(
                    BACKGROUND_GRAY
                ),
                alpha=BACKGROUND_ALPHA,
                edgecolor="none",
                zorder=0,
            )


# ============================================================
# Common axis formatting
# ============================================================

def configure_axes(
    ax,
    time,
    switch_delay,
    ylim=None,
):
    """Apply common axis formatting."""

    add_switch_background(
        ax,
        time,
        switch_delay,
    )

    ax.grid(
        True,
        which="major",
        linestyle=":",
        linewidth=0.5,
        color=COLOR_LIGHT,
        zorder=1,
    )

    ax.margins(x=0.02)

    # Apply optional Y-axis limits.
    if ylim is not None:
        if len(ylim) != 2:
            raise ValueError(
                "ylim must contain exactly "
                "two values: (ymin, ymax)."
            )

        ymin, ymax = ylim

        if ymin >= ymax:
            raise ValueError(
                f"Invalid ylim={ylim}. "
                "ymin must be smaller than ymax."
            )

        ax.set_ylim(ymin, ymax)

    # Make sure data is above background.
    for collection in ax.collections:
        collection.set_zorder(2)

    for line in ax.lines:
        line.set_zorder(3)


# ============================================================
# Save EPS + PNG
# ============================================================

def save_figure(
    fig,
    output_folder,
    basename,
):
    """Save one figure as EPS and PNG."""

    eps_path = (
        output_folder
        / f"{basename}.eps"
    )

    png_path = (
        output_folder
        / f"{basename}.png"
    )

    fig.savefig(
        eps_path,
        format="eps",
        bbox_inches="tight",
    )

    fig.savefig(
        png_path,
        format="png",
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Saved: {eps_path}")
    print(f"Saved: {png_path}")


# ============================================================
# Main plotting routine
# ============================================================

def generate_plots(
    input_folder,
    output_folder,
    font_size,
    switch_delay,
):
    """Load all data and generate the five figures."""

    configure_matplotlib(
        font_size
    )

    input_folder = Path(
        input_folder
    )

    output_folder = Path(
        output_folder
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Input directories
    # --------------------------------------------------------

    h5_folder = (
        input_folder / "h5"
    )

    avi_folder = (
        input_folder / "avi"
    )

    json_folder = (
        input_folder / "json"
    )

    if not h5_folder.exists():
        raise FileNotFoundError(
            f"Missing folder: {h5_folder}"
        )

    if not avi_folder.exists():
        raise FileNotFoundError(
            f"Missing folder: {avi_folder}"
        )

    if not json_folder.exists():
        raise FileNotFoundError(
            f"Missing folder: {json_folder}"
        )

    # --------------------------------------------------------
    # First files
    # --------------------------------------------------------

    h5_path = find_first_file(
        h5_folder,
        ".h5",
    )

    csv_path = find_first_file(
        avi_folder,
        ".csv",
    )

    json_path = (
        json_folder
        / "parameters_holodoppler.json"
    )

    if not json_path.exists():
        raise FileNotFoundError(
            f"JSON file not found: {json_path}"
        )

    # --------------------------------------------------------
    # Load JSON timing parameters
    # --------------------------------------------------------

    (
        time_stride,
        sampling_freq,
        dt,
    ) = load_json_parameters(
        json_path
    )

    # --------------------------------------------------------
    # Load HDF5
    # --------------------------------------------------------

    (
        band_0_15000_18300,
        zernike,
    ) = load_hdf5_data(
        h5_path
    )

    # --------------------------------------------------------
    # Load CSV
    # --------------------------------------------------------

    registration = (
        load_registration_csv(
            csv_path
        )
    )

    # --------------------------------------------------------
    # Validate data dimensions
    # --------------------------------------------------------

    if band_0_15000_18300.ndim != 3:
        raise ValueError(
            "band_0_15000_18300 must have shape "
            "(nt, ny, nx)."
        )

    if (
        zernike.ndim != 2
        or zernike.shape[1] != 3
    ):
        raise ValueError(
            "Zernike coefficients must "
            "have shape (nt, 3)."
        )

    n_moment0 = (
        band_0_15000_18300.shape[0]
    )

    n_zernike = zernike.shape[0]

    n_csv = len(
        registration[
            "translation_x_px"
        ]
    )

    print()

    print("Signal lengths:")

    print(
        f"  band_0_15000_18300 : {n_moment0}"
    )

    print(
        f"  Zernike            : {n_zernike}"
    )

    print(
        f"  translation         : {n_csv}"
    )

    # --------------------------------------------------------
    # All signals should have exactly the same length.
    # --------------------------------------------------------

    if not (
        n_moment0
        == n_zernike
        == n_csv
    ):
        raise ValueError(
            "\nSignal lengths do not match:\n"
            f"  band_0_15000_18300 = {n_moment0}\n"
            f"  Zernike            = {n_zernike}\n"
            f"  CSV                = {n_csv}\n"
            "\n"
            "All signals are expected to have "
            "the same number of samples."
        )

    nt = n_moment0

    # --------------------------------------------------------
    # Calculate time.
    #
    # CSV time_s is NOT used.
    # --------------------------------------------------------

    time = calculate_time(
        nt,
        dt,
    )

    print(
        f"\nNumber of samples : {nt}"
    )

    print(
        f"Time step         : {dt:.9g} s"
    )

    print(
        f"Total duration    : "
        f"{time[-1]:.9g} s"
    )

    # --------------------------------------------------------
    # Doppler signal
    # --------------------------------------------------------

    doppler = (
        compute_doppler_signal(
            band_0_15000_18300,
            radius_fraction=(
                DISK_RADIUS_FRACTION
            ),
        )
    )

    # --------------------------------------------------------
    # Registration signals
    # --------------------------------------------------------

    translation_x = (
        registration[
            "translation_x_px"
        ]
    )

    translation_y = (
        registration[
            "translation_y_px"
        ]
    )

    rotation = (
        registration[
            "rotation_deg"
        ]
    )

    scale = (
        registration[
            "scale"
        ]
    )

    # --------------------------------------------------------
    # Zernike coefficients
    # --------------------------------------------------------

    z4 = zernike[:, 0]
    z5 = zernike[:, 1]
    z6 = zernike[:, 2]

    # ========================================================
    # Fig 1 — Scale
    # ========================================================

    fig, ax = create_figure()

    ax.scatter(
        time,
        scale,
        s=SCATTER_SIZE,
        color=COLOR_BLACK,
        alpha=SCATTER_ALPHA,
        edgecolors="none",
    )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Scale")

    configure_axes(
        ax,
        time,
        switch_delay,
        ylim=YLIM_SCALE,
    )

    fig.tight_layout()

    save_figure(
        fig,
        output_folder,
        "fig1_scale",
    )

    # ========================================================
    # Fig 2 — Rotation
    # ========================================================

    fig, ax = create_figure()

    ax.scatter(
        time,
        rotation,
        s=SCATTER_SIZE,
        color=COLOR_BLACK,
        alpha=SCATTER_ALPHA,
        edgecolors="none",
    )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Rotation (deg)")

    configure_axes(
        ax,
        time,
        switch_delay,
        ylim=YLIM_ROTATION,
    )

    fig.tight_layout()

    save_figure(
        fig,
        output_folder,
        "fig2_rotation",
    )

    # ========================================================
    # Fig 3 — Translation
    # ========================================================

    fig, ax = create_figure()

    ax.scatter(
        time,
        translation_x,
        s=SCATTER_SIZE,
        color=COLOR_BLACK,
        alpha=SCATTER_ALPHA,
        edgecolors="none",
        label=r"$x$",
    )

    ax.scatter(
        time,
        translation_y,
        s=SCATTER_SIZE,
        color=COLOR_MEDIUM,
        alpha=SCATTER_ALPHA,
        edgecolors="none",
        label=r"$y$",
    )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Translation (px)")

    ax.legend(
        frameon=False
    )

    configure_axes(
        ax,
        time,
        switch_delay,
        ylim=YLIM_TRANSLATION,
    )

    fig.tight_layout()

    save_figure(
        fig,
        output_folder,
        "fig3_translation",
    )

    # ========================================================
    # Fig 4 — Doppler signal
    # ========================================================

    fig, ax = create_figure()

    ax.plot(
        time,
        doppler,
        color=COLOR_BLACK,
        linewidth=LINE_WIDTH,
    )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel(
        "Doppler sig (a.u.)"
    )

    configure_axes(
        ax,
        time,
        switch_delay,
        ylim=YLIM_DOPPLER,
    )

    fig.tight_layout()

    save_figure(
        fig,
        output_folder,
        "fig4_doppler_signal",
    )

    # ========================================================
    # Fig 5 — Z4, Z5, Z6
    # ========================================================

    fig, ax = create_figure()

    ax.scatter(
        time,
        z4,
        s=SCATTER_SIZE,
        color=COLOR_BLACK,
        alpha=SCATTER_ALPHA,
        edgecolors="none",
        label=r"$a_4$",
    )

    ax.scatter(
        time,
        z5,
        s=SCATTER_SIZE,
        color=COLOR_MEDIUM,
        alpha=SCATTER_ALPHA,
        edgecolors="none",
        label=r"$a_5$",
    )

    ax.scatter(
        time,
        z6,
        s=SCATTER_SIZE,
        color=COLOR_LIGHT,
        alpha=SCATTER_ALPHA,
        edgecolors="none",
        label=r"$a_6$",
    )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel(
        "Zernike coeff (rad)"
    )

    ax.legend(
        loc="center left",
        frameon=False
    )

    configure_axes(
        ax,
        time,
        switch_delay,
        ylim=YLIM_ZERNIKE,
    )

    fig.tight_layout()

    save_figure(
        fig,
        output_folder,
        "fig5_zernike_coefficients",
    )

    print(
        "\nAll figures generated successfully."
    )


# ============================================================
# Command-line interface
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate grayscale EPS + PNG "
            "plots from HDF5 + CSV + JSON."
        )
    )

    parser.add_argument(
        "input_folder",
        type=Path,
        help=(
            "Path to input folder containing "
            "h5/, avi/ and json/"
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Output directory. Default: "
            "<input_folder>/plots"
        ),
    )

    parser.add_argument(
        "--font-size",
        type=float,
        default=FONT_SIZE,
        help=(
            f"Base font size. "
            f"Default: {FONT_SIZE}"
        ),
    )

    parser.add_argument(
        "--switch-delay",
        type=float,
        default=SWITCH_DELAY,
        help=(
            f"Background switch delay "
            f"in seconds. "
            f"Default: {SWITCH_DELAY}"
        ),
    )

    args = parser.parse_args()

    if args.output_dir is None:
        output_folder = (
            args.input_folder
            / "plots"
        )
    else:
        output_folder = (
            args.output_dir
        )

    generate_plots(
        input_folder=args.input_folder,
        output_folder=output_folder,
        font_size=args.font_size,
        switch_delay=args.switch_delay,
    )


if __name__ == "__main__":
    main()