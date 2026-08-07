"""Export sliding multidimensional HoloDoppler analysis as overview AVIs."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cupy as cp
import numpy as np

from holodoppler.Holodoppler import Holodoppler
from holodoppler.multidimensional import (
    SlidingAnalysisAVIWriter,
    analyze_sliding_window,
    sliding_window_starts,
)
from holodoppler.multidimensional._backend import asnumpy


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Process a recording in bounded complex64 windows and write four "
            "multidimensional diagnostic AVI overview streams."
        )
    )
    parser.add_argument("source", type=Path, help="Read-only .holo input path.")
    parser.add_argument("output", type=Path, help="New output directory.")
    parser.add_argument("--window-length", type=int, default=64)
    parser.add_argument("--stride", type=int, default=64)
    parser.add_argument("--first-frame", type=int, default=0)
    parser.add_argument(
        "--end-frame",
        type=int,
        default=None,
        help="Exclusive end frame; defaults to the complete recording.",
    )
    parser.add_argument("--svd-remove-modes", type=int, default=4)
    parser.add_argument("--playback-fps", type=float, default=None)
    parser.add_argument("--codec", default="MJPG")
    parser.add_argument("--panel-width", type=int, default=320)
    parser.add_argument(
        "--max-windows",
        type=int,
        default=None,
        help="Optional bounded smoke-test window count.",
    )
    return parser.parse_args()


def _parameters_from_footer(footer: dict, window_length: int) -> dict:
    rendering = footer["compute_settings"]["image_rendering"]
    info = footer["info"]
    pitch = info["pixel_pitch"]
    if rendering["space_transformation"] != "FRESNELTR":
        raise RuntimeError(
            f"Unsupported propagation: {rendering['space_transformation']}"
        )
    return {
        "first_frame": 0,
        "batch_size": int(window_length),
        "wavelength": float(rendering["lambda"]),
        "pixel_pitch": (
            float(pitch["y"]) * 1e-6,
            float(pitch["x"]) * 1e-6,
        ),
        "spatial_propagation": "Fresnel",
        "zero_padding": False,
        "z": float(rendering["propagation_distance"]),
        "shack_hartmann": False,
        "sampling_freq": float(info["input_fps"]),
    }


def main() -> None:
    arguments = _arguments()
    source = arguments.source.resolve()
    output = arguments.output.resolve()
    if source.suffix.lower() != ".holo":
        raise ValueError("source must be a .holo recording.")
    if not source.is_file():
        raise FileNotFoundError(source)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite output directory: {output}")

    source_before = source.stat()
    processor = Holodoppler(backend="cupy", pipeline_version="latest")
    pool = cp.get_default_memory_pool()
    pinned_pool = cp.get_default_pinned_memory_pool()
    pool.free_all_blocks()
    pinned_pool.free_all_blocks()
    try:
        cp.fft.config.get_plan_cache().clear()
    except Exception:
        pass

    free_before, total_vram = cp.cuda.runtime.memGetInfo()
    used_before = total_vram - free_before
    peak_global_used = used_before
    peak_pool_used = 0
    peak_pool_reserved = 0
    writer = None
    started = time.perf_counter()
    reports: list[dict] = []

    try:
        processor.load_file(str(source))
        header = dict(processor.file_header)
        parameters = _parameters_from_footer(
            processor.file_footer, arguments.window_length
        )
        first_frame = int(arguments.first_frame)
        end_frame = (
            int(arguments.end_frame)
            if arguments.end_frame is not None
            else int(header["num_frames"])
        )
        if first_frame < 0 or end_frame > header["num_frames"]:
            raise ValueError("The requested frame range lies outside the recording.")
        if end_frame <= first_frame:
            raise ValueError("end_frame must exceed first_frame.")

        local_starts = sliding_window_starts(
            end_frame - first_frame,
            window_length=arguments.window_length,
            stride=arguments.stride,
        )
        starts = tuple(first_frame + value for value in local_starts)
        if arguments.max_windows is not None:
            if arguments.max_windows < 1:
                raise ValueError("max_windows must be positive.")
            starts = starts[: arguments.max_windows]
        physical_analysis_fps = parameters["sampling_freq"] / arguments.stride
        playback_fps = (
            float(arguments.playback_fps)
            if arguments.playback_fps is not None
            else min(physical_analysis_fps, 65.0)
        )

        writer = SlidingAnalysisAVIWriter(
            output,
            playback_fps=playback_fps,
            source_shape=(header["height"], header["width"]),
            codec=arguments.codec,
            panel_width=arguments.panel_width,
        )
        print(
            f"Loaded {header['num_frames']} frames; processing {len(starts)} "
            f"windows of {arguments.window_length} frames.",
            flush=True,
        )
        expected_shape = (
            arguments.window_length,
            header["height"],
            header["width"],
        )

        for window_index, window_start in enumerate(starts):
            window_started = time.perf_counter()
            if window_index == 0:
                print("First-window stage: reading frames", flush=True)
            frames = processor.read_frames(window_start, arguments.window_length)
            if frames is None or frames.shape != expected_shape:
                raise RuntimeError(
                    f"Unexpected frames at {window_start}: "
                    f"{None if frames is None else frames.shape}."
                )
            raw_mean = asnumpy(cp.mean(frames, axis=0))
            if window_index == 0:
                print(
                    f"First-window stage: read complete "
                    f"({time.perf_counter() - window_started:.3f} s); rendering H",
                    flush=True,
                )
            window_parameters = dict(parameters)
            window_parameters["first_frame"] = int(window_start)
            field = processor.render_holograms(
                window_parameters, frames=frames
            )["H"]
            if field.shape != expected_shape or field.dtype != cp.complex64:
                raise RuntimeError(
                    f"Unexpected H at {window_start}: {field.shape}, {field.dtype}."
                )

            if window_index == 0:
                print(
                    f"First-window stage: render complete "
                    f"({time.perf_counter() - window_started:.3f} s); analyzing maps",
                    flush=True,
                )
            analysis = analyze_sliding_window(
                field,
                parameters["sampling_freq"],
                svd_remove_modes=arguments.svd_remove_modes,
            )
            if window_index == 0:
                print(
                    f"First-window stage: analysis complete "
                    f"({time.perf_counter() - window_started:.3f} s); transferring maps",
                    flush=True,
                )
            maps = {name: asnumpy(value) for name, value in analysis.maps.items()}
            maps["raw_mean"] = raw_mean
            window_end = window_start + arguments.window_length - 1
            center_time = (
                window_start + 0.5 * (arguments.window_length - 1)
            ) / parameters["sampling_freq"]
            footer_text = (
                f"window {window_index + 1}/{len(starts)} | frames "
                f"{window_start}-{window_end} | center {center_time:.6f} s | "
                f"SVD modes 1-{arguments.svd_remove_modes} removed"
            )
            if window_index == 0:
                print(
                    f"First-window stage: transfer complete "
                    f"({time.perf_counter() - window_started:.3f} s); encoding AVIs",
                    flush=True,
                )
            writer.write(maps, footer_text)
            cp.cuda.Stream.null.synchronize()

            free_now, total_now = cp.cuda.runtime.memGetInfo()
            peak_global_used = max(peak_global_used, total_now - free_now)
            peak_pool_used = max(peak_pool_used, pool.used_bytes())
            peak_pool_reserved = max(peak_pool_reserved, pool.total_bytes())
            elapsed = time.perf_counter() - window_started
            reports.append(
                {
                    "window_index": window_index,
                    "first_frame": int(window_start),
                    "last_frame": int(window_end),
                    "center_time_s": center_time,
                    "removed_singular_energy_fraction": (
                        analysis.removed_singular_energy_fraction
                    ),
                    "filtered_projection_relative_norm": (
                        analysis.filtered_projection_relative_norm
                    ),
                    "energy_closure_relative_error": (
                        analysis.energy_closure_relative_error
                    ),
                    "elapsed_s": elapsed,
                }
            )
            print(
                f"[{window_index + 1:04d}/{len(starts):04d}] "
                f"frames {window_start}-{window_end} | {elapsed:.3f} s",
                flush=True,
            )

            del maps, analysis, field, frames, raw_mean
            pool.free_all_blocks()
            pinned_pool.free_all_blocks()

        writer.close()
        source_after = source.stat()
        elapsed_total = time.perf_counter() - started
        manifest = {
            "source": str(source),
            "source_opened_read_only": True,
            "source_integrity": {
                "size_before": source_before.st_size,
                "size_after": source_after.st_size,
                "mtime_ns_before": source_before.st_mtime_ns,
                "mtime_ns_after": source_after.st_mtime_ns,
                "unchanged": (
                    source_before.st_size == source_after.st_size
                    and source_before.st_mtime_ns == source_after.st_mtime_ns
                ),
            },
            "branch": "MultidimensionalProcessing",
            "base_commit": "cb0b8201bb210e972d0bbbd3f4b0f7d96b559570",
            "header": header,
            "reconstruction": parameters,
            "frame_range": {
                "first": first_frame,
                "end_exclusive": end_frame,
                "available_count": end_frame - first_frame,
            },
            "sliding": {
                "window_length": arguments.window_length,
                "stride": arguments.stride,
                "window_count": len(starts),
                "starts": list(starts),
                "tail_window_added": bool(
                    starts and starts[-1] != first_frame + (len(starts) - 1) * arguments.stride
                ),
            },
            "analysis": {
                "svd_remove_modes": arguments.svd_remove_modes,
                "spectral_block_length": 32,
                "spectral_overlap": 0,
                "spectral_nfft": 32,
                "number_of_tapers": 4,
                "dpss_time_bandwidth": 2.5,
                "apertures": "fixed balanced NW/NE/SW/SE full plane",
                "delay_frames": 1,
                "delay_seconds": 1.0 / parameters["sampling_freq"],
            },
            "video": {
                "codec": arguments.codec,
                "physical_analysis_fps": physical_analysis_fps,
                "playback_fps": playback_fps,
                "frame_count": writer.frame_count,
                "panel_width": arguments.panel_width,
                "files": {
                    name: str(path.name) for name, path in writer.paths.items()
                },
                "display_scaling": (
                    "per-window robust 1-99.7 percentiles for scalar maps; "
                    "fixed 0-1 coherence; per-window shared signed contrast"
                ),
            },
            "timing": {
                "total_s": elapsed_total,
                "mean_window_s": float(
                    np.mean([report["elapsed_s"] for report in reports])
                ),
            },
            "vram": {
                "total_bytes": total_vram,
                "used_before_bytes": used_before,
                "sampled_peak_global_used_bytes": peak_global_used,
                "sampled_peak_increment_bytes": max(
                    0, peak_global_used - used_before
                ),
                "sampled_peak_cupy_pool_used_bytes": peak_pool_used,
                "sampled_peak_cupy_pool_reserved_bytes": peak_pool_reserved,
            },
            "windows": reports,
        }
        with (output / "manifest.json").open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
        print(json.dumps({key: manifest[key] for key in ("source_integrity", "sliding", "video", "timing", "vram")}, indent=2), flush=True)
    finally:
        if writer is not None:
            writer.close()
        processor._close_file()


if __name__ == "__main__":
    main()
