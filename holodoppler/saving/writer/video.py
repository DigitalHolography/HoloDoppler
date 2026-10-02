"""Video writing on top of the imageio FFMPEG plugin.

Two containers are produced for every video:

``avi``
    MJPEG, 4:2:2, full range. This is the historical HoloDoppler output.
``mp4``
    H.264/AVC through ``libx264`` with ``yuv420p``. Much smaller and far more
    widely decodable, at the cost of a second encode pass and chroma
    subsampling.

The writer no longer builds an FFmpeg command line by hand and no longer needs
the ``imageio-ffmpeg`` executable to be resolved by the application: the
``imageio[ffmpeg]`` dependency ships the binary, and imageio locates it while
opening the stream.

Note on the MJPEG deprecation notice:
    FFmpeg 7.1's MJPEG encoder auto-selects the deprecated full-range
    ``yuvj422p`` for *any* MJPEG encode, so ``swscaler`` reports "deprecated
    pixel format used" whatever pixel format is requested (verified for
    ``yuvj422p``, ``yuv422p``, ``yuv420p``, ``-color_range pc`` and explicit
    ``-vf scale=out_range=...`` filters). The notice is informational and every
    encode succeeds. Requesting the non-deprecated ``yuv422p`` name keeps the
    same 4:2:2 chroma and identical output, and the H.264 path is warning-free.

Known limitation:
    imageio's FFMPEG writer silently keeps only the first frame when the frame
    size is extremely small (observed at 4x4, fine from 8x8 up). Pure FFmpeg
    handles 4x4 correctly, so it is an imageio writer issue. :func:`write_video`
    guards against it by padding frames up to :data:`MIN_FRAME_SIZE`.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import imageio.v3 as iio
import numpy as np

from holodoppler.saving.format.video import (
    is_video,
    make_dimensions_multiple_of,
    prepare_video_frames,
)
from holodoppler.saving.paths import ensure_directory


@dataclass(frozen=True)
class VideoFormat:
    """One container + codec pairing used for video output."""

    #: Format label, also the output sub-directory (``avi``, ``mp4``).
    name: str
    #: FFmpeg encoder name.
    codec: str
    #: Output pixel format.
    pixelformat: str
    #: File extension, including the dot.
    extension: str
    #: Constant Rate Factor, for encoders that take one instead of ``q:v``.
    crf: int | None = None
    #: Legacy ``q:v`` value, for encoders that take that instead.
    q_v: int | None = None


#: The two shipped output formats, keyed by format label.
DEFAULT_VIDEO_FORMATS: Mapping[str, VideoFormat] = {
    # Full-range 4:2:2: `yuv422p` is the modern spelling of the historical
    # `yuvj422p`. There is no pure-`pixelformat` argument that silences
    # FFmpeg's deprecation notice (see the module docstring).
    "avi": VideoFormat(
        name="avi",
        codec="mjpeg",
        pixelformat="yuv422p",
        extension=".avi",
        q_v=1,
    ),
    # yuv420p rather than imageio's yuv444p default: every player and hardware
    # decoder handles 4:2:0 H.264, and the difference is invisible for this data.
    "mp4": VideoFormat(
        name="mp4",
        codec="libx264",
        pixelformat="yuv420p",
        extension=".mp4",
        crf=18,
    ),
}

#: The formats written when `write_videos` is not told otherwise.
DEFAULT_OUTPUT_FORMATS: tuple[str, ...] = ("avi", "mp4")

#: Output pixel format per encoder, kept for backwards compatibility with the
#: previous public constant. Derived from :data:`DEFAULT_VIDEO_FORMATS`.
DEFAULT_PIXELFORMATS: dict[str, str] = {
    "mjpeg": "yuvj422p",
    "utvideo": "gbrp",
}

#: Codecs that take a CRF-style quality value instead of ``q:v``.
_CRF_CODECS = frozenset({"libx264", "libx265", "h264", "hevc"})

#: Smallest frame side handed to the encoder.
#:
#: Not a codec requirement: imageio's FFMPEG writer silently keeps only the
#: first frame when the frames are tiny (reproduced at 4x4, correct from 8x8
#: up, while pure FFmpeg handles 4x4). Letting imageio's ``macro_block_size``
#: do the work is not an option because that path *resizes* the image instead of
#: padding it, so the frames are padded here. This is a floor, not a
#: granularity: larger frames keep their own size.
MIN_FRAME_SIZE = 16

#: imageio FFMPEG plugin name used for every write.
_FFMPEG_PLUGIN = "FFMPEG"


def resolve_video_format(
    name: str,
    formats: Mapping[str, VideoFormat] | None = None,
) -> VideoFormat:
    """
    Look up one output format by label or by codec name.

    ``"mp4"`` and ``"libx264"`` both resolve to the H.264 format, which keeps
    callers that pass a codec name working.
    """
    catalogue = DEFAULT_VIDEO_FORMATS if formats is None else formats
    key = name.strip().lower()

    if key in catalogue:
        return catalogue[key]

    for video_format in catalogue.values():
        if video_format.codec == key:
            return video_format

    raise ValueError(
        f"Unknown video format {name!r}. "
        f"Supported: {sorted(catalogue)} (or their codec names "
        f"{sorted({item.codec for item in catalogue.values()})})."
    )


def quality_from_q_v(q_v: int | float) -> float:
    """
    Convert a legacy FFmpeg ``q:v`` value into imageio's 1-10 quality scale.

    ``q:v`` is "lower is better" and starts at 1; imageio maps quality ``q`` to
    ``-qscale:v int((1 - q / 10) * 30) + 1``.  ``q_v=1`` therefore becomes the
    maximum quality 10, and the worst ``q:v=31`` maps back to 1.
    """
    clamped = min(max(float(q_v), 1.0), 31.0)
    return 1.0 + (31.0 - clamped) / 30.0 * 9.0


def _quality_options(
    codec: str,
    quality: float | None,
    q_v: int | None,
    crf: int | None,
) -> dict[str, Any]:
    """
    Resolve the encoder options for one `write_video` call.

    Precedence: an explicit ``q_v``, then an explicit ``quality``, then the
    encoder's default (a CRF for x264/x265, ``q:v=1`` for MJPEG, otherwise no
    quality flag at all).
    """
    if q_v is not None:
        return {"quality": quality_from_q_v(q_v)}

    if quality is not None:
        return {"quality": float(min(max(quality, 1.0), 10.0))}

    if codec.lower() in _CRF_CODECS:
        if crf is not None:
            return {"quality": float(51 - min(max(int(crf), 0), 51)) / 51.0 * 10.0}
        return {"quality": 5.0}

    if codec.lower() == "mjpeg":
        # Historical behaviour: q:v=1, the best MJPEG quality.
        return {"quality": 10.0}

    return {}


def _default_pixelformat(codec: str, pixelformat: str | None) -> str:
    """Resolve the output pixel format for one `write_video` call."""
    if pixelformat is not None:
        return pixelformat

    for video_format in DEFAULT_VIDEO_FORMATS.values():
        if video_format.codec == codec.lower():
            return video_format.pixelformat

    return DEFAULT_PIXELFORMATS.get(codec.lower(), "yuv444p")


@lru_cache(maxsize=1)
def available_encoders() -> frozenset[str]:
    """
    Names of the encoders offered by the bundled FFmpeg build.

    Queried once per process. An empty result (or an FFmpeg that cannot be
    started) disables codec validation rather than failing every write.
    """
    try:
        binary = find_ffmpeg()
    except RuntimeError:
        return frozenset()

    try:
        completed = subprocess.run(
            [binary, "-hide_banner", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return frozenset()

    if completed.returncode != 0:
        return frozenset()

    return frozenset(parse_encoder_names(completed.stdout))


def parse_encoder_names(output: str) -> set[str]:
    """
    Extract encoder names from ``ffmpeg -encoders`` output.

    The listing has one ``FLAGS NAME DESCRIPTION`` row per encoder, so the
    second whitespace-separated field of every parseable row is the name.
    """
    names: set[str] = set()

    for line in output.splitlines():
        fields = line.split()
        if len(fields) < 2:
            continue

        flags, name = fields[0], fields[1]
        if len(flags) != 6 or not flags[0].isalpha():
            # Header line, or a row whose first field is not a flag column.
            continue

        names.add(name)

    return names


def _validate_codec(codec: str) -> None:
    """
    Reject an encoder name FFmpeg does not know.

    imageio's writer only discovers an unknown encoder when the child process
    dies, and by then it is easy to mistake the empty file for a real video.
    """
    known = available_encoders()
    if not known:
        return

    if codec not in known:
        raise ValueError(
            f"Unknown FFmpeg encoder {codec!r}. "
            "Use one of the encoders reported by 'ffmpeg -encoders' "
            "(HoloDoppler uses 'mjpeg' and 'utvideo')."
        )


def write_video(
    path: Path | str,
    data: np.ndarray,
    fps: float,
    *,
    codec: str = "mjpeg",
    quality: float | None = None,
    q_v: int | None = None,
    crf: int | None = None,
    pixelformat: str | None = None,
    macro_block_size: int = 1,
    **writer_kwargs: Any,
) -> Path:
    """
    Write one video with the imageio FFMPEG writer.

    Args:
        path: Destination file.
        data: ``(T, H, W)`` grayscale or ``(T, H, W, 3/4)`` colour video.
            Any dtype is accepted and normalized to ``uint8``, over the whole
            video at once (one min/max for all frames).
        fps: Output frame rate.
        codec: FFmpeg encoder name. ``mjpeg`` and ``libx264`` are what
            HoloDoppler ships; see :data:`DEFAULT_VIDEO_FORMATS`.
        quality: imageio quality on a 1-10 scale, 10 being best.
        q_v: Legacy FFmpeg ``q:v`` value; takes precedence over ``quality`` and
            is converted with :func:`quality_from_q_v`.
        crf: Constant Rate Factor for x264/x265, used when neither ``q_v`` nor
            ``quality`` is given.
        pixelformat: Output pixel format; defaults per encoder through
            :data:`DEFAULT_VIDEO_FORMATS`.
        macro_block_size: Dimension padding granularity. Frames are always
            padded to at least :data:`MIN_FRAME_SIZE` and to even dimensions
            (which yuv420p H.264 requires); set this higher, e.g. ``16``, to
            align frames for stricter players or hardware encoders. imageio's
            own upscaling stays disabled so the pixel grid is never resampled.
        **writer_kwargs: Extra imageio FFMPEG writer options (``bitrate``,
            ``ffmpeg_params``, ``ffmpeg_log_level``, ...).

    Returns:
        The path that was written.

    Raises:
        ValueError: The array is not a valid video, or ``codec`` is not an
            encoder the bundled FFmpeg offers.
        RuntimeError: FFmpeg exited without producing a video.
        Exception: Whatever imageio raises; the target file is removed first so
            a failed encode cannot look like a product.
    """
    path = Path(path)
    ensure_directory(path.parent)

    frames = prepare_video_frames(data)

    # `macro_block_size` is imageio's own request to upscale the frame to a
    # multiple of that size. It is disabled (1) because the padding is done here
    # instead: imageio's upscaling would *resize* the image rather than pad it,
    # changing the pixel grid. Frames are padded to even dimensions (which
    # yuv420p H.264 requires), to at least `MIN_FRAME_SIZE`, and to a multiple of
    # `macro_block_size` when the caller asks for stricter alignment.
    padding_multiple = max(2, int(macro_block_size))
    frames = make_dimensions_multiple_of(frames, padding_multiple)

    # Pad up to the floor as well, but only when the frame is actually below it:
    # this helper rounds up to a multiple, so applying it unconditionally would
    # widen an already-large frame.
    if min(frames.shape[1], frames.shape[2]) < MIN_FRAME_SIZE:
        frames = make_dimensions_multiple_of(frames, MIN_FRAME_SIZE)

    writer_kwargs.setdefault("ffmpeg_log_level", "error")

    options: dict[str, Any] = {
        "fps": float(fps),
        "codec": codec,
        "pixelformat": _default_pixelformat(codec, pixelformat),
        "macro_block_size": 1,
    }

    options.update(_quality_options(codec, quality, q_v, crf))
    options.update(writer_kwargs)

    # Remove the previous file up front: imageio opens FFmpeg with -y, but a
    # failure before the encoder starts would otherwise keep a stale video.
    if path.exists():
        path.unlink()

    # Reject an encoder FFmpeg does not know before any file is created.
    _validate_codec(codec)

    try:
        # imageio's FFMPEG plugin is still a legacy (v2) format. Its writer can
        # only be used through a single ``imwrite`` call: every ``write`` call on
        # an ``imopen`` handle opens and closes the encoder, which silently keeps
        # just the first frame. Handing it the whole block writes every frame.
        # A ``(T, H, W)`` array is interpreted as a batch of grayscale frames and
        # ``(T, H, W, 3)`` as a batch of RGB frames, which matches how the frames
        # were prepared above.
        iio.imwrite(path, frames, plugin=_FFMPEG_PLUGIN, **options)
    except BaseException:
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        raise

    if not path.is_file() or path.stat().st_size == 0:
        # FFmpeg can die without imageio noticing, which would otherwise leave
        # the caller with a "successful" save and no video.
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass

        raise RuntimeError(
            f"FFmpeg produced no output while saving {path} "
            f"(codec={codec!r}, fps={float(fps)}). "
            "Check the FFmpeg diagnostics above for the failing encoder."
        )

    return path


def save_video(
    path: Path | str,
    data: np.ndarray,
    fps: float,
    ffmpeg: str | None = None,
    codec: str = "mjpeg",
) -> None:
    """
    Backwards-compatible wrapper around :func:`write_video`.

    The ``ffmpeg`` argument is accepted and ignored: the executable is resolved
    by imageio instead of by the caller.
    """
    write_video(path, data, fps, codec=codec)


def write_videos(
    target_dir: Path | str,
    data_map: dict[str, Any],
    fps: float,
    video_keys: Iterable[str] | None = None,
    formats: Sequence[str] | None = None,
    tally: Any = None,
) -> dict[str, int]:
    """
    Save every requested video array once per output format.

    ``avi`` (MJPEG) goes to ``<target_dir>/avi`` and ``mp4`` (H.264) to
    ``<target_dir>/mp4``; see :data:`DEFAULT_VIDEO_FORMATS` and
    :data:`DEFAULT_OUTPUT_FORMATS`.

    Images and non-array values are ignored.

    Returns:
        The number of files written per format label.
    """
    target_dir = Path(target_dir)
    requested = DEFAULT_OUTPUT_FORMATS if formats is None else tuple(formats)
    selected = None if video_keys is None else set(video_keys)

    video_formats = [resolve_video_format(name) for name in requested]

    # Only create a directory when that format actually has something to write.
    writable = [
        (name, value)
        for name, value in data_map.items()
        if value is not None
        and isinstance(value, np.ndarray)
        and is_video(value)
        and (selected is None or name in selected)
    ]

    counts: dict[str, int] = {video_format.name: 0 for video_format in video_formats}

    for video_format in video_formats:
        if not writable:
            continue

        target = ensure_directory(target_dir / video_format.name)

        for name, value in writable:
            write_video(
                target / f"{name}{video_format.extension}",
                value,
                fps=fps,
                codec=video_format.codec,
                pixelformat=video_format.pixelformat,
                crf=video_format.crf,
                q_v=video_format.q_v,
            )

            counts[video_format.name] += 1

            if tally is not None:
                tally.record_video(video_format.name)

    return counts


def save_videos(
    target_dir: Path,
    data_map: dict[str, Any],
    fps: float,
    video_keys: Iterable[str] | None = None,
) -> None:
    """Deprecated alias of :func:`write_videos`."""
    write_videos(
        target_dir,
        data_map,
        fps=fps,
        video_keys=video_keys,
    )


def find_ffmpeg() -> str:
    """
    Return the FFmpeg executable bundled with the ``imageio-ffmpeg`` wheel.

    Deprecated: video writing goes through the imageio FFMPEG plugin, which
    resolves the same binary itself, so normal processing never needs this.
    It is kept for the installer's frozen-runtime smoke test, which checks that
    the packaged application can still start FFmpeg.

    Returns:
        Absolute path to the bundled ffmpeg executable.
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

    return str(Path(executable).resolve())
