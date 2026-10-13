#!/usr/bin/env python3

import argparse
from pathlib import Path

import h5py
import numpy as np
import matplotlib.pyplot as plt


GOLDEN_RATIO = 2.9

# All figures have exactly the same dimensions.
FIGURE_WIDTH = 6.72
FIGURE_HEIGHT = FIGURE_WIDTH / GOLDEN_RATIO

SCATTER_SIZE = 3
SCATTER_SIZE_SECONDARY = 20
SCATTER_ALPHA = 0.75
LINE_WIDTH = 1.5


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


def sliding_mean(x, window):
    """Centered sliding mean."""
    kernel = np.ones(window, dtype=float) / window
    return np.convolve(x, kernel, mode="same")


def sliding_median(x, window):
    """Centered sliding median."""
    if window % 2 == 0:
        raise ValueError("Median window must be odd.")

    half = window // 2
    padded = np.pad(
        x,
        (half, half),
        mode="edge",
    )

    windows = np.lib.stride_tricks.sliding_window_view(
        padded,
        window,
    )

    return np.median(windows, axis=-1)


def plot_coefficient(
    signal,
    mean_signal,
    median_signal,
    coefficient_index,
    output_dir,
    font_size,
    alpha,
):
    """Plot one Zernike coefficient."""

    n_samples = len(signal)
    samples = np.arange(n_samples)

    fig, ax = plt.subplots(
        figsize=(FIGURE_WIDTH, FIGURE_HEIGHT)
    )

    # Raw signal
    ax.scatter(
        samples,
        signal,
        s=SCATTER_SIZE,
        alpha=alpha,
        label="Signal",
        rasterized=True,
    )

    # Sliding average
    ax.plot(
        samples,
        mean_signal,
        linewidth=LINE_WIDTH,
        label="Sliding average",
    )

    # Sliding median
    ax.plot(
        samples,
        median_signal,
        linewidth=LINE_WIDTH,
        label="Sliding median",
    )

    ax.set_xlabel("Sample")
    ax.set_ylabel("Coefficient")

    ax.set_title(
        rf"Zernike coefficient $c_{{{coefficient_index}}}$"
    )

    ax.legend(
        frameon=False,
        loc="best",
    )

    fig.tight_layout()

    stem = output_dir / f"zernike_coef_{coefficient_index:03d}"

    fig.savefig(
        stem.with_suffix(".png"),
        dpi=300,
        bbox_inches="tight",
    )

    fig.savefig(
        stem.with_suffix(".eps"),
        format="eps",
        bbox_inches="tight",
    )

    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compute sliding average and sliding median of "
            "Shack-Hartmann Zernike coefficient signals."
        )
    )

    parser.add_argument(
        "h5_file",
        type=Path,
        help="Input HDF5 file.",
    )

    parser.add_argument(
        "--dataset",
        default="shack_hartmann_zernike_coefs",
        help="HDF5 dataset path.",
    )

    parser.add_argument(
        "--window",
        type=int,
        default=101,
        help="Sliding-window size. Default: 101.",
    )

    parser.add_argument(
        "--font-size",
        type=float,
        default=10,
        help="Matplotlib base font size.",
    )

    parser.add_argument(
        "--alpha",
        type=float,
        default=SCATTER_ALPHA,
        help="Transparency of raw signal.",
    )

    args = parser.parse_args()

    if args.window < 1:
        raise ValueError("Window must be >= 1.")

    if args.window % 2 == 0:
        raise ValueError(
            "Please use an odd window size, e.g. 51, 101, or 201."
        )

    configure_matplotlib(args.font_size)

    # Output directory is next to the H5 file.
    output_dir = args.h5_file.parent / "subplots"
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Read HDF5 data
    # ------------------------------------------------------------------
    with h5py.File(args.h5_file, "r") as h5:
        if args.dataset not in h5:
            raise KeyError(
                f"Dataset '{args.dataset}' not found in "
                f"{args.h5_file}"
            )

        coefs = np.asarray(h5[args.dataset])

    if coefs.ndim != 2:
        raise ValueError(
            f"Expected a 2-D dataset with shape "
            f"(n_samples, n_coefs), got {coefs.shape}"
        )

    n_samples, n_coefs = coefs.shape

    print(f"Input file : {args.h5_file}")
    print(f"Dataset    : {args.dataset}")
    print(f"Shape      : {coefs.shape}")
    print(f"Window     : {args.window}")
    print(f"Output     : {output_dir}")

    # ------------------------------------------------------------------
    # Process and plot each coefficient
    # ------------------------------------------------------------------
    for coef_idx in range(n_coefs):
        signal = np.asarray(
            coefs[:, coef_idx],
            dtype=float,
        )

        mean_signal = sliding_mean(
            signal,
            args.window,
        )

        median_signal = sliding_median(
            signal,
            args.window,
        )

        plot_coefficient(
            signal=signal,
            mean_signal=mean_signal,
            median_signal=median_signal,
            coefficient_index=coef_idx,
            output_dir=output_dir,
            font_size=args.font_size,
            alpha=args.alpha,
        )

        print(
            f"Saved coefficient {coef_idx + 1}/{n_coefs}"
        )

    print("Done.")


if __name__ == "__main__":
    main()