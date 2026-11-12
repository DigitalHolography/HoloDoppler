import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

from holodoppler.file_reader import FileReaderFactory
from holodoppler.core.propagation import fresnel_transform

DATA_PATH = r"Z:\260310_CHOROID\260310_AUZ0752_8.holo"
radius = 3
display_in_time = True

# Load and propagate
reader = FileReaderFactory.create(DATA_PATH)
data = reader.read_frames(0, 512).copy().astype(np.float64)
data = fresnel_transform(np, np.fft, data, 0.5, 20e-6, 852e-9)

nt, ny, nx = data.shape

# Spatial FFT
F = np.fft.fftshift(np.fft.fft2(data, axes=(-2, -1)), axes=(-2, -1))

y, x = np.ogrid[-ny//2:ny-ny//2, -nx//2:nx-nx//2]
mask = x**2 + y**2 <= radius**2

# Removed low spatial frequencies
removed = np.fft.ifft2(
    np.fft.ifftshift(F * mask, axes=(-2, -1)),
    axes=(-2, -1)
)

I = np.abs(removed)**2
Iavg = I.mean(axis=0)

# Time-averaged removed intensity
plt.figure(figsize=(6, 5))
plt.imshow(Iavg, cmap="gray", origin="lower")
plt.colorbar()
plt.title(f"Time-averaged removed intensity (r={radius})")
plt.tight_layout()

# Interactive frame viewer
if display_in_time:
    fig, ax = plt.subplots(figsize=(7, 6))
    plt.subplots_adjust(bottom=0.20)

    im = ax.imshow(I[0], cmap="gray", origin="lower",
                   vmin=0, vmax=np.percentile(I, 99.5))
    ax.set_title("Removed intensity - Frame 0")
    plt.colorbar(im, ax=ax)

    # Slider
    sax = plt.axes([0.20, 0.09, 0.60, 0.03])
    slider = Slider(sax, "Frame", 0, nt-1, valinit=0, valstep=1)

    def update(val):
        k = int(slider.val)
        im.set_data(I[k])
        ax.set_title(f"Removed intensity - Frame {k}")
        fig.canvas.draw_idle()

    slider.on_changed(update)

    # Previous / Next buttons
    bprev = Button(plt.axes([0.25, 0.02, 0.18, 0.045]), "Previous")
    bnext = Button(plt.axes([0.57, 0.02, 0.18, 0.045]), "Next")

    bprev.on_clicked(lambda event: slider.set_val(max(0, slider.val-1)))
    bnext.on_clicked(lambda event: slider.set_val(min(nt-1, slider.val+1)))

plt.show()