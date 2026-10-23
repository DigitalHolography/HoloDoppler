"""Opt-in release checks, also runnable with ``python -m holodoppler._frozen_smoke``.

The frozen launcher calls ``main(report_path)`` for ``--self-test <report.json>``.
Nothing in this module runs during normal application startup.
"""

from __future__ import annotations

import ctypes
from importlib import import_module
import json
import os
from pathlib import Path
import pkgutil
import sys
import tempfile
import traceback


# An empty/incomplete frozen registry must not accidentally pass discovery.
_REQUIRED_PIPELINES = {
    "default", "lsci", "pca_accumulation", "sliding_shack_hartmann", "split_apertures",
}


class _SkipCheck(Exception):
    """A check cannot run because the machine has no CUDA device."""


def _require(condition, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _cpu() -> str:
    import numpy as np
    from scipy import fft, linalg, ndimage
    from holodoppler.core.filtering import svd_filter

    data = np.arange(16, dtype=np.float64).reshape(4, 4)
    _require(np.allclose(fft.ifft2(fft.fft2(data)), data), "SciPy FFT roundtrip failed")
    matrix = np.array([[2., 1.], [1., 2.]])
    values, vectors = linalg.eigh(matrix)
    _require(np.allclose(values, [1., 3.]), "SciPy eigendecomposition failed")
    _require(np.allclose(matrix @ vectors, vectors * values), "Invalid eigenvectors")
    _require(np.allclose(np.linalg.eigvalsh(matrix), values), "NumPy LAPACK failed")
    filtered = ndimage.gaussian_filter(data, 1)
    _require(np.isfinite(filtered).all(), "SciPy Gaussian filter failed")
    _require(ndimage.zoom(filtered, 2, order=1).shape == (8, 8), "SciPy resize failed")
    _require(ndimage.uniform_filter(data, 3).shape == data.shape, "SciPy LSCI filter failed")
    frames = np.arange(48, dtype=np.float64).reshape(3, 4, 4).astype(np.complex128)
    result = svd_filter(np, linalg, frames, 1)
    _require(result.shape == frames.shape and np.isfinite(result).all(), "SVD filter failed")
    return "NumPy/SciPy FFT, LAPACK, ndimage and application SVD filter"


def _pipelines() -> str:
    import holodoppler.pipelines as package

    registered = set(package.pipelines)
    _require(_REQUIRED_PIPELINES <= registered,
             f"Missing pipeline registrations: {sorted(_REQUIRED_PIPELINES - registered)}")
    discovered = [info.name for info in pkgutil.iter_modules(package.__path__)
                  if not info.name.startswith("_")]
    _require(bool(discovered), "No pipeline modules were discovered")
    for name in discovered:
        import_module(f"{package.__name__}.{name}")
    for name, function in package.pipelines.items():
        module_name, function_name = function.__qualname__.split(".")
        module = import_module(f"{package.__name__}.{module_name}")
        _require(callable(getattr(module, function_name, None)), f"Invalid pipeline entry: {name}")
    return ", ".join(sorted(discovered))


def _images_and_hdf5() -> str:
    import h5py
    import numpy as np
    from PIL import Image

    data = np.arange(256, dtype=np.uint16).reshape(16, 16)
    with tempfile.TemporaryDirectory(prefix="holodoppler-smoke-io-") as directory:
        root = Path(directory)
        for extension in ("png", "tiff"):
            path = root / f"image.{extension}"
            Image.fromarray(data).save(path)
            image = Image.open(path)
            try:
                _require(np.array_equal(np.asarray(image), data), f"{extension} roundtrip failed")
            finally:
                # Explicit close also releases TIFF's Windows memory mapping.
                image.close()
        with h5py.File(root / "image.h5", "w") as file:
            file.create_dataset("image", data=data, compression="gzip")
        with h5py.File(root / "image.h5", "r") as file:
            _require(np.array_equal(file["image"][:], data), "HDF5 roundtrip failed")
    return "Pillow 16-bit PNG/TIFF and compressed HDF5 roundtrips"


def _plots() -> str:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.backends.backend_pdf import FigureCanvasPdf
    from matplotlib.figure import Figure

    with tempfile.TemporaryDirectory(prefix="holodoppler-smoke-plots-") as directory:
        figure = Figure(figsize=(2, 2))
        figure.subplots().plot([0, 1, 2], [1, 3, 2])
        png, pdf = Path(directory) / "plot.png", Path(directory) / "plot.pdf"
        FigureCanvasAgg(figure).print_png(str(png))
        FigureCanvasPdf(figure).print_pdf(str(pdf))
        _require(png.read_bytes().startswith(b"\x89PNG"), "Agg PNG export failed")
        _require(pdf.read_bytes().startswith(b"%PDF"), "PDF export failed")
    return "Matplotlib Agg and PDF rendering, including fonts"


def _gui() -> str:
    from tkinter import ttk
    from tkinterdnd2 import DND_FILES, TkinterDnD
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from PIL import Image, ImageTk
    from holodoppler.ui.paths import logo_path, parameters_dir
    from holodoppler.ui.theme import apply_theme
    import yaml

    root = TkinterDnD.Tk()
    root.withdraw()
    try:
        _require(apply_theme(root, "dark"), "sv-ttk dark theme failed to load")
        _require(apply_theme(root, "light"), "sv-ttk light theme failed to load")
        label = ttk.Label(root, text="HoloDoppler release check")
        label.drop_target_register(DND_FILES)
        label.dnd_bind("<<Drop>>", lambda event: None)
        figure = Figure(figsize=(1, 1))
        figure.subplots().plot([0, 1], [0, 1])
        canvas = FigureCanvasTkAgg(figure, master=root)
        canvas.draw()
        logo = logo_path()
        _require(logo is not None, "Application logo is missing")
        with Image.open(logo) as image:
            photo = ImageTk.PhotoImage(image, master=root)
        _require(photo.width() > 0, "Tk/Pillow image support failed")
        presets = list(parameters_dir().glob("*.yaml"))
        _require(bool(presets), "Parameter presets are missing")
        for preset in presets:
            _require(isinstance(yaml.safe_load(preset.read_text(encoding="utf-8")), dict),
                     f"Invalid parameter preset: {preset.name}")
        root.update_idletasks()
        canvas.get_tk_widget().destroy()
        label.drop_target_unregister()
    finally:
        root.destroy()
    return "Tk, drag and drop, both sv-ttk themes, TkAgg, logo and parameter presets"


def _video() -> str:
    import imageio.v2 as imageio
    import imageio_ffmpeg
    import numpy as np
    from holodoppler.saving import save_video_imageio

    # Do not allow a developer's external FFmpeg to conceal a missing bundled one.
    previous = os.environ.pop("IMAGEIO_FFMPEG_EXE", None)
    try:
        executable = Path(imageio_ffmpeg.get_ffmpeg_exe())
        bundled_binaries = Path(imageio_ffmpeg.__file__).parent / "binaries"
        _require(executable.is_file() and executable.parent == bundled_binaries,
                 "imageio-ffmpeg's packaged FFmpeg executable is missing")
        with tempfile.TemporaryDirectory(prefix="holodoppler-smoke-video-") as directory:
            path = Path(directory) / "video.mp4"
            frames = np.zeros((2, 16, 16, 3), dtype=np.uint8)
            frames[0, :, :, 0] = 200
            frames[1, :, :, 1] = 200
            save_video_imageio(path, frames, fps=2, codec="libx264")
            with imageio.get_reader(str(path), format="ffmpeg") as video:
                _require(video.get_data(0).shape == (16, 16, 3), "H.264 decode failed")
                _require(video.get_data(1).shape == (16, 16, 3), "H.264 second frame missing")
    finally:
        if previous is not None:
            os.environ["IMAGEIO_FFMPEG_EXE"] = previous
    return f"ImageIO H.264 encoding/decoding using {executable.name}"


def _registration() -> str:
    import cv2
    import numpy as np
    from holodoppler.core.registration import apply_ecc_registration

    image = np.random.default_rng(7).random((32, 32), dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 20, 1e-5)
    correlation, warp = cv2.findTransformECC(
        image, image.copy(), np.eye(2, 3, dtype=np.float32), cv2.MOTION_AFFINE, criteria)
    _require(correlation > .99 and np.isfinite(warp).all(), "OpenCV ECC failed")
    registration = np.array([[0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1]], dtype=np.float32)
    result = apply_ecc_registration(image[None], registration)
    _require(np.allclose(result[0], image), "Application OpenCV affine registration failed")
    return "OpenCV ECC and application affine registration"


def _cuda_driver_device_count() -> int | None:
    """Distinguish an absent driver from a broken packaged CUDA runtime."""
    # The NVIDIA driver belongs to the host, so avoid PyInstaller's literal
    # ctypes-DLL collection pattern, which could copy a developer's driver.
    loader = ctypes.WinDLL if os.name == "nt" else ctypes.CDLL
    driver_name = "nvcuda.dll" if os.name == "nt" else "libcuda.so.1"
    try:
        driver = loader(driver_name)
    except OSError:
        return None
    driver.cuInit.argtypes, driver.cuInit.restype = [ctypes.c_uint], ctypes.c_int
    driver.cuDeviceGetCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
    driver.cuDeviceGetCount.restype = ctypes.c_int
    status = driver.cuInit(0)
    if status == 100:  # CUDA_ERROR_NO_DEVICE
        return 0
    _require(status == 0, f"NVIDIA driver initialization failed with status {status}")
    count = ctypes.c_int()
    status = driver.cuDeviceGetCount(ctypes.byref(count))
    _require(status == 0, f"NVIDIA device query failed with status {status}")
    return count.value


def _no_gpu_reason(cp) -> str | None:
    try:
        if cp.cuda.runtime.getDeviceCount() == 0:
            return "No CUDA device is present"
    except cp.cuda.runtime.CUDARuntimeError as exc:
        if exc.status == 100:  # cudaErrorNoDevice
            return "No CUDA device is present"
        if exc.status == 35:  # May be a CPU-only machine or an outdated installed driver.
            if _cuda_driver_device_count() in (None, 0):
                return "No NVIDIA driver/device is present; CPU checks still ran"
        raise
    return None


def _gpu() -> str:
    import cupy as cp
    import numpy as np
    from cupyx.scipy import fft, ndimage
    from scipy import ndimage as cpu_ndimage

    reason = _no_gpu_reason(cp)
    if reason:
        raise _SkipCheck(reason)
    # A fresh cache forces NVRTC compilation and validates bundled headers.
    previous = os.environ.get("CUPY_CACHE_DIR")
    with tempfile.TemporaryDirectory(prefix="holodoppler-smoke-cuda-") as cache:
        os.environ["CUPY_CACHE_DIR"] = cache
        try:
            data = np.arange(16, dtype=np.float64).reshape(4, 4)
            device = cp.asarray(data)
            _require(np.allclose(cp.asnumpy(fft.ifft2(fft.fft2(device))), data), "GPU FFT failed")
            _require(np.allclose(cp.asnumpy(fft.idct(fft.dct(device))), data), "GPU DCT failed")
            matrix = cp.asarray([[2., 1.], [1., 2.]])
            values, vectors = cp.linalg.eigh(matrix)
            _require(np.allclose(cp.asnumpy(values), [1., 3.]), "GPU eigh failed")
            _require(np.allclose(cp.asnumpy(matrix @ vectors), cp.asnumpy(vectors * values)),
                     "GPU BLAS/eigenvectors failed")
            rhs = cp.asarray([3., 3.])
            _require(np.allclose(cp.asnumpy(cp.linalg.solve(matrix, rhs)), [1., 1.]), "GPU solve failed")
            solution = cp.linalg.lstsq(matrix, rhs, rcond=None)[0]
            _require(np.allclose(cp.asnumpy(solution), [1., 1.]), "GPU least squares failed")
            for operation, args, kwargs in (
                ("gaussian_filter", (1,), {}), ("uniform_filter", (3,), {}),
                ("zoom", (2,), {"order": 1}),
                ("affine_transform", (np.eye(2),), {"order": 1}),
                ("map_coordinates", (np.array([[0., 1.], [1., 2.]]),), {"order": 1}),
            ):
                gpu_args = tuple(cp.asarray(arg) if isinstance(arg, np.ndarray) else arg for arg in args)
                actual = getattr(ndimage, operation)(device, *gpu_args, **kwargs)
                expected = getattr(cpu_ndimage, operation)(data, *args, **kwargs)
                _require(np.allclose(cp.asnumpy(actual), expected), f"GPU {operation} failed")
            cp.cuda.runtime.deviceSynchronize()
        finally:
            if previous is None:
                os.environ.pop("CUPY_CACHE_DIR", None)
            else:
                os.environ["CUPY_CACHE_DIR"] = previous
    return "CuPy FFT/DCT, BLAS, eigh/solve/lstsq and freshly compiled ndimage kernels"


_CHECKS = (
    ("cpu", _cpu), ("pipelines", _pipelines), ("images_hdf5", _images_and_hdf5),
    ("plots", _plots), ("gui", _gui), ("video", _video),
    ("registration", _registration), ("gpu", _gpu),
)


def main(report_path: str | Path | None = None) -> int:
    """Run real feature checks and write diagnostics even in a windowed build."""
    report = {"ok": True, "checks": {}}
    for name, check in _CHECKS:
        try:
            result = {"status": "passed", "detail": check()}
        except _SkipCheck as exc:
            result = {"status": "skipped", "detail": str(exc)}
        except Exception as exc:
            report["ok"] = False
            result = {"status": "failed", "detail": str(exc), "traceback": traceback.format_exc()}
        report["checks"][name] = result
    serialized = json.dumps(report, indent=2)
    if report_path is not None:
        Path(report_path).write_text(serialized + "\n", encoding="utf-8")
    if sys.stdout is not None:
        print(serialized)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
