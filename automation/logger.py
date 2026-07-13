"""
automation/logger.py
=====================
Centralized logging for the Automation Toolkit.

Design
------
* A single rotating file handler writes every log line to
  ``logs/automation.log`` (rotated once it hits ``max_log_bytes``).
* An optional console handler mirrors the same lines to stdout, so
  running a command interactively shows live progress as well.
* Every other module calls ``get_logger(__name__)`` to get a properly
  namespaced child logger (e.g. ``automation.pdf_tools``), so log lines
  are always traceable back to the module that produced them.
* Configuration (level, file name, rotation size) is pulled from
  ``config.default_config`` but can be overridden explicitly, which
  is useful in tests.

Example
-------
    from automation.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Starting batch rename of %d files", count)
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

try:
    from config import default_config
except ImportError:  # pragma: no cover - allows standalone import/testing
    default_config = None

_ROOT_LOGGER_NAME = "automation"
_configured = False


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def configure_logging(
    log_dir: Optional[Path] = None,
    log_file: str = "automation.log",
    level: int = logging.INFO,
    to_console: bool = True,
    max_bytes: int = 2_000_000,
    backup_count: int = 3,
) -> logging.Logger:
    """Configure the root 'automation' logger.

    Safe to call more than once -- later calls are no-ops so importing
    several modules that each request a logger doesn't create duplicate
    handlers (and therefore duplicate log lines).

    Returns:
        The configured root 'automation' logger.
    """
    global _configured

    root_logger = logging.getLogger(_ROOT_LOGGER_NAME)

    if _configured:
        return root_logger

    log_dir = Path(log_dir) if log_dir else Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger.setLevel(level)
    root_logger.propagate = False  # don't double-log via the root logger

    formatter = _build_formatter()

    file_handler = RotatingFileHandler(
        log_dir / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    _configured = True
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced child of the 'automation' logger.

    Ensures ``configure_logging`` has run at least once (using
    ``config.default_config`` if available) before handing back the
    logger, so callers never have to configure logging themselves.

    Example:
        get_logger(__name__) inside automation/pdf_tools.py
        -> logger named 'automation.pdf_tools'
    """
    if not _configured:
        if default_config is not None:
            configure_logging(
                log_dir=default_config.logs_dir,
                log_file=default_config.log_file,
                level=default_config.log_level_int(),
                to_console=default_config.log_to_console,
                max_bytes=default_config.max_log_bytes,
                backup_count=default_config.backup_log_count,
            )
        else:
            configure_logging()

    if name == "__main__" or not name.startswith(_ROOT_LOGGER_NAME):
        name = f"{_ROOT_LOGGER_NAME}.{name}"
    return logging.getLogger(name)
