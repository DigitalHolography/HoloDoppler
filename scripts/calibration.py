from holodoppler.file_io import FileReaderFactory
import json
import imageio.v3 as iio
from holodoppler.plotting import DebugPlotterManager
import os
from pathlib import Path

from scipy.fftpack import fft

try:
    import cupy as cp
except ImportError:
    cp = None
import numpy as np


def _load_json(path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON file: {path}\n{exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit(f"Config JSON must contain an object at top level: {path}")

    return data


def plot_debug_safe(res, parameters):
    debug_manager = DebugPlotterManager(parameters) if parameters.get("debug") else None

    out = debug_manager.plot_all(res) if parameters.get("debug") else {}

    return out


def calibration_calc_res(file_reader, parameters):
    res = {}

    frames = file_reader.read_frames(
        parameters["first_frame"], parameters["batch_size"]
    )

    N = frames.shape[0] * 1

    # frames = np.ones_like(frames)

    res["average_signal"] = np.mean(frames, axis=(-1, -2))

    ft = fft(frames, n=N, axis=0)

    psd = np.abs(ft) ** 2

    res["spectrum_line"] = np.mean(psd, axis=(-1, -2))

    freqs = np.fft.fftfreq(N, 1 / parameters["sampling_freq"])

    idxs = (parameters["high_freq"] > np.abs(freqs)) & (
        np.abs(freqs) > parameters["low_freq"]
    )

    freqs = freqs[idxs]

    res["M0"] = np.sum(psd[idxs] * (freqs[..., np.newaxis, np.newaxis] ** 0), axis=0)

    return res


def save_debug_images(debug_dict, save_dir, prefix="debug"):
    os.makedirs(save_dir, exist_ok=True)

    for key, img in debug_dict.items():
        if img is None:
            continue
        if cp is not None and isinstance(img, cp.ndarray):
            img = img.get()
        img_np = img

        if img_np.dtype != np.uint8:
            img_min = np.min(img_np)
            img_max = np.max(img_np)

            if img_max > img_min:
                img_np = (img_np - img_min) / (img_max - img_min + 1e-12)

            img_np = (img_np * 255).astype(np.uint8)

        filename = os.path.join(save_dir, f"{prefix}_{key}.png")

        iio.imwrite(filename, img_np)

        print(f"Saved: {filename} | shape={img_np.shape} dtype={img_np.dtype}")


def _cmd(args):

    file_path = Path(args.input)
    file_name = file_path.stem

    file_reader = FileReaderFactory.create(file_path)
    file_reader.open()
    print(file_reader)
    params_path = Path(r"./parameters/default_parameters_debug.json")
    parameters = _load_json(params_path)
    res = calibration_calc_res(file_reader, parameters)
    file_reader.close()
    debug_imgs = plot_debug_safe(res, parameters)

    # --- Add M0 ---
    if "M0" in res:
        M0 = res["M0"]
        if cp is not None and isinstance(M0, cp.ndarray):
            M0 = M0.get()
        M0 = (M0 - np.min(M0)) / (np.max(M0) - np.min(M0) + 1e-12)
        debug_imgs["M0"] = (M0 * 255).astype(np.uint8)

    print("DEBUG KEYS:", list(debug_imgs.keys()))

    # --- Save ---
    save_dir = "./debug_outputs"
    save_debug_images(debug_imgs, save_dir)

    filename = os.path.join(save_dir, f"{file_name}_spectrum_calibration.npy")
    np.save(filename, res["spectrum_line"])

    return 0


import argparse


def _existing_file(value: str) -> Path:
    path = Path(value).expanduser().resolve()

    if not path.is_file():
        raise argparse.ArgumentTypeError(f"File does not exist: {path}")

    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="calibration command-line tools.",
    )

    parser.add_argument(
        "input",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Input file path.",
    )
    parser.set_defaults(func=_cmd)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    main()
