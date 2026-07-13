"""
tests/conftest.py
=====================
Shared pytest fixtures.

Every fixture below builds its test data fresh inside pytest's
per-test ``tmp_path`` directory -- tests never read or write anything
under the project's real ``sample_data/``, so they're fully isolated
and safe to run in parallel or in CI.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from pypdf import PdfWriter


@pytest.fixture
def files_dir(tmp_path: Path) -> Path:
    """A directory with a representative mix of files: spaces in names,
    known duplicate content, and several different extensions -- enough
    to exercise renaming, organizing, and duplicate detection."""
    d = tmp_path / "files"
    d.mkdir()

    (d / "vacation photo.jpg").write_bytes(b"jpg-bytes-AAA")
    (d / "vacation photo copy.jpg").write_bytes(b"jpg-bytes-AAA")  # duplicate of above
    (d / "notes.txt").write_bytes(b"hello notes")
    (d / "notes backup.txt").write_bytes(b"hello notes")  # duplicate of above
    (d / "budget.xlsx").write_bytes(b"fake-xlsx-bytes")
    (d / "script.py").write_bytes(b"print('hi')")
    (d / "unique.pdf").write_bytes(b"unique-pdf-bytes")

    return d


@pytest.fixture
def empty_dir(tmp_path: Path) -> Path:
    d = tmp_path / "empty"
    d.mkdir()
    return d


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """A real, valid 2-page PDF with metadata set."""
    path = tmp_path / "sample.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    writer.add_metadata({"/Title": "Sample PDF", "/Author": "Test Suite"})
    with path.open("wb") as fh:
        writer.write(fh)
    return path


@pytest.fixture
def second_sample_pdf(tmp_path: Path) -> Path:
    """A second, single-page PDF -- used for merge tests."""
    path = tmp_path / "sample_two.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with path.open("wb") as fh:
        writer.write(fh)
    return path


@pytest.fixture
def sample_excel(tmp_path: Path) -> Path:
    """A workbook with known, hand-checkable data for filter/summary tests."""
    path = tmp_path / "sales.xlsx"
    df = pd.DataFrame(
        {
            "Name": ["Asha", "Ravi", "Meera", "Karan"],
            "Region": ["North", "South", "North", "West"],
            "Revenue": [100, 200, 300, 400],
            "Status": ["Active", "Active", "Inactive", "Active"],
        }
    )
    df.to_excel(path, sheet_name="Sheet1", index=False)
    return path
