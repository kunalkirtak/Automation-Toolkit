"""Unit tests for cli.py (argument parsing) and main.py (dispatch/integration)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli import parse_args
import main as main_module


class TestArgumentParsing:
    def test_rename_prefix_parses_expected_fields(self):
        args = parse_args(["rename", "prefix", "--dir", "/tmp/x", "--prefix", "A_"])
        assert args.command == "rename"
        assert args.rename_action == "prefix"
        assert args.dir == Path("/tmp/x")
        assert args.prefix == "A_"
        assert args.dry_run is False

    def test_pdf_merge_accepts_multiple_files(self):
        args = parse_args(["pdf", "merge", "--files", "a.pdf", "b.pdf", "--output", "out.pdf"])
        assert args.pdf_action == "merge"
        assert args.files == [Path("a.pdf"), Path("b.pdf")]

    def test_excel_filter_parses_expected_fields(self):
        args = parse_args(
            ["excel", "filter", "--file", "d.xlsx", "--sheet", "S1", "--column", "Status", "--value", "Active"]
        )
        assert args.excel_action == "filter"
        assert args.column == "Status"
        assert args.value == "Active"

    def test_missing_required_command_exits(self):
        with pytest.raises(SystemExit):
            parse_args([])

    def test_verbose_flag(self):
        args = parse_args(["-v", "backup", "--source", "s", "--destination", "d"])
        assert args.verbose is True


class TestMainDispatchIntegration:
    """Exercises the real CLI -> automation/ pipeline end to end, no mocking."""

    def test_duplicates_command_succeeds_on_real_directory(self, files_dir: Path):
        exit_code = main_module.main(["duplicates", "--dir", str(files_dir)])
        assert exit_code == 0

    def test_rename_dry_run_succeeds(self, files_dir: Path):
        exit_code = main_module.main(
            ["rename", "prefix", "--dir", str(files_dir), "--prefix", "X_", "--dry-run"]
        )
        assert exit_code == 0

    def test_organize_command_actually_moves_files(self, files_dir: Path):
        exit_code = main_module.main(["organize", "--dir", str(files_dir)])
        assert exit_code == 0
        assert (files_dir / "Images").exists()

    def test_missing_directory_returns_nonzero_exit_code(self, tmp_path: Path):
        exit_code = main_module.main(["duplicates", "--dir", str(tmp_path / "ghost")])
        assert exit_code == 1

    def test_pdf_merge_end_to_end(self, sample_pdf: Path, second_sample_pdf: Path, tmp_path: Path):
        output = tmp_path / "merged.pdf"
        exit_code = main_module.main(
            ["pdf", "merge", "--files", str(sample_pdf), str(second_sample_pdf), "--output", str(output)]
        )
        assert exit_code == 0
        assert output.exists()

    def test_excel_read_end_to_end(self, sample_excel: Path):
        exit_code = main_module.main(["excel", "read", "--file", str(sample_excel)])
        assert exit_code == 0

    def test_wrong_pdf_password_returns_clean_error_not_crash(self, sample_pdf: Path, tmp_path: Path):
        encrypted = tmp_path / "locked.pdf"
        main_module.main(["pdf", "encrypt", "--file", str(sample_pdf), "--password", "right", "--output", str(encrypted)])

        exit_code = main_module.main(
            ["pdf", "decrypt", "--file", str(encrypted), "--password", "wrong", "--output", str(tmp_path / "out.pdf")]
        )
        assert exit_code == 1  # handled gracefully, not an unhandled exception

    def test_rename_suffix_timestamp_clean_spaces_extension(self, files_dir: Path):
        assert main_module.main(["rename", "suffix", "--dir", str(files_dir), "--suffix", "_v2"]) == 0
        assert main_module.main(["rename", "timestamp", "--dir", str(files_dir)]) == 0
        assert main_module.main(["rename", "clean-spaces", "--dir", str(files_dir)]) == 0
        assert main_module.main(["rename", "extension", "--dir", str(files_dir), "--old-ext", ".py", "--new-ext", ".pyw"]) == 0

    def test_duplicates_with_delete_flag(self, files_dir: Path):
        exit_code = main_module.main(["duplicates", "--dir", str(files_dir), "--delete", "--dry-run"])
        assert exit_code == 0

    def test_pdf_split_rotate_metadata_extract_text(self, sample_pdf: Path, tmp_path: Path):
        assert main_module.main(["pdf", "split", "--file", str(sample_pdf), "--output-dir", str(tmp_path / "pages")]) == 0
        assert main_module.main(["pdf", "rotate", "--file", str(sample_pdf), "--degrees", "180", "--output", str(tmp_path / "rot.pdf")]) == 0
        assert main_module.main(["pdf", "metadata", "--file", str(sample_pdf)]) == 0
        assert main_module.main(["pdf", "extract-text", "--file", str(sample_pdf)]) == 0

    def test_excel_create_format_summary_filter_export(self, sample_excel: Path, tmp_path: Path):
        new_wb = tmp_path / "new.xlsx"
        assert main_module.main(["excel", "create", "--file", str(new_wb), "--headers", "A", "B"]) == 0
        assert main_module.main(["excel", "format", "--file", str(sample_excel), "--sheet", "Sheet1"]) == 0
        assert main_module.main(
            ["excel", "summary", "--file", str(sample_excel), "--sheet", "Sheet1", "--group-by", "Region", "--agg-column", "Revenue"]
        ) == 0
        assert main_module.main(
            ["excel", "filter", "--file", str(sample_excel), "--sheet", "Sheet1", "--column", "Status", "--value", "Active",
             "--output", str(tmp_path / "filtered.xlsx")]
        ) == 0
        assert main_module.main(
            ["excel", "export", "--file", str(sample_excel), "--sheet", "Sheet1", "--format", "csv", "--output", str(tmp_path / "out.csv")]
        ) == 0

    def test_backup_command_end_to_end(self, files_dir: Path, tmp_path: Path):
        dest = tmp_path / "backups"
        exit_code = main_module.main(["backup", "--source", str(files_dir), "--destination", str(dest)])
        assert exit_code == 0
        assert list(dest.glob("*_backup_*.zip"))

    def test_config_override_file_is_respected(self, files_dir: Path, tmp_path: Path):
        import json

        config_path = tmp_path / "config.local.json"
        config_path.write_text(json.dumps({"log_level": "DEBUG"}))

        exit_code = main_module.main(
            ["--config", str(config_path), "duplicates", "--dir", str(files_dir)]
        )
        assert exit_code == 0
