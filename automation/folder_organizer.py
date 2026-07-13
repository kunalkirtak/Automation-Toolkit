"""
automation/folder_organizer.py
=================================
Organize a directory's files into sub-folders by file type
(Images/, Documents/, Spreadsheets/, ...), using the category map in
config.py by default.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from tqdm import tqdm

from automation.logger import get_logger
from config import default_config

logger = get_logger(__name__)


def _resolve_collision(new_path: Path) -> Path:
    if not new_path.exists():
        return new_path
    stem, suffix = new_path.stem, new_path.suffix
    counter = 1
    candidate = new_path.with_name(f"{stem}_{counter}{suffix}")
    while candidate.exists():
        counter += 1
        candidate = new_path.with_name(f"{stem}_{counter}{suffix}")
    return candidate


def _build_extension_map(categories: Dict[str, List[str]]) -> Dict[str, str]:
    """Invert {category: [extensions]} into {extension: category} for O(1) lookup."""
    ext_map: Dict[str, str] = {}
    for category, extensions in categories.items():
        for ext in extensions:
            ext_map[ext.lower()] = category
    return ext_map


def organize_by_type(
    directory: Path,
    categories: Optional[Dict[str, List[str]]] = None,
    dry_run: bool = False,
) -> Dict[str, List[Path]]:
    """Move files in ``directory`` into category sub-folders (non-recursive).

    Files with an extension not found in ``categories`` are placed in
    an "Others" folder. Category sub-folders themselves, and any file
    already inside one, are skipped so re-running this is idempotent.

    Args:
        directory: Folder to organize.
        categories: Optional override of {category_name: [extensions]}.
            Defaults to config.DEFAULT_FILE_CATEGORIES.
        dry_run: If True, compute the plan without moving any files.

    Returns:
        Mapping of category name -> list of destination paths.
    """
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    categories = categories or default_config.file_categories
    ext_map = _build_extension_map(categories)

    files = [
        p for p in directory.iterdir()
        if p.is_file() and not p.name.startswith(".")
    ]

    moved: Dict[str, List[Path]] = {cat: [] for cat in categories}

    for f in tqdm(files, desc="Organizing files", unit="file", disable=len(files) < 2):
        category = ext_map.get(f.suffix.lower(), "Others")
        target_dir = directory / category
        target_path = target_dir / f.name

        try:
            if target_path.exists() or (dry_run and target_path == f):
                target_path = _resolve_collision(target_path)
            if not dry_run:
                target_dir.mkdir(exist_ok=True)
                f.rename(target_path)
            moved.setdefault(category, []).append(target_path)
            logger.debug(
                "%s %s -> %s/",
                "Would move" if dry_run else "Moved",
                f.name,
                category,
            )
        except OSError as exc:
            logger.error("Failed to move %s: %s", f, exc)

    total_moved = sum(len(v) for v in moved.values())
    logger.info(
        "%s %d files into %d categories",
        "Would organize" if dry_run else "Organized",
        total_moved,
        sum(1 for v in moved.values() if v),
    )
    return moved
