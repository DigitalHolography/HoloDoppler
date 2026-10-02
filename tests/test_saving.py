"""Unit tests for the ``holodoppler.saving`` package.

The package has two halves and both are covered here:

* ``saving.format`` prepares data and is tested without any filesystem access.
* ``saving.writer`` puts data on disk; the video tests use the real bundled
  FFmpeg through imageio and are skipped when that binary is unavailable.

The end-to-end artifact contract stays in ``tests/test_output_contract.py``.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import imageio.v3 as iio
import numpy as np
import pytest
import yaml
from PIL import Image

import holodoppler.saving as saving
from holodoppler.saving.format import (
    cast_png_data,
    is_image,
    is_video,
    make_even_dimensions,
    normalize_float_array_to_uint8,
    prepare_png_image,
    prepare_video_frames,
    to_serializable,
    validate_video,
)


# ---------------------------------------------------------------------------
# Availability guard
# ---------------------------------------------------------------------------

def _ffmpeg_available() -> bool:
    try:
        binary = Path(saving.find_ffmpeg())
    except Exception:
        return False

    return binary.is_file()


requires_ffmpeg = pytest.mark.skipif(
    not _ffmpeg_available(),
    reason="the bundled imageio-ffmpeg binary is unavailable",
)


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

EXPECTED_PUBLIC_NAMES = frozenset(
    {
        # paths
        "calculate_fps",
        "create_directories",
        "ensure_directory",
        "get_default_output_path",
        "is_csv_h5_output",
        # version
        "get_git_version",
        "save_version_files",
        # format
        "json_default",
        "to_serializable",
        "normalize_float_array_to_uint8",
        "cast_png_data",
        "prepare_png_image",
        "is_image",
        "is_grayscale_video",
        "is_color_video",
        "is_video",
        "validate_video",
        "video_to_uint8",
        "average_video",
        "make_even_dimensions",
        "prepare_video_frames",
        "prepare_ffmpeg_frames",
        # writers
        "save_png",
        "save_image_png",
        "save_video_average_png",
        "save_pngs",
        "write_video",
        "write_videos",
        "save_video",
        "save_videos",
        "find_ffmpeg",
        "save_txt",
        "save_csv",
        "save_csv_outputs",
        "save_json",
        "save_yaml",
        "save_h5",
        "save_metadata",
        "save_bundle",
        "save_outputs",
        # output formats and reporting
        "VideoFormat",
        "DEFAULT_VIDEO_FORMATS",
        "DEFAULT_OUTPUT_FORMATS",
        "DEFAULT_PIXELFORMATS",
        "resolve_video_format",
        "WriteTally",
    }
)


def test_public_surface_is_unchanged_by_the_split() -> None:
    """Every historical ``holodoppler.saving`` name still exists."""
    missing = sorted(name for name in EXPECTED_PUBLIC_NAMES if not hasattr(saving, name))

    assert not missing, f"names lost in the saving/ split: {missing}"


def test_package_exposes_the_format_and_writer_groups() -> None:
    import holodoppler.saving.format as saving_format
    import holodoppler.saving.writer as saving_writer

    assert saving_format.prepare_video_frames is saving.prepare_video_frames
    assert saving_writer.write_video is saving.write_video
    assert saving_writer.save_video is saving.save_video


# ---------------------------------------------------------------------------
# format.normalize
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "data, expected_dtype",
    [
        (np.zeros((4, 4), dtype=np.uint8), np.uint8),
        (np.full((4, 4), 65535, dtype=np.uint16), np.uint8),
        (np.array([[-1.0, 0.0], [1.0, 2.0]], dtype=np.float32), np.uint8),
        (np.array([[5, 10], [15, 20]], dtype=np.uint16), np.uint8),
    ],
)
def test_normalize_float_array_to_uint8_dtypes(data, expected_dtype) -> None:
    result = normalize_float_array_to_uint8(data)

    assert result.dtype == expected_dtype
    assert result.shape == data.shape


def test_normalize_handles_nan_inf_and_constant_arrays() -> None:
    with_nan = np.array([[np.nan, np.inf], [-np.inf, 1.0]], dtype=np.float32)

    assert np.isfinite(normalize_float_array_to_uint8(with_nan)).all()

    constant = np.full((3, 3), 7.5, dtype=np.float32)

    assert (normalize_float_array_to_uint8(constant) == 0).all()

    empty = np.zeros((0, 0), dtype=np.float32)

    assert normalize_float_array_to_uint8(empty).dtype == np.uint8


def test_normalize_maps_range_onto_the_full_uint8_scale() -> None:
    data = np.array([[0.0, 5.0, 10.0]], dtype=np.float32)

    result = normalize_float_array_to_uint8(data)

    assert result.min() == 0
    assert result.max() == 255


def test_cast_png_data_keeps_integer_widths_and_normalizes_floats() -> None:
    assert cast_png_data(np.zeros((2, 2), dtype=np.uint16)).dtype == np.uint16
    assert cast_png_data(np.zeros((2, 2), dtype=np.uint8)).dtype == np.uint8
    assert cast_png_data(np.zeros((2, 2), dtype=np.float32)).dtype == np.uint8
    # 16-bit integers that fit in 8 bits are narrowed, larger ones are not.
    assert cast_png_data(np.array([[0, 255]], dtype=np.int32)).dtype == np.uint8
    assert cast_png_data(np.array([[0, 300]], dtype=np.int32)).dtype == np.uint16


@dataclass
class _Dataclass:
    value: int


def test_to_serializable_converts_scientific_types_recursively() -> None:
    payload = {
        "array": np.arange(3),
        "scalar": np.float32(1.5),
        "path": Path("a/b.txt"),
        "nested": [{"inner": np.int64(4)}],
        "dataclass": _Dataclass(value=2),
    }

    result = to_serializable(payload)

    assert result["array"] == [0, 1, 2]
    assert result["scalar"] == 1.5
    assert result["path"] in {"a\\b.txt", "a/b.txt"}
    assert result["nested"][0]["inner"] == 4
    assert result["dataclass"] == {"value": 2}
    # The result must survive a real dump.
    assert json.loads(json.dumps(result))["array"] == [0, 1, 2]


def test_json_default_rejects_unknown_objects() -> None:
    with pytest.raises(TypeError):
        saving.json_default(object())


# ---------------------------------------------------------------------------
# format.image
# ---------------------------------------------------------------------------

def test_is_image_distinguishes_images_from_videos() -> None:
    assert is_image(np.zeros((4, 4), dtype=np.uint8))
    assert is_image(np.zeros((4, 4, 3), dtype=np.uint8))
    assert is_image(np.zeros((4, 4, 4), dtype=np.uint8))
    assert not is_image(np.zeros((4, 4, 2), dtype=np.uint8))


@pytest.mark.parametrize(
    "shape, expected_mode",
    [
        ((4, 4), "L"),
        ((4, 4, 3), "RGB"),
        ((4, 4, 4), "RGBA"),
    ],
)
def test_prepare_png_image_modes(shape, expected_mode) -> None:
    image = prepare_png_image(np.zeros(shape, dtype=np.uint8))

    assert image.mode == expected_mode
    assert image.size == (shape[1], shape[0])


def test_prepare_png_image_preserves_16_bit_images() -> None:
    image = prepare_png_image(np.full((2, 3), 4096, dtype=np.uint16))

    assert image.mode == "I;16"


def test_prepare_png_image_rejects_unsupported_shapes() -> None:
    with pytest.raises(ValueError):
        prepare_png_image(np.zeros((4, 4, 2), dtype=np.uint8))


# ---------------------------------------------------------------------------
# format.video
# ---------------------------------------------------------------------------

def test_is_video_accepts_only_frame_stacks() -> None:
    assert is_video(np.zeros((5, 4, 4), dtype=np.uint8))
    assert is_video(np.zeros((5, 4, 4, 3), dtype=np.uint8))
    assert is_video(np.zeros((5, 4, 4, 4), dtype=np.uint8))
    # A single 3-D image is also a 1-frame grayscale stack.
    assert is_video(np.zeros((4, 4, 3), dtype=np.uint8))
    # 4-D stacks with an unsupported channel count are not videos.
    assert not is_video(np.zeros((5, 4, 4, 2), dtype=np.uint8))
    assert not is_video(np.zeros((4, 4), dtype=np.uint8))


def test_validate_video_rejects_zero_frames_and_bad_shapes() -> None:
    with pytest.raises(ValueError, match="zero frames"):
        validate_video(np.zeros((0, 4, 4), dtype=np.uint8))

    with pytest.raises(ValueError, match="Invalid video shape"):
        validate_video(np.zeros((4, 4), dtype=np.uint8))


def test_make_even_dimensions_pads_odd_sizes() -> None:
    gray = make_even_dimensions(np.zeros((3, 5, 7), dtype=np.uint8))

    assert gray.shape == (3, 6, 8)

    rgb = make_even_dimensions(np.zeros((2, 5, 7, 3), dtype=np.uint8))

    assert rgb.shape == (2, 6, 8, 3)

    already_even = np.zeros((2, 4, 6), dtype=np.uint8)

    assert make_even_dimensions(already_even) is already_even


def test_prepare_video_frames_normalizes_and_drops_alpha() -> None:
    gray = prepare_video_frames(np.random.default_rng(0).random((4, 5, 5)))

    assert gray.shape == (4, 6, 6)
    assert gray.dtype == np.uint8
    assert gray.flags["C_CONTIGUOUS"]

    rgba = np.zeros((2, 4, 4, 4), dtype=np.uint8)

    assert prepare_video_frames(rgba).shape == (2, 4, 4, 3)


def test_prepare_ffmpeg_frames_alias_warns_and_matches() -> None:
    data = np.zeros((2, 4, 4), dtype=np.uint8)

    with pytest.warns(DeprecationWarning):
        frames = saving.prepare_ffmpeg_frames(data)

    assert frames.shape == prepare_video_frames(data).shape


def test_average_video_is_computed_before_quantization() -> None:
    """The mean is taken in the video's own dtype, then converted.

    ``average_video`` keeps the long-standing ``cast_png_data`` conversion, which
    scales the average by the *average image's own* min/max. For a video whose
    mean has no range left (a constant average) that legitimately flattens to
    black, so this pins the current behaviour rather than an ideal one.
    """
    quantized = np.stack(
        [
            np.zeros((2, 2), dtype=np.uint8),
            np.full((2, 2), 200, dtype=np.uint8),
        ]
    )

    average = saving.average_video(quantized)

    assert average.dtype == np.uint8
    assert average.shape == (2, 2)
    # The mean of 0 and 200 is 100, but 100 is constant, so the conversion has
    # no range to work with and every pixel becomes 0.
    assert (average == 0).all()


def test_video_frames_share_one_range_over_the_whole_video() -> None:
    """Frames are normalized together, so relative frame brightness survives."""
    # Frame 0 is uniformly dark, frame 1 uniformly bright. A per-frame
    # normalization would flatten both to identical full-range images.
    data = np.zeros((2, 4, 4), dtype=np.float32)
    data[0] = 10.0
    data[1] = 500.0

    frames = prepare_video_frames(data)

    assert frames.shape == (2, 4, 4)
    assert frames[0].mean() < frames[1].mean()
    # One range for the whole block: the darkest frame maps to 0, the brightest
    # to 255.
    assert frames.min() == 0
    assert frames.max() == 255


# ---------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------

def test_ensure_directory_and_create_directories(case_dir: Path) -> None:
    nested = saving.ensure_directory(case_dir / "a" / "b")

    assert nested.is_dir()

    target = case_dir / "bundle"
    saving.create_directories(target)

    for name in ("png", "avi", "json", "csv", "yaml", "h5"):
        assert (target / name).is_dir()

    saving.create_directories(case_dir / "bundle_no_h5", full=False)

    assert not (case_dir / "bundle_no_h5" / "h5").exists()


@pytest.mark.parametrize(
    "name, expected",
    [
        ("shack_hartmann_autofocus_zernike_coefs", True),
        ("registration_shifts", True),
        ("moment0", False),
    ],
)
def test_is_csv_h5_output(name, expected) -> None:
    assert saving.is_csv_h5_output(name) is expected


def test_get_default_output_path_modes(case_dir: Path) -> None:
    source = case_dir / "movie.holo"
    source.write_bytes(b"")

    assert saving.get_default_output_path(source) == case_dir / "movie" / "movie_HD"
    assert saving.get_default_output_path(source, mode=1) == case_dir / "movie_HD_0"
    assert saving.get_default_output_path(source, mode=2) == (
        case_dir / "movie" / "movie_HD_0"
    )

    (case_dir / "movie" / "movie_HD_3").mkdir(parents=True)

    assert saving.get_default_output_path(source, mode=1).name == "movie_HD_4"

    with pytest.raises(ValueError):
        saving.get_default_output_path(source, mode=9)


def test_calculate_fps_fallbacks() -> None:
    assert saving.calculate_fps(None, 10, 0, {}) == 30.0
    assert saving.calculate_fps(1, 0, 0, {}) == 30.0
    assert saving.calculate_fps(1, 100, 0, {"sampling_freq": 1000}) == 10.0
    # Capped at maximum_fps.
    assert saving.calculate_fps(1000, 100, 0, {"sampling_freq": 1000}) == 65.0


# ---------------------------------------------------------------------------
# writer.image
# ---------------------------------------------------------------------------

def test_save_png_round_trip(case_dir: Path) -> None:
    data = np.arange(16, dtype=np.uint8).reshape(4, 4)

    path = case_dir / "nested" / "image.png"
    saving.save_png(path, data)

    assert path.is_file()

    with Image.open(path) as image:
        assert np.array(image).shape == (4, 4)


def test_prepare_png_image_handles_float_input() -> None:
    image = prepare_png_image(
        np.array([[0.0, 0.5], [1.0, 1.5]], dtype=np.float32)
    )

    assert image.mode == "L"


def test_save_image_png_validates_shape(case_dir: Path) -> None:
    with pytest.raises(ValueError):
        saving.save_image_png(case_dir / "bad.png", np.zeros((2, 2, 2), dtype=np.uint8))


def test_save_pngs_selects_keys_and_averages_videos(case_dir: Path) -> None:
    data_map = {
        "moment0": np.zeros((3, 4, 4), dtype=np.uint8),
        "spectrum_line": np.zeros((4, 4), dtype=np.uint8),
        "skipped": np.zeros((4, 4), dtype=np.uint8),
        "not_an_array": "text",
        "odd_shape": np.zeros((4,), dtype=np.uint8),
    }

    saving.save_pngs(case_dir, data_map, png_keys=["moment0", "spectrum_line", "not_an_array"])

    written = sorted(path.name for path in (case_dir / "png").iterdir())

    assert written == ["moment0.png", "spectrum_line.png"]


def test_save_video_average_png_writes_the_temporal_mean(case_dir: Path) -> None:
    """The average is taken over time before the image is quantized."""
    # Two frames whose temporal mean is a clean, non-flat ramp.
    first = np.array([[0, 40], [80, 120]], dtype=np.uint8)
    second = np.array([[100, 140], [180, 220]], dtype=np.uint8)
    video = np.stack([first, second])

    path = case_dir / "average.png"
    saving.save_video_average_png(path, video)

    with Image.open(path) as image:
        written = np.array(image)

    # The temporal mean of the two frames, in the average image's own 50..170
    # range: 0 -> 0 and 50 -> 255 after the shipped ``cast_png_data`` scaling.
    assert written.shape == (2, 2)
    assert written.dtype == np.uint8
    assert written[0, 0] == 0
    assert written[1, 1] == 255
    assert written.min() == 0 and written.max() == 255
    # Ordering of the original mean (50 < 90 < 130 < 170) is preserved.
    assert written[0, 1] < written[1, 0] < written[1, 1]

# ---------------------------------------------------------------------------
# writer.table
# ---------------------------------------------------------------------------

def test_save_txt_and_json_and_yaml_round_trip(case_dir: Path) -> None:
    txt = case_dir / "value.txt"
    saving.save_txt(txt, 42)

    assert txt.read_text(encoding="utf-8") == "42"

    payload = {"array": np.arange(3), "nested": {"value": np.float32(2.5)}}

    json_path = case_dir / "json" / "payload.json"
    saving.save_json(json_path, payload)

    assert json.loads(json_path.read_text(encoding="utf-8"))["array"] == [0, 1, 2]

    yaml_path = case_dir / "yaml" / "payload.yaml"
    saving.save_yaml(yaml_path, payload)

    assert yaml.safe_load(yaml_path.read_text(encoding="utf-8"))["array"] == [0, 1, 2]


def test_save_csv_supported_inputs(case_dir: Path) -> None:
    rows_path = case_dir / "rows.csv"
    saving.save_csv(rows_path, [[1, 2], [3, 4]])

    assert list(csv.reader(rows_path.read_text(encoding="utf-8").splitlines())) == [
        ["1", "2"],
        ["3", "4"],
    ]

    dicts_path = case_dir / "dicts.csv"
    saving.save_csv(dicts_path, [{"a": 1}, {"a": 2, "b": 3}])

    assert dicts_path.read_text(encoding="utf-8").splitlines()[0] == "a,b"

    array_path = case_dir / "array.csv"
    saving.save_csv(array_path, np.arange(3))

    # A 1-D array is written as a single column.
    assert array_path.read_text(encoding="utf-8") == "0\n1\n2\n"

    empty_path = case_dir / "empty.csv"
    saving.save_csv(empty_path, [])

    assert empty_path.read_text(encoding="utf-8") == ""


def test_save_csv_delegates_to_pandas_like_objects(case_dir: Path) -> None:
    class _Frame:
        def to_csv(self, path, index: bool) -> None:
            Path(path).write_text(f"index={index}", encoding="utf-8")

    path = case_dir / "frame.csv"
    saving.save_csv(path, _Frame())

    assert path.read_text(encoding="utf-8") == "index=False"


def test_save_csv_rejects_unsupported_values(case_dir: Path) -> None:
    with pytest.raises(TypeError):
        saving.save_csv(case_dir / "bad.csv", 3)

    with pytest.raises(ValueError):
        saving.save_csv(case_dir / "bad.csv", np.zeros((2, 2, 2)))


def test_save_csv_outputs_returns_the_h5_names(case_dir: Path) -> None:
    output = {
        "shack_hartmann_autofocus_zernike_coefs": np.arange(3),
        "registration_shifts": np.arange(4),
        "moment0": np.zeros((2, 2)),
        "nothing": None,
    }

    names = saving.save_csv_outputs(case_dir, output)

    assert names == ["shack_hartmann_autofocus_zernike_coefs", "registration_shifts"]
    assert sorted(path.name for path in (case_dir / "csv").iterdir()) == [
        "registration_shifts.csv",
        "shack_hartmann_autofocus_zernike_coefs.csv",
    ]


def test_save_csv_outputs_survives_a_failing_column(case_dir: Path) -> None:
    class _Broken:
        def to_csv(self, path, index: bool) -> None:
            raise OSError("no space left")

    names = saving.save_csv_outputs(case_dir, {"my_coefs": _Broken()})

    assert names == ["my_coefs"]


# ---------------------------------------------------------------------------
# writer.video
# ---------------------------------------------------------------------------

def test_write_video_rejects_invalid_shapes(case_dir: Path) -> None:
    with pytest.raises(ValueError, match="Invalid video shape"):
        saving.write_video(case_dir / "bad.avi", np.zeros((4, 4), dtype=np.uint8), 30)

    with pytest.raises(ValueError, match="zero frames"):
        saving.write_video(case_dir / "bad.avi", np.zeros((0, 4, 4), dtype=np.uint8), 30)

    assert not (case_dir / "bad.avi").exists()


def test_quality_from_q_v_uses_the_imageio_scale() -> None:
    assert saving.quality_from_q_v(1) == 10.0
    assert saving.quality_from_q_v(31) == 1.0
    assert saving.quality_from_q_v(100) == 1.0
    assert 1.0 < saving.quality_from_q_v(10) < 10.0


@requires_ffmpeg
def test_write_video_produces_a_readable_avi(case_dir: Path) -> None:
    """The shipped AVI codec keeps the historical full-range 4:2:2 output."""
    frames = (np.random.default_rng(0).random((4, 24, 32)) * 255).astype(np.uint8)

    path = case_dir / "avi" / "gray.avi"
    saved = saving.write_video(path, frames, 12.5, codec="mjpeg")

    assert saved == path
    assert path.is_file()

    meta = iio.immeta(path, plugin="FFMPEG")

    assert meta["fps"] == pytest.approx(12.5)
    assert tuple(meta["size"]) == (32, 24)
    assert meta["codec"] == "mjpeg"
    # ffmpeg rewrites the modern ``yuv422p`` request to its deprecated
    # full-range spelling; the trailing colour metadata is part of the report.
    assert meta["pix_fmt"].startswith("yuvj422p")
    assert len(list(iio.imiter(path, plugin="FFMPEG"))) == 4


@requires_ffmpeg
def test_mjpeg_keeps_the_full_luma_range(case_dir: Path) -> None:
    """Full range is a luma-mapping property: 1 and 255 must survive."""
    for level in (1, 128, 255):
        frame = np.full((2, 16, 16), level, dtype=np.uint8)

        path = case_dir / f"level_{level}.avi"
        saving.write_video(path, frame, 25, codec="mjpeg")

        decoded = iio.imread(path, plugin="FFMPEG", index=0)
        luma = 0.299 * decoded[..., 0] + 0.587 * decoded[..., 1] + 0.114 * decoded[..., 2]

        assert luma.min() >= level - 1, f"level {level} was clipped"
        assert luma.max() <= level + 1


@requires_ffmpeg
def test_write_video_produces_a_readable_mp4(case_dir: Path) -> None:
    """The new MP4/H.264 path is standard-range, 4:2:0 and widely decodable."""
    frames = (np.random.default_rng(1).random((4, 24, 24)) * 255).astype(np.uint8)

    path = case_dir / "mp4" / "gray.mp4"
    saved = saving.write_video(path, frames, 20.0, codec="libx264", crf=18, pixelformat="yuv420p")

    assert saved == path
    assert path.is_file()

    meta = iio.immeta(path, plugin="FFMPEG")

    assert meta["codec"] == "h264"
    assert meta["pix_fmt"].startswith("yuv420p")
    assert tuple(meta["size"]) == (24, 24)
    assert len(list(iio.imiter(path, plugin="FFMPEG"))) == 4


@requires_ffmpeg
def test_write_video_writes_every_frame_losslessly(case_dir: Path) -> None:
    """A frame-dropping writer once produced a valid but single-frame AVI."""
    frames = np.zeros((5, 16, 16), dtype=np.uint8)

    for index in range(5):
        frames[index, index * 2 : index * 2 + 2, :] = 255

    path = case_dir / "counted.avi"
    saving.write_video(path, frames, 20, codec="utvideo")

    decoded = list(iio.imiter(path, plugin="FFMPEG"))

    assert len(decoded) == len(frames)

    for original, round_tripped in zip(frames, decoded):
        # utvideo is lossless, so the RGB planes must come back untouched.
        assert np.array_equal(round_tripped[:, :, 0], original)


@requires_ffmpeg
def test_write_video_keeps_every_frame_of_an_rgb_video(case_dir: Path) -> None:
    frames = np.zeros((3, 24, 20, 3), dtype=np.uint8)
    frames[:, :, :, 1] = 200

    path = case_dir / "rgb.avi"
    saving.write_video(path, frames, 15, codec="utvideo")

    decoded = list(iio.imiter(path, plugin="FFMPEG"))

    assert len(decoded) == 3
    assert all(round_tripped.shape == (24, 20, 3) for round_tripped in decoded)


@requires_ffmpeg
def test_write_video_keeps_every_frame_of_an_h264_video(case_dir: Path) -> None:
    """H.264 is inter-frame coded, so a dropped frame is easy to miss."""
    frames = np.zeros((6, 16, 16), dtype=np.uint8)

    for index in range(6):
        frames[index, index * 2 : index * 2 + 2, :] = 255

    path = case_dir / "counted.mp4"
    saving.write_video(path, frames, 20, codec="libx264", crf=18)

    decoded = list(iio.imiter(path, plugin="FFMPEG"))

    assert len(decoded) == len(frames)
    assert all(round_tripped.shape == (16, 16, 3) for round_tripped in decoded)


@requires_ffmpeg
def test_write_video_pads_odd_dimensions_and_accepts_quality(case_dir: Path) -> None:
    frames = np.zeros((3, 25, 31, 3), dtype=np.uint8)

    path = case_dir / "odd.avi"
    saving.write_video(path, frames, 10, codec="mjpeg", quality=9)

    meta = iio.immeta(path, plugin="FFMPEG")

    # 25x31 is padded up to the next even size, not resized.
    assert tuple(meta["size"]) == (32, 26)
    # FFmpeg reports the colour metadata alongside the format name.
    assert meta["pix_fmt"].startswith("yuvj422p")
    assert len(list(iio.imiter(path, plugin="FFMPEG"))) == 3


@requires_ffmpeg
def test_write_video_pads_tiny_frames_so_no_frame_is_lost(case_dir: Path) -> None:
    """imageio's writer drops every frame but the first below 8x8."""
    frames = np.zeros((4, 4, 4), dtype=np.uint8)

    for index in range(4):
        frames[index, :, index] = 255

    path = case_dir / "tiny.mp4"
    saving.write_video(path, frames, 8, codec="libx264", pixelformat="yuv420p", crf=18)

    meta = iio.immeta(path, plugin="FFMPEG")

    assert tuple(meta["size"]) == (16, 16)
    assert len(list(iio.imiter(path, plugin="FFMPEG"))) == 4


@requires_ffmpeg
def test_write_video_legacy_save_video_alias_writes_the_same_file(case_dir: Path) -> None:
    frames = np.zeros((2, 4, 4), dtype=np.uint8)

    path = case_dir / "alias.avi"
    saving.save_video(path, frames, 30, ffmpeg="ignored", codec="mjpeg")

    assert iio.immeta(path, plugin="FFMPEG")["codec"] == "mjpeg"


@requires_ffmpeg
def test_write_video_rejects_an_unknown_encoder(case_dir: Path) -> None:
    path = case_dir / "broken.avi"
    # Seed a file so the failure path has something to clean up.
    path.write_bytes(b"stale")

    with pytest.raises(ValueError, match="Unknown FFmpeg encoder"):
        saving.write_video(
            path,
            np.zeros((2, 4, 4), dtype=np.uint8),
            30,
            codec="definitely-not-a-codec",
        )

    assert not path.exists()


def test_parse_encoder_names_ignores_the_header() -> None:
    from holodoppler.saving.writer.video import parse_encoder_names

    listing = (
        "Encoders:\n"
        " V..... = Video\n"
        " ------\n"
        " V....D libx264              libx264 H.264\n"
        " V....D mjpeg                MJPEG\n"
        " A....D aac                  AAC\n"
    )

    names = parse_encoder_names(listing)

    assert {"libx264", "mjpeg", "aac"} <= names
    assert "Encoders:" not in names
    assert "Video" not in names


@requires_ffmpeg
def test_write_videos_filters_and_reports_counts(case_dir: Path) -> None:
    # 16x16 rather than 4x4: imageio's FFMPEG writer drops frames on
    # extremely small frames (see the writer's module docstring).
    data_map = {
        "moment0": np.zeros((3, 16, 16), dtype=np.uint8),
        "not_a_video": np.zeros((4, 4), dtype=np.uint8),
        "not_an_array": "text",
        "other": np.zeros((3, 16, 16), dtype=np.uint8),
    }

    counts = saving.write_videos(case_dir, data_map, fps=8, video_keys=["moment0"])

    # Both shipped formats are written for the one selected video.
    assert counts == {"avi": 1, "mp4": 1}
    assert (case_dir / "avi" / "moment0.avi").is_file()
    assert (case_dir / "mp4" / "moment0.mp4").is_file()
    assert not (case_dir / "avi" / "other.avi").exists()
    assert not (case_dir / "mp4" / "other.mp4").exists()


@requires_ffmpeg
def test_write_videos_can_be_limited_to_one_format(case_dir: Path) -> None:
    counts = saving.write_videos(
        case_dir,
        {"moment0": np.zeros((2, 4, 4), dtype=np.uint8)},
        fps=5,
        formats=["avi"],
    )

    assert counts == {"avi": 1}
    assert (case_dir / "avi" / "moment0.avi").is_file()
    assert not (case_dir / "mp4").exists()


def test_write_videos_does_not_create_empty_format_directories(case_dir: Path) -> None:
    counts = saving.write_videos(case_dir, {"not_a_video": np.zeros((4, 4), dtype=np.uint8)}, fps=5)

    assert counts == {"avi": 0, "mp4": 0}
    assert not (case_dir / "avi").exists()
    assert not (case_dir / "mp4").exists()


def test_resolve_video_format_accepts_labels_and_codec_names() -> None:
    assert saving.resolve_video_format("avi").codec == "mjpeg"
    assert saving.resolve_video_format("MP4").codec == "libx264"
    assert saving.resolve_video_format("libx264").name == "mp4"

    with pytest.raises(ValueError, match="Unknown video format"):
        saving.resolve_video_format("wmv")


def test_default_video_formats_are_avi_mjpeg_and_mp4_h264() -> None:
    formats = saving.DEFAULT_VIDEO_FORMATS

    assert saving.DEFAULT_OUTPUT_FORMATS == ("avi", "mp4")
    assert formats["avi"].codec == "mjpeg"
    # The modern spelling of the historical full-range yuvj422p.
    assert formats["avi"].pixelformat == "yuv422p"
    assert formats["avi"].q_v == 1
    assert formats["mp4"].codec == "libx264"
    assert formats["mp4"].pixelformat == "yuv420p"
    assert formats["mp4"].crf is not None


@requires_ffmpeg
def test_save_videos_alias_matches_write_videos(case_dir: Path) -> None:
    saving.save_videos(
        case_dir,
        {"moment0": np.zeros((2, 4, 4), dtype=np.uint8)},
        fps=5,
    )

    assert (case_dir / "avi" / "moment0.avi").is_file()
    assert (case_dir / "mp4" / "moment0.mp4").is_file()


# ---------------------------------------------------------------------------
# writer.hdf5 / writer.metadata
# ---------------------------------------------------------------------------

def test_save_h5_writes_datasets_parameters_and_attributes(case_dir: Path) -> None:
    import h5py

    tally = saving.WriteTally()

    path = saving.save_h5(
        case_dir / "test_HD",
        {
            "moment0": np.zeros((1, 2, 2), dtype=np.float64),
            "skipped": np.ones((2, 2)),
            "not_an_array": "text",
        },
        parameters={"pipeline_name": "simple"},
        save_only_list=["moment0"],
        git_commit="deadbeef",
        tally=tally,
    )

    assert path.name == "test_HD_output.h5"
    assert tally.h5 == 1

    with h5py.File(path, "r") as h5:
        assert set(h5.keys()) == {"moment0", "HD_parameters", "HD_version", "git_commit"}
        assert h5["moment0"].dtype == np.float32
        assert h5.attrs["git_commit"] == "deadbeef"
        assert json.loads(h5["HD_parameters"][()])["pipeline_name"] == "simple"


def test_save_h5_no_longer_takes_the_dead_registration_lists(case_dir: Path) -> None:
    """``reg_list`` / ``coefs_list`` were accepted and never read."""
    import inspect

    parameters = inspect.signature(saving.save_h5).parameters

    assert "reg_list" not in parameters
    assert "coefs_list" not in parameters

    assert "reg_list" not in inspect.signature(saving.save_bundle).parameters
    assert "coefs_list" not in inspect.signature(saving.save_bundle).parameters
    assert "reg_list" not in inspect.signature(saving.save_outputs).parameters
    assert "coefs_list" not in inspect.signature(saving.save_outputs).parameters

    with pytest.raises(TypeError):
        saving.save_h5(case_dir / "x", {}, reg_list=[])  # type: ignore[call-arg]


def test_save_metadata_writes_parameters_and_version_files(case_dir: Path) -> None:
    class _Reader:
        extension = ".holo"
        header = {"width": 4}
        footer = {"note": "hi"}

    saving.save_metadata(case_dir, file_reader=_Reader(), parameters={"a": 1})

    json_dir = case_dir / "json"

    assert json.loads((json_dir / "parameters_holodoppler.json").read_text("utf-8")) == {
        "a": 1
    }
    assert json.loads((json_dir / "holovibes_header.json").read_text("utf-8")) == {"width": 4}
    assert json.loads((json_dir / "holovibes_footer.json").read_text("utf-8")) == {"note": "hi"}
    assert (case_dir / "version.txt").is_file()
    assert "Git commit" in (case_dir / "git_version.txt").read_text("utf-8")


def test_save_metadata_handles_cine_headers(case_dir: Path) -> None:
    class _Reader:
        extension = ".cine"
        header = {"frames": 10}

    saving.save_metadata(case_dir, file_reader=_Reader())

    assert (case_dir / "json" / "cine_metadata.json").is_file()


# ---------------------------------------------------------------------------
# bundle
# ---------------------------------------------------------------------------

def test_save_outputs_resolves_paths_and_rejects_conflicting_arguments(
    case_dir: Path, monkeypatch
) -> None:
    calls: dict[str, object] = {}

    def fake_save_bundle(**kwargs):
        calls.update(kwargs)

    monkeypatch.setattr(saving.bundle, "save_bundle", fake_save_bundle)

    class _Reader:
        file_path = case_dir / "movie.holo"

    output = {"moment0": np.zeros((1, 2, 2)), "band_0_1": np.zeros((1, 2, 2))}

    target = saving.save_outputs(_Reader(), output, parameters={"sampling_freq": 1000})

    assert target == case_dir / "movie" / "movie_HD"
    assert calls["target_dir"] == target
    assert "moment0" in calls["save_h5_list"]
    assert "band_0_1" in calls["save_h5_list"]

    relative = saving.save_outputs(_Reader(), output, custom_relative_path="preview")

    assert relative == case_dir / "movie" / "movie_HD" / "preview"

    with pytest.raises(ValueError):
        saving.save_outputs(
            _Reader(),
            output,
            custom_path=case_dir / "absolute",
            custom_relative_path="preview",
        )

    with pytest.raises(ValueError):
        saving.save_outputs(_Reader(), output, custom_path="relative/dir")

    with pytest.raises(ValueError):
        saving.save_outputs(
            _Reader(), output, custom_relative_path=case_dir / "absolute"
        )


@requires_ffmpeg
def test_save_bundle_writes_the_expected_directory_tree(case_dir: Path, capsys) -> None:
    class _Reader:
        extension = ".holo"
        header = {"width": 4}
        footer = None
        file_path = case_dir / "movie.holo"

    target = case_dir / "bundle_HD"

    tally = saving.save_bundle(
        target_dir=target,
        output={
            "moment0": np.zeros((2, 4, 4)),
            "moment0ff": np.zeros((2, 4, 4)),
        },
        parameters={"sampling_freq": 1000},
        file_reader=_Reader(),
        fps=10,
        save_h5_list=["moment0", "moment0ff"],
    )

    produced = {
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_file()
    }

    assert produced == {
        "avi/moment0.avi",
        "avi/moment0ff.avi",
        "mp4/moment0.mp4",
        "mp4/moment0ff.mp4",
        "git_version.txt",
        "h5/bundle_HD_output.h5",
        "json/holovibes_header.json",
        "json/parameters_holodoppler.json",
        "png/moment0.png",
        "png/moment0ff.png",
        "version.txt",
    }

    # Counts are returned and match what landed on disk.
    assert tally.videos == {"avi": 2, "mp4": 2}
    assert tally.pngs == 2
    assert tally.json == 2
    assert tally.h5 == 1
    assert tally.failures == 0
    # The two version text files are written outside the tally's categories.
    assert tally.total_files == len(produced) - 2

    # And the run prints exactly one summary block, nothing per file.
    stdout = capsys.readouterr().out
    assert "Saving completed in" in stdout
    assert stdout.count("Saving completed") == 1
    assert "Saving output bundle to" not in stdout
    assert "Saved video" not in stdout
    assert "Saved PNG" not in stdout
    assert "Saving H5" not in stdout


def test_write_tally_describe_shows_only_what_was_written() -> None:
    tally = saving.WriteTally()

    assert tally.describe() == "no files written"
    assert tally.summary(1.234).startswith("Saving completed in 1.2 seconds")

    tally.record_video("avi", 6)
    tally.record_video("mp4", 6)
    tally.record_png(7)
    tally.record_csv(1)
    tally.record_h5()

    described = tally.describe()

    assert "videos[avi]: 6" in described
    assert "videos[mp4]: 6" in described
    assert "pngs: 7" in described
    assert "csv: 1" in described
    assert "h5: 1" in described
    # Zero-count categories are omitted rather than advertised.
    assert "yaml" not in described

    tally.record_failure(2)

    assert "failures: 2" in tally.describe()


def test_saving_writers_do_not_print(case_dir: Path, capsys) -> None:
    """Per-file chatter is gone; only ``save_bundle`` reports, once."""
    saving.save_csv(case_dir / "a.csv", [[1, 2]])
    saving.save_png(case_dir / "a.png", np.zeros((2, 2), dtype=np.uint8))
    saving.save_pngs(case_dir, {"bad": np.zeros((4,), dtype=np.uint8)})
    saving.save_json(case_dir / "a.json", {"a": 1})
    saving.save_csv_outputs(case_dir, {"my_coefs": np.arange(2)})

    assert capsys.readouterr().out == ""
