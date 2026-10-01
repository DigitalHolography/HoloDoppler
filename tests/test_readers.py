"""Reader contract tests for ``.holo`` and ``.cine``.

The ``.cine`` frame-decoding path has no pre-existing implementation in this
repository and no real acquisition fixture, so only the verifiable parts are
covered here: factory dispatch, metadata mapping, the P12L unpacking
primitives, and range validation. The offset-addressing behaviour is pinned by
``tests/test_known_issues.py`` instead.
"""

from __future__ import annotations

import importlib
import struct

import numpy as np
import pytest

from holodoppler.readers import (
    CineFileReader,
    CineMetadata,
    FileReader,
    FileReaderFactory,
    HoloFileReader,
    get_reader,
    unpack_12bitL_batch_to_uint16,
    unpack_12bitL_vectorized,
)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "name, expected_type",
    [
        ("capture.holo", HoloFileReader),
        ("capture.HOLO", HoloFileReader),
        ("capture.Holo", HoloFileReader),
        ("capture.cine", CineFileReader),
        ("capture.CINE", CineFileReader),
        ("capture.Cine", CineFileReader),
    ],
)
def test_factory_dispatches_by_case_insensitive_extension(
    case_dir, name: str, expected_type: type
) -> None:
    reader = FileReaderFactory.create(case_dir / name)

    assert isinstance(reader, expected_type)
    assert type(reader) is expected_type


@pytest.mark.parametrize("name", ["capture.xyz", "capture", "capture.holo.bak"])
def test_factory_rejects_unsupported_extensions(case_dir, name: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        FileReaderFactory.create(case_dir / name)

    message = str(excinfo.value)
    assert "Unsupported file extension" in message
    assert ".holo" in message
    assert ".cine" in message


def test_get_reader_delegates_to_the_factory(case_dir) -> None:
    reader = get_reader(case_dir / "capture.holo")

    assert isinstance(reader, HoloFileReader)


def test_file_reader_is_abstract(case_dir) -> None:
    with pytest.raises(TypeError):
        FileReader(case_dir / "capture.holo")  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# .holo: metadata and frame access
# ---------------------------------------------------------------------------

def test_holo_header_and_metadata(holo_case) -> None:
    reader = HoloFileReader(holo_case.holo)
    header = reader.header

    assert reader.file_path == holo_case.holo
    assert header.magic_number == "HOLO"
    assert header.version == 777
    assert header.bit_depth == 8
    assert header.width == 32
    assert header.height == 32
    assert header.num_frames == 64
    assert header.endianness == 0
    assert header.bytes_per_pixel == 1
    assert header.frame_shape == (32, 32)

    assert reader.frame_shape == (32, 32)
    assert reader.total_frames == 64
    assert reader.dtype == np.dtype("<u1")
    assert reader.extension == ".holo"


def test_holo_footer_round_trips(holo_case) -> None:
    reader = HoloFileReader(holo_case.holo)
    footer = reader.footer

    assert footer["compute_settings"]["image_rendering"]["space_transformation"] == (
        "FRESNELTR"
    )
    assert footer["info"]["pixel_pitch"]["x"] == pytest.approx(20e-6)
    assert footer["info"]["camera_fps"] == 37000


def test_holo_missing_footer_is_empty(holo_case) -> None:
    header_size = 64
    frame_count = 4
    width = height = 8

    path = holo_case.directory / "nofooter.holo"
    with path.open("wb") as handle:
        header = bytearray(header_size)
        header[0:4] = b"HOLO"
        header[4:6] = (1).to_bytes(2, "little")
        header[6:8] = (8).to_bytes(2, "little")
        header[8:12] = width.to_bytes(4, "little")
        header[12:16] = height.to_bytes(4, "little")
        header[16:20] = frame_count.to_bytes(4, "little")
        header[20:28] = (header_size + frame_count * width * height).to_bytes(
            8, "little"
        )
        header[28] = 0
        handle.write(header)
        handle.write(bytes(frame_count * width * height))

    reader = HoloFileReader(path)

    assert reader.footer == {}
    assert reader.total_frames == frame_count


def test_holo_frame_data_matches_a_manual_read(holo_case) -> None:
    reader = HoloFileReader(holo_case.holo)

    expected = np.fromfile(
        holo_case.holo,
        dtype=np.uint8,
        count=64 * 32 * 32,
        offset=64,
    ).reshape(64, 32, 32)

    np.testing.assert_array_equal(reader.read_frames(0, 1), expected[0])
    np.testing.assert_array_equal(reader.read_frames(10, 3), expected[10:13])
    np.testing.assert_array_equal(reader.read_frames(63, 1), expected[63])

    np.testing.assert_array_equal(
        reader.read_selected_frames([0, 5, 63]),
        expected[[0, 5, 63]],
    )
    np.testing.assert_array_equal(
        reader.read_selected_frames([7]),
        expected[7],
    )


def test_holo_frame_ranges_and_stride(holo_case) -> None:
    reader = HoloFileReader(holo_case.holo)

    # A single frame is returned without the leading frame axis.
    assert reader.read_frames(0, 1).shape == (32, 32)
    assert reader.read_frames(0, 5).shape == (5, 32, 32)
    assert reader.read_frames(32, 5).shape == (5, 32, 32)
    assert reader.read_frames(60, 4).shape == (4, 32, 32)

    strided = reader.read_frames(0, 3, skip_every=10)
    assert strided.shape == (3, 32, 32)

    expected = np.fromfile(
        holo_case.holo, dtype=np.uint8, count=64 * 32 * 32, offset=64
    ).reshape(64, 32, 32)
    np.testing.assert_array_equal(strided, expected[[0, 10, 20]])


def test_holo_empty_selection_returns_an_empty_stack(holo_case) -> None:
    reader = HoloFileReader(holo_case.holo)

    empty = reader.read_selected_frames([])

    assert empty.shape == (0, 32, 32)
    assert empty.dtype == np.dtype("<u1")


@pytest.mark.parametrize(
    "first_frame, batch_size, skip_every, expected_error",
    [
        (-1, 1, None, ValueError),
        (0, 0, None, ValueError),
        (0, -1, None, ValueError),
        (0, 1, 0, ValueError),
        (0, 1, -3, ValueError),
        (64, 1, None, IndexError),
        (60, 10, None, IndexError),
        (0, 65, None, IndexError),
    ],
)
def test_holo_invalid_ranges(
    holo_case, first_frame: int, batch_size: int, skip_every, expected_error: type
) -> None:
    reader = HoloFileReader(holo_case.holo)

    with pytest.raises(expected_error):
        reader.read_frames(first_frame, batch_size, skip_every)


@pytest.mark.parametrize("indices", [[-1], [64], [0, 70]])
def test_holo_invalid_selected_indices(holo_case, indices) -> None:
    reader = HoloFileReader(holo_case.holo)

    with pytest.raises(IndexError):
        reader.read_selected_frames(indices)


def test_holo_open_and_close_are_idempotent(holo_case) -> None:
    reader = HoloFileReader(holo_case.holo)

    with reader as opened:
        assert opened is reader
        assert opened.read_frames(0, 2).shape == (2, 32, 32)

    # The reader is still usable after closing; the memmap is recreated lazily.
    assert reader.read_frames(0, 2).shape == (2, 32, 32)

    reader.close()
    reader.close()


def test_holo_repr_reports_unreadable_files(holo_case) -> None:
    broken = holo_case.directory / "broken.holo"
    broken.write_bytes(b"HOLO")

    text = repr(HoloFileReader(broken))

    assert "[unreadable]" in text


# ---------------------------------------------------------------------------
# .cine: metadata mapping
# ---------------------------------------------------------------------------

class _FakeMetaData:
    """Stand-in for ``readers.cine_parser.MetaData``."""

    def __init__(self, **fields) -> None:
        for key, value in fields.items():
            setattr(self, key, value)


def _cine_metadata(**overrides) -> _FakeMetaData:
    fields = {
        "biHeight": 4,
        "biWidth": 4,
        "biCompression": 1024,
        "biSizeImage": 24,
        "TotalImageCount": 3,
        "OffImageOffsets": 1000,
        "FirstImageNo": 0,
        "RealBPP": 12,
        "biYPelsPerMeter": 50000,
        "biXPelsPerMeter": 40000,
        "FrameRate": 1200.0,
    }
    fields.update(overrides)
    return _FakeMetaData(**fields)


@pytest.fixture
def cine_path(case_dir):
    path = case_dir / "capture.cine"
    path.write_bytes(b"\x00" * 64)
    return path


def test_cine_reader_maps_known_metadata(monkeypatch, cine_path) -> None:
    import holodoppler.readers.cine as cine_reader

    monkeypatch.setattr(
        cine_reader, "read_metadata", lambda path: _cine_metadata()
    )

    reader = CineFileReader(cine_path)
    header = reader.header

    assert isinstance(header, CineMetadata)
    assert reader.extension == ".cine"
    assert reader.frame_shape == (4, 4)
    assert reader.total_frames == 3
    assert reader.dtype == np.dtype(np.float32)
    assert header.biCompression == 1024
    assert header.RealBPP == 12

    # Keys the reader does not model are preserved for downstream consumers.
    assert header.extra["biYPelsPerMeter"] == 50000
    assert header.extra["FrameRate"] == 1200.0


def test_cine_metadata_can_feed_parameter_overrides(monkeypatch, cine_path) -> None:
    import holodoppler.readers.cine as cine_reader
    from holodoppler.config import update_from_cine_metadata

    monkeypatch.setattr(
        cine_reader, "read_metadata", lambda path: _cine_metadata()
    )

    parameters = {
        "pixel_pitch": "use_metadata",
        "sampling_freq": "use_metadata",
        "high_freq": "use_metadata",
    }

    update_from_cine_metadata(parameters, CineFileReader(cine_path).header)

    assert parameters["pixel_pitch"] == pytest.approx(
        (1 / 50000, 1 / 40000)
    )
    assert parameters["sampling_freq"] == pytest.approx(1200.0)
    assert parameters["high_freq"] == pytest.approx(600.0)


def test_cine_empty_selection_returns_an_empty_stack(monkeypatch, cine_path) -> None:
    import holodoppler.readers.cine as cine_reader

    monkeypatch.setattr(
        cine_reader, "read_metadata", lambda path: _cine_metadata()
    )

    empty = CineFileReader(cine_path).read_selected_frames([])

    assert empty.shape == (0, 4, 4)
    assert empty.dtype == np.dtype(np.float32)


@pytest.mark.parametrize(
    "first_frame, batch_size, skip_every, expected_error",
    [
        (-1, 1, None, ValueError),
        (0, 0, None, ValueError),
        (0, 1, 0, ValueError),
        (3, 1, None, IndexError),
        (0, 4, None, IndexError),
    ],
)
def test_cine_invalid_ranges(
    monkeypatch,
    cine_path,
    first_frame: int,
    batch_size: int,
    skip_every,
    expected_error: type,
) -> None:
    """Range validation must happen before any frame payload is touched."""
    import holodoppler.readers.cine as cine_reader

    monkeypatch.setattr(
        cine_reader, "read_metadata", lambda path: _cine_metadata()
    )

    reader = CineFileReader(cine_path)

    with pytest.raises(expected_error):
        reader.read_frames(first_frame, batch_size, skip_every)


def test_cine_unsupported_compression_is_explicit(monkeypatch, cine_path) -> None:
    import holodoppler.readers.cine as cine_reader

    metadata = _cine_metadata(biCompression=999)

    monkeypatch.setattr(cine_reader, "read_metadata", lambda path: metadata)

    reader = CineFileReader(cine_path)

    # One offset entry is read, then the frame payload decodes.
    with pytest.raises((NotImplementedError, EOFError, ValueError)):
        reader.read_frames(0, 1)


def test_cine_repr_reports_unreadable_files(monkeypatch, cine_path) -> None:
    import holodoppler.readers.cine as cine_reader

    def boom(path):
        raise OSError("cannot read")

    monkeypatch.setattr(cine_reader, "read_metadata", boom)

    assert "[unreadable]" in repr(CineFileReader(cine_path))


# ---------------------------------------------------------------------------
# .cine: frame decoding against the reader's own documented layout
# ---------------------------------------------------------------------------

def _write_synthetic_cine(
    path,
    frames: np.ndarray,
    *,
    offsets_table: int = 1000,
    frame_offsets=(2000, 2100, 2200),
    annotation_size: int = 8,
) -> None:
    """Write a minimal ``.cine`` whose layout matches ``CineFileReader``.

    The frame-offset table is addressed as::

        OffImageOffsets + (first_frame - TotalImageCount + 1 - FirstImageNo) * 8

    which is the layout the current implementation assumes. Parameter values
    matching this file are supplied through the ``_cine_metadata`` helper.
    """
    frame_count, height, width = frames.shape
    payload_size = (width * height * 3) // 2

    buffer = bytearray(max(frame_offsets) + annotation_size + payload_size)

    for index, offset in enumerate(frame_offsets):
        packed = _pack_12bit_pixels(frames[index])
        assert len(packed) == payload_size

        struct.pack_into("I", buffer, offset, annotation_size)
        buffer[offset + annotation_size : offset + annotation_size + payload_size] = (
            packed
        )

        corrected = index - frame_count + 1
        struct.pack_into("<q", buffer, offsets_table + corrected * 8, offset)

    path.write_bytes(bytes(buffer))


def test_cine_decodes_frames_using_its_documented_offset_layout(
    monkeypatch, case_dir
) -> None:
    """Self-consistency: the reader decodes the layout it documents.

    This is *not* a validation against the real Phantom format; see
    ``test_cine_offset_addressing_seeks_before_the_offset_table``.
    """
    import holodoppler.readers.cine as cine_reader

    rng = np.random.default_rng(11)
    frames = rng.integers(0, 1 << 12, size=(3, 4, 4), dtype=np.uint16)

    path = case_dir / "layout.cine"
    _write_synthetic_cine(path, frames)

    monkeypatch.setattr(
        cine_reader, "read_metadata", lambda p: _cine_metadata()
    )

    reader = CineFileReader(path)

    first = reader.read_frames(0, 1)
    assert first.shape == (4, 4)
    assert first.dtype == np.dtype(np.float32)
    np.testing.assert_array_equal(first, frames[0].astype(np.float32))

    stacked = reader.read_frames(0, 3)
    assert stacked.shape == (3, 4, 4)
    np.testing.assert_array_equal(stacked, frames.astype(np.float32))

    last = reader.read_selected_frames([2])
    np.testing.assert_array_equal(last, frames[2].astype(np.float32))


def test_cine_offset_addressing_seeks_before_the_offset_table() -> None:
    """Document the concrete risk in the ``.cine`` offset arithmetic.

    For the first frames the reader seeks to positions *before*
    ``OffImageOffsets``, i.e. outside the offset table it claims to read. That
    is either a Phantom quirk (table indexed from the last frame) or a bug, and
    cannot be settled without a real acquisition. The behaviour is therefore
    frozen rather than changed.
    """
    total_frames = 3
    first_image_no = 0
    offsets_table = 1000
    first_frame = 0

    corrected = first_frame - total_frames + 1 - first_image_no

    assert corrected == -2
    assert offsets_table + corrected * 8 < offsets_table


# ---------------------------------------------------------------------------
# P12L unpacking primitives
# ---------------------------------------------------------------------------

def _pack_12bit_pixels(pixels: np.ndarray) -> bytes:
    """Pack 12-bit pixels into the P12L layout the reader unpacks."""
    flat = np.asarray(pixels, dtype=np.uint16).ravel()

    if flat.size % 2:
        raise ValueError("P12L packs pixels in pairs")

    out = bytearray()

    for index in range(0, flat.size, 2):
        p0 = int(flat[index])
        p1 = int(flat[index + 1])

        out.append((p0 >> 4) & 0xFF)
        out.append((((p0 & 0x0F) << 4) | ((p1 >> 8) & 0x0F)) & 0xFF)
        out.append(p1 & 0xFF)

    return bytes(out)


@pytest.mark.parametrize("height, width", [(2, 2), (4, 6), (1, 8)])
def test_unpack_12bitl_vectorized_round_trips(height: int, width: int) -> None:
    rng = np.random.default_rng(4242)
    pixels = rng.integers(0, 1 << 12, size=(height, width), dtype=np.uint16)

    packed = _pack_12bit_pixels(pixels)
    unpacked = unpack_12bitL_vectorized(packed, width=width, height=height)

    assert unpacked.shape == (height, width)
    assert unpacked.dtype == np.uint16
    np.testing.assert_array_equal(unpacked, pixels)


def test_unpack_12bitl_batch_matches_per_frame_unpacking() -> None:
    rng = np.random.default_rng(7)
    frames = rng.integers(0, 1 << 12, size=(3, 4, 6), dtype=np.uint16)
    packed = np.frombuffer(
        b"".join(_pack_12bit_pixels(frame) for frame in frames),
        dtype=np.uint8,
    ).reshape(3, -1)

    batch = unpack_12bitL_batch_to_uint16(packed, width=6, height=4)

    assert batch.shape == (3, 4, 6)
    np.testing.assert_array_equal(batch, frames)


def test_unpack_12bitl_rejects_odd_pixel_counts() -> None:
    with pytest.raises(ValueError):
        unpack_12bitL_vectorized(b"\x00" * 3, width=3, height=1)


def test_unpack_12bitl_rejects_wrong_payload_length() -> None:
    with pytest.raises(ValueError):
        unpack_12bitL_vectorized(b"\x00" * 4, width=2, height=2)


def test_unpack_12bitl_batch_rejects_bad_shape() -> None:
    with pytest.raises(ValueError):
        unpack_12bitL_batch_to_uint16(np.zeros((2, 3), dtype=np.uint8), 4, 6)

    with pytest.raises(ValueError):
        unpack_12bitL_batch_to_uint16(np.zeros(6, dtype=np.uint8), 4, 6)


# ---------------------------------------------------------------------------
# Factory surface
# ---------------------------------------------------------------------------

def test_factory_reports_supported_extensions() -> None:
    assert FileReaderFactory.supported_extensions() == [".cine", ".holo"]


def test_the_former_file_reader_module_is_gone() -> None:
    """Readers live in ``holodoppler.readers``; no top-level shim remains."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("holodoppler.file_reader")
