"""
automation/duplicate_finder.py
=================================
Find duplicate files by content hash (not just filename), and
optionally delete all-but-one copy of each duplicate group.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from tqdm import tqdm

from automation.logger import get_logger
from config import default_config

logger = get_logger(__name__)


def compute_file_hash(path: Path, algorithm: str = "sha256", chunk_size: int = 65536) -> str:
    """Compute a streaming content hash of a file (safe for large files).

    Reads the file in ``chunk_size``-byte chunks rather than loading it
    entirely into memory, so this scales to files far larger than RAM.
    """
    path = Path(path)
    hasher = hashlib.new(algorithm)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(directory: Path, recursive: bool = True) -> Dict[str, List[Path]]:
    """Scan ``directory`` and group files by identical content hash.

    Args:
        directory: Folder to scan.
        recursive: If True, scan sub-folders too.

    Returns:
        A dict of {hash: [paths]} filtered to only hashes with 2+
        files (i.e. actual duplicate groups), sorted so the largest
        groups come first.
    """
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    pattern = "**/*" if recursive else "*"
    files = [p for p in directory.glob(pattern) if p.is_file() and not p.name.startswith(".")]

    hash_map: Dict[str, List[Path]] = defaultdict(list)
    for f in tqdm(files, desc="Hashing files", unit="file", disable=len(files) < 2):
        try:
            file_hash = compute_file_hash(
                f, default_config.hash_algorithm, default_config.hash_chunk_size
            )
            hash_map[file_hash].append(f)
        except OSError as exc:
            logger.warning("Skipped unreadable file %s: %s", f, exc)

    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    duplicates = dict(sorted(duplicates.items(), key=lambda item: len(item[1]), reverse=True))

    total_wasted = sum(len(paths) - 1 for paths in duplicates.values())
    logger.info(
        "Found %d duplicate group(s), %d redundant file(s)", len(duplicates), total_wasted
    )
    return duplicates


def delete_duplicates(
    duplicate_groups: Dict[str, List[Path]], keep: str = "first", dry_run: bool = False
) -> List[Path]:
    """Delete all but one file from each duplicate group.

    Args:
        duplicate_groups: Output of find_duplicates().
        keep: Which copy to keep -- 'first' or 'last' (by path sort order).
        dry_run: If True, report what would be deleted without deleting.

    Returns:
        List of paths that were (or would be) deleted.
    """
    if keep not in ("first", "last"):
        raise ValueError("keep must be 'first' or 'last'")

    deleted: List[Path] = []
    for paths in duplicate_groups.values():
        ordered = sorted(paths)
        keeper = ordered[0] if keep == "first" else ordered[-1]
        for p in ordered:
            if p == keeper:
                continue
            try:
                if not dry_run:
                    p.unlink()
                deleted.append(p)
                logger.debug("%s duplicate %s (kept %s)", "Would delete" if dry_run else "Deleted", p, keeper)
            except OSError as exc:
                logger.error("Failed to delete %s: %s", p, exc)

    logger.info("%s %d duplicate file(s)", "Would delete" if dry_run else "Deleted", len(deleted))
    return deleted
