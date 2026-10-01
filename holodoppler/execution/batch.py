"""Batch execution: run one pipeline over many input files.

Every job is attempted, even when an earlier job fails. The caller decides the
process exit status from the returned :class:`BatchResult`.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .context import ExecutionMode
from .runner import run_pipeline


@dataclass
class BatchResult:
    """Outcome of a batch run.

    Attributes
    ----------
    total:
        Number of jobs listed by the batch file, including entries that could
        not be read.
    succeeded:
        Number of jobs that completed without raising.
    failures:
        ``(path, reason)`` pairs for every job that did not complete.
    mode:
        The execution mode the batch ran in.
    """

    total: int
    succeeded: int
    failures: List[Tuple[Path, str]]
    mode: ExecutionMode

    @property
    def failed(self) -> int:
        """Number of failed jobs."""
        return len(self.failures)

    def summary(self) -> str:
        """Render the human-readable batch summary."""
        lines = [
            "",
            "=" * 50,
            f"Batch processing complete ({self.mode} mode):",
            f"  Total files: {self.total}",
            f"  Successful:  {self.succeeded}",
            f"  Failed:      {self.failed}",
        ]

        if self.failures:
            lines.append("")
            lines.append("Failed files:")
            for path, error in self.failures:
                lines.append(f"  - {path.name}: {error}")
            lines.append("")
            lines.append(f"{self.failed}/{self.total} jobs failed")

        return "\n".join(lines)


def _safe_print(message: str, *, file=None) -> None:
    """
    Print a message, degrading gracefully on unencodable characters.

    Batch progress uses the "check" and "cross" markers. Windows consoles
    commonly default to cp1252, where those glyphs cannot be encoded, and a
    UnicodeEncodeError would turn a completed job into a reported failure.
    Fall back to a lossy but encodable rendering when the stream cannot carry
    the character.

    Args:
        message: Text to print
        file: Target stream, defaults to stdout
    """
    stream = sys.stdout if file is None else file

    try:
        print(message, file=stream)
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "ascii"
        print(
            message.encode(encoding, "replace").decode(encoding, "replace"),
            file=stream,
        )



def read_batch_file(
    batch_file: Path,
) -> Tuple[List[Path], List[Tuple[Path, str]]]:
    """
    Read a text file containing file paths (one per line).

    Args:
        batch_file: Path to the batch file

    Returns:
        Tuple of (resolved existing paths, [(missing path, reason), ...])

    Raises:
        SystemExit: If the file cannot be read or contains no entries at all
    """
    paths: List[Path] = []
    failures: List[Tuple[Path, str]] = []

    try:
        with batch_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                path = Path(line).expanduser().resolve()
                if not path.is_file():
                    reason = (
                        f"line {line_num} of {batch_file.name} points to a "
                        f"file that does not exist: {path}"
                    )
                    _safe_print(
                        f"Warning: {reason}. Skipping.",
                        file=sys.stderr,
                    )
                    # A missing entry is counted as a failed job so the batch
                    # cannot report success while silently ignoring inputs.
                    failures.append((path, reason))
                    continue
                paths.append(path)
    except OSError as e:
        raise SystemExit(f"Error reading batch file '{batch_file}': {e}")

    if not paths and not failures:
        raise SystemExit(
            f"No valid file paths found in batch file: {batch_file}\n"
            f"Please ensure the file contains at least one valid .holo path."
        )

    return paths, failures



def run_batch(
    file_paths: List[Path],
    parameters: dict,
    mode: ExecutionMode,
    missing: Optional[List[Tuple[Path, str]]] = None,
) -> BatchResult:
    """
    Process multiple files in batch mode.

    Every job is attempted even when an earlier job fails. Individual error
    messages are preserved and the caller decides the process exit status from
    the returned :class:`BatchResult`.

    Args:
        file_paths: List of input file paths
        parameters: Parameters dict to use for all files
        mode: Execution mode, "preview" or "process"
        missing: Jobs that could not be read from the batch file

    Returns:
        BatchResult describing successes and failures
    """
    results_count: int = 0
    errors: List[Tuple[Path, str]] = list(missing or [])

    # Sequential processing
    total = len(file_paths) + len(errors)
    for idx, file_path in enumerate(file_paths, 1):
        print(f"Processing file {idx}/{total}: {file_path.name}")
        try:
            # Copy parameters to avoid cross-file contamination
            params_copy = parameters.copy()

            # Execute pipeline
            result = run_pipeline(file_path, params_copy, mode)

            # Optionally log result summary if needed
            if result is not None:
                result_type = type(result).__name__
                _safe_print(f"✓ Completed: {file_path.name} (result: {result_type})")
            else:
                _safe_print(f"✓ Completed: {file_path.name} (no result)")

            results_count += 1

        except Exception as e:
            errors.append((file_path, str(e)))
            _safe_print(f"✗ Failed: {file_path.name} - {e}", file=sys.stderr)

    batch_result = BatchResult(
        total=total,
        succeeded=results_count,
        failures=errors,
        mode=mode,
    )

    _safe_print(batch_result.summary())

    return batch_result
