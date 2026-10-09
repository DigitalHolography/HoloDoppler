#!/usr/bin/env python3

"""
Generate a Shack-Hartmann wavefront phase preview from an HDF5 file.

Workflow
--------
1. Take a root folder.
2. Find the first .h5 file.
3. Load the `shack_hartmann_sub_images` dataset.
4. Calculate Shack-Hartmann displacement maps using:
       holodoppler.shack_hartmann.calculate_displacements_graph_laplacian
5. Fit Zernike modes using:
       holodoppler.zernike.fit_zernike_fresnel
6. Plot the reconstructed phase with wavefront slopes overlaid.
7. Save PNG and EPS files to:
       <root_folder>/preview/plots/

Usage
-----
    python shack_hartmann_preview.py /path/to/data

Optional arguments are available with:

    python shack_hartmann_preview.py --help
"""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np
import matplotlib.pyplot as plt

import holodoppler
from holodoppler.shack_hartmann import calculate_displacements_graph_laplacian
from holodoppler.zernike import fit_zernike_fresnel


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Shack-Hartmann configuration
# ---------------------------------------------------------------------------

# Enable Shack-Hartmann processing
SHACK_HARTMANN = True

# Number of sub-apertures
SHACK_HARTMANN_NX_SUBAP = 5
SHACK_HARTMANN_NY_SUBAP = 5

# SVD threshold
SHACK_HARTMANN_SVD_THRESHOLD = 10

# Reject side sub-images below this pupil threshold
SHACK_HARTMANN_PUPIL_THRESHOLD = 2.0

# Maximum accepted displacement in units of standard deviation
SHACK_HARTMANN_DEVIATION_THRESHOLD = 10.0

# Maximum displacement in pixels
SHACK_HARTMANN_SHIFTS_PIXEL_RANGE_THRESHOLD = 1000.0

# Use graph Laplacian displacement calculation
SHACK_HARTMANN_GRAPH_LAPLACIAN = True

# Use Zernike fit
SHACK_HARTMANN_ZERNIKE_FIT = True

# Zernike modes in HoloDoppler NULL ordering
SHACK_HARTMANN_ZERNIKE_FIT_MODES = [4, 5, 6]

N_SUBAPS_Y=5
N_SUBAPS_X=5

PHASE_COLORMAP = "twilight"

# Optical parameters.
#
# IMPORTANT:
# Replace these values with the actual parameters of your experiment.
PIXEL_PITCH_Y = 20e-6
PIXEL_PITCH_X = 20e-6
WAVELENGTH = 852e-9


# ---------------------------------------------------------------------------
# HDF5 utilities
# ---------------------------------------------------------------------------

def find_first_h5(root: Path) -> Path:
    """Find the first HDF5 file below root, sorted alphabetically."""

    h5_files = sorted(root.rglob("*.h5"))

    if not h5_files:
        raise FileNotFoundError(
            f"No .h5 files found below:\n{root}"
        )

    return h5_files[0]


def find_dataset(h5: h5py.File, dataset_name: str):
    """
    Find a dataset recursively by its final name.

    This allows the dataset to be either:

        /shack_hartmann_sub_images

    or something like:

        /experiment_01/shack_hartmann_sub_images
    """

    found = []

    def visitor(name, obj):
        if isinstance(obj, h5py.Dataset):
            if name.split("/")[-1] == dataset_name:
                found.append(name)

    h5.visititems(visitor)

    if not found:
        raise KeyError(
            f"Dataset '{dataset_name}' was not found in the HDF5 file."
        )

    return h5[found[0]], found[0]


def prepare_sub_images(data: np.ndarray) -> np.ndarray:
    """
    Force a 2D camera image into a 5 x 5 grid of Shack-Hartmann
    sub-aperture images.

    Example
    -------
    Input:
        (510, 510)

    Output:
        (5, 5, 102, 102)

    The image is divided into 5 equal regions along Y and 5 equal
    regions along X.

    The returned array has the format expected by:

        calculate_displacements_graph_laplacian()

    i.e.

        (ny_s, nx_s, Ny, Nx)
    """

    data = np.asarray(data)

    print(f"Original dataset shape: {data.shape}")

    # ---------------------------------------------------------------
    # Case 1: already a 5x5 Shack-Hartmann array
    # ---------------------------------------------------------------

    if data.ndim == 4:
        if (
            data.shape[0] == 5
            and data.shape[1] == 5
        ):
            print("Dataset is already in (5, 5, Ny, Nx) format.")
            return data

        if (
            data.shape[2] == 5
            and data.shape[3] == 5
        ):
            print("Transposing dataset from (Ny, Nx, 5, 5).")

            return np.transpose(
                data,
                (2, 3, 0, 1),
            )

    # ---------------------------------------------------------------
    # Case 2: 2D image -> FORCE 5x5 tiling
    # ---------------------------------------------------------------

    if data.ndim == 2:

        height, width = data.shape

        print(
            f"Forcing {height} x {width} image "
            "into a 5 x 5 Shack-Hartmann grid."
        )

        if height % 5 != 0:
            raise ValueError(
                f"Image height {height} is not divisible by 5."
            )

        if width % 5 != 0:
            raise ValueError(
                f"Image width {width} is not divisible by 5."
            )

        sub_height = height // 5
        sub_width = width // 5

        print(
            f"Each sub-aperture: "
            f"{sub_height} x {sub_width}"
        )

        # -----------------------------------------------------------
        # Reshape:
        #
        # (510, 510)
        #
        # -> (5, 102, 5, 102)
        #
        # -> transpose
        #
        # -> (5, 5, 102, 102)
        # -----------------------------------------------------------

        sub_images = data.reshape(
            5,
            sub_height,
            5,
            sub_width,
        )

        sub_images = np.transpose(
            sub_images,
            (0, 2, 1, 3),
        )

        print(
            "Reshaped Shack-Hartmann array:"
            f" {sub_images.shape}"
        )

        return sub_images

    # ---------------------------------------------------------------
    # Case 3: 25 sub-apertures
    # ---------------------------------------------------------------

    if data.ndim == 3:

        if data.shape[0] == 25:

            Ny = data.shape[1]
            Nx = data.shape[2]

            return data.reshape(
                5,
                5,
                Ny,
                Nx,
            )

        if data.shape[-1] == 25:

            Ny = data.shape[0]
            Nx = data.shape[1]

            return np.transpose(
                data,
                (2, 0, 1),
            ).reshape(
                5,
                5,
                Ny,
                Nx,
            )

    # ---------------------------------------------------------------
    # Nothing worked
    # ---------------------------------------------------------------

    raise ValueError(
        "\nUnable to reshape shack_hartmann_sub_images.\n"
        f"Dataset shape: {data.shape}\n"
        "Expected a 2D image divisible by 5, "
        "or an existing 5x5 sub-aperture array."
    )


# ---------------------------------------------------------------------------
# Shack-Hartmann processing
# ---------------------------------------------------------------------------

def calculate_shifts(U_subaps: np.ndarray):
    """
    Calculate Shack-Hartmann displacements using the HoloDoppler
    graph-Laplacian method and the supplied configuration.
    """

    if not SHACK_HARTMANN:
        raise RuntimeError(
            "Shack-Hartmann processing is disabled."
        )

    if not SHACK_HARTMANN_GRAPH_LAPLACIAN:
        raise NotImplementedError(
            "Only the graph-Laplacian Shack-Hartmann method "
            "is enabled in this preview script."
        )

    xp = np
    fft = np.fft

    expected_shape = (
        SHACK_HARTMANN_NY_SUBAP,
        SHACK_HARTMANN_NX_SUBAP,
    )

    if U_subaps.shape[:2] != expected_shape:
        raise ValueError(
            f"Expected a "
            f"{SHACK_HARTMANN_NY_SUBAP}x"
            f"{SHACK_HARTMANN_NX_SUBAP} "
            f"Shack-Hartmann grid, "
            f"got {U_subaps.shape[:2]}"
        )

    print("\nCalculating Shack-Hartmann displacements...")
    print("  Method: graph Laplacian")
    print(
        "  Sub-apertures: "
        f"{SHACK_HARTMANN_NX_SUBAP} x "
        f"{SHACK_HARTMANN_NY_SUBAP}"
    )
    print(
        "  Pupil threshold: "
        f"{SHACK_HARTMANN_PUPIL_THRESHOLD}"
    )
    print(
        "  Deviation threshold: "
        f"{SHACK_HARTMANN_DEVIATION_THRESHOLD}"
    )
    print(
        "  Shift range: "
        f"{SHACK_HARTMANN_SHIFTS_PIXEL_RANGE_THRESHOLD} px"
    )

    result_y, result_x = calculate_displacements_graph_laplacian(
        xp=xp,
        fft=fft,
        U_subaps=U_subaps,
        mask=None,
        pupil_threshold=SHACK_HARTMANN_PUPIL_THRESHOLD,
        deviation_threshold=SHACK_HARTMANN_DEVIATION_THRESHOLD,
        shifts_range=SHACK_HARTMANN_SHIFTS_PIXEL_RANGE_THRESHOLD,
        use_corr_weights=False,
    )

    result_y = np.asarray(
        result_y,
        dtype=np.float32,
    )

    result_x = np.asarray(
        result_x,
        dtype=np.float32,
    )

    print(f"  shifts_y shape: {result_y.shape}")
    print(f"  shifts_x shape: {result_x.shape}")

    return result_y, result_x


def fit_phase(
    shifts_y: np.ndarray,
    shifts_x: np.ndarray,
    Ny: int,
    Nx: int,
):
    """
    Fit Zernike modes to the Shack-Hartmann displacement maps.
    """

    xp = np

    print("\nFitting Zernike wavefront...")

    coefs, phase = fit_zernike_fresnel(
    xp=np,
    ny=Ny,
    nx=Nx,
    pixel_pitch_y=PIXEL_PITCH_Y,
    pixel_pitch_x=PIXEL_PITCH_X,
    wavelength=WAVELENGTH,
    shifts_y=shifts_y,
    shifts_x=shifts_x,
    zernike_modes=SHACK_HARTMANN_ZERNIKE_FIT_MODES,
)

    return (
        np.asarray(coefs),
        np.asarray(phase),
    )


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def plot_phase_with_slopes(
    phase: np.ndarray,
    shifts_y: np.ndarray,
    shifts_x: np.ndarray,
    output_png: Path,
    output_eps: Path,
    title: str = "",
):
    """
    Plot wrapped wavefront phase with Shack-Hartmann slopes.

    Features
    --------
    - Phase wrapped to [0, 2*pi)
    - Selectable twilight / grayscale colormap
    - Invalid phase pixels displayed as white
    - Pixel axes
    - Black Shack-Hartmann slope arrows
    - No colorbar
    - No legend
    - No title
    - No interpolation artifacts
    """

    Ny, Nx = phase.shape
    nsy, nsx = shifts_y.shape

    # ------------------------------------------------------------------
    # Validate colormap
    # ------------------------------------------------------------------

    if PHASE_COLORMAP not in ("twilight", "gray"):
        raise ValueError(
            "PHASE_COLORMAP must be either "
            "'twilight' or 'gray'. "
            f"Got: {PHASE_COLORMAP!r}"
        )

    # ------------------------------------------------------------------
    # Create figure
    # ------------------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(8, 8),
    )

    # ------------------------------------------------------------------
    # Phase validity mask
    # ------------------------------------------------------------------

    phase = np.asarray(
        phase,
        dtype=np.float64,
    )

    valid_phase = np.isfinite(phase)

    # ------------------------------------------------------------------
    # Wrap phase to [0, 2*pi)
    # ------------------------------------------------------------------

    phase_wrapped = np.mod(
        phase,
        2.0 * np.pi,
    )

    # Explicitly mask invalid pixels.
    #
    # This is important because otherwise interpolation can produce
    # thin artificial lines at the boundary between valid and invalid
    # regions.

    phase_masked = np.ma.array(
        phase_wrapped,
        mask=~valid_phase,
    )

    # ------------------------------------------------------------------
    # Colormap
    # ------------------------------------------------------------------

    if PHASE_COLORMAP == "twilight":
        cmap = plt.get_cmap("twilight").copy()

    elif PHASE_COLORMAP == "gray":
        cmap = plt.get_cmap("gray").copy()

    # Invalid pixels -> white
    cmap.set_bad(
        color="white",
    )

    # ------------------------------------------------------------------
    # Display phase
    # ------------------------------------------------------------------

    ax.imshow(
        phase_masked,
        origin="lower",
        extent=[
            0,
            Nx,
            0,
            Ny,
        ],
        cmap=cmap,
        vmin=0.0,
        vmax=2.0 * np.pi,
        interpolation="nearest",
        aspect="equal",
    )

    # ------------------------------------------------------------------
    # Shack-Hartmann sub-aperture centers
    # ------------------------------------------------------------------

    x_centers = (
        np.arange(nsx) + 0.5
    ) * Nx / nsx

    y_centers = (
        np.arange(nsy) + 0.5
    ) * Ny / nsy

    X, Y = np.meshgrid(
        x_centers,
        y_centers,
    )

    U = np.asarray(
        shifts_x,
        dtype=np.float64,
    )

    V = np.asarray(
        shifts_y,
        dtype=np.float64,
    )

    # ------------------------------------------------------------------
    # Only draw valid slope vectors
    # ------------------------------------------------------------------

    valid_slopes = (
        np.isfinite(U)
        & np.isfinite(V)
    )

    # ------------------------------------------------------------------
    # Normalize arrow lengths for visualization
    # ------------------------------------------------------------------

    magnitude = np.sqrt(
        U**2 + V**2
    )

    finite_mag = magnitude[valid_slopes]

    if finite_mag.size:
        reference = np.nanpercentile(
            finite_mag,
            95,
        )

        if (
            not np.isfinite(reference)
            or reference <= 0
        ):
            reference = 1.0

    else:
        reference = 1.0

    # Arrow size in image pixels.
    arrow_scale = Nx / (
        max(nsx, nsy) * 2.5
    )

    U_plot = (
        U / reference
    ) * arrow_scale

    V_plot = (
        V / reference
    ) * arrow_scale

    # ------------------------------------------------------------------
    # Wavefront slope arrows
    # ------------------------------------------------------------------

    ax.quiver(
        X[valid_slopes],
        Y[valid_slopes],
        U_plot[valid_slopes],
        V_plot[valid_slopes],
        color="black",
        angles="xy",
        scale_units="xy",
        scale=1,
        width=0.004,
        headwidth=3.5,
        headlength=4.5,
        headaxislength=4.0,
    )

    # ------------------------------------------------------------------
    # Pixel axes
    # ------------------------------------------------------------------

    ax.set_xlim(
        0,
        Nx,
    )

    ax.set_ylim(
        0,
        Ny,
    )

    ax.set_xlabel(
        "X [pixels]",
        fontsize=12,
    )

    ax.set_ylabel(
        "Y [pixels]",
        fontsize=12,
    )

    ax.tick_params(
        axis="both",
        which="major",
        labelsize=10,
    )

    # ------------------------------------------------------------------
    # Explicitly remove title / legend
    # ------------------------------------------------------------------

    ax.set_title("")

    legend = ax.get_legend()

    if legend is not None:
        legend.remove()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    output_png.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.savefig(
        output_png,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.05,
        facecolor="white",
    )

    fig.savefig(
        output_eps,
        format="eps",
        bbox_inches="tight",
        pad_inches=0.05,
        facecolor="white",
    )

    plt.close(fig)

    print(f"Saved PNG: {output_png}")
    print(f"Saved EPS: {output_eps}")
    print(f"Phase colormap: {PHASE_COLORMAP}")



# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a Zernike-reconstructed wavefront preview "
            "from Shack-Hartmann HDF5 data."
        )
    )

    parser.add_argument(
        "folder",
        type=Path,
        help="Root folder containing the HDF5 data.",
    )

    args = parser.parse_args()

    root = args.folder.expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(
            f"Folder does not exist: {root}"
        )

    if not root.is_dir():
        raise NotADirectoryError(
            f"Not a directory: {root}"
        )

    print("=" * 70)
    print("Shack-Hartmann wavefront preview")
    print("=" * 70)
    print(f"Root folder: {root}")

    # ---------------------------------------------------------------
    # Find HDF5
    # ---------------------------------------------------------------

    h5_path = find_first_h5(root)

    print(f"\nUsing first HDF5 file:")
    print(f"  {h5_path}")

    # ---------------------------------------------------------------
    # Load data
    # ---------------------------------------------------------------

    with h5py.File(h5_path, "r") as h5:

        dataset, dataset_path = find_dataset(
            h5,
            "shack_hartmann_sub_images",
        )

        print(f"\nDataset:")
        print(f"  {dataset_path}")
        print(f"  shape = {dataset.shape}")
        print(f"  dtype = {dataset.dtype}")

        data = dataset[...]

    # ---------------------------------------------------------------
    # Prepare 5x5 Shack-Hartmann sub-apertures
    # ---------------------------------------------------------------

    U_subaps = prepare_sub_images(data)

    print(
        "\nPrepared Shack-Hartmann array:"
        f"\n  shape = {U_subaps.shape}"
    )

    if U_subaps.shape[0:2] != (
        N_SUBAPS_Y,
        N_SUBAPS_X,
    ):
        raise ValueError(
            "The resulting Shack-Hartmann grid is not 5x5."
        )

    _, _, Ny, Nx = U_subaps.shape

    # ---------------------------------------------------------------
    # Calculate displacement maps
    # ---------------------------------------------------------------

    shifts_y, shifts_x = calculate_shifts(
        U_subaps
    )

    # ---------------------------------------------------------------
    # Fit Zernike phase
    # ---------------------------------------------------------------

    coefs, phase = fit_phase(
        shifts_y,
        shifts_x,
        Ny,
        Nx,
    )

    print("\nZernike coefficients:")
    for mode, coef in zip(SHACK_HARTMANN_ZERNIKE_FIT_MODES, coefs):
        print(
            f"  mode {mode:3d}: "
            f"{float(coef): .6e}"
        )

    print(
        "\nPhase statistics:"
        f"\n  min = {np.nanmin(phase): .6e}"
        f"\n  max = {np.nanmax(phase): .6e}"
        f"\n  mean = {np.nanmean(phase): .6e}"
        f"\n  std = {np.nanstd(phase): .6e}"
    )

    # ---------------------------------------------------------------
    # Output paths
    # ---------------------------------------------------------------

    plot_dir = (
        root
        / "plots"
    )

    stem = h5_path.stem

    output_png = (
        plot_dir
        / f"{stem}_wavefront.png"
    )

    output_eps = (
        plot_dir
        / f"{stem}_wavefront.eps"
    )

    # ---------------------------------------------------------------
    # Plot
    # ---------------------------------------------------------------

    plot_phase_with_slopes(
        phase=phase,
        shifts_y=shifts_y,
        shifts_x=shifts_x,
        output_png=output_png,
        output_eps=output_eps,
        title=(
            "Shack–Hartmann Wavefront Reconstruction\n"
            f"{h5_path.name}"
        ),
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
