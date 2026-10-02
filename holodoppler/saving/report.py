"""Per-run accounting for the saving stage.

Writers stay free of progress chatter: they only record what they wrote in a
:class:`WriteTally`, and the bundle prints one summary line at the end. A tally
is optional everywhere so each writer still works standalone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class WriteTally:
    """Counts of the artifacts written during one save run."""

    #: Files written per video format label (``{"avi": 6, "mp4": 6}``).
    videos: dict[str, int] = field(default_factory=dict)
    #: Number of PNG files written.
    pngs: int = 0
    #: Number of individual CSV files written.
    csv: int = 0
    #: Number of JSON files written.
    json: int = 0
    #: Number of YAML files written.
    yaml: int = 0
    #: Number of HDF5 files written.
    h5: int = 0
    #: Items that were requested but could not be written.
    failures: int = 0

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_video(self, format_name: str, count: int = 1) -> None:
        """Record ``count`` videos written in ``format_name``."""
        self.videos[format_name] = self.videos.get(format_name, 0) + count

    def record_png(self, count: int = 1) -> None:
        """Record ``count`` PNG files written."""
        self.pngs += count

    def record_csv(self, count: int = 1) -> None:
        """Record ``count`` CSV files written."""
        self.csv += count

    def record_json(self, count: int = 1) -> None:
        """Record ``count`` JSON files written."""
        self.json += count

    def record_yaml(self, count: int = 1) -> None:
        """Record ``count`` YAML files written."""
        self.yaml += count

    def record_h5(self, count: int = 1) -> None:
        """Record ``count`` HDF5 files written."""
        self.h5 += count

    def record_failure(self, count: int = 1) -> None:
        """Record ``count`` items that could not be written."""
        self.failures += count

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    @property
    def total_files(self) -> int:
        """Every file counted by this tally."""
        return sum(self.videos.values()) + self.pngs + self.csv + self.json + self.yaml + self.h5

    def counts(self) -> dict[str, int]:
        """Flat ``label -> count`` view, video formats included."""
        items = {f"videos[{name}]": count for name, count in sorted(self.videos.items())}
        items.update(
            {
                "pngs": self.pngs,
                "csv": self.csv,
                "json": self.json,
                "yaml": self.yaml,
                "h5": self.h5,
            }
        )
        return items

    def describe(self, labels: Iterable[str] | None = None) -> str:
        """
        Render the per-type counts as one line.

        Only non-zero counts are shown, so a run that wrote no YAML does not
        advertise an empty category. Zero counts are rendered as ``none`` when
        every category is empty.
        """
        parts: list[str] = []

        for name, count in sorted(self.videos.items()):
            if count:
                parts.append(f"videos[{name}]: {count}")

        for label, count in (
            ("pngs", self.pngs),
            ("csv", self.csv),
            ("json", self.json),
            ("yaml", self.yaml),
            ("h5", self.h5),
        ):
            if count:
                parts.append(f"{label}: {count}")

        if self.failures:
            parts.append(f"failures: {self.failures}")

        if not parts:
            return "no files written"

        return " | ".join(parts)

    def summary(self, elapsed: float) -> str:
        """The single line the saving stage prints when it finishes."""
        return (
            f"Saving completed in {elapsed:.1f} seconds\n"
            f"  {self.describe()}"
        )
