from __future__ import annotations
"""
tests/test_saving.py

Tests for holodoppler.saving:
    - find_ffmpeg()
    - save_video()
    - save_videos()

Run with:
    pytest tests/test_saving.py -v
"""

"""
tests/test_saving_fast.py

Fast tests for holodoppler.saving.save_video and save_videos.
Tiny 8x8 frames, 2-3 frames per video, no readback.

Run:
    uv run pytest tests/test_saving_fast.py -v
"""


import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from holodoppler import saving
from holodoppler.saving import (
    find_ffmpeg,
    save_video,
    save_videos,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_video_dir(tmp_path: Path) -> Path:
    """A throwaway directory for video outputs."""
    d = tmp_path / "videos"
    d.mkdir()
    return d


@pytest.fixture
def small_video() -> np.ndarray:
    """
    A tiny 3-channel video: 4 frames of 32x32 random uint8 RGB data.
    Even dimensions, so no padding is triggered.
    """
    rng = np.random.default_rng(0)
    return rng.integers(0, 256, size=(4, 32, 32, 3), dtype=np.uint8)


@pytest.fixture
def odd_video() -> np.ndarray:
    """A tiny video with odd width/height (33x31), to exercise padding."""
    rng = np.random.default_rng(1)
    return rng.integers(0, 256, size=(3, 31, 33, 3), dtype=np.uint8)


@pytest.fixture
def grayscale_video() -> np.ndarray:
    """Single-channel video."""
    rng = np.random.default_rng(2)
    return rng.integers(0, 256, size=(3, 32, 32), dtype=np.uint8)


@pytest.fixture
def rgba_video() -> np.ndarray:
    """4-channel video; the saver should drop alpha."""
    rng = np.random.default_rng(3)
    return rng.integers(0, 256, size=(3, 32, 32, 4), dtype=np.uint8)


@pytest.fixture
def data_map(small_video: np.ndarray, grayscale_video: np.ndarray) -> dict[str, Any]:
    """
    A dict resembling what holodoppler passes to save_videos:
    a mix of videos, still images, scalars, and None.
    """
    return {
        "video_a": small_video,
        "video_b": grayscale_video,
        "still_image": small_video[0],       # 2D → not a video
        "scalar": 42,                        # not an ndarray
        "empty": None,                       # skipped
        "a_string": "not a video",           # skipped
    }


# ---------------------------------------------------------------------------
# find_ffmpeg
# ---------------------------------------------------------------------------


class TestFindFfmpeg:
    def test_returns_existing_executable(self):
        path = find_ffmpeg()
        assert isinstance(path, str)
        assert os.path.isfile(path)

    def test_executable_is_runnable(self):
        path = find_ffmpeg()
        # -version exits 0 on every FFmpeg build.
        result = subprocess.run(
            [path, "-version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "ffmpeg" in (result.stdout + result.stderr).lower()

    def test_is_stable_across_calls(self):
        # Calling twice must not download twice / return different paths.
        assert find_ffmpeg() == find_ffmpeg()

    def test_path_is_absolute(self):
        assert os.path.isabs(find_ffmpeg())



# ---------------------------------------------------------------------------
# Fixtures — deliberately tiny
# ---------------------------------------------------------------------------


@pytest.fixture
def tiny_rgb() -> np.ndarray:
    """3 frames, 8x8, 3 channels. Smallest thing FFmpeg will accept."""
    rng = np.random.default_rng(0)
    return rng.integers(0, 256, size=(3, 8, 8, 3), dtype=np.uint8)


@pytest.fixture
def tiny_gray() -> np.ndarray:
    """2 frames, 8x8, single channel."""
    rng = np.random.default_rng(1)
    return rng.integers(0, 256, size=(2, 8, 8), dtype=np.uint8)


@pytest.fixture
def tiny_odd() -> np.ndarray:
    """7x9 → forces make_even_dimensions to pad."""
    rng = np.random.default_rng(2)
    return rng.integers(0, 256, size=(2, 7, 9, 3), dtype=np.uint8)


@pytest.fixture
def out_dir(tmp_path: Path) -> Path:
    d = tmp_path / "v"
    d.mkdir()
    return d


@pytest.fixture
def ffmpeg_bin() -> str:
    """Resolved once per test session via imageio_ffmpeg."""
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


# ---------------------------------------------------------------------------
# save_video — one call, one file
# ---------------------------------------------------------------------------


def test_save_video_mjpeg(out_dir: Path, tiny_rgb: np.ndarray, ffmpeg_bin: str):
    out = out_dir / "a.mp4"
    save_video(out, tiny_rgb, fps=5, ffmpeg=ffmpeg_bin, codec="mjpeg")
    assert out.is_file() and out.stat().st_size > 0


def test_save_video_utvideo(out_dir: Path, tiny_rgb: np.ndarray, ffmpeg_bin: str):
    out = out_dir / "a.avi"
    save_video(out, tiny_rgb, fps=5, ffmpeg=ffmpeg_bin, codec="utvideo")
    assert out.is_file() and out.stat().st_size > 0


def test_save_video_grayscale(out_dir: Path, tiny_gray: np.ndarray, ffmpeg_bin: str):
    out = out_dir / "g.mp4"
    save_video(out, tiny_gray, fps=5, ffmpeg=ffmpeg_bin)
    assert out.is_file() and out.stat().st_size > 0


def test_save_video_odd_dimensions(out_dir: Path, tiny_odd: np.ndarray, ffmpeg_bin: str):
    out = out_dir / "o.mp4"
    save_video(out, tiny_odd, fps=5, ffmpeg=ffmpeg_bin)
    assert out.is_file() and out.stat().st_size > 0


def test_save_video_creates_parent_dirs(out_dir: Path, tiny_rgb: np.ndarray, ffmpeg_bin: str):
    out = out_dir / "deep" / "nested" / "a.mp4"
    save_video(out, tiny_rgb, fps=5, ffmpeg=ffmpeg_bin)
    assert out.is_file()


def test_save_video_overwrites(out_dir: Path, tiny_rgb: np.ndarray, ffmpeg_bin: str):
    out = out_dir / "a.mp4"
    out.write_bytes(b"junk")
    save_video(out, tiny_rgb, fps=5, ffmpeg=ffmpeg_bin)
    assert out.read_bytes()[:4] != b"junk"


def test_save_video_accepts_str_path(out_dir: Path, tiny_rgb: np.ndarray, ffmpeg_bin: str):
    out = out_dir / "s.mp4"
    save_video(str(out), tiny_rgb, fps=5, ffmpeg=ffmpeg_bin)
    assert out.is_file()


def test_save_video_float_fps(out_dir: Path, tiny_rgb: np.ndarray, ffmpeg_bin: str):
    out = out_dir / "f.mp4"
    save_video(out, tiny_rgb, fps=29.97, ffmpeg=ffmpeg_bin)
    assert out.is_file()


def test_save_video_uses_given_ffmpeg(out_dir, tiny_rgb, ffmpeg_bin, monkeypatch):
    """If ffmpeg= is passed, find_ffmpeg() must not be called."""
    def boom():
        raise AssertionError("find_ffmpeg should not be called")
    monkeypatch.setattr(saving, "find_ffmpeg", boom)

    out = out_dir / "x.mp4"
    save_video(out, tiny_rgb, fps=5, ffmpeg=ffmpeg_bin)
    assert out.is_file()


def test_save_video_looks_up_ffmpeg_when_omitted(out_dir, tiny_rgb, monkeypatch):
    calls = {"n": 0}
    real = saving.find_ffmpeg

    def counted():
        calls["n"] += 1
        return real()

    monkeypatch.setattr(saving, "find_ffmpeg", counted)
    save_video(out_dir / "y.mp4", tiny_rgb, fps=5)
    assert calls["n"] == 1


# ---------------------------------------------------------------------------
# save_videos — batching over a data_map
# ---------------------------------------------------------------------------


@pytest.fixture
def tiny_map(tiny_rgb: np.ndarray, tiny_gray: np.ndarray) -> dict[str, Any]:
    return {
        "v1": tiny_rgb,
        "v2": tiny_gray,
        "img": tiny_rgb[0],        # 2D → skipped
        "n": None,                 # skipped
        "s": "str",                # skipped
        "i": 5,                    # skipped
    }


def test_save_videos_writes_all_avi(out_dir: Path, tiny_map, monkeypatch, ffmpeg_bin):
    monkeypatch.setattr(saving, "find_ffmpeg", lambda: ffmpeg_bin)
    save_videos(out_dir, tiny_map, fps=5)

    avi = out_dir / "avi"
    assert avi.is_dir()
    assert {p.name for p in avi.iterdir()} == {"v1.avi", "v2.avi"}


def test_save_videos_files_nonempty(out_dir: Path, tiny_map, monkeypatch, ffmpeg_bin):
    monkeypatch.setattr(saving, "find_ffmpeg", lambda: ffmpeg_bin)
    save_videos(out_dir, tiny_map, fps=5)

    for name in ("v1.avi", "v2.avi"):
        assert (out_dir / "avi" / name).stat().st_size > 0


def test_save_videos_filter_video_keys(out_dir: Path, tiny_map, monkeypatch, ffmpeg_bin):
    monkeypatch.setattr(saving, "find_ffmpeg", lambda: ffmpeg_bin)
    save_videos(out_dir, tiny_map, fps=5, video_keys=["v2"])

    assert {p.name for p in (out_dir / "avi").iterdir()} == {"v2.avi"}


def test_save_videos_empty_selection_writes_nothing(out_dir, tiny_map, monkeypatch, ffmpeg_bin):
    monkeypatch.setattr(saving, "find_ffmpeg", lambda: ffmpeg_bin)
    save_videos(out_dir, tiny_map, fps=5, video_keys=[])
    assert list((out_dir / "avi").iterdir()) == []


def test_save_videos_skips_non_videos(out_dir, monkeypatch, ffmpeg_bin):
    monkeypatch.setattr(saving, "find_ffmpeg", lambda: ffmpeg_bin)
    save_videos(out_dir, {"a": 1, "b": None, "c": "x"}, fps=5)
    assert list((out_dir / "avi").iterdir()) == []


def test_save_videos_creates_target_dir(tmp_path, tiny_rgb, monkeypatch, ffmpeg_bin):
    monkeypatch.setattr(saving, "find_ffmpeg", lambda: ffmpeg_bin)
    target = tmp_path / "nope" / "nope"
    save_videos(target, {"v": tiny_rgb}, fps=5)
    assert (target / "avi" / "v.avi").is_file()


def test_save_videos_finds_ffmpeg_once(out_dir, tiny_map, monkeypatch, ffmpeg_bin):
    calls = {"n": 0}
    def counted():
        calls["n"] += 1
        return ffmpeg_bin

    monkeypatch.setattr(saving, "find_ffmpeg", counted)
    save_videos(out_dir, tiny_map, fps=5)
    assert calls["n"] == 1


def test_save_videos_reuses_same_ffmpeg_path(out_dir, tiny_map, monkeypatch, ffmpeg_bin):
    seen: list[str | None] = []
    real = saving.save_video

    def spy(path, value, fps, ffmpeg=None, codec="mjpeg"):
        seen.append(ffmpeg)
        return real(path, value, fps=fps, ffmpeg=ffmpeg, codec=codec)

    monkeypatch.setattr(saving, "find_ffmpeg", lambda: ffmpeg_bin)
    monkeypatch.setattr(saving, "save_video", spy)
    save_videos(out_dir, tiny_map, fps=5)

    assert len(seen) == 2
    assert seen[0] == seen[1] == ffmpeg_bin