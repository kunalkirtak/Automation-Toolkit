"""
automation/backup.py
======================
Timestamped zip backup creation and rotation.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from automation.logger import get_logger

logger = get_logger(__name__)

_BACKUP_MARKER = "_backup_"


def create_backup(source: Path, destination: Path) -> Path:
    """Create a timestamped zip backup of ``source`` inside ``destination``.

    Works whether ``source`` is a single file or a whole directory.
    Archive name: ``{source_name}_backup_{YYYYmmdd_HHMMSS}.zip``.

    Returns:
        Path to the created .zip archive.
    """
    source = Path(source)
    if not source.exists():
        raise FileNotFoundError(f"Backup source does not exist: {source}")

    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_base = destination / f"{source.name}{_BACKUP_MARKER}{timestamp}"

    if source.is_dir():
        archive_path = shutil.make_archive(
            str(archive_base), "zip", root_dir=source.parent, base_dir=source.name
        )
    else:
        # shutil.make_archive expects a directory to zip; for a single
        # file, stage it in a throwaway temp layout so the archive
        # still contains just that one file at its root.
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            staged = Path(tmp_dir) / source.name
            shutil.copy2(source, staged)
            archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=tmp_dir)

    logger.info("Backed up %s -> %s", source, archive_path)
    return Path(archive_path)


def rotate_backups(destination: Path, max_backups_to_keep: int = 5) -> int:
    """Delete the oldest backups in ``destination``, keeping only the newest N.

    Only touches files matching the ``*_backup_*.zip`` naming pattern
    produced by ``create_backup``, so it won't delete unrelated files.

    Returns:
        The number of backups deleted.
    """
    if max_backups_to_keep < 0:
        raise ValueError("max_backups_to_keep must be >= 0")

    destination = Path(destination)
    if not destination.exists():
        return 0

    backups = sorted(
        (p for p in destination.glob(f"*{_BACKUP_MARKER}*.zip") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    to_delete = backups[max_backups_to_keep:]

    for backup_file in to_delete:
        try:
            backup_file.unlink()
            logger.debug("Rotated out old backup: %s", backup_file.name)
        except OSError as exc:
            logger.error("Failed to delete old backup %s: %s", backup_file, exc)

    if to_delete:
        logger.info("Rotated %d old backup(s), kept %d newest", len(to_delete), min(len(backups), max_backups_to_keep))
    return len(to_delete)
