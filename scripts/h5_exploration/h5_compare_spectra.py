"""Compare band-averaged images and full-field or ROI spectra from recordings.

Run directly for a file picker, edit FILEPATHS below, or use::

    python scripts/h5_exploration/h5_compare_spectra.py recording1.holo recording2.holo --band 1000 10000

For recording /data/name.holo, look in /data/name/name_HD/h5/ for its H5.
Direct H5 paths are also accepted. Stored spectra must be in unshifted FFT
order with shape (frequency, y, x), as in h5_roi_spectra.py.
"""
import argparse
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import h5py
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.widgets import RectangleSelector

try:
    from scripts.h5_exploration.h5_spectra_normalization import (
        NORMALIZATIONS, PSD_NORMALIZATION, effective_sampling_frequency,
        normalization_divisor, normalize_spectrum)
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from h5_spectra_normalization import (
        NORMALIZATIONS, PSD_NORMALIZATION, effective_sampling_frequency,
        normalization_divisor, normalize_spectrum)


# Startup settings: recording paths and a symmetric absolute-frequency band (Hz).
FILEPATHS = []
FREQUENCY_RANGE_HZ = (0, 10000)
# Normalization settings are shared with h5_roi_spectra.
# Density divides by N * fs_eff, where fs_eff = sampling_freq / skip_every.


def validate_band(low, high):
    if not np.isfinite([low, high]).all() or not 0 <= low < high:
        raise ValueError('Band must satisfy 0 <= minimum < maximum, in Hz.')


def normalize_entry(entry, normalization):
    """Normalize cached raw values; energy always uses raw orthonormal FFT power."""
    n, fs = entry['mean'].size, entry['fs']
    entry['power'] = normalize_spectrum(entry['mean'], fs, normalization)[entry['order']]
    image_divisor = normalization_divisor(
        normalization, n, fs, entry['pixel_sum'], entry['pixel_peak'])
    entry['image'] = np.divide(entry['raw_image'], image_divisor,
                               out=np.zeros_like(entry['raw_image']), where=image_divisor != 0)
    entry.update(normalization=normalization, energy=entry['mean'].sum() / fs,
                 dc_energy=entry['mean'][0] / fs)
    return entry


def select_roi(entry, roi):
    """Use common pixel bounds (x0, x1, y0, y1), clipped to each image's size."""
    result = entry.copy()
    if roi is None:
        result.update(mean=entry['full_mean'], roi=None)
    else:
        ny, nx = entry['raw_image'].shape
        x0, x1, y0, y1 = roi
        x0, x1 = max(0, x0), min(nx, x1)
        y0, y1 = max(0, y0), min(ny, y1)
        if x0 >= x1 or y0 >= y1:
            raise ValueError(f"ROI does not overlap {entry['label']} ({nx} x {ny} pixels).")
        with h5py.File(entry['path'], 'r') as handle:
            data = handle['averaged_spectrogram']
            mean = np.array([np.asarray(data[k, y0:y1, x0:x1], dtype=np.float64).mean()
                             for k in range(data.shape[0])])
        result.update(mean=mean, roi=(x0, x1, y0, y1))
    return normalize_entry(result, entry['normalization'])


def resolve_h5(filepath):
    """Resolve the sibling output tree without silently picking among H5 files."""
    source = Path(filepath).expanduser()
    if source.is_file() and source.suffix.lower() in ('.h5', '.hdf5'):
        return source
    folder = source.parent / source.stem / f'{source.stem}_HD' / 'h5'
    if not folder.is_dir():
        raise FileNotFoundError(f'H5 folder not found: {folder}')
    files = sorted(p for p in folder.iterdir()
                   if p.is_file() and p.suffix.lower() in ('.h5', '.hdf5'))
    if not files:
        raise FileNotFoundError(f'No H5 file in {folder}')
    if len(files) > 1:
        raise ValueError(f'Multiple H5 files in {folder}; select an H5 directly: '
                         + ', '.join(p.name for p in files))
    return files[0]


def load_comparison(filepath, low, high, normalization=PSD_NORMALIZATION):
    """Read one plane at a time, retaining only the band image and mean curve.

    The image is the arithmetic mean over selected positive AND negative bins,
    excluding DC, and the curve is the spatial mean at every non-DC frequency.
    Both use the same power normalization. Different spatial sizes are allowed.
    """
    validate_band(low, high)
    path = resolve_h5(filepath)
    with h5py.File(path, 'r') as handle:
        raw = handle['HD_parameters'][()]
        if isinstance(raw, np.ndarray) and raw.ndim == 0:
            raw = raw.item()
        parameters = json.loads(raw)
        fs, skip = effective_sampling_frequency(parameters)
        spectrum = handle['averaged_spectrogram']
        if spectrum.ndim != 3 or any(size == 0 for size in spectrum.shape):
            raise ValueError('averaged_spectrogram must have shape (frequency, y, x).')
        n = spectrum.shape[0]
        frequency = np.fft.fftfreq(n, d=1 / fs)
        selected = ((np.abs(frequency) >= low) & (np.abs(frequency) <= high)
                    & (frequency != 0))
        if not selected.any():
            raise ValueError(f'No nonzero bins in {low:g}-{high:g} Hz; '
                             f'effective fs={fs:g} Hz, bin width={fs / n:g} Hz.')
        image = np.zeros(spectrum.shape[1:], dtype=np.float64)
        pixel_sum = np.zeros_like(image)
        pixel_peak = np.zeros_like(image)
        mean = np.empty(n, dtype=np.float64)
        for index in range(n):
            plane = np.asarray(spectrum[index], dtype=np.float64)
            mean[index] = plane.mean()
            if frequency[index] != 0:
                pixel_sum += plane
                np.maximum(pixel_peak, plane, out=pixel_peak)
            if selected[index]:
                image += plane
        image /= int(selected.sum())
        order = np.argsort(frequency)
        order = order[frequency[order] != 0]
        return normalize_entry(dict(path=path, label=Path(filepath).stem,
                    raw_image=image, pixel_sum=pixel_sum, pixel_peak=pixel_peak,
                    mean=mean, full_mean=mean, order=order, roi=None,
                    frequency=frequency[order], fs=fs, skip=skip, band=(low, high),
                    selected_bins=int(selected.sum()),
                    covered_high=min(high, fs / 2)), normalization)


def plot_comparisons(entries, image_figure, spectrum_figure):
    """Build separate image and overlaid-spectrum figures (also usable headless)."""
    image_figure.clear()
    spectrum_figure.clear()
    columns = min(3, len(entries))
    rows = (len(entries) + columns - 1) // columns
    axes = image_figure.subplots(rows, columns, squeeze=False)
    curve_ax = spectrum_figure.subplots()
    for ax in axes.flat:
        ax.set_visible(False)
    for ax, entry in zip(axes.flat, entries):
        ax.set_visible(True)
        artist = ax.imshow(entry['image'], origin='upper', cmap='gray')
        low, high = entry['band']
        band_text = f"{low:g} <= |f| <= {high:g} Hz; DC excluded"
        if high > entry['covered_high']:
            band_text += f"\nclipped at Nyquist {entry['covered_high']:g} Hz"
        ax.set_title(f"{entry['label']}\n{band_text}", fontsize=9)
        ax.set_xlabel('x (pixel)')
        ax.set_ylabel('y (pixel)')
        image_figure.colorbar(artist, ax=ax, label='Mean spectral value')
        if entry['roi'] is not None:
            x0, x1, y0, y1 = entry['roi']
            ax.add_patch(Rectangle((x0 - 0.5, y0 - 0.5), x1 - x0, y1 - y0,
                                   edgecolor='tab:red', facecolor='none', linewidth=2))
        region = ('full field' if entry['roi'] is None else
                  f"ROI x[{entry['roi'][0]}:{entry['roi'][1]}], y[{entry['roi'][2]}:{entry['roi'][3]}]")
        curve_ax.plot(entry['frequency'], entry['power'],
                      label=f"{entry['label']} — {region} (fs={entry['fs']:g} Hz, skip={entry['skip']:g}, "
                            f"E={entry['energy']:.4g}, E_DC={entry['dc_energy']:.4g})")
    image_figure.suptitle('Symmetric-band mean images — drag to select ROI (individual color scales)')
    scope = 'Full-field' if entries[0]['roi'] is None else 'ROI'
    curve_ax.set_title(f"{scope} mean spectra ({entries[0]['normalization']}; DC excluded)")
    curve_ax.set_xlabel('Frequency (Hz)')
    curve_ax.set_ylabel('Mean power/Hz' if entries[0]['normalization'] == 'density'
                        else 'Mean spectral value')
    curve_ax.grid(True, alpha=0.3)
    curve_ax.legend(fontsize=9)
    return list(axes.flat)[:len(entries)]


class App:
    def __init__(self, paths, band):
        self.root = tk.Tk()
        self.root.title('H5 recording comparison')
        self.paths = list(map(str, paths))
        self.entries = []
        self.selectors = []
        self.roi = None
        bar = ttk.Frame(self.root)
        bar.pack(fill='x', padx=6, pady=6)
        ttk.Button(bar, text='Choose recordings / H5 files', command=self.choose).pack(side='left')
        ttk.Label(bar, text='Symmetric band |f| (Hz):').pack(side='left', padx=8)
        self.low = tk.StringVar(value=str(band[0]))
        self.high = tk.StringVar(value=str(band[1]))
        ttk.Entry(bar, textvariable=self.low, width=10).pack(side='left')
        ttk.Label(bar, text='to').pack(side='left', padx=4)
        ttk.Entry(bar, textvariable=self.high, width=10).pack(side='left')
        self.compare_button = ttk.Button(bar, text='Compare', command=self.compare)
        self.compare_button.pack(side='left', padx=8)
        options = ttk.Frame(self.root)
        options.pack(fill='x', padx=6)
        ttk.Label(options, text='Normalization:').pack(side='left')
        self.normalization = tk.StringVar(value=PSD_NORMALIZATION)
        dropdown = ttk.Combobox(options, textvariable=self.normalization,
                                values=NORMALIZATIONS, state='readonly', width=20)
        dropdown.pack(side='left', padx=6)
        dropdown.bind('<<ComboboxSelected>>', self.change_normalization)
        ttk.Button(options, text='Clear ROI / full field', command=self.clear_roi).pack(side='left')
        ttk.Label(options, text='Drag on any image; same pixel bounds apply to all files.').pack(side='left', padx=8)
        self.status = tk.StringVar(value='Select several recording paths or H5 files.')
        ttk.Label(self.root, textvariable=self.status).pack(fill='x', padx=6)
        self.image_figure = Figure(figsize=(11, 6), constrained_layout=True)
        self.image_canvas = self.add_canvas(self.root, self.image_figure)
        self.spectrum_window = None
        self.root.after(100, self.compare if self.paths else self.choose)
        self.root.mainloop()

    @staticmethod
    def add_canvas(window, figure):
        canvas = FigureCanvasTkAgg(figure, master=window)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        NavigationToolbar2Tk(canvas, window)
        return canvas

    def choose(self):
        paths = filedialog.askopenfilenames(parent=self.root,
                                            title='Select recordings or H5 files',
                                            filetypes=[('All files', '*.*')])
        if paths:
            self.paths = list(paths)
            self.roi = None
            self.compare()

    def redraw(self):
        for selector in self.selectors:
            selector.disconnect_events()
        self.selectors.clear()
        if not self.entries:
            self.image_figure.clear()
            self.image_canvas.draw_idle()
            if self.spectrum_window is not None and self.spectrum_window.winfo_exists():
                self.spectrum_figure.clear()
                self.spectrum_canvas.draw_idle()
            return
        if self.spectrum_window is None or not self.spectrum_window.winfo_exists():
            self.spectrum_window = tk.Toplevel(self.root)
            self.spectrum_window.title('Mean spectra comparison')
            self.spectrum_figure = Figure(figsize=(10, 6), constrained_layout=True)
            self.spectrum_canvas = self.add_canvas(self.spectrum_window, self.spectrum_figure)
        axes = plot_comparisons(self.entries, self.image_figure, self.spectrum_figure)
        for ax in axes:
            self.selectors.append(RectangleSelector(
                ax, self.on_select, button=[1], useblit=False,
                minspanx=1, minspany=1, spancoords='pixels'))
        self.image_canvas.draw_idle()
        self.spectrum_canvas.draw_idle()
        self.spectrum_window.deiconify()
        self.status.set(f'{len(self.entries)}/{len(self.paths)} files plotted; '
                        f'normalization: {self.normalization.get()}; '
                        + ('full field' if self.roi is None else f'ROI {self.roi}'))

    def change_normalization(self, event=None):
        for entry in self.entries:
            normalize_entry(entry, self.normalization.get())
        self.redraw()

    def on_select(self, start, end):
        coordinates = (start.xdata, end.xdata, start.ydata, end.ydata)
        if any(value is None for value in coordinates):
            return
        x0, x1 = sorted(int(np.floor(value + 0.5)) for value in coordinates[:2])
        y0, y1 = sorted(int(np.floor(value + 0.5)) for value in coordinates[2:])
        roi = (x0, x1 + 1, y0, y1 + 1)
        self.root.config(cursor='watch')
        self.root.update_idletasks()
        try:
            entries = [select_roi(entry, roi) for entry in self.entries]
        except (OSError, ValueError, KeyError) as exc:
            messagebox.showerror('Cannot select ROI', str(exc), parent=self.root)
            self.root.after_idle(self.redraw)
        else:
            self.entries, self.roi = entries, roi
            # Rebuild selectors after the current mouse-release callback completes.
            self.root.after_idle(self.redraw)
        finally:
            self.root.config(cursor='')

    def clear_roi(self):
        self.entries = [select_roi(entry, None) for entry in self.entries]
        self.roi = None
        self.redraw()

    def compare(self):
        try:
            low, high = float(self.low.get()), float(self.high.get())
            validate_band(low, high)
        except ValueError as exc:
            messagebox.showerror('Invalid frequency band', str(exc), parent=self.root)
            return
        if not self.paths:
            self.choose()
            return
        entries, problems = [], []
        self.compare_button.config(state='disabled')
        self.root.config(cursor='watch')
        try:
            for index, path in enumerate(self.paths, 1):
                self.status.set(f'Loading {index}/{len(self.paths)}: {path}')
                self.root.update_idletasks()
                try:
                    entry = load_comparison(path, low, high, self.normalization.get())
                    entries.append(select_roi(entry, self.roi) if self.roi is not None else entry)
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    problems.append(f'{path}\n{exc}')
            self.entries = entries
            self.redraw()
            if not entries:
                self.status.set('No files could be plotted.')
        finally:
            self.compare_button.config(state='normal')
            self.root.config(cursor='')
        if problems:
            messagebox.showwarning('Files could not be loaded', '\n\n'.join(problems),
                                   parent=self.root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('filepaths', nargs='*', help='Recording paths or direct H5 paths')
    parser.add_argument('--band', nargs=2, type=float, metavar=('MIN_HZ', 'MAX_HZ'),
                        default=FREQUENCY_RANGE_HZ)
    args = parser.parse_args()
    try:
        validate_band(*args.band)
    except ValueError as exc:
        parser.error(str(exc))
    App(args.filepaths or FILEPATHS, args.band)


if __name__ == '__main__':
    main()
