
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider

from holodoppler.file_reader import FileReaderFactory

DATA_PATH = r"Y:\260113_IOP_BP\260113_FIY0713.holo"

reader = FileReaderFactory.create(DATA_PATH)
data = reader.read_frames(0, 512).copy().astype(np.float32)

# Optional: subtract temporal mean at each pixel
data -= data.mean(axis=0, keepdims=True)

nt, ny, nx = data.shape
vmax = np.percentile(np.abs(data), 99.5)
vmax = max(vmax, 1e-12)

frame = 0

fig, ax = plt.subplots(figsize=(8, 7))
plt.subplots_adjust(bottom=0.22)

im = ax.imshow(
    data[frame],
    cmap="RdBu_r",
    vmin=-vmax,
    vmax=vmax,
    origin="lower",
    interpolation="nearest",
)
title = ax.set_title(f"Frame {frame + 1}/{nt}")
ax.set_axis_off()
fig.colorbar(im, ax=ax, label="Amplitude", shrink=0.8)

# Buttons
ax_prev = plt.axes([0.22, 0.08, 0.16, 0.06])
ax_next = plt.axes([0.62, 0.08, 0.16, 0.06])
btn_prev = Button(ax_prev, "Previous")
btn_next = Button(ax_next, "Next")

# Frame slider
ax_slider = plt.axes([0.18, 0.16, 0.64, 0.035])
slider = Slider(
    ax_slider, "Frame", 0, nt - 1,
    valinit=0, valstep=1,
)

def show_frame(index):
    global frame
    frame = int(np.clip(index, 0, nt - 1))
    im.set_data(data[frame])
    title.set_text(f"Frame {frame + 1}/{nt}")
    slider.set_val(frame) if int(slider.val) != frame else None
    fig.canvas.draw_idle()

def previous(event):
    show_frame(frame - 1)

def next_frame(event):
    show_frame(frame + 1)

btn_prev.on_clicked(previous)
btn_next.on_clicked(next_frame)
slider.on_changed(show_frame)

plt.show()
