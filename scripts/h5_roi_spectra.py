"""Tkinter H5 ROI spectrum viewer, including skip_every comparisons."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import h5py
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.widgets import RectangleSelector


# Hard-coded normalization choice (N includes the DC bin; fs includes skip_every):
# 'none'       : unchanged stored spectrum
# 'num_freq'   : divide by N
# 'num_freq_squared': divide by N**2 (power per bin for an unnormalized FFT)
# 'density'    : divide by N * fs (power/Hz for an unnormalized FFT)
# 'unit_area'  : divide by sum(non-DC spectrum) * df (integral becomes 1)
# 'peak'       : divide by max(non-DC spectrum) (peak becomes 1)
# Unit-area and peak modes compare shapes, removing absolute power differences.
PSD_NORMALIZATION = 'num_freq' # choose this one !! (if the fft was not normalized in holodoppler as for 1.4.4 and below)


def prepare_spectrum(mean, frequency, fs, normalization=PSD_NORMALIZATION):
    """Remove DC, normalize, and return curve plus its sum and frequency integral.

    Use a bin sum for power-per-bin spectra, or sum * df for densities.
    The bin-width integral avoids bridging the missing DC bin with a trapezoid.
    """
    num_freq = mean.size
    df = fs / num_freq
    nonzero = frequency != 0
    psd = np.asarray(np.fft.fftshift(mean)[nonzero], dtype=np.float64)
    if normalization == 'none':
        divisor = 1.0
    elif normalization == 'num_freq':
        divisor = num_freq
    elif normalization == 'num_freq_squared':
        divisor = num_freq**2
    elif normalization == 'density':
        divisor = num_freq * fs
    elif normalization == 'unit_area':
        divisor = psd.sum() * df
    elif normalization == 'peak':
        divisor = psd.max() if psd.size else 0.0
    else:
        raise ValueError(f'Unknown PSD_NORMALIZATION: {normalization!r}')
    # Leave an all-zero spectrum at zero in shape-normalization modes.
    if divisor != 0:
        psd = psd / divisor
    bin_sum = psd.sum()
    return frequency[nonzero], psd, bin_sum, bin_sum * df


def dataset(file, names):
    """Find the first matching dataset, at the root or in an HDF5 group."""
    for name in names:
        if name in file and isinstance(file[name], h5py.Dataset):
            return file[name]
    for name in names:
        matches = []
        def find(path, obj):
            if isinstance(obj, h5py.Dataset) and path.rsplit('/', 1)[-1] == name:
                matches.append(path)
        file.visititems(find)
        if matches:
            return file[sorted(matches)[0]]
    raise KeyError('Missing H5 dataset: ' + ' or '.join(names))


def load_h5(path, require_moment=True):
    with h5py.File(path, 'r') as f:
        spectrum = dataset(f, ('averaged_spectrogram', 'spectrogram'))[:]
        raw = dataset(f, ('HD_parameters',))[()]
        if isinstance(raw, np.ndarray) and raw.ndim == 0:
            raw = raw.item()
        params = json.loads(raw.decode('utf-8') if isinstance(raw, bytes) else str(raw))
        skip = float(params.get('skip_every', 1))
        if not np.isfinite(skip) or skip <= 0:
            raise ValueError('skip_every must be a positive number')
        fs = float(params['sampling_freq']) / skip
        if not np.isfinite(fs) or fs <= 0:
            raise ValueError('Corrected sampling frequency must be positive')
        moment = None
        if require_moment:
            moment = dataset(f, ('moment0ff',))[:]
            # Original app averaged moment0ff over its leading axis.
            if moment.ndim == 3:
                moment = moment.mean(axis=0)
            if moment.ndim != 2:
                raise ValueError('moment0ff must be 2D or 3D')
    if spectrum.ndim != 3:
        raise ValueError('Expected spectrogram of shape (nfreq, ny, nx)')
    if moment is not None and spectrum.shape[1:] != moment.shape:
        raise ValueError('Spectrogram spatial dimensions do not match moment0ff')
    frequency = np.fft.fftshift(np.fft.fftfreq(spectrum.shape[0], d=1 / fs))
    return {'path': Path(path), 'spectrum': spectrum, 'moment': moment,
            'freq': frequency, 'skip': skip, 'fs': fs}


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('H5 ROI spectra')
        bar = tk.Frame(self.root)
        bar.pack(fill='x')
        tk.Button(bar, text='Open H5', command=self.open).pack(side='left')
        tk.Button(bar, text='skip_every_comparison', command=self.skip_every_comparison).pack(side='left')
        tk.Button(bar, text='Clear ROIs', command=self.clear).pack(side='left')
        self.log_log = tk.BooleanVar(value=False)
        tk.Checkbutton(bar, text='Log-log', variable=self.log_log,
                       command=self.update_spectrum_scale).pack(side='left')
        self.fig = Figure(figsize=(11, 5), constrained_layout=True)
        self.image_ax, self.spectrum_ax = self.fig.subplots(1, 2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        NavigationToolbar2Tk(self.canvas, self.root)
        self.selector = None
        self.rois = []
        self.colors = [f'C{i}' for i in range(10)]
        self.entries = []
        self.moment = None
        self.root.after(100, self.open)
        self.root.mainloop()

    def open(self):
        path = filedialog.askopenfilename(filetypes=[('HDF5 files', '*.h5 *.hdf5'), ('All files', '*.*')])
        if not path:
            return
        try:
            entry = load_h5(path)
        except Exception as exc:
            messagebox.showerror('Cannot open file', f'{path}\n{exc}')
            return
        entry['label'] = Path(path).stem
        self.display([entry], entry['moment'], 'H5 ROI spectra — ' + path)

    def skip_every_comparison(self):
        folder = filedialog.askdirectory(title='Select parent folder containing skip* folders')
        if not folder:
            return
        parent = Path(folder)
        entries, problems = [], []
        skip_dirs = sorted((p for p in parent.rglob('*')
                            if p.is_dir() and p.name.lower().startswith('skip')),
                           key=lambda p: str(p).lower())
        for skip_dir in skip_dirs:
            h5_dirs = sorted((p for p in skip_dir.iterdir()
                              if p.is_dir() and p.name.lower() == 'h5'))
            if not h5_dirs:
                problems.append(f'{skip_dir}: no h5 subfolder')
                continue
            files = sorted((p for p in h5_dirs[0].iterdir()
                            if p.is_file() and p.suffix.lower() in ('.h5', '.hdf5')))
            if not files:
                problems.append(f'{skip_dir}: no H5 file')
                continue
            # One file per skip folder; deterministic choice if there are several.
            path = files[0]
            try:
                entry = load_h5(path, require_moment=False)
                entry['label'] = str(skip_dir.relative_to(parent))
                entries.append(entry)
            except Exception as exc:
                problems.append(f'{path}: {exc}')
        if not entries:
            messagebox.showerror('No usable H5 files',
                                 'No valid files found in skip*/h5 folders.\n' + '\n'.join(problems[:15]))
            return
        shape = entries[0]['spectrum'].shape[1:]
        valid = []
        for entry in entries:
            if entry['spectrum'].shape[1:] != shape:
                problems.append(f"{entry['path']}: spatial dimensions differ")
            else:
                valid.append(entry)
        entries = valid
        if not entries:
            messagebox.showerror('No comparable H5 files', 'Spatial dimensions do not match.')
            return
        # First moment0ff image found in the accepted files. If unavailable there,
        # inspect the skipped files in search order as a fallback.
        moment = None
        for entry in entries:
            try:
                with h5py.File(entry['path'], 'r') as f:
                    moment = dataset(f, ('moment0ff',))[:]
                if moment.ndim == 3:
                    moment = moment.mean(axis=0)
                if moment.ndim != 2 or moment.shape != shape:
                    raise ValueError('moment0ff dimensions mismatch')
                break
            except Exception as exc:
                moment = None
                problems.append(f"{entry['path']}: cannot use moment0ff ({exc})")
        if moment is None:
            messagebox.showerror('No moment0ff', 'Could not find a compatible moment0ff image.')
            return
        for entry in entries:
            entry['label'] += f" (skip_every={entry['skip']:g})"
        self.display(entries, moment, 'H5 ROI spectra — skip_every comparison — ' + str(parent))
        if problems:
            messagebox.showwarning('Some folders/files were skipped',
                                   '\n'.join(problems[:20]) +
                                   (f'\n... and {len(problems)-20} more' if len(problems) > 20 else ''))

    def display(self, entries, moment, title):
        if self.selector is not None:
            self.selector.set_active(False)
            self.selector = None
        self.rois.clear()
        self.entries = entries
        self.moment = moment
        self.image_ax.clear()
        self.spectrum_ax.clear()
        self.image_ax.imshow(moment, origin='upper', cmap='gray')
        self.image_ax.set_title('moment0ff — drag to select ROI')
        self.spectrum_ax.set_title(f'Mean spectrum per ROI ({PSD_NORMALIZATION})')
        self.spectrum_ax.set_xlabel('Frequency (Hz)')
        self.spectrum_ax.set_ylabel('Mean spectral value')
        self.selector = RectangleSelector(self.image_ax, self.select, button=[1],
                                          useblit=True, interactive=False,
                                          minspanx=1, minspany=1, spancoords='data')
        self.root.title(title)
        self.update_spectrum_scale()
        self.canvas.draw_idle()

    def update_spectrum_scale(self):
        """Refresh existing curves when switching between linear and log axes."""
        log_log = self.log_log.get()
        for _, lines in self.rois:
            for line in lines:
                frequency, psd = line.spectrum_data
                mask = ((frequency > 0) & (psd > 0) if log_log else
                        np.ones(frequency.shape, dtype=bool))
                line.set_data(frequency[mask], psd[mask])
        self.spectrum_ax.set_xscale('log' if log_log else 'linear')
        self.spectrum_ax.set_yscale('log' if log_log else 'linear')
        self.spectrum_ax.relim()
        self.spectrum_ax.autoscale_view()
        self.canvas.draw_idle()

    def select(self, start, end):
        if self.moment is None or start.xdata is None or end.xdata is None or start.ydata is None or end.ydata is None:
            return
        ny, nx = self.moment.shape
        x0, x1 = sorted((int(round(start.xdata)), int(round(end.xdata))))
        y0, y1 = sorted((int(round(start.ydata)), int(round(end.ydata))))
        x0, x1 = max(0, x0), min(nx, x1 + 1)
        y0, y1 = max(0, y0), min(ny, y1 + 1)
        if x1 <= x0 or y1 <= y0:
            return
        roi_number = len(self.rois) + 1
        color = self.colors[len(self.rois) % len(self.colors)]
        rect = Rectangle((x0 - .5, y0 - .5), x1 - x0, y1 - y0,
                         edgecolor=color, facecolor='none', linewidth=2)
        self.image_ax.add_patch(rect)
        lines = []
        for i, entry in enumerate(self.entries):
            mean = entry['spectrum'][:, y0:y1, x0:x1].mean(axis=(1, 2))
            frequency, psd, bin_sum, integral = prepare_spectrum(
                mean, entry['freq'], entry['fs'])
            label = (f'ROI {roi_number}' if len(self.entries) == 1 else
                     f"ROI {roi_number} — {entry['label']}")
            # Report both conventions so bin power and density can be compared.
            label += f' | sum={bin_sum:.5g}, integral={integral:.5g}'
            line, = self.spectrum_ax.plot(frequency, psd,
                                          color=color, linestyle=['-', '--', '-.', ':'][i % 4],
                                          alpha=0.95, label=label)
            line.spectrum_data = (frequency, psd)
            lines.append(line)
        self.rois.append((rect, lines))
        self.update_spectrum_scale()
        self.spectrum_ax.legend(fontsize='small')
        self.canvas.draw_idle()

    def clear(self):
        for rect, lines in self.rois:
            rect.remove()
            for line in lines:
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
