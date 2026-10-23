from __future__ import annotations

import shutil
import csv
import json
import os
import re
import subprocess
import time
import tempfile
from queue import Queue
from threading import Condition, Lock, Thread
from numbers import Integral
from dataclasses import asdict, is_dataclass
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
from typing import Iterable, Any

import h5py
import numpy as np
from numpy._core.numeric import True_
import yaml
from PIL import Image

from holodoppler.get_version import get_version
from holodoppler.core.image_utils import resize_frames
from holodoppler.logging import logger


def ensure_directory(path: Path) -> Path:
    """Create a directory and report useful Windows filesystem diagnostics."""
    path = Path(path)

    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        absolute_path = path.resolve(strict=False)

        logger.debug(
            "Could not create directory %s (absolute=%s, cwd=%s, exists=%s, "
            "is_directory=%s, is_file=%s, parent=%s, parent_exists=%s): %s",
            path, absolute_path, Path.cwd(), absolute_path.exists(),
            absolute_path.is_dir(), absolute_path.is_file(),
            absolute_path.parent, absolute_path.parent.exists(), exc,
        )

        raise

    return path


def json_default(value: Any) -> Any:
    """Convert common scientific Python objects into JSON-compatible values."""
    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        return asdict(value)

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def to_serializable(value: Any) -> Any:
    """Recursively convert Python/NumPy objects into json/yaml savable objects."""
    if isinstance(value, dict):
        return {str(k): to_serializable(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [to_serializable(v) for v in value]

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        return to_serializable(asdict(value))

    return value


def normalize_float_array_to_uint8(data: np.ndarray) -> np.ndarray:
    """
    Normalize arbitrary numerical data to uint8.

    NaN and Inf are handled before normalization.
    """
    data = np.asarray(data)

    if data.dtype == np.uint8:
        return data

    if data.dtype == np.uint16:
        return (data.astype(np.float32) / 65535.0 * 255.0).astype(np.uint8)

    data = np.nan_to_num(
        data,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    ).astype(np.float32, copy=False)

    if data.size == 0:
        return np.zeros_like(data, dtype=np.uint8)

    minimum = float(data.min())
    maximum = float(data.max())

    if maximum <= minimum:
        return np.zeros_like(data, dtype=np.uint8)

    normalized = (data - minimum) / (maximum - minimum)
    return np.clip(normalized * 255.0, 0, 255).astype(np.uint8)


def cast_png_data(data: np.ndarray) -> np.ndarray:
    """
    Convert image data to a PIL-compatible integer array.

    Important:
        If the input is floating point, normalization happens before
        the final uint8 cast.
    """
    data = np.asarray(data)

    if data.dtype == np.uint8:
        return data

    if data.dtype == np.uint16:
        return data

    if np.issubdtype(data.dtype, np.floating):
        return normalize_float_array_to_uint8(data)

    if np.issubdtype(data.dtype, np.integer):
        if data.min() >= 0 and data.max() <= 255:
            return data.astype(np.uint8)

        if data.min() >= 0 and data.max() <= 65535:
            return data.astype(np.uint16)

    return normalize_float_array_to_uint8(data)


def prepare_png_image(data: np.ndarray) -> Image.Image:
    """
    Convert a 2-D grayscale or 3-D RGB/RGBA array into a PIL Image.
    """
    data = cast_png_data(data)

    if data.ndim == 2:
        if data.dtype == np.uint16:
            return Image.fromarray(data, mode="I;16")

        return Image.fromarray(data, mode="L")

    if data.ndim == 3:
        channels = data.shape[-1]

        if channels == 3:
            return Image.fromarray(data, mode="RGB")

        if channels == 4:
            return Image.fromarray(data, mode="RGBA")

    raise ValueError(
        f"Unsupported PNG shape {data.shape}. "
        "Expected (H, W), (H, W, 3), or (H, W, 4)."
    )


def save_png(path: Path, data: np.ndarray) -> None:
    """Save one image using PIL."""
    path = Path(path)
    ensure_directory(path.parent)

    image = prepare_png_image(data)
    image.save(path)

def is_grayscale_video(data: np.ndarray) -> bool:
    """Return True for a video represented as (T, H, W)."""
    return data.ndim == 3


def is_color_video(data: np.ndarray) -> bool:
    """Return True for a video represented as (T, H, W, C)."""
    return data.ndim == 4 and data.shape[-1] in (3, 4)


def is_image(data: np.ndarray) -> bool:
    """Return True for a 2-D grayscale or 3-D RGB/RGBA image."""
    if data.ndim == 2:
        # if data.shape[0] > 4 and data.shape[1] > 4 : # images should be more than 4 by 4 pixels (else they are simply)
        return True

    return data.ndim == 3 and data.shape[-1] in (3, 4)


def is_video(data: np.ndarray) -> bool:
    """
    Determine whether an array represents a video.

    Convention:
        (T, H, W)       -> grayscale video
        (T, H, W, 3)    -> RGB video
        (T, H, W, 4)    -> RGBA video

    A 3-D array whose final dimension is 3 or 4 is interpreted as an image.
    """
    return not is_image(data) and (is_grayscale_video(data) or is_color_video(data))


def validate_video(data: np.ndarray) -> np.ndarray:
    """
    Validate and prepare video data.

    Accepted:
        (T, H, W)
        (T, H, W, 3)
        (T, H, W, 4)
    """
    data = np.asarray(data)

    if not is_video(data):
        raise ValueError(
            f"Invalid video shape {data.shape}. "
            "Expected (T,H,W), (T,H,W,3), or (T,H,W,4)."
        )

    if data.shape[0] == 0:
        raise ValueError("Cannot save a video with zero frames.")

    return data


def video_to_uint8(data: np.ndarray) -> np.ndarray:
    """Convert a complete video to uint8 for FFmpeg."""
    data = validate_video(data)
    return normalize_float_array_to_uint8(data)


def average_video(data: np.ndarray) -> np.ndarray:
    """
    Compute the temporal average of a video.

    For floating-point videos:
        mean is computed while still floating point,
        then the result is converted to uint8.

    This intentionally avoids converting every frame to uint8 before
    calculating the average.
    """
    data = validate_video(data)

    average = np.mean(data, axis=0)

    return cast_png_data(average)


# ============================================================================
# 3. FFmpeg / Ut Video writer
# ============================================================================


def make_even_dimensions(frames: np.ndarray) -> np.ndarray:
    """
    Pad video dimensions to even values.

    This is useful for codecs/pixel formats requiring even dimensions.
    """
    height = frames.shape[1]
    width = frames.shape[2]

    new_height = height + (height % 2)
    new_width = width + (width % 2)

    if new_height == height and new_width == width:
        return frames

    if frames.ndim == 3:
        padded = np.zeros(
            (frames.shape[0], new_height, new_width),
            dtype=frames.dtype,
        )
    else:
        padded = np.zeros(
            (frames.shape[0], new_height, new_width, frames.shape[3]),
            dtype=frames.dtype,
        )

    padded[:, :height, :width, ...] = frames

    return padded


def prepare_ffmpeg_frames(
    data: np.ndarray,
    codec: str = "mjpeg",
) -> tuple[np.ndarray, str, str]:
    """
    Prepare video for FFmpeg.
    """
    frames = video_to_uint8(data)
    frames = make_even_dimensions(frames)

    if frames.ndim == 3:
        return np.ascontiguousarray(frames), "gray", "gray"

    channels = frames.shape[-1]

    if channels == 4:
        frames = frames[..., :3]
        channels = 3

    if channels != 3:
        raise ValueError(
            f"Unsupported number of video channels: {channels}. "
            "Expected 3 or 4."
        )

    if codec.lower() == "mjpeg":
        output_pix_fmt = "yuvj422p"
    elif codec.lower() == "utvideo":
        output_pix_fmt = "gbrp"
    else:
        output_pix_fmt = "yuv444p"

    return np.ascontiguousarray(frames), "rgb24", output_pix_fmt

def find_ffmpeg() -> str:
    """
    Return the FFmpeg executable provided by imageio-ffmpeg.

    imageio-ffmpeg ships a platform-specific FFmpeg binary with the Python
    package.  PyInstaller includes that binary in the Windows installer, so
    resolving it through imageio-ffmpeg works both from source and from the
    installed application without a second download.

    Returns:
        Absolute path to ffmpeg executable.
    """
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise RuntimeError(
            "FFmpeg support is unavailable because imageio-ffmpeg is not "
            "installed. Reinstall HoloDoppler to restore the bundled FFmpeg."
        ) from exc

    try:
        executable = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError(
            "The FFmpeg executable bundled with HoloDoppler could not be "
            "located. Reinstall HoloDoppler to restore it."
        ) from exc

    path = Path(executable).expanduser()
    if path.is_file():
        return str(path.resolve())

    # get_ffmpeg_exe() can legitimately return a command name for an
    # environment override or a system installation.
    resolved = shutil.which(executable)
    if resolved is not None:
        return str(Path(resolved).resolve())

    raise RuntimeError(
        "imageio-ffmpeg selected an FFmpeg executable that does not exist: "
        f"{executable}"
    )


# ============================================================================
# 4. PNG saving
# ============================================================================


def save_video_average_png(path: Path, video: np.ndarray) -> None:
    """
    Save the temporal average of a video as PNG.

    The average is calculated first in the original numerical representation,
    then converted to a PNG-compatible integer representation.
    """
    average = average_video(video)
    save_png(path, average)


def save_image_png(path: Path, image: np.ndarray) -> None:
    """Save an image directly as PNG."""
    if not is_image(image):
        raise ValueError(f"Invalid image shape: {image.shape}")

    save_png(path, image)


def save_pngs(
    target_dir: Path,
    data_map: dict[str, Any],
    png_keys: Iterable[str] | None = None,
) -> None:
    """Save images and temporal-average PNGs."""
    png_dir = ensure_directory(target_dir / "png")
    selected_keys = None if png_keys is None else set(png_keys)

    for name, data in data_map.items():
        if data is None or not isinstance(data, np.ndarray):
            continue

        if selected_keys is not None and name not in selected_keys:
            continue

        try:
            path = png_dir / f"{name}.png"

            if is_image(data):
                save_image_png(path, data)

            elif is_video(data):
                save_video_average_png(path, data)

            else:
                continue

            logger.info(f"Saved PNG: {name}")

        except Exception as exc:
            logger.exception(f"Failed to save PNG {name}: {exc}")


# ============================================================================
# 5. Text / CSV / JSON / YAML
# ============================================================================


def save_txt(path: Path, value: Any) -> None:
    """Save arbitrary text or a string representation."""
    path = Path(path)
    ensure_directory(path.parent)

    if isinstance(value, str):
        text = value
    else:
        text = str(value)

    path.write_text(text, encoding="utf-8")


def save_csv(path: Path, value: Any) -> None:
    """
    Save CSV data.

    Supported inputs:
        - list of dictionaries
        - list/tuple of rows
        - numpy 1-D / 2-D arrays
        - pandas-like objects exposing to_csv()
    """
    path = Path(path)
    ensure_directory(path.parent)

    if hasattr(value, "to_csv"):
        value.to_csv(path, index=False)
        return

    if isinstance(value, np.ndarray):
        value = np.asarray(value)

        if value.ndim == 1:
            value = value[:, None]

        if value.ndim != 2:
            raise ValueError(
                f"CSV numpy data must be 1-D or 2-D, got {value.shape}"
            )

        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerows(value.tolist())

        return

    if isinstance(value, (list, tuple)):
        if not value:
            path.write_text("", encoding="utf-8")
            return

        with path.open("w", newline="", encoding="utf-8") as handle:

            if all(isinstance(row, dict) for row in value):
                fieldnames = []
                for row in value:
                    for key in row:
                        if key not in fieldnames:
                            fieldnames.append(key)

                writer = csv.DictWriter(
                    handle,
                    fieldnames=fieldnames,
                )
                writer.writeheader()
                writer.writerows(value)

            else:
                writer = csv.writer(handle)
                writer.writerows(value)

        return

    raise TypeError(
        f"Unsupported CSV data type: {type(value).__name__}"
    )


def save_json(path: Path, value: Any) -> None:
    """Save a Python object as JSON."""
    path = Path(path)
    ensure_directory(path.parent)

    serializable = to_serializable(value)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(
            serializable,
            handle,
            indent=4,
            ensure_ascii=False,
        )


def save_yaml(path: Path, value: Any) -> None:
    """Save a Python object as YAML."""
    path = Path(path)
    ensure_directory(path.parent)

    serializable = to_serializable(value)

    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            serializable,
            handle,
            sort_keys=False,
            allow_unicode=True,
        )

def save_json_and_yaml(json_path: Path, yaml_path: Path, value: Any) -> None:
    """Save a Python object as YAML and JSON."""
    save_json(json_path, value)
    save_yaml(yaml_path, value)


# ============================================================================
# 6. HDF5
# ============================================================================


def save_h5(
    target_dir: Path,
    data_map: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    save_only_list: Iterable[str] | None = None,
    h5_file_name = None,
    git_commit: str | None = None,
) -> Path:
    """
    Save numerical output data to HDF5.
    """
    target_dir = Path(target_dir)
    h5_dir = ensure_directory(target_dir / "h5")

    if h5_file_name is None:
        target_name = target_dir.name or "output"
    else:
        target_name = h5_file_name
    h5_path = h5_dir / f"{target_name}_output.h5"

    selected = None if save_only_list is None else set(save_only_list)

    logger.info(f"Saving H5: {h5_path}")

    with h5py.File(h5_path, "w") as h5:

        for name, value in data_map.items():

            if selected is not None and name not in selected:
                continue

            if value is None:
                continue

            if not isinstance(value, np.ndarray):
                continue

            # HDF5 should preserve useful numerical precision.
            if np.issubdtype(value.dtype, np.floating):
                value_to_save = np.nan_to_num(
                    value,
                    nan=0.0,
                    posinf=0.0,
                    neginf=0.0,
                ).astype(np.float32)

            else:
                value_to_save = value

            h5.create_dataset(
                name,
                data=value_to_save,
                compression=None,
            )

        if parameters is not None:
            h5.create_dataset(
                "HD_parameters",
                data=json.dumps(
                    to_serializable(parameters),
                    ensure_ascii=False,
                ),
            )

        h5.create_dataset(
            "HD_version",
            data=f"py{get_version()}",
        )

        h5.create_dataset(
            "git_commit",
            data=f"{git_commit or get_git_version()}",
        )

        h5.attrs["git_commit"] = git_commit or get_git_version()
        h5.attrs["version"] = f"py{get_version()}"

    size_gb = h5_path.stat().st_size / (1024**3)

    logger.info("H5 saved: %s (%.2f GB)", h5_path, size_gb)

    return h5_path

# ============================================================================
# 7. Metadata / versioning
# ============================================================================

def get_git_version() -> str:
    """Return the current Git commit, or a fallback string."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        OSError,
    ):
        return "Not Available"


def save_version_files(target_dir: Path) -> None:
    """Save version.txt and git_version.txt."""
    target_dir = Path(target_dir)
    version = f"py{get_version()}"
    git_commit = get_git_version()

    (target_dir / "version.txt").write_text(
        version + "\n",
        encoding="utf-8",
    )
    (target_dir / "git_version.txt").write_text(
        f"Git commit: {git_commit}\n"
        f"Version: {version}\n",
        encoding="utf-8",
    )


def save_metadata(
    target_dir: Path,
    file_reader: Any = None,
    parameters: dict[str, Any] | None = None,
) -> None:
    """Save generic and HoloVibes-specific metadata."""
    target_dir = Path(target_dir)
    json_dir = ensure_directory(target_dir / "json")
    yaml_dir = ensure_directory(target_dir / "yaml")

    if parameters is not None:
        save_json_and_yaml(
            json_dir / "parameters_holodoppler.json",
            yaml_dir / "parameters_holodoppler.yaml",
            parameters,
        )

    if file_reader is not None:
        if getattr(file_reader, "extension", None) == ".holo":
            footer = getattr(file_reader, "footer", None)
            if footer is not None:
                save_json_and_yaml(
                    json_dir / "holovibes_footer.json",
                    yaml_dir / "holovibes_footer.yaml",
                    footer,
                )

            header = getattr(file_reader, "header", None)
            if header is not None:
                if is_dataclass(header):
                    header = asdict(header)
                save_json_and_yaml(
                    json_dir / "holovibes_header.json",
                    yaml_dir / "holovibes_header.yaml",
                    header,
                )
        if getattr(file_reader, "extension", None) == ".cine":
            header = getattr(file_reader, "header", None)
            if header is not None:
                if is_dataclass(header):
                    header = asdict(header)
                save_json_and_yaml(
                    json_dir / "cine_metadata.json",
                    yaml_dir / "cine_metadata.yaml",
                    header,
                )

    save_version_files(target_dir)


# ============================================================================
# Output helpers
# ============================================================================

def is_csv_output(name: str) -> bool:
    """Return True if an output must be saved to both CSV and HDF5."""
    name = name.lower()
    return "coefs" in name or "registration" in name


def save_csv_outputs(
    target_dir: Path,
    output: dict[str, Any]
    ):
    """
    Save coefs/registration outputs to CSV.

    Returns the output names that should also be stored in HDF5.
    """
    csv_dir = ensure_directory(Path(target_dir) / "csv")

    for name, value in output.items():
        if value is None or not is_csv_output(name):
            continue
        try:
            path = csv_dir / f"{name}.csv"
            save_csv(path, value)
            logger.info(f"Saved CSV: {path}")
        except Exception as exc:
            logger.exception(f"Failed to save CSV {name}: {exc}")

def create_directories(
    target_dir: Path,
) -> None:
    """Create the output directory structure."""
    target_dir = Path(target_dir)

    subdirectories = [
        "png",
        "avi",
        "mp4",
        "json",
        "csv",
        "yaml",
        "h5"
    ]

    for directory in subdirectories:
        ensure_directory(target_dir / directory)

from typing import Literal

VideoWriter = Literal["imageio", "cmd", "pyav"]



def save_video(
    path: Path,
    data: np.ndarray,
    fps: float,
    ffmpeg: str | None = None,
    codec: str = "mjpeg",
    writer: VideoWriter = "imageio",
) -> None:
    """
    Save a video using ImageIO, FFmpeg CLI, or PyAV.

    Supported combinations:
        AVI + utvideo: lossless
        AVI + mjpeg: lossy
        MP4 + libx264: H.264

    Output container is inferred from file extension.
    """
    path = Path(path)
    ensure_directory(path.parent)

    suffix = path.suffix.lower()

    if suffix not in {".avi", ".mp4"}:
        raise ValueError(f"Unsupported video extension: {suffix}")

    if suffix == ".mp4":
        codec = "libx264"
    
    if writer == "imageio":
        save_video_imageio(
            path, data, fps,
            codec=codec,
        )

    elif writer == "cmd":
        if ffmpeg is None:
            ffmpeg = find_ffmpeg()

        save_video_cmd(
            path, data, fps, ffmpeg,
            codec=codec,
        )

    elif writer == "pyav":
        save_video_pyav(
            path, data, fps,
            codec=codec,
        )

    else:
        raise ValueError(
            f"Unsupported video writer: {writer!r}. "
            "Expected 'imageio', 'cmd', or 'pyav'."
        )



def save_video_imageio(
    path: Path,
    data: np.ndarray,
    fps: float,
    codec: str,
) -> None:
    """Save video using ImageIO's FFmpeg plugin."""
    import imageio.v2 as imageio

    frames = video_to_uint8(data)
    frames = make_even_dimensions(frames)

    # Use RGB for broad codec and container compatibility.
    if frames.ndim == 3:
        frames = np.repeat(frames[..., None], 3, axis=-1)
    elif frames.shape[-1] == 4:
        frames = frames[..., :3]

    frames = np.ascontiguousarray(frames)

    kwargs = {
        "fps": float(fps),
        "codec": codec,
        "macro_block_size": 2,
    }

    if path.suffix.lower() == ".mp4":
        kwargs.update({
            "pixelformat": "yuv420p",
            "ffmpeg_params": ["-crf", "18", "-preset", "medium"],
        })
    elif codec.lower() == "utvideo":
        kwargs.update({
            "pixelformat": "yuv444p",
        })
    elif codec.lower() == "mjpeg":
        kwargs.update({
            "pixelformat": "yuv420p",
            "quality": 10,
            "ffmpeg_params": ["-color_range", "pc"],
        })

    with imageio.get_writer(str(path), **kwargs) as video:
        for frame in frames:
            video.append_data(frame)



def save_video_pyav(
    path: Path,
    data: np.ndarray,
    fps: float,
    codec: str,
) -> None:
    """
    Save AVI or MP4 using PyAV.

    The entire video is prepared as a contiguous NumPy array,
    then frames are submitted directly to the FFmpeg encoder.
    """
    import av
    from fractions import Fraction

    path = Path(path)
    ensure_directory(path.parent)

    if not np.isfinite(fps) or fps <= 0:
        raise ValueError(f"Invalid FPS: {fps}")

    if path.suffix.lower() not in (".avi", ".mp4"):
        raise ValueError("Only AVI and MP4 are supported")

    if path.suffix.lower() == ".mp4":
        codec = "libx264"

    frames = video_to_uint8(data)
    frames = make_even_dimensions(frames)

    if frames.ndim == 3:
        input_format = "gray"

    elif frames.shape[-1] == 4:
        frames = frames[..., :3]
        input_format = "rgb24"

    else:
        input_format = "rgb24"

    frames = np.ascontiguousarray(frames)

    height, width = frames.shape[1:3]
    rate = Fraction(str(float(fps))).limit_denominator(100000)

    with av.open(str(path), mode="w") as container:
        stream = container.add_stream(codec, rate=rate)
        stream.width = width
        stream.height = height

        if codec == "libx264":
            stream.pix_fmt = "yuv420p"
            stream.options = {
                "crf": "18",
                "preset": "medium",
            }

        elif codec == "mjpeg":
            stream.pix_fmt = "yuvj422p"

            # Do not pass "qscale" as an encoder option.
            stream.options = {}

        elif codec == "utvideo":
            stream.pix_fmt = "gbrp"
            stream.options = {}

        for array in frames:
            frame = av.VideoFrame.from_ndarray(
                array,
                format=input_format,
            )

            for packet in stream.encode(frame):
                container.mux(packet)

        for packet in stream.encode():
            container.mux(packet)



def save_video_cmd(
    path: Path,
    data: np.ndarray,
    fps: float,
    ffmpeg: str,
    codec: str,
) -> None:
    """Save video through the explicit FFmpeg CLI."""
    frames = video_to_uint8(data)
    frames = make_even_dimensions(frames)

    if frames.ndim == 3:
        input_pix_fmt = "gray"
    else:
        if frames.shape[-1] == 4:
            frames = frames[..., :3]
        if frames.shape[-1] != 3:
            raise ValueError(f"Unsupported video shape: {frames.shape}")
        input_pix_fmt = "rgb24"

    frames = np.ascontiguousarray(frames)
    height, width = frames.shape[1:3]

    is_mp4 = path.suffix.lower() == ".mp4"
    if is_mp4:
        codec = "libx264"
        output_pix_fmt = "yuv420p"
    elif codec.lower() == "utvideo":
        output_pix_fmt = "yuv444p" if frames.ndim == 4 else "gray"
    elif codec.lower() == "mjpeg":
        output_pix_fmt = "yuvj422p" if frames.ndim == 4 else "gray"
    else:
        output_pix_fmt = "yuv444p" if frames.ndim == 4 else "gray"

    command = [
        ffmpeg, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", input_pix_fmt,
        "-s", f"{width}x{height}",
        "-r", str(float(fps)),
        "-i", "-",
        "-an",
        "-c:v", codec,
    ]

    if is_mp4:
        command += [
            "-crf", "18",
            "-preset", "medium",
        ]
    elif codec.lower() == "mjpeg":
        command += ["-q:v", "1"]

    command += ["-pix_fmt", output_pix_fmt, str(path)]

    result = subprocess.run(
        command,
        input=frames.tobytes(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed while saving {path}.\n"
            f"Command: {' '.join(command)}\n"
            f"FFmpeg output:\n"
            f"{result.stderr.decode(errors='replace')}"
        )


def save_videos(
    target_dir: Path,
    data_map: dict[str, Any],
    fps: float,
    video_keys: Iterable[str] | None = None,
    video_formats: Iterable[str] = ("avi",),
    writer: VideoWriter = "cmd",
) -> None:
    """Save selected videos as AVI and/or MP4. Saves avi in mjpeg for now and mp4 in libx264"""
    avi_dir = ensure_directory(Path(target_dir) / "avi")
    mp4_dir = ensure_directory(Path(target_dir) / "mp4")

    selected = None if video_keys is None else set(video_keys)
    formats = {fmt.lower().lstrip(".") for fmt in video_formats}

    unsupported = formats - {"avi", "mp4"}
    if unsupported:
        raise ValueError(f"Unsupported video formats: {unsupported}")

    ffmpeg = find_ffmpeg() if writer == "cmd" else None
    if ffmpeg:
        logger.debug(f"Using FFmpeg: {ffmpeg}")

    for name, value in data_map.items():
        if value is None or not isinstance(value, np.ndarray):
            continue
        if not is_video(value):
            continue
        if selected is not None and name not in selected:
            continue

        for fmt in sorted(formats):
            directory = avi_dir if fmt == "avi" else mp4_dir
            path = directory / f"{name}.{fmt}"
            codec = "mjpeg" if fmt == "avi" else "libx264"

            start = time.time()
            save_video(
                path,
                value,
                fps=fps,
                ffmpeg=ffmpeg,
                codec=codec,
                writer=writer,
            )
            logger.info("Saved video: %s (%.1fs)", path, time.time() - start)

def save_videos_parallel(
    target_dir: Path,
    data_map: dict[str, Any],
    fps: float,
    video_keys: Iterable[str] | None = None,
    video_formats: Iterable[str] = ("avi",),
    writer: VideoWriter = "cmd",
    max_workers: int = 8,
) -> None:
    """
    Save selected videos as AVI and/or MP4 in parallel.

    AVI: MJPEG
    MP4: H.264 (libx264)

    Each worker runs one independent video encoding job.
    """

    target_dir = Path(target_dir)

    avi_dir = ensure_directory(target_dir / "avi")
    mp4_dir = ensure_directory(target_dir / "mp4")

    selected = None if video_keys is None else set(video_keys)
    formats = {fmt.lower().lstrip(".") for fmt in video_formats}

    unsupported = formats - {"avi", "mp4"}
    if unsupported:
        raise ValueError(f"Unsupported video formats: {unsupported}")

    if max_workers < 1:
        raise ValueError("max_workers must be >= 1")

    cpu_count = os.cpu_count() or 1
    max_workers = max(min(max_workers, cpu_count // 2),1)

    ffmpeg = find_ffmpeg() if writer == "cmd" else None

    if ffmpeg:
        logger.debug(f"Using FFmpeg: {ffmpeg}")

    def save_one_video(
        name: str,
        value: np.ndarray,
        fmt: str,
    ) -> tuple[Path, float]:

        directory = avi_dir if fmt == "avi" else mp4_dir
        path = directory / f"{name}.{fmt}"

        codec = "mjpeg" if fmt == "avi" else "libx264"

        start = time.perf_counter()

        save_video(
            path,
            value,
            fps=fps,
            ffmpeg=ffmpeg,
            codec=codec,
            writer=writer,
        )

        elapsed = time.perf_counter() - start
        return path, elapsed

    # Build encoding jobs without duplicating NumPy arrays.
    jobs = []

    for name, value in data_map.items():
        if value is None or not isinstance(value, np.ndarray):
            continue

        if not is_video(value):
            continue

        if selected is not None and name not in selected:
            continue

        for fmt in sorted(formats):
            jobs.append((name, value, fmt))

    if not jobs:
        logger.info("No videos to save.")
        return

    logger.info(
        "Saving %s video(s) using %s workers...",
        len(jobs), min(max_workers, len(jobs)),
    )

    start_total = time.perf_counter()
    errors = []

    with ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="VideoEncoder",
    ) as executor:

        futures = {
            executor.submit(save_one_video, name, value, fmt):
                (name, fmt)
            for name, value, fmt in jobs
        }

        for future in as_completed(futures):
            name, fmt = futures[future]

            try:
                path, elapsed = future.result()

                logger.info("Saved video: %s (%.1fs)", path, elapsed)

            except Exception as exc:
                errors.append((name, fmt, exc))
                logger.exception(f"Failed to save {name}.{fmt}: {exc}")

    elapsed_total = time.perf_counter() - start_total

    logger.info(
        "Video saving completed in %.1fs (%s/%s successful)",
        elapsed_total, len(jobs) - len(errors), len(jobs),
    )

    if errors:
        raise RuntimeError(
            f"{len(errors)} video encoding job(s) failed."
        ) from errors[0][2]


# ============================================================================
# Default output path
# ============================================================================

def get_default_output_path(
    file_path: str | Path,
    mode: int = 0,
) -> Path:
    """
    Generate the standard output directory.

    mode 0:
        {base_name}/{base_name}_HD

    mode 1:
        {base_name}_HD_{index}

    mode 2:
        {base_name}/{base_name}_HD_{index}
    """
    path = Path(file_path)
    base_name = path.stem

    if mode not in (0, 1, 2):
        raise ValueError("mode must be 0, 1, or 2")

    if mode == 0:
        return path.parent / base_name / f"{base_name}_HD"

    indices = []
    search_directories = [
        path.parent,
        path.parent / base_name,
    ]

    for directory in search_directories:
        if not directory.exists():
            continue

        for subdir in directory.iterdir():
            if not subdir.is_dir():
                continue

            match = re.search(
                rf"^{re.escape(base_name)}_HD_(\d+)$",
                subdir.name,
            )
            if match:
                indices.append(int(match.group(1)))

    new_index = max(indices) + 1 if indices else 0

    if mode == 1:
        return path.parent / f"{base_name}_HD_{new_index}"

    return path.parent / base_name / f"{base_name}_HD_{new_index}"


# ============================================================================
# FPS
# ============================================================================

def calculate_fps(
    parameters: dict[str, Any] | None,
    default_fps: float = 30.0,
    maximum_fps: float = 65.0,
) -> float:
    """Calculate output FPS with safe fallbacks."""

    return default_fps # TODO change but 144Hz is to fast to display anyway


# ============================================================================
# Bundle saving
# ============================================================================

def _prepare_output_directory(file_reader, parameters, custom_path, custom_relative_path):
    """Resolve and prepare a destination once, before any writers are opened."""
    if custom_path is not None and custom_relative_path is not None:
        raise ValueError("custom_path and custom_relative_path cannot be used together")
    default_path = get_default_output_path(file_reader.file_path)
    if custom_path is None:
        custom_path = parameters.get("custom_path")
    if custom_path is not None:
        target = Path(custom_path).expanduser()
        if not target.is_absolute():
            raise ValueError("custom_path must be an absolute path")
    else:
        if custom_relative_path is None:
            custom_relative_path = parameters.get("custom_relative_path")
        relative = Path(custom_relative_path or "")
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("custom_relative_path must stay within the output directory")
        target = default_path / relative
    option = parameters.get("overwrite_option", "overwrite")
    if option not in {"overwrite", "erase", "archive_old"}:
        raise ValueError(f"Unknown overwrite_option: {option}")
    if target.exists():
        if option == "archive_old":
            archive = ensure_directory(target.parent / "archive")
            destination = archive / target.name
            number = 1
            while destination.exists():
                destination = archive / f"{target.name} (#{number})"
                number += 1
            shutil.move(str(target), str(destination))
        elif option == "erase":
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
    create_directories(target)
    for directory in [target, *(target / name for name in
                      ("avi", "mp4", "h5", "png", "csv", "json", "yaml"))]:
        with tempfile.TemporaryFile(dir=directory) as probe:
            probe.write(b"HoloDoppler")
            probe.flush()
    return target


def _saving_options(num_saving_workers, saving_queue_depth):
    if isinstance(num_saving_workers, bool) or not isinstance(num_saving_workers, Integral):
        raise TypeError("Parameter 'num_saving_workers' must be an integer.")
    if num_saving_workers < 0:
        raise ValueError("Parameter 'num_saving_workers' must be nonnegative.")
    if saving_queue_depth is not None:
        if isinstance(saving_queue_depth, bool) or not isinstance(saving_queue_depth, Integral):
            raise TypeError("Parameter 'saving_queue_depth' must be an integer or null.")
        if saving_queue_depth < 1:
            raise ValueError("Parameter 'saving_queue_depth' must be positive.")
    return num_saving_workers, saving_queue_depth or max(1, 2 * num_saving_workers)


class _SavingScheduler:
    """Bound whole submissions and keep each output on a single FIFO worker.

    Producers submit factories so capacity is acquired before arrays are copied.
    Workers never wait for other workers or close the resources they share.
    """

    def __init__(self, workers, depth):
        self._condition = Condition()
        self._queues = [Queue() for _ in range(workers)]
        self._lanes = {}
        self._pending = 0
        self.peak_pending = 0
        self.depth = depth
        self._error = None
        self._stopping = False
        self._cancelled = False
        self._threads = []
        try:
            for index, queue in enumerate(self._queues):
                thread = Thread(target=self._work, args=(queue,), name=f"Saving-{index}")
                thread.start()
                self._threads.append(thread)
        except BaseException:
            self.close(cancel=True)
            raise

    def _check(self):
        if self._error is not None:
            raise self._error
        if self._stopping:
            raise RuntimeError("Saving scheduler is closed")

    def submit(self, make_jobs):
        with self._condition:
            while self._pending >= self.depth:
                self._check()
                self._condition.wait()
            self._check()
            self._pending += 1
            try:
                jobs = make_jobs()
                groups = {}
                for name, callback, args in jobs:
                    if name not in self._lanes:
                        self._lanes[name] = len(self._lanes) % len(self._queues)
                    groups.setdefault(self._lanes[name], []).append((callback, args))
                if not groups:
                    self._pending -= 1
                    self._condition.notify_all()
                    return
                packet = {"remaining": len(groups)}
                self.peak_pending = max(self.peak_pending, self._pending)
                for lane, tasks in groups.items():
                    self._queues[lane].put((packet, tasks))
            except BaseException:
                self._pending -= 1
                self._condition.notify_all()
                raise

    def _work(self, queue):
        while True:
            item = queue.get()
            if item is None:
                return
            packet, tasks = item
            try:
                for callback, args in tasks:
                    with self._condition:
                        skip = self._cancelled or self._error is not None
                    if skip:
                        break
                    callback(*args)
            except BaseException as exc:
                with self._condition:
                    if self._error is None:
                        self._error = exc
                    self._condition.notify_all()
            finally:
                # Do not retain the previous batch while waiting for the next one.
                del item, tasks
                callback = args = None
                with self._condition:
                    packet["remaining"] -= 1
                    if packet["remaining"] == 0:
                        self._pending -= 1
                        self._condition.notify_all()
                del packet

    def close(self, *, cancel=False):
        with self._condition:
            if not self._stopping:
                self._stopping = True
                self._cancelled = cancel
                for queue in self._queues:
                    queue.put(None)
                self._condition.notify_all()
        for thread in self._threads:
            thread.join()
        if self._error is not None:
            raise self._error


class OutputClass:
    """Append ordered batch results to AVI, MP4 and HDF5 with bounded memory.

    ``add(name, value, t)`` accepts one NumPy result at batch index ``t``.
    Use as a context manager to finalize videos and average PNGs reliably.
    Each name starts at index zero and keeps the same shape and dtype.
    Floating-point video levels are fixed from the first frame; HDF5 retains
    numerical values using the same selection and conversions as save_outputs.
    ``num_saving_workers`` defaults to zero (synchronous); positive values
    overlap saving with processing. ``saving_queue_depth`` counts outstanding
    batches, including active writes, and defaults to twice the worker count.
    Submit from one producer thread. Queued inputs are copied before returning;
    close waits for accepted work and reports background errors.
    Output files are partial if processing or writing fails.

    Example::

        with OutputClass(reader, parameters) as output:
            output.add("moment0", first_image, 0)
            output.add("moment0", second_image, 1)
    """

    def __init__(self, file_reader, parameters=None, custom_path=None,
                 custom_relative_path=None, save_to_h5=True):
        self.parameters = parameters or {}
        self.num_saving_workers, self.saving_queue_depth = _saving_options(
            self.parameters.get("num_saving_workers", 0),
            self.parameters.get("saving_queue_depth"))
        self.target_dir = _prepare_output_directory(
            file_reader, self.parameters, custom_path, custom_relative_path)
        self.fps = calculate_fps(self.parameters)
        self._streams = {}
        self._static_names = set()
        self._h5 = None
        self._h5_lock = Lock()
        self._scheduler = None
        self._accepted = {}
        self._closing = False
        self._closed = False
        try:
            save_metadata(self.target_dir, file_reader, self.parameters)
            if save_to_h5:
                path = self.target_dir / "h5" / f"{self.target_dir.name}_output.h5"
                self._h5 = h5py.File(path, "w")
                self._h5.create_dataset("HD_parameters", data=json.dumps(
                    to_serializable(self.parameters), ensure_ascii=False))
                self._h5.create_dataset("HD_version", data=f"py{get_version()}")
                self._h5.create_dataset("git_commit", data=get_git_version())
            if self.num_saving_workers:
                self._scheduler = _SavingScheduler(
                    self.num_saving_workers, self.saving_queue_depth)
        except BaseException:
            self.close(finalize=False)
            raise

    @staticmethod
    def _h5_selected(name):
        return name in {"moment0ff", "moment0", "moment1", "moment2",
                        "spectrum_line", "sh_psd", "averaged_spectrogram",
                        "spectrograms"} or "band_" in name or is_csv_output(name)

    @staticmethod
    def _h5_value(value):
        if np.issubdtype(value.dtype, np.floating):
            return np.nan_to_num(value, nan=0., posinf=0., neginf=0.).astype(np.float32)
        return value

    def _validate(self, name, value):
        if self._closed or self._closing:
            raise RuntimeError("OutputClass is closed")
        if (not isinstance(name, str) or not name or name in {".", ".."}
                or any(c in name for c in '/\\:')
                or name in {"HD_parameters", "HD_version", "git_commit"}):
            raise ValueError(f"Invalid output name: {name!r}")
        value = np.asarray(value)
        if value.dtype.kind not in "biufc" or value.size == 0:
            raise ValueError("Outputs must be nonempty numerical arrays")
        return value

    def _open_video(self, name, fmt):
        import imageio.v2 as imageio
        kwargs = dict(fps=self.fps, macro_block_size=2, pixelformat="yuv420p")
        if fmt == "avi":
            kwargs.update(codec="mjpeg", quality=10,
                          ffmpeg_params=["-color_range", "pc"])
        else:
            kwargs.update(codec="libx264",
                          ffmpeg_params=["-crf", "18", "-preset", "medium"])
        return imageio.get_writer(str(self.target_dir / fmt / f"{name}.{fmt}"), **kwargs)

    def add(self, name: str, value: np.ndarray, t: int) -> None:
        """Append one output; a standalone call consumes one queue slot."""
        self.add_batch({name: value}, t)

    def add_batch(self, outputs: dict[str, np.ndarray], t: int) -> None:
        """Append a whole batch under one queue slot, copying queued inputs."""
        self._submit(outputs, t, static=False)

    def write_static(self, name: str, value: np.ndarray) -> None:
        """Save an aggregate or diagnostic without adding a batch dimension."""
        self._submit({name: value}, None, static=True)

    def _submit(self, outputs, t, *, static):
        if self._closed or self._closing:
            raise RuntimeError("OutputClass is closed")
        values = {}
        for name, value in outputs.items():
            value = self._validate(name, value)
            previous = self._accepted.get(name)
            if static:
                if previous is not None:
                    raise ValueError(f"Output {name!r} has already been written")
            else:
                if previous is not None and previous["static"]:
                    raise ValueError(f"Output {name!r} was already written as static data")
                expected = previous["count"] if previous else 0
                if isinstance(t, bool) or not isinstance(t, Integral) or t != expected:
                    raise ValueError(f"Output {name!r} expected batch index {expected}, got {t}")
                if previous and (value.shape != previous["shape"] or value.dtype != previous["dtype"]):
                    raise ValueError(f"Output {name!r} changed shape or dtype at batch {t}")
            values[name] = value

        def make_jobs():
            snapshots = {name: value.copy() if self._scheduler else value
                         for name, value in values.items()}
            jobs = []
            for name, value in snapshots.items():
                self._accepted[name] = dict(static=static, count=0 if static else t + 1,
                                            shape=value.shape, dtype=value.dtype)
                callback = self._write_static if static else self._write_add
                args = (name, value) if static else (name, value, t)
                jobs.append((name, callback, args))
            return jobs

        try:
            if self._scheduler:
                self._scheduler.submit(make_jobs)
            else:
                for name, callback, args in make_jobs():
                    callback(*args)
        except BaseException:
            self.close(finalize=False)
            raise

    def _write_add(self, name, value, t):
        state = self._streams.get(name)
        if state is None:
            state = dict(count=0, shape=value.shape, dtype=value.dtype, writers=[], csv=None)
            self._streams[name] = state
        with self._h5_lock:
            if self._h5 is not None and self._h5_selected(name):
                data = self._h5_value(value)
                if t == 0:
                    self._h5.create_dataset(name, shape=(0, *value.shape),
                                            maxshape=(None, *value.shape), dtype=data.dtype)
                dataset = self._h5[name]
                dataset.resize(t + 1, axis=0)
                dataset[t] = data
                self._h5.flush()
        if is_csv_output(name):
            if state["csv"] is None:
                state["csv"] = (self.target_dir / "csv" / f"{name}.csv").open(
                    "w", newline="", encoding="utf-8")
            csv.writer(state["csv"]).writerow(value.reshape(-1).tolist())
            state["csv"].flush()
        elif is_image(value) and not np.iscomplexobj(value):
            clean = np.nan_to_num(value, nan=0., posinf=0., neginf=0.).astype(np.float64)
            if t == 0:
                state["range"] = (float(clean.min()), float(clean.max()))
                state["sum"] = np.zeros_like(clean)
                for fmt in ("avi", "mp4"):
                    state["writers"].append(self._open_video(name, fmt))
            low, high = state["range"]
            if value.dtype == np.uint8:
                frame = value
            elif value.dtype == np.uint16:
                frame = (clean / 65535. * 255.).astype(np.uint8)
            elif high > low:
                frame = (np.clip((clean - low) / (high - low), 0., 1.) * 255.).astype(np.uint8)
            else:
                frame = np.zeros(value.shape, dtype=np.uint8)
            if frame.ndim == 2:
                frame = np.repeat(frame[..., None], 3, axis=-1)
            frame = make_even_dimensions(frame[None, ..., :3])[0]
            for writer in state["writers"]:
                writer.append_data(np.ascontiguousarray(frame))
            state["sum"] += value
        state["count"] += 1

    def _write_static(self, name, value):
        with self._h5_lock:
            if self._h5 is not None and self._h5_selected(name):
                self._h5.create_dataset(name, data=self._h5_value(value))
                self._h5.flush()
        if is_csv_output(name):
            save_csv(self.target_dir / "csv" / f"{name}.csv", value)
        else:
            if is_image(value):
                save_png(self.target_dir / "png" / f"{name}.png", value)
            elif is_video(value):
                save_video_average_png(self.target_dir / "png" / f"{name}.png", value)
                for fmt in ("avi", "mp4"):
                    save_video(self.target_dir / fmt / f"{name}.{fmt}", value,
                               self.fps, writer="imageio")
        self._static_names.add(name)

    def close(self, *, finalize: bool = True) -> None:
        if self._closed:
            return
        report_errors = finalize
        self._closing = True
        errors = []
        worker_error = None
        if self._scheduler:
            try:
                self._scheduler.close(cancel=not finalize)
            except BaseException as exc:
                worker_error = exc
        finalize = finalize and worker_error is None
        self._closed = True
        for name, state in self._streams.items():
            resources = [*state["writers"], state["csv"]]
            for resource in resources:
                if resource is not None:
                    try:
                        resource.close()
                    except Exception as exc:
                        errors.append(exc)
            if finalize and "sum" in state and state["count"]:
                try:
                    save_png(self.target_dir / "png" / f"{name}.png",
                             state["sum"] / state["count"])
                except Exception as exc:
                    errors.append(exc)
        if self._h5 is not None:
            try:
                self._h5.close()
            except Exception as exc:
                errors.append(exc)
        self._streams.clear()
        self._accepted.clear()
        if worker_error is not None and report_errors:
            raise worker_error
        if errors and finalize:
            raise RuntimeError("Failed to finalize output files") from errors[0]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close(finalize=exc_type is None)


def save_outputs(
    file_reader: Any,
    output: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    custom_path: str | Path | None = None,
    custom_relative_path: str | Path | None = None,
    save_to_h5: bool = True,
    *,
    num_saving_workers: int | None = None,
    saving_queue_depth: int | None = None,
) -> Path:
    """Save a complete HoloDoppler output bundle.

    custom_path:
        Absolute path used directly as the output directory.

    custom_relative_path:
        Path relative to the default *_HD output directory.

    num_saving_workers:
        None preserves legacy video scheduling; zero saves sequentially.
        Positive values share a bounded thread pool across output formats.
    """
    start_time = time.time()
    parameters = parameters or {}
    if num_saving_workers is not None:
        num_saving_workers, saving_queue_depth = _saving_options(
            num_saving_workers, saving_queue_depth)

    target_dir = _prepare_output_directory(
        file_reader, parameters, custom_path, custom_relative_path)

    logger.info(f"Saving output bundle to: {target_dir}")

    # FPS.
    fps = calculate_fps(
        parameters=parameters,
    )

    if num_saving_workers is not None:
        _run_saving_jobs(
            _bundle_saving_jobs(target_dir, file_reader, output, parameters, fps, save_to_h5),
            num_saving_workers, saving_queue_depth)
        print(f"Saving completed in {time.time() - start_time:.1f} seconds")
        return target_dir

    # 1. Videos.
    save_videos_parallel(
        target_dir,
        output,
        fps=fps,
        video_formats=("avi","mp4"),
        writer="imageio",
    )

    # 2. PNGs.
    save_pngs(
        target_dir,
        output,
    )

    # 3. CSV outputs, also selected for HDF5.
    save_csv_outputs(target_dir, output)

    # 4. JSON and YAML.

    # 5. Metadata.
    save_metadata(
        target_dir,
        file_reader=file_reader,
        parameters=parameters,
    )

    # 6. HDF5.
    if save_to_h5:
        h5_names = [
                "moment0ff",
                "moment0",
                "moment1",
                "moment2",
                "spectrum_line",
                "sh_psd",
                "averaged_spectrogram",
                "spectrograms"
            ]

        # Include all band_* and automatically selected CSV outputs.
        for name in output:
            if (
                "band_" in name
                or "coefs" in name.lower()
                or "registration" in name.lower()
            ) and name not in h5_names:
                h5_names.append(name)

        save_h5(
            target_dir,
            output,
            parameters=parameters,
            save_only_list=h5_names,
            git_commit=get_git_version(),
        )

    logger.info(f"Saving completed in {time.time() - start_time:.1f} seconds")
    return target_dir


def _bundle_saving_jobs(target_dir, file_reader, output, parameters, fps, save_to_h5):
    """Independent jobs sharing read-only arrays; a single job owns HDF5."""
    for name, value in output.items():
        if not isinstance(value, np.ndarray):
            continue
        if is_video(value):
            for fmt in ("avi", "mp4"):
                yield save_video, (target_dir / fmt / f"{name}.{fmt}", value, fps), {
                    "writer": "imageio"}
        png_path = target_dir / "png" / f"{name}.png"
        if is_image(value):
            yield save_png, (png_path, value), {}
        elif is_video(value):
            yield save_video_average_png, (png_path, value), {}
        # The existing bundle saver skips unsupported CSV shapes (e.g. ECC matrices).
        if is_csv_output(name) and value.ndim in (1, 2):
            yield save_csv, (target_dir / "csv" / f"{name}.csv", value), {}
    yield save_metadata, (target_dir,), {"file_reader": file_reader, "parameters": parameters}
    if save_to_h5:
        yield save_h5, (target_dir, output), {
            "parameters": parameters,
            "save_only_list": [name for name in output if OutputClass._h5_selected(name)],
            "git_commit": get_git_version(),
        }


def _run_saving_jobs(jobs, workers, depth):
    """Run bundle jobs without nested pools or an unbounded future list."""
    if workers == 0:
        for callback, args, kwargs in jobs:
            callback(*args, **kwargs)
        return
    pending = deque()
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="SavingBundle") as executor:
        try:
            for callback, args, kwargs in jobs:
                if len(pending) >= depth:
                    pending.popleft().result()
                pending.append(executor.submit(callback, *args, **kwargs))
            while pending:
                pending.popleft().result()
        finally:
            for future in pending:
                future.cancel()
