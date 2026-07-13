"""
config.py
=========
Central configuration for the Automation Toolkit.

Every path, default, and tunable value used across the codebase is
defined here as a single ``Config`` dataclass instance. Nothing else in
the project should hardcode a path or a "magic number" -- it should be
read from here instead. This keeps the toolkit easy to reconfigure
(e.g. for a different machine or a stricter logging setup) without
touching business logic.

Usage
-----
    from config import default_config as cfg
    print(cfg.output_dir)

    # Or load project-specific overrides from a JSON file:
    from config import Config
    cfg = Config.from_file("config.local.json")
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Union

PathLike = Union[str, Path]

# --------------------------------------------------------------------------- #
# Base paths (relative to the project root, i.e. this file's directory)
# --------------------------------------------------------------------------- #
BASE_DIR: Path = Path(__file__).resolve().parent
SAMPLE_DATA_DIR: Path = BASE_DIR / "sample_data"
OUTPUT_DIR: Path = BASE_DIR / "output"
LOGS_DIR: Path = BASE_DIR / "logs"

# --------------------------------------------------------------------------- #
# Default file-type categories used by the folder organizer.
# Extend or override via Config(file_categories=...) or a JSON config file.
# --------------------------------------------------------------------------- #
DEFAULT_FILE_CATEGORIES: Dict[str, List[str]] = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md"],
    "Spreadsheets": [".xlsx", ".xls", ".csv", ".ods"],
    "Presentations": [".ppt", ".pptx", ".odp"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
    "Video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".json", ".ipynb"],
    "Executables": [".exe", ".msi", ".apk", ".sh", ".bat"],
    "Others": [],
}


@dataclass
class Config:
    """Runtime configuration for the toolkit.

    Instantiate directly for sensible defaults, or use
    :meth:`Config.from_file` to layer JSON overrides on top of them.
    """

    # ---- Directories -----------------------------------------------------
    base_dir: Path = BASE_DIR
    sample_data_dir: Path = SAMPLE_DATA_DIR
    output_dir: Path = OUTPUT_DIR
    logs_dir: Path = LOGS_DIR

    # ---- Logging -----------------------------------------------------------
    log_level: str = "INFO"
    log_file: str = "automation.log"
    log_to_console: bool = True
    max_log_bytes: int = 2_000_000
    backup_log_count: int = 3

    # ---- File renamer --------------------------------------------------
    rename_dry_run_default: bool = False
    timestamp_format: str = "%Y%m%d_%H%M%S"

    # ---- Duplicate finder ------------------------------------------------
    hash_algorithm: str = "sha256"
    hash_chunk_size: int = 65536  # 64 KB read chunks for large files

    # ---- Folder organizer --------------------------------------------------
    file_categories: Dict[str, List[str]] = field(
        default_factory=lambda: {k: list(v) for k, v in DEFAULT_FILE_CATEGORIES.items()}
    )

    # ---- Backup ------------------------------------------------------------
    backup_dir_name: str = "backups"
    max_backups_to_keep: int = 5

    # ---- Excel ---------------------------------------------------------
    default_sheet_name: str = "Sheet1"
    header_fill_color: str = "FFD9E1F2"  # light blue, used by excel_tools formatting

    def __post_init__(self) -> None:
        # Ensure the directories the toolkit writes to always exist.
        self.base_dir = Path(self.base_dir)
        self.sample_data_dir = Path(self.sample_data_dir)
        self.output_dir = Path(self.output_dir)
        self.logs_dir = Path(self.logs_dir)
        for directory in (self.output_dir, self.logs_dir):
            directory.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # (De)serialization helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def from_file(cls, path: PathLike) -> "Config":
        """Build a Config by overlaying JSON values on top of the defaults.

        Raises:
            FileNotFoundError: if ``path`` does not exist.
            json.JSONDecodeError: if the file is not valid JSON.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open("r", encoding="utf-8") as fh:
            overrides = json.load(fh)

        for key in ("base_dir", "sample_data_dir", "output_dir", "logs_dir"):
            if key in overrides:
                overrides[key] = Path(overrides[key])

        return cls(**overrides)

    def to_file(self, path: PathLike) -> None:
        """Persist the current configuration to a JSON file."""
        data = asdict(self)
        for key in ("base_dir", "sample_data_dir", "output_dir", "logs_dir"):
            data[key] = str(data[key])
        with Path(path).open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def log_level_int(self) -> int:
        """Return the configured log level as a logging.* int constant."""
        return getattr(logging, self.log_level.upper(), logging.INFO)


# A ready-to-use default instance so other modules can simply do:
#   from config import default_config as cfg
default_config = Config()
