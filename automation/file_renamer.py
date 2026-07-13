"""
automation/file_renamer.py
============================
Batch file renaming utilities.

All functions operate non-recursively on a single directory, return a
list of ``RenameResult`` records describing exactly what happened (or
would happen, in dry-run mode), and never silently overwrite an
existing file -- name collisions are resolved by appending ``_1``,
``_2``, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

from tqdm import tqdm

from automation.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RenameResult:
    """Outcome of renaming a single file."""

    original_path: Path
    new_path: Path
    success: bool
    error: str = ""


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def _validate_directory(directory: Path) -> Path:
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    return directory


def _list_files(directory: Path) -> List[Path]:
    """Non-recursive list of files (skips sub-directories and hidden files)."""
    return sorted(p for p in directory.iterdir() if p.is_file() and not p.name.startswith("."))


def _resolve_collision(new_path: Path) -> Path:
    """If new_path already exists, append _1, _2, ... before the extension."""
    if not new_path.exists():
        return new_path
    stem, suffix = new_path.stem, new_path.suffix
    counter = 1
    candidate = new_path.with_name(f"{stem}_{counter}{suffix}")
    while candidate.exists():
        counter += 1
        candidate = new_path.with_name(f"{stem}_{counter}{suffix}")
    return candidate


def _apply_rename(original: Path, new_name: str, dry_run: bool) -> RenameResult:
    new_path = original.with_name(new_name)
    if new_path == original:
        return RenameResult(original, original, True)  # nothing to change

    new_path = _resolve_collision(new_path)
    try:
        if not dry_run:
            original.rename(new_path)
        logger.debug(
            "%s: %s -> %s",
            "Would rename" if dry_run else "Renamed",
            original.name,
            new_path.name,
        )
        return RenameResult(original, new_path, True)
    except OSError as exc:
        logger.error("Failed to rename %s: %s", original, exc)
        return RenameResult(original, new_path, False, str(exc))


def _log_summary(results: List[RenameResult], dry_run: bool) -> None:
    succeeded = sum(1 for r in results if r.success)
    failed = len(results) - succeeded
    verb = "Would rename" if dry_run else "Renamed"
    logger.info("%s %d/%d files (%d failed)", verb, succeeded, len(results), failed)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def rename_with_prefix(directory: Path, prefix: str, dry_run: bool = False) -> List[RenameResult]:
    """Prepend ``prefix`` to every filename in ``directory`` (non-recursive)."""
    directory = _validate_directory(directory)
    files = _list_files(directory)
    results = [
        _apply_rename(f, f"{prefix}{f.name}", dry_run)
        for f in tqdm(files, desc="Adding prefix", unit="file", disable=len(files) < 2)
    ]
    _log_summary(results, dry_run)
    return results


def rename_with_suffix(directory: Path, suffix: str, dry_run: bool = False) -> List[RenameResult]:
    """Append ``suffix`` (before the extension) to every filename in ``directory``."""
    directory = _validate_directory(directory)
    files = _list_files(directory)
    results = [
        _apply_rename(f, f"{f.stem}{suffix}{f.suffix}", dry_run)
        for f in tqdm(files, desc="Adding suffix", unit="file", disable=len(files) < 2)
    ]
    _log_summary(results, dry_run)
    return results


def rename_with_timestamp(
    directory: Path, timestamp_format: str = "%Y%m%d_%H%M%S", dry_run: bool = False
) -> List[RenameResult]:
    """Prepend a single, shared timestamp to every filename in ``directory``.

    The timestamp is captured once at the start of the batch (not per
    file) so all files renamed in the same run share the same prefix.
    """
    directory = _validate_directory(directory)
    files = _list_files(directory)
    stamp = datetime.now().strftime(timestamp_format)
    results = [
        _apply_rename(f, f"{stamp}_{f.name}", dry_run)
        for f in tqdm(files, desc="Adding timestamp", unit="file", disable=len(files) < 2)
    ]
    _log_summary(results, dry_run)
    return results


def remove_spaces(directory: Path, replacement: str = "_", dry_run: bool = False) -> List[RenameResult]:
    """Replace whitespace in filenames with ``replacement`` (default underscore)."""
    directory = _validate_directory(directory)
    files = _list_files(directory)
    results = [
        _apply_rename(f, f.name.replace(" ", replacement), dry_run)
        for f in tqdm(files, desc="Removing spaces", unit="file", disable=len(files) < 2)
    ]
    _log_summary(results, dry_run)
    return results


def change_extension(
    directory: Path, old_ext: str, new_ext: str, dry_run: bool = False
) -> List[RenameResult]:
    """Change every file matching ``old_ext`` in ``directory`` to ``new_ext``.

    Note: this only relabels the file extension; it does not convert
    the underlying file format (e.g. .txt -> .md just renames the file,
    it doesn't reformat the content).
    """
    directory = _validate_directory(directory)
    if not old_ext.startswith("."):
        old_ext = f".{old_ext}"
    if not new_ext.startswith("."):
        new_ext = f".{new_ext}"

    files = [f for f in _list_files(directory) if f.suffix.lower() == old_ext.lower()]
    results = [
        _apply_rename(f, f"{f.stem}{new_ext}", dry_run)
        for f in tqdm(files, desc="Changing extension", unit="file", disable=len(files) < 2)
    ]
    _log_summary(results, dry_run)
    return results
