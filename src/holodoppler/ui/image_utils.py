from __future__ import annotations

from pathlib import Path
from typing import Any

import tkinter as tk

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None


def load_photo(path: Path | None, max_size: tuple[int, int], master: tk.Misc) -> tk.PhotoImage | None:
    if path is None or not path.is_file():
        return None

    if Image is not None and ImageTk is not None:
        image = Image.open(path).convert("RGBA")
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image, master=master)

    try:
        return tk.PhotoImage(master=master, file=str(path))
    except tk.TclError:
        return None


def array_to_photo_image(
    array: Any,
    max_size: tuple[int, int],
    master: tk.Misc,
) -> tk.PhotoImage | None:
    if array is None or Image is None or ImageTk is None:
        return None

    import numpy as np

    data = np.asarray(array).squeeze()
    if data.size == 0:
        return None

    if np.iscomplexobj(data):
        data = np.abs(data)

    if data.ndim == 3:
        if data.shape[-1] in {3, 4}:
            pass
        elif data.shape[0] in {3, 4}:
            data = np.moveaxis(data, 0, -1)
        else:
            data = data[0]
    elif data.ndim > 3:
        data = data.reshape((-1, *data.shape[-2:]))[0]

    data = np.nan_to_num(data)
    if data.dtype != np.uint8:
        data = data.astype("float32", copy=False)
        low = float(np.min(data))
        high = float(np.max(data))
        if high > low:
            data = (data - low) / (high - low)
        else:
            data = data * 0
        data = (data * 255).clip(0, 255).astype("uint8")

    image = Image.fromarray(data)
    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGB")
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image, master=master)
