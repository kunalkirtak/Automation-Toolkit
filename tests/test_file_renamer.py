"""Unit tests for automation/file_renamer.py"""

from __future__ import annotations

from pathlib import Path

import pytest

from automation import file_renamer


def _names(directory: Path) -> set[str]:
    return {p.name for p in directory.iterdir() if p.is_file()}


class TestRenameWithPrefix:
    def test_adds_prefix_to_every_file(self, files_dir: Path):
        before = _names(files_dir)
        results = file_renamer.rename_with_prefix(files_dir, "NEW_")

        assert all(r.success for r in results)
        after = _names(files_dir)
        assert after == {f"NEW_{name}" for name in before}

    def test_dry_run_does_not_touch_disk(self, files_dir: Path):
        before = _names(files_dir)
        results = file_renamer.rename_with_prefix(files_dir, "NEW_", dry_run=True)

        assert all(r.success for r in results)
        assert _names(files_dir) == before  # nothing actually renamed

    def test_missing_directory_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            file_renamer.rename_with_prefix(tmp_path / "does_not_exist", "NEW_")

    def test_file_instead_of_directory_raises(self, tmp_path: Path):
        f = tmp_path / "a_file.txt"
        f.write_text("x")
        with pytest.raises(NotADirectoryError):
            file_renamer.rename_with_prefix(f, "NEW_")


class TestRenameWithSuffix:
    def test_adds_suffix_before_extension(self, files_dir: Path):
        results = file_renamer.rename_with_suffix(files_dir, "_v2")
        assert all(r.success for r in results)
        assert "notes_v2.txt" in _names(files_dir)
        assert "script_v2.py" in _names(files_dir)


class TestRenameWithTimestamp:
    def test_all_files_share_one_timestamp(self, files_dir: Path):
        file_renamer.rename_with_timestamp(files_dir, timestamp_format="%Y%m%d")
        names = _names(files_dir)
        # every renamed file should start with the same 8-digit date stamp
        prefixes = {name.split("_", 1)[0] for name in names}
        assert len(prefixes) == 1
        assert len(next(iter(prefixes))) == 8


class TestRemoveSpaces:
    def test_replaces_spaces_with_underscore_by_default(self, files_dir: Path):
        file_renamer.remove_spaces(files_dir)
        names = _names(files_dir)
        assert "vacation_photo.jpg" in names
        assert not any(" " in name for name in names)

    def test_custom_replacement_character(self, files_dir: Path):
        file_renamer.remove_spaces(files_dir, replacement="-")
        assert "vacation-photo.jpg" in _names(files_dir)


class TestChangeExtension:
    def test_only_matching_extension_is_changed(self, files_dir: Path):
        results = file_renamer.change_extension(files_dir, ".txt", ".md")
        names = _names(files_dir)
        assert "notes.md" in names
        assert "notes backup.md" in names
        assert "script.py" in names  # untouched
        assert len(results) == 2  # only the two .txt files matched

    def test_extension_without_leading_dot_is_normalized(self, files_dir: Path):
        results = file_renamer.change_extension(files_dir, "txt", "md")
        assert len(results) == 2


class TestCollisionHandling:
    def test_appends_counter_on_name_collision(self, tmp_path: Path):
        d = tmp_path / "collide"
        d.mkdir()
        (d / "report.txt").write_text("1")
        (d / "report.md").write_text("2")  # pre-existing file NOT part of the .txt batch

        # report.txt -> report.md is the natural target, but report.md
        # already exists and isn't being renamed itself, so this is a
        # guaranteed, deterministic collision regardless of iteration order.
        file_renamer.change_extension(d, ".txt", ".md")

        names = _names(d)
        assert "report.md" in names    # original file, untouched
        assert "report_1.md" in names  # renamed report.txt, collision resolved
        assert len(names) == 2
