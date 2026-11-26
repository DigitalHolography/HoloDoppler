import json
import struct
from types import SimpleNamespace

import numpy as np
import pytest

from holodoppler.file_reader import FileReader
from holodoppler.file_reader import file_reader as legacy
from holodoppler.file_reader.cine import CineFileReader
from holodoppler.file_reader.holo import HoloFileReader


def test_imports_and_dispatch():
    assert legacy.FileReader is FileReader
    assert legacy.HoloFileReader is HoloFileReader
    assert legacy.CineFileReader is CineFileReader
    assert isinstance(FileReader('sample.HOLO'), HoloFileReader)
    assert isinstance(FileReader('sample.cine'), CineFileReader)
    with pytest.raises(ValueError, match='Unsupported file extension'):
        FileReader('sample.invalid')


def test_holo_frames_and_footer(tmp_path):
    path = tmp_path / 'frames.holo'
    header = bytearray(64)
    header[:4] = b'HOLO'
    header[4:6] = (1).to_bytes(2, 'little')
    header[6:8] = (8).to_bytes(2, 'little')
    header[8:12] = (2).to_bytes(4, 'little')
    header[12:16] = (2).to_bytes(4, 'little')
    header[16:20] = (3).to_bytes(4, 'little')
    pixels = np.arange(12, dtype=np.uint8).reshape(3, 2, 2)
    path.write_bytes(header + pixels.tobytes() + json.dumps({'fps': 10}).encode())
    with FileReader(path) as reader:
        np.testing.assert_array_equal(reader.read_frames(1), pixels[1])
        np.testing.assert_array_equal(reader.read_frames(0, 2, 2), pixels[[0, 2]])
        np.testing.assert_array_equal(reader.read_selected_frames([2, 0]), pixels[[2, 0]])
        assert reader.read_selected_frames([]).shape == (0, 2, 2)
        assert reader.footer == {'fps': 10}
        with pytest.raises(IndexError):
            reader.read_frames(2, 2)
        with pytest.raises(ValueError):
            reader.read_frames(batch_size=0)


def test_cine_frames_and_errors(tmp_path, monkeypatch):
    path = tmp_path / 'frames.cine'
    # Two offsets, followed by annotations and packed 12-bit frame payloads.
    path.write_bytes(struct.pack('<qq', 16, 23) + struct.pack('<I', 4) + bytes([0x12, 0x34, 0x56]) + struct.pack('<I', 4) + bytes([0x78, 0x9a, 0xbc]))
    metadata = SimpleNamespace(biHeight=1, biWidth=2, biCompression=1024,
                               biSizeImage=3, TotalImageCount=2,
                               OffImageOffsets=0, FirstImageNo=-1)
    monkeypatch.setattr('holodoppler.file_reader.cine.read_metadata', lambda _: metadata)
    reader = FileReader(path)
    np.testing.assert_array_equal(reader.read_frames(0), [[0x123, 0x456]])
    np.testing.assert_array_equal(reader.read_selected_frames([1, 0]), [[[0x789, 0xabc]], [[0x123, 0x456]]])
    assert reader.read_selected_frames([]).shape == (0, 1, 2)
    with pytest.raises(IndexError):
        reader.read_selected_frames([-1])
    with pytest.raises(ValueError):
        reader.read_frames(skip_every=0)

