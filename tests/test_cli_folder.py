"""Folder jobs, parameter isolation, and early permission/GPU checks."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from holodoppler import cli
import holodoppler.backend as backend


class FolderTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name).resolve()
        self.input = self.root / "input"
        self.input.mkdir()
        self.output = self.root / "output"
        self.config = self.root / "settings.yaml"
        self.config.write_text("pipeline_name: simple\nfilter_settings: {threshold: 1}\n", encoding="utf-8")

    def run_cli(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return cli.main(list(arguments))

    def test_discovery_is_sorted_and_accepts_uppercase_extensions(self):
        for name in ("z.holo", "A.HOLO", "b.cine", "ignore.txt"):
            (self.input / name).touch()
        (self.input / "fake.holo").mkdir()
        self.assertEqual(
            [path.name for path in cli._read_input_folder(self.input)],
            ["A.HOLO", "b.cine", "z.holo"],
        )

    def test_subfolders_are_opt_in(self):
        nested = self.input / "session"
        nested.mkdir()
        (nested / "recording.holo").touch()
        with self.assertRaisesRegex(ValueError, "No .holo or .cine"):
            cli._read_input_folder(self.input)
        self.assertEqual(cli._read_input_folder(self.input, recursive=True), [nested / "recording.holo"])

    def test_folder_command_keeps_recordings_and_nested_parameters_separate(self):
        for name in ("first", "second"):
            directory = self.input / name
            directory.mkdir()
            (directory / "same.holo").touch()
        calls = []

        def process(path, parameters, mode):
            self.assertEqual(parameters["filter_settings"], {"threshold": 1})
            parameters["filter_settings"]["threshold"] = 99
            calls.append((path, Path(parameters["saving_to_folder"]), mode))

        with patch.object(cli, "_run_pipeline", side_effect=process):
            result = self.run_cli("process", "--folder", str(self.input), str(self.config),
                                  "--output-dir", str(self.output), "--recursive")
        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 2)
        self.assertNotEqual(calls[0][1], calls[1][1])
        self.assertTrue(all(call[1].parent == self.output for call in calls))
        self.assertTrue(all(call[2] == cli.PipelineMode.PROCESS for call in calls))

    def test_a_failed_recording_does_not_stop_the_rest_and_exits_nonzero(self):
        for name in ("first.holo", "second.holo"):
            (self.input / name).touch()
        with patch.object(cli, "_run_pipeline", side_effect=[ValueError("broken recording"), None]) as run:
            result = self.run_cli("process", "--folder", str(self.input), str(self.config))
        self.assertEqual(result, 1)
        self.assertEqual(run.call_count, 2)

    def test_empty_input_returns_failure(self):
        with patch.object(cli, "_run_pipeline") as run:
            result = self.run_cli("process", "--folder", str(self.input), str(self.config))
        self.assertEqual(result, 1)
        run.assert_not_called()

    def test_unwritable_output_fails_before_processing(self):
        (self.input / "recording.holo").touch()
        with patch.object(cli.tempfile, "TemporaryFile", side_effect=PermissionError("read-only")), \
             patch.object(cli, "_run_pipeline") as run:
            result = self.run_cli("process", "--folder", str(self.input), str(self.config),
                                  "--output-dir", str(self.output))
        self.assertEqual(result, 1)
        run.assert_not_called()

    def test_preview_folder_uses_preview_pipeline(self):
        (self.input / "recording.holo").touch()
        with patch.object(cli, "_run_pipeline") as run:
            result = self.run_cli("preview", "--folder", str(self.input), str(self.config))
        self.assertEqual(result, 0)
        self.assertEqual(run.call_args.args[2], cli.PipelineMode.PREVIEW)

    def test_gpu_requirement_rejects_cpu_fallback(self):
        with patch.object(backend, "is_gpu", False):
            with self.assertRaisesRegex(ValueError, "CUDA is unavailable"):
                cli._check_required_gpu({"force_numpy": False, "use_parallel": False})

    def test_gpu_requirement_rejects_cpu_settings(self):
        with patch.object(backend, "is_gpu", True):
            for settings in ({"force_numpy": True}, {"use_parallel": True}):
                with self.assertRaisesRegex(ValueError, "force_numpy: false"):
                    cli._check_required_gpu(settings)

    def test_batch_list_still_accepts_a_config_and_output_directory(self):
        recording = self.input / "recording.holo"
        recording.touch()
        listing = self.root / "files.txt"
        listing.write_text(str(recording) + "\n", encoding="utf-8")
        with patch.object(cli, "_run_pipeline") as run:
            result = self.run_cli("process", "--batch", str(listing), str(self.config),
                                  "--output-dir", str(self.output))
        self.assertEqual(result, 0)
        self.assertEqual(run.call_args.args[0], recording)


if __name__ == "__main__":
    unittest.main()
