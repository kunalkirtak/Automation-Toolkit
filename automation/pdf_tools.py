"""
automation/pdf_tools.py
=========================
PDF automation built on top of ``pypdf``: merge, split, extract text,
rotate, encrypt, decrypt, and read metadata.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from pypdf import PdfReader, PdfWriter
from tqdm import tqdm

from automation.logger import get_logger

logger = get_logger(__name__)


def _require_file(path: Path) -> Path:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a .pdf file: {path}")
    return path


def merge_pdfs(input_paths: List[Path], output_path: Path) -> Path:
    """Merge multiple PDFs, in order, into a single ``output_path`` file."""
    if not input_paths:
        raise ValueError("input_paths must contain at least one PDF")

    writer = PdfWriter()
    for p in tqdm(input_paths, desc="Merging PDFs", unit="file"):
        p = _require_file(p)
        reader = PdfReader(str(p))
        for page in reader.pages:
            writer.add_page(page)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        writer.write(fh)

    logger.info("Merged %d file(s) -> %s", len(input_paths), output_path)
    return output_path


def split_pdf(input_path: Path, output_dir: Path) -> List[Path]:
    """Split ``input_path`` into one single-page PDF per page in ``output_dir``."""
    input_path = _require_file(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(input_path))
    stem = input_path.stem
    output_paths: List[Path] = []

    for i, page in enumerate(tqdm(reader.pages, desc="Splitting PDF", unit="page"), start=1):
        writer = PdfWriter()
        writer.add_page(page)
        page_path = output_dir / f"{stem}_page_{i:03d}.pdf"
        with page_path.open("wb") as fh:
            writer.write(fh)
        output_paths.append(page_path)

    logger.info("Split %s into %d page file(s) -> %s", input_path.name, len(output_paths), output_dir)
    return output_paths


def extract_text(input_path: Path, output_path: Optional[Path] = None) -> str:
    """Extract all text from a PDF. Optionally also write it to ``output_path``."""
    input_path = _require_file(input_path)
    reader = PdfReader(str(input_path))

    pages_text = [
        page.extract_text() or ""
        for page in tqdm(reader.pages, desc="Extracting text", unit="page")
    ]
    full_text = "\n\n".join(pages_text).strip()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(full_text, encoding="utf-8")
        logger.info("Extracted text from %s -> %s", input_path.name, output_path)
    else:
        logger.info("Extracted %d character(s) of text from %s", len(full_text), input_path.name)

    return full_text


def rotate_pages(input_path: Path, output_path: Path, degrees: int = 90) -> Path:
    """Rotate every page of a PDF by ``degrees`` (must be a multiple of 90)."""
    if degrees % 90 != 0:
        raise ValueError("degrees must be a multiple of 90")

    input_path = _require_file(input_path)
    reader = PdfReader(str(input_path))
    writer = PdfWriter()

    for page in tqdm(reader.pages, desc="Rotating pages", unit="page"):
        page.rotate(degrees)
        writer.add_page(page)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        writer.write(fh)

    logger.info("Rotated %s by %d degrees -> %s", input_path.name, degrees, output_path)
    return output_path


def encrypt_pdf(input_path: Path, output_path: Path, password: str) -> Path:
    """Password-protect a PDF, writing the result to ``output_path``."""
    if not password:
        raise ValueError("password must not be empty")

    input_path = _require_file(input_path)
    reader = PdfReader(str(input_path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        writer.write(fh)

    logger.info("Encrypted %s -> %s", input_path.name, output_path)
    return output_path


def decrypt_pdf(input_path: Path, output_path: Path, password: str) -> Path:
    """Remove password protection from a PDF, given the correct ``password``."""
    input_path = _require_file(input_path)
    reader = PdfReader(str(input_path))

    if reader.is_encrypted:
        if reader.decrypt(password) == 0:
            raise ValueError("Incorrect password for encrypted PDF")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        writer.write(fh)

    logger.info("Decrypted %s -> %s", input_path.name, output_path)
    return output_path


def extract_metadata(input_path: Path) -> Dict[str, str]:
    """Return a PDF's metadata (title, author, page count, etc.) as a dict."""
    input_path = _require_file(input_path)
    reader = PdfReader(str(input_path))

    meta = reader.metadata or {}
    result: Dict[str, str] = {str(k).lstrip("/"): str(v) for k, v in meta.items()}
    result["page_count"] = str(len(reader.pages))
    result["encrypted"] = str(reader.is_encrypted)
    result["file_size_bytes"] = str(input_path.stat().st_size)

    return result
