"""
cli.py
======
Argument parser for the Automation Toolkit.

This module only *defines* the command-line interface -- it builds an
``argparse.ArgumentParser`` with one subcommand per feature group
(rename, organize, duplicates, pdf, excel, backup) and returns parsed
args. Dispatching those args to the right function in ``automation/``
happens in ``main.py``, keeping "what the CLI looks like" separate from
"what happens when you run it".

Run ``python main.py --help`` (or any subcommand + --help) to see the
full, auto-generated usage text.
"""

from __future__ import annotations

import argparse
from pathlib import Path

PROG_NAME = "automation-toolkit"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description=(
            "Automation Toolkit -- batch file renaming, folder organizing, "
            "duplicate detection, PDF automation, and Excel automation, "
            "all from one CLI."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable DEBUG-level logging"
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="path to a JSON config override file"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_rename_parser(subparsers)
    _add_organize_parser(subparsers)
    _add_duplicates_parser(subparsers)
    _add_pdf_parser(subparsers)
    _add_excel_parser(subparsers)
    _add_backup_parser(subparsers)

    return parser


# --------------------------------------------------------------------------- #
# rename
# --------------------------------------------------------------------------- #
def _add_rename_parser(subparsers: argparse._SubParsersAction) -> None:
    rename = subparsers.add_parser("rename", help="batch rename files in a folder")
    rename_sub = rename.add_subparsers(dest="rename_action", required=True)

    prefix = rename_sub.add_parser("prefix", help="prepend a prefix to every filename")
    prefix.add_argument("--dir", type=Path, required=True, help="target directory")
    prefix.add_argument("--prefix", type=str, required=True)
    prefix.add_argument("--dry-run", action="store_true", help="preview without renaming")

    suffix = rename_sub.add_parser("suffix", help="append a suffix to every filename")
    suffix.add_argument("--dir", type=Path, required=True)
    suffix.add_argument("--suffix", type=str, required=True)
    suffix.add_argument("--dry-run", action="store_true")

    timestamp = rename_sub.add_parser("timestamp", help="prepend a timestamp to every filename")
    timestamp.add_argument("--dir", type=Path, required=True)
    timestamp.add_argument("--format", type=str, default="%Y%m%d_%H%M%S", dest="ts_format")
    timestamp.add_argument("--dry-run", action="store_true")

    clean = rename_sub.add_parser("clean-spaces", help="replace spaces in filenames")
    clean.add_argument("--dir", type=Path, required=True)
    clean.add_argument("--replacement", type=str, default="_")
    clean.add_argument("--dry-run", action="store_true")

    ext = rename_sub.add_parser("extension", help="change file extensions in bulk")
    ext.add_argument("--dir", type=Path, required=True)
    ext.add_argument("--old-ext", type=str, required=True, help="e.g. .txt")
    ext.add_argument("--new-ext", type=str, required=True, help="e.g. .md")
    ext.add_argument("--dry-run", action="store_true")


# --------------------------------------------------------------------------- #
# organize
# --------------------------------------------------------------------------- #
def _add_organize_parser(subparsers: argparse._SubParsersAction) -> None:
    organize = subparsers.add_parser("organize", help="sort a folder's files by type")
    organize.add_argument("--dir", type=Path, required=True, help="directory to organize")
    organize.add_argument("--dry-run", action="store_true", help="preview without moving files")


# --------------------------------------------------------------------------- #
# duplicates
# --------------------------------------------------------------------------- #
def _add_duplicates_parser(subparsers: argparse._SubParsersAction) -> None:
    dupes = subparsers.add_parser("duplicates", help="find (and optionally delete) duplicate files")
    dupes.add_argument("--dir", type=Path, required=True)
    dupes.add_argument("--recursive", action="store_true", default=True)
    dupes.add_argument("--delete", action="store_true", help="delete all but one copy of each duplicate")
    dupes.add_argument("--keep", choices=["first", "last"], default="first")
    dupes.add_argument("--dry-run", action="store_true", help="preview deletions without deleting")


# --------------------------------------------------------------------------- #
# pdf
# --------------------------------------------------------------------------- #
def _add_pdf_parser(subparsers: argparse._SubParsersAction) -> None:
    pdf = subparsers.add_parser("pdf", help="PDF automation: merge, split, rotate, encrypt, ...")
    pdf_sub = pdf.add_subparsers(dest="pdf_action", required=True)

    merge = pdf_sub.add_parser("merge", help="merge multiple PDFs into one")
    merge.add_argument("--files", type=Path, nargs="+", required=True)
    merge.add_argument("--output", type=Path, required=True)

    split = pdf_sub.add_parser("split", help="split a PDF into one file per page")
    split.add_argument("--file", type=Path, required=True)
    split.add_argument("--output-dir", type=Path, required=True)

    extract_text = pdf_sub.add_parser("extract-text", help="extract all text from a PDF")
    extract_text.add_argument("--file", type=Path, required=True)
    extract_text.add_argument("--output", type=Path, default=None, help="optional .txt output path")

    rotate = pdf_sub.add_parser("rotate", help="rotate every page of a PDF")
    rotate.add_argument("--file", type=Path, required=True)
    rotate.add_argument("--degrees", type=int, default=90, choices=[90, 180, 270])
    rotate.add_argument("--output", type=Path, required=True)

    encrypt = pdf_sub.add_parser("encrypt", help="password-protect a PDF")
    encrypt.add_argument("--file", type=Path, required=True)
    encrypt.add_argument("--password", type=str, required=True)
    encrypt.add_argument("--output", type=Path, required=True)

    decrypt = pdf_sub.add_parser("decrypt", help="remove password protection from a PDF")
    decrypt.add_argument("--file", type=Path, required=True)
    decrypt.add_argument("--password", type=str, required=True)
    decrypt.add_argument("--output", type=Path, required=True)

    metadata = pdf_sub.add_parser("metadata", help="print a PDF's metadata")
    metadata.add_argument("--file", type=Path, required=True)


# --------------------------------------------------------------------------- #
# excel
# --------------------------------------------------------------------------- #
def _add_excel_parser(subparsers: argparse._SubParsersAction) -> None:
    excel = subparsers.add_parser("excel", help="Excel automation: read, create, format, filter, ...")
    excel_sub = excel.add_subparsers(dest="excel_action", required=True)

    read = excel_sub.add_parser("read", help="print the contents of a worksheet")
    read.add_argument("--file", type=Path, required=True)
    read.add_argument("--sheet", type=str, default=None)

    create = excel_sub.add_parser("create", help="create a new workbook with a header row")
    create.add_argument("--file", type=Path, required=True)
    create.add_argument("--headers", type=str, nargs="+", required=True)
    create.add_argument("--sheet", type=str, default="Sheet1")

    fmt = excel_sub.add_parser("format", help="apply header styling / column autofit")
    fmt.add_argument("--file", type=Path, required=True)
    fmt.add_argument("--sheet", type=str, default="Sheet1")

    summary = excel_sub.add_parser("summary", help="create a grouped summary sheet")
    summary.add_argument("--file", type=Path, required=True)
    summary.add_argument("--sheet", type=str, required=True)
    summary.add_argument("--group-by", type=str, required=True)
    summary.add_argument("--agg-column", type=str, required=True)

    filter_cmd = excel_sub.add_parser("filter", help="filter rows by a column value")
    filter_cmd.add_argument("--file", type=Path, required=True)
    filter_cmd.add_argument("--sheet", type=str, required=True)
    filter_cmd.add_argument("--column", type=str, required=True)
    filter_cmd.add_argument("--value", type=str, required=True)
    filter_cmd.add_argument("--output", type=Path, default=None)

    export = excel_sub.add_parser("export", help="export a sheet to xlsx or csv")
    export.add_argument("--file", type=Path, required=True)
    export.add_argument("--sheet", type=str, default=None)
    export.add_argument("--format", type=str, choices=["xlsx", "csv"], default="csv")
    export.add_argument("--output", type=Path, required=True)


# --------------------------------------------------------------------------- #
# backup
# --------------------------------------------------------------------------- #
def _add_backup_parser(subparsers: argparse._SubParsersAction) -> None:
    backup = subparsers.add_parser("backup", help="create a timestamped zip backup of a folder")
    backup.add_argument("--source", type=Path, required=True)
    backup.add_argument("--destination", type=Path, required=True)
    backup.add_argument("--max-keep", type=int, default=5, help="how many backups to retain")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments. Pass argv explicitly in tests; defaults to sys.argv."""
    parser = build_parser()
    return parser.parse_args(argv)
