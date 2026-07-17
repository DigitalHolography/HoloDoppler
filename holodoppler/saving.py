from pathlib import Path
import h5py
import imageio as iio
import numpy as np
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
import os

from .utils import (
    resize_slicewise,
    normalize_to_uint8,
    unsharp_projection,
    _pad_to_even,
    imadjust,
    stretchlim,
)
from .get_version import get_version


def save_preview_images(save_dict, save_dir, prefix="debug", square=False):
    os.makedirs(save_dir, exist_ok=True)
    for key, img in save_dict.items():
        if img is None:
            continue
        if (img.ndim not in [2, 3]) or (img.ndim == 3 and img.shape[-1] > 3):
            continue
        if square:
            m = max(img.shape)
            img = resize_slicewise(img, m, m, axes=(0, 1))
        if img.dtype != np.uint8:
            img_min, img_max = np.min(img), np.max(img)
            if img_max >= img_min:
                img_np = (img - img_min) / (img_max - img_min + 1e-12)
            img_np = (img_np * 255).astype(np.uint8)
        filename = os.path.join(save_dir, f"{prefix}_{key}.png")
        print("Saving : ", filename)
        iio.imwrite(filename, img_np)


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
    backend=None,
):
    """
    Main entry point for saving.
    Priority: holodoppler_path > video_path > default
    """
    start_time = time.time()

    # Path resolution
    default_path = _get_default_output_path(file_reader.file_path)

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

    print(f"Output directory: {target_dir}")
    print(f"Save mode: {save_mode}")

    # Execute save
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
        backend=backend,
    )

    elapsed = time.time() - start_time
    print(f"\nSaving completed in {elapsed:.1f} seconds")


def _get_default_output_path(file_path):
    """Generates the standard Holodoppler directory structure"""
    path = Path(file_path)
    base_name = path.stem
    return path.parent / base_name / f"{base_name}_HD"


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
    backend=None,
):
    """
    Unified saving engine.
    mode="FULL" -> Saves everything including H5.
    mode="LITE" -> Saves videos, pngs, json, txt.
    """
    start_time = time.time()

    # Create subdirectories
    _create_directories(target_dir, mode)

    # Calculate FPS with safety check
    fps = _calculate_fps(num_batch, end_frame, first_frame, parameters)

    # Prepare data for saving
    save_map = _build_save_map(vid, parameters, vid_debug, num_batch)

    # Process and save projections (unsharp masking)
    _save_projections(target_dir, save_map, parameters, backend)

    # Convert all data to uint8 once (memory efficient)
    # uint8_map = {name: normalize_to_uint8(data) for name, data in save_map.items()}
    contrast_cfg = parameters.get("contrast_adjustment", {})
    uint8_map = {}
    for name, data in save_map.items():
        if contrast_cfg.get("enabled", False) and not name.startswith("debug_"):
            # Data already in [0,1] thanks to imadjust
            uint8_map[name] = (np.clip(data, 0, 1) * 255).astype(np.uint8)
        else:
            uint8_map[name] = normalize_to_uint8(data)

    # Save videos (sequential to avoid encoding conflicts)
    _save_videos(target_dir, uint8_map, fps)

    # Save PNGs (parallel)
    _save_pngs(target_dir, uint8_map)

    # Save metadata (fast)
    _save_metadata(target_dir, file_reader, parameters)

    # Save H5 if FULL mode
    if mode == "FULL":
        _save_h5(target_dir, vid, parameters, reg_list, coefs_list)

    elapsed = time.time() - start_time
    print(f"_save_bundle completed in {elapsed:.1f} seconds")


def _create_directories(target_dir, mode):
    """Create required subdirectories"""
    subdirs = ["png", "mp4", "avi", "json"]
    if mode == "FULL":
        subdirs.append("h5")
    for sub in subdirs:
        (target_dir / sub).mkdir(parents=True, exist_ok=True)


def _calculate_fps(num_batch, end_frame, first_frame, parameters):
    """Calculate FPS with bounds checking"""
    if end_frame is None or first_frame is None:
        fps = 30  # Default fallback
        print(f"Using default FPS: {fps}")
    else:
        frame_range = end_frame - first_frame
        if frame_range <= 0:
            fps = 30
            print(f"Invalid frame range, using default FPS: {fps}")
        else:
            sampling_freq = parameters.get("sampling_freq", 1000)  # Default 1kHz
            fps = min((num_batch / frame_range * sampling_freq), 65)

    return fps


def _build_save_map(vid, parameters, vid_debug, num_batch):
    """Build dictionary of all data to save"""
    save_map = {
        "moment_0": vid[:, 0, :, :],
        "moment_1": vid[:, 1, :, :],
        "moment_2": vid[:, 2, :, :],
        "moment_0_ff": vid[:, 3, :, :],
    }

    # Frequency bands
    for k, v in enumerate(parameters.get("frequency_bands", [])):
        band_name = f"band_avg_{v[0]}_{v[1]}"
        save_map[band_name] = vid[:, 4 + k, :, :]

    # Debug videos
    if vid_debug:
        for key, data in vid_debug.items():
            if data.ndim == 3 and data.shape[-1] == num_batch:
                data = np.moveaxis(data, -1, 0)  # ensure (T, H, W)

            # Handle special cases
            if parameters.get("square") and key in [
                "M0ffnoreg",
                "M0notfixed",
                "montage",
                "montagenormalized",
                "psd_map_avg",
                "SVD_M0_inversed_svd_filter",
            ]:
                m = max(data.shape[-2], data.shape[-1])
                data = resize_slicewise(data, m, m)

            if key == "psd_map_avg":  # Special normalization
                for i in range(data.shape[0]):
                    data[i] = normalize_to_uint8(data[i])

            if data.ndim == 3 or data.ndim == 4:
                save_map[f"debug_{key}"] = data

    contrast_cfg = parameters.get("contrast_adjustment", {})
    if contrast_cfg.get("enabled", False):
        low_pct = contrast_cfg.get("low_percent", 1)
        high_pct = contrast_cfg.get("high_percent", 99)
        gamma = contrast_cfg.get("gamma", 1.0)
        for name, data in save_map.items():
            # For 4D debug data we might need per-channel – but we'll keep it simple:
            # compute limits globally across all dimensions.
            if name.startswith("debug_"):
                continue
            low, high = stretchlim(data, low_pct, high_pct)
            save_map[name] = imadjust(data, low, high, gamma)

    return save_map


def _save_projections(target_dir, save_map, parameters, backend):
    """Save unsharp masked projections as PNGs"""
    # Initialize backend if needed
    if backend is None:
        from .backend import BackendManager

        bm = BackendManager(backend=parameters.get("backend", "cpu"))
    else:
        bm = backend

    # Define which keys get projection
    projection_keys = {
        "moment_0",
        "moment_1",
        "moment_2",
        "moment_0_ff",
        "montage",
        "montagenormalized",
    }

    # Also include frequency bands
    projection_keys.update([k for k in save_map.keys() if "frequency_bands" in k])

    for name, data in save_map.items():
        if name in projection_keys:
            try:
                # Create projection
                im = unsharp_projection(bm, data, (1024, 1024), radius=2.0, amount=2.0)
                im = normalize_to_uint8(im)

                # Save
                png_path = target_dir / "png" / f"{name}_unsharped.png"
                iio.imwrite(png_path, im)
            except Exception as e:
                print(f"Failed to save projection for {name}: {e}")


def _save_videos(target_dir, np_map, fps):
    """Save all videos as MP4 and AVI"""
    start_time = time.time()
    completed = 0
    for name, np_data in np_map.items():
        if np_data.ndim != 3 and np_data.ndim != 4:
            continue

        # Determine bit depth and convert appropriately
        uint8_data = _normalize_to_uint8(np_data)

        # MP4
        mp4_path = target_dir / "mp4" / f"{name}.mp4"
        _write_video_fast(
            mp4_path,
            uint8_data,
            fps,
            codec="libx264",
            preset="ultrafast",
            crf=28,
        )

        # AVI
        avi_path = target_dir / "avi" / f"{name}.avi"
        _write_video_fast(
            avi_path,
            uint8_data,
            fps,
            codec="mjpeg",
            quality=8,
        )

        completed += 1

    elapsed = time.time() - start_time
    print(f"Videos saved in {elapsed:.1f} seconds ({completed} videos)")


def normalize(data):
    mi = data.min()
    ma = data.max()

    return (data - mi) / (ma - mi + 1e-24)


def _save_pngs(target_dir, np_map):
    """Save mean frames as PNGs in parallel"""
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=8) as executor:
        tasks = []
        for name, data in np_map.items():
            if data.ndim != 3 and data.ndim != 4:
                continue
            png_path = target_dir / "png" / f"{name}.png"
            mean_frame = np.mean(data, axis=0)

            # Preserve original dtype for PNG saving
            if data.dtype == np.uint16:
                mean_frame = mean_frame.astype(np.uint16)
            elif data.dtype == np.float32 or data.dtype == np.float64:
                # For float data, normalize to 16-bit to preserve precision
                mean_frame = np.clip(normalize(mean_frame), 0, 1)
                mean_frame = (mean_frame * 65535).astype(np.uint16)
            else:
                mean_frame = mean_frame.astype(np.uint8)

            tasks.append(executor.submit(iio.imwrite, png_path, mean_frame))

        # Wait for all tasks to complete
        completed = 0
        for future in as_completed(tasks):
            try:
                future.result()
                completed += 1
            except Exception as e:
                print(f"PNG save failed: {e}")

    elapsed = time.time() - start_time
    print(f"PNGs saved in {elapsed:.1f} seconds ({completed} images)")


def _save_metadata(target_dir, file_reader, parameters):
    """Saves all configuration and versioning files"""
    start_time = time.time()

    # JSON params
    json_path = target_dir / "json" / "parameters_holodoppler.json"
    with open(json_path, "w") as f:
        json.dump(parameters, f, indent=4)

    # Version
    (target_dir / "version_holodoppler.txt").write_text(f"py{get_version()}")

    # Git commit (with error handling)
    try:
        import subprocess

        commit = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        info_text = f"Git commit: {commit}\npy{get_version()}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        info_text = "Git commit: Not Available (not a git repo)"
    (target_dir / "git_version.txt").write_text(info_text)

    # Holo-specific metadata
    if hasattr(file_reader, "ext") and file_reader.ext == ".holo":
        with open(target_dir / "json" / "holovibes_footer.json", "w") as f:
            json.dump(file_reader.file_footer, f, indent=4)
        with open(target_dir / "json" / "holovibes_header.json", "w") as f:
            json.dump(asdict(file_reader.file_header), f, indent=4)

    elapsed = time.time() - start_time
    print(f"Metadata saved in {elapsed:.2f} seconds")


def _save_h5_2(target_dir, save_map, parameters, save_only_list=None):
    """
    Saves raw data to HDF5.
    """
    start_time = time.time()

    target_dir_name = target_dir.name if target_dir.name else "output"
    h5_path = target_dir / "h5" / f"{target_dir_name}_output.h5"

    print(f"Saving H5 to: {h5_path}")

    # No compression for faster writing and lower memory usage
    compression = None

    with h5py.File(h5_path, "w") as f:

        for k, v in save_map.items():

            if save_only_list is not None and k not in save_only_list:
                continue

            v = np.clip(v, -3.4e38, 3.4e38)
            data = v.astype(np.float32)

            f.create_dataset(
                k,
                data=data,
                compression=compression,
            )

        # Save metadata
        f.create_dataset("HD_parameters", data=json.dumps(parameters))
        f.create_dataset("HD_version", data=f"py{get_version()}")

    elapsed = time.time() - start_time
    file_size = h5_path.stat().st_size / (1024**3)
    print(f"H5 saved in {elapsed:.1f} seconds (file size: {file_size:.2f} GB)")


def _save_h5(target_dir, vid, parameters, reg_list, coefs_list):
    """
    Saves raw data to HDF5.

    MEMORY WARNING:
    HDF5 writing can use large amounts of RAM because:
    1. The entire 'vid' array is kept in memory (size = nt * nchannels * h * w * dtype)
    2. HDF5 may buffer data during compression
    3. Each dataset copy uses additional memory
    4. If using compression, more memory is used for the compression buffer

    For a 1000-frame, 4-channel, 512x512 video at float32:
    - vid memory: 1000 * 4 * 512 * 512 * 4 = ~4GB
    - Additional buffers: 500MB - 2GB
    - Total: ~5-6GB RAM required

    To reduce memory:
    - Disable compression (set to None)
    - Use chunking
    - Process in batches
    """
    start_time = time.time()

    target_dir_name = target_dir.name if target_dir.name else "output"
    h5_path = target_dir / "h5" / f"{target_dir_name}_output.h5"

    print(f"Saving H5 to: {h5_path}")
    print(f"   Data shape: {vid.shape}")
    print(f"   Data size: {vid.nbytes / (1024**3):.2f} GB")

    # No compression for faster writing and lower memory usage
    compression = None

    with h5py.File(h5_path, "w") as f:
        # Save moments
        f.create_dataset("moment0", data=vid[:, 0, :, :], compression=compression)
        f.create_dataset("moment1", data=vid[:, 1, :, :], compression=compression)
        f.create_dataset("moment2", data=vid[:, 2, :, :], compression=compression)
        f.create_dataset("moment0ff", data=vid[:, 3, :, :], compression=compression)

        # Save frequency bands
        for k, v in enumerate(parameters.get("frequency_bands", [])):
            f.create_dataset(
                f"band_{v[0]}_{v[1]}",
                data=vid[:, 4 + k, :, :],
                compression=compression,
            )

        # Save metadata
        f.create_dataset("HD_parameters", data=json.dumps(parameters))
        f.create_dataset("HD_version", data=f"py{get_version()}")

        # Save registration data
        if parameters.get("image_registration") and reg_list:
            reg_data = np.array(reg_list, dtype=np.float32)
            f.create_dataset("registration", data=reg_data, compression=compression)
            print(f"   Registration data: {reg_data.shape}")

        # Save Zernike coefficients
        if parameters.get("shack_hartmann") and coefs_list:
            coefs_data = np.stack(coefs_list).astype(np.float32)
            f.create_dataset(
                "zernike_coefs_radians",
                data=coefs_data,
                compression=compression,
            )
            print(f"   Zernike coefficients: {coefs_data.shape}")

    elapsed = time.time() - start_time
    file_size = h5_path.stat().st_size / (1024**3)
    print(f"H5 saved in {elapsed:.1f} seconds (file size: {file_size:.2f} GB)")


def _write_video_fast(
    path,
    frames,
    fps,
    codec="libx264",
    preset=None,
    crf=None,
    quality=None,
    overwrite=True,
    pad_even=True,
    bit_depth=8,
):
    """
    Write video with ffmpeg backend.
    Supports 8-bit, 10-bit, 12-bit, and 16-bit encoding.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if overwrite and path.exists():
        path.unlink()

    frames = np.asarray(frames)

    # Validate and normalize frames based on bit depth
    if bit_depth == 8:
        max_val = 255
        target_dtype = np.uint8
    elif bit_depth == 10:
        max_val = 1023
        target_dtype = np.uint16
    elif bit_depth == 12:
        max_val = 4095
        target_dtype = np.uint16
    elif bit_depth == 16:
        max_val = 65535
        target_dtype = np.uint16
    elif bit_depth == 32:
        max_val = 1.0
        target_dtype = np.float32
    else:
        raise ValueError(f"Unsupported bit depth: {bit_depth}")

    # Normalize frames to target range
    if frames.dtype != target_dtype or (bit_depth <= 16 and frames.max() > max_val):
        if frames.dtype == np.float32 or frames.dtype == np.float64:
            if frames.max() <= 1.0:
                # Normalize from [0, 1] to [0, max_val]
                frames = (frames * max_val).astype(target_dtype)
            else:
                # Already in range, just clip and convert
                frames = np.clip(frames, 0, max_val).astype(target_dtype)
        elif frames.dtype == np.uint8 and bit_depth > 8:
            # Scale up
            frames = frames.astype(np.float32) * (max_val / 255.0)
            frames = frames.astype(target_dtype)
        elif frames.dtype == np.uint16 and bit_depth == 8:
            # Scale down
            frames = (frames.astype(np.float32) * (255.0 / 65535.0)).astype(np.uint8)
        else:
            frames = np.clip(frames, 0, max_val).astype(target_dtype)

    # Handle NaN and Inf values
    frames = np.nan_to_num(frames, nan=0, posinf=max_val, neginf=0)

    # Validate shape
    if frames.ndim == 3:
        # Grayscale: (T, H, W) - fine
        pass
    elif frames.ndim == 4:
        # Color: (T, H, W, C)
        if frames.shape[-1] == 4:
            frames = frames[..., :3]  # RGBA -> RGB
        elif frames.shape[-1] != 3:
            raise ValueError(f"Invalid color channels: {frames.shape[-1]}, expected 3")
    else:
        raise ValueError(f"Invalid video shape: {frames.shape}, expected 3D or 4D")

    if frames.shape[0] == 0:
        raise ValueError(f"Zero-frame video: {path}")

    # Pad to even dimensions for codec compatibility
    if pad_even and codec in ("libx264", "libx265", "h264", "hevc"):
        frames = _pad_to_even(frames)

    # Build writer parameters
    output_params = ["-y"] if overwrite else []
    if preset is not None:
        output_params += ["-preset", str(preset)]
    if crf is not None:
        output_params += ["-crf", str(crf)]

    # Add pixel format for higher bit depths
    if bit_depth > 8:
        if bit_depth == 10:
            output_params += ["-pix_fmt", "yuv420p10le"]
        elif bit_depth == 12:
            output_params += ["-pix_fmt", "yuv420p12le"]
        elif bit_depth == 16:
            output_params += ["-pix_fmt", "yuv420p16le"]
        elif bit_depth == 32:
            output_params += ["-pix_fmt", "gbrpf32le"]  # For float32

    kwargs = {
        "fps": float(fps),
        "codec": codec,
        "macro_block_size": 1,
    }
    if output_params:
        kwargs["output_params"] = output_params
    if quality is not None:
        kwargs["quality"] = quality

    # Write video
    with iio.get_writer(str(path), **kwargs) as writer:
        for frame in frames:
            writer.append_data(frame)


def _normalize_to_uint8(data):
    """Helper function to normalize various data types to uint8"""
    data = np.asarray(data)

    if data.dtype == np.uint8:
        return data
    elif data.dtype == np.uint16:
        return (data.astype(np.float32) / 65535.0 * 255).astype(np.uint8)
    else:
        # For any other type, try to normalize
        data = np.nan_to_num(data, nan=0)
        min_val, max_val = data.min(), data.max()
        if max_val > min_val:
            return ((data - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        else:
            return np.zeros_like(data, dtype=np.uint8)
