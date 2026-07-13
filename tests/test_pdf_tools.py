"""Unit tests for automation/pdf_tools.py"""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from automation import pdf_tools


class TestMergePdfs:
    def test_merged_page_count_is_the_sum(self, sample_pdf: Path, second_sample_pdf: Path, tmp_path: Path):
        output = tmp_path / "merged.pdf"
        pdf_tools.merge_pdfs([sample_pdf, second_sample_pdf], output)

        assert output.exists()
        reader = PdfReader(str(output))
        assert len(reader.pages) == 3  # 2 pages + 1 page

    def test_missing_input_file_raises(self, sample_pdf: Path, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            pdf_tools.merge_pdfs([sample_pdf, tmp_path / "ghost.pdf"], tmp_path / "out.pdf")

    def test_empty_input_list_raises(self, tmp_path: Path):
        with pytest.raises(ValueError):
            pdf_tools.merge_pdfs([], tmp_path / "out.pdf")


class TestSplitPdf:
    def test_creates_one_file_per_page(self, sample_pdf: Path, tmp_path: Path):
        out_dir = tmp_path / "pages"
        result = pdf_tools.split_pdf(sample_pdf, out_dir)

        assert len(result) == 2  # sample_pdf fixture has 2 pages
        assert all(p.exists() for p in result)
        assert PdfReader(str(result[0])).pages[0] is not None


class TestExtractText:
    def test_returns_string_without_crashing_on_blank_pages(self, sample_pdf: Path):
        text = pdf_tools.extract_text(sample_pdf)
        assert isinstance(text, str)  # blank pages -> empty string is fine

    def test_writes_to_output_path_when_given(self, sample_pdf: Path, tmp_path: Path):
        out_file = tmp_path / "extracted.txt"
        pdf_tools.extract_text(sample_pdf, output_path=out_file)
        assert out_file.exists()


class TestRotatePages:
    def test_rotation_is_applied_to_every_page(self, sample_pdf: Path, tmp_path: Path):
        output = tmp_path / "rotated.pdf"
        pdf_tools.rotate_pages(sample_pdf, output, degrees=90)

        reader = PdfReader(str(output))
        assert all(page.get("/Rotate", 0) == 90 for page in reader.pages)

    def test_invalid_degrees_raises(self, sample_pdf: Path, tmp_path: Path):
        with pytest.raises(ValueError):
            pdf_tools.rotate_pages(sample_pdf, tmp_path / "out.pdf", degrees=45)


class TestEncryptDecrypt:
    def test_roundtrip_recovers_readable_pdf(self, sample_pdf: Path, tmp_path: Path):
        encrypted = tmp_path / "locked.pdf"
        decrypted = tmp_path / "unlocked.pdf"

        pdf_tools.encrypt_pdf(sample_pdf, encrypted, password="hunter2")

        locked_reader = PdfReader(str(encrypted))
        assert locked_reader.is_encrypted

        pdf_tools.decrypt_pdf(encrypted, decrypted, password="hunter2")
        open_reader = PdfReader(str(decrypted))
        assert not open_reader.is_encrypted
        assert len(open_reader.pages) == 2

    def test_wrong_password_raises(self, sample_pdf: Path, tmp_path: Path):
        encrypted = tmp_path / "locked.pdf"
        pdf_tools.encrypt_pdf(sample_pdf, encrypted, password="correct-password")

        with pytest.raises(ValueError):
            pdf_tools.decrypt_pdf(encrypted, tmp_path / "unlocked.pdf", password="wrong-password")

    def test_empty_password_raises(self, sample_pdf: Path, tmp_path: Path):
        with pytest.raises(ValueError):
            pdf_tools.encrypt_pdf(sample_pdf, tmp_path / "out.pdf", password="")


class TestExtractMetadata:
    def test_returns_title_author_and_page_count(self, sample_pdf: Path):
        meta = pdf_tools.extract_metadata(sample_pdf)

        assert meta["Title"] == "Sample PDF"
        assert meta["Author"] == "Test Suite"
        assert meta["page_count"] == "2"
        assert meta["encrypted"] == "False"

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            pdf_tools.extract_metadata(tmp_path / "ghost.pdf")

    def test_wrong_extension_raises(self, tmp_path: Path):
        fake = tmp_path / "not_a_pdf.txt"
        fake.write_text("hello")
        with pytest.raises(ValueError):
            pdf_tools.extract_metadata(fake)
