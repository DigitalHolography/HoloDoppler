import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from pathlib import Path
from PIL import Image


# ========================================================
# Configuration
# ========================================================

# --------------------------------------------------------
# Input / output
# --------------------------------------------------------

CSV_FILE = r"D:\za\260716_AUZ_1\260716_AUZ_1_HD\csv\shack_hartmann_zernike_coefs.csv"
OUTPUT_FOLDER = r"D:\za\260716_AUZ_1\260716_AUZ_1_HD\csv"

# --------------------------------------------------------
# Acquisition
# --------------------------------------------------------

# Original acquisition / sampling rate [Hz]
FS = 144.0

# Desired display / animation rate [Hz]
DISPLAY_FPS = 16.0

# Number of samples to advance per displayed frame.
#
# At 144 Hz acquisition and 16 Hz display:
#
#     144 / 16 = 9 samples/frame
#
# Therefore every displayed frame represents ~62.5 ms
# of the original signal.
FRAME_STEP = max(1, int(round(FS / DISPLAY_FPS)))

# --------------------------------------------------------
# Figure
# --------------------------------------------------------

FIGSIZE = (10, 5.5)

# Smaller DPI for faster/smaller animations
DPI = 100

# --------------------------------------------------------
# Y-axis
# --------------------------------------------------------

# Set to None for automatic limits.
#
# Example:
# YLIM_ZERNIKE = (-0.8, 0.2)
#
# Or:
# YLIM_ZERNIKE = (-1.0, 1.0)

YLIM_ZERNIKE = (-0.9,0.2)

# --------------------------------------------------------
# Plot appearance
# --------------------------------------------------------

SCATTER_SIZE = 8
SCATTER_ALPHA = 0.8
LINE_WIDTH = 1.8

# --------------------------------------------------------
# Colors
# --------------------------------------------------------
#
# Okabe-Ito colorblind-friendly palette.
#
# Blue   = #0072B2
# Orange = #E69F00
# Vermilion = #D55E00
#
# These are widely used for scientific figures.

COLOR_Z4 = "#0072B2"      # blue
COLOR_Z5 = "#E69F00"      # orange
COLOR_Z6 = "#D55E00"      # vermilion

COLOR_CURSOR = "#CC79A7"  # purple
COLOR_SWITCH = "#7F7F7F"  # neutral gray

# --------------------------------------------------------
# Optional switch/delay marker
# --------------------------------------------------------

# Set to None to disable.
#
# Example:
# SWITCH_DELAY = 1.5

SWITCH_DELAY = None


# ========================================================
# Load CSV
# ========================================================

data = pd.read_csv(
    CSV_FILE,
    header=None
)

if data.shape[1] < 3:
    raise ValueError(
        "CSV must contain at least 3 columns: Z4, Z5, Z6"
    )

z4 = data.iloc[:, 0].to_numpy(dtype=float)
z5 = data.iloc[:, 1].to_numpy(dtype=float)
z6 = data.iloc[:, 2].to_numpy(dtype=float)

n_samples = len(z4)

if not (
    len(z5) == n_samples
    and len(z6) == n_samples
):
    raise ValueError(
        "Z4, Z5 and Z6 must have the same number of samples."
    )


# ========================================================
# Time vector
# ========================================================

time = np.arange(n_samples) / FS


# ========================================================
# Output folder
# ========================================================

output_folder = Path(OUTPUT_FOLDER)
output_folder.mkdir(
    parents=True,
    exist_ok=True
)


# ========================================================
# Determine Y limits
# ========================================================

all_zernike = np.concatenate(
    [z4, z5, z6]
)

if YLIM_ZERNIKE is None:

    y_min = np.nanmin(all_zernike)
    y_max = np.nanmax(all_zernike)

    padding = 0.08 * (y_max - y_min)

    if padding == 0:
        padding = 0.1

    ylim = (
        y_min - padding,
        y_max + padding
    )

else:

    if len(YLIM_ZERNIKE) != 2:
        raise ValueError(
            "YLIM_ZERNIKE must contain two values, "
            "e.g. (-0.8, 0.2)"
        )

    ylim = tuple(YLIM_ZERNIKE)


# ========================================================
# Print animation information
# ========================================================

actual_display_fps = FS / FRAME_STEP

print()
print("========================================")
print("Zernike animation")
print("========================================")
print(f"Samples              : {n_samples}")
print(f"Acquisition rate     : {FS:.2f} Hz")
print(f"Requested display FPS: {DISPLAY_FPS:.2f}")
print(f"Frame step           : {FRAME_STEP} samples")
print(f"Actual display FPS   : {actual_display_fps:.2f}")
print(f"Signal duration      : {time[-1]:.3f} s")
print(f"Y limits             : {ylim}")
print("========================================")
print()


# ========================================================
# FULL STATIC FIGURE
# ========================================================

fig_full, ax_full = plt.subplots(
    figsize=FIGSIZE,
    dpi=DPI
)

# Z4
ax_full.scatter(
    time,
    z4,
    s=SCATTER_SIZE,
    color=COLOR_Z4,
    alpha=SCATTER_ALPHA,
    edgecolors="none",
    label=r"$a_4$"
)

# Z5
ax_full.scatter(
    time,
    z5,
    s=SCATTER_SIZE,
    color=COLOR_Z5,
    alpha=SCATTER_ALPHA,
    edgecolors="none",
    label=r"$a_5$"
)

# Z6
ax_full.scatter(
    time,
    z6,
    s=SCATTER_SIZE,
    color=COLOR_Z6,
    alpha=SCATTER_ALPHA,
    edgecolors="none",
    label=r"$a_6$"
)

ax_full.set_xlabel(
    "Time (s)"
)

ax_full.set_ylabel(
    "Zernike coeff (rad)"
)

ax_full.set_xlim(
    time[0],
    time[-1]
)

ax_full.set_ylim(
    *ylim
)

ax_full.legend(
    loc="center left",
    frameon=False
)

ax_full.grid(
    True,
    alpha=0.15
)

if SWITCH_DELAY is not None:

    ax_full.axvline(
        SWITCH_DELAY,
        color=COLOR_SWITCH,
        linestyle="--",
        linewidth=1,
        alpha=0.7
    )

fig_full.tight_layout()


# ========================================================
# Save FULL PNG
# ========================================================

full_png = (
    output_folder /
    "fig5_zernike_coefficients_full.png"
)

fig_full.savefig(
    full_png,
    dpi=DPI,
    bbox_inches="tight"
)

plt.close(fig_full)

print(
    f"Saved full figure: {full_png}"
)


# ========================================================
# ANIMATED FIGURE — SCATTER ONLY
# ========================================================

fig, ax = plt.subplots(
    figsize=FIGSIZE,
    dpi=DPI
)

# ========================================================
# Empty scatter plots
# ========================================================

points_z4 = ax.scatter(
    [],
    [],
    s=SCATTER_SIZE,
    color=COLOR_Z4,
    alpha=SCATTER_ALPHA,
    edgecolors="none",
    label=r"$a_4$"
)

points_z5 = ax.scatter(
    [],
    [],
    s=SCATTER_SIZE,
    color=COLOR_Z5,
    alpha=SCATTER_ALPHA,
    edgecolors="none",
    label=r"$a_5$"
)

points_z6 = ax.scatter(
    [],
    [],
    s=SCATTER_SIZE,
    color=COLOR_Z6,
    alpha=SCATTER_ALPHA,
    edgecolors="none",
    label=r"$a_6$"
)


# ========================================================
# Moving time cursor
# ========================================================

time_cursor = ax.axvline(
    time[0],
    color=COLOR_CURSOR,
    linestyle="--",
    linewidth=1.2,
    alpha=0.9
)


# ========================================================
# Formatting
# ========================================================

ax.set_xlabel("Time (s)")

ax.set_ylabel(
    "Zernike coeff (rad)"
)

ax.set_xlim(
    time[0],
    time[-1]
)

ax.set_ylim(
    *ylim
)

ax.legend(
    loc="center left",
    frameon=False
)

ax.grid(
    True,
    alpha=0.15
)

if SWITCH_DELAY is not None:

    ax.axvline(
        SWITCH_DELAY,
        color=COLOR_SWITCH,
        linestyle="--",
        linewidth=1,
        alpha=0.7
    )


# ========================================================
# Time indicator
# ========================================================

time_text = ax.text(
    0.98,
    0.95,
    "",
    transform=ax.transAxes,
    ha="right",
    va="top",
    fontsize=10
)


# ========================================================
# Frame indices
# ========================================================

frame_indices = np.arange(
    0,
    n_samples,
    FRAME_STEP
)

if frame_indices[-1] != n_samples - 1:

    frame_indices = np.append(
        frame_indices,
        n_samples - 1
    )


# ========================================================
# Animation update
# ========================================================

def update(frame_number):

    # Current sample in the original 144 Hz data
    sample = frame_indices[frame_number]

    # Data revealed so far
    t = time[:sample + 1]

    y4 = z4[:sample + 1]
    y5 = z5[:sample + 1]
    y6 = z6[:sample + 1]

    # ----------------------------------------------------
    # Update scatter points ONLY
    # ----------------------------------------------------

    points_z4.set_offsets(
        np.column_stack(
            (t, y4)
        )
    )

    points_z5.set_offsets(
        np.column_stack(
            (t, y5)
        )
    )

    points_z6.set_offsets(
        np.column_stack(
            (t, y6)
        )
    )

    # ----------------------------------------------------
    # Moving cursor
    # ----------------------------------------------------

    current_time = time[sample]

    time_cursor.set_xdata(
        [current_time, current_time]
    )

    # ----------------------------------------------------
    # Time label
    # ----------------------------------------------------

    time_text.set_text(
        f"t = {current_time:.3f} s"
    )

    return (
        points_z4,
        points_z5,
        points_z6,
        time_cursor,
        time_text
    )


# ========================================================
# Create animation
# ========================================================

animation = FuncAnimation(
    fig,
    update,
    frames=len(frame_indices),

    # Real-time display interval
    interval=1000 / DISPLAY_FPS,

    blit=True,
    repeat=False
)


# ========================================================
# Save GIF
# ========================================================

gif_file = (
    output_folder /
    "fig5_zernike_animation.gif"
)

print("Saving GIF...")

animation.save(
    gif_file,
    writer=PillowWriter(
        fps=DISPLAY_FPS
    ),
    dpi=DPI
)

print(
    f"Saved GIF: {gif_file}"
)


# ========================================================
# Save Animated PNG / APNG
# ========================================================

apng_file = (
    output_folder /
    "fig5_zernike_animation.png"
)

print("Saving animated PNG...")

# --------------------------------------------------------
# Render each displayed frame
# --------------------------------------------------------

frames = []

for frame_number in range(
    len(frame_indices)
):

    update(frame_number)

    fig.canvas.draw()

    image = np.asarray(
        fig.canvas.buffer_rgba()
    )

    image = Image.fromarray(
        image[:, :, :3]
    )

    frames.append(
        image.copy()
    )


# --------------------------------------------------------
# Save APNG
# --------------------------------------------------------

frames[0].save(
    apng_file,
    save_all=True,
    append_images=frames[1:],
    duration=int(
        1000 / DISPLAY_FPS
    ),
    loop=0,
    optimize=False
)

print(
    f"Saved APNG: {apng_file}"
)


# ========================================================
# Finish
# ========================================================

plt.close(fig)

print()
print("========================================")
print("Done!")
print("========================================")
print(f"Full PNG : {full_png}")
print(f"GIF      : {gif_file}")
print(f"APNG     : {apng_file}")
print()
print(
    f"Animation uses {FRAME_STEP} samples/frame "
    f"({FS:.0f} Hz acquisition → "
    f"{DISPLAY_FPS:.0f} Hz display)."
)
print(
    f"Actual displayed duration: "
    f"{time[-1]:.3f} s"
)
print("========================================")