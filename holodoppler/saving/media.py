"""Image conversion, video encoders, and streaming media resources."""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable, Literal

import numpy as np
from PIL import Image

from holodoppler.core.image_utils import resize_frames
from holodoppler.logging import logger
from . import data as numerical
from . import policy

VideoWriter = Literal["imageio", "cmd", "pyav"]


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

    floating_rgb = (np.issubdtype(data.dtype, np.floating) and data.ndim in (3, 4)
                    and data.shape[-1] in (3, 4))

    data = np.nan_to_num(
        data,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    ).astype(np.float32, copy=False)

    if data.size == 0:
        return np.zeros_like(data, dtype=np.uint8)

    if floating_rgb:
        # Floating RGB already has an absolute display range; preserve its colors.
        return np.rint(data * 255).clip(0, 255).astype(np.uint8)

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
    numerical.ensure_directory(path.parent)

    image = prepare_png_image(data)
    image.save(path)


def validate_video(data: np.ndarray) -> np.ndarray:
    """
    Validate and prepare video data.

    Accepted:
        (T, H, W)
        (T, H, W, 3)
        (T, H, W, 4)
    """
    data = np.asarray(data)

    if not policy.is_video(data):
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

    average = np.mean(data, axis=0, dtype=np.float64)

    if data.dtype == np.uint8 and policy.is_color_video(data):
        return np.rint(average).clip(0, 255).astype(np.uint8)

    return cast_png_data(average)


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


def _save_average_png(path: Path, average: np.ndarray, resize_averaged_images: bool) -> None:
    image = prepare_png_image(average)
    if resize_averaged_images:
        image = image.resize((image.width * 2, image.height * 2), Image.Resampling.BICUBIC)
    numerical.ensure_directory(Path(path).parent)
    image.save(path)


def save_video_average_png(path: Path, video: np.ndarray, *, resize_averaged_images: bool = False) -> None:
    """
    Save the temporal average of a video as PNG.

    The average is calculated first in the original numerical representation,
    then converted to a PNG-compatible integer representation.
    """
    average = average_video(video)
    _save_average_png(path, average, resize_averaged_images)


def save_image_png(path: Path, image: np.ndarray) -> None:
    """Save an image directly as PNG."""
    if not policy.is_image(image):
        raise ValueError(f"Invalid image shape: {image.shape}")

    save_png(path, image)


def save_pngs(
    target_dir: Path,
    data_map: dict[str, Any],
    png_keys: Iterable[str] | None = None,
    *,
    resize_averaged_images: bool = False,
) -> None:
    """Save images and temporal-average PNGs."""
    png_dir = numerical.ensure_directory(target_dir / "png")
    selected_keys = None if png_keys is None else set(png_keys)

    for name, data in data_map.items():
        if data is None or not isinstance(data, np.ndarray):
            continue

        if selected_keys is not None and name not in selected_keys:
            continue

        if "png" not in policy.output_formats(name, data):
            continue

        try:
            path = png_dir / f"{name}.png"

            if policy.is_image(data):
                save_image_png(path, data)

            elif policy.is_video(data):
                save_video_average_png(path, data, resize_averaged_images=resize_averaged_images)

            else:
                continue

            logger.info(f"Saved PNG: {name}")

        except Exception as exc:
            logger.exception(f"Failed to save PNG {name}: {exc}")


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
    numerical.ensure_directory(path.parent)

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
    numerical.ensure_directory(path.parent)

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
    avi_dir = numerical.ensure_directory(Path(target_dir) / "avi")
    mp4_dir = numerical.ensure_directory(Path(target_dir) / "mp4")

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
        if not {"avi", "mp4"}.intersection(policy.output_formats(name, value)):
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


def open_video(target_dir: Path, name: str, fmt: str, fps: float):
    """Open the streaming encoder with the existing display codec settings."""
    import imageio.v2 as imageio

    kwargs = dict(fps=fps, macro_block_size=2, pixelformat="yuv420p")
    if fmt == "avi":
        kwargs.update(codec="mjpeg", quality=10,
                      ffmpeg_params=["-color_range", "pc"])
    else:
        kwargs.update(codec="libx264",
                      ffmpeg_params=["-crf", "18", "-preset", "medium"])
    return imageio.get_writer(str(target_dir / fmt / f"{name}.{fmt}"), **kwargs)


class MediaStream:
    """Own encoders, first-frame display levels, and an unquantized average."""

    def __init__(self, target_dir: Path, name: str, open_encoder, *, resize_averaged_images: bool = False):
        self.target_dir = target_dir
        self.name = name
        self.open_encoder = open_encoder
        self.resize_averaged_images = resize_averaged_images
        self.writers = []
        self.count = 0
        self.total = None
        self.display_range = None
        self.dtype = None

    def append(self, value: np.ndarray) -> None:
        clean = np.nan_to_num(value, nan=0., posinf=0., neginf=0.).astype(np.float64)
        if self.count == 0:
            self.dtype = value.dtype
            self.display_range = (float(clean.min()), float(clean.max()))
            self.total = np.zeros_like(clean)
            for fmt in ("avi", "mp4"):
                self.writers.append(self.open_encoder(fmt))
        low, high = self.display_range
        if value.dtype == np.uint8:
            frame = value
        elif (np.issubdtype(value.dtype, np.floating) and value.ndim == 3
              and value.shape[-1] in (3, 4)):
            frame = np.rint(clean * 255).clip(0, 255).astype(np.uint8)
        elif value.dtype == np.uint16:
            frame = (clean / 65535. * 255.).astype(np.uint8)
        elif high > low:
            frame = (np.clip((clean - low) / (high - low), 0., 1.) * 255.).astype(np.uint8)
        else:
            frame = np.zeros(value.shape, dtype=np.uint8)
        if frame.ndim == 2:
            frame = np.repeat(frame[..., None], 3, axis=-1)
        frame = make_even_dimensions(frame[None, ..., :3])[0]
        for writer in self.writers:
            writer.append_data(np.ascontiguousarray(frame))
        self.total += value
        self.count += 1

    def close(self, *, finalize: bool = True) -> None:
        errors = []
        for writer in self.writers:
            try:
                writer.close()
            except Exception as exc:
                errors.append(exc)
        self.writers.clear()
        if finalize and self.count:
            try:
                average = self.total / self.count
                if self.dtype == np.uint8 and average.ndim == 3:
                    average = np.rint(average).clip(0, 255).astype(np.uint8)
                _save_average_png(self.target_dir / "png" / f"{self.name}.png", average,
                                  self.resize_averaged_images)
            except Exception as exc:
                errors.append(exc)
        if errors:
            raise RuntimeError(f"Failed to finalize media output {self.name!r}") from errors[0]


def media_jobs(target_dir: Path, name: str, value: np.ndarray, fps: float, *, resize_averaged_images: bool = False):
    """Describe static image or complete-video exports for any execution mode."""
    formats = policy.output_formats(name, value)
    for fmt in ("avi", "mp4"):
        if fmt in formats:
            yield save_video, (target_dir / fmt / f"{name}.{fmt}", value, fps), {"writer": "imageio"}
    if "png" in formats:
        callback = save_image_png if policy.is_image(value) else save_video_average_png
        kwargs = {} if policy.is_image(value) else {"resize_averaged_images": resize_averaged_images}
        yield callback, (target_dir / "png" / f"{name}.png", value), kwargs
