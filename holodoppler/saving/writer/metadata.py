"""Reader metadata and version stamping."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from holodoppler.saving.paths import ensure_directory
from holodoppler.saving.version import save_version_files
from holodoppler.saving.writer.table import save_json

if TYPE_CHECKING:
    from holodoppler.saving.report import WriteTally


def save_metadata(
    target_dir: Path,
    file_reader: Any = None,
    parameters: dict[str, Any] | None = None,
    tally: "WriteTally | None" = None,
) -> None:
    """Save generic and HoloVibes-specific metadata."""
    target_dir = Path(target_dir)
    json_dir = ensure_directory(target_dir / "json")

    if parameters is not None:
        save_json(
            json_dir / "parameters_holodoppler.json",
            parameters,
            tally=tally,
        )

    if file_reader is not None:
        if getattr(file_reader, "extension", None) == ".holo":
            footer = getattr(file_reader, "footer", None)
            if footer is not None:
                save_json(
                    json_dir / "holovibes_footer.json",
                    footer,
                    tally=tally,
                )

            header = getattr(file_reader, "header", None)
            if header is not None:
                if is_dataclass(header):
                    header = asdict(header)
                save_json(
                    json_dir / "holovibes_header.json",
                    header,
                    tally=tally,
                )
        if getattr(file_reader, "extension", None) == ".cine":
            header = getattr(file_reader, "header", None)
            if header is not None:
                if is_dataclass(header):
                    header = asdict(header)
                save_json(
                    json_dir / "cine_metadata.json",
                    header,
                    tally=tally,
                )

    save_version_files(target_dir)
