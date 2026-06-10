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

def plot_debug_safe(res,parameters):
    debug_manager = DebugPlotterManager(parameters) if parameters.get("debug") else None
    
    out = debug_manager.plot_all(res) if parameters.get("debug") else {}

    return out

def calibration_calc_res(file_reader, parameters):
    res = {}
    
    frames = file_reader.read_frames(parameters["first_frame"], parameters["batch_size"])
    
    N = frames.shape[0] * 1
    
    
    res["average_signal"] = np.mean(frames, axis=(-1,-2))
    
    ft = fft(frames, n=N, axis=0)
    
    psd = np.abs(ft) ** 2
    
    res["calibration_spectrum_line"] = np.mean(psd, axis=(-1,-2))
    
    freqs = np.fft.fftfreq(N, 1 / parameters["sampling_freq"])
    
    idxs = (parameters["high_freq"] > np.abs(freqs)) & (np.abs(freqs) > parameters["low_freq"])
    
    freqs = freqs[idxs]
    
    res["M0"] = np.sum( psd[idxs] * (freqs[..., np.newaxis, np.newaxis] ** 0),axis=0)
    
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
        

def get_frames(file_path, size= None):
    file_reader = FileReaderFactory.create(file_path)
    file_reader.open()
    if size is None:
        frames = file_reader.read_frames(0, file_reader.file_header["num_frames"])
    else:
        frames = file_reader.read_frames(0, size)
    file_reader.close()
    return frames
    
def _cmd(args):
    
    file_path_ref = Path(args.inputa)
    file_path_obj = Path(args.inputb)
    file_path_ref_obj = Path(args.inputc)
    
    fs = args.fs
    
    frames_ref = get_frames(file_path_ref, size=2048)
    frames_obj = get_frames(file_path_obj, size=2048)
    frames_ref_obj = get_frames(file_path_ref_obj, size=2048)
    
    
    frames_ref = fft(frames_ref, axis=0)
    frames_obj = fft(frames_obj, axis=0)
    frames_ref_obj = fft(frames_ref_obj, axis=0)
    
    frames_int = frames_ref_obj - frames_ref - frames_obj
    
    # frames_int = frames_int / np.sqrt(np.abs(frames_ref) * np.abs(frames_obj) )
    
    frames_int = np.abs(frames_int) **2 
    frames_ref = np.abs(frames_ref) **2 
    frames_obj = np.abs(frames_obj) **2 
    frames_ref_obj = np.abs(frames_ref_obj) **2 
    
    s_ref = np.mean(frames_ref , axis=(-2,-1))
    s_obj = np.mean(frames_obj , axis=(-2,-1))
    s_ref_obj = np.mean(frames_ref_obj , axis=(-2,-1))
    s_int = np.mean(frames_int , axis=(-2,-1))
    
    print(s_ref.shape)
    
    sref = np.fft.fftshift(s_ref)
    sobj = np.fft.fftshift(s_obj)
    stot = np.fft.fftshift(s_ref_obj)
    sint = np.fft.fftshift(s_int)
    
    assert sref.shape == sobj.shape == stot.shape

    n = sref.size
    freq = np.fft.fftshift(np.fft.fftfreq(n, d=1 / args.fs))

    # sref = np.fft.fftshift(sref)
    # sobj = np.fft.fftshift(sobj)
    # stot = np.fft.fftshift(stot)

    eref = np.sum(sref)
    eobj = np.sum(sobj)
    etot = np.sum(stot)
    eint = np.sum(sint)

    print(f"Energy reference     : {eref:.6e}")
    print(f"Energy object        : {eobj:.6e}")
    print(f"Energy total         : {etot:.6e}")
    print(f"Energy interference  : {eint:.6e}")
    print(f"Relative interference: {eint / etot:.6%}")

    eps = 1e-30

    # For log-log, remove f=0 and use positive frequencies only
    pos = freq > 0
    
    import matplotlib.pyplot as plt

    plt.figure(figsize=(9, 5.5))
    plt.loglog(freq[pos], sref[pos] + eps, label=f"Reference, E={eref:.2e}")
    plt.loglog(freq[pos], sobj[pos] + eps, label=f"Object, E={eobj:.2e}")
    plt.loglog(freq[pos], stot[pos] + eps, label=f"Reference + object, E={etot:.2e}")

    plt.xlabel("Frequency [Hz]")
    plt.ylabel(r"Spectrum $|\mathcal{F}\{I(t)\}|^2$")
    plt.title("Intensity spectra")
    plt.grid(True, which="both", alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Interference spectrum can be negative, so semilog-x is safer than log-log
    plt.figure(figsize=(9, 5.5))
    plt.semilogx(freq[pos], sint[pos], label=f"Interference, E={eint:.2e}")
    plt.axhline(0, color="black", linewidth=0.8)

    plt.xlabel("Frequency [Hz]")
    plt.ylabel(r"$S_{tot} - S_{ref} - S_{obj}$")
    plt.title("Estimated interference spectrum")
    plt.grid(True, which="both", alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.show()
    
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
        "inputa",
        type=_existing_file,
        nargs="?",  
        default=None,
        help="Input file path. Ref",
    )
    
    parser.add_argument(
        "inputb",
        type=_existing_file,
        nargs="?",  
        default=None,
        help="Input file path. Obj",
    )
    
    parser.add_argument(
        "inputc",
        type=_existing_file,
        nargs="?",  
        default=None,
        help="Input file path. Tot",
    )
    
    parser.add_argument("--fs", type=float, default=37037.0)
    parser.set_defaults(func=_cmd)
    return parser

def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return args.func(args)

if __name__ == "__main__":
    main()