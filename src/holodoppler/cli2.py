from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import numpy as np
import os
from .plotting import DebugPlotterManager
from .processing import process
import yaml

import imageio.v3 as iio

def plot_debug_safe(res, pipeline_config):
        debug_manager = DebugPlotterManager(pipeline_config) if pipeline_config.get("debug") else None
        
        out = debug_manager.plot_all(res) if pipeline_config.get("debug") else {}

        return out

def save_debug_images(debug_dict, save_dir, prefix="debug"):
    os.makedirs(save_dir, exist_ok=True)

    for key, img in debug_dict.items():
        if img is None:
            continue

        img_np = to_numpy(img)

        if img_np.dtype != np.uint8:
            img_min = np.min(img_np)
            img_max = np.max(img_np)

            if img_max > img_min:
                img_np = (img_np - img_min) / (img_max - img_min + 1e-12)

            img_np = (img_np * 255).astype(np.uint8)

        filename = os.path.join(save_dir, f"{prefix}_{key}.png")

        iio.imwrite(filename, img_np)

        print(f"Saved: {filename} | shape={img_np.shape} dtype={img_np.dtype}")

def preview(holo_path, yaml_pipeline_path, tictoc=False):

    with open(yaml_pipeline_path, "r") as file:
        pipeline_config = yaml.safe_load(file)

    iterator = process(holo_path, pipeline_config, tictoc=tictoc)

    res = next(iterator) # get the first iteration only as preview

    # --- Generate debug safely ---
    debug_imgs = plot_debug_safe(res, pipeline_config)

    if pipeline_config["debug"]["enabled"] and "zernike_coefficients" in res:
        print("zernike_fit_coeffs (radians):", to_numpy(res["coefs"]) if "coefs" in res else "N/A")
        # print("delta to true z in mm if coef[0] is defocus : ", 4* np.sqrt(3) * parameters["z"]**2 / ((min(frames.shape[1:])* parameters["pixel_pitch"])**2)  * parameters["wavelength"] / (2*np.pi) * (HD.bm.to_numpy(res["coefs"])[0] if "coefs" in res else 0) * 1e3)

    # --- Add M0 ---
    if "M0" in res:
        M0 = to_numpy(res["moments"][0])
        M0 = (M0 - np.min(M0)) / (np.max(M0) - np.min(M0) + 1e-12)
        debug_imgs["M0"] = (M0 * 255).astype(np.uint8)

    print("DEBUG KEYS:", list(debug_imgs.keys()))

    # --- Save ---
    save_dir = "./debug_outputs"
    save_debug_images(debug_imgs, save_dir)
    
    M0img = debug_imgs.get("M0")
    if M0img is not None:
        return M0img


def process(holo_path, yaml_pipeline_path, tictoc=False):

    with open(yaml_pipeline_path, "r") as file:
        pipeline_config = yaml.safe_load(file)

    iterator = process(holo_path, pipeline_config, tictoc=tictoc)

    out_list = []

    goals = pipeline_config.get("goals")
        
    # Debug setup

    do_debug =  pipeline_config.get('debug', {}).get('enabled')
    debug_manager = DebugPlotterManager(pipeline_config) if do_debug else None

    if do_debug:
        import threading
        import queue
        
        debug_results = {}
        res_store = {}
        lock = threading.Lock()
        debug_queue = queue.Queue(maxsize=100)
        stop_event = threading.Event()
        
        def plotting_worker():
            while not stop_event.is_set() or not debug_queue.empty():
                try:
                    i = debug_queue.get(timeout=0.1)
                    with lock:
                        res = res_store.pop(i)
                    out = debug_manager.plot_all(res)
                    with lock:
                        debug_results[i] = out
                    debug_queue.task_done()
                except queue.Empty:
                    continue
        
        debug_thread = threading.Thread(target=plotting_worker, daemon=True)
        debug_thread.start()
    else :
        debug_queue = None
        res_store = None
        lock = None  

    for res in iterator: # get all iterations

        out_list.append({res[k] for k in goals})
        
        if do_debug:
            with lock:
                res_store[i] = res
            debug_queue.put(i)

        

def _existing_file(value: str) -> Path:
    path = Path(value).expanduser().resolve()

    if not path.is_file():
        raise argparse.ArgumentTypeError(f"File does not exist: {path}")

    return path


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON file: {path}\n{exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit(f"Config JSON must contain an object at top level: {path}")

    return data


def _load_json(path: Path) -> dict:
    """Load and parse JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def _get_debug_config() -> dict:
    """Load debug configuration if it exists."""
    debug_paths_file = Path(".debug_paths.json")
    if debug_paths_file.exists():
        with open(debug_paths_file, 'r') as f:
            return json.load(f)
    return {}

def _cmd_preview(args: argparse.Namespace) -> int:
    debug_config = _get_debug_config()
    
    # Determine input path
    if args.input is None:
        holofilepath = debug_config.get("HOLOFILEPATH")
        if not holofilepath:
            print("Error: No input file provided and HOLOFILEPATH not found in .debug_paths.json")
            return 1
        input_path = Path(holofilepath)
        if not input_path.exists():
            print(f"Error: HOLOFILEPATH '{input_path}' does not exist")
            return 1
    else:
        input_path = args.input
    
    # Determine config path
    if args.config is None:
        config_path = Path("parameters/default_parameters_debug.json")
        if not config_path.exists():
            print("Error: No config file provided and parameters/default_parameters_debug.json not found")
            return 1
    else:
        config_path = args.config
    
    config = _load_json(config_path)
    preview(input_path, config)
    return 0

def _cmd_process(args: argparse.Namespace) -> int:
    debug_config = _get_debug_config()
    
    # Determine input path
    if args.input is None:
        holofilepath = debug_config.get("HOLOFILEPATH")
        if not holofilepath:
            print("Error: No input file provided and HOLOFILEPATH not found in .debug_paths.json")
            return 1
        input_path = Path(holofilepath)
        if not input_path.exists():
            print(f"Error: HOLOFILEPATH '{input_path}' does not exist")
            return 1
    else:
        input_path = args.input
    
    # Determine config path
    if args.config is None:
        config_path = Path("parameters/default_parameters_debug.json")
        if not config_path.exists():
            print("Error: No config file provided and parameters/default_parameters_debug.json not found")
            return 1
    else:
        config_path = args.config
    
    config = _load_json(config_path)
    process(input_path, config)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="holodoppler",
        description="HoloDoppler command-line tools.",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )

    preview_parser = subparsers.add_parser(
        "preview",
        help="Preview a HoloDoppler input file using a JSON configuration.",
    )
    preview_parser.add_argument(
        "input",
        type=_existing_file,
        nargs="?",  # Make optional
        default=None,
        help="Input file path. If not provided, uses HOLOFILEPATH from .debug_paths.json",
    )
    preview_parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",  # Make optional
        default=None,
        help="JSON configuration file path. If not provided, uses parameters/default_parameters_debug.json",
    )
    preview_parser.set_defaults(func=_cmd_preview)

    process_parser = subparsers.add_parser(
        "process",
        help="Process a HoloDoppler input file using a JSON configuration.",
    )
    process_parser.add_argument(
        "input",
        type=_existing_file,
        nargs="?",
        default=None,
        help="Input file path. If not provided, uses HOLOFILEPATH from .debug_paths.json",
    )
    process_parser.add_argument(
        "config",
        type=_existing_file,
        nargs="?",
        default=None,
        help="JSON configuration file path. If not provided, uses parameters/default_parameters_debug.json",
    )
    process_parser.set_defaults(func=_cmd_process)

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return args.func(args)