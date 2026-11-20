"""Batch sources support file lists and non-recursive recording folders."""

import pytest

from holodoppler.cli import command
from holodoppler.cli.parser import parse_args


@pytest.mark.parametrize("mode", ["process", "preview"])
def test_batch_folder_processes_only_direct_recording_files(tmp_path, monkeypatch, mode):
    recordings = tmp_path / "recordings"
    recordings.mkdir()
    names = ["a.holo", "b.cine", "c.HOLO", "d.CINE"]
    for name in names + ["notes.txt", "e.holo.bak"]:
        (recordings / name).touch()
    nested = recordings / "nested.holo"
    nested.mkdir()
    (nested / "hidden.cine").touch()
    config = tmp_path / "config.yaml"
    config.touch()
    calls = []
    monkeypatch.setattr(command, "configure_logging", lambda: None)
    monkeypatch.setattr(command, "load_config", lambda path: {"pipeline_name": "default"})
    monkeypatch.setattr(command, "_run_pipeline", lambda *args: calls.append(args))

    assert command.main([mode, "--batch", str(recordings), str(config)]) == 0
    assert [args[0] for args in calls] == [recordings / name for name in names]
    assert all(args[2] == command.PipelineMode(mode) for args in calls)


def test_batch_file_list_still_accepts_comments_and_skips_missing_files(tmp_path):
    recording = tmp_path / "input.holo"
    recording.touch()
    batch_file = tmp_path / "files.txt"
    batch_file.write_text(f"# Recordings\n\n{recording}\n{tmp_path / 'missing.cine'}\n",
                          encoding="utf-8")
    args = parse_args(["process", "--batch", str(batch_file)])
    assert command._read_batch_paths(args.batch) == [recording]


def test_batch_folder_with_no_direct_recordings_reports_error(tmp_path):
    (tmp_path / "notes.txt").touch()
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "hidden.holo").touch()
    with pytest.raises(SystemExit, match="No .holo or .cine files found"):
        command._read_batch_paths(tmp_path)


def test_batch_rejects_missing_path(tmp_path):
    with pytest.raises(SystemExit) as error:
        parse_args(["process", "--batch", str(tmp_path / "missing")])
    assert error.value.code == 2
