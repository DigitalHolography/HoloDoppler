"""Tkinter H5 ROI spectrum viewer, including skip_every comparisons."""
import json
import queue
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import warnings

import h5py
import numpy as np
from matplotlib import colormaps
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.widgets import RectangleSelector
from scipy.optimize import OptimizeWarning, curve_fit


# Hard-coded normalization choice (N includes the DC bin; fs includes skip_every):
# 'none'       : unchanged stored spectrum
# 'num_freq'   : divide by N
# 'num_freq_squared': divide by N**2 (power per bin for an unnormalized FFT)
# 'density'    : divide by N * fs (power/Hz for an unnormalized FFT)
# 'unit_area'  : divide by sum(non-DC spectrum) * df (integral becomes 1)
# 'peak'       : divide by max(non-DC spectrum) (peak becomes 1)

# Unit-area and peak modes compare shapes, removing absolute power differences.
PSD_NORMALIZATION = 'num_freq' # choose this one or replace with a skip_every based normalisation because its really the fact that frames where skipped that reduce total power.


def gaussian_model(frequency, K, A, W):
    return K + A * np.exp(-0.5 * (frequency / W)**2)


def gaussian_initial(frequency, values):
    baseline = max(0.0, float(values.min()))
    return (baseline, max(float(np.ptp(values)), 0.1),
            max(float(np.max(np.abs(frequency))) / 2, 0.01))


FIT_MODELS = {
    'Zero-centered Gaussian': {
        'formula': 'K + A · exp(−f² / (2W²))',
        'parameters': ('K', 'A', 'W'),
        'function': gaussian_model,
        'bounds': ((0, 0, 1e-10), (np.inf, np.inf, np.inf)),
        'initial': gaussian_initial,
    },
}


def fit_frequency_mask(frequency, low, high, symmetric):
    """Select non-DC bins, requiring enough distinct samples for this model."""
    if not np.isfinite([low, high]).all() or not 0 <= low < high:
        raise ValueError('Frequency bounds must be finite and satisfy 0 ≤ minimum < maximum.')
    selected_frequency = np.abs(frequency) if symmetric else frequency
    mask = ((selected_frequency >= low) & (selected_frequency <= high) &
            (frequency != 0))
    if np.unique(np.abs(frequency[mask])).size < 4:
        raise ValueError('Select at least four distinct nonzero absolute frequencies.')
    return mask


def fit_pixel_maps(entry, low, high, symmetric=True,
                   model_name='Zero-centered Gaussian', normalization=PSD_NORMALIZATION,
                   progress=None, cancel=None):
    """Fit normalized spectra; return NaN for invalid pixels, or None on cancellation."""
    model = FIT_MODELS[model_name]
    mask = fit_frequency_mask(entry['freq'], low, high, symmetric)
    frequency = entry['freq'][mask]
    frequency_scale = float(np.max(np.abs(frequency)))
    x = frequency / frequency_scale
    shape = entry['spectrum'].shape[1:]
    maps = {name: np.full(shape, np.nan) for name in (*model['parameters'], 'R²')}
    total = int(np.prod(shape))
    report_every = max(1, total // 200)
    for index, (row, col) in enumerate(np.ndindex(shape)):
        if cancel is not None and cancel.is_set():
            return None
        raw = entry['spectrum'][:, row, col]
        # Invalid bins must not poison the normalization of otherwise usable data.
        finite_raw = np.isfinite(raw)
        normalization_input = (np.where(finite_raw, raw, 0)
                               if normalization in ('peak', 'unit_area') else raw)
        _, values, _, _ = prepare_spectrum(
            normalization_input, entry['freq'], entry['fs'], normalization)
        values[~np.fft.fftshift(finite_raw)[entry['freq'] != 0]] = np.nan
        values = values[mask[entry['freq'] != 0]]
        valid = np.isfinite(values)
        y = values[valid]
        pixel_x = x[valid]
        if np.unique(np.abs(pixel_x)).size >= 4 and np.ptp(y) > 0:
            scale = float(np.max(np.abs(y)))
            y = y / scale
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('error', OptimizeWarning)
                    parameters, _ = curve_fit(
                        model['function'], pixel_x, y,
                        p0=model['initial'](pixel_x, y), bounds=model['bounds'],
                        maxfev=2000)
                prediction = model['function'](pixel_x, *parameters)
                score = 1 - np.sum((y - prediction)**2) / np.sum((y - y.mean())**2)
                parameters = parameters * np.array([scale, scale, frequency_scale])
                if np.isfinite(parameters).all() and np.isfinite(score):
                    for name, value in zip(model['parameters'], parameters):
                        maps[name][row, col] = value
                    maps['R²'][row, col] = score
            except (RuntimeError, ValueError, FloatingPointError, OptimizeWarning):
                pass
        if progress is not None and ((index + 1) % report_every == 0 or index + 1 == total):
            progress(index + 1, total)
    if cancel is not None and cancel.is_set():
        return None
    return maps


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


def frequency_range_image(entry, lower, upper, symmetric=False, difference=False):
    """Sum normalized, non-DC PSD bins per pixel in the requested Hz range."""
    if not np.isfinite([lower, upper]).all() or lower > upper:
        raise ValueError('Enter finite frequency bounds with minimum <= maximum.')
    if difference and lower < 0:
        raise ValueError('For positive minus negative, enter nonnegative frequency bounds.')
    # Stored spectra use FFT order, whereas entry frequencies are shifted.
    frequency = np.fft.ifftshift(entry['freq'])
    selected = (frequency >= lower) & (frequency <= upper)
    if symmetric or difference:
        selected |= (frequency >= -upper) & (frequency <= -lower)
    selected &= frequency != 0
    if not selected.any():
        raise ValueError('The selected range contains no nonzero frequency bins.')
    spectrum = entry['spectrum']
    num_freq = spectrum.shape[0]
    if difference:
        positive = selected & (frequency > 0)
        negative = selected & (frequency < 0)
        image = (spectrum[positive].sum(axis=0, dtype=np.float64)
                 - spectrum[negative].sum(axis=0, dtype=np.float64))
    else:
        image = spectrum[selected].sum(axis=0, dtype=np.float64)
    if PSD_NORMALIZATION == 'none':
        divisor = 1.0
    elif PSD_NORMALIZATION == 'num_freq':
        divisor = num_freq
    elif PSD_NORMALIZATION == 'num_freq_squared':
        divisor = num_freq**2
    elif PSD_NORMALIZATION == 'density':
        divisor = num_freq * entry['fs']
    elif PSD_NORMALIZATION == 'unit_area':
        divisor = spectrum[frequency != 0].sum(axis=0, dtype=np.float64)
        divisor *= entry['fs'] / num_freq
    elif PSD_NORMALIZATION == 'peak':
        divisor = spectrum[frequency != 0].max(axis=0)
    else:
        raise ValueError(f'Unknown PSD_NORMALIZATION: {PSD_NORMALIZATION!r}')
    return np.divide(image, divisor, out=np.zeros_like(image), where=divisor != 0)


class FrequencyRangeDialog(simpledialog.Dialog):
    def __init__(self, parent, entries, difference=False):
        self.entries = entries
        self.difference = difference
        super().__init__(parent, title=('PSD positive minus negative' if difference
                                       else 'PSD frequency range'))

    def body(self, master):
        tk.Label(master, text='Minimum frequency (Hz)').grid(row=0, column=0)
        tk.Label(master, text='Maximum frequency (Hz)').grid(row=1, column=0)
        self.lower = tk.Entry(master)
        self.upper = tk.Entry(master)
        self.lower.grid(row=0, column=1)
        self.upper.grid(row=1, column=1)
        self.lower.insert(0, '0')
        self.upper.insert(0, f"{self.entries[0]['freq'].max():g}")
        self.symmetric = tk.BooleanVar(value=True)
        if self.difference:
            tk.Label(master, text='Positive [min, max] minus negative [-max, -min]; min >= 0'
                     ).grid(row=2, column=0, columnspan=2)
        else:
            tk.Checkbutton(master, text='Symmetric: also include [-maximum, -minimum]',
                           variable=self.symmetric).grid(row=2, column=0, columnspan=2)
        self.sources = [f"{i + 1}: {entry['label']}" for i, entry in enumerate(self.entries)]
        self.source = tk.StringVar(value=self.sources[0])
        if len(self.entries) > 1:
            tk.Label(master, text='Image source').grid(row=3, column=0)
            tk.OptionMenu(master, self.source, *self.sources).grid(row=3, column=1)
        return self.lower

    def validate(self):
        try:
            lower, upper = float(self.lower.get()), float(self.upper.get())
            index = self.sources.index(self.source.get())
            image = frequency_range_image(self.entries[index], lower, upper,
                                          self.symmetric.get(), difference=self.difference)
        except ValueError as exc:
            messagebox.showerror('Invalid frequency range', str(exc), parent=self)
            return False
        self.result = (image, lower, upper, self.symmetric.get(), index)
        return True


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
        self.fit_button = tk.Button(bar, text='Fit pixels', command=self.fit_pixels, state='disabled')
        self.fit_button.pack(side='left')
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
        self.fit_button.config(state='normal')
        self.moment = moment
        self.image_ax.clear()
        self.spectrum_ax.clear()
        self.image_artist = self.image_ax.imshow(moment, origin='upper', cmap='gray')
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

    def fit_pixels(self):
        if not self.entries:
            return
        FitDialog(self.root, tuple(self.entries))

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


class FitDialog:
    """Own a snapshot of the selected datasets and a cancellable fitting worker."""

    def __init__(self, parent, entries):
        self.entries = entries
        self.window = tk.Toplevel(parent)
        self.window.title('Fit every pixel')
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.running = False
        self.closed = False
        self.dataset = tk.StringVar()
        self.model = tk.StringVar(value=next(iter(FIT_MODELS)))
        self.low = tk.StringVar(value='0')
        self.high = tk.StringVar()
        self.symmetric = tk.BooleanVar(value=True)
        body = ttk.Frame(self.window, padding=12)
        body.pack(fill='both', expand=True)
        self.controls = []
        labels = [f"{i + 1}: {entry['label']}" for i, entry in enumerate(entries)]
        for row, (label, variable, choices) in enumerate((
                ('Dataset', self.dataset, labels), ('Model', self.model, list(FIT_MODELS)))):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky='w')
            widget = ttk.Combobox(body, textvariable=variable, values=choices,
                                  state='readonly', width=48)
            widget.grid(row=row, column=1, sticky='ew', pady=3)
            self.controls.append((widget, 'readonly'))
        self.dataset_box = self.controls[0][0]
        self.dataset_box.current(0)
        self.dataset_box.bind('<<ComboboxSelected>>', self.update_range)
        ttk.Label(body, text=FIT_MODELS[self.model.get()]['formula'] + '\nW = standard deviation (Hz); K, A ≥ 0; W > 0').grid(
            row=2, column=0, columnspan=2, pady=6)
        for row, (label, variable) in enumerate((('Minimum (Hz)', self.low),
                                                ('Maximum (Hz)', self.high)), start=3):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky='w')
            widget = ttk.Entry(body, textvariable=variable)
            widget.grid(row=row, column=1, sticky='ew', pady=3)
            self.controls.append((widget, 'normal'))
        symmetric = ttk.Checkbutton(body, text='Include symmetric negative range', variable=self.symmetric)
        symmetric.grid(row=5, column=0, columnspan=2, sticky='w')
        self.controls.append((symmetric, 'normal'))
        ttk.Label(body, text=f'All spatial pixels · normalization: {PSD_NORMALIZATION} · DC excluded').grid(
            row=6, column=0, columnspan=2, pady=6)
        self.progress = ttk.Progressbar(body, mode='determinate')
        self.progress.grid(row=7, column=0, columnspan=2, sticky='ew')
        self.status = ttk.Label(body, text='Ready')
        self.status.grid(row=8, column=0, columnspan=2, sticky='w', pady=6)
        self.start_button = ttk.Button(body, text='Fit', command=self.start)
        self.start_button.grid(row=9, column=0)
        self.cancel_button = ttk.Button(body, text='Cancel', command=self.cancel_fit, state='disabled')
        self.cancel_button.grid(row=9, column=1)
        body.columnconfigure(1, weight=1)
        self.update_range()

    def update_range(self, event=None):
        frequency = self.entries[self.dataset_box.current()]['freq']
        positive = frequency[frequency > 0]
        self.low.set('0')
        self.high.set(str(float(positive.max())) if positive.size else '0')

    def start(self):
        entry = self.entries[self.dataset_box.current()]
        try:
            low, high = float(self.low.get()), float(self.high.get())
            symmetric, model = self.symmetric.get(), self.model.get()
            fit_frequency_mask(entry['freq'], low, high, symmetric)
        except ValueError as exc:
            messagebox.showerror('Invalid fitting range', str(exc), parent=self.window)
            return
        self.running = True
        self.cancel.clear()
        for control, _ in self.controls:
            control.config(state='disabled')
        self.start_button.config(state='disabled')
        self.cancel_button.config(state='normal')
        self.progress.config(maximum=np.prod(entry['spectrum'].shape[1:]), value=0)
        self.status.config(text='Fitting…')

        def worker():
            try:
                maps = fit_pixel_maps(entry, low, high, symmetric, model,
                                      progress=lambda done, total: self.events.put(('progress', done, total)),
                                      cancel=self.cancel)
                self.events.put(('done', maps))
            except Exception as exc:
                self.events.put(('error', str(exc)))

        self.run_description = (f"{entry['label']}\n{model}: {FIT_MODELS[model]['formula']}\n"
                                f'{low:g}–{high:g} Hz; symmetric: {symmetric}; normalization: {PSD_NORMALIZATION}')
        threading.Thread(target=worker, daemon=True).start()
        self.window.after(100, self.poll)

    def cancel_fit(self):
        self.cancel.set()
        self.cancel_button.config(state='disabled')
        self.status.config(text='Cancelling…')

    def close(self):
        self.closed = True
        self.cancel.set()
        self.window.destroy()

    def poll(self):
        if self.closed:
            return
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            if event[0] == 'progress':
                self.progress.config(value=event[1])
                self.status.config(text=f'{event[1]:,} / {event[2]:,} pixels')
                continue
            self.running = False
            for control, state in self.controls:
                control.config(state=state)
            self.start_button.config(state='normal')
            self.cancel_button.config(state='disabled')
            if event[0] == 'error':
                self.status.config(text='Fit failed')
                messagebox.showerror('Fit failed', event[1], parent=self.window)
            elif event[1] is None or self.cancel.is_set():
                self.status.config(text='Cancelled')
            else:
                maps = event[1]
                success = int(np.isfinite(maps['R²']).sum())
                self.status.config(text=f'Done: {success:,} successful; {maps["R²"].size - success:,} failed')
                if success:
                    show_fit_maps(self.window.master, maps, self.run_description)
                else:
                    messagebox.showinfo('No successful fits',
                                        'All pixels failed or had constant, nonfinite, or insufficient data.',
                                        parent=self.window)
        if self.running:
            self.window.after(100, self.poll)


def show_fit_maps(parent, maps, description):
    window = tk.Toplevel(parent)
    window.title('Pixel fit maps')
    ttk.Label(window, text=description).pack(padx=10, pady=6)
    success = int(np.isfinite(maps['R²']).sum())
    ttk.Label(window, text=f'{success:,} successful; {maps["R²"].size - success:,} failed pixels').pack()
    choice = tk.StringVar(value=next(iter(maps)))
    selector = ttk.Combobox(window, textvariable=choice,
                            values=['W (Hz)' if name == 'W' else name for name in maps], state='readonly')
    selector.pack(pady=6)
    figure = Figure(figsize=(7, 6), constrained_layout=True)
    ax = figure.subplots()
    cmap = colormaps['viridis'].copy()
    cmap.set_bad('lightgray')
    image = ax.imshow(np.ma.masked_invalid(maps[choice.get()]), origin='upper', cmap=cmap)
    colorbar = figure.colorbar(image, ax=ax)
    canvas = FigureCanvasTkAgg(figure, master=window)
    canvas.get_tk_widget().pack(fill='both', expand=True)
    NavigationToolbar2Tk(canvas, window)

    def update(event=None):
        label = choice.get()
        name = 'W' if label == 'W (Hz)' else label
        values = maps[name]
        finite = values[np.isfinite(values)]
        image.set_data(np.ma.masked_invalid(values))
        if finite.size:
            low, high = float(finite.min()), float(finite.max())
            if low == high:
                delta = max(abs(low) * 0.01, 1e-12)
                low, high = low - delta, high + delta
            image.set_clim(low, high)
        colorbar.set_label(label)
        ax.set_title(label)
        ax.set_xlabel('x (pixel)')
        ax.set_ylabel('y (pixel)')
        canvas.draw_idle()

    selector.bind('<<ComboboxSelected>>', update)
    update()


if __name__ == '__main__':
    App()
