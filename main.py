#!/usr/bin/env python3
"""
main.py
=======
Entry point for the Automation Toolkit.

This module is intentionally thin: it parses CLI arguments (via
``cli.py``), sets up logging and config, then dispatches to the right
function in ``automation/``. All the "what does this command actually
do" logic lives in the automation modules, not here -- that keeps this
file readable as a table of contents for the whole toolkit.

Usage:
    python main.py --help
    python main.py rename prefix --dir ./sample_data/files --prefix "IMG_"
    python main.py organize --dir ./downloads
    python main.py duplicates --dir ./sample_data/files
    python main.py pdf merge --files a.pdf b.pdf --output merged.pdf
    python main.py excel read --file data.xlsx
    python main.py backup --source ./important --destination ./backups
"""

from __future__ import annotations

import logging
import sys

from cli import parse_args
from config import Config, default_config

# NOTE: automation.logger must be configured before other automation
# modules are imported so their module-level `get_logger(__name__)`
# calls pick up the right settings.
from automation.logger import configure_logging, get_logger


def _load_config(args) -> Config:
    """Return the active Config: overrides from --config if given, else defaults."""
    if args.config:
        return Config.from_file(args.config)
    return default_config


def _dispatch(args, logger: logging.Logger) -> int:
    """Route parsed CLI args to the matching automation function.

    Returns:
        Process exit code (0 = success).
    """
    # Local imports so `python main.py --help` stays fast and doesn't
    # eagerly import every dependency (pandas, openpyxl, pypdf) just to
    # print usage text.
    from automation import backup, duplicate_finder, file_renamer, folder_organizer

    if args.command == "rename":
        action = args.rename_action
        if action == "prefix":
            file_renamer.rename_with_prefix(args.dir, args.prefix, args.dry_run)
        elif action == "suffix":
            file_renamer.rename_with_suffix(args.dir, args.suffix, args.dry_run)
        elif action == "timestamp":
            file_renamer.rename_with_timestamp(args.dir, args.ts_format, args.dry_run)
        elif action == "clean-spaces":
            file_renamer.remove_spaces(args.dir, args.replacement, args.dry_run)
        elif action == "extension":
            file_renamer.change_extension(args.dir, args.old_ext, args.new_ext, args.dry_run)

    elif args.command == "organize":
        folder_organizer.organize_by_type(args.dir, dry_run=args.dry_run)

    elif args.command == "duplicates":
        groups = duplicate_finder.find_duplicates(args.dir, recursive=args.recursive)
        if args.delete:
            duplicate_finder.delete_duplicates(groups, keep=args.keep, dry_run=args.dry_run)

    elif args.command == "pdf":
        from automation import pdf_tools

        action = args.pdf_action
        if action == "merge":
            pdf_tools.merge_pdfs(args.files, args.output)
        elif action == "split":
            pdf_tools.split_pdf(args.file, args.output_dir)
        elif action == "extract-text":
            text = pdf_tools.extract_text(args.file, args.output)
            print(text)
        elif action == "rotate":
            pdf_tools.rotate_pages(args.file, args.output, args.degrees)
        elif action == "encrypt":
            pdf_tools.encrypt_pdf(args.file, args.output, args.password)
        elif action == "decrypt":
            pdf_tools.decrypt_pdf(args.file, args.output, args.password)
        elif action == "metadata":
            meta = pdf_tools.extract_metadata(args.file)
            for key, value in meta.items():
                print(f"{key}: {value}")

    elif args.command == "excel":
        from automation import excel_tools

        action = args.excel_action
        if action == "read":
            df = excel_tools.read_workbook(args.file, args.sheet)
            print(df)
        elif action == "create":
            excel_tools.create_workbook(args.file, args.headers, args.sheet)
        elif action == "format":
            excel_tools.apply_formatting(args.file, args.sheet)
        elif action == "summary":
            excel_tools.create_summary_sheet(args.file, args.sheet, args.group_by, args.agg_column)
        elif action == "filter":
            df = excel_tools.filter_data(args.file, args.sheet, args.column, args.value)
            if args.output:
                excel_tools.export_report(df, args.output)
            else:
                print(df)
        elif action == "export":
            df = excel_tools.read_workbook(args.file, args.sheet)
            excel_tools.export_report(df, args.output, args.format)

    elif args.command == "backup":
        backup.create_backup(args.source, args.destination)
        backup.rotate_backups(args.destination, args.max_keep)

    else:  # pragma: no cover - argparse's `required=True` should prevent this
        logger.error("Unknown command: %s", args.command)
        return 2

    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = _load_config(args)

    configure_logging(
        log_dir=cfg.logs_dir,
        log_file=cfg.log_file,
        level=logging.DEBUG if args.verbose else cfg.log_level_int(),
        to_console=cfg.log_to_console,
        max_bytes=cfg.max_log_bytes,
        backup_count=cfg.backup_log_count,
    )
    logger = get_logger(__name__)
    logger.debug("Parsed args: %s", args)

    try:
        return _dispatch(args, logger)
    except NotImplementedError as exc:
        # Expected right now: Part 1 ships the CLI + config + logging
        # scaffolding; automation modules are filled in during Part 2.
        logger.warning(str(exc))
        print(f"Not implemented yet: {exc}")
        return 1
    except FileNotFoundError as exc:
        logger.error("File not found: %s", exc)
        print(f"Error: {exc}")
        return 1
    except (ValueError, KeyError, NotADirectoryError) as exc:
        # Expected, user-actionable input problems (bad password, missing
        # column, wrong file type, etc.) -- log without a stack trace and
        # show a clean one-line message instead of a Python traceback.
        message = str(exc).strip("'\"")
        logger.error("Invalid input for '%s': %s", args.command, message)
        print(f"Error: {message}")
        return 1
    except Exception as exc:  # noqa: BLE001 - top-level safety net for real bugs
        logger.exception("Unexpected error while running '%s'", args.command)
        print(f"Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
