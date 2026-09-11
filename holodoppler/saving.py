from __future__ import annotations

import sys
import shutil
import csv
import json
import os
import re
import subprocess
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import yaml
from PIL import Image
import ffmpeg_downloader as ffdl

from holodoppler.get_version import get_version
from holodoppler.utils import resize_frames


def ensure_directory(path: Path) -> Path:
    """Create a directory if necessary and return it."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
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
    return is_grayscale_video(data) or is_color_video(data)


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

    return np.ascontiguousarray(frames), "rgb24", "gbrp"

def find_ffmpeg() -> str:
    """
    Find FFmpeg, downloading it with ffmpeg-downloader if necessary.

    Search order:
        1. FFmpeg already available on PATH.
        2. FFmpeg already installed by ffmpeg-downloader.
        3. Download FFmpeg using ffmpeg-downloader.

    Returns:
        Absolute path to ffmpeg executable.
    """
    # ---------------------------------------------------------
    # 1. Check normal PATH first
    # ---------------------------------------------------------
    executable = shutil.which("ffmpeg")

    if executable is not None:
        path = Path(executable).resolve()

        if path.is_file():
            return str(path)

    # ---------------------------------------------------------
    # 2. Check ffmpeg-downloader installation
    # ---------------------------------------------------------
    try:
        import ffmpeg_downloader as ffdl
    except ImportError as exc:
        raise RuntimeError(
            "FFmpeg was not found and ffmpeg-downloader is not installed.\n"
            "Install it with:\n"
            "    pip install ffmpeg-downloader"
        ) from exc

    ffmpeg_path = getattr(ffdl, "ffmpeg_path", None)

    if ffmpeg_path:
        path = Path(ffmpeg_path)

        if path.is_file():
            return str(path.resolve())

    # ---------------------------------------------------------
    # 3. Download FFmpeg
    # ---------------------------------------------------------
    print("FFmpeg not found. Downloading FFmpeg...")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ffmpeg_downloader",
            "install",
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "ffmpeg-downloader failed to install FFmpeg "
            f"(exit code {result.returncode})."
        )

    # ---------------------------------------------------------
    # 4. Read the path provided by ffmpeg-downloader
    # ---------------------------------------------------------
    import importlib

    ffdl = importlib.reload(ffdl)

    ffmpeg_path = getattr(ffdl, "ffmpeg_path", None)

    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg was installed, but ffmpeg-downloader did not "
            "provide an ffmpeg_path."
        )

    path = Path(ffmpeg_path).resolve()

    if not path.is_file():
        raise RuntimeError(
            f"FFmpeg was installed but the executable does not exist:\n"
            f"{path}"
        )

    return str(path)


def save_video(
    path: Path,
    data: np.ndarray,
    fps: float,
    ffmpeg: str | None = None,
) -> None:
    """
    Save a video using FFmpeg + Ut Video.

    The NumPy frames are streamed directly to FFmpeg stdin.
    No intermediate PNG files are created.

    Output:
        AVI container
        Ut Video codec
        lossless encoding
    """
    path = Path(path)
    ensure_directory(path.parent)

    if ffmpeg is None:
        ffmpeg = find_ffmpeg()

    frames, input_pix_fmt, output_pix_fmt = prepare_ffmpeg_frames(data)

    height = frames.shape[1]
    width = frames.shape[2]

    command = [
        ffmpeg,
        "-y",

        # Raw frames coming from NumPy
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        input_pix_fmt,
        "-s",
        f"{width}x{height}",
        "-r",
        str(float(fps)),
        "-i",
        "-",

        # No audio
        "-an",

        # Ut Video
        "-c:v",
        "utvideo",
        "-pix_fmt",
        output_pix_fmt,

        # Output
        str(path),
    ]

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    try:
        assert process.stdin is not None

        # Make sure NumPy memory is contiguous before sending it.
        frames = np.ascontiguousarray(frames)

        process.stdin.write(frames.tobytes())
        process.stdin.close()

        stderr = process.stderr.read().decode(
            errors="replace"
        )

        return_code = process.wait()

    except Exception:
        process.kill()
        process.wait()
        raise

    if return_code != 0:
        raise RuntimeError(
            f"FFmpeg failed while saving {path}.\n"
            f"Command: {' '.join(command)}\n"
            f"FFmpeg output:\n{stderr}"
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

            print(f"Saved PNG: {name}")

        except Exception as exc:
            print(f"Failed to save PNG {name}: {exc}")


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


# ============================================================================
# 6. HDF5
# ============================================================================


def save_h5(
    target_dir: Path,
    data_map: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    save_only_list: Iterable[str] | None = None,
    reg_list: Any = None,
    coefs_list: Any = None,
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

    print(f"Saving H5: {h5_path}")

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

    print(
        f"H5 saved: {h5_path} "
        f"({size_gb:.2f} GB)"
    )

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

    if parameters is not None:
        save_json(
            json_dir / "parameters_holodoppler.json",
            parameters,
        )

    if file_reader is not None:
        if getattr(file_reader, "extension", None) == ".holo":
            footer = getattr(file_reader, "footer", None)
            if footer is not None:
                save_json(
                    json_dir / "holovibes_footer.json",
                    footer,
                )

            header = getattr(file_reader, "header", None)
            if header is not None:
                if is_dataclass(header):
                    header = asdict(header)
                save_json(
                    json_dir / "holovibes_header.json",
                    header,
                )

    save_version_files(target_dir)


# ============================================================================
# Output helpers
# ============================================================================

def is_csv_h5_output(name: str) -> bool:
    """Return True if an output must be saved to both CSV and HDF5."""
    name = name.lower()
    return "coefs" in name or "registration" in name


def save_csv_outputs(
    target_dir: Path,
    output: dict[str, Any],
) -> list[str]:
    """
    Save coefs/registration outputs to CSV.

    Returns the output names that should also be stored in HDF5.
    """
    csv_dir = ensure_directory(Path(target_dir) / "csv")
    h5_names = []

    for name, value in output.items():
        if value is None or not is_csv_h5_output(name):
            continue

        h5_names.append(name)

        try:
            path = csv_dir / f"{name}.csv"
            save_csv(path, value)
            print(f"Saved CSV: {path}")
        except Exception as exc:
            print(f"Failed to save CSV {name}: {exc}")

    return h5_names


def create_directories(
    target_dir: Path,
    full: bool = True,
) -> None:
    """Create the output directory structure."""
    target_dir = Path(target_dir)

    subdirectories = [
        "png",
        "avi",
        "json",
        "csv",
        "yaml",
    ]

    if full:
        subdirectories.append("h5")

    for directory in subdirectories:
        ensure_directory(target_dir / directory)

def save_videos(
    target_dir: Path,
    data_map: dict[str, Any],
    fps: float,
    video_keys: Iterable[str] | None = None,
) -> None:
    """
    Save all requested video arrays as Ut Video AVI files.

    Images are ignored.

    FFmpeg is located/downloaded once and reused for all videos.
    """
    avi_dir = ensure_directory(Path(target_dir) / "avi")

    selected = None if video_keys is None else set(video_keys)

    # Find existing FFmpeg or download it.
    ffmpeg = find_ffmpeg()

    print(f"Using FFmpeg: {ffmpeg}")

    for name, value in data_map.items():

        if value is None or not isinstance(value, np.ndarray):
            continue

        if not is_video(value):
            continue

        if selected is not None and name not in selected:
            continue

        path = avi_dir / f"{name}.avi"

        start = time.time()

        save_video(
            path,
            value,
            fps=fps,
            ffmpeg=ffmpeg,
        )

        print(
            f"Saved video: {path} "
            f"({time.time() - start:.1f}s)"
        )


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
    num_batch: int | None,
    end_frame: int | None,
    first_frame: int | None,
    parameters: dict[str, Any] | None,
    default_fps: float = 30.0,
    maximum_fps: float = 65.0,
) -> float:
    """Calculate output FPS with safe fallbacks."""
    if (
        num_batch is None
        or end_frame is None
        or first_frame is None
    ):
        return default_fps

    frame_range = end_frame - first_frame

    if frame_range <= 0:
        return default_fps

    parameters = parameters or {}
    sampling_freq = parameters.get("sampling_freq", 1000)

    fps = num_batch / frame_range * sampling_freq

    return min(float(fps), maximum_fps)


# ============================================================================
# Bundle saving
# ============================================================================

def save_bundle(
    target_dir: Path,
    output: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    file_reader: Any = None,
    fps: float = 30.0,
    save_h5_output: bool = True,
    save_h5_list: Iterable[str] | None = None,
    video_keys: Iterable[str] | None = None,
    png_keys: Iterable[str] | None = None,
    json_outputs: dict[str, Any] | None = None,
    yaml_outputs: dict[str, Any] | None = None,
    reg_list: Any = None,
    coefs_list: Any = None,
    backend: Any = None,
    square: bool = False,
) -> None:
    """Save a complete Holodoppler output bundle."""
    start_time = time.time()
    target_dir = Path(target_dir)

    create_directories(
        target_dir,
        full=save_h5_output,
    )

    print(f"Saving output bundle to: {target_dir}")

    # ------------------------------------------------------------------
    # 1. Videos
    # ------------------------------------------------------------------

    save_videos(
        target_dir,
        output,
        fps=fps,
        video_keys=video_keys,
    )

    # ------------------------------------------------------------------
    # 2. PNGs
    # ------------------------------------------------------------------

    save_pngs(
        target_dir,
        output,
        png_keys=png_keys,
    )

    # ------------------------------------------------------------------
    # 3. Automatic CSV outputs
    #
    # Any output containing "coefs" or "registration" is saved as CSV
    # and included in HDF5.
    # ------------------------------------------------------------------

    csv_h5_names = save_csv_outputs(
        target_dir,
        output,
    )

    # ------------------------------------------------------------------
    # 4. JSON / YAML
    # ------------------------------------------------------------------

    if json_outputs:
        for name, value in json_outputs.items():
            save_json(
                target_dir / "json" / f"{name}.json",
                value,
            )

    if yaml_outputs:
        for name, value in yaml_outputs.items():
            save_yaml(
                target_dir / "yaml" / f"{name}.yaml",
                value,
            )

    # ------------------------------------------------------------------
    # 5. Metadata
    # ------------------------------------------------------------------

    save_metadata(
        target_dir,
        file_reader=file_reader,
        parameters=parameters,
    )

    # ------------------------------------------------------------------
    # 6. HDF5
    # ------------------------------------------------------------------

    if save_h5_output:
        h5_names = list(save_h5_list or [])

        for name in csv_h5_names:
            if name not in h5_names:
                h5_names.append(name)

        save_h5(
            target_dir,
            output,
            parameters=parameters,
            save_only_list=h5_names,
            reg_list=reg_list,
            coefs_list=coefs_list,
            git_commit=get_git_version(),
        )

    elapsed = time.time() - start_time
    print(f"Saving completed in {elapsed:.1f} seconds")


# ============================================================================
# Main public entry point
# ============================================================================

def save_outputs(
    file_reader: Any,
    output: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    holodoppler_path: str | Path | bool | None = None,
    video_path: str | Path | bool | None = None,
    custom_path: str | Path | None = None,
    custom_relative_path: str | Path | None = None,
    reg_list: Any = None,
    coefs_list: Any = None,
    end_frame: int | None = None,
    first_frame: int | None = None,
    num_batch: int | None = None,
    backend: Any = None,
    save_h5_output: bool = True,
    png_keys: Iterable[str] | None = None,
    video_keys: Iterable[str] | None = None,
    square: bool = False,
) -> Path:
    """
    Main public saving entry point.

    custom_path:
        Absolute path used directly as the output directory.

    custom_relative_path:
        Path relative to the default *_HD output directory.

    Example:
        custom_relative_path="preview"
        -> <default_output_path>/preview
    """
    parameters = parameters or {}

    default_path = get_default_output_path(
        file_reader.file_path
    )

    # ------------------------------------------------------------------
    # Resolve target path
    # ------------------------------------------------------------------

    if custom_path is not None and custom_relative_path is not None:
        raise ValueError(
            "custom_path and custom_relative_path "
            "cannot be used together"
        )

    if custom_path is not None:
        target_dir = Path(custom_path).expanduser()

        if not target_dir.is_absolute():
            raise ValueError(
                "custom_path must be an absolute path"
            )

    elif custom_relative_path is not None:
        relative_path = Path(custom_relative_path)

        if relative_path.is_absolute():
            raise ValueError(
                "custom_relative_path must be relative"
            )

        target_dir = default_path / relative_path

    elif holodoppler_path:
        target_dir = (
            default_path
            if isinstance(holodoppler_path, bool)
            else Path(holodoppler_path)
        )

    elif video_path:
        target_dir = (
            default_path
            if isinstance(video_path, bool)
            else Path(video_path)
        )

    else:
        target_dir = default_path

    # ------------------------------------------------------------------
    # FPS
    # ------------------------------------------------------------------

    fps = calculate_fps(
        num_batch=num_batch,
        end_frame=end_frame,
        first_frame=first_frame,
        parameters=parameters,
    )

    # ------------------------------------------------------------------
    # HDF5 outputs
    #
    # Fixed outputs + all "band_*" + automatic coefs/registration.
    # ------------------------------------------------------------------

    save_h5_list = [
        "moment0ff",
        "moment0",
        "moment1",
        "moment2",
        "spectrum_line",
    ]

    save_h5_list.extend(
        key
        for key in output
        if (
            "band_" in key
            or "coefs" in key.lower()
            or "registration" in key.lower()
        )
    )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    save_bundle(
        target_dir=target_dir,
        output=output,
        parameters=parameters,
        file_reader=file_reader,
        fps=fps,
        save_h5_output=save_h5_output,
        save_h5_list=save_h5_list,
        video_keys=video_keys,
        png_keys=png_keys,
        reg_list=reg_list,
        coefs_list=coefs_list,
        backend=backend,
        square=square,
    )

    return target_dir