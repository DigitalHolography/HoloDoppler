import json
import tkinter as tk
from tkinter import filedialog, messagebox

import h5py
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.widgets import RectangleSelector


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('H5 ROI spectra')
        bar = tk.Frame(self.root)
        bar.pack(fill='x')
        tk.Button(bar, text='Open H5', command=self.open).pack(side='left')
        tk.Button(bar, text='Clear ROIs', command=self.clear).pack(side='left')
        self.fig = Figure(figsize=(11, 5), constrained_layout=True)
        self.image_ax, self.spectrum_ax = self.fig.subplots(1, 2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        NavigationToolbar2Tk(self.canvas, self.root)
        self.selector = None
        self.rois = []
        self.colors = [f'C{i}' for i in range(10)]
        self.root.after(100, self.open)
        self.root.mainloop()

    def open(self):
        path = filedialog.askopenfilename(filetypes=[('HDF5 files', '*.h5 *.hdf5'), ('All files', '*.*')])
        if not path:
            return
        try:
            with h5py.File(path) as f:
                spectrum = f['averaged_spectrogram'][:]
                moment = f['moment0ff'][:].mean(axis=0)
                raw = f['HD_parameters'][()]
                params = json.loads(raw.decode() if isinstance(raw, bytes) else str(raw))
            if spectrum.ndim != 3 or spectrum.shape[1:] != moment.shape:
                raise ValueError('Expected spectrum (nfreq, ny, nx) and moment0ff (ny, nx)')
            fs = float(params['sampling_freq']) / (params.get('skip_every') or 1)
        except Exception as e:
            messagebox.showerror('Cannot open file', str(e))
            return

        self.spectrum = spectrum
        self.moment = moment
        self.freq = np.fft.fftshift(np.fft.fftfreq(spectrum.shape[0], d=1 / fs))
        if self.selector:
            self.selector.set_active(False)
            self.selector = None
        self.clear()
        self.image_ax.clear()
        self.spectrum_ax.clear()
        self.image_ax.imshow(moment, origin='upper', cmap='gray')
        self.image_ax.set_title('moment0ff — drag to select ROI')
        self.spectrum_ax.set_title('Mean spectrum per ROI')
        self.spectrum_ax.set_xlabel('Frequency (Hz)')
        self.spectrum_ax.set_ylabel('Mean spectral value')
        self.clear()
        self.selector = RectangleSelector(self.image_ax, self.select, button=[1],
                                          useblit=True, interactive=False,
                                          minspanx=1, minspany=1, spancoords='data')
        self.root.title('H5 ROI spectra — ' + path)
        self.canvas.draw_idle()

    def select(self, start, end):
        ny, nx = self.moment.shape
        x0, x1 = sorted((int(round(start.xdata)), int(round(end.xdata))))
        y0, y1 = sorted((int(round(start.ydata)), int(round(end.ydata))))
        x0, x1 = max(0, x0), min(nx, x1 + 1)
        y0, y1 = max(0, y0), min(ny, y1 + 1)
        if x1 <= x0 or y1 <= y0:
            return
        color = self.colors[len(self.rois) % len(self.colors)]
        rect = Rectangle((x0 - .5, y0 - .5), x1 - x0, y1 - y0,
                         edgecolor=color, facecolor='none', linewidth=2)
        self.image_ax.add_patch(rect)
        mean = self.spectrum[:, y0:y1, x0:x1].mean(axis=(1, 2))
        line, = self.spectrum_ax.plot(self.freq, np.fft.fftshift(mean), color=color,
                                      label=f'ROI {len(self.rois) + 1}')
        self.rois.append((rect, line))
        self.spectrum_ax.legend()
        self.canvas.draw_idle()

    def clear(self):
        for rect, line in self.rois:
            rect.remove()
            line.remove()
        self.rois.clear()
        legend = self.spectrum_ax.get_legend()
        if legend:
            legend.remove()
        self.spectrum_ax.relim()
        self.spectrum_ax.autoscale_view()
        self.canvas.draw_idle()


if __name__ == '__main__':
    App()
