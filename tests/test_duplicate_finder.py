"""Unit tests for automation/duplicate_finder.py"""

from __future__ import annotations

from pathlib import Path

import pytest

from automation import duplicate_finder


class TestComputeFileHash:
    def test_identical_content_produces_identical_hash(self, tmp_path: Path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_bytes(b"same content")
        b.write_bytes(b"same content")

        assert duplicate_finder.compute_file_hash(a) == duplicate_finder.compute_file_hash(b)

    def test_different_content_produces_different_hash(self, tmp_path: Path):
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_bytes(b"content one")
        b.write_bytes(b"content two")

        assert duplicate_finder.compute_file_hash(a) != duplicate_finder.compute_file_hash(b)

    def test_respects_chosen_algorithm(self, tmp_path: Path):
        f = tmp_path / "a.txt"
        f.write_bytes(b"hello")
        md5_hash = duplicate_finder.compute_file_hash(f, algorithm="md5")
        sha_hash = duplicate_finder.compute_file_hash(f, algorithm="sha256")
        assert len(md5_hash) == 32
        assert len(sha_hash) == 64


class TestFindDuplicates:
    def test_finds_known_duplicate_groups(self, files_dir: Path):
        groups = duplicate_finder.find_duplicates(files_dir, recursive=False)
        # files_dir fixture has exactly two duplicate pairs by content
        assert len(groups) == 2
        group_sizes = sorted(len(paths) for paths in groups.values())
        assert group_sizes == [2, 2]

    def test_no_duplicates_returns_empty_dict(self, tmp_path: Path):
        d = tmp_path / "unique_files"
        d.mkdir()
        (d / "a.txt").write_bytes(b"aaa")
        (d / "b.txt").write_bytes(b"bbb")

        assert duplicate_finder.find_duplicates(d) == {}

    def test_missing_directory_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            duplicate_finder.find_duplicates(tmp_path / "nope")


class TestDeleteDuplicates:
    def test_keep_first_deletes_all_others(self, files_dir: Path):
        groups = duplicate_finder.find_duplicates(files_dir, recursive=False)
        deleted = duplicate_finder.delete_duplicates(groups, keep="first")

        assert len(deleted) == 2  # one deletion per duplicate pair
        for group in groups.values():
            survivors = [p for p in group if p.exists()]
            assert len(survivors) == 1
            assert survivors[0] == sorted(group)[0]

    def test_keep_last_keeps_the_other_copy(self, files_dir: Path):
        groups = duplicate_finder.find_duplicates(files_dir, recursive=False)
        duplicate_finder.delete_duplicates(groups, keep="last")

        for group in groups.values():
            survivors = [p for p in group if p.exists()]
            assert survivors[0] == sorted(group)[-1]

    def test_dry_run_deletes_nothing(self, files_dir: Path):
        groups = duplicate_finder.find_duplicates(files_dir, recursive=False)
        deleted = duplicate_finder.delete_duplicates(groups, dry_run=True)

        assert len(deleted) == 2  # reports what *would* be deleted
        for group in groups.values():
            assert all(p.exists() for p in group)  # but nothing actually removed

    def test_invalid_keep_value_raises(self, files_dir: Path):
        groups = duplicate_finder.find_duplicates(files_dir, recursive=False)
        with pytest.raises(ValueError):
            duplicate_finder.delete_duplicates(groups, keep="middle")
