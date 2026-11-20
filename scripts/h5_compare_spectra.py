"""Compare band-averaged images and full-field spectra from several recordings.

Run directly for a file picker, edit FILEPATHS below, or use::

    python scripts/h5_compare_spectra.py recording1.holo recording2.holo --band 1000 10000

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


# Startup settings: recording paths and a symmetric absolute-frequency band (Hz).
FILEPATHS = []
FREQUENCY_RANGE_HZ = (0, 10000)
# Same default as h5_roi_spectra; also supports 'none', 'num_freq_squared', 'density'.
# 'density' divides unnormalized FFT power by N * effective_fs (power/Hz).
PSD_NORMALIZATION = 'num_freq'
# Effective fs already includes skip_every. Future skip-dependent absolute-power
# compensation must follow the saved FFT/window normalization; do not assume
# multiplying power by skip_every recovers power lost to decimation/aliasing.


def validate_band(low, high):
    if not np.isfinite([low, high]).all() or not 0 <= low < high:
        raise ValueError('Band must satisfy 0 <= minimum < maximum, in Hz.')


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
        sampling_freq = float(parameters['sampling_freq'])
        skip_value = parameters.get('skip_every', 1)
        skip = float(1 if skip_value is None else skip_value)
        if not np.isfinite(skip) or skip <= 0 or skip != int(skip):
            raise ValueError('skip_every must be a positive integer (or null).')
        fs = sampling_freq / skip
        if not np.isfinite(fs) or fs <= 0:
            raise ValueError('sampling_freq must be finite and positive.')
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
        divisors = {'none': 1, 'num_freq': n, 'num_freq_squared': n**2,
                    'density': n * fs}
        if normalization not in divisors:
            raise ValueError(f'Unknown normalization: {normalization}')
        divisor = divisors[normalization]
        image = np.zeros(spectrum.shape[1:], dtype=np.float64)
        mean = np.empty(n, dtype=np.float64)
        for index in range(n):
            plane = np.asarray(spectrum[index], dtype=np.float64)
            mean[index] = plane.mean()
            if selected[index]:
                image += plane
        image /= int(selected.sum()) * divisor
        order = np.argsort(frequency)
        order = order[frequency[order] != 0]
        return dict(path=path, label=Path(filepath).stem, image=image,
                    frequency=frequency[order], power=mean[order] / divisor,
                    fs=fs, skip=skip, band=(low, high), normalization=normalization,
                    selected_bins=int(selected.sum()),
                    covered_high=min(high, fs / 2))


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
        curve_ax.plot(entry['frequency'], entry['power'],
                      label=f"{entry['label']} (fs={entry['fs']:g} Hz, skip={entry['skip']:g})")
    image_figure.suptitle('Symmetric-band mean images (individual color scales)')
    curve_ax.set_title(f"Full-field mean spectra ({entries[0]['normalization']}; DC excluded)")
    curve_ax.set_xlabel('Frequency (Hz)')
    curve_ax.set_ylabel('Mean power/Hz' if entries[0]['normalization'] == 'density'
                        else 'Mean spectral value')
    curve_ax.grid(True, alpha=0.3)
    curve_ax.legend(fontsize=9)


class App:
    def __init__(self, paths, band):
        self.root = tk.Tk()
        self.root.title('H5 recording comparison')
        self.paths = list(map(str, paths))
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
            self.compare()

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
                    entries.append(load_comparison(path, low, high))
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    problems.append(f'{path}\n{exc}')
            if entries:
                if self.spectrum_window is None or not self.spectrum_window.winfo_exists():
                    self.spectrum_window = tk.Toplevel(self.root)
                    self.spectrum_window.title('Full-field mean spectra')
                    self.spectrum_figure = Figure(figsize=(10, 6), constrained_layout=True)
                    self.spectrum_canvas = self.add_canvas(self.spectrum_window,
                                                          self.spectrum_figure)
                plot_comparisons(entries, self.image_figure, self.spectrum_figure)
                self.image_canvas.draw_idle()
                self.spectrum_canvas.draw_idle()
                self.spectrum_window.deiconify()
                self.spectrum_window.lift()
            self.status.set(f'{len(entries)}/{len(self.paths)} files plotted; '
                            f'normalization: {PSD_NORMALIZATION}')
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
