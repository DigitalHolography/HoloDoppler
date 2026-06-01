from pathlib import Path
import os
import h5py
from tqdm import tqdm
import imageio as iio
import numpy as np
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils import *
from .get_version import get_version


def save_outputs(
    file_reader,
    video_path=None,
    holodoppler_path=None,
    vid=None,
    vid_debug=None,
    parameters=None,
    reg_list=None,
    coefs_list=None,
    end_frame=None,
    first_frame=None,
    num_batch=None,
):
    """
    Main entry point for saving.
    Determines priority: holodoppler_path > video_path > default
    """

    # 1. Path and Mode Resolution
    # Default path generation
    default_path = _get_default_output_path(file_reader)

    if holodoppler_path:
        if isinstance(holodoppler_path, bool):
            holodoppler_path = default_path
        target_dir = Path(holodoppler_path)
        save_mode = "FULL"
    elif video_path:
        if isinstance(video_path, bool):
            video_path = default_path
        target_dir = Path(video_path)
        save_mode = "LITE"
    else:
        target_dir = default_path
        save_mode = "FULL"

    # 2. Execute Save Bundle
    _save_bundle(
        file_reader,
        target_dir=target_dir,
        mode=save_mode,
        vid=vid,
        vid_debug=vid_debug,
        parameters=parameters,
        reg_list=reg_list,
        coefs_list=coefs_list,
        end_frame=end_frame,
        first_frame=first_frame,
        num_batch=num_batch,
    )


def _get_default_output_path(file_reader):
    """Generates the standard Holodoppler directory structure"""
    base_name = Path(file_reader.file_path).stem
    return Path(file_reader.file_path).parent / base_name / f"{base_name}_HD"


def _save_bundle(
    file_reader,
    target_dir,
    mode,
    vid,
    vid_debug,
    parameters,
    reg_list,
    coefs_list,
    end_frame,
    first_frame,
    num_batch,
):
    """
    Unified saving engine.
    mode="FULL" -> Saves everything including H5.
    mode="LITE" -> Saves videos, pngs, json, txt.
    Optimized: parallel file writing, faster video encoding.
    """
    # Create subdirectories once
    subdirs = ["png", "mp4", "avi", "json"]
    if mode == "FULL":
        subdirs.append("h5")
    for sub in subdirs:
        (target_dir / sub).mkdir(parents=True, exist_ok=True)
        
    print("Saving in : ", target_dir)

    # FPS calculation (unchanged logic)
    fps = min((num_batch / (end_frame - first_frame) * parameters["sampling_freq"]), 65)

    # --- 1. Build data map ---
    save_map = {
        "moment_0": vid[:, 0, :, :],
        "moment_1": vid[:, 1, :, :],
        "moment_2": vid[:, 2, :, :],
        "moment_0_ff": vid[:, 3, :, :],
    }

    # Frequency bands
    for k, v in enumerate(parameters.get("frequency_bands", [])):
        save_map[f"band_{v[0]}_{v[1]}"] = vid[:, 4 + k, :, :]

    # Debug videos
    if vid_debug:
        for key, data in vid_debug.items():
            if data.ndim == 3 and data.shape[-1] == num_batch:
                data = np.moveaxis(data, -1, 0)  # ensure (T, H, W)

            if parameters.get("square") and key in [
                "M0ffnoreg",
                "M0notfixed",
                "montage",
                "montagenormalized",
            ]:
                m = max(data.shape[-2], data.shape[-1])
                data = resize_slicewise(data, m, m)

            save_map[f"debug_{key}"] = data

    # --- 2. Parallel saving of videos and PNGs ---
    # Pre-convert everything to uint8 once (avoids repeated normalization)
    uint8_map = {name: normalize_to_uint8(data) for name, data in save_map.items()}

    # Collect all file‑write tasks
    with ThreadPoolExecutor(max_workers=8) as executor:
        tasks = []

        # Videos: write sequentially, avoids ffmpeg/imageio concurrency issues
        for name, uint8_data in tqdm(uint8_map.items(), desc="Saving videos"):
            mp4_path = target_dir / "mp4" / f"{name}.mp4"
            write_video_fast(
                mp4_path,
                uint8_data,
                fps,
                codec="libx264",
                preset="ultrafast",
                crf=28,
            )

            avi_path = target_dir / "avi" / f"{name}.avi"
            write_video_fast(
                avi_path,
                uint8_data,
                fps,
                codec="mjpeg",
                quality=8,
            )

        # PNGs: parallel is fine
        with ThreadPoolExecutor(max_workers=8) as executor:
            tasks = []

            for name, uint8_data in uint8_map.items():
                png_path = target_dir / "png" / f"{name}.png"
                mean_frame = np.mean(uint8_data, axis=0).astype(np.uint8)
                tasks.append(executor.submit(iio.imwrite, png_path, mean_frame))

            for fut in tqdm(as_completed(tasks), total=len(tasks), desc="Saving PNGs"):
                fut.result()

        # for fut in tqdm(as_completed(tasks), total=len(tasks), desc="Saving visuals"):
        #     fut.result()

    # --- 3. Save metadata (fast text/json writes) ---
    save_metadata(target_dir, file_reader, parameters)

    # --- 4. Save H5 only if FULL mode ---
    if mode == "FULL":
        save_h5(target_dir, vid, parameters, reg_list, coefs_list)

def _pad_to_even(frames):
    """
    Pads H/W to even size for libx264/yuv420p.
    Supports:
      (T, H, W)
      (T, H, W, C)
    """
    h = frames.shape[1]
    w = frames.shape[2]

    pad_h = h % 2
    pad_w = w % 2

    if pad_h == 0 and pad_w == 0:
        return frames

    if frames.ndim == 3:
        pad_width = (
            (0, 0),      # T
            (0, pad_h),  # H
            (0, pad_w),  # W
        )
    else:
        pad_width = (
            (0, 0),      # T
            (0, pad_h),  # H
            (0, pad_w),  # W
            (0, 0),      # C
        )

    return np.pad(frames, pad_width, mode="edge")

def write_video_fast(
    path,
    frames,
    fps,
    codec="libx264",
    preset=None,
    crf=None,
    quality=None,
    overwrite=True,
    pad_even=True,
):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if overwrite and path.exists():
        path.unlink()

    frames = np.asarray(frames)

    if frames.dtype != np.uint8:
        frames = np.nan_to_num(frames)
        frames = np.clip(frames, 0, 255).astype(np.uint8)

    if frames.ndim == 3:
        # grayscale video: (T, H, W)
        pass

    elif frames.ndim == 4:
        # color video: (T, H, W, C)
        if frames.shape[-1] == 4:
            frames = frames[..., :3]  # RGBA -> RGB
        elif frames.shape[-1] != 3:
            raise ValueError(f"Invalid color channel count: {frames.shape}")
    else:
        raise ValueError(f"Invalid video shape: {frames.shape}")

    if frames.shape[0] == 0:
        raise ValueError(f"Zero-frame video: {path}")
    
    if pad_even and codec in ("libx264", "libx265", "h264", "hevc"):
        frames = _pad_to_even(frames)

    output_params = ["-y"] if overwrite else []

    if preset is not None:
        output_params += ["-preset", str(preset)]
    if crf is not None:
        output_params += ["-crf", str(crf)]

    kwargs = {
        "fps": float(fps),
        "codec": codec,
        "macro_block_size": 1,
    }

    if output_params:
        kwargs["output_params"] = output_params

    if quality is not None:
        kwargs["quality"] = quality

    with iio.get_writer(str(path), **kwargs) as writer:
        for frame in frames:
            writer.append_data(frame)
       


def save_metadata(target_dir, file_reader, parameters):
    """Saves all configuration and versioning files"""
    # JSON params
    with open(target_dir / "json" / "parameters_holodoppler.json", "w") as f:
        json.dump(parameters, f, indent=4)

    # Version
    (target_dir / "version_holodoppler.txt").write_text(f"py{get_version()}")

    # Git commit
    try:
        import subprocess
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        info_text = f"Git commit: {commit}\npy{get_version()}"
    except Exception:
        info_text = "Git commit: Not Available"
    (target_dir / "git_version.txt").write_text(info_text)

    # Holo-specific metadata
    if file_reader.ext == ".holo":
        with open(target_dir / "json" / "holovibes_footer.json", "w") as f:
            json.dump(file_reader.file_footer, f, indent=4)
        with open(target_dir / "json" / "holovibes_header.json", "w") as f:
            json.dump(file_reader.file_header, f, indent=4)


def save_h5(target_dir, vid, parameters, reg_list, coefs_list):
    """
    Saves raw data to HDF5. Fixed: uses `vid` (not `vid_t`).
    Added optional compression for speed/space tradeoff.
    """
    target_dir_name = target_dir.name if target_dir.name else "output"

    # Don't use compression because 
    compression = None # "lzf"  # can be set to None for fastest writing

    pbar = tqdm(total=2, desc="Saving h5:")

    with h5py.File(target_dir / "h5" / f"{target_dir_name}_output.h5", "w") as f:
        f.create_dataset("moment0", data=vid[:, 0, :, :], compression=compression)
        f.create_dataset("moment1", data=vid[:, 1, :, :], compression=compression)
        f.create_dataset("moment2", data=vid[:, 2, :, :], compression=compression)
        f.create_dataset("moment0ff", data=vid[:, 3, :, :], compression=compression)
        pbar.update(1)
        for k, v in enumerate(parameters.get("frequency_bands", [])):
            f.create_dataset(
                f"band_{v[0]}_{v[1]}",
                data=vid[:, 4 + k, :, :],
                compression=compression,
            )
        f.create_dataset("HD_parameters", data=json.dumps(parameters))
        f.create_dataset("HD_version", data=f"py{get_version()}")

        if parameters.get("image_registration") and reg_list:
            f.create_dataset("registration", data=np.array(reg_list, dtype=np.float32),
                             compression=compression)

        if parameters.get("shack_hartmann") and coefs_list:
            f.create_dataset(
                "zernike_coefs_radians",
                data=np.stack(coefs_list).astype(np.float32),
                compression=compression,
            )
        pbar.update(1)