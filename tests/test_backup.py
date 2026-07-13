"""Unit tests for automation/backup.py"""

from __future__ import annotations

import time
import zipfile
from pathlib import Path

import pytest

from automation import backup


class TestCreateBackup:
    def test_backs_up_a_directory(self, files_dir: Path, tmp_path: Path):
        dest = tmp_path / "backups"
        archive = backup.create_backup(files_dir, dest)

        assert archive.exists()
        assert archive.suffix == ".zip"
        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
        assert any("notes.txt" in n for n in names)

    def test_backs_up_a_single_file(self, tmp_path: Path):
        source_file = tmp_path / "important.txt"
        source_file.write_text("critical data")
        dest = tmp_path / "backups"

        archive = backup.create_backup(source_file, dest)

        assert archive.exists()
        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
        assert "important.txt" in names

    def test_missing_source_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            backup.create_backup(tmp_path / "ghost", tmp_path / "backups")


class TestRotateBackups:
    def test_keeps_only_the_newest_n(self, tmp_path: Path):
        source = tmp_path / "data"
        source.mkdir()
        (source / "f.txt").write_text("x")
        dest = tmp_path / "backups"

        for _ in range(4):
            backup.create_backup(source, dest)
            time.sleep(1.1)  # ensure distinct mtimes/filenames (1s timestamp resolution)

        all_backups = list(dest.glob("*_backup_*.zip"))
        assert len(all_backups) == 4

        deleted_count = backup.rotate_backups(dest, max_backups_to_keep=2)

        remaining = list(dest.glob("*_backup_*.zip"))
        assert deleted_count == 2
        assert len(remaining) == 2

    def test_nonexistent_destination_returns_zero(self, tmp_path: Path):
        assert backup.rotate_backups(tmp_path / "nowhere", max_backups_to_keep=5) == 0

    def test_negative_max_keep_raises(self, tmp_path: Path):
        with pytest.raises(ValueError):
            backup.rotate_backups(tmp_path, max_backups_to_keep=-1)

    def test_only_touches_files_matching_backup_pattern(self, tmp_path: Path):
        dest = tmp_path / "backups"
        dest.mkdir()
        (dest / "unrelated_file.zip").write_bytes(b"not a backup")

        backup.rotate_backups(dest, max_backups_to_keep=0)

        assert (dest / "unrelated_file.zip").exists()  # left alone
