import logging
from logging.handlers import BufferingHandler
from pathlib import Path

import numpy as np
import pytest

from holodoppler import saving
from holodoppler.saving import media as saving_media
from holodoppler.cli import command
from holodoppler.logging import logger


@pytest.fixture
def records(monkeypatch):
    # Capture the shared logger without opening the user's persistent log.
    monkeypatch.setattr(command, "configure_logging", lambda: logger)
    previous_level = logger.level
    logger.setLevel(logging.DEBUG)
    handler = BufferingHandler(100)
    logger.addHandler(handler)
    try:
        yield handler.buffer
    finally:
        logger.removeHandler(handler)
        handler.close()
        logger.setLevel(previous_level)


@pytest.mark.parametrize("action", ["process", "preview"])
def test_processing_api_shares_pipeline_messages_and_lifecycle(
    action, monkeypatch, records
):
    def pipeline(file_path, parameters, **kwargs):
        logger.debug("Technical details for %s", file_path)
        logger.warning("Some frames were skipped")
        return "result"

    key = "logging_test" if action == "process" else "preview_logging_test"
    monkeypatch.setitem(command.pipelines, key, pipeline)

    result = getattr(command, action)(
        Path("recording.holo"), {"pipeline_name": "logging_test"}
    )

    assert result == "result"
    assert all(record.name == "holodoppler" for record in records)
    assert records[0].levelno == logging.INFO
    assert "recording.holo" in records[0].getMessage()
    technical = next(record for record in records if "Technical details" in record.getMessage())
    assert technical.levelno == logging.DEBUG
    warning = next(record for record in records if "Some frames" in record.getMessage())
    assert warning.levelno == logging.WARNING
    assert any(
        record.levelno == logging.INFO and "complete" in record.getMessage()
        for record in records
    )


def test_batch_keeps_exception_traceback_and_continues(monkeypatch, records):
    visited = []

    def run(file_path, parameters, mode):
        visited.append(file_path.name)
        if file_path.name == "broken.holo":
            raise ValueError("invalid recording")
        return "processed"

    monkeypatch.setattr(command, "_run_pipeline", run)

    status = command._batch_process(
        [Path("broken.holo"), Path("good.holo")], {}, command.PipelineMode.PROCESS
    )

    assert status == command.EXIT_FAILURE
    assert visited == ["broken.holo", "good.holo"]
    failure = next(record for record in records if record.exc_info is not None)
    assert failure.levelno == logging.ERROR
    assert failure.exc_info[0] is ValueError
    assert "broken.holo" in failure.getMessage()
    assert any("1 successful, 1 failed" in record.getMessage() for record in records)


def test_png_saving_logs_failure_and_keeps_other_outputs(monkeypatch, records, tmp_path):
    save_image = saving.save_image_png

    def save(path, image):
        if path.name == "broken.png":
            raise OSError("write failed")
        save_image(path, image)

    monkeypatch.setattr(saving_media, "save_image_png", save)
    image = np.zeros((3, 4), dtype=np.uint8)

    saving.save_pngs(tmp_path, {"broken": image, "good": image})

    assert (tmp_path / "png" / "good.png").is_file()
    failure = next(record for record in records if record.exc_info is not None)
    assert failure.levelno == logging.ERROR
    assert failure.exc_info[0] is OSError
    assert "broken" in failure.getMessage()
    assert any("Saved PNG: good" in record.getMessage() for record in records)


def test_directory_failure_keeps_diagnostics_and_propagates(records, tmp_path):
    blocked = tmp_path / "occupied"
    blocked.write_text("a file already exists", encoding="utf-8")

    with pytest.raises(OSError):
        saving.ensure_directory(blocked)

    assert len(records) == 1
    assert records[0].levelno == logging.DEBUG
    assert records[0].exc_info is None
    assert "is_file=True" in records[0].getMessage()
