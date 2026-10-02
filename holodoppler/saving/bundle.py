"""Complete output bundles: :func:`save_bundle` and its path-resolving wrapper."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Iterable, Sequence

from holodoppler.saving.paths import (
    calculate_fps,
    create_directories,
    get_default_output_path,
)
from holodoppler.saving.report import WriteTally
from holodoppler.saving.version import get_git_version
from holodoppler.saving.writer.hdf5 import save_h5
from holodoppler.saving.writer.image import save_pngs
from holodoppler.saving.writer.metadata import save_metadata
from holodoppler.saving.writer.table import save_csv_outputs, save_json, save_yaml
from holodoppler.saving.writer.video import write_videos


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
    video_formats: Sequence[str] | None = None,
) -> WriteTally:
    """
    Save a complete Holodoppler output bundle.

    ``video_formats`` selects which containers to write; it defaults to
    :data:`holodoppler.saving.writer.video.DEFAULT_OUTPUT_FORMATS` (``avi``
    MJPEG and ``mp4`` H.264).

    Returns:
        The :class:`~holodoppler.saving.report.WriteTally` for the run, whose
        counts were already summarized on stdout.
    """
    start_time = time.time()
    target_dir = Path(target_dir)
    tally = WriteTally()

    create_directories(
        target_dir,
        full=save_h5_output,
    )

    # ------------------------------------------------------------------
    # 1. Videos
    # ------------------------------------------------------------------

    write_videos(
        target_dir,
        output,
        fps=fps,
        video_keys=video_keys,
        formats=video_formats,
        tally=tally,
    )

    # ------------------------------------------------------------------
    # 2. PNGs
    # ------------------------------------------------------------------

    save_pngs(
        target_dir,
        output,
        png_keys=png_keys,
        tally=tally,
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
        tally=tally,
    )

    # ------------------------------------------------------------------
    # 4. JSON / YAML
    # ------------------------------------------------------------------

    if json_outputs:
        for name, value in json_outputs.items():
            save_json(
                target_dir / "json" / f"{name}.json",
                value,
                tally=tally,
            )

    if yaml_outputs:
        for name, value in yaml_outputs.items():
            save_yaml(
                target_dir / "yaml" / f"{name}.yaml",
                value,
                tally=tally,
            )

    # ------------------------------------------------------------------
    # 5. Metadata
    # ------------------------------------------------------------------

    save_metadata(
        target_dir,
        file_reader=file_reader,
        parameters=parameters,
        tally=tally,
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
            git_commit=get_git_version(),
            tally=tally,
        )

    elapsed = time.time() - start_time
    print(tally.summary(elapsed))

    return tally


def save_outputs(
    file_reader: Any,
    output: dict[str, Any],
    parameters: dict[str, Any] | None = None,
    holodoppler_path: str | Path | bool | None = None,
    video_path: str | Path | bool | None = None,
    custom_path: str | Path | None = None,
    custom_relative_path: str | Path | None = None,
    end_frame: int | None = None,
    first_frame: int | None = None,
    num_batch: int | None = None,
    save_h5_output: bool = True,
    png_keys: Iterable[str] | None = None,
    video_keys: Iterable[str] | None = None,
    video_formats: Sequence[str] | None = None,
) -> Path:
    """
    Main public saving entry point.

    custom_path:
        Absolute path used directly as the output directory.

    custom_relative_path:
        Path relative to the default *_HD output directory.

    video_formats:
        Video containers to write. Defaults to ``("avi", "mp4")``, i.e. MJPEG
        and H.264.

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
        "sh_psd"
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
        video_formats=video_formats,
    )

    return target_dir
