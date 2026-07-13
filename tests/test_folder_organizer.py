"""Unit tests for automation/folder_organizer.py"""

from __future__ import annotations

from pathlib import Path

import pytest

from automation import folder_organizer


class TestOrganizeByType:
    def test_moves_files_into_category_folders(self, files_dir: Path):
        folder_organizer.organize_by_type(files_dir)

        assert (files_dir / "Images" / "vacation photo.jpg").exists()
        assert (files_dir / "Images" / "vacation photo copy.jpg").exists()
        assert (files_dir / "Documents" / "notes.txt").exists()
        assert (files_dir / "Spreadsheets" / "budget.xlsx").exists()
        assert (files_dir / "Code" / "script.py").exists()
        assert (files_dir / "Documents" / "unique.pdf").exists()

        # nothing should remain loose at the top level
        loose_files = [p for p in files_dir.iterdir() if p.is_file()]
        assert loose_files == []

    def test_unknown_extension_goes_to_others(self, tmp_path: Path):
        d = tmp_path / "misc"
        d.mkdir()
        (d / "weird.xyz123").write_text("mystery")

        folder_organizer.organize_by_type(d)

        assert (d / "Others" / "weird.xyz123").exists()

    def test_dry_run_leaves_files_in_place(self, files_dir: Path):
        before = sorted(p.name for p in files_dir.iterdir() if p.is_file())
        folder_organizer.organize_by_type(files_dir, dry_run=True)
        after = sorted(p.name for p in files_dir.iterdir() if p.is_file())

        assert before == after
        assert not (files_dir / "Images").exists()

    def test_return_value_maps_category_to_paths(self, files_dir: Path):
        result = folder_organizer.organize_by_type(files_dir)
        assert len(result["Images"]) == 2  # both .jpg files
        assert len(result["Documents"]) == 3  # notes.txt, notes backup.txt, unique.pdf

    def test_custom_categories_override_defaults(self, tmp_path: Path):
        d = tmp_path / "custom"
        d.mkdir()
        (d / "data.csv").write_text("a,b,c")

        custom_categories = {"CSVFiles": [".csv"], "Others": []}
        result = folder_organizer.organize_by_type(d, categories=custom_categories)

        assert (d / "CSVFiles" / "data.csv").exists()
        assert len(result["CSVFiles"]) == 1

    def test_missing_directory_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            folder_organizer.organize_by_type(tmp_path / "nope")
