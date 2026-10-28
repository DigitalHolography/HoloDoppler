import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector, Button
from matplotlib.patches import Rectangle


DATA_PATH = r"Y:\260113_IOP_BP\260113_FIY0713.holo"

from holodoppler.file_reader import FileReaderFactory

reader = FileReaderFactory.create(DATA_PATH)

data = reader.read_frames(0,512).copy().astype(np.float64)

nt, ny, nx = data.shape

# -----------------------------------
# 1. FFT2 of all frames
# -----------------------------------
fft_cube = np.fft.fftshift(
    np.fft.fft2(data, axes=(-2, -1)),
    axes=(-2, -1)
)

mean_intensity = np.mean(np.abs(fft_cube)**2, axis=0)
log_intensity = np.log10(mean_intensity + 1e-12)

ny, nx = log_intensity.shape

# -----------------------------------
# 2. Reconstruction from selected zone
# -----------------------------------
def reconstruct(mask):
    fft_masked = fft_cube * mask[None, :, :]

    reconstructed = np.fft.ifft2(
        np.fft.ifftshift(fft_masked, axes=(-2, -1)),
        axes=(-2, -1)
    )

    return reconstructed.real.mean(axis=0)


# Initially select the full FFT
mask = np.ones((ny, nx), dtype=bool)
average_image = reconstruct(mask)

# -----------------------------------
# 3. Figure
# -----------------------------------
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
plt.subplots_adjust(bottom=0.17, wspace=0.3)

# Left: log FFT2
im_fft = axes[0].imshow(
    log_intensity,
    cmap='inferno',
    origin='lower'
)

fig.colorbar(im_fft, ax=axes[0], label='log10(Mean FFT intensity)')

axes[0].set_title('Select a rectangle in Fourier space')
axes[0].set_xlabel('kx')
axes[0].set_ylabel('ky')

# Right: inverse FFT2 average
im_recon = axes[1].imshow(
    average_image,
    cmap='gray',
    origin='lower'
)

fig.colorbar(im_recon, ax=axes[1], label='Reconstructed intensity')

axes[1].set_title('Average inverse FFT2 of selected zone')
axes[1].set_xlabel('x')
axes[1].set_ylabel('y')

# Rectangle outline
rect_patch = Rectangle(
    (0, 0), 0, 0,
    linewidth=1.5,
    edgecolor='cyan',
    facecolor='none'
)
axes[0].add_patch(rect_patch)

# -----------------------------------
# 4. Rectangle selection callback
# -----------------------------------
def onselect(eclick, erelease):
    global mask, average_image

    if eclick.xdata is None or erelease.xdata is None:
        return

    x1, x2 = sorted([eclick.xdata, erelease.xdata])
    y1, y2 = sorted([eclick.ydata, erelease.ydata])

    # Convert to pixel indices
    x1 = int(np.clip(np.floor(x1), 0, nx))
    x2 = int(np.clip(np.ceil(x2), 0, nx))
    y1 = int(np.clip(np.floor(y1), 0, ny))
    y2 = int(np.clip(np.ceil(y2), 0, ny))

    # Build rectangle mask
    mask = np.zeros((ny, nx), dtype=bool)
    mask[y1:y2, x1:x2] = True

    # Update rectangle outline
    rect_patch.set_xy((x1, y1))
    rect_patch.set_width(x2 - x1)
    rect_patch.set_height(y2 - y1)

    # Reconstruct selected Fourier region
    average_image = reconstruct(mask)

    # Update right image
    im_recon.set_data(average_image)
    im_recon.set_clim(
        average_image.min(),
        average_image.max() + 1e-12
    )

    axes[1].set_title(
        f'Average IFFT2 | {100 * mask.mean():.2f}% frequencies'
    )

    fig.canvas.draw_idle()


# -----------------------------------
# 5. Interactive rectangle selector
# -----------------------------------
selector = RectangleSelector(
    axes[0],
    onselect,
    useblit=True,
    button=[1],
    minspanx=2,
    minspany=2,
    spancoords='pixels',
    interactive=True,
    props=dict(
        facecolor='cyan',
        edgecolor='cyan',
        alpha=0.2,
        fill=True
    )
)

# -----------------------------------
# 6. Save button
# -----------------------------------
save_ax = fig.add_axes([0.42, 0.04, 0.16, 0.055])
save_button = Button(save_ax, 'Save selection')

def save_selection(event):
    np.save('fft_rectangle_mask.npy', mask)
    np.save('ifft_average_selected.npy', average_image)
    fig.savefig('fft_rectangle_selection.png', dpi=300)

    print("Saved mask, reconstructed image and figure.")

save_button.on_clicked(save_selection)

plt.show()
