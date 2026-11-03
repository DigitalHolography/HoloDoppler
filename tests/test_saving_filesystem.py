import os
from types import SimpleNamespace

import pytest

from holodoppler.saving import filesystem, session


@pytest.mark.parametrize("option", ["erase", "archive_old"])
def test_blocked_tree_is_untouched(tmp_path, monkeypatch, option):
    target = tmp_path / "results"
    target.mkdir()
    (target / "first.txt").write_text("keep")
    nested = target / "nested"
    nested.mkdir()
    blocked = nested / "blocked.txt"
    blocked.write_text("keep too")

    def check(path):
        if path == blocked:
            raise PermissionError(13, "blocked", str(path))

    monkeypatch.setattr(filesystem.os, "name", os.name)
    if os.name == "nt":
        monkeypatch.setattr(filesystem, "_check_windows_access", check)
    else:
        original = filesystem.os.access
        monkeypatch.setattr(filesystem.os, "access", lambda p, mode: False if p == nested else original(p, mode))
    with pytest.raises(PermissionError):
        session._prepare_output_directory(SimpleNamespace(file_path=tmp_path / "input.raw"),
                                          {"overwrite_option": option}, target, None)
    assert (target / "first.txt").read_text() == "keep"
    assert blocked.read_text() == "keep too"
    assert not (tmp_path / "archive").exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows sharing semantics")
def test_real_open_file_blocks_probe(tmp_path):
    path = tmp_path / "open.txt"
    path.write_text("keep")
    with path.open("rb"):
        with pytest.raises(PermissionError):
            filesystem.check_output_access(tmp_path)
    filesystem.check_output_access(tmp_path)


@pytest.mark.parametrize("option", ["erase", "archive_old"])
def test_unlocked_tree_prepares(tmp_path, option):
    target = tmp_path / "results"
    target.mkdir()
    (target / "old.txt").write_text("old")
    session._prepare_output_directory(SimpleNamespace(file_path=tmp_path / "input.raw"),
                                      {"overwrite_option": option}, target, None)
    assert not (target / "old.txt").exists()
    assert (target / "h5").is_dir()
    if option == "archive_old":
        assert (tmp_path / "archive" / "results" / "old.txt").read_text() == "old"
