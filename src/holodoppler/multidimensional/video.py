"""AVI encoding for reduced sliding multidimensional diagnostic maps."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import cv2
import numpy as np


VIDEO_FILENAMES = {
    "svd": "01_svd4_doppler_overview.avi",
    "coupling": "02_log_amplitude_phase_coupling.avi",
    "recombination": "03_time_lagged_aperture_recombination.avi",
    "contrasts": "04_time_lagged_band_contrasts.avi",
}


def _robust_unit(values: np.ndarray, *, log10: bool = False) -> np.ndarray:
    work = np.asarray(values, dtype=np.float64)
    if log10:
        positive = work[np.isfinite(work) & (work > 0)]
        floor = float(np.min(positive)) if positive.size else 1.0
        work = np.log10(np.maximum(work, floor))
    finite = work[np.isfinite(work)]
    if not finite.size:
        return np.zeros(work.shape, dtype=np.float32)
    lower, upper = np.percentile(finite, (1.0, 99.7))
    if not upper > lower:
        upper = lower + 1.0
    return np.clip((work - lower) / (upper - lower), 0, 1).astype(np.float32)


def _gray(values: np.ndarray, *, log10: bool = False) -> np.ndarray:
    unit = (_robust_unit(values, log10=log10) * 255).astype(np.uint8)
    return cv2.cvtColor(unit, cv2.COLOR_GRAY2BGR)


def _colored(values: np.ndarray, colormap: int, *, log10: bool = False) -> np.ndarray:
    unit = (_robust_unit(values, log10=log10) * 255).astype(np.uint8)
    return cv2.applyColorMap(unit, colormap)


def _coherence(values: np.ndarray) -> np.ndarray:
    unit = (np.clip(values, 0, 1) * 255).astype(np.uint8)
    return cv2.applyColorMap(unit, cv2.COLORMAP_VIRIDIS)


def _phase_coherence(phase: np.ndarray, coherence_squared: np.ndarray) -> np.ndarray:
    hsv = np.empty((*phase.shape, 3), dtype=np.uint8)
    hsv[..., 0] = np.mod((phase + np.pi) / (2 * np.pi), 1.0) * 179
    hsv[..., 1] = 255
    hsv[..., 2] = np.sqrt(np.clip(coherence_squared, 0, 1)) * 255
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def _contrast(values: np.ndarray, limit: float) -> np.ndarray:
    unit = np.clip(0.5 + np.asarray(values) / (2 * limit), 0, 1)
    blue = np.where(unit <= 0.5, 255, 255 * (2 - 2 * unit))
    green = 255 * (1 - np.abs(2 * unit - 1))
    red = np.where(unit >= 0.5, 255, 255 * (2 * unit))
    return np.stack([blue, green, red], axis=-1).astype(np.uint8)


def _doppler_rgb(maps: Mapping[str, np.ndarray]) -> np.ndarray:
    low = _robust_unit(maps["doppler_low_0250_1000"], log10=True)
    middle = _robust_unit(maps["doppler_mid_1000_3000"], log10=True)
    high = _robust_unit(maps["doppler_high_3000_4000"], log10=True)
    return (np.stack([low, middle, high], axis=-1) * 255).astype(np.uint8)


def _panel(image: np.ndarray, title: str, size: tuple[int, int]) -> np.ndarray:
    width, height = size
    resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    header = np.zeros((26, width, 3), dtype=np.uint8)
    cv2.putText(
        header,
        title,
        (6, 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (235, 235, 235),
        1,
        cv2.LINE_AA,
    )
    return np.concatenate([header, resized], axis=0)


def _grid(
    panels: list[tuple[np.ndarray, str]],
    *,
    rows: int,
    columns: int,
    panel_size: tuple[int, int],
    footer_text: str,
) -> np.ndarray:
    if len(panels) != rows * columns:
        raise ValueError("The panel count does not match the requested grid.")
    rendered = [_panel(image, title, panel_size) for image, title in panels]
    row_images = [
        np.concatenate(rendered[index * columns : (index + 1) * columns], axis=1)
        for index in range(rows)
    ]
    canvas = np.concatenate(row_images, axis=0)
    footer = np.zeros((30, canvas.shape[1], 3), dtype=np.uint8)
    cv2.putText(
        footer,
        footer_text,
        (8, 21),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (235, 235, 235),
        1,
        cv2.LINE_AA,
    )
    return np.concatenate([canvas, footer], axis=0)


class SlidingAnalysisAVIWriter:
    """Write four labeled overview AVI streams from reduced NumPy maps."""

    def __init__(
        self,
        output_directory: str | Path,
        *,
        playback_fps: float,
        source_shape: tuple[int, int],
        codec: str = "MJPG",
        panel_width: int = 320,
    ) -> None:
        if playback_fps <= 0:
            raise ValueError("playback_fps must be positive.")
        if len(codec) != 4:
            raise ValueError("codec must contain exactly four characters.")
        ny, nx = map(int, source_shape)
        if ny < 1 or nx < 1:
            raise ValueError("source_shape must be positive.")
        if panel_width < 64:
            raise ValueError("panel_width must be at least 64 pixels.")

        self.output_directory = Path(output_directory)
        if self.output_directory.exists():
            raise FileExistsError(
                f"Refusing to overwrite output directory: {self.output_directory}"
            )
        self.output_directory.mkdir(parents=True, exist_ok=False)
        panel_height = int(round(panel_width * ny / nx))
        if panel_height % 2:
            panel_height += 1
        self.panel_size = (int(panel_width), panel_height)
        self.playback_fps = float(playback_fps)
        self.codec = codec
        self._writers: dict[str, cv2.VideoWriter] = {}
        self._frame_count = 0

    @property
    def paths(self) -> dict[str, Path]:
        return {
            name: self.output_directory / filename
            for name, filename in VIDEO_FILENAMES.items()
        }

    @property
    def frame_count(self) -> int:
        return self._frame_count

    def _write_frame(self, name: str, frame: np.ndarray) -> None:
        writer = self._writers.get(name)
        if writer is None:
            path = self.paths[name]
            fourcc = cv2.VideoWriter_fourcc(*self.codec)
            writer = cv2.VideoWriter(
                str(path),
                fourcc,
                self.playback_fps,
                (frame.shape[1], frame.shape[0]),
                isColor=True,
            )
            if not writer.isOpened():
                raise RuntimeError(f"Could not open AVI writer: {path}")
            self._writers[name] = writer
        writer.write(frame)

    def write(self, maps: Mapping[str, np.ndarray], footer_text: str) -> None:
        contrast_arrays = [
            maps[f"delay_{mode}_contrast_{band}"]
            for band in (
                "total_0250_4000",
                "low_0250_1000",
                "mid_1000_3000",
                "high_3000_4000",
            )
            for mode in ("x", "y", "xy")
        ]
        finite = np.concatenate(
            [array[np.isfinite(array)].reshape(-1) for array in contrast_arrays]
        )
        contrast_limit = float(np.percentile(np.abs(finite), 99.5))
        if not contrast_limit > 0:
            contrast_limit = 1.0

        svd_panels = [
            (_gray(maps["raw_mean"]), "Raw mean"),
            (_gray(maps["unfiltered_amplitude"], log10=True), "Before SVD: log amplitude"),
            (_colored(maps["removed_power"], cv2.COLORMAP_INFERNO, log10=True), "Removed modes 1-4: log power"),
            (_gray(maps["filtered_amplitude"], log10=True), "After SVD4: log amplitude"),
            (_colored(maps["doppler_total_0250_4000"], cv2.COLORMAP_INFERNO, log10=True), "SVD4 power 250-4000 Hz"),
            (_colored(maps["doppler_low_0250_1000"], cv2.COLORMAP_MAGMA, log10=True), "SVD4 power 250-1000 Hz"),
            (_colored(maps["doppler_mid_1000_3000"], cv2.COLORMAP_MAGMA, log10=True), "SVD4 power 1000-3000 Hz"),
            (_colored(maps["doppler_high_3000_4000"], cv2.COLORMAP_MAGMA, log10=True), "SVD4 power 3000-4000 Hz"),
            (_doppler_rgb(maps), "RGB: high / mid / low"),
        ]
        self._write_frame(
            "svd",
            _grid(
                svd_panels,
                rows=3,
                columns=3,
                panel_size=self.panel_size,
                footer_text=footer_text,
            ),
        )

        bands = (
            ("total_0250_4000", "250-4000 Hz"),
            ("low_0250_1000", "250-1000 Hz"),
            ("mid_1000_3000", "1000-3000 Hz"),
            ("high_3000_4000", "3000-4000 Hz"),
        )
        coupling_panels: list[tuple[np.ndarray, str]] = []
        coupling_panels.extend(
            (
                _colored(maps[f"coupling_cross_{name}"], cv2.COLORMAP_INFERNO, log10=True),
                f"Cross magnitude {label}",
            )
            for name, label in bands
        )
        coupling_panels.extend(
            (
                _coherence(maps[f"coupling_coherence2_{name}"]),
                f"Coherence squared {label}",
            )
            for name, label in bands
        )
        coupling_panels.extend(
            (
                _phase_coherence(
                    maps[f"coupling_phase_{name}"],
                    maps[f"coupling_coherence2_{name}"],
                ),
                f"Phase hue / coherence {label}",
            )
            for name, label in bands
        )
        self._write_frame(
            "coupling",
            _grid(
                coupling_panels,
                rows=3,
                columns=4,
                panel_size=self.panel_size,
                footer_text=footer_text,
            ),
        )

        recombination_panels: list[tuple[np.ndarray, str]] = []
        for mode in ("x", "y", "xy"):
            recombination_panels.extend(
                [
                    (_colored(maps[f"delay_{mode}_plus_total"], cv2.COLORMAP_MAGMA, log10=True), f"{mode}: positive one-frame arrangement"),
                    (_colored(maps[f"delay_{mode}_minus_total"], cv2.COLORMAP_MAGMA, log10=True), f"{mode}: reciprocal arrangement"),
                    (_contrast(maps[f"delay_{mode}_contrast_total_0250_4000"], contrast_limit), f"{mode}: normalized reciprocal contrast"),
                ]
            )
        self._write_frame(
            "recombination",
            _grid(
                recombination_panels,
                rows=3,
                columns=3,
                panel_size=self.panel_size,
                footer_text=footer_text,
            ),
        )

        contrast_panels = [
            (
                _contrast(maps[f"delay_{mode}_contrast_{name}"], contrast_limit),
                f"{mode} contrast, {label}",
            )
            for name, label in bands
            for mode in ("x", "y", "xy")
        ]
        self._write_frame(
            "contrasts",
            _grid(
                contrast_panels,
                rows=4,
                columns=3,
                panel_size=self.panel_size,
                footer_text=footer_text,
            ),
        )
        self._frame_count += 1

    def close(self) -> None:
        for writer in self._writers.values():
            writer.release()
        self._writers.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
