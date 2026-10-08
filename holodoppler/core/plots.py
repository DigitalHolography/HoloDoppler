import numpy as np
import matplotlib.pyplot as plt

def plot_phase_with_slopes_rgb(
    phase: np.ndarray,
    shifts_y: np.ndarray,
    shifts_x: np.ndarray,
    *,
    dpi: int = 300,
    figsize=(8, 8),
) -> np.ndarray:
    """
    Render the reconstructed wavefront as an RGB NumPy array using
    Matplotlib's Agg backend.

    Parameters
    ----------
    phase:
        Reconstructed phase, shape (Ny, Nx), in radians.

    shifts_y, shifts_x:
        Shack-Hartmann displacement maps.

    dpi:
        Rendering resolution.

    figsize:
        Figure size in inches.

    Returns
    -------
    np.ndarray
        RGB uint8 image with shape (H, W, 3).

    Notes
    -----
    - Uses the multicolor cyclic ``twilight`` colormap.
    - Phase is wrapped to [0, 2*pi).
    - Invalid phase pixels are white.
    - Axes, ticks, labels, borders, and colorbars are removed.
    - The returned array contains RGB only, no alpha channel.
    """

    # Import Agg explicitly so this function does not require a GUI backend.
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    Ny, Nx = phase.shape
    nsy, nsx = shifts_y.shape

    # -----------------------------------------------------------------------
    # Create figure directly with Agg
    # -----------------------------------------------------------------------

    fig = Figure(
        figsize=figsize,
        dpi=dpi,
        facecolor="white",
    )
    canvas = FigureCanvasAgg(fig)

    ax = fig.add_axes([0, 0, 1, 1])

    # -----------------------------------------------------------------------
    # Phase
    # -----------------------------------------------------------------------

    phase = np.asarray(phase, dtype=np.float64)

    valid_phase = np.isfinite(phase)

    # Wrap phase into [0, 2*pi)
    phase_wrapped = np.mod(phase, 2.0 * np.pi)

    # Mask invalid values
    phase_masked = np.ma.array(
        phase_wrapped,
        mask=~valid_phase,
    )

    # -----------------------------------------------------------------------
    # Multicolor cyclic phase colormap
    # -----------------------------------------------------------------------

    twilight = plt.get_cmap("twilight").copy()

    # Invalid / masked pixels are white
    twilight.set_bad(color="white")

    ax.imshow(
        phase_masked,
        origin="lower",
        extent=[0, Nx, 0, Ny],
        cmap=twilight,
        vmin=0.0,
        vmax=2.0 * np.pi,
        interpolation="nearest",
        aspect="equal",
    )

    # -----------------------------------------------------------------------
    # Shack-Hartmann slope arrows
    # -----------------------------------------------------------------------

    x_centers = (np.arange(nsx) + 0.5) * Nx / nsx
    y_centers = (np.arange(nsy) + 0.5) * Ny / nsy

    X, Y = np.meshgrid(x_centers, y_centers)

    U = np.asarray(shifts_x, dtype=np.float64)
    V = np.asarray(shifts_y, dtype=np.float64)

    valid_slopes = np.isfinite(U) & np.isfinite(V)

    magnitude = np.sqrt(U**2 + V**2)
    finite_mag = magnitude[valid_slopes]

    if finite_mag.size:
        reference = np.nanpercentile(finite_mag, 95)

        if not np.isfinite(reference) or reference <= 0:
            reference = 1.0
    else:
        reference = 1.0

    arrow_scale = Nx / (max(nsx, nsy) * 2.5)

    U_plot = (U / reference) * arrow_scale
    V_plot = (V / reference) * arrow_scale

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

    # -----------------------------------------------------------------------
    # Remove axes completely
    # -----------------------------------------------------------------------

    ax.set_axis_off()
    ax.set_xlim(0, Nx)
    ax.set_ylim(0, Ny)
    ax.margins(0)

    # -----------------------------------------------------------------------
    # Render with Agg
    # -----------------------------------------------------------------------

    canvas.draw()

    # RGBA buffer -> RGB
    rgba = np.asarray(canvas.buffer_rgba())

    rgb = np.asarray(rgba[..., :3], dtype=np.uint8).copy()

    # Close the figure
    plt.close(fig)

    return rgb