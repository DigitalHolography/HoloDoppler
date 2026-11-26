"""Paint manual DopplerView-compatible masks over time-averaged HD moments.

Run: python scripts/h5_exploration/h5_mask_painter.py [file_path] [--output masks.h5]
file_path may be a recording, run folder, *_HD folder, h5 folder, or HDF5.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import h5py
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.patches import Circle


MASK_PATHS = {
    'Artery': 'segmentation/Retina/artery_mask',
    'Vein': 'segmentation/Retina/vein_mask',
    'Optic disc': 'segmentation/OpticDisc/mask',
}
COLORS = {'Artery': (1, .15, .1), 'Vein': (.1, .45, 1),
          'Optic disc': (1, .8, .1)}
THRESHOLD = .5


def resolve_input(file_path):
    """Resolve the alphabetically first HDF5 and its standard DV companion."""
    path = Path(file_path).expanduser().resolve()
    if path.suffix.lower() in ('.h5', '.hdf5') and path.is_file():
        source = path
        folder = path.parent
    else:
        if path.is_dir():
            folder = path
        else:
            # Also accept an acquisition path when only its processed run exists.
            folder = path.with_suffix('')
        if folder.name.lower() == 'h5':
            pass
        elif folder.name.endswith('_HD'):
            folder = folder / 'h5'
        else:
            folder = folder / f'{folder.name}_HD' / 'h5'
        files = sorted((p for p in folder.glob('*')
                        if p.is_file() and p.suffix.lower() in ('.h5', '.hdf5')),
                       key=lambda p: p.name)
        if not files:
            raise FileNotFoundError(f'No HDF5 files in {folder}')
        source = files[0]
    if folder.name.lower() == 'h5' and folder.parent.name.endswith('_HD'):
        stem = folder.parent.name[:-3]
        run = folder.parent.parent
    else:
        stem = source.stem.removesuffix('_HD_output').removesuffix('_HD')
        run = source.parent
    output = run / f'{stem}_DV' / 'h5' / f'{stem}_DV.h5'
    return source, output


def load_background(path):
    """Stream a finite-sample time mean; prefer moment0ff over moment0."""
    with h5py.File(path, 'r') as handle:
        names = []
        handle.visititems(lambda name, obj: names.append(name)
                          if isinstance(obj, h5py.Dataset) else None)
        selected = None
        for key in ('moment0ff', 'moment0'):
            matches = [n for n in names if n.rsplit('/', 1)[-1] == key]
            if matches:
                selected = key if key in matches else sorted(matches)[0]
                break
        if selected is None:
            raise ValueError('No moment0ff or moment0 dataset found.')
        data = handle[selected]
        if data.ndim != 3 or not all(data.shape) or data.dtype.kind not in 'biuf':
            raise ValueError(f'{selected} must be a real (NT, NY, NX) array; got {data.shape}.')
        total = np.zeros(data.shape[1:], dtype=np.float64)
        count = np.zeros(data.shape[1:], dtype=np.int64)
        # Bound temporary storage to approximately 32 MiB, or one frame.
        batch = max(1, (32 * 1024**2) // (data.shape[1] * data.shape[2] * 8))
        for start in range(0, data.shape[0], batch):
            values = np.asarray(data[start:start + batch], dtype=np.float64)
            valid = np.isfinite(values)
            total += np.where(valid, values, 0).sum(axis=0)
            count += valid.sum(axis=0)
        mean = np.divide(total, count, out=np.zeros_like(total), where=count > 0)
    return mean, selected


def load_masks(path, shape):
    masks = {name: np.zeros(shape, np.float32) for name in MASK_PATHS}
    if not Path(path).exists():
        return masks
    with h5py.File(path, 'r') as handle:
        for name, key in MASK_PATHS.items():
            probability = key + '_probability'
            key = probability if probability in handle else key
            if key not in handle:
                continue
            values = np.asarray(handle[key], dtype=np.float32)
            if values.shape != shape or not np.isfinite(values).all():
                raise ValueError(f'{key}: expected finite mask of shape {shape}.')
            if np.any((values < 0) | (values > 1)):
                raise ValueError(f'{key}: values must be in [0, 1].')
            masks[name] = values
    return masks


def paint_segment(mask, start, end, radius, value):
    """Rasterize a continuous round brush segment in native pixel coordinates."""
    x0, y0 = start
    x1, y1 = end
    if not np.isfinite([x0, y0, x1, y1, radius, value]).all() or radius <= 0:
        raise ValueError('Brush coordinates and value must be finite; radius must be positive.')
    if not 0 <= value <= 1:
        raise ValueError('Brush value must be in [0, 1].')
    ny, nx = mask.shape
    left, right = max(0, int(np.floor(min(x0, x1) - radius))), min(nx, int(np.ceil(max(x0, x1) + radius)) + 1)
    top, bottom = max(0, int(np.floor(min(y0, y1) - radius))), min(ny, int(np.ceil(max(y0, y1) + radius)) + 1)
    if left >= right or top >= bottom:
        return
    yy, xx = np.mgrid[top:bottom, left:right]
    dx, dy = x1 - x0, y1 - y0
    length2 = dx * dx + dy * dy
    t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / length2, 0, 1) if length2 else 0
    covered = (xx - x0 - t * dx)**2 + (yy - y0 - t * dy)**2 <= radius**2
    mask[top:bottom, left:right][covered] = value


def save_masks(path, masks, source, moment_name):
    """Atomically update mask fields, preserving unrelated existing DV results."""
    path, source = Path(path).resolve(), Path(source).resolve()
    if path == source:
        raise ValueError('The mask output must differ from the source HD file.')
    shape = np.asarray(masks['Artery']).shape
    if len(shape) != 2 or not all(shape):
        raise ValueError('Masks must be nonempty 2-D arrays.')
    for name in MASK_PATHS:
        values = np.asarray(masks[name])
        if values.shape != shape or not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
            raise ValueError(f'{name}: expected finite [0, 1] mask of shape {shape}.')
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp = tempfile.mkstemp(suffix='.h5', dir=path.parent)
    os.close(descriptor)
    try:
        with h5py.File(temp, 'w') as handle:
            if path.exists():
                with h5py.File(path, 'r') as previous:
                    for key in previous:
                        previous.copy(key, handle)
                    handle.attrs.update(dict(previous.attrs))

            def put(key, value, **attrs):
                if key in handle:
                    del handle[key]
                parent, leaf = key.rsplit('/', 1)
                group = handle.require_group(parent)
                array = np.asarray(value)
                dataset = group.create_dataset(leaf, data=value,
                                               **({'compression': 'gzip'} if array.ndim == 2 else {}))
                dataset.attrs.update(attrs)
                dataset.attrs['manual'] = True
                dataset.attrs['annotation_method'] = 'manual_brush'

            for name, key in MASK_PATHS.items():
                put(key, masks[name] > THRESHOLD, axis_order='y,x', threshold=THRESHOLD)
                put(key + '_probability', np.asarray(masks[name], np.float32), axis_order='y,x')
            vessel = np.maximum(masks['Artery'], masks['Vein'])
            # Topology labels from a previous segmentation no longer describe these masks.
            if 'segmentation/Retina/labeled_vessels' in handle:
                del handle['segmentation/Retina/labeled_vessels']
            put('segmentation/Retina/vessel_mask', vessel > THRESHOLD, axis_order='y,x')
            put('segmentation/Retina/vessel_segmentation_logits', vessel.astype(np.float32), axis_order='y,x')
            # DV center is (x, y); dimensions follow its mask bounding box.
            yy, xx = np.nonzero(masks['Optic disc'] > THRESHOLD)
            for key in ('center', 'width', 'height'):
                full = 'segmentation/OpticDisc/' + key
                if full in handle:
                    del handle[full]
            if xx.size:
                put('segmentation/OpticDisc/center', np.array([(xx.min() + xx.max()) / 2,
                                                              (yy.min() + yy.max()) / 2], np.float32),
                    coordinate_order='x,y')
                put('segmentation/OpticDisc/width', np.float32(xx.max() - xx.min()))
                put('segmentation/OpticDisc/height', np.float32(yy.max() - yy.min()))
            put('provenance/manual', True)
            put('provenance/annotation_method', 'manual_brush')
            put('provenance/source_h5', str(source))
            put('provenance/background_dataset', moment_name)
            put('provenance/modified_utc', datetime.now(timezone.utc).isoformat())
            handle.attrs['manual'] = True
            handle.attrs['annotation_method'] = 'manual_brush'
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class App:
    def __init__(self, file_path=None, output=None):
        self.root = tk.Tk()
        self.root.title('H5 manual mask painter')
        self.root.geometry('1150x850')
        self.source = None
        self.output_override = output
        self.dirty = False
        self.stroke = None
        self.undo_stack, self.redo_stack = [], []
        bar = ttk.Frame(self.root, padding=6)
        bar.pack(fill='x')
        for text, command in [('Open file', self.open_file), ('Open run folder', self.open_folder),
                              ('Save', self.save), ('Save as', self.save_as),
                              ('Undo', self.undo), ('Redo', self.redo)]:
            ttk.Button(bar, text=text, command=command).pack(side='left', padx=2)
        controls = ttk.Frame(self.root, padding=6)
        controls.pack(fill='x')
        self.layer = tk.StringVar(value='Artery')
        self.selector = ttk.Combobox(controls, textvariable=self.layer, values=list(MASK_PATHS),
                                     state='readonly', width=12)
        self.selector.pack(side='left')
        self.selector.bind('<<ComboboxSelected>>', lambda event: self.refresh())
        ttk.Button(controls, text='Next mask', command=self.next_mask).pack(side='left', padx=4)
        ttk.Label(controls, text='Radius (px)').pack(side='left')
        self.radius = tk.DoubleVar(value=5)
        ttk.Spinbox(controls, from_=.5, to=500, increment=.5, textvariable=self.radius, width=6).pack(side='left')
        self.soft = tk.BooleanVar(value=False)
        ttk.Checkbutton(controls, text='Soft value [0,1]', variable=self.soft).pack(side='left', padx=4)
        self.value = tk.DoubleVar(value=1)
        ttk.Spinbox(controls, from_=0, to=1, increment=.05, textvariable=self.value, width=5).pack(side='left')
        self.erase = tk.BooleanVar(value=False)
        ttk.Checkbutton(controls, text='Eraser', variable=self.erase).pack(side='left', padx=4)
        self.show_all = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text='All layers', variable=self.show_all, command=self.refresh).pack(side='left')
        ttk.Button(controls, text='Clear layer', command=self.clear).pack(side='left', padx=4)
        display = ttk.Frame(self.root, padding=6)
        display.pack(fill='x')
        ttk.Label(display, text='Overlay opacity').pack(side='left')
        self.opacity = tk.DoubleVar(value=.5)
        ttk.Scale(display, from_=0, to=1, variable=self.opacity,
                  command=lambda _: self.refresh()).pack(side='left', fill='x', expand=True)
        ttk.Label(display, text='Gamma').pack(side='left', padx=6)
        self.gamma = tk.DoubleVar(value=1)
        ttk.Scale(display, from_=.2, to=3, variable=self.gamma,
                  command=lambda _: self.refresh()).pack(side='left', fill='x', expand=True)
        self.figure = Figure(figsize=(9, 7))
        self.ax = self.figure.add_subplot()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root, pack_toolbar=False)
        self.toolbar.pack(side='bottom', fill='x')
        self.status = tk.StringVar(value='Open a recording or run folder to begin.')
        ttk.Label(self.root, textvariable=self.status, wraplength=1100).pack(side='bottom', fill='x', padx=8)
        ttk.Label(self.root, text='Left drag: paint | Right drag: erase | Pan/zoom: toolbar | '
                  'Ctrl+Z/Y: undo/redo | Ctrl+S: save | Masks are independent and may overlap.').pack(side='bottom')
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        for name, callback in [('button_press_event', self.press), ('motion_notify_event', self.move),
                               ('button_release_event', self.release)]:
            self.canvas.mpl_connect(name, callback)
        self.root.bind('<Control-z>', lambda _: self.undo())
        self.root.bind('<Control-y>', lambda _: self.redo())
        self.root.bind('<Control-s>', lambda _: self.save())
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        if file_path:
            self.load(file_path)

    def can_discard(self):
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel('Unsaved masks', 'Save your masks before continuing?')
        return self.save() if answer else answer is False

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[('Recording / HDF5', '*.holo *.cine *.h5 *.hdf5'),
                                                    ('All files', '*.*')])
        if path:
            self.load(path)

    def open_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.load(path)

    def load(self, path):
        if not self.can_discard():
            return
        try:
            source, output = resolve_input(path)
            output = Path(self.output_override).expanduser().resolve() if self.output_override else output
            if source == output:
                raise ValueError('Output must differ from source HD file.')
            background, moment = load_background(source)
            masks = load_masks(output, background.shape)
        except Exception as exc:
            messagebox.showerror('Cannot open', str(exc))
            return
        self.source, self.output, self.moment = source, output, moment
        self.masks = masks
        low, high = np.percentile(background, [1, 99])
        self.background = np.clip((background - low) / (high - low), 0, 1) if high > low else np.zeros_like(background)
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.stroke, self.dirty = None, False
        self.layer.set('Artery')
        self.ax.clear()
        self.image = self.ax.imshow(self.background, cmap='gray', origin='upper', vmin=0, vmax=1)
        self.overlay = self.ax.imshow(np.zeros((*background.shape, 4)), origin='upper', interpolation='nearest')
        self.cursor = Circle((0, 0), self.radius.get(), fill=False, color='white', linewidth=.8, visible=False)
        self.ax.add_patch(self.cursor)
        self.ax.set(xlabel='x (pixel)', ylabel='y (pixel)')
        self.refresh()

    def refresh(self):
        if self.source is None:
            return
        rgba = np.zeros((*self.background.shape, 4), np.float32)
        layers = list(MASK_PATHS) if self.show_all.get() else [self.layer.get()]
        for name in layers:
            alpha = self.masks[name] * self.opacity.get()
            rgba[..., :3] = rgba[..., :3] * (1 - alpha[..., None]) + np.array(COLORS[name]) * alpha[..., None]
            rgba[..., 3] = rgba[..., 3] + alpha * (1 - rgba[..., 3])
        # Convert premultiplied colors to straight alpha for imshow.
        np.divide(rgba[..., :3], rgba[..., 3, None], out=rgba[..., :3], where=rgba[..., 3, None] > 0)
        self.overlay.set_data(rgba)
        self.image.set_data(self.background ** self.gamma.get())
        self.ax.set_title(f'{self.source.name} / mean({self.moment}, axis=0) / {self.layer.get()}')
        self.status.set(f'{"Unsaved | " if self.dirty else ""}{self.background.shape} | Output: {self.output}')
        self.canvas.draw_idle()

    def remember(self, name):
        self.undo_stack.append((name, self.masks[name].copy()))
        self.undo_stack = self.undo_stack[-30:]
        self.redo_stack.clear()

    def press(self, event):
        if self.source is None or event.inaxes != self.ax or self.toolbar.mode or event.button not in (1, 3):
            return
        try:
            radius = self.radius.get()
            value = 0 if event.button == 3 or self.erase.get() else self.value.get() if self.soft.get() else 1
            if not np.isfinite([radius, value]).all() or radius <= 0 or not 0 <= value <= 1:
                raise ValueError('Use a positive brush radius and a value in [0, 1].')
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror('Invalid brush', str(exc))
            return
        name = self.layer.get()
        self.remember(name)
        self.stroke = (name, radius, value, (event.xdata, event.ydata))
        self.move(event)

    def move(self, event):
        if self.source is None:
            return
        inside = event.inaxes == self.ax and not self.toolbar.mode
        self.cursor.set_visible(inside)
        if inside:
            self.cursor.center = (event.xdata, event.ydata)
            try:
                self.cursor.set_radius(self.radius.get())
            except tk.TclError:
                pass
        if self.stroke is not None:
            name, radius, value, previous = self.stroke
            if inside:
                point = (event.xdata, event.ydata)
                paint_segment(self.masks[name], previous or point, point, radius, value)
                self.stroke = (name, radius, value, point)
                self.dirty = True
                self.refresh()
            else:
                self.stroke = (name, radius, value, None)
        self.canvas.draw_idle()

    def release(self, event):
        self.stroke = None

    def next_mask(self):
        names = list(MASK_PATHS)
        self.layer.set(names[(names.index(self.layer.get()) + 1) % len(names)])
        self.refresh()

    def clear(self):
        if self.source is not None:
            name = self.layer.get()
            self.remember(name)
            self.masks[name].fill(0)
            self.dirty = True
            self.refresh()

    def history(self, source, destination):
        if source:
            name, mask = source.pop()
            destination.append((name, self.masks[name].copy()))
            self.masks[name] = mask
            self.layer.set(name)
            self.dirty = True
            self.refresh()

    def undo(self):
        self.history(self.undo_stack, self.redo_stack)

    def redo(self):
        self.history(self.redo_stack, self.undo_stack)

    def save(self):
        if self.source is None:
            return False
        try:
            save_masks(self.output, self.masks, self.source, self.moment)
        except Exception as exc:
            messagebox.showerror('Cannot save', str(exc))
            return False
        self.dirty = False
        self.refresh()
        return True

    def save_as(self):
        if self.source is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.h5', initialfile=self.output.name,
                                          filetypes=[('HDF5', '*.h5')])
        if path:
            previous = self.output
            self.output = Path(path)
            if not self.save():
                self.output = previous

    def close(self):
        if self.can_discard():
            self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file_path', nargs='?', help='Recording, run folder, HD folder, or HDF5 file')
    parser.add_argument('--output', type=Path, help='Override the standard DV companion output')
    args = parser.parse_args()
    app = App(args.file_path, args.output)
    app.root.mainloop()


if __name__ == '__main__':
    main()
